from src.database import db
from src.llm_client import llm_client
from src.logger import logger
from src.templates import (
    build_department_headcount_query,
    build_leave_query,
    build_pay_rate_query,
    build_dead_stock_query,
)


_SCHEMA_LOCK_RULES = r"""
--- STRICT SCHEMA LOCK (MANDATORY OVERRIDES) ---
1. HR DEPARTMENT QUERIES: You are FORBIDDEN from using `DepartmentID` on the `HumanResources.Employee` table. It does not exist.
2. HR BRIDGE TABLE: You MUST join through the bridge table: `HumanResources.Employee` -> `HumanResources.EmployeeDepartmentHistory` -> `HumanResources.Department`.
3. HR CURRENT EMPLOYEES: When joining `EmployeeDepartmentHistory`, filter with `WHERE EDH.EndDate IS NULL`.
4. BIKES / PRODUCTS: You are FORBIDDEN from using the word 'Bicycle' or `ProductNumber LIKE 'BK-%'`. You MUST filter bikes using: `Name LIKE '%Bike%'` AND you MUST ALSO join to `Production.ProductCategory pc` (via `Production.ProductSubcategory ps`) and require `pc.Name = 'Bikes'`. This is MANDATORY — `Name LIKE '%Bike%'` alone also matches non-bike accessories like "Mountain Bike Socks" or "Bike Wash", which are WRONG results. Never return an accessory, clothing, or cleaning product when the user asks about bikes.
5. DEAD STOCK DEFINITION: For any dead stock query, you MUST use `Production.ProductInventory` with `Quantity > 0` AND `ProductID NOT IN (SELECT ProductID FROM Sales.SalesOrderDetail sod JOIN Sales.SalesOrderHeader soh ON sod.SalesOrderID = soh.SalesOrderID WHERE soh.OrderDate >= DATEADD(year, -1, '<ANCHOR_DATE>'))`. NEVER use an inner join to sales for dead stock. If the dead stock question is specifically about bikes, also apply the BIKES category filter from rule 4 above (join to ProductCategory and require pc.Name = 'Bikes') — do not rely on name matching alone.
6. ANTI-EMPTY RESULT RULES (MANDATORY): Never use strict equality (`=`) for string names. ALWAYS use `LIKE '%keyword%'`.
7. EMPLOYEE NAME RESTRICTION (MANDATORY): HumanResources.Employee has NO FirstName, LastName, or Name column. You are STRICTLY FORBIDDEN from using `e.FirstName` or `e.LastName`. You MUST ALWAYS JOIN `HumanResources.Employee` to `Person.Person p ON e.BusinessEntityID = p.BusinessEntityID` to get employee names using `CONCAT(p.FirstName, ' ', p.LastName)`.
8. DEPARTMENT & SALES SEPARATION: Back-office departments (such as 'Engineering', 'Production', 'Human Resources', etc.) DO NOT have sales records. Do not force an inner join between non-sales departments and sales tables.
9. MINIMAL JOIN RULE (MANDATORY): Only join tables strictly required. For simple aggregates (total sales, total orders) without employee/customer/territory filter, aggregate directly on SalesOrderHeader alone — no Person, Territory, or Address joins.
10. LEAVE / VACATION RULE: There is NO leave-history table. The ONLY leave data is `VacationHours` and `SickLeaveHours` on `HumanResources.Employee` (running totals, not dated records). Query Employee directly (joined to Person.Person for name), order by VacationHours DESC (or SickLeaveHours DESC, or their sum). Do NOT join any leave-specific table.
11. PAY RATE / SALARY RULE: `EmployeePayHistory` has NO `CurrentPayRate`, `RateChangeAmount`, or `Salary` column. It has only `BusinessEntityID`, `RateChangeDate`, `Rate`. For current rate: CROSS APPLY with TOP 1 per employee ordered by RateChangeDate DESC. Rate is hourly ($6.50-$125). Annualize by multiplying by 2080 for salary comparisons.
12. PRODUCT.CATEGORY JOINS: `Production.Product` does NOT have a `ProductCategoryID` column. It has `ProductSubcategoryID`. To reach ProductCategory, you MUST go through `Production.ProductSubcategory`: Product.ProductSubcategoryID -> ProductSubcategory.ProductSubcategoryID -> ProductSubcategory.ProductCategoryID -> ProductCategory.ProductCategoryID.
13. SALESORDERDETAIL DATE: `Sales.SalesOrderDetail` does NOT have an `OrderDate` column. It has `SalesOrderID`. To filter sales by date, JOIN to `Sales.SalesOrderHeader` on SalesOrderID and use `SalesOrderHeader.OrderDate`.
14. TRANSACTION HISTORY: `Production.TransactionHistory` has `TransactionDate`, not `OrderDate`. TransactionType: 'S'=Sale (links to SalesOrderHeader), 'W'=WorkOrder (links to WorkOrder), 'P'=PurchaseOrder.
15. CUSTOMER ADDRESS RESOLUTION (MANDATORY): `Sales.Customer` has NO address columns — no `StateProvinceID`, no `AddressID`, no `City`, no `PostalCode`, nothing. You are FORBIDDEN from joining `Sales.Customer` directly to `Person.StateProvince`, `Person.Address`, or any address table. To find a customer's location (country, state, city, postal code), you MUST follow this exact chain: `Sales.Customer` → `Person.Person` ON `c.PersonID = p.BusinessEntityID` → `Person.BusinessEntityAddress` ON `p.BusinessEntityID = bea.BusinessEntityID` → `Person.Address` ON `bea.AddressID = a.AddressID` → `Person.StateProvince` ON `a.StateProvinceID = sp.StateProvinceID` → `Person.CountryRegion` ON `sp.CountryRegionCode = cr.CountryRegionCode`. Then filter on `cr.Name` (for country), `sp.Name` (for state), `a.City` (for city), or `a.PostalCode` (for postal code). For store (B2B) customers, replace the Person link with: `Sales.Customer` → `Sales.Store` ON `c.StoreID = s.BusinessEntityID` → `Person.BusinessEntityAddress` ON `s.BusinessEntityID = bea.BusinessEntityID` → same address chain. Use `UNION` if you need both individual and store customers.
16. EMPLOYEE COLUMN OWNERSHIP (MANDATORY): When joining `HumanResources.Employee e` with `Person.Person p`, you MUST use the correct table alias for each column. The following columns exist ONLY on `HumanResources.Employee` (use `e.` prefix): `BirthDate`, `HireDate`, `JobTitle`, `Gender`, `MaritalStatus`, `VacationHours`, `SickLeaveHours`, `CurrentFlag`, `SalariedFlag`, `LoginID`, `NationalIDNumber`, `OrganizationNode`, `OrganizationLevel`, `ManagerID`. The following columns exist ONLY on `Person.Person` (use `p.` prefix): `FirstName`, `LastName`, `MiddleName`, `Title`, `Suffix`, `PersonType`, `NameStyle`, `EmailPromotion`. NEVER use `p.BirthDate`, `p.HireDate`, `p.JobTitle`, `p.Gender`, or `p.VacationHours` — these columns do NOT exist on Person.Person.

--- OUTPUT RULES ---
1. Return ONLY pure, executable T-SQL code. No markdown, no explanations.
2. RETURN EXACTLY ONE SELECT STATEMENT. DO NOT use `USE database_name;` or `SET NOCOUNT ON;`.
3. Strictly adhere to the retrieved schema and VERIFIED LIVE COLUMNS below — those are ground truth.
"""


def _build_system_prompt(schema_context: str, error_feedback: str = "") -> str:
    anchor_date = db.get_temporal_anchor() or "2014-05-31"
    rules = _SCHEMA_LOCK_RULES.replace("<ANCHOR_DATE>", anchor_date)
    temporal_block = f"""
TEMPORAL CONTEXT: The most recent order date actually present in the data is {anchor_date}.
Interpret relative-time phrases relative to {anchor_date}.
"""
    prompt = f"""You are an expert SQL Server Developer for an enterprise ERP.

{rules}

{temporal_block}

CRITICAL SCHEMA FACTS — NEVER VIOLATE:
- Sales.Customer has NO Name column. Never use c.Name or Customer.Name.
- Sales.Customer has NO address columns (no StateProvinceID, no AddressID, no City). NEVER join Sales.Customer directly to Person.StateProvince or Person.Address. Use the Person.BusinessEntityAddress → Person.Address → Person.StateProvince chain.
- HumanResources.Employee has NO Name column — always JOIN to Person.Person for names.
- HumanResources.Employee OWNS: BirthDate, HireDate, JobTitle, Gender, MaritalStatus, VacationHours, SickLeaveHours, CurrentFlag, SalariedFlag. NEVER use p.BirthDate or p.HireDate — use e.BirthDate and e.HireDate.
- Person.Person OWNS: FirstName, LastName, MiddleName, Title, Suffix, PersonType. NEVER use e.FirstName or e.LastName.
- Purchasing.Vendor uses BusinessEntityID as PK, NOT VendorID.
- Sales.SalesOrderHeader.Status IN (2,5) for valid revenue — always apply this filter.
- DATE HARDCODING BAN: NEVER hardcode a year like '2022', '2023' in any form. Use only {anchor_date} as reference.
- MONTH RULE: If a user specifies a month without year, use only MONTH(OrderDate) = X. Never add YEAR() filter.

Use ONLY these exact column names from the VERIFIED LIVE COLUMNS:
{schema_context}
"""
    if error_feedback:
        prompt += f"""
CRITICAL: Your previous query failed or returned 0 rows:
{error_feedback}
Use ONLY tables/columns from VERIFIED LIVE COLUMNS. Never invent table or column names.
"""
    return prompt


def generate_sql(
    clarified_query: str,
    schema_context: str,
    error_feedback: str = "",
    original_query: str = "",
) -> tuple[str, tuple | None]:
    template_input = original_query or clarified_query

    template_result = build_department_headcount_query(template_input)
    if template_result[0]:
        logger.info("Using department headcount template")
        return template_result

    template_result = build_leave_query(template_input)
    if template_result[0]:
        logger.info("Using leave query template")
        return template_result

    template_result = build_pay_rate_query(template_input)
    if template_result[0]:
        logger.info("Using pay rate template")
        return template_result

    template_result = build_dead_stock_query(template_input)
    if template_result[0]:
        logger.info("Using dead stock template")
        return template_result

    system_prompt = _build_system_prompt(schema_context, error_feedback)
    raw_sql = llm_client.generate(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clarified_query},
        ],
        temperature=0.0,
    )
    return raw_sql, None

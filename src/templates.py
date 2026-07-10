import re


ANNUAL_HOURS = 2080


def match_dept_headcount(user_query: str) -> bool:
    return bool(re.search(r"\bdepartment\b", user_query, flags=re.IGNORECASE)) and bool(
        re.search(r"\b(?:how many|kitne|count|number of|employees?)\b", user_query, flags=re.IGNORECASE)
    )


def extract_department_name(user_query: str) -> str | None:
    quoted = re.search(r"[\"'‘’“”]([^\"'‘’“”]+)[\"'‘’“”]\s*department", user_query, flags=re.IGNORECASE)
    if quoted:
        return quoted.group(1).strip()
    plain = re.search(r"([A-Za-z][A-Za-z0-9 &/-]+?)\s+department", user_query, flags=re.IGNORECASE)
    if plain:
        return re.sub(r"^(?:the|this|that)\s+", "", plain.group(1).strip(), flags=re.IGNORECASE)
    return None


def is_superlative(user_query: str) -> tuple[bool, bool]:
    highest = bool(re.search(
        r"\b(highest|maximum|max|top)\b|(?:sa?bse|sab\s*se)\s*(?:zyada|zayada|jyada|jaada|adhik|jyaada)",
        user_query, flags=re.IGNORECASE,
    ))
    lowest = bool(re.search(
        r"\b(lowest|minimum|min)\b|(?:sa?bse|sab\s*se)\s*kam",
        user_query, flags=re.IGNORECASE,
    ))
    return highest, lowest


def list_all_mode(user_query: str) -> bool:
    return bool(re.search(
        r"\b(sab|sabhi|list|kaun[\s-]?kaun|all employees|ranking)\b", user_query, flags=re.IGNORECASE,
    ))


def build_department_headcount_query(user_query: str) -> tuple[str | None, tuple | None]:
    if not match_dept_headcount(user_query):
        return None, None
    dept = extract_department_name(user_query)
    if not dept:
        return None, None
    safe_dept = dept.replace("'", "''")
    sql = (
        "SELECT COUNT(DISTINCT e.BusinessEntityID) AS EmployeeCount "
        "FROM HumanResources.EmployeeDepartmentHistory edh "
        "JOIN HumanResources.Department d ON edh.DepartmentID = d.DepartmentID "
        "JOIN HumanResources.Employee e ON edh.BusinessEntityID = e.BusinessEntityID "
        f"WHERE edh.EndDate IS NULL AND d.Name LIKE '%{safe_dept}%'"
    )
    return sql, None


def build_leave_query(user_query: str) -> tuple[str | None, tuple | None]:
    if not re.search(r"chutt\w*|chhutt\w*|\bleave\b|\bvacation\b", user_query, flags=re.IGNORECASE):
        return None, None
    order_col = "e.SickLeaveHours" if re.search(r"\bsick\b", user_query, flags=re.IGNORECASE) else "e.VacationHours"
    direction = "ASC" if bool(re.search(r"\b(kam|least|lowest|minimum|sabse kam)\b", user_query, flags=re.IGNORECASE)) else "DESC"
    top_clause = "" if list_all_mode(user_query) else "TOP 1 "
    sql = (
        f"SELECT {top_clause}CONCAT(p.FirstName, ' ', p.LastName) AS EmployeeName, "
        f"{order_col} AS LeaveHours "
        "FROM HumanResources.Employee e "
        "JOIN Person.Person p ON e.BusinessEntityID = p.BusinessEntityID "
        f"ORDER BY {order_col} {direction}"
    )
    return sql, None


def build_pay_rate_query(user_query: str) -> tuple[str | None, tuple | None]:
    if not re.search(r"\bsalary\b|\bsalaries\b|pay\s*rate|\bwage\b|\bwages\b|\bpaid\b|tankhwah|tankha", user_query, flags=re.IGNORECASE):
        return None, None
    base_from = (
        "FROM HumanResources.Employee e "
        "JOIN Person.Person p ON e.BusinessEntityID = p.BusinessEntityID "
        "CROSS APPLY ("
        "SELECT TOP 1 ph.Rate "
        "FROM HumanResources.EmployeePayHistory ph "
        "WHERE ph.BusinessEntityID = e.BusinessEntityID "
        "ORDER BY ph.RateChangeDate DESC"
        ") cpr(Rate) "
    )
    select_cols = (
        "CONCAT(p.FirstName, ' ', p.LastName) AS EmployeeName, "
        "e.BusinessEntityID, e.JobTitle, "
        "cpr.Rate AS HourlyRate, "
        f"cpr.Rate * {ANNUAL_HOURS} AS EstimatedAnnualSalary "
    )
    highest, lowest = is_superlative(user_query)
    if highest or lowest:
        direction = "ASC" if lowest else "DESC"
        top_clause = "" if list_all_mode(user_query) else "TOP 1 "
        sql = (
            f"SELECT {top_clause}{select_cols}"
            f"{base_from}"
            "WHERE e.CurrentFlag = 1 "
            f"ORDER BY cpr.Rate {direction}"
        )
        return sql, None
    number_match = re.search(r"(\d[\d,]*)", user_query)
    if not number_match:
        return None, None
    threshold = number_match.group(1).replace(",", "")
    operator = "<" if re.search(r"\b(kam|less|below|under|se\s*kam)\b", user_query, flags=re.IGNORECASE) else ">"
    sql = (
        f"SELECT {select_cols}"
        f"{base_from}"
        f"WHERE e.CurrentFlag = 1 AND cpr.Rate * {ANNUAL_HOURS} {operator} {threshold} "
        "ORDER BY cpr.Rate DESC"
    )
    return sql, None


def build_dead_stock_query(user_query: str) -> tuple[str | None, tuple | None]:
    if not re.search(r"\b(?:dead\s*stock|unsold|baki|stock\s*me\s*[ph]ada|not\s*sold|bina\s*bik[ae])\b", user_query, flags=re.IGNORECASE):
        return None, None
    is_bikes = bool(re.search(r"\b(bike|bicycle|cycle|motorcycle)\b", user_query, flags=re.IGNORECASE))
    anchor_date = "2014-05-31"
    bike_join = ""
    if is_bikes:
        bike_join = (
            "JOIN Production.ProductSubcategory ps ON p.ProductSubcategoryID = ps.ProductSubcategoryID "
            "JOIN Production.ProductCategory pc ON ps.ProductCategoryID = pc.ProductCategoryID AND pc.Name = 'Bikes' "
        )
    sql = (
        "SELECT p.Name, SUM(pi.Quantity) AS TotalStock "
        "FROM Production.Product p "
        "JOIN Production.ProductInventory pi ON p.ProductID = pi.ProductID "
        f"{bike_join}"
        "WHERE pi.Quantity > 0 "
        "AND p.ProductID NOT IN ("
        "SELECT sod.ProductID "
        "FROM Sales.SalesOrderDetail sod "
        "JOIN Sales.SalesOrderHeader soh ON sod.SalesOrderID = soh.SalesOrderID "
        f"WHERE soh.OrderDate >= DATEADD(year, -1, '{anchor_date}')"
        ")"
        "GROUP BY p.Name "
        "ORDER BY TotalStock DESC"
    )
    return sql, None

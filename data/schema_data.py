TABLE_DESCRIPTIONS: dict[str, str] = {
    "Sales.Customer": (
        "Customer master table holding B2B and B2C references. "
        "CRITICAL RULE: This table does NOT have a Name column. "
        "CRITICAL RULE: This table has NO address columns (no StateProvinceID, no AddressID, no City). "
        "To find a customer's location, you MUST go through Person.BusinessEntityAddress → Person.Address → Person.StateProvince. "
        "If you need to display or group by a customer, you MUST use a LEFT JOIN on both Sales.Store and Person.Person. "
        "Use this exact logic in SELECT and GROUP BY: ISNULL(Store.Name, Person.FirstName + ' ' + Person.LastName) AS CustomerName.  Use this for customer-level order counting and grouping. Keywords: customer wise, total orders paid by customer, client volume."
    ),

    "Person.BusinessEntity": (
        "Root supertype table that issues a globally unique BusinessEntityID to every "
        "legal entity — persons, stores, vendors, and employees. "
        "All other entity tables share this PK; always JOIN through here when resolving identity.  The root identification table for corporate entities, tracking internal ID numbers for companies like 'A. Datum Corporation'. Keywords: internal ID number, vendor company ID."
    ),
    "Person.Person": (
        "Individual person master. PersonType: 'EM'=Employee, 'SP'=SalesPerson, "
        "'SC'=StoreContact, 'IN'=IndividualCustomer, 'VC'=VendorContact, 'GC'=GeneralContact. "
        "EmailPromotion: 0=No email, 1=AW only, 2=AW+partners. "
        "BusinessEntityID is a shared PK/FK pointing to Person.BusinessEntity."
    ),
    "Person.Address": (
        "Canonical postal address shared across customers, employees, and vendors. "
        "Never stores entity-specific data — linked via bridge tables "
        "(BusinessEntityAddress, SalesOrderHeader.BillToAddressID, etc.)."
    ),
    "Person.AddressType": (
        "Lookup for address category labels: 'Billing', 'Home', 'Main Office', "
        "'Primary', 'Shipping', 'Archive'. Used in BusinessEntityAddress."
    ),
    "Person.BusinessEntityAddress": (
        "Many-to-many bridge linking any BusinessEntity to one or more postal addresses, "
        "each tagged with an AddressType. Use this to answer 'what address does entity X have?'"
    ),
    "Person.BusinessEntityContact": (
        "Associates an organisation (Store or Vendor) with a named contact person and their "
        "role (ContactType). Answers: 'who is the purchasing manager at vendor X?'"
    ),
    "Person.ContactType": (
        "Lookup of contact role labels: 'Owner', 'Purchasing Agent', 'Purchasing Manager', "
        "'Technical Support', 'Marketing Manager'."
    ),
    "Person.CountryRegion": (
        "ISO 3166 country/region code lookup (e.g. 'US', 'CA', 'DE', 'GB'). "
        "Referenced by StateProvince and Sales.CountryRegionCurrency."
    ),
    "Person.StateProvince": (
        "State and province lookup. References CountryRegion and Sales.SalesTerritory. "
        "IsOnlyStateProvinceFlag=1 means the country has only one province entry.  State, state codes, province, and regional geography lookups. Contains state names like Texas, California, Washington. Keywords: buyers from Texas, registered in state."
    ),
    "Person.EmailAddress": (
        "One or more email addresses per Person. A person may have multiple active emails. "
        "Always JOIN via BusinessEntityID."
    ),
    "Person.PersonPhone": (
        "Phone numbers for Person records, each tagged with PhoneNumberType: Cell, Home, Work. "
        "One person may have multiple phone entries."
    ),
    "Person.PhoneNumberType": (
        "Lookup for phone categories: 'Cell', 'Home', 'Work'."
    ),
    "Person.Password": (
        "Hashed credential store for Person accounts on the AW e-commerce site. "
        "Stores a salted SHA1 hash (PasswordHash) and salt (PasswordSalt). Never plain text."
    ),

    "HumanResources.Department": (
        "Lookup of organisational departments (e.g. Engineering, Marketing, Finance). "
        "Each belongs to a GroupName: 'Research and Development', 'Sales and Marketing', "
        "'Manufacturing'."
    ),
    "HumanResources.Employee": (
        "Core employee master. Stores LoginID, NationalIDNumber, JobTitle, HireDate, "
        "BirthDate, MaritalStatus (M/S), Gender (M/F), SalariedFlag (0=Hourly, 1=Salaried), "
        "VacationHours, SickLeaveHours. CurrentFlag=1 means active. "
        "Self-references via ManagerID for org-chart hierarchy. "
        "JOIN to Person.Person on BusinessEntityID to get employee names."
    ),
    "HumanResources.EmployeeDepartmentHistory": (
        "Full audit trail of every department and shift assignment per employee. "
        "EndDate IS NULL = current assignment. "
        "Use this to answer 'what department is employee X in?' or headcount-by-date queries."
    ),
    "HumanResources.EmployeePayHistory": (
        "Time-series pay history per employee — one row per rate change (RateChangeDate). "
        "Current pay = row with MAX(RateChangeDate) per BusinessEntityID. "
        "PayFrequency: 1=Monthly, 2=Bi-weekly."
    ),
    "HumanResources.JobCandidate": (
        "Résumés submitted by external job applicants, stored as XML. "
        "BusinessEntityID is populated if the candidate was later hired; NULL otherwise."
    ),
    "HumanResources.Shift": (
        "Work shift lookup: Day (07:00–15:00), Evening (15:00–23:00), Night (23:00–07:00). "
        "Referenced by EmployeeDepartmentHistory."
    ),

    "Production.BillOfMaterials": (
        "Recursive BOM: ComponentID builds ProductAssemblyID. BOMLevel=0 = finished good. "
        "StartDate/EndDate define validity windows. "
        "Use dbo.uspGetBillOfMaterials or a recursive CTE to unroll the tree."
    ),
    "Production.Culture": (
        "Locale/language code lookup for product description localisation "
        "(e.g. 'en', 'fr', 'zh-cht', 'ar', 'he', 'th')."
    ),
    "Production.Document": (
        "Engineering and marketing documents (CAD specs, assembly instructions) in a "
        "hierarchical folder structure via DocumentNode (hierarchyid). "
        "Status: 1=Pending Approval, 2=Approved, 3=Obsolete. FolderFlag=1 = folder node."
    ),
    "Production.Illustration": (
        "XML-stored bicycle part diagrams linked to ProductModel for catalogues and assembly docs."
    ),
    "Production.Location": (
        "Inventory and manufacturing locations within the plant "
        "(e.g. 'Tool Crib', 'Frame Storage', 'Paint Shop', 'Subassembly'). "
        "Availability = shelf space in machine-hours per week. CostRate = cost per machine-hour."
    ),
    "Production.Product": (
        "Central product master covering manufactured goods and purchased components. "
        "MakeFlag=1 → manufactured in-house (has WorkOrders). "
        "MakeFlag=0 → purchased externally (has PurchaseOrderDetail rows). "
        "FinishedGoodsFlag=1 → saleable to customers. "
        "ProductLine: 'R'=Road, 'M'=Mountain, 'T'=Touring, 'S'=Standard. "
        "Style: 'W'=Womens, 'M'=Mens, 'U'=Universal. Class: 'H'=High, 'M'=Medium, 'L'=Low. "
        "SellEndDate IS NOT NULL means the product is discontinued."
    ),
    "Production.ProductCategory": (
        "Top-level product grouping: 'Bikes', 'Components', 'Clothing', 'Accessories'."
    ),
    "Production.ProductSubcategory": (
        "Second-level grouping beneath ProductCategory "
        "(e.g. 'Mountain Bikes', 'Road Frames', 'Helmets', 'Gloves'). "
        "Each row belongs to one ProductCategory."
    ),
    "Production.ProductModel": (
        "Product model grouping (e.g. 'Road-150', 'Mountain-500', 'Touring-1000'). "
        "CatalogDescription stores XML marketing specs. Instructions stores XML assembly steps."
    ),
    "Production.ProductDescription": (
        "Localised free-text product descriptions, one row per language via Culture. "
        "Joined through ProductModelProductDescriptionCulture."
    ),
    "Production.ProductModelProductDescriptionCulture": (
        "Three-way bridge: links a ProductModel to a ProductDescription in a specific Culture. "
        "Required for multi-language product catalogue queries."
    ),
    "Production.ProductModelIllustration": (
        "Bridge linking ProductModel records to Illustration diagrams."
    ),
    "Production.ProductCostHistory": (
        "Time-series of standard manufacturing cost changes per product. "
        "Current cost = row WHERE EndDate IS NULL per ProductID. "
        "Prefer this over Product.StandardCost for accurate historical cost analysis."
    ),
    "Production.ProductListPriceHistory": (
        "Audit of retail list price changes per product over time. "
        "Current price = row WHERE EndDate IS NULL per ProductID. "
        "Prefer this over Product.ListPrice for accurate pricing queries."
    ),
    "Production.ProductInventory": (
        "Current on-hand inventory per product per storage Location. "
        "Shelf and Bin provide warehouse coordinates. "
        "Total stock = SUM(Quantity) GROUP BY ProductID across all locations."
    ),
    "Production.ProductDocument": (
        "Bridge table linking products to their engineering/marketing documents."
    ),
    "Production.ProductPhoto": (
        "Product photos stored as binary blobs — ThumbNailPhoto and LargePhoto — "
        "with filename captions."
    ),
    "Production.ProductProductPhoto": (
        "Bridge linking products to their photos. Primary=1 denotes the hero/main image."
    ),
    "Production.ProductReview": (
        "Customer-submitted product reviews with star ratings (1–5) and free-text comments. "
        "ReviewDate is auto-populated. EmailAddress captures the reviewer."
    ),
    "Production.ScrapReason": (
        "Lookup of reasons why work order quantity was scrapped "
        "(e.g. 'Paint failure', 'Drill size too large', 'Thermoform temperature')."
    ),
    "Production.TransactionHistory": (
        "Running ledger of every inventory-impacting transaction. "
        "TransactionType: 'W'=WorkOrder (production output), "
        "'S'=SalesOrder (outbound shipment), 'P'=PurchaseOrder (inbound receipt). "
        "ReferenceOrderID links to the source order in its respective table."
    ),
    "Production.TransactionHistoryArchive": (
        "Archived rows from TransactionHistory — identical schema. "
        "UNION ALL both tables for complete historical analysis."
    ),
    "Production.UnitMeasure": (
        "Unit-of-measure lookup. Common codes: 'EA'=Each, 'LB'=Pounds, 'OZ'=Ounces, "
        "'G'=Grams, 'KG'=Kilograms, 'CM'=Centimetres, 'IN'=Inches."
    ),
    "Production.WorkOrder": (
        "Manufacturing work orders for in-house product production. "
        "StockedQty = OrderQty - ScrappedQty (computed). "
        "ScrappedQty > 0 → ScrapReasonID must be populated. "
        "Only products with MakeFlag=1 have WorkOrders."
    ),
    "Production.WorkOrderRouting": (
        "Step-by-step routing of each WorkOrder through production Locations. "
        "OperationSequence defines step order. Stores planned vs actual times, "
        "labour hours, and machine hours. ActualCost = ActualResourceHrs × Location.CostRate."
    ),

    "Purchasing.Vendor": (
        "Supplier/vendor master. CreditRating: 1=Superior, 2=Excellent, 3=Above Average, "
        "4=Average, 5=Below Average. PreferredVendorStatus=1 → preferred for purchasing. "
        "ActiveFlag=0 → vendor no longer used; exclude from sourcing queries."
    ),
    "Purchasing.ProductVendor": (
        "Vendor-product sourcing catalogue. Defines which vendors supply which products, "
        "at what StandardPrice, with what AverageLeadTime (days) and order quantity constraints. "
        "LastReceiptCost and LastReceiptDate track the most recent actual purchase.  Cross-reference table linking specific products or parts (like tires, wheels, chains) to their preferred supplier or vendor. Keywords: preferred choice for buying, supplies the part."
    ),
    "Purchasing.PurchaseOrderHeader": (
        "Master header for supplier purchase orders. "
        "Status: 1=Pending, 2=Approved, 3=Rejected, 4=Complete. "
        "TotalDue is computed: SubTotal + TaxAmt + Freight. "
        "EmployeeID is the AW buyer who created the PO."
    ),
    "Purchasing.PurchaseOrderDetail": (
        "Line items for each purchase order. LineTotal is computed: OrderQty × UnitPrice. "
        "StockedQty = ReceivedQty - RejectedQty (goods accepted into inventory). "
        "DueDate drives procurement scheduling per line.  Tracks items that were damaged, broken, or rejected from vendor supply shipments. Contains RejectedQty and ReceivedQty. Keywords: broken items, rejected from shipment, vendor damage."
    ),
    "Purchasing.ShipMethod": (
        "Inbound and outbound shipping method/carrier lookup. "
        "ShipBase = flat base fee; ShipRate = per-pound variable rate. "
        "Used by PurchaseOrderHeader (inbound) and SalesOrderHeader (outbound)."
    ),

    "Sales.SalesTerritory": (
        "Geographic sales territory master. Group: 'North America', 'Europe', or 'Pacific'. "
        "Tracks SalesYTD, SalesLastYear, CostYTD, CostLastYear for territory-level P&L."
    ),
    "Sales.Store": (
        "Business customer (retail store) master. Demographics is an XML column with store "
        "attributes: AnnualSales, NumberEmployees, BusinessType, etc. "
        "SalesPersonID links the store to its assigned AW sales representative.  Represents physical retail stores and business-to-business (B2B) customers who buy inventory or stock from us. Keywords: physical retail stores, retail buyers."
    ),
    "Sales.SalesPerson": (
        "Sales representative performance data: quota, bonus, CommissionPct, SalesYTD. "
        "Linked to HumanResources.Employee via BusinessEntityID. "
        "JOIN to Person.Person for the rep's name."
    ),
    "Sales.SalesPersonQuotaHistory": (
        "Time-series of quarterly quota assignments per SalesPerson. "
        "Used to compute quota attainment trends over time."
    ),
    "Sales.SalesTerritoryHistory": (
        "Audit trail of territory assignments per SalesPerson. "
        "EndDate IS NULL = current territory assignment."
    ),
    "Sales.SalesOrderHeader": (
        "Master header table for every sales order placed by a customer. "
        "Each row is one order transaction — use this table to query orders, "
        "revenue, order dates, and shipment status. "
        "Status: 1=InProcess, 2=Approved, 3=Backordered, 4=Rejected, 5=Shipped, 6=Cancelled. "
        "OnlineOrderFlag=1 = web/online order (SalesPersonID is NULL for these). "
        "TotalDue is computed: SubTotal + TaxAmt + Freight. "
        "Revenue and sales reporting: always filter Status IN (2, 5) for approved/shipped orders. "
        "Links to Customer (who ordered), SalesPerson (who sold), SalesTerritory (where), "
        "and Address tables for billing and shipping. "
        "SalesOrderNumber is a computed human-readable order ID (e.g. SO43659)."
    ),
    "Sales.SalesOrderDetail": (
        "Line-item details for each sales order. "
        "LineTotal is computed: OrderQty × UnitPrice × (1 - UnitPriceDiscount). "
        "SpecialOfferID + ProductID is a composite FK to SpecialOfferProduct. "
        "SpecialOfferID=1 always means 'No Discount'.  Contains the individual line items, specific products, quantities, and contents inside a given sales order number. Keywords: inside order, contents of order, line items."
    ),
    "Sales.SalesOrderHeaderSalesReason": (
        "Bridge recording one or more purchase motivations per sales order "
        "(e.g. 'Price', 'Quality', 'On Promotion'). Used for marketing attribution."
    ),
    "Sales.SalesReason": (
        "Lookup of purchase motivations: 'Price', 'Quality', 'Review', 'On Promotion', "
        "'Magazine Advertisement', 'Demo Event'. ReasonType: 'Marketing' or 'Other'."
    ),
    "Sales.SpecialOffer": (
        "Promotional discounts catalogue. DiscountPct applied per line in SalesOrderDetail. "
        "StartDate/EndDate define the promotion window. "
        "Type: 'Seasonal Discount', 'Volume Discount', 'Discontinued Product', 'No Discount'. "
        "SpecialOfferID=1 is always the 'No Discount' sentinel row."
    ),
    "Sales.SpecialOfferProduct": (
        "Bridge restricting which Products are eligible for which SpecialOffers. "
        "SalesOrderDetail references (SpecialOfferID, ProductID) here as a composite FK "
        "to enforce discount validity per product."
    ),
    "Sales.Currency": (
        "ISO 4217 currency code lookup (e.g. 'USD', 'EUR', 'GBP', 'CAD', 'AUD')."
    ),
    "Sales.CountryRegionCurrency": (
        "Maps country/region codes to the currencies accepted there. "
        "A country may have multiple currencies."
    ),
    "Sales.CurrencyRate": (
        "Daily FX exchange rates between USD (base) and foreign currencies. "
        "AverageRate = used for P&L conversion. EndOfDayRate = balance-sheet reporting."
    ),
    "Sales.CreditCard": (
        "Tokenised credit card vault. CardNumber stores last 4 digits only — never full PAN. "
        "CardType: 'SuperiorCard', 'Distinguish', 'ColonialVoice', 'Vista'."
    ),
    "Sales.PersonCreditCard": (
        "Bridge linking Person records to their CreditCard(s). "
        "One person can register multiple cards."
    ),
    "Sales.SalesTaxRate": (
        "Tax rates by StateProvince. TaxType: 1=State, 2=County, 3=City. "
        "TaxRate is a percentage (e.g. 8.75 = 8.75%)."
    ),
    "Sales.ShoppingCartItem": (
        "Transient table for unpurchased items in web shopping carts. "
        "ShoppingCartID is a session identifier. DateCreated enables abandoned-cart analysis."
    ),

    "dbo.AWBuildVersion": (
        "Tracks the current version number of the AdventureWorks database installation. "
        "Single-row metadata table."
    ),
    "dbo.DatabaseLog": (
        "Audit log capturing every DDL statement (CREATE, ALTER, DROP) executed against the DB. "
        "Stores event type, schema, object name, raw T-SQL, and XML representation of the change."
    ),
    "dbo.ErrorLog": (
        "Runtime error audit populated by uspLogError when a TRY…CATCH block fires. "
        "Captures error number, severity, state, procedure name, line number, and message."
    ),
}

TABLE_FOREIGN_KEYS: dict[str, list[dict[str, str]]] = {

    "Person.Person": [
        {"column": "BusinessEntityID", "references_table": "Person.BusinessEntity",
         "references_column": "BusinessEntityID",
         "description": "Shared PK — Person inherits identity from BusinessEntity supertype."},
    ],
    "Person.Address": [
        {"column": "StateProvinceID", "references_table": "Person.StateProvince",
         "references_column": "StateProvinceID",
         "description": "State or province of the address."},
    ],
    "Person.BusinessEntityAddress": [
        {"column": "BusinessEntityID", "references_table": "Person.BusinessEntity",
         "references_column": "BusinessEntityID",
         "description": "Entity (person/vendor/store) that holds this address."},
        {"column": "AddressID", "references_table": "Person.Address",
         "references_column": "AddressID",
         "description": "The physical postal address."},
        {"column": "AddressTypeID", "references_table": "Person.AddressType",
         "references_column": "AddressTypeID",
         "description": "Category of the address (Billing, Shipping, Home, etc.)."},
    ],
    "Person.BusinessEntityContact": [
        {"column": "BusinessEntityID", "references_table": "Person.BusinessEntity",
         "references_column": "BusinessEntityID",
         "description": "The organisation being contacted."},
        {"column": "PersonID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "The person acting as the contact."},
        {"column": "ContactTypeID", "references_table": "Person.ContactType",
         "references_column": "ContactTypeID",
         "description": "Role of the contact at the organisation."},
    ],
    "Person.EmailAddress": [
        {"column": "BusinessEntityID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Person who owns this email address."},
    ],
    "Person.Password": [
        {"column": "BusinessEntityID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Person whose login credentials are stored."},
    ],
    "Person.PersonPhone": [
        {"column": "BusinessEntityID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Person who owns this phone number."},
        {"column": "PhoneNumberTypeID", "references_table": "Person.PhoneNumberType",
         "references_column": "PhoneNumberTypeID",
         "description": "Classification: Cell, Home, or Work."},
    ],
    "Person.StateProvince": [
        {"column": "CountryRegionCode", "references_table": "Person.CountryRegion",
         "references_column": "CountryRegionCode",
         "description": "Country this state/province belongs to."},
        {"column": "TerritoryID", "references_table": "Sales.SalesTerritory",
         "references_column": "TerritoryID",
         "description": "Sales territory covering this state/province."},
    ],

    "HumanResources.Employee": [
        {"column": "BusinessEntityID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Employee IS a Person; shares the same identity record."},
        {"column": "ManagerID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "Self-referencing FK for org hierarchy; NULL = top of tree."},
    ],
    "HumanResources.EmployeeDepartmentHistory": [
        {"column": "BusinessEntityID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "Employee whose assignment is recorded."},
        {"column": "DepartmentID", "references_table": "HumanResources.Department",
         "references_column": "DepartmentID",
         "description": "Department the employee was assigned to."},
        {"column": "ShiftID", "references_table": "HumanResources.Shift",
         "references_column": "ShiftID",
         "description": "Work shift during this assignment period."},
    ],
    "HumanResources.EmployeePayHistory": [
        {"column": "BusinessEntityID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "Employee whose pay rate is recorded."},
    ],
    "HumanResources.JobCandidate": [
        {"column": "BusinessEntityID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "Populated if candidate was later hired as an employee."},
    ],

    "Production.BillOfMaterials": [
        {"column": "ProductAssemblyID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Parent assembly product. NULL = top-level finished good."},
        {"column": "ComponentID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Child component or raw material required by the assembly."},
        {"column": "UnitMeasureCode", "references_table": "Production.UnitMeasure",
         "references_column": "UnitMeasureCode",
         "description": "Unit of measure for PerAssemblyQty."},
    ],
    "Production.Document": [
        {"column": "Owner", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "Employee responsible for maintaining the document."},
    ],
    "Production.Product": [
        {"column": "ProductSubcategoryID", "references_table": "Production.ProductSubcategory",
         "references_column": "ProductSubcategoryID",
         "description": "Subcategory the product belongs to (NULL for non-catalogue components)."},
        {"column": "ProductModelID", "references_table": "Production.ProductModel",
         "references_column": "ProductModelID",
         "description": "Model group this product variant belongs to."},
        {"column": "SizeUnitMeasureCode", "references_table": "Production.UnitMeasure",
         "references_column": "UnitMeasureCode",
         "description": "Unit for the Size column (CM, IN)."},
        {"column": "WeightUnitMeasureCode", "references_table": "Production.UnitMeasure",
         "references_column": "UnitMeasureCode",
         "description": "Unit for the Weight column (LB, G)."},
    ],
    "Production.ProductCostHistory": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product whose cost is being recorded."},
    ],
    "Production.ProductListPriceHistory": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product whose list price history is tracked."},
    ],
    "Production.ProductInventory": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product being stocked."},
        {"column": "LocationID", "references_table": "Production.Location",
         "references_column": "LocationID",
         "description": "Warehouse/shop-floor location where stock is held."},
    ],
    "Production.ProductDocument": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product the document describes."},
        {"column": "DocumentNode", "references_table": "Production.Document",
         "references_column": "DocumentNode",
         "description": "Engineering/marketing document linked to the product."},
    ],
    "Production.ProductModelProductDescriptionCulture": [
        {"column": "ProductModelID", "references_table": "Production.ProductModel",
         "references_column": "ProductModelID",
         "description": "Product model being described."},
        {"column": "ProductDescriptionID", "references_table": "Production.ProductDescription",
         "references_column": "ProductDescriptionID",
         "description": "The localised description text."},
        {"column": "CultureID", "references_table": "Production.Culture",
         "references_column": "CultureID",
         "description": "Language/locale of the description."},
    ],
    "Production.ProductModelIllustration": [
        {"column": "ProductModelID", "references_table": "Production.ProductModel",
         "references_column": "ProductModelID",
         "description": "Product model the illustration belongs to."},
        {"column": "IllustrationID", "references_table": "Production.Illustration",
         "references_column": "IllustrationID",
         "description": "The diagram or illustration being linked."},
    ],
    "Production.ProductProductPhoto": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product the photo belongs to."},
        {"column": "ProductPhotoID", "references_table": "Production.ProductPhoto",
         "references_column": "ProductPhotoID",
         "description": "The photo record containing image blobs."},
    ],
    "Production.ProductReview": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product being reviewed."},
    ],
    "Production.ProductSubcategory": [
        {"column": "ProductCategoryID", "references_table": "Production.ProductCategory",
         "references_column": "ProductCategoryID",
         "description": "Parent category this subcategory rolls up to."},
    ],
    "Production.TransactionHistory": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product involved in the inventory transaction."},
    ],
    "Production.TransactionHistoryArchive": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product involved in the archived inventory transaction."},
    ],
    "Production.WorkOrder": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product being manufactured by this work order."},
        {"column": "ScrapReasonID", "references_table": "Production.ScrapReason",
         "references_column": "ScrapReasonID",
         "description": "Reason for scrapped units; NULL if ScrappedQty = 0."},
    ],
    "Production.WorkOrderRouting": [
        {"column": "WorkOrderID", "references_table": "Production.WorkOrder",
         "references_column": "WorkOrderID",
         "description": "Parent work order this routing step belongs to."},
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product being routed through this manufacturing step."},
        {"column": "LocationID", "references_table": "Production.Location",
         "references_column": "LocationID",
         "description": "Workstation/area where this routing step occurs."},
    ],

    "Purchasing.Vendor": [
        {"column": "BusinessEntityID", "references_table": "Person.BusinessEntity",
         "references_column": "BusinessEntityID",
         "description": "Vendor shares its ID with the BusinessEntity supertype."},
    ],
    "Purchasing.ProductVendor": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product that can be sourced from this vendor."},
        {"column": "BusinessEntityID", "references_table": "Purchasing.Vendor",
         "references_column": "BusinessEntityID",
         "description": "Vendor/supplier offering this product."},
        {"column": "UnitMeasureCode", "references_table": "Production.UnitMeasure",
         "references_column": "UnitMeasureCode",
         "description": "Unit in which the vendor sells this product."},
    ],
    "Purchasing.PurchaseOrderHeader": [
        {"column": "EmployeeID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "AW buyer/employee who created the PO."},
        {"column": "VendorID", "references_table": "Purchasing.Vendor",
         "references_column": "BusinessEntityID",
         "description": "Supplier the order is placed with."},
        {"column": "ShipMethodID", "references_table": "Purchasing.ShipMethod",
         "references_column": "ShipMethodID",
         "description": "Inbound freight carrier for this PO."},
    ],
    "Purchasing.PurchaseOrderDetail": [
        {"column": "PurchaseOrderID", "references_table": "Purchasing.PurchaseOrderHeader",
         "references_column": "PurchaseOrderID",
         "description": "Parent purchase order this line belongs to."},
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product being purchased on this line."},
    ],

    "Sales.Customer": [
        {"column": "PersonID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Populated for individual (B2C) customers; NULL for store customers."},
        {"column": "StoreID", "references_table": "Sales.Store",
         "references_column": "BusinessEntityID",
         "description": "Populated for business (B2B) customers; NULL for individual consumers."},
        {"column": "TerritoryID", "references_table": "Sales.SalesTerritory",
         "references_column": "TerritoryID",
         "description": "Sales territory the customer is assigned to."},
    ],
    "Sales.Store": [
        {"column": "BusinessEntityID", "references_table": "Person.BusinessEntity",
         "references_column": "BusinessEntityID",
         "description": "Store inherits its ID from the BusinessEntity supertype."},
        {"column": "SalesPersonID", "references_table": "Sales.SalesPerson",
         "references_column": "BusinessEntityID",
         "description": "Sales rep responsible for this store account."},
    ],
    "Sales.SalesPerson": [
        {"column": "BusinessEntityID", "references_table": "HumanResources.Employee",
         "references_column": "BusinessEntityID",
         "description": "The employee record for this sales representative."},
        {"column": "TerritoryID", "references_table": "Sales.SalesTerritory",
         "references_column": "TerritoryID",
         "description": "Primary territory assigned to the rep."},
    ],
    "Sales.SalesPersonQuotaHistory": [
        {"column": "BusinessEntityID", "references_table": "Sales.SalesPerson",
         "references_column": "BusinessEntityID",
         "description": "Sales person whose quota is being recorded."},
    ],
    "Sales.SalesTerritoryHistory": [
        {"column": "BusinessEntityID", "references_table": "Sales.SalesPerson",
         "references_column": "BusinessEntityID",
         "description": "Sales person whose territory assignment is recorded."},
        {"column": "TerritoryID", "references_table": "Sales.SalesTerritory",
         "references_column": "TerritoryID",
         "description": "Territory assigned in this window."},
    ],
    "Sales.SalesOrderHeader": [
        {"column": "CustomerID", "references_table": "Sales.Customer",
         "references_column": "CustomerID",
         "description": "Customer who placed the order."},
        {"column": "SalesPersonID", "references_table": "Sales.SalesPerson",
         "references_column": "BusinessEntityID",
         "description": "Sales rep who owns the order; NULL for web orders."},
        {"column": "TerritoryID", "references_table": "Sales.SalesTerritory",
         "references_column": "TerritoryID",
         "description": "Sales territory in which the order was placed."},
        {"column": "BillToAddressID", "references_table": "Person.Address",
         "references_column": "AddressID",
         "description": "Billing address for this order."},
        {"column": "ShipToAddressID", "references_table": "Person.Address",
         "references_column": "AddressID",
         "description": "Shipping/delivery address for this order."},
        {"column": "ShipMethodID", "references_table": "Purchasing.ShipMethod",
         "references_column": "ShipMethodID",
         "description": "Outbound shipping carrier used."},
        {"column": "CreditCardID", "references_table": "Sales.CreditCard",
         "references_column": "CreditCardID",
         "description": "Credit card used for payment; NULL for offline orders."},
        {"column": "CurrencyRateID", "references_table": "Sales.CurrencyRate",
         "references_column": "CurrencyRateID",
         "description": "FX rate applied for foreign-currency orders; NULL for USD."},
    ],
    "Sales.SalesOrderDetail": [
        {"column": "SalesOrderID", "references_table": "Sales.SalesOrderHeader",
         "references_column": "SalesOrderID",
         "description": "Parent sales order this line belongs to."},
        {"column": "SpecialOfferID", "references_table": "Sales.SpecialOfferProduct",
         "references_column": "SpecialOfferID",
         "description": "Discount offer applied (composite FK with ProductID)."},
        {"column": "ProductID", "references_table": "Sales.SpecialOfferProduct",
         "references_column": "ProductID",
         "description": "Product sold on this line (composite FK with SpecialOfferID)."},
    ],
    "Sales.SalesOrderHeaderSalesReason": [
        {"column": "SalesOrderID", "references_table": "Sales.SalesOrderHeader",
         "references_column": "SalesOrderID",
         "description": "The sales order this reason is attributed to."},
        {"column": "SalesReasonID", "references_table": "Sales.SalesReason",
         "references_column": "SalesReasonID",
         "description": "The purchase motivation recorded for the order."},
    ],
    "Sales.SpecialOfferProduct": [
        {"column": "SpecialOfferID", "references_table": "Sales.SpecialOffer",
         "references_column": "SpecialOfferID",
         "description": "The promotional offer being scoped."},
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product eligible for the offer."},
    ],
    "Sales.PersonCreditCard": [
        {"column": "BusinessEntityID", "references_table": "Person.Person",
         "references_column": "BusinessEntityID",
         "description": "Person who owns the credit card."},
        {"column": "CreditCardID", "references_table": "Sales.CreditCard",
         "references_column": "CreditCardID",
         "description": "Credit card token record."},
    ],
    "Sales.CountryRegionCurrency": [
        {"column": "CountryRegionCode", "references_table": "Person.CountryRegion",
         "references_column": "CountryRegionCode",
         "description": "Country the currency mapping applies to."},
        {"column": "CurrencyCode", "references_table": "Sales.Currency",
         "references_column": "CurrencyCode",
         "description": "Currency accepted in that country."},
    ],
    "Sales.CurrencyRate": [
        {"column": "FromCurrencyCode", "references_table": "Sales.Currency",
         "references_column": "CurrencyCode",
         "description": "Source currency (typically USD)."},
        {"column": "ToCurrencyCode", "references_table": "Sales.Currency",
         "references_column": "CurrencyCode",
         "description": "Target foreign currency."},
    ],
    "Sales.SalesTaxRate": [
        {"column": "StateProvinceID", "references_table": "Person.StateProvince",
         "references_column": "StateProvinceID",
         "description": "State/province to which this tax rate applies."},
    ],
    "Sales.ShoppingCartItem": [
        {"column": "ProductID", "references_table": "Production.Product",
         "references_column": "ProductID",
         "description": "Product added to the shopping cart."},
    ],
    "xml_parsing_forbidden": (
        "NEVER use XQuery, .value(), .nodes(), or CROSS APPLY to parse XML columns like "
        "Demographics, CatalogDescription, or Instructions. ALWAYS use the pre-flattened views "
        "instead (e.g., Sales.vStoreWithDemographics, Sales.vPersonDemographics, "
        "Production.vProductModelCatalogDescription, Production.vProductModelInstructions). "
        "Manual XML parsing will cause namespace crashes."
    ),
    "customer_revenue_joins": (
        "To calculate revenue per customer, ALWAYS join Sales.Customer to Sales.SalesOrderHeader "
        "ON Sales.Customer.CustomerID = Sales.SalesOrderHeader.CustomerID. "
        "Do NOT join through SalesPerson to find customer revenue."
    ),
}

BUSINESS_LOGIC: dict[str, str] = {


    "entity_supertype_pattern": (
        "Person.BusinessEntity is the root supertype. Person.Person, Sales.Store, "
        "Purchasing.Vendor, and HumanResources.Employee all share their PK "
        "(BusinessEntityID) with BusinessEntity. "
        "To get an employee's name: JOIN HumanResources.Employee → Person.Person "
        "ON BusinessEntityID. Never assume name columns exist on Employee or Vendor tables."
    ),
    "get_employee_name": (
        "Employee names are in Person.Person, NOT in HumanResources.Employee. "
        "Required JOIN: HumanResources.Employee → Person.Person ON BusinessEntityID. "
        "Extension for full contact: also JOIN Person.EmailAddress, Person.PersonPhone."
    ),
    "current_employee_department": (
        "HumanResources.EmployeeDepartmentHistory.EndDate IS NULL = employee's CURRENT department. "
        "Always filter EndDate IS NULL for headcount or current-department queries. "
        "Without this filter you get all historical assignments."
    ),
    "current_pay_rate": (
        "Current pay = row with MAX(RateChangeDate) per BusinessEntityID in EmployeePayHistory. "
        "There is NO EndDate column — use GROUP BY + MAX or ROW_NUMBER() OVER "
        "(PARTITION BY BusinessEntityID ORDER BY RateChangeDate DESC)."
    ),
    "current_product_list_price": (
        "Use Production.ProductListPriceHistory WHERE EndDate IS NULL for current retail price. "
        "Product.ListPrice is a snapshot that may be stale — avoid it for pricing queries."
    ),
    "current_product_cost": (
        "Use Production.ProductCostHistory WHERE EndDate IS NULL for current standard cost. "
        "Product.StandardCost is a snapshot that may be stale."
    ),
    "sales_order_status_codes": (
        "Sales.SalesOrderHeader.Status: "
        "1=InProcess | 2=Approved | 3=Backordered | 4=Rejected | 5=Shipped | 6=Cancelled. "
        "Revenue reporting: filter Status IN (2, 5). "
        "Exclude Status IN (4, 6) for cancelled/rejected orders."
    ),
    "purchase_order_status_codes": (
        "Purchasing.PurchaseOrderHeader.Status: "
        "1=Pending | 2=Approved | 3=Rejected | 4=Complete. "
        "Valid spend queries: filter Status IN (2, 4)."
    ),
    "individual_vs_store_customer": (
        "Sales.Customer: PersonID IS NOT NULL AND StoreID IS NULL → B2C individual consumer. "
        "Sales.Customer: StoreID IS NOT NULL AND PersonID IS NULL → B2B business/reseller. "
        "These are mutually exclusive per row. "
        "JOIN to Person.Person for individual names; JOIN to Sales.Store for business names. "
        "CRITICAL: If combining both using UNION, you MUST concatenate Person.FirstName and "
        "Person.LastName into a single 'CustomerName' column so it perfectly matches the single "
        "Sales.Store.Name column."
    ),
    "discount_enforcement": (
        "Sales.SalesOrderDetail references Sales.SpecialOfferProduct(SpecialOfferID, ProductID) "
        "as a composite FK — enforces discount validity per product. "
        "SpecialOfferID=1 is always the 'No Discount' sentinel row. "
        "Discounted lines: WHERE SpecialOfferID <> 1."
    ),
    "active_products_for_customers": (
        "For customer-facing product queries: "
        "WHERE FinishedGoodsFlag = 1 AND SellEndDate IS NULL. "
        "FinishedGoodsFlag=0 = internal component; SellEndDate IS NOT NULL = discontinued."
    ),
    "make_vs_buy": (
        "Production.Product.MakeFlag=1 → manufactured in-house → has WorkOrder records. "
        "MakeFlag=0 → purchased externally → has PurchaseOrderDetail records. "
        "Never look for a WorkOrder on a purchased product or vice versa."
    ),
    "bom_recursion": (
        "Production.BillOfMaterials is a recursive structure. "
        "ProductAssemblyID IS NULL = top-level finished good. "
        "Use dbo.uspGetBillOfMaterials(@ProductID, @CheckDate) or a recursive CTE. "
        "Filter: StartDate <= GETDATE() AND (EndDate IS NULL OR EndDate > GETDATE()) "
        "for currently active components."
    ),
    "transaction_type_routing": (
        "Production.TransactionHistory.TransactionType: "
        "'W' → ReferenceOrderID = Production.WorkOrder.WorkOrderID. "
        "'S' → ReferenceOrderID = Sales.SalesOrderHeader.SalesOrderID. "
        "'P' → ReferenceOrderID = Purchasing.PurchaseOrderHeader.PurchaseOrderID. "
        "Always join through the correct table based on TransactionType."
    ),
    "complete_transaction_history": (
        "For full transaction history across all time, UNION ALL "
        "Production.TransactionHistory and Production.TransactionHistoryArchive. "
        "They have identical schemas."
    ),
    "vendor_active_preferred": (
        "Purchasing.Vendor: ActiveFlag=1 for current vendors. "
        "PreferredVendorStatus=1 for preferred sourcing. "
        "CreditRating: 1=Superior (best), 5=Below Average (worst)."
    ),
    "linetotal_computation": (
        "Sales.SalesOrderDetail.LineTotal (computed) = OrderQty * UnitPrice * (1 - UnitPriceDiscount). "
        "Purchasing.PurchaseOrderDetail.LineTotal (computed) = OrderQty * UnitPrice. "
        "These are computed columns — SELECT LineTotal directly, do not manually recalculate."
    ),
    "address_resolution_for_orders": (
        "To resolve shipping/billing address from SalesOrderHeader: "
        "JOIN Person.Address ON SalesOrderHeader.ShipToAddressID = Address.AddressID, "
        "then JOIN Person.StateProvince and Person.CountryRegion for full address. "
        "Do NOT join through BusinessEntityAddress for order addresses."
    ),
    "person_type_codes": (
        "Person.Person.PersonType: "
        "'EM'=Employee | 'SP'=SalesPerson | 'SC'=StoreContact | "
        "'IN'=IndividualCustomer | 'VC'=VendorContact | 'GC'=GeneralContact."
    ),
    "inventory_stock_total": (
        "Production.ProductInventory: total on-hand for a product = SUM(Quantity) GROUP BY ProductID. "
        "LocationID=6 is 'Miscellaneous Storage' — used internally by ufnGetStock function."
    ),
    "special_offer_active_window": (
        "Active promotions in Sales.SpecialOffer: "
        "WHERE StartDate <= GETDATE() AND EndDate >= GETDATE()."
    ),
    "customer_contact_info": (
        "Sales.Customer only contains IDs. For customer names, JOIN Person.Person "
        "ON Sales.Customer.PersonID = Person.Person.BusinessEntityID. "
        "For phone numbers, JOIN Person.PersonPhone ON "
        "Person.Person.BusinessEntityID = Person.PersonPhone.BusinessEntityID."
    ),
    "customer_address_resolution": (
        "Sales.Customer has NO address columns (no StateProvinceID, no AddressID, no City, no PostalCode). "
        "To find a customer's location (country, state, city), follow this EXACT chain: "
        "Sales.Customer → Person.Person (ON c.PersonID = p.BusinessEntityID) → "
        "Person.BusinessEntityAddress (ON p.BusinessEntityID = bea.BusinessEntityID) → "
        "Person.Address (ON bea.AddressID = a.AddressID) → "
        "Person.StateProvince (ON a.StateProvinceID = sp.StateProvinceID) → "
        "Person.CountryRegion (ON sp.CountryRegionCode = cr.CountryRegionCode). "
        "Then filter on cr.Name (country), sp.Name (state), a.City (city), or a.PostalCode. "
        "NEVER join Sales.Customer directly to Person.StateProvince or Person.Address — the FK does not exist."
    ),
}

VIEW_DESCRIPTIONS: dict[str, str] = {
    "Production.vProductAndDescription": (
        "Pre-joined view: Product + ProductModel + ProductDescription + Culture. "
        "Use for 'find product description in language X' queries. Filter on CultureID (e.g. 'en')."
    ),
    "Production.vProductModelCatalogDescription": (
        "Flattened XML catalogue description per ProductModel. Contains marketing attributes "
        "like Wheel, Saddle, Color, Material, WarrantyPeriod, RiderExperience."
    ),
    "Production.vProductModelInstructions": (
        "Flattened assembly instruction steps per ProductModel and LocationID. "
        "Each row = one manufacturing step at one location."
    ),
    "Purchasing.vVendorWithAddresses": (
        "Pre-joined view: Vendor + BusinessEntityAddress + Address + AddressType + "
        "StateProvince + CountryRegion. Use for vendor address lookups."
    ),
    "Purchasing.vVendorWithContacts": (
        "Pre-joined view: Vendor + BusinessEntityContact + Person + EmailAddress + PersonPhone. "
        "Use to find named contacts at vendor organisations."
    ),
    "Sales.vIndividualCustomer": (
        "Pre-joined view for individual (B2C) customers: Customer + Person + Address + "
        "EmailAddress + PersonPhone. Use for customer contact and address lookups."
    ),
    "Sales.vPersonDemographics": (
        "Flattened XML Demographics from Person.Person. Contains TotalPurchaseYTD, "
        "DateFirstPurchase, YearlyIncome, Occupation, HomeOwnerFlag, NumberCarsOwned. "
        "Use for customer segmentation queries."
    ),
    "Sales.vSalesPerson": (
        "Pre-joined view: SalesPerson + Employee + Person + Address + EmailAddress + "
        "SalesTerritory. Use for sales rep contact/territory lookups."
    ),
    "Sales.vSalesPersonSalesByFiscalYears": (
        "Pivoted view of SalesPerson sales by fiscal year (columns 2002, 2003, 2004). "
        "Use for multi-year sales rep performance comparisons."
    ),
    "Sales.vStoreWithAddresses": (
        "Pre-joined view: Store + BusinessEntityAddress + Address + AddressType. "
        "Use for store address lookups."
    ),
    "Sales.vStoreWithContacts": (
        "Pre-joined view: Store + BusinessEntityContact + Person + EmailAddress + PersonPhone. "
        "Use to find named contacts at store organisations."
    ),
    "Sales.vStoreWithDemographics": (
        "Flattened XML Demographics from Sales.Store. Contains AnnualSales, AnnualRevenue, "
        "NumberEmployees, BusinessType, YearOpened, Brands. Use for store segmentation."
    ),
    "hr_balances_snapshot": (
        "HumanResources.Employee.SickLeaveHours and VacationHours represent CURRENT accrued balances, "
        "not a historical log of hours taken. If a user asks for hours 'this year', simply pull the current balance "
        "for currently active employees (using EmployeeDepartmentHistory.EndDate IS NULL). Do NOT attempt to "
        "filter by StartDate or GETDATE() to solve 'this year' for these columns."
    ),
}

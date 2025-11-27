org_units:
  # Executive Board ----------------------------------------------------------
  - id: CEO
    name: Sofia Berger
    role_title: Chief Executive Officer
    level: Executive
    org_unit: Group Executive Board
    reports_to: null

  - id: CFO
    name: Amira El-Sayed
    role_title: Chief Financial Officer
    level: Executive
    org_unit: Group Finance
    reports_to: CEO

  - id: CHRO
    name: Jonas Weber
    role_title: Chief People & Culture Officer
    level: Executive
    org_unit: People & Culture
    reports_to: CEO

  - id: CCO
    name: Isabella Conti
    role_title: Chief Commercial Officer
    level: Executive
    org_unit: Group Commercial
    reports_to: CEO

  - id: COO
    name: Rafael Mendes
    role_title: Chief Operating Officer
    level: Executive
    org_unit: Operations & Supply Chain
    reports_to: CEO

  - id: CIO
    name: Priya Srinivasan
    role_title: Chief Information Officer
    level: Executive
    org_unit: Technology & Data
    reports_to: CEO

  - id: CSO
    name: Erik Jónsson
    role_title: Chief Sustainability Officer
    level: Executive
    org_unit: ESG & Sustainability
    reports_to: CEO

  # Commercial (under CCO) ---------------------------------------------------
  - id: CAT_MGMT
    name: Miguel Alvarez
    role_title: VP Category Management
    level: Function
    org_unit: Category Management
    reports_to: CCO

  - id: PRICING_PROMO
    name: Nora Schmidt
    role_title: VP Pricing & Promotions
    level: Function
    org_unit: Pricing & Promotions
    reports_to: CCO

  - id: ECOM
    name: Lina Pettersson
    role_title: VP E-Commerce & Marketplaces
    level: Function
    org_unit: E-Commerce & Marketplaces
    reports_to: CCO

  - id: MKTG
    name: Kwame Owusu
    role_title: VP Brand & Marketing
    level: Function
    org_unit: Brand & Marketing
    reports_to: CCO

  # Operations (under COO) ---------------------------------------------------
  - id: STORE_OPS
    name: Sophie Dubois
    role_title: VP Store Operations
    level: Function
    org_unit: Store Operations
    reports_to: COO

  - id: SUPPLY_CHAIN
    name: Tomasz Wójcik
    role_title: VP Supply Chain & Logistics
    level: Function
    org_unit: Supply Chain & Logistics
    reports_to: COO

  - id: INVENTORY
    name: Fatima Al-Hariri
    role_title: Director Inventory Management
    level: Function
    org_unit: Inventory Management
    reports_to: COO

  - id: CUSTOMER_SERVICE
    name: Samuel Adeyemi
    role_title: Director Customer Service & Returns
    level: Function
    org_unit: Customer Service & Returns
    reports_to: COO

  # Technology & Data (under CIO) -------------------------------------------
  - id: CORE_IT
    name: Jakub Novak
    role_title: VP Core IT Platforms
    level: Function
    org_unit: ERP, POS & Core Systems
    reports_to: CIO

  - id: INFRA_SEC
    name: Helena Campos
    role_title: VP Infrastructure & Cyber Security
    level: Function
    org_unit: Infrastructure & Cyber Security
    reports_to: CIO

  - id: DATA_AI
    name: Dilan Yılmaz
    role_title: VP Data, Analytics & AI
    level: Function
    org_unit: Data, Analytics & AI
    reports_to: CIO

  # Finance (under CFO) ------------------------------------------------------
  - id: FIN_CONTROLLING
    name: Mark O’Connor
    role_title: VP Finance & Controlling
    level: Function
    org_unit: Finance & Controlling
    reports_to: CFO

  - id: FPNA
    name: Yu Chen
    role_title: Director Financial Planning & Analysis
    level: Function
    org_unit: FP&A
    reports_to: CFO

  # People & Culture (under CHRO) -------------------------------------------
  - id: PEOPLE_TALENT
    name: Thandi Mbeki
    role_title: VP People & Talent
    level: Function
    org_unit: Talent & Development
    reports_to: CHRO

  # ESG (under CSO) ----------------------------------------------------------
  - id: ESG_STRATEGY
    name: Lars Henriksen
    role_title: Director ESG Strategy & Reporting
    level: Function
    org_unit: ESG Strategy & Reporting
    reports_to: CSO

  # Regions (under COO) ------------------------------------------------------
  - id: REG_DACH
    name: Katharina Steiner
    role_title: Regional Managing Director DACH
    level: Region
    org_unit: Region DACH
    reports_to: COO
    markets: [Germany, Austria, Switzerland]

  - id: REG_BENELUX
    name: Jeroen van Dijk
    role_title: Regional Managing Director Benelux
    level: Region
    org_unit: Region Benelux
    reports_to: COO
    markets: [Belgium, Netherlands, Luxembourg]

  - id: REG_NORDICS
    name: Anneli Virtanen
    role_title: Regional Managing Director Nordics
    level: Region
    org_unit: Region Nordics
    reports_to: COO
    markets: [Sweden, Denmark, Norway, Finland]

  - id: REG_SOUTH
    name: Marco Santoro
    role_title: Regional Managing Director Southern Europe
    level: Region
    org_unit: Region Southern Europe
    reports_to: COO
    markets: [Italy, Spain, Portugal, Greece]

  - id: REG_CEE
    name: Petra Kovács
    role_title: Regional Managing Director CEE
    level: Region
    org_unit: Region Central & Eastern Europe
    reports_to: COO
    markets: [Poland, Czech Republic, Hungary, Slovakia]

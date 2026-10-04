# Retail Business Growth & Vendor Intelligence Platform

An end-to-end **Retail Business Intelligence and Analytics Platform** designed to help retail businesses analyze sales, purchases, vendors, stores, products, inventory, forecasts, and business opportunities.

The project combines **Python, SQL, MySQL, ETL, analytics, Power BI, machine-learning forecasting, business recommendations, Flask APIs, and role-based authentication** into a single analytics platform.

---

## 1. Project Overview

Retail businesses generate large amounts of sales, purchase, inventory, vendor, store, and product data.

Analyzing these datasets separately can make it difficult for business owners and decision-makers to understand:

* How the business is performing
* Which vendors generate the most value
* Which stores perform better
* Which products contribute the most sales
* Where inventory risks exist
* How purchases compare with sales
* What future sales may look like
* Where business opportunities exist
* Which products may require inventory attention

This project addresses these challenges by building an end-to-end data analytics and business intelligence platform.

---

## 2. Business Problem

The objective is to transform raw retail datasets into actionable business insights.

The platform provides analysis across:

* Business performance
* Sales
* Purchases
* Vendors
* Stores
* Products
* Inventory
* Forecasting
* Business opportunities
* Recommendations

The final solution provides both:

1. **Business intelligence and visualization** through Power BI
2. **Application/API-based access** through Flask

---

## 3. Project Objectives

The major objectives of the project are:

* Perform exploratory data analysis on raw retail datasets
* Clean and transform data using Python
* Design and populate a MySQL database
* Build reusable ETL pipelines
* Develop SQL-based business KPIs
* Analyze vendor performance
* Analyze store performance
* Analyze product performance
* Analyze inventory movement and risk
* Build business opportunity intelligence
* Develop a sales forecasting component
* Build a rule-based recommendation engine
* Create interactive Power BI dashboards
* Develop Flask APIs for analytical data
* Implement authentication and role-based access
* Provide separate owner and vendor views

---

# 4. End-to-End Architecture

```text
Raw CSV Data
     |
     v
Data Exploration & Data Quality Checks
     |
     v
Python ETL Pipeline
     |
     v
MySQL Database
     |
     +--------------------+
     |                    |
     v                    v
SQL Business KPIs     Python Analytics
                           |
                           +------------------+
                           |                  |
                           v                  v
                    Intelligence        Forecasting
                           |
                           v
                  Recommendation Engine
                           |
             +-------------+-------------+
             |                           |
             v                           v
        Power BI                    Flask APIs
        Dashboards                       |
                                         v
                              Web Dashboard + Auth
```

---

# 5. Technology Stack

| Technology    | Purpose                                        |
| ------------- | ---------------------------------------------- |
| Python        | Data processing, ETL and analytics             |
| Pandas        | Data cleaning, transformation and analysis     |
| NumPy         | Numerical operations                           |
| Matplotlib    | Data visualization during analysis             |
| Seaborn       | Statistical visualization during analysis      |
| SQL           | Business queries and KPI calculations          |
| MySQL         | Relational database                            |
| SQLAlchemy    | Database connectivity                          |
| PyMySQL       | MySQL database driver                          |
| Python-dotenv | Environment variable management                |
| Scikit-learn  | Machine-learning functionality and forecasting |
| Flask         | Backend APIs and web application               |
| Power BI      | Interactive business intelligence dashboards   |
| Jupyter       | Exploratory analysis and experimentation       |
| OpenPyXL      | Excel file processing                          |
| Git/GitHub    | Version control and project management         |

---

# 6. Project Workflow

The project was implemented through the following stages:

### Phase 1 — Business & Project Understanding

Defined the retail business problem, analytical requirements, users, objectives and expected outputs.

### Phase 2 — Environment & Folder Setup

Created the project structure, Python virtual environment and required dependencies.

### Phase 3 — Exploratory Data Analysis

Examined the raw datasets for:

* Missing values
* Duplicates
* Data types
* Unique values
* Distributions
* Outliers
* Data quality issues

### Phase 4 — Data Relationships & Data Model

Identified relationships between:

* Businesses
* Vendors
* Stores
* Products
* Sales
* Purchases
* Inventory

### Phase 5 — MySQL Database Design

Designed the relational database and created the required tables.

### Phase 6 — ETL Pipeline

Built Python-based extraction, transformation and loading processes.

### Phase 7 — Master Data Loading

Loaded master entities such as:

* Businesses
* Vendors
* Stores
* Products
* Users

### Phase 8 — Fact Data Loading

Loaded transactional datasets including:

* Sales
* Purchases
* Vendor invoices
* Beginning inventory
* Ending inventory

### Phase 9 — SQL KPI & Business Analytics

Developed SQL queries for major business metrics including:

* Sales quantity
* Sales revenue
* Purchase quantity
* Purchase spending
* Inventory quantity
* Inventory value
* Sales and purchase comparisons

### Phase 10 — Business Intelligence & Intelligence Layers

Developed analytical modules for:

* Vendor intelligence
* Store intelligence
* Product intelligence
* Inventory intelligence
* Business opportunities
* Cross-business intelligence

### Phase 11 — Power BI Dashboard

Created a multi-page Power BI dashboard for interactive business analysis.

### Phase 12 — Sales Forecasting

Developed a machine-learning forecasting component to estimate future sales.

### Phase 13 — Business Recommendations

Created a rule-based recommendation engine using business and inventory signals.

### Phase 14 — Flask Backend

Developed Flask APIs to expose business intelligence data.

### Phase 15 — Authentication & Role-Based Access

Implemented authentication with separate:

* Owner access
* Vendor access

### Phase 16 — Web Dashboard & Integration

Integrated Flask APIs with the web dashboard and completed owner/vendor testing.

---

# 7. Dataset & Data Processing

The project works with multiple retail datasets covering sales, purchases, inventory, vendors, products and stores.

Major source datasets include:

* Sales
* Purchases
* Purchase prices
* Vendor invoices
* Beginning inventory
* Ending inventory

The ETL process transforms the raw data into structured datasets suitable for:

* Database storage
* SQL analytics
* Power BI
* Forecasting
* Recommendation generation
* Flask APIs

---

# 8. Database

The project uses **MySQL** as the central relational database.

### Main tables

```text
businesses
vendors
stores
products
sales
purchases
vendor_invoices
begin_inventory
end_inventory
users
```

The database provides a centralized source for business analytics and application APIs.

---

# 9. Analytics Modules

The `analytics/` directory contains reusable Python analytical modules covering multiple business areas.

### Sales Analytics

Includes:

* Monthly sales
* Sales growth
* Sales distribution
* Sales by city
* Sales by weekday
* Sales outlier analysis
* Sales performance

### Purchase Analytics

Includes:

* Purchase KPIs
* Purchase by vendor
* Purchase by store
* Purchase price analysis
* Purchase price matching
* Purchase vs sales analysis

### Vendor Analytics

Includes:

* Vendor sales
* Vendor sales performance
* Vendor purchase performance
* Vendor sales vs purchase
* Vendor performance segmentation
* Vendor intelligence

### Store Analytics

Includes:

* Store sales
* Store sales contribution
* Store sales performance
* Store purchase performance
* Store purchase vs sales
* Store inventory analysis
* Store performance segmentation
* Store intelligence

### Product Analytics

Includes:

* Product sales
* Product sales contribution
* Product sales performance
* Product purchase performance
* Product purchase vs sales
* Product inventory analysis
* Product performance segmentation
* Product intelligence

### Inventory Analytics

Includes:

* Beginning vs ending inventory
* Inventory quantity change
* Inventory value analysis
* Inventory risk analysis
* Inventory intelligence

### Business Intelligence

Includes:

* Overall KPIs
* Business health indicators
* Business opportunity intelligence
* Cross-intelligence analysis
* Business recommendation intelligence

---

# 10. Power BI Dashboard

The Power BI report contains **10 analytical pages**.

### Page 1 — Executive Dashboard

Provides an overall view of business performance and major KPIs.

### Page 2 — Sales Performance

Analyzes sales revenue, sales quantity and sales trends.

### Page 3 — Purchase Performance

Analyzes purchase quantity, spending and purchasing performance.

### Page 4 — Vendor Intelligence

Provides vendor-level performance and business insights.

### Page 5 — Store Intelligence

Analyzes store-level sales, purchases and performance.

### Page 6 — Product & Inventory Intelligence

Provides product-level and inventory-related insights.

### Page 7 — Inventory & Risk

Highlights inventory movement and potential inventory risks.

### Page 8 — Business Opportunities

Identifies products/business areas that may require attention or action.

### Page 9 — Sales Forecasting

Displays forecasted future sales values.

### Page 10 — Recommendation Engine

Displays business recommendations and priority levels.

The Power BI `.pbix` file is maintained separately because of its large binary file size.

---

# 11. Sales Forecasting

The project includes a sales forecasting component that generates future sales estimates.

Example forecast output:

| Month         | Forecast Sales |
| ------------- | -------------: |
| January 2025  | $48,542,321.51 |
| February 2025 | $50,214,692.11 |
| March 2025    | $51,887,062.70 |

The forecast output is stored in:

```text
data/processed/sales_forecast.csv
```

The forecasting component can help management with:

* Sales planning
* Inventory planning
* Purchasing decisions
* Resource planning

---

# 12. Recommendation Engine

The recommendation engine uses **business rules and analytical signals** to generate actionable recommendations.

Major recommendation categories include:

* Performance Monitoring
* Purchasing Review
* Inventory Replenishment
* Low Activity Review
* Inventory Optimization
* Replenishment
* Risk Monitoring

Recommendations are also assigned priority levels:

* High
* Medium
* Normal
* Low

The rule-based approach provides transparent and explainable recommendations that can be validated against business conditions.

---

# 13. Flask Backend

The Flask application provides APIs for accessing analytical information.

### Main API endpoints

```text
/api/db-test
/api/kpis
/api/sales
/api/purchases
/api/vendors
/api/stores
/api/products
/api/inventory
/api/recommendations
/api/forecast
```

Vendor-specific APIs include:

```text
/api/my-vendor
/api/my-vendor/recommendations
```

The APIs connect the analytical layer with the web application.

---

# 14. Authentication & Role-Based Access

The application supports two user roles:

### Owner

The owner can access overall business intelligence including:

* Business KPIs
* Sales
* Purchases
* Vendors
* Stores
* Products
* Inventory
* Forecasting
* Recommendations

### Vendor

A vendor can access vendor-specific information such as:

* Vendor performance
* Vendor purchase metrics
* Vendor sales metrics
* Vendor recommendations

Role-based authorization prevents vendor users from accessing owner-only functionality.

---

# 15. Web Dashboard

The Flask web application provides:

* Login page
* Authentication
* Owner dashboard
* Vendor dashboard
* KPI cards
* Sales performance
* Purchase performance
* Vendor intelligence
* Store intelligence
* Inventory intelligence
* Sales forecasting
* Business recommendations

The web dashboard communicates with the Flask API layer to retrieve analytical information.

---

# 16. Project Structure

```text
Retail-Business-Intelligence/
│
├── analytics/
│   ├── business_health_indicators.py
│   ├── business_opportunity_intelligence.py
│   ├── business_recommendation_intelligence.py
│   ├── forecasting.py
│   ├── inventory_intelligence.py
│   ├── product_intelligence.py
│   ├── recommendation_engine.py
│   ├── store_intelligence.py
│   ├── vendor_intelligence.py
│   └── ...
│
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   └── auth.py
│   └── templates/
│       ├── dashboard.html
│       └── login.html
│
├── data/
│   └── processed/
│       ├── business_opportunity_intelligence.csv
│       ├── business_recommendation_intelligence.csv
│       ├── inventory_intelligence.csv
│       ├── product_intelligence.csv
│       ├── recommendation_engine.csv
│       ├── sales_forecast.csv
│       ├── store_intelligence.csv
│       ├── vendor_intelligence.csv
│       └── ...
│
├── database/
│
├── docs/
│
├── etl/
│
├── models/
│
├── notebooks/
│
├── recommendations/
│
├── reports/
│
├── tests/
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 17. Installation

Clone the repository and navigate into the project:

```bash
git clone https://github.com/AmmajiShaik06/Retail-Business-Intelligence.git

cd Retail-Business-Intelligence
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 18. Environment Configuration

Database credentials are managed using environment variables.

Create a local `.env` file with the required database configuration.

Example structure:

```text
DB_HOST=localhost
DB_PORT=3306
DB_NAME=retail_business_intelligence
DB_USER=your_username
DB_PASSWORD=your_password
```

Do not commit `.env` to GitHub.

---

# 19. Running the Flask Application

After configuring the database and environment variables:

```bash
python -m flask --app app run
```

The application runs locally using Flask's development server.

The API can then be accessed through the application endpoints.

---

# 20. Key Business Results

The completed analytical platform produced the following business-level metrics:

| Metric                       |           Value |
| ---------------------------- | --------------: |
| Total Sales Revenue          | $452,062,952.02 |
| Total Sales Quantity         |      32,917,876 |
| Total Purchase Spending      | $321,900,765.53 |
| Total Purchase Quantity      |      33,584,377 |
| Beginning Inventory Quantity |       4,219,275 |
| Ending Inventory Quantity    |       4,885,776 |

These metrics provide a high-level view of business activity across the analyzed retail data.

---

# 21. Key Analytical Insights

The platform supports analysis of:

* Sales and purchase relationships
* Vendor contribution
* Store performance
* Product performance
* Inventory changes
* Inventory risk
* Business opportunities
* Future sales expectations
* Actionable recommendations

The platform is designed to convert transactional data into information that can support operational and management decisions.

---

# 22. Data Quality Considerations

During data exploration and preparation, several real-world data-quality challenges were identified, including:

* Missing values
* Duplicate identifiers
* Vendor naming inconsistencies
* Product matching issues
* Multiple transaction lines associated with the same purchase order
* Differences between analytical product combinations and master product entities

Rather than blindly removing duplicates, the project evaluates duplicates according to their business meaning.

---

# 23. Limitations

Current limitations include:

* Forecast accuracy depends on the available historical data.
* Recommendations are primarily rule-based rather than fully machine-learning driven.
* The Flask application is designed as a local/development application rather than a production deployment.
* Power BI is maintained as a separate `.pbix` report.
* Future versions could incorporate real-time data pipelines.
* Recommendation quality could be improved using historical outcome feedback.

---

# 24. Future Improvements

Possible future enhancements include:

* Deploy Flask application to a cloud platform
* Add real-time or scheduled ETL pipelines
* Add advanced forecasting models
* Introduce ML-based recommendation models
* Add automated anomaly detection
* Add more granular role and permission management
* Add automated dashboard refresh
* Add monitoring and logging
* Improve API security
* Containerize the application using Docker
* Add CI/CD using GitHub Actions

---

# 25. Project Status

**Project Status: Completed**

All major implementation phases have been completed:

```text
Phase 1  → Business Understanding                 ✅
Phase 2  → Environment Setup                      ✅
Phase 3  → EDA                                   ✅
Phase 4  → Data Relationships & Modeling          ✅
Phase 5  → MySQL Database Design                  ✅
Phase 6  → ETL Pipeline                           ✅
Phase 7  → Master Data Loading                    ✅
Phase 8  → Fact Data Loading                      ✅
Phase 9  → SQL KPI & Business Analytics           ✅
Phase 10 → Intelligence Layer                     ✅
Phase 11 → Power BI Dashboard                     ✅
Phase 12 → Sales Forecasting                      ✅
Phase 13 → Business Recommendations               ✅
Phase 14 → Flask Backend                          ✅
Phase 15 → Authentication & RBAC                  ✅
Phase 16 → Web Dashboard & Integration            ✅
```

---

# 26. Portfolio Value

This project demonstrates practical skills in:

* Data Analysis
* Python
* Pandas
* SQL
* MySQL
* ETL
* Data Cleaning
* Exploratory Data Analysis
* Business Intelligence
* Power BI
* Data Visualization
* Machine Learning
* Forecasting
* Business Recommendation Systems
* Flask API Development
* Authentication
* Role-Based Access Control
* Git and GitHub

The project demonstrates an end-to-end workflow from **raw data to business insights and an analytical web application**.

# mexico-team-8
## Abstract
## Introduction
## Data Engineering
## Infrastructure
## Application
### Database Creation
#### a) Create CSVs temporary files

**CreaCSVs.ipyb** creates 7 temporary files from the files obtained in the data cleaning process
- PatentDrug.csv, Request.csv, RequestMedCode.csv, PurchaseOrder.csv, POReqMedCode.csv, PatientCosumption.csv, PatConsMedCode.csv

#### b) Create Database

**CreateDB.ipyb** creates the tables in the PostgreSQL Database from the temporary files, according with the next image:

![alt text](CreateCSVsDB/DB%20design.png "Database")

### Web Site
#### a) Includinding the Web Application Framework Django to build the Web Site and permit manages the information and produces reports, the directory Django contains the files to enable the environment.

#### b) Dash Framework is integrated to Django to create the Dashboards with themes called layouts. The graphs are integrated with Plotly python structure code, in the directory dash_apps.

## 4. Data Analysis and Computation
## 5. Conclusions and Future Work

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
#### a) Web Application Framework Django:
To build the Web Site that permits manage the information and produce reports, the directory Django contains the files to enable the environment.

#### b) Dash Framework:
Is integrated to Django to create the Dashboards with themes called layouts. The graphs are integrated with Plotly python structure code, in the directory dash_apps.

### Run Server

In Django/Dalinde directory run:
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

View the Web site at http://<host_name>:8000/

## 4. Data Analysis and Computation
## 5. Conclusions and Future Work

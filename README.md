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

**CreateDB.ipyb** creates the tables in the PostgreSQL Database from the temporary files, according with the Database design included in the next image:

![alt text](CreateCSVsDB/DB%20design.png "Database")

### Web Site
#### a) Web Application Framework Django:
The directory Django contains the files to enable the environment, the Web Site permits manage the information and produce reports.

#### b) Dash Framework:
It's integrated to Django to create the Dashboards with themes called layouts. The graphs are integrated with Plotly python structure code, wich is included in the directory dash_apps.

### Run Server

In Django/Dalinde directory run:
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

View the Web site at http://<host_name>:8000/

## Data Analysis and Computation

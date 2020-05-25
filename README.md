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

**Requirements**
- Intall python
- Add Packages: dash 1.10.0, django 3.0.3, django-plotly-dash 1.3.1, gekko 0.2.6, matplotlib 3.1.3, numpy                1.18.4, pandas 1.0.3, plotly 4.7.1, psycopg2 2.8.4, sqlalchemy 1.3.16

In Django/Dalinde directory run:
- python manage.py makemigrations
- python manage.py migrate
- python manage.py runserver

View the Web site at http://<host_name>:8000/

## Data Analysis and Computation

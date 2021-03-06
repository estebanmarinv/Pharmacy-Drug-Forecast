# Demand Forecast & Inventory Control of Pharmaceutical Drugs

This repository keeps track of the code for the Team 8 Mexico final project for DS4A-Latam 2020 parts where I was involved.

## Application
### Database Creation
#### a) Create CSVs temporary files

**CreaCSVs.ipyb** creates 7 temporary files from the files obtained in the data cleaning process
- PatentDrug.csv, Request.csv, RequestMedCode.csv, PurchaseOrder.csv, POReqMedCode.csv, PatientCosumption.csv, PatConsMedCode.csv

#### b) Create Database

**CreateDB.ipyb** creates the tables in the PostgreSQL Database from the temporary files, according with the Database design included in the next image:

## Data Analysis

### Data cleaning

Data cleaning is documented in the file [data_cleaner.ipynb](data-analysis/data_cleaner.ipynb). This notebook takes a series of Excel files from [data-analysis/data/](data-analysis/data/) and [data-analysis/data_2020](data-analysis/data2020/) and outputs a group of CSV files needed for the Exploratory Data Analysis.

### Exploratory Data Analysis

Exploratory Data Analysis is documented in the notebook [EDA.ipynb](data-analysis/EDA.ipynb). This notebook takes the CSV files generated by the data cleaner and explains the process of the data exploration and discusses relevant findings.

## Modeling

### ARIMA model

The notebook [ARIMA_model.ipynb](modeling/ARIMA_model.ipynb) uses the TOP 9 MedCodes produced in the [EDA.ipynb](data-analysis/EDA.ipynb) Jupyter Notebook.

The code provided here computes the 9 ARIMA models for each of the time series, and outputs CSV files with the results. 


## Model comparison

A comparison between the modeling approaches was made. This is documented in the file [model_comparison.ipynb](modeling/model_comparison.ipynb).


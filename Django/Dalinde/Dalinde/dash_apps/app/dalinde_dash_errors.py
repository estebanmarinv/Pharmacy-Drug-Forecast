# PENDIENTE Solucion Callback_Context en Djanjo-Dash
# v2.0
# Para subir a Django, solo puede cambiar una vez entre REQUESTED vs MISSINGS
# * Add AVG, MIN y MAX de Request by Pharmacy in a Period
# Intercambiar Pie Missings vs Pie Requests
# Correccion de Missings
#v3.0
# Inclusion de PID para cada MedCode con los 2 años

from django_plotly_dash import DjangoDash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
from sqlalchemy import create_engine, text
import warnings
from gekko import GEKKO
import numpy as np
import datetime
import os
import plotly.graph_objects as go

warnings.simplefilter(action='ignore', category=FutureWarning)
#Inicia Dash - APP 'Dalinde'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = DjangoDash('dalinde_dash_error', external_stylesheets=external_stylesheets)


#Conexion a la Base de Datos
pd.options.display.max_rows = 20
engine=create_engine('postgresql://postgres:Ds4_MX_2020@54.184.252.64/DalindeDB', max_overflow=30)

def runQuery(sql):
    result = engine.connect().execution_options(isolation_level="AUTOCOMMIT").execute((text(sql)))
    return pd.DataFrame(result.fetchall(), columns=result.keys())

def TraeMedCodeBD():
    Query = """
        Select * FROM "PatentDrug"
    ;"""
    MedCode = runQuery(Query)

    return MedCode

MC = TraeMedCodeBD()
forecasts = pd.read_csv('./Dalinde/dash_apps/app/assets/forecasts.csv').set_index('Month')
errors    = pd.read_csv('./Dalinde/dash_apps/app/assets/prediction_errors.csv').set_index('Month')

#---------------------- OVERAL ERRORS
# Average errors for every drug and make a boxplot of errors per model
error_overall = errors.groupby('MedCode').mean()

mae_overall = go.Figure()
mape_overall = go.Figure()

for model in ['Mean','ARIMA','RNN']:
    # MAE
    mae_model = error_overall[model+'_AbsError']
    mae_overall.add_trace(go.Box(y=mae_model, name=model))
    # MAPE
    mape_model = error_overall[model+'_PerError']
    mape_overall.add_trace(go.Box(y=mape_model, name=model))

mae_overall.update_layout(title='Overall MAE per model',
                          xaxis_title='Prediction model',
                          yaxis_title='Mean Absolute Error',
                          autosize=False, width=600, height=450)
mape_overall.update_layout(title='Overall MAPE per model',
                           xaxis_title='Prediction model',
                           yaxis_title='Mean Absolute Percentage Error [%]',
                           autosize=False, width=600, height=450)
#mae_overall.show()
#mape_overall.show()

#---------------------- ERRORS PER MONTH
# Group errors by month

mae_monthly = go.Figure()
mape_monthly = go.Figure()

for model in ['Mean','ARIMA','RNN']:
    # MAE
    mae_model = errors[model+'_AbsError']
    mae_monthly.add_trace(go.Box(x=errors.index.str[:-3], y=mae_model, name=model))
    # MAPE
    mape_model = errors[model+'_PerError']
    mape_monthly.add_trace(go.Box(x=errors.index.str[:-3], y=mape_model, name=model))

mae_monthly.update_layout(title='Forecast MAE per month',
                          boxmode='group', xaxis_type='category',
                          xaxis_title='Forecasted month',
                          yaxis_title='Mean Absolute Error',
                          autosize=False, width=600, height=450)
mape_monthly.update_layout(title='Forecast MAPE per month',
                           boxmode='group', xaxis_type='category',
                           xaxis_title='Forecasted month',
                           yaxis_title='Mean Absolute Percentage Error [%]',
                           autosize=False, width=600, height=450)
#mae_monthly.show()
#mape_monthly.show()


#---------------------- AVERAGE ERRORS PER MONTH
# Average errors per month

error_avg = errors.groupby(errors.index).mean()

avg_mae_monthly = go.Figure()
avg_mape_monthly = go.Figure()

for model in ['Mean','ARIMA','RNN']:
    # MAE
    avg_mae_model = error_avg[model+'_AbsError']
    avg_mae_monthly.add_trace(go.Scatter(x=error_avg.index.str[:-3], y=avg_mae_model, mode='lines+markers', name=model))
    # MAPE
    avg_mape_model = error_avg[model+'_PerError']
    avg_mape_monthly.add_trace(go.Scatter(x=error_avg.index.str[:-3], y=avg_mape_model, mode='lines+markers', name=model))

avg_mae_monthly.update_layout(title='Average Forecast MAE per month',
                          boxmode='group', xaxis_type='category',
                          xaxis_title='Forecasted month',
                          yaxis_title='Average MAE',
                          autosize=False, width=600, height=450)
avg_mape_monthly.update_layout(title='Average Forecast MAPE per month',
                           boxmode='group', xaxis_type='category',
                           xaxis_title='Forecasted month',
                           yaxis_title='Average MAPE [%]',
                           autosize=False, width=600, height=450)
#avg_mae_monthly.show()
#avg_mape_monthly.show()

#---------------------- GRAFICAS DASH
app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='/static/css/dash.css'
    ),
        html.Div([
            html.H3('Overall Errors'),
            html.Div(className="graph-child", children=[
                dcc.Graph(figure=mae_overall),
            ], style={'display': 'inline-block', 'width': '50%'}),
            html.Div(className="graph-child", children=[    
                dcc.Graph(figure=mape_overall),
            ], style={'display': 'inline-block', 'width': '50%'}),
        ]),

        html.Div([
            html.H3('Errors per Month'),
            html.Div(className="graph-child", children=[
                dcc.Graph(figure=mae_monthly),
            ], style={'display': 'inline-block', 'width': '50%'}),
            html.Div(className="graph-child", children=[
                dcc.Graph(figure=mape_monthly),
            ], style={'display': 'inline-block', 'width': '50%'}),
        ]),

        html.Div([
            html.H3('Average Errors per Month'),
            html.Div(className="graph-child", children=[
                dcc.Graph(figure=avg_mae_monthly),
            ], style={'display': 'inline-block', 'width': '50%'}),
            html.Div(className="graph-child", children=[    
                dcc.Graph(figure=avg_mape_monthly),
            ], style={'display': 'inline-block', 'width': '50%'}),
        ]),
        ])


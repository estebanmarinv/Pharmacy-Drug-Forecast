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
app = DjangoDash('dalinde_dash_top9', external_stylesheets=external_stylesheets)

Top9=[3300663, 3301778, 3301771, 3302307, 3300115, 3300142, 3302934, 3500322, 3302669]

#Conexion a la Base de Datos
pd.options.display.max_rows = 20
engine=create_engine('postgresql://postgres:Ds4_MX_2020@54.184.252.64/DalindeDB', max_overflow=30)

def runQuery(sql):
    result = engine.connect().execution_options(isolation_level="AUTOCOMMIT").execute((text(sql)))
    return pd.DataFrame(result.fetchall(), columns=result.keys())

def TraeBDPO():
    Query = """
        SELECT porqmc.*, po."SupplierName", po."OrderDate", po."RequiredDeliveryDate"
        FROM
        (SELECT pormc."MedCode",pormc."PurchaseNumber", pormc."RequestNumber",
            rqmc."RequestDate", rqmc."AmountRequested",
            pormc."AmountPurchased", pormc."AmountReceived", rqmc."WeekDay"
        FROM "POReqMedCode" pormc
        JOIN
        (SELECT rmc."MedCode", rmc."RequestNumber", rmc."AmountRequested",
                rq."RequestDate", date_part('dow', rq."RequestDate") AS "WeekDay"
        FROM "RequestMedCode" AS rmc
        JOIN (SELECT r."RequestNumber", r."RequestDate" FROM "Request" AS r) AS rq
        ON rq."RequestNumber" = rmc."RequestNumber") AS rqmc
        ON pormc."RequestNumber" = rqmc."RequestNumber" AND
        pormc."MedCode" = rqmc."MedCode"
        ) as porqmc
        JOIN "PurchaseOrder" as po ON po."PurchaseNumber" = porqmc."PurchaseNumber"
        ;"""
    MedCode_All = runQuery(Query)
    return MedCode_All

def TraeMedCodeBD():
    Query = """
        Select * FROM "PatentDrug"
    ;"""
    MedCode = runQuery(Query)

    return MedCode

def TraeFaltantes():
    Query = """
    SELECT *, date_part('dow', t."RequestDate") AS "WeekDay"
    FROM
    (
    SELECT rmc."RequestNumber", rmc."MedCode", rmc."AmountRequested",
        (SELECT r."RequestDate" FROM "Request" as r WHERE r."RequestNumber" = rmc."RequestNumber")
    FROM "RequestMedCode" as rmc
    WHERE NOT EXISTS
    (SELECT * FROM "POReqMedCode" as pormc 
        WHERE pormc."RequestNumber" = rmc."RequestNumber" 
        AND pormc."MedCode" = rmc."MedCode")) as t
    ;"""
    
    Faltan = runQuery(Query)
    Faltan['PurchaseNumber']=0
    Faltan['AmountPurchased']=0
    Faltan['AmountReceived']=0

    return Faltan

def AjustaBD():
    global BDPO

    BDM = BDPO.copy()
    BDM.drop(['SupplierName', 'OrderDate', 'RequiredDeliveryDate'], axis=1, inplace=True)
    # Primera parte Creacion de BD(Request) + #PUCHASE ORDERS
    BD = pd.DataFrame()
    BD = BDM.groupby(['RequestNumber', 'MedCode','AmountRequested','RequestDate', 'WeekDay'])['PurchaseNumber'].count()
    BD = BD.reset_index()
    BD.reset_index(inplace=True, drop=True)

    #Segunda Parte, suma de las Amount Purchased
    BDAP = BDM.groupby(['RequestNumber', 'MedCode'])['AmountPurchased'].sum()
    BDAP = BDAP.reset_index()
    #Tercera Parte, suma de las Amount Received
    BDAR = BDM.groupby(['RequestNumber', 'MedCode'])['AmountReceived'].sum()
    BDAR = BDAR.reset_index()

    BD['AmountPurchased'] = BDAP[(BDAP['RequestNumber']==BD['RequestNumber']) & (BDAP['MedCode']==BD['MedCode'])]['AmountPurchased']
    BD['AmountReceived'] = BDAR[(BDAR['RequestNumber']==BD['RequestNumber']) & (BDAR['MedCode']==BD['MedCode'])]['AmountReceived']

    Faltantes = TraeFaltantes()
    BD = BD.append(Faltantes, ignore_index = True)
    BD['AmountMissing'] = BD['AmountRequested']-BD['AmountReceived']
    BD.sort_values(['RequestDate', 'RequestNumber', 'MedCode'], ascending=[True, True, True], inplace=True)
    BD.reset_index(inplace=True, drop=True)

    return(BD)

BDPO = TraeBDPO()
BDT = AjustaBD()
MC = TraeMedCodeBD()
Forecast = pd.read_csv('./Dalinde/dash_apps/app/assets/forecasts.csv')
Errors = pd.read_csv('./Dalinde/dash_apps/app/assets/prediction_errors.csv')
PDI = pd.read_csv('./Dalinde/dash_apps/app/assets/pdi_top9.csv')
#NeuralNet = pd.read_csv('./Dalinde/dash_apps/app/assets/NeuralNetPredictions2020.csv')

def WeekYear(Fecha):
    inicio = datetime.datetime(2018, 1, 1)
    siguiente = datetime.datetime(Fecha.year, Fecha.month, Fecha.day)
    return(int(abs(siguiente - inicio).days/7))

app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='/static/css/dash.css'
    ),
        html.Div(id="dash-head", className='dash-sec', children=[
            html.Div([
                 html.H3('Periodo'),
                dcc.RadioItems(id='periodo',
                    options=[{'label': c, 'value': c} for c in ['2Y', '1Y', '9M', '6M', '3M', '1M']],
                    value='2Y', labelStyle={'display':'inline-block'})
            ], style={'display': 'inline-block', 'width': '50%'}),

            html.Div([
                html.H3('Error'),
                dcc.RadioItems(id='error',
                    options=[{'label': c, 'value': c} for c in ['MAE', 'MAPE']],
                    value='MAE', labelStyle={'display':'inline-block'}),
            ], style={'display': 'inline-block', 'width': '50%'}),
               
            ]),

        html.Div(className="overborder", children=[
                html.Div([html.P(id='mis-tot'),],
                    style={'display': 'inline-block', 'width': '33%', 'color':'#FFF', 'background-color':'#666'}),
                html.Div([html.P(id='mis-top9'),],
                    style={'display': 'inline-block', 'width': '33%', 'color':'#FFF', 'background-color':'#606'}),
                html.Div([html.P(id='porcentaje'),],
                    style={'display': 'inline-block', 'width': '33%', 'color':'#FFF', 'background-color':'#333'}),
            ]),
        html.Div(className="dual-graph", children=[
                html.Div(className="graph-child", children=[
                    dcc.Graph(id='pie-toptenM')
                ], style={'display': 'inline-block', 'width': '50%'}),
                html.Div(className="graph-child", children=[
                    dcc.Graph(id='bar-error')
            ], style={'display': 'inline-block', 'width': '50%'}),
        ]),
        
        html.Div(className="single-graph", children=[
                dcc.Graph(id='forecast-graph')
        ]),

        html.Div(className="single-graph", children=[
                dcc.Graph(id='pdi-graph')
        ]),
])

#Periodo a revisar
def RevisaPeriodo(value):

    if (value == '2Y'):
        StartDate = '2018-01-01'
    elif (value == '1Y'):
        StartDate = '2019-01-01'
    elif (value == '9M'):
        StartDate = '2019-04-01'
    elif (value == '6M'):
        StartDate = '2019-07-01'
    elif (value == '3M'):
        StartDate = '2019-10-01'
    elif (value == '1M'):
        StartDate = '2019-12-01'
    
    return StartDate

def TraePrecio(medcode):
    global MC
    
    MCD = MC.copy()
    MCD['MedCode'] = MCD['MedCode'].astype(str)
    MCD = MCD[MCD['MedCode'].isin([str(medcode)])]
    Lista = MCD.values.tolist()
    Precio = Lista[0][4]

    return Precio

def TraePharmacon(medcode):
    global MC
    
    MCD = MC.copy()
    MCD['MedCode'] = MCD['MedCode'].astype(str)
    MCD = MCD[MCD['MedCode'].isin([str(medcode)])]
    Lista = MCD.values.tolist()
    Pharmacon = Lista[0][1].split()[0]

    return Pharmacon

def TraeTotal(start_date, Type):
    global Top9, BDT

    PD = BDT.copy()
    if Type=='Top9':
        PD = PD[PD['MedCode'].isin(Top9)]
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    PD = PD[PD['AmountMissing'] > 0]
    PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].sum()
    PD = pd.DataFrame(PD)
    Sum = 0
    for row in PD.iterrows():
            Sum = Sum+row[1].AmountMissing*TraePrecio(row[1].MedCode)

    return Sum

def TraeMTop9(start_date):
    global BDT

    PD = BDT.copy()
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    PD = PD[PD['MedCode'].isin(Top9)]
    PD = PD[PD['AmountMissing'] > 0]
    PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].sum()
    PD.sort_values('AmountMissing', ascending=False,  inplace=True)

    PD['Pharmacon'] = PD['MedCode'].apply(lambda x: TraePharmacon(x))

    return PD

def TraeMCDesc(medcode):
    global MC

    MCD = MC.copy()
    MCD['MedCode'] = MCD['MedCode'].astype(str)
    MCD = MCD[MCD['MedCode']==str(medcode)]
    Patente = MCD['MedDescription'].values.tolist()

    return Patente[0]

@app.callback(
    Output('porcentaje', 'children'),
    [Input('periodo', 'value'),])
def update_porcentaje(value):
    Periodo = RevisaPeriodo(value)
    MisTop9= TraeTotal(Periodo, 'Top9')
    MisTot= TraeTotal(Periodo, 'Total')

    return '% Impact: '+format(MisTop9/MisTot*100, ',.2f')+'%'

@app.callback(
    Output('mis-top9', 'children'),
    [Input('periodo', 'value'),])
def update_miss_top9(value):

    Periodo = RevisaPeriodo(value)
    MisTop9= TraeTotal(Periodo, 'Top9')

    return 'Total-Top9: $ '+format(MisTop9, ',.2f')

@app.callback(
    Output('mis-tot', 'children'),
    [Input('periodo', 'value'),])
def update_miss_tot(value):

    Periodo = RevisaPeriodo(value)
    MisTot= TraeTotal(Periodo, 'Total')

    return 'Total-Missings: $ '+format(MisTot, ',.2f')

@app.callback(
    Output('pie-toptenM', 'figure'),
    [Input('periodo', 'value'),])
def update_graph_pieM(value):

    Periodo = RevisaPeriodo(value)
    PDMissings = TraeMTop9(Periodo)

    return {'data': [
                {
                    'labels': PDMissings.MedCode,
                    'values': PDMissings.AmountMissing,
                    'type': 'pie',
                    }
                ],
                    'layout': {
                        'title':'Top9 MedCode - Missings',
                    }
                }

@app.callback(
    Output('forecast-graph', 'figure'),
    [Input('pie-toptenM', 'clickData'),])
def update_forecast_graph(point):
    global Forecast

    if point==None:
        return {
                'data': [],
                'layout': { 'autosize': False,
                            'height': 450,
                            'template': '...',
                            'title': {'text': ''},
                            'width': 1000,
                            'xaxis': {'title': {'text': 'Date'}},
                            'yaxis': {'title': {'text': 'Consumed Amount'}}}
                }

    medcode =point['points'][0]['label']

    # Timeseries line plot
    plot_df = Forecast[Forecast.MedCode==int(medcode)]
    line_plot = go.Figure()
    for column in ['Mean_Forecast','ARIMA_Forecast','RNN_Forecast','AmountConsumed']:
        line_plot.add_trace(go.Scatter(x=plot_df.Month, y=plot_df[column], mode='lines+markers', name=column))
    #MedDescription = plot_df.MedDescription.unique()[0]
    MedDescription = TraeMCDesc(medcode)
    line_plot.update_layout(title=MedDescription,
                            xaxis_title='Date', yaxis_title='Consumed Amount',
                            autosize=False, width=1000, height=450)
    #line_plot.show()

    return line_plot.to_dict()

@app.callback(
    Output('bar-error', 'figure'),
    [Input('error', 'value'),
     Input('pie-toptenM', 'clickData'),])
def update_bar_error(error, point):
    global Errors

    if point==None:
        return {
                'data': [
                    {
                    'marker': {'color': ['#636efa', '#ef553b', '#00cc96']},
                    },
                ],
                'layout': {'autosize': False,
                            'barmode': 'group',
                            'height': 450,
                            'template': '...',
                            'title': {'text': ''},
                            'width': 500,
                            'xaxis': {'title': {'text': 'Model'}},
                            'yaxis': {'title': {'text': ''}}}
        }

    # Errors bar plot
    medcode =point['points'][0]['label']
    plot_errors = Errors[Errors.MedCode==int(medcode)].mean()

    colors = ['#636efa','#ef553b','#00cc96']
    # MAE
    mae_bar = go.Figure()
    mae_error = plot_errors[['Mean_AbsError','ARIMA_AbsError','RNN_AbsError']]
    mae_bar.add_trace(go.Bar(x=['Mean','ARIMA','RNN'], y=mae_error,
                             text=mae_error, name='MAE', marker_color=colors)
                     )
    # MAPE
    mape_bar = go.Figure()
    mape_error = plot_errors[['Mean_PerError','ARIMA_PerError','RNN_PerError']]
    mape_bar.add_trace(go.Bar(x=['Mean','ARIMA','RNN'], y=mape_error,
                              text=mape_error, name='MAPE', marker_color=colors)
                      )
    # Format
    mae_bar.update_traces(texttemplate='%{value:.1f}', textposition='auto')
    mae_bar.update_layout(title='Forecast MAE per model', barmode='group',
                          xaxis_title='Model',
                          yaxis_title='Mean Absolute Error',
                          autosize=False, width=500, height=450)
    mape_bar.update_traces(texttemplate='%{value:.1f}%', textposition='auto')
    mape_bar.update_layout(title='Forecast MAPE per model', barmode='group',
                           xaxis_title='Model',
                           yaxis_title='Mean Absolute Percentage Error [%]',
                           autosize=False, width=500, height=450)

    if error == 'MAE':
        figure = mae_bar
    else:
        figure = mape_bar

    return figure.to_dict()


@app.callback(
    Output('pdi-graph', 'figure'),
    [Input('pie-toptenM', 'clickData'),])
def update_pdi_graph(point):
    global PDI

    if point==None:
        return {
                'data': [{},],
                'layout': {}
        }

    medcode =point['points'][0]['label']
    plot_df = PDI[PDI.MedCode==int(medcode)]
    line_plot = go.Figure()
    for column in ['SP','PV','OP','AmountInventory','AmountConsumed']:
        #line_plot.add_trace(go.Scatter(x=plot_df.YearMonth, y=plot_df[column], mode='lines+markers', name=column))
        line_plot.add_trace(go.Scatter(x=plot_df.YearMonth, y=plot_df[column], mode='lines', name=column))
    #MedDescription = plot_df.MedDescription.unique()[0]
    MedDescription = TraeMCDesc(medcode)
    line_plot.update_layout(title='PDI Inventory suggestion - '+MedDescription,
                            xaxis_title='Date', yaxis_title='Consumed Amount',
                            autosize=False, width=1000, height=450)

    return line_plot.to_dict()

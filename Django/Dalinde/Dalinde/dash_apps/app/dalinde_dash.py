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

warnings.simplefilter(action='ignore', category=FutureWarning)
#Inicia Dash - APP 'Dalinde'
external_stylesheets = ['http://54.184.252.64:8000/static/css/dash.css']
app = DjangoDash('dalinde_dash', external_stylesheets=external_stylesheets)
#app = DjangoDash('dalinde_dash', serve_locally=True)

#Conexion a la Base de Datos
pd.options.display.max_rows = 20
engine=create_engine('postgresql://postgres:Ds4_MX_2020@54.184.252.64/DalindeDB', max_overflow=30)

PDMissings = pd.DataFrame()
PDRequests = pd.DataFrame()

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
BD = AjustaBD()
MC = TraeMedCodeBD()

def WeekYear(Fecha):
    inicio = datetime.datetime(2018, 1, 1)
    siguiente = datetime.datetime(Fecha.year, Fecha.month, Fecha.day)
    return(int(abs(siguiente - inicio).days/7))

def GetData(medcode):
    global BD
    
    BDMC = BD.copy() # Copia de la BD Req con Consolidado de PO
    # Aplicando el filtro del MedCode
    BDMC['MedCode'] = BDMC['MedCode'].astype(str)
    BDMC = BDMC[BDMC['MedCode']==str(medcode)]
    # Creando la tabla paa MEDCODE, Week vs AmountRequested
    data = pd.DataFrame(columns=('Week', 'AmountRequested'))
    for row in BDMC.iterrows():
        Week = WeekYear(row[1].RequestDate)
        Quantity = row[1].AmountRequested
        data = data.append({'Week': Week, 'AmountRequested': Quantity}, ignore_index=True)

    data = data.set_index('Week')
    data = data.groupby("Week").sum()
    return(data)

#Solucion PDI
def PDIDash(MedCode):
    m = GEKKO()                #Modelo GEKKO
    tf = 105
    Data = GetData(MedCode)
    #LLENAR EL EJE DE LAS X, EN FECHAS (SEMANAS EN DOS AÑOS)
    m.time = np.linspace(0,tf-1,tf)  #Return evenly spaced numbers over a specified interval.
    #LLENAR EL EJE DE LAS Y DEMANDA DE CADA MED CODE
    step = np.zeros(tf)
    for row in Data.iterrows():
        step[row[0]] = row[1].AmountRequested    

    # Controller model
    Kc = 15.0                   # controller gain
    tauI = 2.0                  # controller reset time
    tauD = 1.0                  # derivative constant
    OP_0 = m.Const(value=0.0)   # OP bias
    OP = m.Var(value=0.0)       # controller output
    PV = m.Var(value=0.0)       # process variable
    SP = m.Param(value=step)    # set point
    Intgl = m.Var(value=0.0)    # integral of the error
    err = m.Intermediate(SP-PV) # set point error
    m.Equation(Intgl.dt()==err) # integral of the error
    m.Equation(OP == OP_0 + Kc*err + (Kc/tauI)*Intgl - PV.dt())

    # Process model
    Kp = 0.5                    # process gain
    tauP = 10.0                 # process time constant
    m.Equation(tauP*PV.dt() + PV == Kp*OP)

    m.options.IMODE=4
    m.solve(disp=False)

    # OUTPUT (LO dejo pendiente para graficar)
    # plt.plot(m.time,OP.value,'b:',label='OP')

    # A GRAFICAR
    # - m.time SON LAS SEMANAS
    # - SP son los AmontRequested por Semanas
    # - PV serías las prediciones 
    # plt.plot(m.time,SP.value,'k-',label='SP')
    # plt.plot(m.time,PV.value,'r--',label='PV')

    #SP['value'] = int(round(SP['value']))

    return m.time, SP.value, PV.Value

app.layout = html.Div([
    html.Link(
        rel='stylesheet',
        href='/static/css/dash.css'
    ),
    html.Div(id="dash-head", className='dash-sec', children=[
        html.Div([
            html.H3('Period'),
            dcc.RadioItems(id='periodo',
                options=[{'label': c, 'value': c} for c in ['2Y', '1Y', '9M', '6M', '3M', '1M']],
                value='6M', labelStyle={'display':'inline-block'})
        ], style={'display': 'inline-block', 'width': '40%'}),
        html.Div([
            html.H3('Type'),
            dcc.RadioItems(id='amt_qty',
                options=[{'label': c, 'value': c} for c in ['Amount', 'Times']],
                value='Times', labelStyle={'display':'inline-block'}) 
        ], style={'display': 'inline-block', 'width': '30%'}),
        html.Div([
            html.H3('MedCode'),
            dcc.Input(id='medcode', value='', type='text', minLength='7')
        ], style={'display': 'inline-block', 'width': '30%'}),
    ]),

    html.Div(id="dash-graph", className='dash-sec', children=[
        # Una Grafica, Pie de 10 Mas solicitados en el Periodo
        html.Div(id="pie-topten-wrap", children=[
            html.H2('TopTen Graphs'),
            html.Div(className="overborder", children=[
                html.Div([html.P(id='mreq-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mpur-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mrec-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mmis-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mprice-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
            ]),
            
            html.Div(className='dash-sec', children=[
            dcc.Graph(id='pie-toptenM')
            ]),
            
            html.Div(className="overborder", children=[
                html.Div([html.P(id='req-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='pur-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='rec-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mis-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='price-qty'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
            ]),

            html.Div(id="pi-topten-r", className='dash-sec', children=[
            dcc.Graph(id='pie-toptenR')
            ])
        ], style={'display': 'inline-block', 'width': '49%'}),

        # Dos Graficas Lineas(Cantidades x dia) + Histograma(dias con faltantes) en un periodo
        html.Div(id="histogram", className='dash-sec', children=[
            html.H1('MedCode Graphs'),
            html.Div(className="overborder", children=[
                html.Div([html.P(id='mc-req'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mc-min'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mc-avg'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mc-max'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
                html.Div([html.P(id='mc-mis'),],
                    style={'display': 'inline-block', 'width': '20%', 'color':'#FFF', 'background-color':'#666', 'font-size':'10px'}),
            ]),
            html.Div(className='dash-sec', children=[
            dcc.Graph(id='graph-medcode'),
            ]),
            html.Div([html.H5('Graph by WeekDay')]),
            html.Div([
            dcc.Graph(id='hist-medcode')
            ]),
#            html.Div([
#            dcc.Graph(id='graph-pdi')
#            ])
        ], style={'display': 'inline-block', 'width': '49%', 'font-size':'10px'}),
    ]),
])

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

def TraePD(start_date, aort):
    global BD

    PD = BD.copy()
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    if aort=='Amount':
        PD = PD.groupby('MedCode', as_index=False)['AmountRequested'].sum()
    else:
        PD = PD.groupby('MedCode', as_index=False)['AmountRequested'].count()
    PD.sort_values('AmountRequested', ascending=False,  inplace=True)
    
    return PD.head(10)

def TraePDM(start_date, aort):
    global BD

    PD = BD.copy()
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    PD = PD[PD['AmountMissing'] > 0]
    if aort=='Amount':
        PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].sum()
    else:
        PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].count()
    PD.sort_values('AmountMissing', ascending=False,  inplace=True)

    return PD.head(10)

@app.callback(
    Output('medcode', 'value'),
    [Input('pie-toptenR', 'clickData'),
    Input('pie-toptenM', 'clickData')])
def update_medcode(clickData, clickData2):
    if (clickData==None) & (clickData2==None):
        return ''
    elif clickData2==None:
        return clickData['points'][0]['label']
    else:
        return clickData2['points'][0]['label']

#CALLBACKs de Etiquetas de MedCode
def TraeMCQty(start_date, medcode, Tipo):
    global BD

    PD = BD.copy()
    PD['MedCode'] = PD['MedCode'].astype(str)
    PD = PD[PD['MedCode']==str(medcode)]
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]

    if Tipo=='Minimum':
        Qty = PD['AmountRequested'].min()
    elif Tipo=='Average':
        if PD['AmountRequested'].count() == 0:
            Qty = 0
        else:
            Qty = int(round(PD['AmountRequested'].mean()))
    elif Tipo=='Maximum':
        Qty = PD['AmountRequested'].max()
    elif Tipo=='Requested':
        Qty = PD['AmountRequested'].count()
    elif Tipo=='Missings':
        Qty = PD[PD['AmountMissing']>0]['AmountMissing'].count()

    return Qty

@app.callback(
    Output('mc-mis', 'children'),
    [Input('periodo', 'value'),
    Input('medcode', 'value'),])
def update_mc_mis(per, medcode):

    if medcode == '':
        return '#Missings:'
    Periodo = RevisaPeriodo(per)
    MCQty= TraeMCQty(Periodo, medcode, 'Missings')

    return '#Missings: '+str(MCQty)

@app.callback(
    Output('mc-max', 'children'),
    [Input('periodo', 'value'),
    Input('medcode', 'value')])
def update_mc_max(per, medcode):

    if medcode == '':
        return 'Maximum:'
    Periodo = RevisaPeriodo(per)
    MCQty= TraeMCQty(Periodo, medcode, 'Maximum')

    return 'Maximum: '+str(MCQty)

@app.callback(
    Output('mc-avg', 'children'),
    [Input('periodo', 'value'),
    Input('medcode', 'value')])
def update_mc_avg(per, medcode):

    if medcode == '':
        return 'Average:'
    Periodo = RevisaPeriodo(per)
    MCQty= TraeMCQty(Periodo, medcode, 'Average')

    return 'Average: '+str(MCQty)

@app.callback(
    Output('mc-min', 'children'),
    [Input('periodo', 'value'),
    Input('medcode', 'value')])
def update_mc_min(per, medcode):

    if medcode == '':
        return 'Minimum:'
    Periodo = RevisaPeriodo(per)
    MCQty= TraeMCQty(Periodo, medcode, 'Minimum')

    return 'Minimum: '+str(MCQty)

@app.callback(
    Output('mc-req', 'children'),
    [Input('periodo', 'value'),
    Input('medcode', 'value')])
def update_mc_req(per, medcode):

    if medcode == '':
        return '#Requests:'
    Periodo = RevisaPeriodo(per)
    MCQty= TraeMCQty(Periodo, medcode, 'Requested')

    return '#Requests: '+str(MCQty)

# Callbacks Etiquetas Top Ten REQUESTS
def TraePrecio(medcode):
    global MC

    MCD = MC.copy()
    MCD['MedCode'] = MCD['MedCode'].astype(str)
    MCD = MCD[MCD['MedCode'].isin([str(medcode)])]
    Lista = MCD.values.tolist()
    Precio = Lista[0][4]

    return Precio

def TraeTotQty(start_date, Tipo):
    global BD, PDRequests

    PD = BD.copy()
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    PD = PD[PD['MedCode'].isin(PDRequests['MedCode'])]
    PD.reset_index(inplace = True)

    if Tipo=='Requested':
        Sum = PD['AmountRequested'].sum()
    elif Tipo=='Purchased':
        Sum = PD['AmountPurchased'].sum()
    elif Tipo=='Received':
        Sum = PD['AmountReceived'].sum()
    elif Tipo=='Missing':
        Sum = PD[PD['AmountMissing']>0]['AmountMissing'].sum()
    elif Tipo=='Price':
        Sum = 0
        PD = PD[PD['AmountMissing']>0]
        PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].sum()
        for row in PD.iterrows():
            Sum = Sum+row[1].AmountMissing*TraePrecio(row[1].MedCode)

    return Sum

@app.callback(
    Output('mis-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenR', ''),
    Input('amt_qty', 'value')])
def update_mis_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotQty(Periodo, 'Missing')

    return 'Missings: '+format(QtyReq, ',d')

@app.callback(
    Output('rec-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenR', ''),
    Input('amt_qty', 'value')])
def update_rec_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotQty(Periodo, 'Received')

    return 'Received: '+format(QtyReq, ',d')

@app.callback(
    Output('pur-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenR', ''),
    Input('amt_qty', 'value')])
def update_pur_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotQty(Periodo, 'Purchased')

    return 'Purchased: '+format(QtyReq, ',d')

@app.callback(
    Output('req-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenR', ''),
    Input('amt_qty', 'value')])
def update_req_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotQty(Periodo, 'Requested')

    return 'Requested: '+format(QtyReq, ',d')

@app.callback(
    Output('price-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenR', ''),
    Input('amt_qty', 'value')])
def update_pri_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotQty(Periodo, 'Price')

    return 'Impact: $ '+format(QtyReq, ',.2f')

#CALLBACKs ETIQUETAS TOPTEN MISSINGS

def TraeTotMis(start_date, Tipo):
    global BD, PDMissings

    PD = BD.copy()
    PD['RequestDate'] = pd.to_datetime(PD['RequestDate'], format='%Y-%m-%d')
    PD = PD[(PD['RequestDate'] > start_date) & (PD['RequestDate']<'2019-12-31')]
    PD = PD[PD['MedCode'].isin(PDMissings['MedCode'])]
    PD.reset_index(inplace = True)

    if Tipo=='Requested':
        Sum = PD['AmountRequested'].sum()
    elif Tipo=='Purchased':
        Sum = PD['AmountPurchased'].sum()
    elif Tipo=='Received':
        Sum = PD['AmountReceived'].sum()
    elif Tipo=='Missing':
        Sum = PD[PD['AmountMissing']>0]['AmountMissing'].sum()
    elif Tipo=='Price':
        Sum=0
        PD = PD[PD['AmountMissing']>0]
        PD = PD.groupby('MedCode', as_index=False)['AmountMissing'].sum()
        for row in PD.iterrows():
            Sum = Sum+row[1].AmountMissing*TraePrecio(row[1].MedCode)

    return Sum

@app.callback(
    Output('mmis-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenM', ''),
    Input('amt_qty', 'value')])
def update_mmis_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotMis(Periodo, 'Missing')

    return 'Missings: '+format(QtyReq, ',d')

@app.callback(
    Output('mrec-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenM', ''),
    Input('amt_qty', 'value')])
def update_mrec_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotMis(Periodo, 'Received')

    return 'Received: '+format(QtyReq, ',d')

@app.callback(
    Output('mpur-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenM', ''),
    Input('amt_qty', 'value')])
def update_mpur_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotMis(Periodo, 'Purchased')

    return 'Purchased: '+format(QtyReq, ',d')

@app.callback(
    Output('mreq-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenM', ''),
    Input('amt_qty', 'value')])
def update_mreq_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotMis(Periodo, 'Requested')

    return 'Requested: '+format(QtyReq, ',d')

@app.callback(
    Output('mprice-qty', 'children'),
    [Input('periodo', 'value'),
    Input('pie-toptenM', ''),
    Input('amt_qty', 'value')])
def update_mprice_val(value, pie, aoq):
    Periodo = RevisaPeriodo(value)
    QtyReq= TraeTotMis(Periodo, 'Price')

    return 'Impact: $ '+format(QtyReq, ',.2f')

#CALLBACKs de los Pie
@app.callback(
    Output('pie-toptenM', 'figure'),
    [Input('periodo', 'value'),
    Input('amt_qty', 'value')])
def update_graph_pieM(value, aot):
    global PDMissings

    Periodo = RevisaPeriodo(value)
    PDMissings = TraePDM(Periodo, aot)

    return {'data': [
                {
                    'labels': PDMissings.MedCode,
                    'values': PDMissings.AmountMissing,
                    'type': 'pie',
                    }
                ],
                    'layout': {
                        'title':'TopTen MedCode Missings',
                    }
                }

@app.callback(
    Output('pie-toptenR', 'figure'),
    [Input('periodo', 'value'),
    Input('amt_qty', 'value')])
def update_graph_pieR(value, aot):
    global PDRequests

    Periodo = RevisaPeriodo(value)
    PDRequests = TraePD(Periodo, aot)

    return {'data': [
                {
                    'labels': PDRequests.MedCode,
                    'values': PDRequests.AmountRequested,
                    'type': 'pie',
                    }
                ],
                    'layout': {
                        'title':'TopTen MedCode Requested',
                    }
                }
def TraeMCDay(start_date, medcode):
    global BD

    MCDay = BD.copy()
    MCDay['MedCode'] = MCDay['MedCode'].astype(str)
    MCDay = MCDay[MCDay['MedCode']==str(medcode)]
    MCDay['RequestDate'] = pd.to_datetime(MCDay['RequestDate'], format='%Y-%m-%d')
    MCDay = MCDay[(MCDay['RequestDate'] > start_date) & (MCDay['RequestDate']<'2019-12-31')]
    
    MCDay = MCDay.groupby(['MedCode', 'WeekDay']).count()
    MCDay.reset_index(inplace=True)

    return MCDay

def TraeMCReq(start_date, medcode):
    global BD

    MCReq = BD.copy()
    MCReq['MedCode'] = MCReq['MedCode'].astype(str)
    MCReq = MCReq[MCReq['MedCode']==str(medcode)]
    MCReq['RequestDate'] = pd.to_datetime(MCReq['RequestDate'], format='%Y-%m-%d')
    MCReq = MCReq[(MCReq['RequestDate'] > start_date) & (MCReq['RequestDate']<'2019-12-31')]
    
    return MCReq

def TraeMCDesc(medcode):
    global MC

    MCD = MC.copy()
    MCD['MedCode'] = MCD['MedCode'].astype(str)
    MCD = MCD[MCD['MedCode']==str(medcode)]
    Patente = MCD['MedDescription'].values.tolist()
    
    return Patente[0]

@app.callback(
    Output('hist-medcode', 'figure'),
    [Input('periodo', 'value'),
     Input('medcode', 'value')])
def update_hist_medcode(val_periodo, medcode):
    if medcode=='':
        return {
                'data': [
                    {'x':[], 'y':[], 'type':'bar', 'name':'Day'},  
                ],
                'layout': {
                    'title':'Requests by WeekDay - '
                }
        }
    periodo = RevisaPeriodo(val_periodo)
    MCDay = TraeMCDay(periodo, medcode)
    #Week = Grafica(MCDay)
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(0.0, 'Domingo')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(1.0, 'Lunes')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(2.0, 'Martes')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(3.0, 'Miercoles')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(4.0, 'Jueves')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(5.0, 'Viernes')
    MCDay['WeekDay'] = MCDay['WeekDay'].replace(6.0, 'Sabado')

    return {
            'data': [
                    {'x':MCDay.WeekDay, 'y':MCDay.PurchaseNumber, 'type':'bar', 'name':'Day'},
                    ],
            'layout': {
                    'title':'Requests by WeekDay - '+str(medcode)
    }            }

@app.callback(
    Output('graph-medcode', 'figure'),
    [Input('periodo', 'value'),
     Input('medcode', 'value')])
def update_graph_medcode(val_periodo, medcode):
    if medcode=='':
        return {
                'data': [],
                'layout': {
                    'title':'MedCode'
                }
        }
    periodo = RevisaPeriodo(val_periodo)
    MCReq = TraeMCReq(periodo, medcode)
    Patente = TraeMCDesc(medcode)

    return {
            'data': [
                    {'x':MCReq.RequestDate, 'y':MCReq.AmountRequested, 'type':'line', 'name':'Requested'},
                    {'x':MCReq.RequestDate, 'y':MCReq.AmountPurchased, 'type':'line', 'name':'Purchased'},
                    {'x':MCReq.RequestDate, 'y':MCReq.AmountReceived, 'type':'line', 'name':'Received'},
                    ],
            'layout': {
                    'title':medcode+'-'+Patente,
                    'font':{'size':'10', 'color':'black'}}
    }
"""
@app.callback(
    Output('graph-pdi', 'figure'),
    [Input('periodo', 'value'),
     Input('medcode', 'value')])
def update_graph_pdi(val_periodo, medcode):
    if medcode=='':
        return {
                'data': [],
                'layout': {
                    'title':' MPC MedCode'
                }
        }
    periodo = RevisaPeriodo(val_periodo)
    time, SP, PV = PDIDash(medcode)

    return {
            'data': [
                    {'x':time, 'y':SP, 'type':'line', 'name':'Requested',
                    'line': {'color':'black'}},
                    {'x':time, 'y':PV, 'type':'line', 'name':'PDI-Predicted',
                    'line': {'color':'red', 'dash':'dashdot'}},
                    ],
            'layout': {
                    'title':'MPC - '+medcode+' - Predicted --> '+str(int(round(PV[-1]))),
                    'font':{'size':'10', 'color':'black'}}
    }
"""

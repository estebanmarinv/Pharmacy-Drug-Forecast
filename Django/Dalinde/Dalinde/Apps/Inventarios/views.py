from django.shortcuts import render
from django.http import HttpResponse
import matplotlib.pyplot as plt
import datetime
import matplotlib
import pandas as pd
from gekko import GEKKO
import numpy as np
from .forms import *
from .models import PReqMedCode, RequestMedCode, POReqMedCode, POinReq, MCReq, PatentDrug, POinReq2, POReqMedCode2, PatentDrug2
import os
from django.forms import formset_factory

# Create your views here.

def NextRequest(request):
    request_medcode = PatentDrug.objects.raw("""SELECT * FROM "PatentDrug"
        WHERE "Predict" > 0
        ORDER BY "Predict" DESC
    """)
    return render(request, 'NextRequest.html', {'req':request_medcode})

def ReqMCForm(request):
    Saber = PatentDrug2.objects.filter(MedCode=3302093).values("Predict")
    print(Saber[0]['Predict'])
    
    #DrugFormSet = formset_factory(RequestMedCodeForm, extra=2, max_num=3)
    DrugFormSet = formset_factory(RequestMedCodeForm, extra=3, max_num=5)
    form_ReqMC = DrugFormSet()
    form_Req = RequestForm()
    if request.method == 'POST':
        form_ReqMC = DrugFormSet(request.Post, request.FILES)
        if form_ReqMC.is_valid():
            print('VALID')
            #form_ReqMC.save()
            #return redirect('/')
    
    return render(request, 'ReqMCForm.html', {'formReqMC':form_ReqMC,'formReq':form_Req})

def DescMC(MC):
    Des = PatentDrug.objects.raw("""SELECT "MedCode", "MedDescription" FROM "PatentDrug" WHERE "MedCode"=%s  """,[MC])
    for r in Des[:1]:
        DesMed = r.MedDescription
    return DesMed

def Menu(request):
    return render(request, 'Menu.html')

def TopTenMedCodeReq():
    TOP10_ReqMC = PReqMedCode.objects.raw("""SELECT
        "RequestNumber",
        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
            WHERE "RequestMedCode"."MedCode" = "PatentDrug"."MedCode"),
        "AmountRequested"
        FROM "RequestMedCode"
        ORDER BY "AmountRequested" DESC
    """)

    matplotlib.use('Agg')
    Data = pd.DataFrame(columns=['RequestDate', 'AmountRequested'])
    for p in request_medcode:
        Data =Data.append({'RequestDate':p.RequestDate, 'AmountRequested':p.AmountRequested}, ignore_index=True)

    DesMed = DescMC(MedCode)
    Data.plot(x='RequestDate', y='AmountRequested', kind = 'line', rot=90, color='blue')
    plt.title(DesMed)
    plt.savefig('./Dalinde/Apps/Inventarios/static/ImagenTopTenReq.png')
    plt.close('all')

def Dashboard(request):
    #print(BASE_DIR)
    page_title="Dashboard"
    return render(request, 'Dashboard.html', {'page_title':page_title, 'id_pass':'dash-main-body'})

def Dashboard_Top9(request):
    #print(BASE_DIR)
    page_title="Dashboard top 9"
    return render(request, 'Dashboard_Top9.html', {'page_title':page_title, 'id_pass':'dash-main-body'})

def Dashboard_Errors(request):
    #print(BASE_DIR)
    page_title="Dashboard Errors"
    return render(request, 'Dashboard_Errors.html', {'page_title':page_title, 'id_pass':'dash-main-body'})

def Faltantes(request):
    page_title = "Shortages"
    request_medcode = PReqMedCode.objects.raw("""SELECT
        "RequestNumber",
        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
            WHERE "RequestMedCode"."MedCode" = "PatentDrug"."MedCode"),
        "AmountRequested"
        FROM "RequestMedCode"
        WHERE NOT EXISTS
            (SELECT * FROM "POReqMedCode" 
                WHERE "POReqMedCode"."RequestNumber" = "RequestMedCode"."RequestNumber" 
                AND "POReqMedCode"."MedCode" = "RequestMedCode"."MedCode")
        ORDER BY "AmountRequested" DESC
    """)
    return render(request, 'FaltantesBusqueda.html', {'reqmedcode':request_medcode, 'page_title':page_title})

def Faltantesmal(request):
    request_medcode = PReqMedCode.objects.raw("""SELECT
        "RequestNumber",
        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
            WHERE "RequestMedCode"."MedCode" = "PatentDrug"."MedCode"),
        "AmountRequested"
        FROM "RequestMedCode"
        WHERE
            (SELECT "Purchase Number" FROM "POReqMedCode" 
                WHERE "POReqMedCode"."RequestNumber" = "RequestMedCode"."RequestNumber" 
                AND "POReqMedCode"."MedCode" = "RequestMedCode"."MedCode")
        ORDER BY "AmountRequested" DESC
    """)
    return render(request, 'FaltantesBusqueda.html', {'reqmedcode':request_medcode})

def Search(request):
    page_title = "List patent drugs by request order"
    return render(request, 'Busqueda.html', {'page_title':page_title})

def SearchRequest(request):
    if request.GET['request']:
        Request = int(request.GET['request'])
        print(Request) 
        #request_medcode = RequestMedCode.objects.filter(RequestNumber=Request)
        request_medcode = RequestMedCode.objects.raw("""SELECT * FROM "RequestMedCode" WHERE "RequestNumber" = %s""", [Request])
        #request_medcode = PReqMedCode.objects.raw("""SELECT * FROM "RequestMedCode" WHERE "RequestNumber" = %s""", [Request])
        return render(request, 'ResultadosBusqueda.html', {'reqmedcode':request_medcode, 'query':Request})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def SearchPO(request):
    page_title = "List patent drugs by purchase order"
    return render(request, "BusquedaPO.html", {'page_title':page_title})

def SearchPOReq(request):
    if request.GET['po']:
        PO = int(request.GET['po'])
 #       poreq_medcode = POReqMedCode.objects.filter(PurchaseNumber=PO)
        poreq_medcode = POReqMedCode2.objects.raw("""SELECT *, po."SupplierName",
                                                    (SELECT "MedDescription" FROM "PatentDrug" AS p
                                                    WHERE p."MedCode" = pormc."MedCode"
                                                    ) AS "MedDescription"
                                                    FROM "POReqMedCode" AS pormc
                                                    JOIN "PurchaseOrder" AS po
                                                    ON pormc."PurchaseNumber" = po."PurchaseNumber"
                                                    WHERE pormc."PurchaseNumber"=%s
                                                """, [PO])
        Sup='Error'
        Req=0
        for p in poreq_medcode:
            Sup = p.SupplierName
            Req = p.RequestNumber
            break
        
        return render(request, 'ResultadosBusquedaPO.html', {'poreqmedcode':poreq_medcode, 'query':PO, 'sup':Sup, 'req':Req})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def SearchReq2(request):
    page_title = "List purchase orders/drugs by request"
    return render(request, "BusquedaReqPO2.html", {'page_title':page_title})

def SearchReq(request):
    page_title = "List purchase orders by request"
    return render(request, "BusquedaReqPO.html", {'page_title':page_title})

def SearchReqPO2(request):
    if request.GET['req']:
        Req = int(request.GET['req'])
        print(Req)
        req_pos = POinReq2.objects.raw("""SELECT
                                        "PurchaseNumber",
                                        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
                                        WHERE "POReqMedCode"."MedCode" = "PatentDrug"."MedCode") AS "MedDescription",
                                        "AmountPurchased"
                                        FROM "POReqMedCode" WHERE "RequestNumber" = %s
                                        GROUP BY "PurchaseNumber", "MedDescription", "AmountPurchased" ORDER BY "AmountPurchased" DESC """, [Req])
        print(req_pos)
        return render(request, 'ResultadosBusquedaReqPO2.html', {'reqpos':req_pos, 'query':Req})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def SearchReqPO(request):
    if request.GET['req']:
        Req = int(request.GET['req'])
        #req_pos = POinReq.objects.raw("""SELECT "POReqMedCode"."PurchaseNumber", count("POReqMedCode"."MedCode") AS "Cantidad" FROM "POReqMedCode" WHERE "POReqMedCode"."RequestNumber" = %s GROUP BY "POReqMedCode"."PurchaseNumber" ORDER BY "Cantidad" DESC """, [Req])
        req_pos = POinReq.objects.raw("""SELECT "PurchaseNumber", count("MedCode") AS "Cantidad" FROM "POReqMedCode" WHERE "RequestNumber" = %s GROUP BY "PurchaseNumber" ORDER BY "Cantidad" DESC """, [Req])
        return render(request, 'ResultadosBusquedaReqPO.html', {'reqpos':req_pos, 'query':Req})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def SeachMC(request):
    return render(request, "BusquedaMC.html")

def Grafica(MCReq, MedCode):
    matplotlib.use('Agg')
    Data = pd.DataFrame(columns=['RequestDate', 'AmountRequested'])
    for p in MCReq:
        Data =Data.append({'RequestDate':p.RequestDate, 'AmountRequested':p.AmountRequested}, ignore_index=True)

    DesMed = DescMC(MedCode)
    Data.plot(x='RequestDate', y='AmountRequested', kind = 'line', rot=90, color='blue')
    plt.title(DesMed)
    plt.savefig('./Dalinde/Apps/Inventarios/static/ImagenMCReq.png')
    plt.close('all')
    #plt.show()

def SeachMCReq(request):
    if request.GET['mc']:
        MC = int(request.GET['mc'])
        #req_pos = POinReq.objects.raw("""SELECT "POReqMedCode"."PurchaseNumber", count("POReqMedCode"."MedCode") AS "Cantidad" FROM "POReqMedCode" WHERE "POReqMedCode"."RequestNumber" = %s GROUP BY "POReqMedCode"."PurchaseNumber" ORDER BY "Cantidad" DESC """, [Req])
        mc_req = MCReq.objects.raw("""SELECT
        "MedCode",
        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
            WHERE "RequestMedCode"."MedCode" = "PatentDrug"."MedCode") AS "MedCodeDescription",
        "RequestNumber",
        (SELECT "Request"."RequestDate" FROM "Request"
            WHERE "RequestMedCode"."RequestNumber" = "Request"."RequestNumber") AS "RequestDate",
        "AmountRequested"
        FROM "RequestMedCode"
        WHERE "MedCode" = %s
        """, [MC])
        Grafica(mc_req, MC)
        return render(request, 'ResultadosBusquedaMCReq.html', {'mcreq':mc_req, 'query':MC})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def SearchPDI(request):
    page_title = "PDI model"
    return render(request, "BusquedaPDI.html", {'page_title':page_title})

def WeekYear(Fecha):
    inicio = datetime.datetime(2018, 1, 1)
    siguiente = datetime.datetime(Fecha.year, Fecha.month, Fecha.day)
    return(int(abs(siguiente - inicio).days/7))

def GetData(PDIReq):
    
    PDIReqBD = pd.DataFrame(columns=('MedCode','MedCodeDescription','RequestNumber','RequestDate','AmountRequested'))
    for p in PDIReq:
        PDIReqBD =PDIReqBD.append({'MedCode':p.MedCode, 'MedCodeDescription':p.MedCodeDescription, 'RequestNumer':p.RequestNumber, 'RequestDate':p.RequestDate, 'AmountRequested':p.AmountRequested}, ignore_index=True)

    data = pd.DataFrame(columns=('Week', 'AmountRequested'))
    for row in PDIReqBD.iterrows():
        Week = WeekYear(row[1].RequestDate)
        Quantity = row[1].AmountRequested
        data = data.append({'Week': Week, 'AmountRequested': Quantity}, ignore_index=True)

    data = data.set_index('Week')
    data = data.groupby("Week").sum()
    return(data)

def PDI(PDIReq, MC):
    matplotlib.use('Agg')
    m = GEKKO()                #Modelo GEKKO
    tf = 105
    Data = GetData(PDIReq)
    #LLENAR EL EJE DE LAS X, EN FECHAS
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

    plt.figure()
    plt.subplot(2,1,1)
    plt.plot(m.time,OP.value,'b:',label='OP')
    plt.ylabel('Output')
    plt.legend()
    plt.subplot(2,1,2)
    plt.plot(m.time,SP.value,'k-',label='SP')
    plt.plot(m.time,PV.value,'r--',label='PV')
    plt.xlabel('Week -- 2018-2019')
    plt.ylabel('Process')
    plt.legend()
     
    plt.savefig('./Dalinde/Apps/Inventarios/static/ImagenMCPDI.png')
    plt.close('all')

def SearchPDIReq(request):
    page_title = 'PDI model'
    if request.GET['mc']:
        MC = int(request.GET['mc'])
        #req_pos = POinReq.objects.raw("""SELECT "POReqMedCode"."PurchaseNumber", count("POReqMedCode"."MedCode") AS "Cantidad" FROM "POReqMedCode" WHERE "POReqMedCode"."RequestNumber" = %s GROUP BY "POReqMedCode"."PurchaseNumber" ORDER BY "Cantidad" DESC """, [Req])
        mc_pdi = MCReq.objects.raw("""SELECT
        "MedCode",
        (SELECT "PatentDrug"."MedDescription" FROM "PatentDrug"
            WHERE "RequestMedCode"."MedCode" = "PatentDrug"."MedCode") AS "MedCodeDescription",
        "RequestNumber",
        (SELECT "Request"."RequestDate" FROM "Request"
            WHERE "RequestMedCode"."RequestNumber" = "Request"."RequestNumber") AS "RequestDate",
        "AmountRequested"
        FROM "RequestMedCode"
        WHERE "MedCode" = %s
        """, [MC])
        PDI(mc_pdi, MC)

        DesMed = DescMC(MC)
        return render(request, 'ResultadosBusquedaMCPDI.html', {'mcpdi':mc_pdi, 'query':MC, 'des':DesMed, 'page_title':page_title})
    else:
        mensaje='No has introducido nada'
    return HttpResponse(mensaje)

def index(request):
    page_title = 'Datafolio'
    return render(request, 'index.html', {'page_title':page_title})

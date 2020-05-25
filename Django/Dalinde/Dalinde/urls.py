"""Dalinde URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .Apps.Inventarios import views
from .dash_apps.app import dalinde_dash, dalinde1, SimpleExample, dalinde_dash_top9, dalinde_dash_errors

urlpatterns = [
    path('menu/', views.Menu),
    path('admin/', admin.site.urls),
    path('search/', views.Search),
    path('search_request/', views.SearchRequest),
    path('search_po/',views.SearchPO),
    path('search_poreq/',views.SearchPOReq),
    path('search_req/',views.SearchReq),
    path('search_reqpo/',views.SearchReqPO),
    path('search_req2/',views.SearchReq2),
    path('search_reqpo2/',views.SearchReqPO2),
    path('search_mc/', views.SeachMC),
    path('search_mcreq/', views.SeachMCReq),
    path('search_pdi/', views.SearchPDI),
    path('search_pdireq/', views.SearchPDIReq),
    path('faltantes/', views.Faltantes),
    path('dashboard/', views.Dashboard),
    path('dashboard_top9/', views.Dashboard_Top9),
    path('dashboard_error/', views.Dashboard_Errors),
    path('dash_apps/', include('django_plotly_dash.urls')),
    path('req_mc_form/', views.ReqMCForm),
    path('next_req/', views.NextRequest),
    path('', views.index, name='index'),
]

from django.contrib import admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from Dalinde.Apps.Inventarios.models import PatentDrug, Request, PurchaseOrder, RequestMedCode, POReqMedCode, PatientConsumption, PatConsMedCode

# Register your models here.

class AdminPatentDrug(admin.ModelAdmin):
    list_display = ["MedCode", "MedDescription"]
    list_display_links = ["MedCode"]
    list_filter = ["MedFamily"]
    search_fields = ["MedDescription"]
    class Meta:
        model = PatentDrug

class AdminRequest(admin.ModelAdmin):
    list_display = ["__str__", "RequestNumber", "RequestDate"]
    list_display_links = ["RequestNumber"]
    #list_filter = ["RequestDate"]
    list_filter = (('RequestDate', DateRangeFilter),)
    search_fields = ["RequestNumber"]
    class Meta:
        model = Request

class AdminPO(admin.ModelAdmin):
    list_display = ["__str__", "PurchaseNumber", "OrderDate", "RequiredDeliveryDate"]
    list_display_links = ["PurchaseNumber"]
    #list_filter = ["OrderDate", "RequiredDeliveryDate"]
    list_filter = (('OrderDate', DateRangeFilter),('RequiredDeliveryDate', DateRangeFilter),)
    search_fields = ["PurchaseNumber"]
    class Meta:
        model = PurchaseOrder

class AdminRequestMedCode(admin.ModelAdmin):
    list_display = ["RequestNumber", "__str__"]
    list_display_links = ["RequestNumber"]
    list_filter = ["RequestNumber"]
    search_fields = ["RequestNumber", "MedCode"]
    class Meta:
        model = RequestMedCode

class AdminPOReqMedCode(admin.ModelAdmin):
    list_display = ["PurchaseNumber", "RequestNumber"]
    list_display_links = ["PurchaseNumber", "RequestNumber"]
    list_filter = ["PurchaseNumber", "RequestNumber"]
    search_fields = ["PurchaseNumber", "RequestNumber", "MedCode"]
    class Meta:
        model = POReqMedCode

class AdminPatientConsumption(admin.ModelAdmin):
    list_display = ["ConsumptionNumber", "ConsumptionDate"]
    list_display_links = ["ConsumptionNumber"]
    #list_filter = ["ConsumptionDate"]
    list_filter = (('ConsumptionDate', DateRangeFilter),)
    search_fields = ["ConsumptionNumber"]
    class Meta:
        model = PatientConsumption

class AdminConsMedCode(admin.ModelAdmin):
    list_display = ["ConsumptionNumber", "MedCode"]
    list_display_links = ["ConsumptionNumber"]
    list_filter = ["ConsumptionNumber"]
    search_fields = ["ConsumptionNumber", "MedCode"]
    class Meta:
        model = PatConsMedCode

admin.site.register(PatentDrug, AdminPatentDrug)
admin.site.register(Request, AdminRequest)
admin.site.register(PurchaseOrder, AdminPO)
admin.site.register(RequestMedCode, AdminRequestMedCode)
admin.site.register(POReqMedCode, AdminPOReqMedCode)
admin.site.register(PatientConsumption, AdminPatientConsumption)
admin.site.register(PatConsMedCode, AdminConsMedCode)
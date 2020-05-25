# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from datetime import datetime
from django.utils import timezone

class POReqMedCode2(models.Model):
    PurchaseNumber = models.IntegerField(primary_key=True)
    RequestNumber = models.IntegerField()
    MedCode= models.IntegerField()
    AmountPurchased = models.IntegerField()
    AmountReceived = models.IntegerField()
    MedDescription = models.CharField(max_length=100, null=True)
    SupplierName = models.CharField(max_length=80)

class MCReq(models.Model):
    MedCode = models.IntegerField(primary_key=True)
    MedDescription = models.CharField(max_length=100)
    RequestNumber = models.IntegerField()
    RequestDate = models.DateField()
    AmountRequested = models.IntegerField()

class POinReq(models.Model):
    PurchaseNumber = models.IntegerField(primary_key=True)
    Cantidad = models.IntegerField()

class POinReq2(models.Model):
    PurchaseNumber = models.IntegerField(primary_key=True)
    MedDescription = models.CharField(max_length=100)
    AmountPurchased = models.IntegerField()

class PReqMedDesCode(models.Model):
    MedDescription = models.CharField(max_length=100)
    RequestNumber = models.IntegerField(primary_key=True)
    AmountRequested = models.IntegerField()

    def __str__(self):
        return (self.MedDescription, self.RequestNumber, self.AmountRequested)

class PReqMedCode(models.Model):
    RequestNumber = models.IntegerField(primary_key=True)
    MedCode = models.IntegerField()
    AmountRequested = models.IntegerField()

class PatentDrug2(models.Model):
    MedCode = models.IntegerField(db_column='MedCode', primary_key=True, null=False)
    MedDescription = models.CharField(max_length=100, db_column='MedDescription', null=False)
    Price = models.DecimalField(db_column="Price", null=False, max_digits=6, decimal_places=2)
    MinStock = models.IntegerField(db_column="MinStock", null=False)
    MaxStock = models.IntegerField(db_column="MaxStock", null=False)
    Predict = models.IntegerField(db_column="Predict", default=14)
    
    class Meta:
        managed = False
        db_table = 'PatentDrug'

    def __str__(self):
        cadena =  "{0}, {1}"
        return cadena.format(self.MedDescription, self.Predict)

class PatentDrug(models.Model):
    MedCode = models.IntegerField(db_column='MedCode', primary_key=True, null=False)
    MedDescription = models.CharField(max_length=100, db_column='MedDescription', null=False)
    MedPharmacon = models.CharField(max_length=50, db_column='MedPharmacon', null=False)
    MedFamily = models.CharField(max_length=80, db_column='MedFamily', null=False)
    Price = models.DecimalField(db_column="Price", null=False, max_digits=6, decimal_places=2)
    MinStock = models.IntegerField(db_column="MinStock", null=False)
    MaxStock = models.IntegerField(db_column="MaxStock", null=False)
    Predict = models.IntegerField(db_column="Predict", null=False)
    
    class Meta:
        managed = False
        db_table = 'PatentDrug'

    def __str__(self):
        cadena =  "{0}"
        return cadena.format(self.MedDescription)

class Request(models.Model):
    RequestNumber = models.IntegerField(db_column='RequestNumber', default=90001, primary_key=True, null=False)
    RequestDate = models.DateField(db_column='RequestDate', default=timezone.now, null=False)
    
    class Meta:
        managed = False
        db_table = 'Request'

    def __str__(self):
        cadena =  "{0} ({1})"
        return cadena.format(self.RequestNumber, self.RequestDate)

class PurchaseOrder(models.Model):
    PurchaseNumber = models.IntegerField(db_column='PurchaseNumber', primary_key=True, null=False)
    OrderDate = models.DateField(db_column='OrderDate', null=False)
    RequiredDeliveryDate = models.DateField(db_column='RequiredDeliveryDate', null=False)
    SupplierName = models.CharField(max_length=80, db_column='SupplierName', null=False)
    
    class Meta:
        managed = False
        db_table = 'PurchaseOrder'

    def __str__(self):
        cadena =  "{0} ({1})"
        return cadena.format(self.PurchaseNumber, self.SupplierName)

class RequestMedCode(models.Model):
    RequestNumber = models.IntegerField('Request', db_column='RequestNumber', primary_key=True)
    MedCode= models.ForeignKey('PatentDrug', db_column='MedCode',  on_delete=models.CASCADE)
    AmountRequested = models.IntegerField(db_column='AmountRequested', null=False)

    class Meta:
        managed = False
        db_table = 'RequestMedCode'
        unique_together = (('RequestNumber', 'MedCode'),)

    def __str__(self):
        cadena =  "{0}"
        return cadena.format(self.MedCode)

class POReqMedCode(models.Model):
    PurchaseNumber = models.OneToOneField('PurchaseOrder', db_column='PurchaseNumber', primary_key=True, on_delete=models.CASCADE)
    RequestNumber = models.ForeignKey('Request', db_column='RequestNumber',  on_delete=models.CASCADE)
    MedCode= models.ForeignKey('PatentDrug', db_column='MedCode',  on_delete=models.CASCADE)
    AmountPurchased = models.IntegerField(db_column='AmountPurchased', null=False)
    AmountReceived = models.IntegerField(db_column='AmountReceived')

    class Meta:
        managed = False
        db_table = 'POReqMedCode'
        unique_together = (('PurchaseNumber', 'RequestNumber', 'MedCode'),)

    def __str__(self):
        cadena =  "{0} - {1} -{2} ({3})"
        return cadena.format(self.PurchaseNumber, self.RequestNumber, self.MedCode, self.AmountPurchased)

class PatientConsumption(models.Model):
    ConsumptionNumber = models.IntegerField(db_column='ConsumptionNumber', primary_key=True, null=False)
    ConsumptionDate = models.DateField(db_column='ConsumptionDate', null=False)
    Department = models.CharField(max_length=80, db_column='Department', null=False)
    
    class Meta:
        managed = False
        db_table = 'PatientConsumption'

    def __str__(self):
        cadena =  "{0}"
        return cadena.format(self.ConsumptionNumber)

class PatConsMedCode(models.Model):
    ConsumptionNumber = models.OneToOneField('PatientConsumption', db_column='ConsumptionNumber', primary_key=True, on_delete=models.CASCADE)
    MedCode= models.ForeignKey('PatentDrug', db_column='MedCode',  on_delete=models.CASCADE)
    AmountConsumed = models.IntegerField(db_column='AmountConsumed', null=False)

    class Meta:
        managed = False
        db_table = 'PatConsMedCode'
        unique_together = (('ConsumptionNumber', 'MedCode'),)

    def __str__(self):
        cadena =  "{0} {1} {2}"
        return cadena.format(self.ConsumptionNumber, self.MedCode), self.AmountConsumed
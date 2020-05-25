from django import forms
from .models import RequestMedCode, Request, PatentDrug2

class RequestForm(forms.ModelForm):

    class Meta:
        model = Request
        fields = ['RequestNumber', 'RequestDate']

class RequestMedCodeForm(forms.ModelForm):

    #Predict = forms.IntegerField(queryset=PatentDrug.objects.filter(MedCode=RequestMedCode.MedCode).select_related("Predict"))
    #Predict = forms.IntegerField(queryset=list(PatentDrug.objects.filter(MedCode=RequestMedCode.MedCode))[0].Predict)
    #Predict = forms.IntegerField(queryset=PatentDrug2.objects.filter(MedCode=3302093).values("Predict")[0]['Predict'])
    
    Predict = forms.IntegerField()

    class Meta:
        model = RequestMedCode
        fields = ('RequestNumber', 'MedCode', 'AmountRequested')
        fields = ['MedCode', 'AmountRequested']

from django import forms
from .models import Payment

class MpesaVerificationForm(forms.Form):
    transaction_id = forms.CharField(max_length=100, label="M-Pesa Transaction ID")
    phone_number = forms.CharField(max_length=15, label="Phone Number Used")
    verification_notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
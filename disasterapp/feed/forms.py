from django import forms
from .models import DisasterPost
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class MyForm(forms.ModelForm):
    user_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your PayPal email'})
    )

    class Meta:
        model = DisasterPost
        fields = ['title', 'description', 'location', 'donation_required', 'image', 'user_email']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter disaster title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the disaster', 'rows': 4}),  
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter disaster location'}),
            'donation_required': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify needed donations'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

        error_messages = {
            'title': {'required': 'Disaster title is required'},
            'description': {'required': 'Please provide details about the disaster'},
            'location': {'required': 'Location is required'},
            'donation_required': {'required': 'Specify what donations are needed'},
            'image': {'required': 'Please upload an image'},
            'user_email': {'required': 'Please enter a valid PayPal email'},
        }

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Ensure email is required

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match. Please enter the same password.")

        return cleaned_data


class DonationForm(forms.Form):
    amount = forms.IntegerField(min_value=1, label="Enter Donation Amount")

    def __init__(self, *args, **kwargs):
        self.post = kwargs.pop('post', None)
        super(DonationForm, self).__init__(*args, **kwargs)
        if self.post:
            self.fields['amount'].max_value = self.post.remaining_donation  # Prevent over-donation

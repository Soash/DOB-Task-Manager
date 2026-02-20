from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department
from django.core import validators
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter email address"
        }),
        validators=[validators.EmailValidator(message="Enter a valid email address.")]
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password"
        })
    )





class CustomUserCreationForm(UserCreationForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'first_name',
            'dob_id',
            'department',
            'role',
            'username',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            field.required = True        
            
        # Optional: Add helper text for social profile
        self.fields['username'].help_text = None
        self.fields['username'].label = "Email address"
        self.fields['username'].widget.attrs.pop("autofocus", None)
        self.fields['first_name'].label = "Full Name"
        
        

        


                
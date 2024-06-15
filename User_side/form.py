from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import PasswordInput
from django.core.exceptions import ValidationError
from django.core.validators import validate_email,EmailValidator
import re

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']
          
    def clean_email(self):
        mail_regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        email = self.data.get('email')
        # print(email)
        if re.fullmatch(mail_regex,email):
            # print("inside try")
            return email
        else:
            raise ValidationError("Invalid email format")
          
    def clean_password(self):
        # pass_regex=r'[A-Za-z0-9@#$%^&+=]{8,}'
        password=self.data.get('password1')

        def validate_password(password):
            # Check for minimum length
            if len(password) < 8:
                return "Password should contain at least 8 characters."
            
            # Check for at least one uppercase letter
            if not re.search("[A-Z]", password):
                return "Password should contain at least one uppercase letter."
            
            # Check for at least one lowercase letter
            if not re.search("[a-z]", password):
                return "Password should contain at least one lowercase letter."
            
            # Check for at least one digit
            if not re.search("[0-9]", password):
                return "Password should contain at least one digit."
            
            # Check for at least one special character
            if not re.search("[@#$%^&*(),.?\":{}|<>]", password):
                return "Password should contain at least one special character."
            
            # If all conditions are met, return None to indicate a valid password
            return None
        result=validate_password(password)
        if result:
            raise ValidationError(result)
        else:
            return password
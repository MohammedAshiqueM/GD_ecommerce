from django.shortcuts import render,redirect
from . form import UserRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
# from django.core.validators import validate_email,EmailValidator
import re
from .utils import generate_otp, send_otp
from datetime import datetime, timedelta


########################## function for login & singUp ###############################
@never_cache
def userLogin(request):
    # print("Submit value:", request.POST.get('submit'))

    # if request.user.is_authenticated:
    #     return redirect('userHome') 
    
    active_form = 'login'  # Default active form
    print("Initial active_form:", active_form)

    def clean_email(email):
        mail_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if re.fullmatch(mail_regex, email):
            return email
        else:
            raise ValidationError("Invalid email format")

    def clean_password(password):
        if len(password) < 8:
            raise ValidationError("Password should contain at least 8 characters.")
        if not re.search("[A-Z]", password):
            raise ValidationError("Password should contain at least one uppercase letter.")
        if not re.search("[a-z]", password):
            raise ValidationError("Password should contain at least one lowercase letter.")
        if not re.search("[0-9]", password):
            raise ValidationError("Password should contain at least one digit.")
        if not re.search("[@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError("Password should contain at least one special character.")
        return password

    if request.method == 'POST':
        if request.POST.get('submit') == 'login_form':
        ## login the user
        
            username = request.POST.get('loginUsername')
            password = request.POST.get('loginPassword')
            active_form = 'login'

            if not username:
                messages.error(request, "Enter the Email")
            elif not password:
                messages.error(request, "Enter the Password")
            else:
                user = authenticate(username=username, password=password)
                if user is None:
                    messages.error(request, "Invalid Email Id or Password")
                else:
                    auth_login(request, user)
                    return redirect('userHome')

        elif request.POST.get('submit') == 'signup_form':
            ## signUp new user
            
            signUp_username = request.POST['signupUsername']
            signUp_email = request.POST['signupEmail']
            signUp_password1 = request.POST['signupPassword']
            signUp_password2 = request.POST['signupConfirmationPassword']
            active_form = 'signup'
            
            if User.objects.filter(username=signUp_username).exists():
                messages.error(request, f"User name '{signUp_username}' is already taken")
            elif User.objects.filter(email=signUp_email).exists():
                messages.error(request, f"Mail Id '{signUp_email}' already has an account")
            elif signUp_password1 != signUp_password2:
                messages.error(request, "Passwords do not match")
            else:
                    if not signUp_username:
                        messages.error(request, "Enter the username")
                    elif not signUp_email:
                        messages.error(request, "Enter the email")
                    elif not signUp_password1:
                        messages.error(request, "Enter the Password")
                    elif not signUp_password2:
                        messages.error(request, "Enter the Confirmation Password")
                    else:
                
                        try:
                            clean_email(signUp_email)
                            clean_password(signUp_password1)
                        except ValidationError as e:
                            messages.error(request, e.message)
                        else:
                            # Save user data to session
                            request.session['username'] = signUp_username
                            request.session['email'] = signUp_email
                            request.session['password'] = signUp_password1

                            # Generate OTP and send it via email
                            otp = generate_otp()
                            send_otp(signUp_email, otp)
                            request.session['otp'] = otp
                            request.session['otp_creation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            return redirect('otp')
                            messages.success(request, f"New user '{signUp_username}' is created")
                            return redirect('userLogin')

    print("Final active_form:", active_form)
    return render(request, "login.html", {'active_form': active_form})

def otp(request):
    # Retrieve user data from session
    username = request.session.get('username')
    email = request.session.get('email')
    password = request.session.get('password')
    otp_creation_time_str = request.session.get('otp_creation_time')
    
    # Check if user data is present in session
    if not (username and email and password):
        return redirect('userLogin')
    
    otp_creation_time = datetime.strptime(otp_creation_time_str, '%Y-%m-%d %H:%M:%S')
    otp_expiry_time = otp_creation_time + timedelta(minutes=5)

    if datetime.now() > otp_expiry_time:
        messages.error(request, "OTP has expired. Please sign up again.")
        return redirect('userLogin')

    if request.method == 'POST':
        # Assuming your OTP fields are named 'ist', 'sec', 'third', 'fourth', and 'fifth'
        otp_digits = [request.POST.get('ist', ''),
                      request.POST.get('sec', ''),
                      request.POST.get('third', ''),
                      request.POST.get('fourth', ''),
                      request.POST.get('fifth', '')]

        # Concatenate OTP digits into a single OTP string
        otp = ''.join(otp_digits)
        print("otp",otp)
        # Retrieve OTP from session
        session_otp = request.session.get('otp')
        print("session",otp)
        if otp == session_otp:
            # OTP is correct, create user and log in
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = True
            user.save()
            # auth_login(request, user)
            return redirect('userLogin')
        else:
            # Invalid OTP, display error message
            messages.error(request,"Ivalid otp")
            return render(request, 'otp.html')

    return render(request, 'otp.html')

def resend_otp(request):
    if request.method == 'GET':
        # Retrieve user email from session
        email = request.session.get('email')
        
        # Generate new OTP and update session
        new_otp = generate_otp()
        request.session['otp'] = new_otp
        request.session['otp_creation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Resend OTP via email (assuming send_otp function sends the OTP)
        send_otp(email, new_otp)
        
        # Display success message
        messages.success(request, "OTP has been resent.")
        
        # Redirect back to OTP page
        return redirect('otp')
########################## function for home page ############################
# @login_required(login_url='userLogin')
# @never_cache
def userHome(request):
    # if request.user.is_authenticated:
        return render(request,"home.html")

########################## function for logout ############################
def logout(request):
    auth_logout(request)
    return redirect('userLogin')

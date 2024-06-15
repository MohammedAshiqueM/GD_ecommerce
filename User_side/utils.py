import random
from django.core.mail import send_mail
import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', '.env')
load_dotenv(dotenv_path)

# Retrieve the email address from the environment variable
from_email = os.getenv('EMAIL_HOST_USER')

def generate_otp():
    return str(random.randint(10000, 99999))

def send_otp(email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}'
    from_email = os.getenv('EMAIL_HOST_USER')
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

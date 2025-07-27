import os
import random
import string
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logging.basicConfig(level=logging.INFO)

def generate_random_key(length=6):
    """Generate a random numeric key for the OTP."""
    return "".join(random.choices(string.digits, k=length))

def send_verification_email(request, user, otp):
    """
    Sends a verification email to the user with an OTP.
    
    This function now uses Django's template engine to render the email,
    ensuring all template variables are correctly replaced.
    """
    try:
        subject = "Verify Your Almanac Account"
        # Use a relative path that Django's template loader can find.
        # This assumes your template is in 'stocks/templates/email/'.
        template_name = 'email/verification_email.html'
        
        # Create a context dictionary with variables for the template.
        context = {
            'username': user.username,
            'otp_code': otp,
        }
        
        # Render the HTML message using the template and context.
        html_message = render_to_string(template_name, context)
        
        # Create a plain-text version of the email.
        plain_message = strip_tags(html_message)
        to_email = user.email

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=[to_email],
            html_message=html_message
        )
        
        return True
        
    except Exception as e:
        logging.error(f"Error sending verification email to {user.email}: {e}")
        return False
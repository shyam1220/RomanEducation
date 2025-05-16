import random
import string
import secrets
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request

def generate_otp(length=6):
    """Generate a random numeric OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def verify_otp(stored_otp, submitted_otp):
    """Verify if submitted OTP matches stored OTP."""
    return stored_otp == submitted_otp

# def is_valid_email(email):
#     """Validate email format."""
#     email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
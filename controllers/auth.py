import random
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user import User
from utils.email_sender import send_email
from utils.helpers import generate_otp

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        # Get form data
        user_data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'phone_number': request.form['phone_number'],
            'location': request.form['location'],
            'occupation': request.form['occupation']
        }
        
        # Check if email already exists
        if User.get_by_email(user_data['email']):
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html')
        
        # Insert user data
        User.create(user_data)
        
        # Generate and send OTP for email verification
        otp = generate_otp()
        User.save_otp(user_data['email'], otp, 'registration')
        
        email_body = f"""
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Thank you for registering with our course platform. Please use the following OTP to verify your email address:</p>
            <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
        </body>
        </html>
        """
        
        send_email(user_data['email'], "Email Verification OTP", email_body)
        
        # Store email in session for verification
        session['verification_email'] = user_data['email']
        
        return redirect(url_for('auth.verify_email'))
    
    return render_template('register.html')

@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Handle email verification."""
    if 'verification_email' not in session:
        return redirect(url_for('auth.register'))
    
    email = session['verification_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if User.verify_otp(email, otp, 'registration'):
            # Mark email as verified
            User.update_email_verification(email, True)
            
            flash('Email verified successfully! You can now login.', 'success')
            session.pop('verification_email', None)
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('verify_email.html', email=email)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP for email verification."""
    if 'verification_email' not in session:
        return jsonify({'status': 'error', 'message': 'No email found for verification'})
    
    email = session['verification_email']
    otp = generate_otp()
    User.save_otp(email, otp, 'registration')
    
    email_body = f"""
    <html>
    <body>
        <h2>Verify Your Email Address</h2>
        <p>Here is your new OTP to verify your email address:</p>
        <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
        <p>This OTP will expire in 10 minutes.</p>
    </body>
    </html>
    """
    
    if send_email(email, "New Email Verification OTP", email_body):
        return jsonify({'status': 'success', 'message': 'New OTP sent to your email'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send OTP. Please try again.'})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if user exists and email is verified
        user = User.get_by_email(email)
        
        if not user:
            flash('Email not registered. Please register first.', 'danger')
            return render_template('login.html')
        
        if not user['email_verified']:
            session['verification_email'] = email
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('auth.verify_email'))
        
        # Generate and send OTP for login
        otp = generate_otp()
        User.save_otp(email, otp, 'login')
        
        email_body = f"""
        <html>
        <body>
            <h2>Login OTP</h2>
            <p>Use the following OTP to login to your account:</p>
            <h3 style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 24px;">{otp}</h3>
            <p>This OTP will expire in 10 minutes.</p>
        </body>
        </html>
        """
        
        send_email(email, "Login OTP", email_body)
        
        # Store email in session for OTP verification
        session['login_email'] = email
        
        return redirect(url_for('auth.verify_login'))
    
    return render_template('login.html')

@auth_bp.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
    """Handle login verification."""
    if 'login_email' not in session:
        return redirect(url_for('auth.login'))
    
    email = session['login_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if User.verify_otp(email, otp, 'login'):
            user = User.get_by_email(email)
            
            if user:
                session['user_id'] = user['id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session.pop('login_email', None)
                return redirect(url_for('user.home'))
        
        flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('login.html', verify_mode=True, email=email)

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('auth.login'))
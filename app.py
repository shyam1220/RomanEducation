import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets


from controllers.auth import auth_bp
from controllers.courses import courses_bp
from controllers.user import user_bp
from controllers.payment import payment_bp
import os
from datetime import datetime
import razorpay
from config import app_config

from decimal import Decimal

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(courses_bp, url_prefix='/courses')
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(payment_bp, url_prefix='/payment')

# Database configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': '',  # Default XAMPP password is empty
#     'database': 'course_registration'
# }

db_config = {
    'host': 'bnpn8bf9dbappwuwevvh-mysql.services.clever-cloud.com',  # Replace with your host
    'user': 'uvtqwkyuu61gaskr',               # Replace with your username
    'password': 'YOM0ukqfeqYpmBuAMsIJ',           # Replace with your password
    'database': 'bnpn8bf9dbappwuwevvh',           # Replace with your database name
    'port': 3306                                        # MySQL default port
}



# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=("rzp_test_JkbAxq5JbkMpIB", "B8lCButNGCldzgnZ6MYI25Mb")
)


# Helper functions
def get_db_connection():
    return mysql.connector.connect(**db_config)

def send_email(to_email, subject, body):
    # Configure this with your email provider details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "varadharaj160@gmail.com"  # Replace with your email
    smtp_password = "jlsbkoanclltyfdy"     # Replace with your app password
    
    # Create message
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = to_email
    message["Subject"] = subject
    
    # Add body to email
    message.attach(MIMEText(body, "html"))
    
    try:
        # Create SMTP session
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.send_message(message)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def save_otp(email, otp, purpose):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete any existing OTPs for this email and purpose
    cursor.execute(
        "DELETE FROM otp_verification WHERE email = %s AND purpose = %s",
        (email, purpose)
    )
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Save new OTP
    cursor.execute(
        "INSERT INTO otp_verification (email, otp, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (email, otp, purpose, expires_at)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def verify_otp(email, otp, purpose):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM otp_verification WHERE email = %s AND otp = %s AND purpose = %s AND expires_at > NOW()",
        (email, otp, purpose)
    )
    
    result = cursor.fetchone()
    
    if result:
        # OTP is valid, delete it to prevent reuse
        cursor.execute("DELETE FROM otp_verification WHERE id = %s", (result['id'],))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    cursor.close()
    conn.close()
    return False



# Tax calculation function
def calculate_tax(price):
    """Calculate tax (18%) from a price"""
    tax_rate = Decimal('0.18')
    return price * tax_rate


def get_course_image_by_title(title):
    """
    Get an appropriate image for a course based on keywords in its title.
    """
    title = title.lower() if title else ""
    
    # Programming languages
    if any(keyword in title for keyword in ["startertrack"]):
        return "/static/images/courses/startertrack.webp"
    
    # Web development
    elif any(keyword in title for keyword in ["launchpro"]):
        return "/static/images/courses/launchpro.jpg"
    
    # Data science
    elif any(keyword in title for keyword in ["careerboost"]):
        return "/static/images/courses/careerboost.avif"
    
    # Design
    elif any(keyword in title for keyword in ["devpath"]):
        return "/static/images/courses/fullstack.png"
    
    # Business
    elif any(keyword in title for keyword in ["prosuite"]):
        return "/static/images/courses/prosuit.jpg"
    
    # Language learning
    elif any(keyword in title for keyword in ["language", "english", "spanish", "french", "german", 
                                             "japanese", "chinese", "italian"]):
        return "/static/images/courses/language.jpg"
    
   
    
    # Default image if no specific category is matched
    else:
        return "/static/images/courses/careerboost.jpg"
    
@app.context_processor
def utility_processor():
    return dict(get_course_image_by_title=get_course_image_by_title)
# Routes

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user_home'))
    return redirect(url_for('login'))



@app.context_processor
def inject_globals():
    """Add global variables to all templates."""
    return {
        'now': datetime.now(),
        'razorpay_key_id': app_config.RAZORPAY_KEY_ID
    }

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        location = request.form['location']
        occupation = request.form['occupation']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            flash('Email already registered. Please use a different email or login.', 'danger')
            return render_template('register.html', now=datetime.now())
        
        # Insert user data
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, phone_number, location, occupation) VALUES (%s, %s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone_number, location, occupation)
        )
        conn.commit()
        
        # Generate and send OTP for email verification
        otp = generate_otp()
        save_otp(email, otp, 'registration')
        
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
        
        send_email(email, "Email Verification OTP", email_body)
        
        # Store email in session for verification
        session['verification_email'] = email
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('verify_email'))
    
    return render_template('register.html', now=datetime.now())

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if 'verification_email' not in session:
        return redirect(url_for('register'))
    
    email = session['verification_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if verify_otp(email, otp, 'registration'):
            # Mark email as verified
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (email,))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Email verified successfully! You can now login.', 'success')
            session.pop('verification_email', None)
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('verify_email.html', email=email, now=datetime.now())

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'verification_email' not in session:
        return jsonify({'status': 'error', 'message': 'No email found for verification'})
    
    email = session['verification_email']
    otp = generate_otp()
    save_otp(email, otp, 'registration')
    
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists and email is verified
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            flash('Email not registered. Please register first.', 'danger')
            return render_template('login.html', now=datetime.now())
        
        if not user['email_verified']:
            session['verification_email'] = email
            cursor.close()
            conn.close()
            flash('Please verify your email before logging in.', 'warning')
            return redirect(url_for('verify_email'))
        
        # Generate and send OTP for login
        otp = generate_otp()
        save_otp(email, otp, 'login')
        
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
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('verify_login'))
    
    return render_template('login.html', now=datetime.now())

@app.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
    if 'login_email' not in session:
        return redirect(url_for('login'))
    
    email = session['login_email']
    
    if request.method == 'POST':
        otp = request.form['otp']
        
        if verify_otp(email, otp, 'login'):
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name, last_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session.pop('login_email', None)
                return redirect(url_for('user_home'))
        
        flash('Invalid or expired OTP. Please try again.', 'danger')
    
    return render_template('login.html', verify_mode=True, email=email, now=datetime.now())

@app.route('/user-home')
def user_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user profile
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    # Get user's registered courses
    cursor.execute("""
        SELECT c.*, uc.registration_date, uc.payment_status 
        FROM courses c 
        JOIN user_courses uc ON c.id = uc.course_id 
        WHERE uc.user_id = %s AND uc.payment_status = 'completed'
    """, (session['user_id'],))
    registered_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('user_home.html', user=user, registered_courses=registered_courses, now=datetime.now())

@app.route('/all-courses')
def all_courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all courses
    cursor.execute("SELECT * FROM courses")
    all_courses = cursor.fetchall()
    
    # Get user's registered courses for exclusion
    cursor.execute(
        "SELECT course_id FROM user_courses WHERE user_id = %s AND payment_status = 'completed'", 
        (session['user_id'],)
    )
    registered_course_ids = [row['course_id'] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return render_template(
        'all_courses.html', 
        courses=all_courses, 
        registered_course_ids=registered_course_ids,
        now=datetime.now()
    )

@app.route('/registered-courses')
def registered_courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user's registered courses
    cursor.execute("""
        SELECT c.*, uc.registration_date, uc.payment_status 
        FROM courses c 
        JOIN user_courses uc ON c.id = uc.course_id 
        WHERE uc.user_id = %s AND uc.payment_status = 'completed'
    """, (session['user_id'],))
    registered_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('registered_courses.html', courses=registered_courses, now=datetime.now())

@app.route('/payment/<int:course_id>')
def payment(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get course details
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    
    # Check if user already registered for this course
    cursor.execute(
        "SELECT * FROM user_courses WHERE user_id = %s AND course_id = %s AND payment_status = 'completed'",
        (session['user_id'], course_id)
    )
    
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash('You have already registered for this course.', 'info')
        return redirect(url_for('registered_courses'))
    
    # Get user email for the payment form
    cursor.execute("SELECT email FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    user_email = user['email'] if user else ''
    
    cursor.close()
    conn.close()
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('all_courses'))
    
    # Calculate tax and total beforehand to avoid template calculation errors
    tax = calculate_tax(course['price'])
    total = course['price'] + tax
    
    # Create Razorpay Order
    order_amount = int(total * 100)  # Converting to paise (smallest currency unit)
    order_currency = 'INR'
    
    # Generate unique receipt ID
    receipt_id = f'rcpt_{secrets.token_hex(6)}'
    
    # Create order in Razorpay
    try:
        order_data = {
            'amount': order_amount,
            'currency': order_currency,
            'receipt': receipt_id,
            'payment_capture': 1  # Auto-capture
        }
        razorpay_order = razorpay_client.order.create(data=order_data)
        razorpay_order_id = razorpay_order['id']
    except Exception as e:
        flash(f'Error creating payment order: {str(e)}', 'danger')
        return redirect(url_for('all_courses'))
    
    return render_template('payment.html', 
                           course=course, 
                           tax=tax, 
                           total=total,
                           razorpay_order_id=razorpay_order_id,
                           user_email=user_email,
                           now=datetime.now())


@app.route('/process-payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get payment details
    course_id = request.form.get('course_id')
    payment_id = request.form.get('payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')
    
    if not all([course_id, payment_id, razorpay_order_id, razorpay_signature]):
        flash('Missing payment information. Please try again.', 'danger')
        return redirect(url_for('payment', course_id=course_id))
    
    # Verify payment signature
    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        # Verify the payment signature
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if already registered
        cursor.execute(
            "SELECT id FROM user_courses WHERE user_id = %s AND course_id = %s",
            (session['user_id'], course_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute(
                "UPDATE user_courses SET payment_status = 'completed', payment_id = %s WHERE user_id = %s AND course_id = %s",
                (payment_id, session['user_id'], course_id)
            )
        else:
            # Create new registration
            cursor.execute(
                "INSERT INTO user_courses (user_id, course_id, payment_status, payment_id) VALUES (%s, %s, %s, %s)",
                (session['user_id'], course_id, 'completed', payment_id)
            )
        
        conn.commit()
        
        # Get user email and course details for confirmation email
        cursor.execute("SELECT email, first_name, last_name FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        user_email = user['email']
        user_name = f"{user['first_name']} {user['last_name']}"
        
        cursor.execute("SELECT title, price, duration FROM courses WHERE id = %s", (course_id,))
        course = cursor.fetchone()
        course_title = course['title']
        course_price = course['price']
        course_duration = course['duration']
        
        cursor.close()
        conn.close()
        
        # Send confirmation email to user
        email_body = f"""
        <html>
        <body>
            <h2>Course Registration Confirmation</h2>
            <p>Dear {user_name},</p>
            <p>Congratulations! You have successfully registered for the following course:</p>
            <table style="border-collapse: collapse; width: 100%; margin-top: 15px; margin-bottom: 15px;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Course</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{course_title}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Duration</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{course_duration}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Price</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">₹{course_price}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Payment ID</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{payment_id}</td>
                </tr>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Order ID</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{razorpay_order_id}</td>
                </tr>
            </table>
            <p>You can access your course materials from your dashboard.</p>
            <p>Thank you for choosing our platform!</p>
            <p>Best regards,<br>Course Registration Team</p>
        </body>
        </html>
        """
        
        send_email(user_email, "Course Registration Confirmation", email_body)
        
        # Send notification email to admin (if configured)
        if hasattr(app_config, 'ADMIN_EMAIL'):
            admin_email = app_config.ADMIN_EMAIL
            admin_email_body = f"""
            <html>
            <body>
                <h2>New Course Registration</h2>
                <p>A new course registration has been completed:</p>
                <table style="border-collapse: collapse; width: 100%; margin-top: 15px; margin-bottom: 15px;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">User</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{user_name} ({user_email})</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Course</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{course_title}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Duration</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{course_duration}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Price</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">₹{course_price}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Payment ID</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{payment_id}</td>
                    </tr>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Order ID</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{razorpay_order_id}</td>
                    </tr>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Registration Date</th>
                        <td style="border: 1px solid #ddd; padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            send_email(admin_email, "New Course Registration Notification", admin_email_body)
        
        flash('Payment successful! You have been registered for the course.', 'success')
        return redirect(url_for('registered_courses'))
    
    except Exception as e:
        print(f"Payment verification error: {e}")
        flash('Payment verification failed. Please try again or contact support.', 'danger')
        return redirect(url_for('payment', course_id=course_id))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.context_processor
def inject_now():
    """Add the current datetime to all templates."""
    return {'now': datetime.now()}

if __name__ == '__main__':
    app.run(debug=True)

import razorpay
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from utils.email_sender import send_email
from database import Database
import secrets
from datetime import datetime

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/create_razorpay_order', methods=['POST'])
def create_razorpay_order():
    """Create a Razorpay order for payment processing."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'})
    
    try:
        # Get request data
        data = request.get_json()
        course_id = data.get('course_id')
        amount = data.get('amount')  # Amount in paise
        
        # Initialize Razorpay client
        client = razorpay.Client(
            auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET'])
        )
        
        # Create order
        order_data = {
            'amount': amount,  # amount in paise
            'currency': 'INR',
            'receipt': f'rcpt_{secrets.token_hex(6)}',
            'payment_capture': 1  # Auto-capture
        }
        
        order = client.order.create(data=order_data)
        
        # Store order details in database for verification later
        order_info = {
            'user_id': session['user_id'],
            'course_id': course_id,
            'order_id': order['id'],
            'amount': amount / 100,  # Convert back to rupees for storage
            'status': 'created',
            'created_at': datetime.now()
        }
        
        Database.insert('payment_orders', order_info)
        
        return jsonify({
            'status': 'success',
            'order_id': order['id']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        })

@payment_bp.route('/process-payment', methods=['POST'])
def process_payment():
    """Process payment after Razorpay callback."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    try:
        # Get payment details
        payment_id = request.form.get('razorpay_payment_id')
        order_id = request.form.get('razorpay_order_id')
        signature = request.form.get('razorpay_signature')
        course_id = request.form.get('course_id')
        
        # Initialize Razorpay client
        client = razorpay.Client(
            auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET'])
        )
        
        # Verify payment signature
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': 'Payment verification failed'
            })
        
        # Update order status in database
        Database.update(
            'payment_orders',
            {'status': 'paid', 'payment_id': payment_id},
            'order_id = %s',
            (order_id,)
        )
        
        # Register user for the course
        conn = Database.get_connection()
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
        user_email_body = f"""
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{order_id}</td>
                </tr>
            </table>
            <p>You can access your course materials from your dashboard.</p>
            <p>Thank you for choosing our platform!</p>
            <p>Best regards,<br>Course Registration Team</p>
        </body>
        </html>
        """
        
        send_email(user_email, "Course Registration Confirmation", user_email_body)
        
        # Send notification email to admin
        admin_email = current_app.config['ADMIN_EMAIL']
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
                    <td style="border: 1px solid #ddd; padding: 8px;">{order_id}</td>
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
        
        return jsonify({'status': 'success', 'message': 'Payment successful'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
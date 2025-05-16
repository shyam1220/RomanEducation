from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user import User
from models.course import Course
import secrets
from utils.email_sender import send_email

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/all-courses')
def all_courses():
    """Display all available courses."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get all courses
    all_courses = Course.get_all()
    
    # Get user's registered courses for exclusion
    registered_course_ids = Course.get_user_registered_course_ids(session['user_id'])
    
    return render_template(
        'all_courses.html', 
        courses=all_courses, 
        registered_course_ids=registered_course_ids
    )

@courses_bp.route('/registered-courses')
def registered_courses():
    """Display user's registered courses."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get user's registered courses
    user_courses = User.get_registered_courses(session['user_id'])
    
    return render_template('registered_courses.html', courses=user_courses)

@courses_bp.route('/payment/<int:course_id>')
def payment(course_id):
    """Display payment page for a course."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get course details
    course = Course.get_by_id(course_id)
    
    # Check if user already registered for this course
    if Course.is_user_registered(session['user_id'], course_id):
        flash('You have already registered for this course.', 'info')
        return redirect(url_for('courses.registered_courses'))
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('courses.all_courses'))
    
    return render_template('payment.html', course=course)

@courses_bp.route('/process-payment', methods=['POST'])
def process_payment():
    """Process payment for a course."""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'})
    
    course_id = request.form.get('course_id')
    
    try:
        # In a real application, you would process payment with a payment gateway
        # For demonstration, we'll assume payment is successful
        
        # Register user for the course with payment completed
        payment_id = f"PAY-{secrets.token_hex(6).upper()}"
        Course.register_user(
            session['user_id'], 
            course_id, 
            payment_status='completed', 
            payment_id=payment_id
        )
        
        # Get user email and course details for confirmation email
        user = User.get_by_id(session['user_id'])
        course = Course.get_by_id(course_id)
        
        # Send confirmation email
        email_body = f"""
        <html>
        <body>
            <h2>Course Registration Confirmation</h2>
            <p>Congratulations! You have successfully registered for the following course:</p>
            <p><strong>Course:</strong> {course['title']}</p>
            <p><strong>Price:</strong> ${course['price']}</p>
            <p>You can access your course materials from your dashboard.</p>
            <p>Thank you for choosing our platform!</p>
        </body>
        </html>
        """
        
        send_email(user['email'], "Course Registration Confirmation", email_body)
        
        return jsonify({'status': 'success', 'message': 'Payment successful'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
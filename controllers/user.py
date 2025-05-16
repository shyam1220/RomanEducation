from flask import Blueprint, render_template, redirect, url_for, session
from models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/home')
def home():
    """Display user dashboard/home page."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get user profile
    user = User.get_by_id(session['user_id'])
    
    # Get user's registered courses
    registered_courses = User.get_registered_courses(session['user_id'])
    
    return render_template('user_home.html', user=user, registered_courses=registered_courses)
from database import Database

class User:
    """User model for managing user data."""
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        return Database.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        return Database.execute_query(query, (email,), fetch_one=True)
    
    @staticmethod
    def create(user_data):
        """
        Create a new user.
        
        Args:
            user_data (dict): User data with keys:
                - first_name: First name
                - last_name: Last name
                - email: Email address
                - phone_number: Phone number
                - location: Location
                - occupation: Occupation
                
        Returns:
            int: User ID if successful
        """
        return Database.insert('users', user_data)
    
    @staticmethod
    def update_email_verification(email, verified=True):
        """Mark a user's email as verified."""
        return Database.update(
            'users',
            {'email_verified': verified},
            'email = %s',
            (email,)
        )
    
    @staticmethod
    def update_profile(user_id, user_data):
        """
        Update user profile information.
        
        Args:
            user_id (int): User ID
            user_data (dict): User data to update
                
        Returns:
            bool: True if successful
        """
        return Database.update(
            'users',
            user_data,
            'id = %s',
            (user_id,)
        )
    
    @staticmethod
    def save_otp(email, otp, purpose):
        """
        Save OTP for email verification or login.
        
        Args:
            email (str): User email
            otp (str): One-time password
            purpose (str): 'registration' or 'login'
                
        Returns:
            int: OTP ID if successful
        """
        # Delete any existing OTPs for this email and purpose
        Database.delete(
            'otp_verification',
            'email = %s AND purpose = %s',
            (email, purpose)
        )
        
        # Calculate expiration time
        from datetime import datetime, timedelta
        from config import app_config
        
        expires_at = datetime.now() + timedelta(minutes=app_config.OTP_EXPIRY_MINUTES)
        
        # Save new OTP
        otp_data = {
            'email': email,
            'otp': otp,
            'purpose': purpose,
            'expires_at': expires_at
        }
        
        return Database.insert('otp_verification', otp_data)
    
    @staticmethod
    def verify_otp(email, otp, purpose):
        """
        Verify OTP for the given email and purpose.
        
        Args:
            email (str): User email
            otp (str): One-time password
            purpose (str): 'registration' or 'login'
                
        Returns:
            bool: True if OTP is valid
        """
        query = """
            SELECT * FROM otp_verification 
            WHERE email = %s AND otp = %s AND purpose = %s AND expires_at > NOW()
        """
        
        result = Database.execute_query(
            query,
            (email, otp, purpose),
            fetch_one=True
        )
        
        if result:
            # OTP is valid, delete it to prevent reuse
            Database.delete(
                'otp_verification',
                'id = %s',
                (result['id'],)
            )
            return True
        
        return False
    
    @staticmethod
    def get_registered_courses(user_id):
        """
        Get all courses registered by the user.
        
        Args:
            user_id (int): User ID
                
        Returns:
            list: List of course dictionaries
        """
        query = """
            SELECT c.*, uc.registration_date, uc.payment_status 
            FROM courses c 
            JOIN user_courses uc ON c.id = uc.course_id 
            WHERE uc.user_id = %s AND uc.payment_status = 'completed'
        """
        
        return Database.execute_query(query, (user_id,), fetch=True)
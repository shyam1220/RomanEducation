from database import Database

class Course:
    """Course model for managing course data."""
    
    @staticmethod
    def get_by_id(course_id):
        """Get course by ID."""
        query = "SELECT * FROM courses WHERE id = %s"
        return Database.execute_query(query, (course_id,), fetch_one=True)
    
    @staticmethod
    def get_all():
        """Get all courses."""
        query = "SELECT * FROM courses"
        return Database.execute_query(query, fetch=True)
    
    @staticmethod
    def register_user(user_id, course_id, payment_status='pending', payment_id=None):
        """
        Register a user for a course.
        
        Args:
            user_id (int): User ID
            course_id (int): Course ID
            payment_status (str): Payment status ('pending' or 'completed')
            payment_id (str): Payment ID from payment gateway
                
        Returns:
            int: Registration ID if successful
        """
        # Check if already registered
        query = "SELECT id FROM user_courses WHERE user_id = %s AND course_id = %s"
        existing = Database.execute_query(query, (user_id, course_id), fetch_one=True)
        
        if existing:
            # Update existing record
            Database.update(
                'user_courses',
                {
                    'payment_status': payment_status,
                    'payment_id': payment_id
                },
                'user_id = %s AND course_id = %s',
                (user_id, course_id)
            )
            return existing['id']
        else:
            # Create new registration
            course_data = {
                'user_id': user_id,
                'course_id': course_id,
                'payment_status': payment_status,
                'payment_id': payment_id
            }
            return Database.insert('user_courses', course_data)
    
    @staticmethod
    def is_user_registered(user_id, course_id):
        """
        Check if a user is registered for a course.
        
        Args:
            user_id (int): User ID
            course_id (int): Course ID
                
        Returns:
            bool: True if user is registered for the course
        """
        query = """
            SELECT COUNT(*) as count FROM user_courses 
            WHERE user_id = %s AND course_id = %s AND payment_status = 'completed'
        """
        
        result = Database.execute_query(query, (user_id, course_id), fetch_one=True)
        return result['count'] > 0
    
    @staticmethod
    def get_user_registered_course_ids(user_id):
        """
        Get IDs of all courses registered by the user.
        
        Args:
            user_id (int): User ID
                
        Returns:
            list: List of course IDs
        """
        query = """
            SELECT course_id FROM user_courses 
            WHERE user_id = %s AND payment_status = 'completed'
        """
        
        results = Database.execute_query(query, (user_id,), fetch=True)
        return [row['course_id'] for row in results]
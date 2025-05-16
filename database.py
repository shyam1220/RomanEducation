from mysql.connector import connect, Error
from config import app_config

class Database:
    """Database connection and helper methods."""
    
    @staticmethod
    def get_connection():
        """Get a MySQL database connection."""
        return connect(
            host=app_config.DB_HOST,
            user=app_config.DB_USER,
            password=app_config.DB_PASSWORD,
            database=app_config.DB_NAME
        )
    
    @staticmethod
    def execute_query(query, params=None, fetch=False, fetch_one=False):
        """
        Execute a SQL query with parameters.
        
        Args:
            query (str): SQL query
            params (tuple): Query parameters
            fetch (bool): Whether to fetch all results
            fetch_one (bool): Whether to fetch one result
                
        Returns:
            list/dict/int: Query results or row count
        """
        conn = Database.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
                
            return result
        
        except Error as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def insert(table, data):
        """
        Insert data into a table.
        
        Args:
            table (str): Table name
            data (dict): Data to insert
                
        Returns:
            int: ID of inserted row
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, list(data.values()))
            conn.commit()
            return cursor.lastrowid
        
        except Error as e:
            conn.rollback()
            raise e
        
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update(table, data, where_clause, where_params):
        """
        Update data in a table.
        
        Args:
            table (str): Table name
            data (dict): Data to update
            where_clause (str): WHERE clause
            where_params (tuple): WHERE parameters
                
        Returns:
            int: Number of rows affected
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        params = list(data.values()) + list(where_params) if isinstance(where_params, tuple) else list(data.values()) + [where_params]
        
        return Database.execute_query(query, params)
    
    @staticmethod
    def delete(table, where_clause, where_params):
        """
        Delete data from a table.
        
        Args:
            table (str): Table name
            where_clause (str): WHERE clause
            where_params (tuple): WHERE parameters
                
        Returns:
            int: Number of rows affected
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        return Database.execute_query(query, where_params)
from database.db import get_db_connection
from mysql.connector import Error
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

class HotelManager:
    @staticmethod
    def create_account(name, email, username, password):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT * FROM managers WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Username or email already exists!'}
            
            # Insert new manager
            hashed_password = hash_password(password)
            cursor.execute(
                "INSERT INTO managers (name, email, username, password) VALUES (%s, %s, %s, %s)",
                (name, email, username, hashed_password)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'Account created successfully!'}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}
    
    @staticmethod
    def login(username, password):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Find manager by username
            cursor.execute("SELECT * FROM managers WHERE username = %s", (username,))
            manager = cursor.fetchone()
            
            if not manager:
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Username not found!'}
            
            # Check password
            hashed_password = hash_password(password)
            if manager[4] != hashed_password:  # manager[4] is the password column
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Incorrect password!'}
            
            manager_id = manager[0]
            manager_name = manager[1]
            
            # Fetch hotel assignment and modules for this manager
            cursor.execute("""
                SELECT hma.hotel_id, hm.kyc_enabled, hm.food_enabled, h.hotel_name
                FROM hotel_managers hma
                JOIN hotel_modules hm ON hma.hotel_id = hm.hotel_id
                JOIN hotels h ON hma.hotel_id = h.id
                WHERE hma.manager_id = %s
                LIMIT 1
            """, (manager_id,))
            hotel_data = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if hotel_data:
                return {
                    'success': True,
                    'message': 'Login successful!',
                    'name': manager_name,
                    'id': manager_id,
                    'hotel_id': hotel_data[0],
                    'kyc_enabled': bool(hotel_data[1]),
                    'food_enabled': bool(hotel_data[2]),
                    'hotel_name': hotel_data[3]
                }
            else:
                # Manager not assigned to any hotel yet
                return {
                    'success': True,
                    'message': 'Login successful!',
                    'name': manager_name,
                    'id': manager_id,
                    'hotel_id': None,
                    'kyc_enabled': False,
                    'food_enabled': False,
                    'hotel_name': None
                }
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}
    
    @staticmethod
    def get_all_managers():
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, email, username, created_at FROM managers")
            managers = cursor.fetchall()
            cursor.close()
            connection.close()
            return managers
        except Error as exc:
            return None

    @staticmethod
    def delete_manager(manager_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Verify manager exists
            cursor.execute("SELECT * FROM managers WHERE id = %s", (manager_id,))
            if not cursor.fetchone():
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Manager not found!'}

            # Delete manager (waiters will cascade)
            cursor.execute("DELETE FROM managers WHERE id = %s", (manager_id,))
            connection.commit()
            cursor.close()
            connection.close()

            return {'success': True, 'message': 'Manager deleted successfully!'}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}

class Waiter:
    @staticmethod
    def create_waiter(manager_id, name, email, phone, hotel_id=None):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT * FROM waiters WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Email already exists!'}
            
            # Insert new waiter
            cursor.execute(
                "INSERT INTO waiters (manager_id, name, email, phone, hotel_id) VALUES (%s, %s, %s, %s, %s)",
                (manager_id, name, email, phone, hotel_id)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'Waiter created successfully!'}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}
    
    @staticmethod
    def get_waiters_by_hotel(hotel_id):
        """Get all waiters for a specific hotel"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            if hotel_id:
                cursor.execute("SELECT id, name, email, phone, created_at FROM waiters WHERE hotel_id = %s", (hotel_id,))
            else:
                cursor.execute("SELECT id, name, email, phone, created_at FROM waiters")
            waiters = cursor.fetchall()
            cursor.close()
            connection.close()
            return waiters
        except Error as exc:
            return None
    
    @staticmethod
    def get_waiters_by_manager(manager_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, email, phone, created_at FROM waiters WHERE manager_id = %s", (manager_id,))
            waiters = cursor.fetchall()
            cursor.close()
            connection.close()
            return waiters
        except Error as exc:
            return None
    
    @staticmethod
    def delete_waiter(waiter_id, hotel_id=None):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Verify waiter belongs to this hotel
            if hotel_id:
                cursor.execute("SELECT * FROM waiters WHERE id = %s AND hotel_id = %s", (waiter_id, hotel_id))
            else:
                cursor.execute("SELECT * FROM waiters WHERE id = %s", (waiter_id,))
            if not cursor.fetchone():
                cursor.close()
                connection.close()
                return {'success': False, 'message': 'Waiter not found!'}
            
            cursor.execute("DELETE FROM waiters WHERE id = %s", (waiter_id,))
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'Waiter deleted successfully!'}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}
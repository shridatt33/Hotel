from database.db import get_db_connection
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename

class GuestVerification:
    @staticmethod
    def create_table():
        """Create guest_verifications table directly in MySQL"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Create table directly using cursor execution
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guest_verifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    manager_id INT NOT NULL,
                    hotel_id INT,
                    guest_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    kyc_number VARCHAR(100) NOT NULL,
                    identity_file VARCHAR(500),
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
                )
            """)
            
            # Ensure hotel_id column exists
            cursor.execute("SHOW COLUMNS FROM guest_verifications LIKE 'hotel_id'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE guest_verifications ADD COLUMN hotel_id INT")
            
            # Also create kyc_verifications as alias for admin dashboard compatibility
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kyc_verifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    manager_id INT NOT NULL,
                    guest_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    kyc_number VARCHAR(100) NOT NULL,
                    identity_file VARCHAR(500),
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE
                )
            """)
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Error as exc:
            print(f"Error creating table: {exc}")
            return False

    @staticmethod
    def submit_verification(manager_id, guest_name, phone, address, kyc_number, identity_file=None, hotel_id=None):
        """Submit new guest verification directly to MySQL"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Insert data directly using cursor execution
            cursor.execute("""
                INSERT INTO guest_verifications 
                (manager_id, guest_name, phone, address, kyc_number, identity_file, hotel_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (manager_id, guest_name, phone, address, kyc_number, identity_file, hotel_id))
            
            connection.commit()
            verification_id = cursor.lastrowid
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'Verification submitted successfully!', 'id': verification_id}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}

    @staticmethod
    def get_verifications_by_hotel(hotel_id):
        """Get all verifications for a specific hotel from MySQL"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Fetch data directly using cursor execution
            if hotel_id:
                cursor.execute("""
                    SELECT id, guest_name, phone, address, kyc_number, 
                           identity_file, submitted_at, status 
                    FROM guest_verifications 
                    WHERE hotel_id = %s 
                    ORDER BY submitted_at DESC
                """, (hotel_id,))
            else:
                cursor.execute("""
                    SELECT id, guest_name, phone, address, kyc_number, 
                           identity_file, submitted_at, status 
                    FROM guest_verifications 
                    ORDER BY submitted_at DESC
                """)
            
            verifications = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return verifications
        except Error as exc:
            print(f"Error fetching verifications: {exc}")
            return []

    @staticmethod
    def get_verifications_by_manager(manager_id):
        """Get all verifications for a specific manager from MySQL"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Fetch data directly using cursor execution
            cursor.execute("""
                SELECT id, guest_name, phone, address, kyc_number, 
                       identity_file, submitted_at, status 
                FROM guest_verifications 
                WHERE manager_id = %s 
                ORDER BY submitted_at DESC
            """, (manager_id,))
            
            verifications = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return verifications
        except Error as exc:
            print(f"Error fetching verifications: {exc}")
            return []

    @staticmethod
    def update_status(verification_id, status):
        """Update verification status directly in MySQL"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Update data directly using cursor execution
            cursor.execute("""
                UPDATE guest_verifications 
                SET status = %s 
                WHERE id = %s
            """, (status, verification_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return {'success': True, 'message': 'Status updated successfully!'}
        except Error as exc:
            return {'success': False, 'message': f'Database error: {str(exc)}'}

    @staticmethod
    def save_uploaded_file(file, manager_id):
        """Save uploaded file securely"""
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Create unique filename with manager_id prefix
            import time
            timestamp = str(int(time.time()))
            filename = f"manager_{manager_id}_{timestamp}_{filename}"
            
            # Create uploads directory if not exists
            upload_dir = os.path.join('static', 'uploads', 'verifications')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            return f"uploads/verifications/{filename}"
        return None
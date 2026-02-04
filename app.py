import os
import mysql.connector
from flask import Flask, render_template, request, jsonify
from mysql.connector import Error
from hotel_manager import hotel_manager_bp
from admin import admin_bp
from guest_verification import guest_verification_bp
from menu import menu_bp
from orders import orders_bp
from flask import redirect, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

# Register blueprints
app.register_blueprint(hotel_manager_bp, url_prefix='/hotel-manager')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(guest_verification_bp, url_prefix='/guest-verification')
app.register_blueprint(menu_bp)
app.register_blueprint(orders_bp, url_prefix='/orders')

def get_db_connection():
    """Create a MySQL connection using environment variables."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "Dattu@1234"),
        database=os.getenv("MYSQL_DATABASE", "hotelease"),
    )

def init_db():
    """Initialize database tables"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create managers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create waiters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waiters (
                id INT AUTO_INCREMENT PRIMARY KEY,
                manager_id INT NOT NULL,
                hotel_id INT,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
            )
        """)
        
        # Ensure waiters table has hotel_id column
        cursor.execute("SHOW COLUMNS FROM waiters LIKE 'hotel_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE waiters ADD COLUMN hotel_id INT")
            cursor.execute("ALTER TABLE waiters ADD FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE")

        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create hotels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hotel_name VARCHAR(255) NOT NULL,
                address TEXT,
                city VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ensure legacy hotels table has expected columns
        cursor.execute("SHOW COLUMNS FROM hotels LIKE 'city'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE hotels ADD COLUMN city VARCHAR(100)")

        cursor.execute("SHOW COLUMNS FROM hotels LIKE 'name'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE hotels MODIFY COLUMN name VARCHAR(255) NULL")

        cursor.execute("SHOW COLUMNS FROM hotels LIKE 'email'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE hotels MODIFY COLUMN email VARCHAR(100) NULL")

        cursor.execute("SHOW COLUMNS FROM hotels LIKE 'password'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE hotels MODIFY COLUMN password VARCHAR(255) NULL")
        
        # Create hotel_modules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotel_modules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hotel_id INT NOT NULL,
                kyc_enabled BOOLEAN DEFAULT FALSE,
                food_enabled BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
            )
        """)
        
        # Create hotel_managers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotel_managers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hotel_id INT NOT NULL,
                manager_id INT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE,
                FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE
            )
        """)
        
        # Create kyc_verifications table (alias for guest_verifications)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kyc_verifications (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES managers(id) ON DELETE CASCADE,
                FOREIGN KEY (hotel_id) REFERENCES hotels(id) ON DELETE CASCADE
            )
        """)
        
        # Ensure kyc_verifications table has hotel_id column
        cursor.execute("SHOW COLUMNS FROM kyc_verifications LIKE 'hotel_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE kyc_verifications ADD COLUMN hotel_id INT")
        
        # Create menu_categories table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hotel_id INT,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure menu_categories has hotel_id column
        cursor.execute("SHOW COLUMNS FROM menu_categories LIKE 'hotel_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE menu_categories ADD COLUMN hotel_id INT")
        
        # Create menu_dishes table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_dishes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hotel_id INT,
                category_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                quantity VARCHAR(50),
                description TEXT,
                images JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ensure menu_dishes has hotel_id column
        cursor.execute("SHOW COLUMNS FROM menu_dishes LIKE 'hotel_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE menu_dishes ADD COLUMN hotel_id INT")
        
        # Create default admin if not exists
        import hashlib
        cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
        if not cursor.fetchone():
            default_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO admins (name, username, password) VALUES (%s, %s, %s)",
                ('Administrator', 'admin', default_password)
            )
            print("Default admin created - Username: admin, Password: admin123")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Initialize guest verification table
        from guest_verification.models import GuestVerification
        GuestVerification.create_table()
        
        print("Database initialized successfully")
    except Error as exc:
        print(f"Error initializing database: {exc}")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/db-test")
def db_test():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        current_db = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify({
            "status": "success",
            "database": current_db[0] if current_db else None,
        })
    except Error as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route("/create-hotel", methods=["GET", "POST"])
def create_hotel_redirect():
    code = 307 if request.method == "POST" else 302
    return redirect(url_for("admin.create_hotel"), code=code)

if os.getenv("SKIP_DB_INIT") != "1":
    init_db()  # Initialize database tables on startup

if __name__ == "__main__":
    app.run(debug=True)

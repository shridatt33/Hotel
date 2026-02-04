from database.db import get_db_connection

class Table:
    @staticmethod
    def create_tables():
        """Create tables if not exist"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            def ensure_column(table_name, column_name, column_def):
                try:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = %s
                          AND COLUMN_NAME = %s
                        """,
                        (table_name, column_name)
                    )
                    exists = cursor.fetchone()[0]
                    if not exists:
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
                except Exception as e:
                    print(f"Error ensuring column {table_name}.{column_name}: {e}")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hotel_id INT,
                    table_number VARCHAR(50) NOT NULL,
                    qr_code_path VARCHAR(500),
                    current_session_id VARCHAR(100),
                    status ENUM('AVAILABLE', 'BUSY') DEFAULT 'AVAILABLE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_table_per_hotel (hotel_id, table_number)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS table_orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hotel_id INT,
                    table_id INT NOT NULL,
                    session_id VARCHAR(100),
                    items JSON NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    order_status ENUM('ACTIVE', 'PREPARING', 'COMPLETED') DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE
                )
            """)

            # Backward-compatible schema updates
            ensure_column("tables", "current_session_id", "current_session_id VARCHAR(100)")
            ensure_column("tables", "hotel_id", "hotel_id INT")
            ensure_column("table_orders", "session_id", "session_id VARCHAR(100)")
            ensure_column("table_orders", "hotel_id", "hotel_id INT")

            # Ensure enums match expected values
            try:
                cursor.execute(
                    "ALTER TABLE table_orders MODIFY COLUMN order_status ENUM('ACTIVE', 'PREPARING', 'COMPLETED') DEFAULT 'ACTIVE'"
                )
            except Exception as e:
                print(f"Error ensuring order_status enum: {e}")
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    @staticmethod
    def add_table(table_number, qr_code_path, hotel_id=None):
        """Add new table"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "INSERT INTO tables (table_number, qr_code_path, hotel_id) VALUES (%s, %s, %s)",
                (table_number, qr_code_path, hotel_id)
            )
            
            table_id = cursor.lastrowid
            connection.commit()
            cursor.close()
            connection.close()
            return table_id
        except Exception as e:
            print(f"Error adding table: {e}")
            return None
    
    @staticmethod
    def get_all_tables(hotel_id=None):
        """Get all tables for a specific hotel"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            if hotel_id:
                cursor.execute("SELECT * FROM tables WHERE hotel_id = %s ORDER BY table_number", (hotel_id,))
            else:
                cursor.execute("SELECT * FROM tables ORDER BY table_number")
            tables = cursor.fetchall()
            
            cursor.close()
            connection.close()
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    @staticmethod
    def get_table_by_id(table_id):
        """Get table by ID"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM tables WHERE id = %s", (table_id,))
            table = cursor.fetchone()
            
            cursor.close()
            connection.close()
            return table
        except Exception as e:
            print(f"Error getting table: {e}")
            return None
    
    @staticmethod
    def start_table_session(table_id, session_id):
        """Start a new session for table (mark as BUSY)"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE tables SET status = 'BUSY', current_session_id = %s WHERE id = %s",
                (session_id, table_id)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error starting table session: {e}")
            return False
    
    @staticmethod
    def end_table_session(table_id):
        """End table session (mark as AVAILABLE)"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cursor.execute(
                "UPDATE tables SET status = 'AVAILABLE', current_session_id = NULL WHERE id = %s",
                (table_id,)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error ending table session: {e}")
            return False
    
    @staticmethod
    def get_table_session(table_id):
        """Get current session ID for table"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT current_session_id FROM tables WHERE id = %s", (table_id,))
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            return result['current_session_id'] if result else None
        except Exception as e:
            print(f"Error getting table session: {e}")
            return None

class TableOrder:
    @staticmethod
    def add_order(table_id, session_id, items, total_amount, hotel_id=None):
        """Add new ACTIVE order and set table BUSY"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            import json
            items_json = json.dumps(items)
            
            # Add order as ACTIVE
            cursor.execute(
                "INSERT INTO table_orders (table_id, session_id, items, total_amount, order_status, hotel_id) VALUES (%s, %s, %s, %s, 'ACTIVE', %s)",
                (table_id, session_id, items_json, total_amount, hotel_id)
            )
            
            order_id = cursor.lastrowid
            
            # Set table BUSY
            cursor.execute(
                "UPDATE tables SET status = 'BUSY', current_session_id = COALESCE(current_session_id, %s) WHERE id = %s",
                (session_id, table_id)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return order_id, None
        except Exception as e:
            print(f"Error adding order: {e}")
            return None, str(e)
    
    @staticmethod
    def complete_order(order_id):
        """Complete order and set table AVAILABLE"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Get table_id for this order
            cursor.execute("SELECT table_id FROM table_orders WHERE id = %s", (order_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            table_id = result[0]
            
            # Update order to COMPLETED
            cursor.execute(
                "UPDATE table_orders SET order_status = 'COMPLETED' WHERE id = %s",
                (order_id,)
            )
            
            # Set table AVAILABLE (core logic: Order COMPLETED = Table AVAILABLE)
            cursor.execute(
                "UPDATE tables SET status = 'AVAILABLE' WHERE id = %s",
                (table_id,)
            )
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error completing order: {e}")
            return False
    
    @staticmethod
    def get_all_orders(hotel_id=None):
        """Get all orders with table info for a specific hotel"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            if hotel_id:
                # Match orders by hotel_id OR by table's hotel_id (fallback for older orders)
                cursor.execute("""
                    SELECT o.*, t.table_number, t.status as table_status
                    FROM table_orders o
                    JOIN tables t ON o.table_id = t.id
                    WHERE o.hotel_id = %s OR (o.hotel_id IS NULL AND t.hotel_id = %s)
                    ORDER BY o.created_at DESC
                """, (hotel_id, hotel_id))
            else:
                cursor.execute("""
                    SELECT o.*, t.table_number, t.status as table_status
                    FROM table_orders o
                    JOIN tables t ON o.table_id = t.id
                    ORDER BY o.created_at DESC
                """)
            
            orders = cursor.fetchall()
            
            # Parse JSON items
            import json
            for order in orders:
                if order['items']:
                    order['items'] = json.loads(order['items'])
            
            cursor.close()
            connection.close()
            return orders
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    @staticmethod
    def update_order_status(order_id, status):
        """Update order status; if completed, free the table."""
        try:
            if status == 'COMPLETED':
                return TableOrder.complete_order(order_id)

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "UPDATE table_orders SET order_status = %s WHERE id = %s",
                (status, order_id)
            )

            connection.commit()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

    @staticmethod
    def get_orders_by_session(table_id, session_id):
        """Get orders for a specific table session"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT o.*, t.table_number, t.status as table_status
                FROM table_orders o
                JOIN tables t ON o.table_id = t.id
                WHERE o.table_id = %s AND o.session_id = %s
                ORDER BY o.created_at DESC
                """,
                (table_id, session_id)
            )

            orders = cursor.fetchall()

            import json
            for order in orders:
                if order['items']:
                    order['items'] = json.loads(order['items'])

            cursor.close()
            connection.close()
            return orders
        except Exception as e:
            print(f"Error getting session orders: {e}")
            return []
    

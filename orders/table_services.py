import os
import qrcode
import uuid
from .table_models import Table, TableOrder

class TableService:
    @staticmethod
    def create_qr_code(table_id, table_number):
        """Generate QR code for table"""
        try:
            # QR code contains URL to menu with table ID
            qr_data = f"http://localhost:5000/orders/menu/{table_id}"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_dir = "static/uploads"
            os.makedirs(qr_dir, exist_ok=True)
            
            filename = f"Table_{table_number}_QR.png"
            filepath = os.path.join(qr_dir, filename)
            img.save(filepath)
            
            return filepath
        except Exception as e:
            print(f"Error creating QR code: {e}")
            return None
    
    @staticmethod
    def add_new_table(table_number, hotel_id=None):
        """Add new table with QR code"""
        try:
            # Check if table number exists for this hotel
            existing_tables = Table.get_all_tables(hotel_id)
            for table in existing_tables:
                if table['table_number'] == table_number:
                    return {"success": False, "message": "Table number already exists"}
            
            # Create table first
            table_id = Table.add_table(table_number, "", hotel_id)
            if not table_id:
                return {"success": False, "message": "Failed to create table"}
            
            # Generate QR code
            qr_path = TableService.create_qr_code(table_id, table_number)
            if not qr_path:
                return {"success": False, "message": "Failed to generate QR code"}
            
            # Update table with QR path
            from database.db import get_db_connection
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE tables SET qr_code_path = %s WHERE id = %s",
                (qr_path, table_id)
            )
            connection.commit()
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "message": "Table added successfully",
                "table_id": table_id
            }
        except Exception as e:
            print(f"Error adding table: {e}")
            return {"success": False, "message": "Server error"}
    
    @staticmethod
    def delete_table(table_number):
        """Delete specific table by table number"""
        try:
            from database.db import get_db_connection
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Get table info first
            cursor.execute("SELECT id, qr_code_path FROM tables WHERE table_number = %s", (table_number,))
            table = cursor.fetchone()
            
            if not table:
                return {"success": False, "message": "Table not found"}
            
            table_id, qr_path = table
            
            # Delete orders first (foreign key constraint)
            cursor.execute("DELETE FROM table_orders WHERE table_id = %s", (table_id,))
            
            # Delete table
            cursor.execute("DELETE FROM tables WHERE id = %s", (table_id,))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Delete QR file if exists
            if qr_path and os.path.exists(qr_path):
                os.remove(qr_path)
            
            return {"success": True, "message": f"Table {table_number} deleted successfully"}
            
        except Exception as e:
            print(f"Error deleting table: {e}")
            return {"success": False, "message": "Server error"}

class OrderService:
    @staticmethod
    def create_order(table_id, items, session_id=None):
        """Create new ACTIVE order and set table BUSY"""
        try:
            table = Table.get_table_by_id(table_id)
            if not table:
                return {"success": False, "message": "Table not found"}
            
            current_session_id = table.get('current_session_id')
            hotel_id = table.get('hotel_id')  # Get hotel_id from table

            if table['status'] == 'BUSY':
                if not session_id or session_id != current_session_id:
                    return {"success": False, "message": "Table is currently busy"}

            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Calculate total
            total_amount = sum(item['price'] * item['quantity'] for item in items)
            
            # Add ACTIVE order (automatically sets table BUSY) - include hotel_id
            order_id, error_message = TableOrder.add_order(table_id, session_id, items, total_amount, hotel_id)
            if not order_id:
                if error_message:
                    return {"success": False, "message": f"Failed to create order: {error_message}"}
                return {"success": False, "message": "Failed to create order"}
            
            return {
                "success": True,
                "message": "Order created successfully",
                "order_id": order_id,
                "session_id": session_id
            }
        except Exception as e:
            print(f"Error creating order: {e}")
            return {"success": False, "message": "Server error"}
    
    @staticmethod
    def complete_order(order_id):
        """Complete order and set table AVAILABLE immediately"""
        try:
            if TableOrder.complete_order(order_id):
                return {"success": True, "message": "Order completed. Table is now available."}
            else:
                return {"success": False, "message": "Failed to complete order"}
        except Exception as e:
            print(f"Error completing order: {e}")
            return {"success": False, "message": "Server error"}

    @staticmethod
    def get_session_orders(table_id, session_id):
        """Get orders for current session"""
        try:
            orders = TableOrder.get_orders_by_session(table_id, session_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            print(f"Error getting session orders: {e}")
            return {"success": False, "message": "Server error"}

    @staticmethod
    def complete_payment(table_id, session_id):
        """Complete payment and end table session"""
        try:
            table = Table.get_table_by_id(table_id)
            if not table:
                return {"success": False, "message": "Table not found"}

            current_session_id = table.get('current_session_id')
            if not current_session_id or current_session_id != session_id:
                return {"success": False, "message": "Invalid session"}

            from database.db import get_db_connection
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                "UPDATE table_orders SET order_status = 'COMPLETED' WHERE table_id = %s AND session_id = %s",
                (table_id, session_id)
            )

            cursor.execute(
                "UPDATE tables SET status = 'AVAILABLE', current_session_id = NULL WHERE id = %s",
                (table_id,)
            )

            connection.commit()
            cursor.close()
            connection.close()

            return {"success": True, "message": "Payment completed. Table is now available."}
        except Exception as e:
            print(f"Error completing payment: {e}")
            return {"success": False, "message": "Server error"}

    @staticmethod
    def update_order_status(order_id, status):
        """Update order status (ACTIVE/PREPARING/COMPLETED)."""
        try:
            if status not in {"ACTIVE", "PREPARING", "COMPLETED"}:
                return {"success": False, "message": "Invalid status"}

            if TableOrder.update_order_status(order_id, status):
                return {"success": True, "message": "Order status updated"}

            return {"success": False, "message": "Failed to update order status"}
        except Exception as e:
            print(f"Error updating order status: {e}")
            return {"success": False, "message": "Server error"}
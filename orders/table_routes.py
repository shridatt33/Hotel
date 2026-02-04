import os
from flask import request, jsonify, render_template, send_file, session
from . import orders_bp
from .table_services import TableService, OrderService
from .table_models import Table, TableOrder

# Initialize tables
Table.create_tables()

def check_food_module():
    """Check if food module is enabled for this manager's hotel"""
    if not session.get('manager_id'):
        return False
    return session.get('food_enabled', False)

@orders_bp.route('/api/tables', methods=['GET'])
def get_tables():
    """Get all tables for current hotel"""
    try:
        hotel_id = session.get('hotel_id')
        tables = Table.get_all_tables(hotel_id)
        return jsonify({"success": True, "tables": tables})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/tables', methods=['POST'])
def add_table():
    """Add new table"""
    if not check_food_module():
        return jsonify({"success": False, "message": "Food ordering module not enabled for this hotel"}), 403
    try:
        data = request.get_json()
        table_number = data.get('table_number', '').strip()
        hotel_id = session.get('hotel_id')
        
        if not table_number:
            return jsonify({"success": False, "message": "Table number is required"})
        
        result = TableService.add_new_table(table_number, hotel_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/download-qr/<int:table_id>')
def download_qr(table_id):
    """Download QR code"""
    try:
        table = Table.get_table_by_id(table_id)
        if not table or not table['qr_code_path']:
            return jsonify({"success": False, "message": "QR code not found"})
        
        qr_path = table['qr_code_path']
        if os.path.exists(qr_path):
            return send_file(qr_path, as_attachment=True, 
                           download_name=f"Table_{table['table_number']}_QR.png")
        else:
            return jsonify({"success": False, "message": "QR file not found"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/menu/<int:table_id>')
def table_menu(table_id):
    """Show menu for table (QR destination)"""
    table = Table.get_table_by_id(table_id)
    if not table:
        return "Table not found", 404
    
    # Show menu; ordering rules are enforced server-side via session checks
    table_busy = table['status'] == 'BUSY'

    return render_template('table_menu.html', table=table, table_busy=table_busy)

@orders_bp.route('/api/create-order', methods=['POST'])
def create_order():
    """Create new ACTIVE order"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        items = data.get('items', [])
        session_id = data.get('session_id')
        
        if not table_id or not items:
            return jsonify({"success": False, "message": "Table ID and items required"})
        
        result = OrderService.create_order(table_id, items, session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders for current hotel"""
    try:
        hotel_id = session.get('hotel_id')
        orders = TableOrder.get_all_orders(hotel_id)
        return jsonify({"success": True, "orders": orders})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/session-orders/<int:table_id>/<session_id>', methods=['GET'])
def get_session_orders(table_id, session_id):
    """Get orders for current session"""
    try:
        result = OrderService.get_session_orders(table_id, session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/complete-payment', methods=['POST'])
def complete_payment():
    """Complete payment and free QR for next customer"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        session_id = data.get('session_id')
        
        if not table_id or not session_id:
            return jsonify({"success": False, "message": "Table ID and session ID required"})
        
        result = OrderService.complete_payment(table_id, session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/complete-order', methods=['POST'])
def complete_order():
    """Complete order and set table AVAILABLE"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({"success": False, "message": "Order ID required"})
        
        result = OrderService.complete_order(order_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/update-order-status', methods=['POST'])
def update_order_status():
    """Update order status (ACTIVE/PREPARING/COMPLETED)"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        status = data.get('status')

        if not order_id or not status:
            return jsonify({"success": False, "message": "Order ID and status required"})

        result = OrderService.update_order_status(order_id, status)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/tables/<table_number>', methods=['DELETE'])
def delete_table(table_number):
    """Delete table by table number"""
    try:
        result = TableService.delete_table(table_number)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})
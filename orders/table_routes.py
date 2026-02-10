import os
from flask import request, jsonify, render_template, send_file, session
from . import orders_bp
from .table_services import TableService, OrderService
from .table_models import Table, TableOrder, Bill, ActiveTable

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
    
    # Check for any open bill with a guest_name to determine initial busy state
    # Bills with NULL/empty guest_name are treated as available (orphaned bills)
    # Note: The actual access logic is handled by check-guest-access API after guest enters name
    open_bill = Bill.get_any_open_bill_for_table(table_id)
    
    # Only show busy if there's an open bill WITH a guest name assigned
    table_busy = False
    if open_bill and open_bill.get('guest_name') and open_bill.get('guest_name').strip():
        table_busy = True

    return render_template('table_menu.html', table=table, table_busy=table_busy)

@orders_bp.route('/api/check-guest-access', methods=['POST'])
def check_guest_access():
    """Check if a guest can access a table based on existing OPEN bills"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        guest_name = data.get('guest_name')
        
        if not table_id:
            return jsonify({"success": False, "message": "Table ID required", "can_order": False})
        
        if not guest_name or not guest_name.strip():
            return jsonify({"success": False, "message": "Guest name is required", "can_order": False})
        
        result = OrderService.check_guest_access(table_id, guest_name)
        return jsonify(result)
    except Exception as e:
        print(f"Error in check_guest_access: {e}")
        return jsonify({"success": False, "message": "Server error", "can_order": False})

@orders_bp.route('/api/create-order', methods=['POST'])
def create_order():
    """Create new ACTIVE order with guest name"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        items = data.get('items', [])
        session_id = data.get('session_id')
        guest_name = data.get('guest_name')
        
        if not table_id or not items:
            return jsonify({"success": False, "message": "Table ID and items required"})
        
        if not guest_name or not guest_name.strip():
            return jsonify({"success": False, "message": "Guest name is required"})
        
        result = OrderService.create_order(table_id, items, session_id, guest_name)
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

# ============== Bill & Payment Routes ==============

@orders_bp.route('/api/bill/<int:order_id>', methods=['GET'])
def get_bill_by_order(order_id):
    """Get bill for a specific order"""
    try:
        bill = Bill.get_bill_by_order(order_id)
        if bill:
            return jsonify({"success": True, "bill": bill})
        return jsonify({"success": False, "message": "Bill not found"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/session-bill/<int:table_id>/<session_id>', methods=['GET'])
def get_session_bill(table_id, session_id):
    """Get combined bill for entire session"""
    try:
        bill = Bill.get_session_total(table_id, session_id)
        if bill:
            return jsonify({"success": True, "bill": bill})
        return jsonify({"success": False, "message": "No orders found for this session"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/guest-bill/<int:table_id>/<guest_name>', methods=['GET'])
def get_guest_bill(table_id, guest_name):
    """Get open bill for a specific guest at a table"""
    try:
        bill = Bill.get_open_bill_by_table_and_guest(table_id, guest_name)
        if bill:
            return jsonify({"success": True, "bill": bill})
        return jsonify({"success": False, "message": "No open bill found for this guest"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/complete-bill', methods=['POST'])
def complete_bill():
    """Complete a bill - lock it and free table"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        
        if not bill_id:
            return jsonify({"success": False, "message": "Bill ID required"})
        
        result = OrderService.complete_bill(bill_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/process-payment', methods=['POST'])
def process_payment():
    """Process payment - ALWAYS succeeds if OPEN bill exists"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        guest_name = data.get('guest_name')
        payment_method = data.get('payment_method', 'CASH')
        
        if not table_id:
            return jsonify({"success": False, "message": "Table ID is required"})
        
        # Find OPEN bill for this table
        open_bill = Bill.get_any_open_bill_for_table(table_id)
        
        if not open_bill:
            return jsonify({"success": False, "message": "No open bill found. Please place an order first."})
        
        # Process payment in atomic transaction
        payment_success = Bill.process_payment_atomic(table_id, open_bill['id'], payment_method)
        
        if payment_success:
            return jsonify({
                "success": True, 
                "message": "Payment successful! Thank you for dining with us."
            })
        return jsonify({"success": False, "message": "Failed to process payment"})
    except Exception as e:
        print(f"Error processing payment: {e}")
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/orders-with-bills', methods=['GET'])
def get_orders_with_bills():
    """Get all orders with their bill information for the current hotel"""
    try:
        hotel_id = session.get('hotel_id')
        orders = TableOrder.get_all_orders(hotel_id)
        
        # Add bill info to each order
        for order in orders:
            bill = Bill.get_bill_by_order(order['id'])
            order['bill'] = bill
        
        return jsonify({"success": True, "orders": orders})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/active-bills', methods=['GET'])
def get_active_bills():
    """Get all OPEN bills for the current hotel - one per table"""
    try:
        hotel_id = session.get('hotel_id')
        bills = Bill.get_all_active_bills(hotel_id)
        return jsonify({"success": True, "bills": bills})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/all-bills', methods=['GET'])
def get_all_bills():
    """Get all bills for the current hotel with optional status filter"""
    try:
        hotel_id = session.get('hotel_id')
        status = request.args.get('status')  # Optional: 'OPEN' or 'COMPLETED'
        bills = Bill.get_all_bills(hotel_id, status)
        return jsonify({"success": True, "bills": bills})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/table-bill/<int:table_id>', methods=['GET'])
def get_table_bill(table_id):
    """Get the current OPEN bill for a specific table"""
    try:
        bill = Bill.get_any_open_bill_for_table(table_id)
        if bill:
            return jsonify({"success": True, "bill": bill, "has_open_bill": True})
        return jsonify({"success": True, "bill": None, "has_open_bill": False, "message": "No open bill for this table"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/mark-bill-paid', methods=['POST'])
def mark_bill_paid():
    """Mark a bill as PAID and complete it, releasing the table"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        table_id = data.get('table_id')
        
        if not bill_id:
            return jsonify({"success": False, "message": "Bill ID required"})
        
        # Complete the bill (mark as PAID and COMPLETED)
        result = Bill.complete_bill(bill_id)
        if not result:
            return jsonify({"success": False, "message": "Failed to complete bill"})
        
        # Release the table (set to AVAILABLE)
        if table_id:
            Table.update_status(table_id, 'AVAILABLE')
        
        return jsonify({"success": True, "message": "Bill marked as paid and table released"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/bill-details/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    """Get detailed bill information including items"""
    try:
        bill = Bill.get_bill_by_id(bill_id)
        if bill:
            return jsonify({"success": True, "bill": bill})
        return jsonify({"success": False, "message": "Bill not found"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

# ============== Active Tables Routes ==============

@orders_bp.route('/api/active-tables', methods=['GET'])
def get_active_tables():
    """Get all active tables (linked to open bills) for the hotel"""
    try:
        hotel_id = session.get('hotel_id')
        active_tables = ActiveTable.get_all_active_tables(hotel_id)
        return jsonify({"success": True, "active_tables": active_tables})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/active-tables/<int:table_id>', methods=['GET'])
def get_active_table(table_id):
    """Get active entry for a specific table"""
    try:
        entry = ActiveTable.get_active_entry(table_id)
        if entry:
            return jsonify({"success": True, "active_table": entry, "is_active": True})
        return jsonify({"success": True, "active_table": None, "is_active": False})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})

@orders_bp.route('/api/active-tables/sync', methods=['POST'])
def sync_active_tables():
    """Sync active tables with bill status - cleanup stale entries"""
    try:
        ActiveTable.sync_with_bills()
        return jsonify({"success": True, "message": "Active tables synced with bills"})
    except Exception as e:
        return jsonify({"success": False, "message": "Server error"})
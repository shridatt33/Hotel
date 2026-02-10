from flask import request, jsonify, session
from . import wallet_bp
from .models import HotelWallet

# Initialize tables on import
HotelWallet.create_tables()


@wallet_bp.route('/api/balance/<int:hotel_id>', methods=['GET'])
def get_balance(hotel_id):
    """Get wallet balance and details for a hotel"""
    # Check if admin or manager of this hotel
    admin_id = session.get('admin_id')
    manager_hotel_id = session.get('hotel_id')
    
    if not admin_id and int(manager_hotel_id or 0) != hotel_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Use get_or_create_wallet to auto-create if not exists
    wallet = HotelWallet.get_or_create_wallet(hotel_id)
    if wallet:
        return jsonify({'success': True, 'wallet': wallet})
    return jsonify({'success': False, 'message': 'Could not retrieve or create wallet'})


@wallet_bp.route('/api/add-balance', methods=['POST'])
def add_balance():
    """Add balance to hotel wallet (Admin or Manager)"""
    try:
        data = request.json
        hotel_id = int(data.get('hotel_id', 0))
        amount = float(data.get('amount', 0))
        description = data.get('description', 'Balance added')
        
        if not hotel_id:
            return jsonify({'success': False, 'message': 'Hotel ID is required'})
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than 0'})
        
        # Determine who is adding balance
        admin_id = session.get('admin_id')
        manager_id = session.get('manager_id')
        manager_hotel_id = session.get('hotel_id')
        
        if admin_id:
            created_by_type = 'ADMIN'
            created_by_id = admin_id
        elif manager_id and int(manager_hotel_id or 0) == hotel_id:
            created_by_type = 'MANAGER'
            created_by_id = manager_id
        else:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        result = HotelWallet.add_balance(hotel_id, amount, description, created_by_type, created_by_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error in add_balance route: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})


@wallet_bp.route('/api/all-wallets', methods=['GET'])
def get_all_wallets():
    """Get all hotel wallets (Admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    wallets = HotelWallet.get_all_wallets()
    return jsonify({'success': True, 'wallets': wallets})


@wallet_bp.route('/api/transactions/<int:hotel_id>', methods=['GET'])
def get_transactions(hotel_id):
    """Get transaction history for a hotel"""
    # Check authorization
    admin_id = session.get('admin_id')
    manager_hotel_id = session.get('hotel_id')
    
    if not admin_id and int(manager_hotel_id or 0) != hotel_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    transactions = HotelWallet.get_transactions(hotel_id, limit)
    return jsonify({'success': True, 'transactions': transactions})


@wallet_bp.route('/api/update-charges', methods=['POST'])
def update_charges():
    """Update hotel charges (Admin only)"""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        data = request.json
        hotel_id = int(data.get('hotel_id', 0))
        per_verification_charge = float(data.get('per_verification_charge', 0))
        per_order_charge = float(data.get('per_order_charge', 0))
        
        if not hotel_id:
            return jsonify({'success': False, 'message': 'Hotel ID is required'})
        
        result = HotelWallet.update_charges(hotel_id, per_verification_charge, per_order_charge)
        return jsonify(result)
    except Exception as e:
        print(f"Error in update_charges route: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})


@wallet_bp.route('/api/check-verification-balance/<int:hotel_id>', methods=['GET'])
def check_verification_balance(hotel_id):
    """Check if hotel has sufficient balance for verification"""
    result = HotelWallet.check_balance_for_verification(hotel_id)
    return jsonify(result)


@wallet_bp.route('/api/check-order-balance/<int:hotel_id>', methods=['GET'])
def check_order_balance(hotel_id):
    """Check if hotel has sufficient balance for order"""
    result = HotelWallet.check_balance_for_order(hotel_id)
    return jsonify(result)

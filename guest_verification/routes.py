from flask import request, jsonify, render_template, redirect, url_for, send_file, session
from . import guest_verification_bp
from .models import GuestVerification
import qrcode
import io
import base64
from urllib.parse import urljoin
from database.db import get_db_connection

def check_kyc_module():
    """Check if KYC module is enabled for this manager's hotel"""
    if not session.get('manager_id'):
        return False
    return session.get('kyc_enabled', False)

@guest_verification_bp.route('/dashboard/<int:manager_id>')
def verification_dashboard(manager_id):
    """Verification dashboard for managers"""
    if not check_kyc_module():
        return jsonify({"success": False, "message": "Customer verification module not enabled for this hotel"}), 403
    
    hotel_id = session.get('hotel_id')
    
    # Get all verifications for this hotel
    verifications = GuestVerification.get_verifications_by_hotel(hotel_id)
    
    # Generate QR code for public form (using hotel_id for hotel-specific form)
    public_url = f"{request.url_root}guest-verification/form/{manager_id}?hotel_id={hotel_id}"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(public_url)
    qr.make(fit=True)
    
    # Convert QR to base64 image
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('verification_dashboard.html', 
                         manager_id=manager_id,
                         hotel_id=hotel_id,
                         verifications=verifications,
                         public_url=public_url,
                         qr_code=qr_code_base64)

@guest_verification_bp.route('/form/<int:manager_id>')
def public_form(manager_id):
    """Public guest verification form"""
    hotel_id = request.args.get('hotel_id')
    return render_template('guest_verification_form.html', manager_id=manager_id, hotel_id=hotel_id)

@guest_verification_bp.route('/submit/<int:manager_id>', methods=['POST'])
def submit_verification(manager_id):
    """Handle verification form submission"""
    try:
        # Get form data
        guest_name = request.form.get('guest_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        kyc_number = request.form.get('kyc_number')
        hotel_id = request.form.get('hotel_id') or request.args.get('hotel_id')
        
        # Handle file upload
        identity_file = request.files.get('identity_file')
        file_path = None
        
        if identity_file:
            file_path = GuestVerification.save_uploaded_file(identity_file, manager_id)
        
        # Submit verification with hotel_id
        result = GuestVerification.submit_verification(
            manager_id, guest_name, phone, address, kyc_number, file_path, hotel_id
        )
        
        if result['success']:
            # Log activity
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO recent_activities (activity_type, message) VALUES (%s, %s)",
                    ('verification', f"Verification completed for '{guest_name}'")
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception:
                pass
            
            return render_template('verification_success.html')
        else:
            return render_template('guest_verification_form.html', 
                                 manager_id=manager_id, 
                                 error=result['message'])
    
    except Exception as e:
        return render_template('guest_verification_form.html', 
                             manager_id=manager_id, 
                             error=f"Error: {str(e)}")

@guest_verification_bp.route('/update-status', methods=['POST'])
def update_status():
    """Update verification status (AJAX)"""
    data = request.json
    result = GuestVerification.update_status(
        data.get('verification_id'), 
        data.get('status')
    )
    return jsonify(result)

@guest_verification_bp.route('/download-qr/<int:manager_id>')
def download_qr(manager_id):
    """Download QR code as PNG file"""
    public_url = f"{request.url_root}guest-verification/form/{manager_id}"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(public_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return send_file(img_buffer, 
                     mimetype='image/png',
                     as_attachment=True,
                     download_name=f'verification_qr_manager_{manager_id}.png')

@guest_verification_bp.route('/api/verifications/<int:manager_id>')
def api_get_verifications(manager_id):
    """API endpoint to get verifications for AJAX calls"""
    verifications = GuestVerification.get_verifications_by_manager(manager_id)
    
    # Convert to JSON-serializable format
    verification_list = []
    for v in verifications:
        verification_list.append({
            'id': v[0],
            'guest_name': v[1],
            'phone': v[2],
            'address': v[3],
            'kyc_number': v[4],
            'identity_file': v[5],
            'submitted_at': v[6].isoformat() if v[6] else None,
            'status': v[7]
        })
    
    return jsonify({'verifications': verification_list})

@guest_verification_bp.route('/api/qr-code/<int:manager_id>')
def api_get_qr_code(manager_id):
    """API endpoint to get QR code data for AJAX calls"""
    public_url = f"{request.url_root}guest-verification/form/{manager_id}"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(public_url)
    qr.make(fit=True)
    
    # Convert QR to base64 image
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return jsonify({
        'qr_code': qr_code_base64,
        'public_url': public_url
    })
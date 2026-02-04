from flask import request, jsonify, session, render_template
from . import hotel_manager_bp
from .models import HotelManager, Waiter

@hotel_manager_bp.route('/login-page')
def login_page():
    return render_template('manager_login.html')

@hotel_manager_bp.route('/signup-page')
def signup_page():
    return render_template('manager_signup.html')

@hotel_manager_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    print(f"Signup attempt - Username: {data.get('username')}, Email: {data.get('email')}")
    result = HotelManager.create_account(
        data.get('name'),
        data.get('email'),
        data.get('username'),
        data.get('password')
    )
    print(f"Signup result: {result}")
    return jsonify(result)

@hotel_manager_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    print(f"Login attempt - Username: {data.get('username')}")
    result = HotelManager.login(
        data.get('username'),
        data.get('password')
    )
    print(f"Login result: {result}")
    
    # Store session data if login successful
    if result.get('success'):
        session['manager_id'] = result.get('id')
        session['manager_name'] = result.get('name')
        session['hotel_id'] = result.get('hotel_id')
        session['hotel_name'] = result.get('hotel_name')
        session['kyc_enabled'] = result.get('kyc_enabled', False)
        session['food_enabled'] = result.get('food_enabled', False)
    
    return jsonify(result)

@hotel_manager_bp.route('/dashboard')
def dashboard():
    # Check session-based auth first
    manager_id = session.get('manager_id') or request.args.get('id')
    manager_name = session.get('manager_name') or request.args.get('name')
    hotel_id = session.get('hotel_id')
    
    if not manager_id or not manager_name:
        return "Invalid access. Please login first.", 403
    
    # Get module flags from session (default to False if not set)
    kyc_enabled = session.get('kyc_enabled', False)
    food_enabled = session.get('food_enabled', False)
    hotel_name = session.get('hotel_name', '')
    
    # Get waiters for this hotel
    waiters = Waiter.get_waiters_by_hotel(hotel_id)
    waiters_count = len(waiters) if waiters else 0
    
    # Create waiters HTML table
    waiters_html = ""
    if waiters:
        waiters_html = "<table class='waiters-table'>"
        waiters_html += "<thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Created At</th><th>Action</th></tr></thead>"
        waiters_html += "<tbody>"
        for waiter in waiters:
            waiters_html += f"<tr><td>{waiter[0]}</td><td>{waiter[1]}</td><td>{waiter[2]}</td><td>{waiter[3]}</td><td>{waiter[4]}</td><td><button class='delete-btn' onclick='deleteWaiter({waiter[0]})'>Delete</button></td></tr>"
        waiters_html += "</tbody></table>"
    else:
        waiters_html = "<p style='color: #718096; text-align: center; padding: 2rem;'>No waiters added yet</p>"
    
    return render_template('manager_dashboard.html', 
                         manager_id=manager_id, 
                         manager_name=manager_name,
                         hotel_id=hotel_id,
                         hotel_name=hotel_name,
                         kyc_enabled=kyc_enabled,
                         food_enabled=food_enabled,
                         waiters_html=waiters_html,
                         waiters_count=waiters_count)

@hotel_manager_bp.route('/add-waiter', methods=['POST'])
def add_waiter():
    data = request.json
    hotel_id = session.get('hotel_id')
    result = Waiter.create_waiter(
        data.get('manager_id'),
        data.get('name'),
        data.get('email'),
        data.get('phone'),
        hotel_id
    )
    return jsonify(result)

@hotel_manager_bp.route('/delete-waiter', methods=['POST'])
def delete_waiter():
    data = request.json
    hotel_id = session.get('hotel_id')
    result = Waiter.delete_waiter(
        data.get('waiter_id'),
        hotel_id
    )
    return jsonify(result)

@hotel_manager_bp.route('/all-managers')
def all_managers():
    managers = HotelManager.get_all_managers()
    
    managers_html = ""
    if managers:
        managers_html = "<table class='managers-table'>"
        managers_html += "<thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Username</th><th>Created At</th></tr></thead>"
        managers_html += "<tbody>"
        for manager in managers:
            managers_html += f"<tr><td>{manager[0]}</td><td>{manager[1]}</td><td>{manager[2]}</td><td>{manager[3]}</td><td>{manager[4]}</td></tr>"
        managers_html += "</tbody></table>"
    else:
        managers_html = "<p class='no-data'>No managers found</p>"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Managers - HotelEase</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; }}
            
            .navbar {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .navbar h1 {{ font-size: 1.8rem; }}
            
            .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 2rem; width: 100%; flex: 1; }}
            
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }}
            .header h2 {{ color: #2d3748; font-size: 1.8rem; }}
            .back-btn {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 0.7rem 1.5rem; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.3s ease; text-decoration: none; display: inline-block; }}
            .back-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3); }}
            
            .card {{ background: white; border-radius: 12px; padding: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            
            .managers-table {{ width: 100%; border-collapse: collapse; }}
            .managers-table thead {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
            .managers-table th {{ color: white; padding: 1.2rem; text-align: left; font-weight: 600; }}
            .managers-table td {{ padding: 1rem 1.2rem; border-bottom: 1px solid #e2e8f0; }}
            .managers-table tbody tr:hover {{ background: #f7fafc; }}
            .managers-table tbody tr:last-child td {{ border-bottom: none; }}
            
            .no-data {{ text-align: center; color: #718096; font-size: 1.1rem; padding: 2rem; }}
            
            .footer {{ background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); color: white; text-align: center; padding: 1.5rem; margin-top: auto; }}
            
            @media (max-width: 768px) {{
                .container {{ padding: 0 1rem; }}
                .header {{ flex-direction: column; gap: 1rem; }}
                .managers-table {{ font-size: 0.9rem; }}
                .managers-table th, .managers-table td {{ padding: 0.8rem 0.5rem; }}
            }}
        </style>
    </head>
    <body>
        <nav class="navbar">
            <h1>🏨 HotelEase - Manager Credentials</h1>
        </nav>
        
        <div class="container">
            <div class="header">
                <h2>All Registered Managers</h2>
                <a href="/" class="back-btn">← Back to Home</a>
            </div>
            
            <div class="card">
                {managers_html}
            </div>
        </div>
        
        <footer class="footer">
            <p>&copy; 2026 HotelEase - All Rights Reserved</p>
        </footer>
    </body>
    </html>
    """

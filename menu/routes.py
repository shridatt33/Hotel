import os
from flask import jsonify, request, render_template, url_for, session
from werkzeug.utils import secure_filename
from . import menu_bp
from .models import MenuCategory, MenuDish

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def check_food_module():
    """Check if food module is enabled for this manager's hotel"""
    if not session.get('manager_id'):
        return False
    return session.get('food_enabled', False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, dish_id):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(f"dish_{dish_id}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        try:
            file.save(filepath)
            return filename
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    return None

def build_image_urls(images):
    """Return only image URLs that actually exist on disk."""
    if not images:
        return []

    urls = []
    # Handle both comma-separated string and list
    if isinstance(images, str):
        images = [img.strip() for img in images.split(',') if img.strip()]
    
    for img in images:
        upload_path = os.path.join(UPLOAD_FOLDER, img)
        if os.path.exists(upload_path):
            urls.append(url_for('static', filename=f'uploads/{img}'))
    return urls

def format_dish(dish_row):
    """Format a dish database row into the expected dictionary format"""
    images = dish_row.get('images', '') or ''
    if isinstance(images, str):
        images_list = [img.strip() for img in images.split(',') if img.strip()]
    else:
        images_list = images if images else []
    
    return {
        "id": dish_row['id'],
        "name": dish_row['name'],
        "price": float(dish_row['price']),
        "quantity": dish_row['quantity'],
        "description": dish_row.get('description', ''),
        "images": images_list,
        "image_urls": build_image_urls(images_list),
        "category_id": dish_row.get('category_id')
    }

@menu_bp.route("/menu")
def menu_page():
    return render_template('menu/menu_page.html')

@menu_bp.route("/menu-dashboard")
def menu_dashboard():
    if not check_food_module():
        return jsonify({"success": False, "message": "Food ordering module not enabled for this hotel"}), 403
    return render_template('menu/menu_dashboard.html')

@menu_bp.route("/api/categories")
def get_categories():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    categories_list = MenuCategory.get_categories_by_hotel(hotel_id)
    # Convert to dict format {id: name} for frontend compatibility
    categories = {cat['id']: cat['name'] for cat in categories_list}
    return jsonify({"success": True, "categories": categories})

@menu_bp.route("/api/dishes/<int:category_id>")
def get_dishes(category_id):
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    dishes_list = MenuDish.get_dishes_by_category(category_id, hotel_id)
    dishes = [format_dish(dish) for dish in dishes_list]
    return jsonify({"success": True, "dishes": dishes})

@menu_bp.route("/api/add-dish", methods=["POST"])
def add_dish():
    if not check_food_module():
        return jsonify({"success": False, "message": "Food ordering module not enabled for this hotel"}), 403
    
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        category_id = int(request.form.get("category_id", 0))
        name = request.form.get("name", "").strip()
        price_str = request.form.get("price", "0").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        description = request.form.get("description", "").strip()
        
        # Validation
        if not name:
            return jsonify({"success": False, "message": "Dish name is required"})
        
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            return jsonify({"success": False, "message": "Invalid price format"})
            
        quantity = quantity_str.strip() if quantity_str else "0"
        
        if price <= 0:
            return jsonify({"success": False, "message": "Price must be greater than 0"})
        if not quantity:
            return jsonify({"success": False, "message": "Quantity is required"})
        
        # Verify category exists for this hotel
        categories = MenuCategory.get_categories_by_hotel(hotel_id)
        category_ids = [cat['id'] for cat in categories]
        if category_id not in category_ids:
            return jsonify({"success": False, "message": "Category not found"})
        
        # Handle image uploads first to get filenames
        images = []
        uploaded_files = request.files.getlist('images')
        valid_files = [f for f in uploaded_files if f and f.filename and f.filename.strip()]
        
        if len(valid_files) > 3:
            return jsonify({"success": False, "message": "Maximum 3 images allowed"})
        
        # We need a temporary ID for saving files, so add dish first with empty images
        result = MenuDish.add_dish(
            hotel_id=hotel_id,
            category_id=category_id,
            name=name,
            price=price,
            quantity=quantity,
            description=description,
            images=[]  # Empty list initially
        )
        
        if not result.get("success"):
            return jsonify({"success": False, "message": "Failed to add dish"})
        
        new_id = result.get("dish_id")
        
        # Now save files with the dish ID
        for file in valid_files:
            saved_filename = save_uploaded_file(file, new_id)
            if saved_filename:
                images.append(saved_filename)
        
        # Update dish with images if any were uploaded
        if images:
            MenuDish.update_dish(
                dish_id=new_id,
                name=name,
                price=price,
                quantity=quantity,
                description=description,
                images=images,  # Pass as list
                hotel_id=hotel_id
            )
        
        # Create response dish
        new_dish = {
            "id": new_id,
            "name": name,
            "price": price,
            "quantity": quantity,
            "description": description,
            "images": images,
            "image_urls": build_image_urls(images)
        }
        
        return jsonify({"success": True, "message": "Dish added successfully", "dish": new_dish})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/edit-dish", methods=["POST"])
def edit_dish():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        dish_id = int(request.form.get("dish_id", 0))
        name = request.form.get("name", "").strip()
        price_str = request.form.get("price", "0").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        description = request.form.get("description", "").strip()
        
        # Validation
        if not name:
            return jsonify({"success": False, "message": "Dish name is required"})
            
        try:
            price = float(price_str) if price_str else 0
        except ValueError:
            return jsonify({"success": False, "message": "Invalid price format"})
            
        quantity = quantity_str.strip() if quantity_str else "0"
        
        if price <= 0:
            return jsonify({"success": False, "message": "Price must be greater than 0"})
        if not quantity:
            return jsonify({"success": False, "message": "Quantity is required"})
        
        # Get existing dish
        existing_dish = MenuDish.get_dish_by_id(dish_id, hotel_id)
        if not existing_dish:
            return jsonify({"success": False, "message": "Dish not found"})
        
        # Handle new image uploads
        uploaded_files = request.files.getlist('images')
        valid_files = [f for f in uploaded_files if f and f.filename and f.filename.strip()]
        
        if valid_files:
            if len(valid_files) > 3:
                return jsonify({"success": False, "message": "Maximum 3 images allowed"})
            
            new_images = []
            for file in valid_files:
                saved_filename = save_uploaded_file(file, dish_id)
                if saved_filename:
                    new_images.append(saved_filename)
            images_list = new_images
        else:
            # Keep existing images (already a list from the model)
            images_list = existing_dish.get('images', [])
        
        # Update dish
        success = MenuDish.update_dish(
            dish_id=dish_id,
            name=name,
            price=price,
            quantity=quantity,
            description=description,
            images=images_list,  # Pass as list
            hotel_id=hotel_id
        )
        
        if success:
            # Get updated dish for response
            updated_dish = MenuDish.get_dish_by_id(dish_id, hotel_id)
            return jsonify({"success": True, "message": "Dish updated successfully", "dish": format_dish(updated_dish)})
        else:
            return jsonify({"success": False, "message": "Failed to update dish"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/delete-dish", methods=["POST"])
def delete_dish():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})
        
        dish_id = int(data.get("dish_id", 0))
        
        result = MenuDish.delete_dish(dish_id, hotel_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/add-category", methods=["POST"])
def add_category():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})
        
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"success": False, "message": "Category name is required"})
        
        # Check if category already exists for this hotel
        existing_categories = MenuCategory.get_categories_by_hotel(hotel_id)
        for cat in existing_categories:
            if cat['name'].lower() == name.lower():
                return jsonify({"success": False, "message": "Category already exists"})
        
        result = MenuCategory.add_category(hotel_id, name)  # hotel_id first
        
        if result.get("success"):
            return jsonify({
                "success": True, 
                "message": f"Category '{name}' added successfully", 
                "category": {"id": result.get("category_id"), "name": name}
            })
        else:
            return jsonify({"success": False, "message": result.get("message", "Failed to add category")})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/edit-category", methods=["POST"])
def edit_category():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})
        
        category_id = int(data.get("category_id", 0))
        name = data.get("name", "").strip()
        
        if not name:
            return jsonify({"success": False, "message": "Category name is required"})
        
        # Check if category exists for this hotel
        existing_categories = MenuCategory.get_categories_by_hotel(hotel_id)
        category_ids = [cat['id'] for cat in existing_categories]
        if category_id not in category_ids:
            return jsonify({"success": False, "message": "Category not found"})
        
        # Check if name already exists (excluding current category)
        for cat in existing_categories:
            if cat['id'] != category_id and cat['name'].lower() == name.lower():
                return jsonify({"success": False, "message": "Category name already exists"})
        
        result = MenuCategory.update_category(category_id, name, hotel_id)
        
        if result.get("success"):
            return jsonify({
                "success": True, 
                "message": f"Category updated to '{name}' successfully", 
                "category": {"id": category_id, "name": name}
            })
        else:
            return jsonify({"success": False, "message": result.get("message", "Failed to update category")})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/delete-category", methods=["POST"])
def delete_category():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"})
        
        category_id = int(data.get("category_id", 0))
        
        # Check if category exists for this hotel
        existing_categories = MenuCategory.get_categories_by_hotel(hotel_id)
        category = None
        for cat in existing_categories:
            if cat['id'] == category_id:
                category = cat
                break
        
        if not category:
            return jsonify({"success": False, "message": "Category not found"})
        
        category_name = category['name']
        
        # Get dishes count before deletion
        dishes = MenuDish.get_dishes_by_category(category_id, hotel_id)
        dishes_count = len(dishes)
        
        # Delete category (dishes will be deleted via CASCADE or manually)
        result = MenuCategory.delete_category(category_id, hotel_id)
        
        if result.get("success"):
            return jsonify({
                "success": True, 
                "message": f"Category '{category_name}' and {dishes_count} dish(es) deleted successfully"
            })
        else:
            return jsonify({"success": False, "message": result.get("message", "Failed to delete category")})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

@menu_bp.route("/api/full-menu")
def get_full_menu():
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    full_menu = []
    categories = MenuCategory.get_categories_by_hotel(hotel_id)
    
    for category in categories:
        dishes_list = MenuDish.get_dishes_by_category(category['id'], hotel_id)
        dishes = [format_dish(dish) for dish in dishes_list]
        full_menu.append({
            "category_id": category['id'],
            "category_name": category['name'],
            "dishes": dishes
        })
    return jsonify({"success": True, "menu": full_menu})


@menu_bp.route("/api/public-menu/<int:table_id>")
def get_public_menu(table_id):
    """Public API to get menu for a table - no login required"""
    try:
        from orders.table_models import Table
        
        # Get the table to find its hotel_id
        table = Table.get_table_by_id(table_id)
        if not table:
            return jsonify({"success": False, "message": "Table not found"}), 404
        
        hotel_id = table.get('hotel_id')
        if not hotel_id:
            return jsonify({"success": False, "message": "Hotel not configured for this table"}), 400
        
        full_menu = []
        categories = MenuCategory.get_categories_by_hotel(hotel_id)
        
        for category in categories:
            dishes_list = MenuDish.get_dishes_by_category(category['id'], hotel_id)
            dishes = [format_dish(dish) for dish in dishes_list]
            full_menu.append({
                "category_id": category['id'],
                "category_name": category['name'],
                "dishes": dishes
            })
        return jsonify({"success": True, "menu": full_menu})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@menu_bp.route("/api/public-daily-special/<int:table_id>")
def get_public_daily_special(table_id):
    """Public API to get today's daily special for a table - no login required"""
    try:
        from orders.table_models import Table
        from hotel_manager.models import DailySpecialMenu
        
        # Get the table to find its hotel_id
        table = Table.get_table_by_id(table_id)
        if not table:
            return jsonify({"success": False, "message": "Table not found"}), 404
        
        hotel_id = table.get('hotel_id')
        if not hotel_id:
            return jsonify({"success": False, "message": "Hotel not configured for this table"}), 400
        
        # Get today's special for this hotel
        special = DailySpecialMenu.get_today_special(hotel_id)
        
        if special:
            return jsonify({
                "success": True, 
                "special": {
                    "menu_name": special['menu_name'],
                    "description": special['description'],
                    "price": float(special['price']),
                    "image_path": special.get('image_path')
                }
            })
        return jsonify({"success": True, "special": None})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


@menu_bp.route("/api/dish/<int:dish_id>")
def get_dish(dish_id):
    hotel_id = session.get('hotel_id')
    if not hotel_id:
        return jsonify({"success": False, "message": "Hotel not found"}), 400
    
    try:
        dish = MenuDish.get_dish_by_id(dish_id, hotel_id)
        if dish:
            return jsonify({"success": True, "dish": format_dish(dish)})
        return jsonify({"success": False, "message": "Dish not found"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"})

# Initialize database tables for menu if using database
def init_menu_db():
    """Initialize menu database tables if needed"""
    pass
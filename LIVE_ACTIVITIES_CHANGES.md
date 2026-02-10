# LIVE ACTIVITY UPDATES - CODE CHANGES

## 📁 FILES MODIFIED

1. ✅ `admin/routes.py` - Added API endpoint + activity logging
2. ✅ `templates/admin/admin_dashboard.html` - Added JavaScript polling
3. ✅ `database/create_activities_table.sql` - SQL table creation
4. ✅ `setup_activities.py` - Python setup script

---

## 1️⃣ FLASK ROUTE CODE (`admin/routes.py`)

### Import Added:
```python
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
```

### Activity Logging in create_hotel():
```python
# After hotel creation, before commit
cursor.execute(
    "INSERT INTO recent_activities (activity_type, message) VALUES (%s, %s)",
    ('hotel_created', f'New hotel <strong>{hotel_name}</strong> was registered')
)
```

### Activity Logging in add_manager():
```python
# After manager creation, before commit
cursor.execute(
    "INSERT INTO recent_activities (activity_type, message) VALUES (%s, %s)",
    ('manager_added', f'Manager <strong>{name}</strong> was added to the system')
)
```

### API Endpoint:
```python
@admin_bp.route("/api/recent-activities")
def get_recent_activities():
    if "admin_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete activities older than 3 days
    cursor.execute("DELETE FROM recent_activities WHERE created_at < NOW() - INTERVAL 3 DAY")
    conn.commit()

    # Fetch latest 10 activities
    cursor.execute("""
        SELECT activity_type, message, created_at
        FROM recent_activities
        ORDER BY created_at DESC
        LIMIT 10
    """)
    activities = cursor.fetchall()
    conn.close()

    result = []
    for activity in activities:
        result.append({
            "activity_type": activity[0],
            "message": activity[1],
            "created_at": activity[2].strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result)
```

---

## 2️⃣ SQL CLEANUP QUERY

```sql
DELETE FROM recent_activities WHERE created_at < NOW() - INTERVAL 3 DAY
```

This runs automatically in the API endpoint before fetching activities.

---

## 3️⃣ JAVASCRIPT POLLING CODE (`admin_dashboard.html`)

### Activity List HTML (Updated):
```html
<ul class="activity-list" id="activityList">
    <li class="activity-item">
        <div class="activity-icon" style="background: rgba(79, 70, 229, 0.1); color: var(--primary);">
            <i class="fas fa-spinner fa-spin"></i>
        </div>
        <div class="activity-content">
            <p>Loading activities...</p>
            <span>Please wait</span>
        </div>
    </li>
</ul>
```

### JavaScript Code:
```javascript
// Activity icon mapping
const activityIcons = {
    'hotel_created': { icon: 'fa-hotel', color: 'rgba(16, 185, 129, 0.1)', iconColor: 'var(--success)' },
    'manager_added': { icon: 'fa-user-plus', color: 'rgba(79, 70, 229, 0.1)', iconColor: 'var(--primary)' },
    'kyc_verified': { icon: 'fa-id-card', color: 'rgba(245, 158, 11, 0.1)', iconColor: 'var(--warning)' },
    'system_update': { icon: 'fa-cog', color: 'rgba(6, 182, 212, 0.1)', iconColor: 'var(--secondary)' }
};

// Time formatting
function timeAgo(dateString) {
    const now = new Date();
    const past = new Date(dateString);
    const seconds = Math.floor((now - past) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 172800) return 'Yesterday';
    return Math.floor(seconds / 86400) + ' days ago';
}

// Fetch and update activities
function fetchActivities() {
    fetch('{{ url_for("admin.get_recent_activities") }}')
        .then(response => response.json())
        .then(data => {
            const activityList = document.getElementById('activityList');
            
            if (data.length === 0) {
                activityList.innerHTML = `
                    <li class="activity-item">
                        <div class="activity-icon" style="background: rgba(156, 163, 175, 0.1); color: var(--gray);">
                            <i class="fas fa-info-circle"></i>
                        </div>
                        <div class="activity-content">
                            <p>No recent activities</p>
                            <span>Start by creating a hotel or adding a manager</span>
                        </div>
                    </li>
                `;
                return;
            }

            activityList.innerHTML = data.map(activity => {
                const iconData = activityIcons[activity.activity_type] || activityIcons['system_update'];
                return `
                    <li class="activity-item">
                        <div class="activity-icon" style="background: ${iconData.color}; color: ${iconData.iconColor};">
                            <i class="fas ${iconData.icon}"></i>
                        </div>
                        <div class="activity-content">
                            <p>${activity.message}</p>
                            <span>${timeAgo(activity.created_at)}</span>
                        </div>
                    </li>
                `;
            }).join('');
        })
        .catch(error => console.error('Error fetching activities:', error));
}

// Initial load
fetchActivities();

// Poll every 10 seconds
setInterval(fetchActivities, 10000);
```

---

## 4️⃣ EXAMPLE JSON RESPONSE

```json
[
  {
    "activity_type": "hotel_created",
    "message": "New hotel <strong>Grand Palace</strong> was registered",
    "created_at": "2026-02-08 15:20:00"
  },
  {
    "activity_type": "manager_added",
    "message": "Manager <strong>John Doe</strong> was added to the system",
    "created_at": "2026-02-08 14:10:00"
  }
]
```

---

## 5️⃣ DATABASE TABLE

```sql
CREATE TABLE IF NOT EXISTS recent_activities (
    id INT PRIMARY KEY AUTO_INCREMENT,
    activity_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);
```

---

## 🚀 SETUP STEPS

1. **Create the table:**
   ```bash
   python setup_activities.py
   ```

2. **Restart Flask app**

3. **Test:**
   - Login to admin dashboard
   - Create a hotel or add a manager
   - Watch activities update automatically

---

## ✅ REQUIREMENTS MET

✅ Database table with auto-cleanup  
✅ Activity logging on hotel/manager creation  
✅ Auto-delete records older than 3 days  
✅ Live updates via AJAX polling (10 seconds)  
✅ Time formatting ("Just now", "2 minutes ago")  
✅ No UI/CSS changes  
✅ Clean, production-ready code  

**All requirements completed! 🎉**

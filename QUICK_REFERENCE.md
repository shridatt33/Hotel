# ⚡ LIVE ACTIVITIES - QUICK REFERENCE

## 🚀 SETUP (3 COMMANDS)
```bash
python setup_activities.py    # Create table
python test_activities.py     # Test setup
python app.py                 # Start app
```

## 📡 API ENDPOINT
```
GET /admin/api/recent-activities
Returns: JSON array of latest 10 activities
Auth: Session-based (admin_id required)
```

## 💾 DATABASE
```sql
-- Table
recent_activities (id, activity_type, message, created_at)

-- Cleanup
DELETE FROM recent_activities WHERE created_at < NOW() - INTERVAL 3 DAY
```

## 🔧 LOG ACTIVITY
```python
cursor.execute(
    "INSERT INTO recent_activities (activity_type, message) VALUES (%s, %s)",
    ('activity_type', 'Your message here')
)
conn.commit()
```

## 🎨 ACTIVITY TYPES
```javascript
'hotel_created'  → fa-hotel      (Green)
'manager_added'  → fa-user-plus  (Blue)
'kyc_verified'   → fa-id-card    (Orange)
'system_update'  → fa-cog        (Cyan)
```

## ⏱️ TIME FORMATTING
```
< 60s    → "Just now"
< 60m    → "X minutes ago"
< 24h    → "X hours ago"
< 48h    → "Yesterday"
> 48h    → "X days ago"
```

## 📝 EXAMPLE JSON
```json
[{
  "activity_type": "hotel_created",
  "message": "New hotel <strong>Grand Palace</strong> was registered",
  "created_at": "2026-02-08 15:20:00"
}]
```

## 🔄 POLLING
```javascript
// Initial load
fetchActivities();

// Auto-refresh every 10 seconds
setInterval(fetchActivities, 10000);
```

## 🎯 ADD NEW ACTIVITY TYPE
```javascript
// 1. Add to activityIcons object
'hotel_deleted': { 
    icon: 'fa-trash', 
    color: 'rgba(239, 68, 68, 0.1)', 
    iconColor: 'var(--danger)' 
}

// 2. Log in your route
cursor.execute(
    "INSERT INTO recent_activities (activity_type, message) VALUES (%s, %s)",
    ('hotel_deleted', f'Hotel <strong>{name}</strong> was deleted')
)
```

## 📁 KEY FILES
```
admin/routes.py                    # Backend API
templates/admin/admin_dashboard.html  # Frontend JS
setup_activities.py                # Setup script
test_activities.py                 # Test script
```

## 🐛 TROUBLESHOOTING
```bash
# Table doesn't exist?
python setup_activities.py

# Test everything
python test_activities.py

# Check API response
curl http://localhost:5000/admin/api/recent-activities

# Check browser console
F12 → Console tab
```

## ⚙️ CONFIGURATION
```python
# Change polling interval (in milliseconds)
setInterval(fetchActivities, 10000);  # 10 seconds

# Change activity limit
LIMIT 10  # In SQL query

# Change cleanup period
INTERVAL 3 DAY  # In DELETE query
```

## ✅ CHECKLIST
- [ ] Run setup_activities.py
- [ ] Run test_activities.py
- [ ] Start Flask app
- [ ] Login to dashboard
- [ ] Create hotel → Check activity
- [ ] Add manager → Check activity
- [ ] Wait 10s → Check refresh
- [ ] Verify timestamps

## 📚 DOCUMENTATION
- README_LIVE_ACTIVITIES.md - Main guide
- LIVE_ACTIVITIES_GUIDE.md - Full documentation
- LIVE_ACTIVITIES_CHANGES.md - Code changes
- SYSTEM_FLOW_DIAGRAM.md - Architecture

## 🎉 SUCCESS CRITERIA
✅ Activities appear immediately after action
✅ List refreshes every 10 seconds
✅ Timestamps are human-readable
✅ Icons match activity types
✅ Old activities (>3 days) are deleted
✅ No page reload needed

---

**Quick Start**: `python setup_activities.py && python app.py`

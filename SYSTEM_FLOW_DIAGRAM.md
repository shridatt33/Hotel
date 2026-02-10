# 🔄 LIVE ACTIVITY UPDATES - SYSTEM FLOW

## 📊 ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                        ADMIN DASHBOARD                          │
│                     (Browser - Frontend)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ JavaScript Polling
                              │ Every 10 seconds
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FLASK API ENDPOINT                           │
│          GET /admin/api/recent-activities                       │
│                                                                 │
│  1. Check session authentication                               │
│  2. Delete old activities (> 3 days)                           │
│  3. Fetch latest 10 activities                                 │
│  4. Return JSON response                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQL Queries
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MYSQL DATABASE                               │
│                                                                 │
│  Table: recent_activities                                      │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ id | activity_type | message | created_at           │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ 1  | hotel_created | New hotel...  | 2026-02-08... │     │
│  │ 2  | manager_added | Manager...    | 2026-02-08... │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ INSERT queries
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    ACTIVITY LOGGING                             │
│                                                                 │
│  Triggered by:                                                 │
│  • create_hotel() → Logs "hotel_created"                      │
│  • add_manager() → Logs "manager_added"                       │
│  • kyc_verify() → Logs "kyc_verified"                         │
│  • Any admin action                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW

### 1️⃣ ACTIVITY CREATION
```
User Action (Create Hotel)
    ↓
Flask Route (create_hotel)
    ↓
INSERT INTO recent_activities
    ↓
Database stores activity
    ↓
Redirect to dashboard
```

### 2️⃣ ACTIVITY DISPLAY
```
Dashboard loads
    ↓
JavaScript executes
    ↓
Fetch API call to /admin/api/recent-activities
    ↓
Flask endpoint processes request
    ↓
Delete old activities (> 3 days)
    ↓
Fetch latest 10 activities
    ↓
Return JSON response
    ↓
JavaScript updates DOM
    ↓
User sees activities
```

### 3️⃣ LIVE UPDATES
```
Every 10 seconds:
    ↓
JavaScript timer triggers
    ↓
Fetch API call
    ↓
Get latest activities
    ↓
Update activity list
    ↓
Format timestamps
    ↓
Apply icons and colors
    ↓
Display to user
```

---

## 🎯 COMPONENT INTERACTION

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Frontend   │◄────────│   Backend    │◄────────│   Database   │
│  (Browser)   │  JSON   │   (Flask)    │  SQL    │   (MySQL)    │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       │ 1. Page Load          │                        │
       │───────────────────────►│                        │
       │                        │ 2. Fetch Activities   │
       │                        │───────────────────────►│
       │                        │ 3. Return Data        │
       │                        │◄───────────────────────│
       │ 4. JSON Response      │                        │
       │◄───────────────────────│                        │
       │ 5. Update DOM         │                        │
       │                        │                        │
       │ (Wait 10 seconds)     │                        │
       │                        │                        │
       │ 6. Poll Again         │                        │
       │───────────────────────►│                        │
       │                        │ 7. Cleanup Old Data   │
       │                        │───────────────────────►│
       │                        │ 8. Fetch Latest       │
       │                        │───────────────────────►│
       │                        │ 9. Return Data        │
       │                        │◄───────────────────────│
       │ 10. JSON Response     │                        │
       │◄───────────────────────│                        │
       │ 11. Update DOM        │                        │
```

---

## 🕐 TIMELINE EXAMPLE

```
Time: 00:00 - User creates hotel "Grand Palace"
    ↓
    INSERT INTO recent_activities
    (activity_type='hotel_created', message='New hotel Grand Palace...')
    ↓
Time: 00:01 - Dashboard loads
    ↓
    JavaScript calls API
    ↓
    Returns: [{ "message": "New hotel Grand Palace...", "created_at": "..." }]
    ↓
    Display: "Just now"
    ↓
Time: 00:11 - Auto-refresh (10 seconds later)
    ↓
    JavaScript calls API again
    ↓
    Display: "10 seconds ago"
    ↓
Time: 00:21 - Auto-refresh
    ↓
    Display: "20 seconds ago"
    ↓
Time: 02:00 - Auto-refresh
    ↓
    Display: "2 hours ago"
    ↓
Time: 3 days + 1 second - Auto-refresh
    ↓
    API deletes old activity
    ↓
    Activity no longer shown
```

---

## 🔍 REQUEST/RESPONSE CYCLE

### REQUEST
```http
GET /admin/api/recent-activities HTTP/1.1
Host: localhost:5000
Cookie: session=abc123...
```

### PROCESSING
```python
1. Check session → Valid? Continue : Return 401
2. Execute: DELETE FROM recent_activities WHERE created_at < NOW() - INTERVAL 3 DAY
3. Execute: SELECT * FROM recent_activities ORDER BY created_at DESC LIMIT 10
4. Format results as JSON
5. Return response
```

### RESPONSE
```http
HTTP/1.1 200 OK
Content-Type: application/json

[
  {
    "activity_type": "hotel_created",
    "message": "New hotel <strong>Grand Palace</strong> was registered",
    "created_at": "2026-02-08 15:20:00"
  }
]
```

### FRONTEND PROCESSING
```javascript
1. Receive JSON response
2. Parse data
3. Loop through activities
4. For each activity:
   - Get icon based on activity_type
   - Format timestamp using timeAgo()
   - Build HTML string
5. Update DOM (innerHTML)
6. User sees updated list
```

---

## 📈 PERFORMANCE OPTIMIZATION

```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION LAYERS                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DATABASE LAYER                                         │
│     • Index on created_at column                           │
│     • LIMIT 10 (small result set)                          │
│     • Auto-cleanup prevents bloat                          │
│                                                             │
│  2. BACKEND LAYER                                          │
│     • Efficient SQL queries                                │
│     • Minimal data processing                              │
│     • Fast JSON serialization                              │
│                                                             │
│  3. NETWORK LAYER                                          │
│     • Small JSON payload                                   │
│     • 10-second polling (not too frequent)                 │
│     • Session-based auth (no token overhead)               │
│                                                             │
│  4. FRONTEND LAYER                                         │
│     • Efficient DOM updates                                │
│     • No page reload                                       │
│     • Minimal JavaScript processing                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 SECURITY FLOW

```
User Request
    ↓
Check Session
    ↓
    ├─ Valid Session? ──► Continue
    │
    └─ Invalid? ──► Return 401 Unauthorized
                    ↓
                    Stop
    ↓
Execute SQL with Parameterized Queries
    ↓
Sanitize Output (HTML escaping)
    ↓
Return JSON
    ↓
Frontend displays safely
```

---

## 🎨 UI UPDATE FLOW

```
API Response Received
    ↓
Parse JSON
    ↓
Check if empty
    ├─ Empty? ──► Show "No activities" message
    │
    └─ Has data? ──► Continue
                     ↓
                     Loop through activities
                     ↓
                     For each activity:
                     ├─ Map activity_type to icon
                     ├─ Format timestamp
                     ├─ Build HTML
                     └─ Append to list
                     ↓
                     Update DOM
                     ↓
                     User sees updated activities
```

---

## 🔄 COMPLETE LIFECYCLE

```
┌─────────────────────────────────────────────────────────────┐
│                    ACTIVITY LIFECYCLE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. CREATION                                               │
│     User performs action → Activity logged to database     │
│                                                             │
│  2. STORAGE                                                │
│     Activity stored with timestamp in MySQL                │
│                                                             │
│  3. RETRIEVAL                                              │
│     API fetches latest activities every 10 seconds        │
│                                                             │
│  4. DISPLAY                                                │
│     Frontend shows activities with formatted time          │
│                                                             │
│  5. AGING                                                  │
│     Timestamp gets older, display updates automatically    │
│                                                             │
│  6. CLEANUP                                                │
│     After 3 days, activity is automatically deleted        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 DATA TRANSFORMATION

```
DATABASE FORMAT:
{
  activity_type: "hotel_created",
  message: "New hotel <strong>Grand Palace</strong> was registered",
  created_at: datetime(2026, 2, 8, 15, 20, 0)
}
    ↓
BACKEND PROCESSING:
{
  "activity_type": "hotel_created",
  "message": "New hotel <strong>Grand Palace</strong> was registered",
  "created_at": "2026-02-08 15:20:00"
}
    ↓
FRONTEND PROCESSING:
{
  icon: "fa-hotel",
  color: "rgba(16, 185, 129, 0.1)",
  iconColor: "var(--success)",
  message: "New hotel <strong>Grand Palace</strong> was registered",
  timeAgo: "2 hours ago"
}
    ↓
HTML OUTPUT:
<li class="activity-item">
  <div class="activity-icon" style="background: rgba(16, 185, 129, 0.1); color: var(--success);">
    <i class="fas fa-hotel"></i>
  </div>
  <div class="activity-content">
    <p>New hotel <strong>Grand Palace</strong> was registered</p>
    <span>2 hours ago</span>
  </div>
</li>
```

---

**This diagram shows the complete flow of the live activity updates system!**

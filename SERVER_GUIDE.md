# Server Guide - Daphne vs Uvicorn

## 🚀 Quick Start

### For Collaborative Editor (WebSockets):
```bash
python run_daphne.py
```
Then visit: http://localhost:8000/collab/

### For Basic Django (No WebSockets):
```bash
python run_uvicorn.py
```
Then visit: http://localhost:8000/

---

## 📊 Server Comparison

| Feature | Daphne | Uvicorn |
|---------|--------|---------|
| **Django Channels** | ✅ Full support | ⚠️ Limited |
| **WebSockets** | ✅ Yes | ⚠️ Basic only |
| **Collaborative Editor** | ✅ Required | ❌ Won't work |
| **Regular Django** | ✅ Yes | ✅ Yes |
| **Speed** | Good | Slightly faster |
| **Use Case** | Production + WebSockets | Basic Django |

---

## 🎯 When to Use Each

### Use Daphne When:
- ✅ Working with collaborative editor (`/collab/`)
- ✅ Need WebSocket support
- ✅ Using Django Channels features
- ✅ Production deployment with real-time features

### Use Uvicorn When:
- ✅ Only using basic Django pages
- ✅ No WebSocket requirements
- ✅ Slightly better performance for HTTP-only

---

## 🔧 Current Project Status

**Collaborative Editor Status:** ✅ **ACTIVE**

The project now includes:
- Django Channels for WebSocket support
- Real-time text synchronization
- Room-based collaborative editing

**Therefore:** You **MUST use Daphne** to access `/collab/` features.

---

## 💻 Commands

### Start with Daphne (Recommended):
```bash
# Option 1: Using convenience script
python run_daphne.py

# Option 2: Direct command
daphne -b 0.0.0.0 -p 8000 mysite.asgi:application

# Option 3: With auto-reload (development)
daphne -b 0.0.0.0 -p 8000 mysite.asgi:application --reload
```

### Start with Uvicorn (Basic Django only):
```bash
# Option 1: Using convenience script
python run_uvicorn.py

# Option 2: Direct command
uvicorn mysite.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Check if Server is Running:
```bash
# Windows
netstat -ano | findstr :8000

# See running processes
tasklist | findstr python
```

### Stop Server:
- Press `Ctrl+C` in the terminal where it's running

---

## ⚠️ Common Issues

### Issue: "Address already in use"
**Problem:** Port 8000 is already occupied

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue: ModuleNotFoundError: No module named 'daphne'
**Problem:** Virtual environment not activated or daphne not installed

**Solution:**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### Issue: WebSocket connection failed
**Problem:** Using Uvicorn instead of Daphne

**Solution:** Use Daphne:
```bash
python run_daphne.py
```

---

## 📝 Configuration

### Current Setup:
- **ASGI Application:** `mysite.asgi:application`
- **Channel Layer:** InMemoryChannelLayer (development)
- **WebSocket URLs:** `/ws/collab/<room_name>/`
- **Default Port:** 8000
- **Default Host:** 0.0.0.0 (all interfaces)

### Production Notes:
- Switch to Redis channel layer for multi-server support
- Use reverse proxy (Nginx) in front of Daphne
- Enable SSL/TLS for secure WebSocket (wss://)
- Set proper ALLOWED_HOSTS in settings.py

---

## 🔗 URLs Available

### With Daphne Running:

**Collaborative Editor:**
- Home: http://localhost:8000/collab/
- Room: http://localhost:8000/collab/{room_name}/

**Regular Django:**
- Home: http://localhost:8000/
- LeetCode: http://localhost:8000/leetcode/
- Polls: http://localhost:8000/polls/
- Admin: http://localhost:8000/admin/

**All URLs work with both Daphne and Uvicorn**, but `/collab/` WebSockets only work with Daphne.

---

**Remember:** For the collaborative editor, always use Daphne! 🚀

*Last updated: October 7, 2025*


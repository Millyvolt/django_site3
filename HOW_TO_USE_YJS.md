# How to Access Y.js CRDT Editor

## ✅ Server is Running on Port 8000

The Daphne server is currently running and ready!

---

## 🎯 Step-by-Step Guide

### Step 1: Open Your Browser
Navigate to:
```
http://localhost:8000/collab/
```

**OR**

```
http://127.0.0.1:8000/collab/
```

---

### Step 2: You Should See This Page

**Title:** "🤝 Collaborative Editor"  
**Subtitle:** "Real-time collaborative text editing"

**There will be a form with:**

1. **"Enter Room Name:"** input field
   - Example: "test-room", "my-project", etc.

2. **"Choose Synchronization Method:"** (Radio buttons)
   - ⚪ **Simple Sync** (selected by default)
   - ⚪ **Y.js CRDT ⭐** ← **SELECT THIS ONE!**

3. **"Join / Create Room"** button

---

### Step 3: Select Y.js CRDT

Click on the **"Y.js CRDT ⭐"** radio button.

You should see:
- A radio button next to "Simple Sync"
- A radio button next to "Y.js CRDT ⭐" (with a star)

---

### Step 4: Enter Room Name

Type any room name (e.g., "test-room")

---

### Step 5: Click "Join / Create Room"

This will take you to:
```
http://localhost:8000/collab/yjs/test-room/
```

Notice the `/yjs/` in the URL - this is the Y.js version!

---

## 🔍 Troubleshooting

### If You Don't See the Radio Buttons:

1. **Clear Browser Cache:**
   - Press `Ctrl + Shift + Delete`
   - Clear cached images and files
   - Try again

2. **Hard Refresh:**
   - Press `Ctrl + F5` to force reload

3. **Try a Different Browser:**
   - Chrome
   - Firefox
   - Edge

4. **Check the Correct URL:**
   - Make sure you're at `http://localhost:8000/collab/`
   - NOT `http://localhost:8000/` (root)

---

## 📸 What You Should See

### On the Home Page (`/collab/`):

```
┌─────────────────────────────────────────┐
│  🤝 Collaborative Editor                │
│  Real-time collaborative text editing   │
│                                          │
│  Enter Room Name:                        │
│  ┌─────────────────────────────────┐   │
│  │ e.g., my-project, team-meeting  │   │
│  └─────────────────────────────────┘   │
│                                          │
│  Choose Synchronization Method:          │
│  ◉ Simple Sync                           │
│  ○ Y.js CRDT ⭐                          │
│                                          │
│  ┌───────────────────────────────┐      │
│  │   Join / Create Room          │      │
│  └───────────────────────────────┘      │
└─────────────────────────────────────────┘
```

### On the Y.js Room Page (`/collab/yjs/test-room/`):

```
┌───────────────────────────────────────────────┐
│  📝 Room: test-room          ● Connected      │
│                        ← Back to Rooms        │
├───────────────────────────────────────────────┤
│  Collaborative Text Editor  [Y.js CRDT]       │
│                                    👤 YourName│
├───────────────────────────────────────────────┤
│                                                │
│  [Type here - real-time Y.js sync!]           │
│                                                │
│                                                │
│                                                │
└───────────────────────────────────────────────┘
│  💡 Enhanced with Y.js CRDT:                  │
│  • Character-level synchronization            │
│  • Perfect handling of simultaneous edits     │
└───────────────────────────────────────────────┘
```

**Look for the green badge:** `[Y.js CRDT]` in the editor header!

---

## 🧪 Test It Works

### Quick Test:

1. Open the Y.js room: `http://localhost:8000/collab/yjs/test-room/`
2. Open the **same URL** in another browser tab
3. Type in one tab
4. See it appear in the other tab **in real-time!**

### Check Browser Console:

Press `F12` and look for:
```
Y.js initialized: ...
✓ WebSocket connected
✓ Sent Y.js update to server, size: X bytes
```

---

## ⚠️ Important Notes

### URLs:

**Simple Sync (old way):**
```
http://localhost:8000/collab/test-room/
```

**Y.js CRDT (new way):**
```
http://localhost:8000/collab/yjs/test-room/
                              ^^^^
                         Notice "yjs" here!
```

---

## 🆘 Still Can't See It?

### Option 1: Direct URL

Skip the home page and go directly to:
```
http://localhost:8000/collab/yjs/test-room/
```

This bypasses the selection page and goes straight to the Y.js editor.

### Option 2: Check Server Logs

Look at your terminal where the server is running. You should see:
```
============================================================
Starting Django with Daphne ASGI Server
============================================================
Server will be available at:
  - http://localhost:8000
  - http://127.0.0.1:8000
```

If you don't see this, the server isn't running.

### Option 3: Restart Server

In your terminal:
1. Press `Ctrl + C` to stop the server
2. Run: `python run_daphne.py`
3. Try accessing the page again

---

## ✅ Success Indicators

You'll know Y.js is working when you see:

1. **URL contains `/yjs/`**
2. **Green badge** in editor: `Y.js CRDT`
3. **Browser console** shows "Y.js initialized"
4. **Multiple tabs** sync perfectly without conflicts
5. **Character-by-character** sync (not full text)

---

*Guide created: October 7, 2025*  
*Server: Daphne on port 8000*


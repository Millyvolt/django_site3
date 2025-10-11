# 🚀 Monaco Editor - Quick Start Guide

## ✅ Phase 2 Implementation Complete!

Monaco Editor is now fully functional and ready to use!

---

## 🎯 Quick Test (5 minutes)

### 1. Start the Server

```bash
cd C:\Projects_cursor\django_site3
venv\Scripts\activate
python run_dev_server.py
```

Wait for: `Server running at http://127.0.0.1:8000/`

### 2. Open First Browser Tab

1. Go to: `http://localhost:8000/collab/`
2. Find the **"Monaco Editor (IDE)"** card (with VS Code badge)
3. Enter room name: `test-monaco`
4. Select language: **JavaScript**
5. Click **"Join / Create Room"**

**You should see:**
- ✅ Monaco Editor loads (1-3 seconds)
- ✅ Loading spinner disappears
- ✅ Dark theme editor appears
- ✅ Connection status shows "Connected"
- ✅ Green pulsing dot in header
- ✅ Minimap visible on right side

### 3. Open Second Browser Tab

1. Go to: `http://localhost:8000/collab/`
2. Click **"Monaco Editor (IDE)"**
3. Enter same room: `test-monaco`
4. Select same language: **JavaScript**
5. Click **"Join / Create Room"**

### 4. Test Real-Time Collaboration

**In Tab 1, type:**
```javascript
function hello() {
    console.log("Hello from Tab 1!");
}
```

**Result:** Should appear instantly in Tab 2! ✨

**In Tab 2, type:**
```javascript
function goodbye() {
    console.log("Goodbye from Tab 2!");
}
```

**Result:** Should appear instantly in Tab 1! ✨

### 5. Test Language Switching

**In Tab 1:**
1. Click the **Language** dropdown
2. Select **Python**

**Result:**
- ✅ Both tabs switch to Python
- ✅ Syntax highlighting changes
- ✅ Code remains intact

**Now type Python code:**
```python
def greet():
    print("Hello Python!")
```

### 6. Test IntelliSense (Autocomplete)

**Switch back to JavaScript:**
1. Change language to **JavaScript**
2. Type: `console.`
3. Wait 1 second

**Result:**
- ✅ Autocomplete menu appears
- ✅ Shows: `log`, `error`, `warn`, `info`, etc.
- ✅ You can select with arrow keys + Enter

### 7. Test Theme Switching

**In Tab 1 only:**
1. Click **Theme** dropdown
2. Select **Light**

**Result:**
- ✅ Tab 1 switches to light theme
- ✅ Tab 2 stays dark (personal preference!)
- ✅ Reload Tab 1: theme persists (localStorage)

### 8. Test Other Features

**Minimap:**
- Type 50+ lines of code
- See minimap on right showing overview
- Click minimap to jump to sections

**Zoom:**
- Hold `Ctrl` (or `Cmd` on Mac)
- Scroll mouse wheel
- Font size increases/decreases

**Multi-cursor:**
- Hold `Alt` (or `Option` on Mac)
- Click multiple locations
- Type - appears in all places!

**Code Folding:**
- Write a function or if-statement
- See arrow icon next to line number
- Click to collapse/expand

---

## 🎨 Test All 12 Languages

Try switching between:

1. **JavaScript** - Type `console.log()` - see IntelliSense
2. **TypeScript** - Type `const x: string = "test"` - see type highlighting
3. **Python** - Type `def hello():` - see indentation guides
4. **Java** - Type `public class Test {}` - see class highlighting
5. **C++** - Type `#include <iostream>` - see preprocessor highlighting
6. **C#** - Type `using System;` - see namespace highlighting
7. **Go** - Type `package main` - see package highlighting
8. **Rust** - Type `fn main() {}` - see function highlighting
9. **HTML** - Type `<div>` - see tag autocomplete
10. **CSS** - Type `.class {` - see property autocomplete
11. **SQL** - Type `SELECT * FROM` - see SQL keyword highlighting
12. **JSON** - Type `{"key":` - see bracket matching

---

## 🐛 Troubleshooting

### Monaco doesn't load / white screen
- **Check console:** Press F12, look for errors
- **Check network:** Look in Network tab for failed requests
- **CDN issue?** Try reloading page (CDN might be slow)
- **Firewall?** Check if `cdn.jsdelivr.net` is blocked

### Changes don't sync between tabs
- **Check connection:** Look for green dot in header
- **Check WebSocket:** Console should show "WebSocket connected"
- **Server running?** Make sure Daphne is running
- **Different rooms?** Both tabs must use same room name

### Cursor jumps when other user types
- This is **expected behavior** with simple sync
- Cursor preservation works for receiving updates, not simultaneous edits
- For perfect cursor handling, upgrade to Y-Monaco in Phase 3

### Theme doesn't save
- **localStorage blocked?** Check browser privacy settings
- **Incognito mode?** localStorage doesn't persist in incognito
- **Try again:** Select theme, reload page

---

## 📊 Performance Check

### Good Performance Indicators:
- ✅ Monaco loads in <3 seconds
- ✅ Typing feels instant (no lag)
- ✅ Changes appear in other tab within 300-400ms
- ✅ Language switching is instant
- ✅ Theme switching is instant
- ✅ No console errors

### If Performance is Poor:
- **Slow load:** CDN might be slow, try again later
- **Typing lag:** Check CPU usage (close other apps)
- **Sync lag:** Check network (run locally, not over VPN)
- **Memory issues:** Close other browser tabs

---

## 🎉 Success Checklist

After testing, you should see:

- ✅ Monaco Editor loads successfully
- ✅ Can type and edit code
- ✅ Syntax highlighting works for all 12 languages
- ✅ Changes sync between browser tabs in real-time
- ✅ Language changes sync across users
- ✅ Theme selector works (personal preference)
- ✅ IntelliSense appears (try JavaScript `console.`)
- ✅ Minimap visible on right side
- ✅ Zoom works (Ctrl + scroll)
- ✅ Connection status accurate
- ✅ No console errors
- ✅ Professional look and feel

---

## 🚀 Next Steps

### Use It!
- Create different rooms for different projects
- Collaborate with friends on coding problems
- Use for pair programming
- Practice coding interview problems

### Share the URL:
```
http://localhost:8000/collab/
```

Anyone on your local network can join!

### Upgrade (Optional):
If you want advanced features:
- **Phase 3:** Y-Monaco for visible user cursors
- **Phase 4:** Code execution/testing
- **Phase 5:** Save code to database

---

## 💡 Pro Tips

1. **URL Parameters:**
   - `?lang=python` - Start with Python
   - `?lang=javascript` - Start with JavaScript

2. **Keyboard Shortcuts (Monaco built-in):**
   - `Ctrl+F` - Find
   - `Ctrl+H` - Replace
   - `Ctrl+/` - Toggle comment
   - `Alt+Shift+F` - Format code
   - `Ctrl+Space` - Trigger IntelliSense

3. **Theme Persistence:**
   - Your theme choice is saved per browser
   - Each user can have their own theme
   - Doesn't affect other users

4. **Best Languages for IntelliSense:**
   - JavaScript ⭐⭐⭐⭐⭐
   - TypeScript ⭐⭐⭐⭐⭐
   - HTML ⭐⭐⭐⭐
   - CSS ⭐⭐⭐⭐
   - JSON ⭐⭐⭐⭐

5. **For Coding Interviews:**
   - Use C++ or Python (most common)
   - Share room name: `interview-2025`
   - Interviewer and candidate see same code

---

**Enjoy your new VS Code-like collaborative editor! 🎊**

*Need help? Check PHASE_2_COMPLETE.md for detailed documentation.*


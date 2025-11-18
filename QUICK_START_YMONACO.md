# Quick Start: Monaco + Y.js CRDT

**Ready to test in 30 seconds!** ⚡

---

## 🚀 Start the Server

```bash
python run_dev_server.py
```

Wait for: `Starting development server at http://127.0.0.1:8000/`

---

## 🎯 Test in 3 Steps

### Step 1: Create Room
1. Open: `http://localhost:8000/collab/`
2. Room name: `test-crdt`
3. Editor type: **Monaco + Y.js (CRDT IDE)**
4. Language: **Python**
5. Click **"Join / Create Room"**

✅ **Expected:** Monaco editor loads with status "Connected (Y.js CRDT)"

---

### Step 2: Join from Another Browser
1. Open **Incognito/Private window**
2. Go to: `http://localhost:8000/collab/monaco-yjs/test-crdt/?lang=python`

✅ **Expected:** Same room, empty editor

---

### Step 3: Test CRDT Magic! ⭐
1. **Browser 1:** Type `def hello():`
2. **Watch Browser 2:** Text appears in real-time!
3. **Both browsers:** Put cursor at line 1, column 1
4. **Browser 1:** Type `AAAA`
5. **Browser 2:** Type `BBBB` (simultaneously)

✅ **Expected:** Both edits appear, perfectly merged, no data loss!

---

## ✨ What You Should See

### Console Output (Browser DevTools)
```
✓ Monaco Editor loaded from CDN
✓ Loading Y.js libraries...
✓ Y.js loaded from CDN
✓ y-websocket loaded from CDN
✓ y-monaco loaded from CDN
✓ Initializing Monaco with Y.js CRDT...
✓ Monaco Editor created
✓ Y.js modules imported successfully
✓ Y.js binding created
WebSocket status: connected
```

### Status Indicator
- 🟢 Green pulsing dot
- Text: "Connected (Y.js CRDT) - Room: test-crdt"

---

## 🎮 Try These!

### Test Conflict Resolution
- Both users type at same position
- All text preserved and merged

### Test Language Switching
- Change dropdown to JavaScript
- Syntax highlighting updates

### Test Theme
- Switch between Dark/Light/High Contrast
- Theme persists across sessions

### Test Reconnection
- Stop server (Ctrl+C)
- Status shows "Disconnected - Reconnecting..."
- Restart server
- Auto-reconnects!

---

## 🐛 If Something Goes Wrong

### "Failed to Load Monaco Editor"
```bash
# Re-run download script
.\download_monaco_full.ps1
```

### "Failed to Load Y.js Libraries"
```bash
# Re-run Y.js download script
.\download_yjs_libs.ps1
```

### Server Not Starting
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed, then restart
python run_dev_server.py
```

### WebSocket Not Connecting
- Check that Daphne is running (not runserver)
- Check console for errors
- Verify URL includes `/ws/collab/`

---

## 📚 Full Documentation

- **Testing Guide:** `PHASE_3_YMONACO_TESTING_GUIDE.md` (12 comprehensive tests)
- **Implementation Details:** `PHASE_3_CRDT_IMPLEMENTATION_COMPLETE.md`
- **Project Roadmap:** `COLLABORATIVE_EDITOR_ROADMAP.md`

---

## 🎉 Success!

If you see text syncing in real-time between browsers with perfect conflict resolution, **you're done!**

Your collaborative IDE with Y.js CRDT is working! 🚀

---

**Next Steps:**
1. Run full test suite (12 tests in testing guide)
2. Add user cursors (Phase 3 full - optional)
3. Add code execution (Phase 4)
4. Or ship it! ✅









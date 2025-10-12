# 🧪 Quick Test Guide: User Awareness Features

## Prerequisites

1. **Multiple Authenticated Users:**
   - You need at least 2 user accounts
   - Or use 2 different browsers (one logged in, one incognito with different user)

2. **Server Running:**
   ```bash
   python run_dev_server.py
   ```

---

## 🚀 Quick Test (5 Minutes)

### Step 1: Open Two Tabs
1. **Tab 1:** Login as User A
2. **Tab 2:** Login as User B (different browser or incognito)
3. Both navigate to: `http://localhost:8000/collab/monaco-yjs/test-room/`

### Step 2: Check User List
1. Click the **👥** button (top right)
2. You should see:
   - **Both users listed** with their names
   - **Different colored circles** for each user
   - **User count badge** showing "2"
   - **"(You)"** label next to your own name

### Step 3: Test Cursors
1. **In Tab 1:** Click in the editor and move your cursor around
2. **In Tab 2:** You should see:
   - A **colored line** (User A's cursor)
   - User A's **name label** above the cursor
   - The cursor **following** User A's movements in real-time

### Step 4: Test Selections
1. **In Tab 1:** Select several lines of text (drag to select)
2. **In Tab 2:** You should see:
   - The selected text **highlighted** in User A's color
   - **Semi-transparent** background (30% opacity)
   - Highlight **disappears** when User A deselects

### Step 5: Test Both Ways
1. Now do the same from **Tab 2** → **Tab 1**
2. Each user should see the other's cursor/selection in a **different color**

### Step 6: Test Disconnect
1. **Close Tab 1** (User A leaves)
2. **In Tab 2:** You should see:
   - User A **disappears** from user list
   - User count updates to **"1"**
   - User A's **cursor/selection removed** from editor

---

## ✅ What You Should See

### User List Panel:
```
┌─────────────────────────────────┐
│ Online Users            [2]  [×]│
├─────────────────────────────────┤
│ ●  john_doe (You)              │
│    Online                       │
├─────────────────────────────────┤
│ ●  jane_smith                  │
│    Online                       │
└─────────────────────────────────┘
```

### Cursors in Editor:
```javascript
function hello() {
    console.log("Hello");  ← [john_doe]
    return true;           ← [jane_smith]
}
```

### Selections in Editor:
```javascript
function hello() {
    ████████████████████████  ← Highlighted in user color
    ████████████████████████
}
```

---

## 🎨 Color Palette

Each user gets one of these colors:
- 🔴 Red (#FF6B6B)
- 🔵 Cyan (#4ECDC4)
- 🔵 Blue (#45B7D1)
- 🟠 Orange (#FFA07A)
- 🟢 Mint (#98D8C8)
- 🟡 Yellow (#F7DC6F)
- 🟣 Purple (#BB8FCE)
- 🔵 Sky Blue (#85C1E2)
- 🟠 Peach (#F8B88B)
- 🟢 Light Green (#ABEBC6)

---

## 🐛 Troubleshooting

### "I don't see other users' cursors"
- ✅ Make sure **both users are authenticated** (logged in)
- ✅ Check that **both are in the same room** (same URL)
- ✅ Open browser console and look for:
  - `✓ User joined: [username]`
  - `✓ WebSocket connected`

### "User list is empty"
- ✅ Click the **👥 button** to open the panel
- ✅ Refresh the page and check again
- ✅ Verify you're logged in (check top-right user badge)

### "Cursors appear but don't move"
- ✅ Wait 100ms (debounce delay)
- ✅ Check console for `✓ [Room: ...] Awareness update`
- ✅ Try moving cursor more dramatically (across multiple lines)

### "Selection highlighting doesn't work"
- ✅ Make sure you're **selecting text** (not just clicking)
- ✅ Select at least a few words or lines
- ✅ Check that the other user's cursor is visible

---

## 📊 Performance Test

### Test with 3+ Users:
1. Open **4-5 browser tabs** with different users
2. All users type simultaneously
3. Move cursors around quickly
4. Select different text sections

**Expected Results:**
- ✅ All cursors visible and color-coded
- ✅ No lag or stuttering
- ✅ Selections don't overlap incorrectly
- ✅ User list updates correctly
- ✅ No console errors

---

## 🔍 Debug Mode

Open browser console (F12) to see detailed logs:

```
✓ User john_doe (ID: 1) connected to room: test-room
✓ User joined: jane_smith
✓ Awareness update from jane_smith
✓ Remote user cursor at line 5, column 10
✓ User left: jane_smith
```

---

## 📱 Mobile Test

1. Open on mobile device
2. User list should appear as **bottom sheet**
3. Toggle button at **bottom-right**
4. Cursors/selections should be **touch-friendly**

---

## ✅ Success Criteria

Your implementation is working if:
- [x] User list shows all online users
- [x] Cursors appear in real-time (within 100ms)
- [x] Each user has a unique color
- [x] Selections are highlighted correctly
- [x] Users disappear when they disconnect
- [x] No console errors
- [x] Smooth performance with 3+ users

---

## 🎯 Next Steps

Once testing is complete:
1. ✅ Mark the testing TODO as complete
2. ✅ Update COLLABORATIVE_EDITOR_ROADMAP.md
3. ✅ Commit changes to git
4. 🚀 Deploy to production!

---

*Happy Testing!* 🎉


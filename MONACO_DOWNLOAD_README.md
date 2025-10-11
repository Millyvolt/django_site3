# Monaco Editor Download Scripts

Two PowerShell scripts are available to download Monaco Editor files for local backup.

---

## Quick Start (Recommended)

**Use the full download script:**

```powershell
powershell -ExecutionPolicy Bypass -File download_monaco_full.ps1
```

This downloads the **complete** Monaco Editor package (13.41 MB, 112 files) from npm.

---

## Scripts Available

### 1. `download_monaco_full.ps1` ⭐ **RECOMMENDED**

**What it does:**
- Downloads complete Monaco package from npm registry
- Extracts all files using tar (Windows 10+ built-in)
- Copies to `collab/static/collab/monaco/vs/`
- ~30-60 seconds to complete

**Size:** 13.41 MB (112 files)

**Includes:**
- All languages (50+ languages)
- All workers (TypeScript, JSON, CSS, HTML, editor)
- All themes (vs-dark, vs, hc-black)
- All localization files

**Run:**
```powershell
powershell -ExecutionPolicy Bypass -File download_monaco_full.ps1
```

---

### 2. `download_monaco.ps1` (Minimal)

**What it does:**
- Downloads only essential Monaco files from jsDelivr CDN
- Downloads files one by one
- Smaller but may miss some dependencies

**Size:** ~3-4 MB (20-30 files)

**Includes:**
- Core editor files
- Only our 12 languages
- Basic workers

**Run:**
```powershell
powershell -ExecutionPolicy Bypass -File download_monaco.ps1
```

**⚠️ Note:** May not include all dependencies. Use `download_monaco_full.ps1` instead.

---

## Which Script to Use?

| Scenario | Recommended Script |
|----------|-------------------|
| **First-time setup** | `download_monaco_full.ps1` |
| **Production deployment** | `download_monaco_full.ps1` |
| **Quick test** | `download_monaco_full.ps1` |
| **Limited bandwidth** | `download_monaco.ps1` (not recommended) |

**TL;DR:** Always use `download_monaco_full.ps1` ⭐

---

## Requirements

### Windows 10 or later (recommended)
- Built-in `tar` command for extraction
- PowerShell 5.0+

### Alternative: 7-Zip
- If tar fails, script will try 7-Zip
- Download: https://www.7-zip.org/

### Internet Connection
- Download requires ~16 MB download
- Takes 30-60 seconds on typical connection

---

## Troubleshooting

### "Execution Policy" Error

**Error:**
```
... cannot be loaded because running scripts is disabled...
```

**Solution:**
```powershell
powershell -ExecutionPolicy Bypass -File download_monaco_full.ps1
```

---

### "Files Already Exist" Warning

**Message:**
```
WARNING: Monaco files already exist at: collab\static\collab\monaco\vs
Do you want to re-download? (y/n)
```

**Options:**
- Type `n` to keep existing files
- Type `y` to re-download

**Or delete manually:**
```powershell
Remove-Item -Path "collab\static\collab\monaco" -Recurse -Force
```

---

### "tar extraction failed" Error

**Solution 1:** Update to Windows 10 or later (has built-in tar)

**Solution 2:** Install 7-Zip
```
Download: https://www.7-zip.org/
Install to: C:\Program Files\7-Zip\
```

**Solution 3:** Use online extraction
1. Download: https://registry.npmjs.org/monaco-editor/-/monaco-editor-0.54.0.tgz
2. Extract using https://extract.me/
3. Copy `package/min/vs/` to `collab/static/collab/monaco/vs/`

---

### Slow Download

**Typical times:**
- Fast connection (50 Mbps+): 10-20 seconds
- Average connection (10-50 Mbps): 30-60 seconds
- Slow connection (<10 Mbps): 1-3 minutes

**If taking longer:**
- Check internet connection
- Check firewall settings
- Try again later (npm registry may be slow)

---

## What Gets Downloaded?

### Directory Structure

```
collab/static/collab/monaco/vs/
├── loader.js                 # AMD module loader (critical!)
├── editor/
│   ├── editor.main.js        # Core editor (~3 MB)
│   ├── editor.main.css       # Editor styles
│   └── editor.main.nls.js    # Localization
├── assets/                   # Web workers
│   ├── editor.worker-*.js    # General worker
│   ├── ts.worker-*.js        # TypeScript/JavaScript
│   ├── json.worker-*.js      # JSON
│   ├── css.worker-*.js       # CSS
│   └── html.worker-*.js      # HTML
├── basic-languages/          # Language definitions
│   └── monaco.contribution.js
├── language/                 # Advanced features
│   ├── typescript/           # TypeScript IntelliSense
│   ├── json/                 # JSON validation
│   ├── css/                  # CSS features
│   └── html/                 # HTML features
├── cpp-*.js                  # C++ syntax
├── python-*.js               # Python syntax
├── javascript-*.js           # JavaScript syntax
├── rust-*.js                 # Rust syntax
└── ... (50+ more languages)
```

---

## After Download

### Verify Files

**Check if download succeeded:**
```powershell
dir collab\static\collab\monaco\vs\loader.js
```

**Should show:**
```
    Directory: C:\Projects_cursor\django_site3\collab\static\collab\monaco\vs

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        10/11/2025   2:30 PM          12345 loader.js
```

**Count files:**
```powershell
(Get-ChildItem -Path "collab\static\collab\monaco\vs" -Recurse -File | Measure-Object).Count
```

**Should show:** `112` files

---

### Test Monaco

1. **Start server:**
   ```bash
   python run_dev_server.py
   ```

2. **Open Monaco room:**
   ```
   http://localhost:8000/collab/monaco/test/
   ```

3. **Block CDN to test fallback:**
   - Press F12 (DevTools)
   - Go to Network tab
   - Block domain: `cdn.jsdelivr.net`
   - Reload page

4. **Check console:**
   ```
   Expected: "✗ CDN failed, trying local files..."
   Expected: "✓ Monaco Editor loaded from local files"
   ```

5. **Verify editor works:**
   - Type code
   - Change language
   - Check syntax highlighting

---

## Updating Monaco

To update to a newer version:

1. **Change version in script:**
   ```powershell
   # Edit download_monaco_full.ps1
   $MonacoVersion = "0.55.0"  # Or latest version
   ```

2. **Delete old files:**
   ```powershell
   Remove-Item -Path "collab\static\collab\monaco" -Recurse -Force
   ```

3. **Run script:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File download_monaco_full.ps1
   ```

4. **Update CDN URL in template:**
   ```javascript
   // Edit collab/templates/collab/room_monaco.html
   // Change:
   https://cdn.jsdelivr.net/npm/monaco-editor@0.54.0/min/vs
   // To:
   https://cdn.jsdelivr.net/npm/monaco-editor@0.55.0/min/vs
   ```

---

## File Sizes

| Component | Size |
|-----------|------|
| Download (.tgz) | 15.94 MB |
| Extracted | 13.41 MB |
| Core editor | ~3 MB |
| Workers | ~2 MB |
| Languages | ~8 MB |
| Other | ~0.41 MB |

---

## Need Help?

**Check these files:**
- `MONACO_LOCAL_BACKUP_COMPLETE.md` - Full implementation guide
- `MONACO_QUICK_START.md` - Quick testing guide
- `PHASE_2_COMPLETE.md` - Monaco editor documentation

**Still stuck?**
1. Check console (F12) for errors
2. Verify files downloaded (112 files, 13.41 MB)
3. Check Django serving static files correctly
4. Try clearing browser cache

---

*Scripts created: October 11, 2025*  
*Monaco Version: 0.54.0*


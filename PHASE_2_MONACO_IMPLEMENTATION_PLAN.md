# Phase 2: Monaco Editor Implementation Plan

**Editor Choice:** Monaco Editor (VS Code's Editor)  
**Difficulty:** ⭐⭐⭐⭐ High  
**Estimated Time:** 2-3 hours  
**Bundle Size:** ~5MB  
**Result:** Full-featured IDE experience in the browser

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Why Monaco?](#why-monaco)
3. [Implementation Steps](#implementation-steps)
4. [File Structure](#file-structure)
5. [Technical Details](#technical-details)
6. [Challenges & Solutions](#challenges--solutions)
7. [Code Examples](#code-examples)
8. [Testing Plan](#testing-plan)
9. [Future Enhancements](#future-enhancements)

---

## 🎯 **Overview**

### **What We're Building:**
A collaborative code editor powered by Monaco Editor (the same engine that runs VS Code), featuring:
- ✅ Full IDE-like editing experience
- ✅ IntelliSense (intelligent code completion)
- ✅ Syntax highlighting for 50+ languages
- ✅ Multi-cursor editing
- ✅ Minimap
- ✅ Error checking & linting
- ✅ Real-time collaborative editing
- ✅ Code folding
- ✅ Find & Replace
- ✅ Command palette
- ✅ Git diff view (optional)

---

## 🚀 **Why Monaco?**

### **Advantages:**
- **Most Powerful:** Same editor as VS Code
- **IntelliSense:** Autocomplete, parameter hints, quick info
- **Multi-cursor:** Edit multiple locations simultaneously
- **Rich API:** Extensive customization options
- **TypeScript Support:** Best-in-class TypeScript/JavaScript support
- **Professional:** Industry-standard editor
- **Actively Maintained:** Microsoft backing

### **Disadvantages:**
- **Large Size:** ~5MB bundle (vs 500KB for CodeMirror)
- **Complex Setup:** More configuration required
- **Loading Time:** Takes longer to initialize
- **Resource Heavy:** Uses more memory
- **CDN Required:** Or need to host large files locally

### **When to Choose Monaco:**
- ✅ Building a serious coding platform
- ✅ Need autocomplete/IntelliSense
- ✅ Want VS Code experience
- ✅ Professional/commercial application
- ✅ Don't mind larger bundle size

---

## 📝 **Implementation Steps**

### **Phase 2A: Basic Setup** (1 hour)

#### **Step 1: Download Monaco Editor**
```bash
# Option A: Via npm (if using build tools)
npm install monaco-editor

# Option B: Download from CDN (easiest)
# We'll use this approach - download to static files
```

**Files to download:**
- `monaco-editor/min/vs/` folder (~5MB)
  - `loader.js` - AMD loader
  - `editor/` - Editor modules
  - `base/` - Base components
  - `basic-languages/` - Language definitions
  - `language/` - Advanced language features

**Where to place:**
```
collab/static/collab/monaco/
├── vs/
│   ├── loader.js
│   ├── editor/
│   ├── base/
│   ├── basic-languages/
│   └── language/
```

---

#### **Step 2: Create Monaco Template**

Create: `collab/templates/collab/room_monaco.html`

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Monaco Editor - Room {{ room_name }}</title>
    <style>
        /* Full-screen Monaco container */
        #editor-container { height: 100vh; }
    </style>
</head>
<body>
    <div id="header">...</div>
    <div id="editor-container"></div>
    
    <!-- Monaco Loader -->
    <script src="{% static 'collab/monaco/vs/loader.js' %}"></script>
    <script>
        require.config({ paths: { vs: '{% static "collab/monaco/vs" %}' }});
        require(['vs/editor/editor.main'], function() {
            // Initialize Monaco
        });
    </script>
</body>
</html>
```

---

#### **Step 3: Add URL Route**

Update: `collab/urls.py`
```python
urlpatterns = [
    path('', views.collab_home, name='collab_home'),
    path('room/<str:room_name>/', views.collab_room, name='collab_room'),
    path('room-yjs/<str:room_name>/', views.collab_room_yjs, name='collab_room_yjs'),
    path('room-monaco/<str:room_name>/', views.collab_room_monaco, name='collab_room_monaco'),  # NEW
]
```

---

#### **Step 4: Add View Function**

Update: `collab/views.py`
```python
def collab_room_monaco(request, room_name):
    """
    Collaborative editor room with Monaco Editor.
    Full IDE experience with IntelliSense and advanced features.
    """
    return render(request, 'collab/room_monaco.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user': request.user
    })
```

---

### **Phase 2B: Monaco Integration** (1 hour)

#### **Step 5: Initialize Monaco Editor**

**JavaScript code structure:**
```javascript
require(['vs/editor/editor.main'], function() {
    // 1. Create Monaco editor instance
    const editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: '',  // Initial content
        language: 'javascript',  // Default language
        theme: 'vs-dark',  // Theme: 'vs', 'vs-dark', 'hc-black'
        
        // IDE Features
        automaticLayout: true,  // Auto-resize
        minimap: { enabled: true },  // Code minimap
        fontSize: 14,
        lineNumbers: 'on',
        
        // IntelliSense
        quickSuggestions: true,
        suggestOnTriggerCharacters: true,
        
        // Advanced features
        folding: true,  // Code folding
        wordWrap: 'on',
        mouseWheelZoom: true,
    });
    
    // 2. Connect to WebSocket
    // 3. Set up real-time sync
    // 4. Handle language changes
});
```

---

#### **Step 6: WebSocket Integration**

**Challenge:** Monaco uses a different model than textarea

**Solution:** Listen to Monaco's change events

```javascript
// Listen to content changes
editor.onDidChangeModelContent((event) => {
    if (isReceivingUpdate) return;  // Don't echo back received updates
    
    // Debounce sending
    clearTimeout(sendTimeout);
    sendTimeout = setTimeout(() => {
        const content = editor.getValue();
        ws.send(JSON.stringify({
            text: content,
            language: editor.getModel().getLanguageId()
        }));
    }, 300);
});

// Receive updates from WebSocket
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    isReceivingUpdate = true;
    
    // Update editor content
    editor.setValue(data.text);
    
    // Update language if changed
    if (data.language) {
        monaco.editor.setModelLanguage(editor.getModel(), data.language);
    }
    
    setTimeout(() => { isReceivingUpdate = false; }, 50);
};
```

---

#### **Step 7: Language Selector**

Add dropdown to switch programming languages:

**HTML:**
```html
<div class="toolbar">
    <select id="languageSelector">
        <option value="javascript">JavaScript</option>
        <option value="typescript">TypeScript</option>
        <option value="python">Python</option>
        <option value="java">Java</option>
        <option value="cpp">C++</option>
        <option value="csharp">C#</option>
        <option value="html">HTML</option>
        <option value="css">CSS</option>
        <option value="sql">SQL</option>
        <option value="go">Go</option>
        <option value="rust">Rust</option>
        <option value="php">PHP</option>
    </select>
</div>
```

**JavaScript:**
```javascript
document.getElementById('languageSelector').addEventListener('change', (e) => {
    const language = e.target.value;
    monaco.editor.setModelLanguage(editor.getModel(), language);
    
    // Broadcast language change
    ws.send(JSON.stringify({
        type: 'language_change',
        language: language
    }));
});
```

---

### **Phase 2C: Advanced Features** (30-60 min)

#### **Step 8: Theme Selector**

**Themes available:**
- `vs` - Light theme
- `vs-dark` - Dark theme (default in VS Code)
- `hc-black` - High contrast

**Implementation:**
```javascript
const themeSelector = document.getElementById('themeSelector');
themeSelector.addEventListener('change', (e) => {
    monaco.editor.setTheme(e.target.value);
    localStorage.setItem('monacoTheme', e.target.value);
});

// Restore saved theme
const savedTheme = localStorage.getItem('monacoTheme') || 'vs-dark';
monaco.editor.setTheme(savedTheme);
```

---

#### **Step 9: IntelliSense Configuration**

**For JavaScript/TypeScript:**
Monaco automatically provides IntelliSense for:
- Built-in JavaScript/TypeScript APIs
- DOM APIs
- Node.js APIs (if configured)

**For other languages:**
Need to configure language servers (advanced)

---

#### **Step 10: Cursor Position Preservation**

**Problem:** When receiving updates, cursor jumps to end

**Solution:** Preserve cursor position
```javascript
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // Save cursor position
    const position = editor.getPosition();
    const selection = editor.getSelection();
    
    isReceivingUpdate = true;
    
    // Update content
    editor.setValue(data.text);
    
    // Restore cursor
    if (position) {
        editor.setPosition(position);
    }
    if (selection) {
        editor.setSelection(selection);
    }
    
    setTimeout(() => { isReceivingUpdate = false; }, 50);
};
```

---

## 📁 **File Structure**

```
django_site3/
├── collab/
│   ├── static/
│   │   └── collab/
│   │       ├── monaco/                    # NEW - Monaco Editor files
│   │       │   └── vs/
│   │       │       ├── loader.js
│   │       │       ├── editor/
│   │       │       ├── base/
│   │       │       ├── basic-languages/
│   │       │       └── language/
│   │       └── js/
│   │           └── monaco-sync.js         # NEW - WebSocket sync logic
│   │
│   ├── templates/
│   │   └── collab/
│   │       ├── home.html
│   │       ├── room_simple.html           # Phase 1
│   │       ├── room_yjs.html              # Y.js version
│   │       └── room_monaco.html           # NEW - Phase 2 Monaco
│   │
│   ├── consumers.py                        # No changes needed
│   ├── views.py                            # Add collab_room_monaco()
│   └── urls.py                             # Add monaco route
│
└── PHASE_2_MONACO_IMPLEMENTATION_PLAN.md  # This file
```

---

## 🔧 **Technical Details**

### **Monaco Editor Initialization Options:**

```javascript
monaco.editor.create(container, {
    // Content
    value: '',                          // Initial text
    language: 'javascript',             // Programming language
    
    // Appearance
    theme: 'vs-dark',                   // Theme
    fontSize: 14,                       // Font size
    fontFamily: 'Consolas, monospace',  // Font
    lineHeight: 19,                     // Line height
    
    // Editor behavior
    automaticLayout: true,              // Auto-resize with container
    wordWrap: 'on',                     // Word wrapping
    lineNumbers: 'on',                  // Line numbers
    glyphMargin: true,                  // Gutter for breakpoints
    
    // Minimap
    minimap: {
        enabled: true,
        side: 'right',                  // 'left' or 'right'
        showSlider: 'mouseover',        // Always show or on hover
    },
    
    // IntelliSense
    quickSuggestions: true,             // Auto-suggest
    suggestOnTriggerCharacters: true,   // Trigger on . [ (
    acceptSuggestionOnEnter: 'on',      // Enter accepts
    tabCompletion: 'on',                // Tab accepts
    
    // Advanced
    folding: true,                      // Code folding
    foldingStrategy: 'indentation',     // How to fold
    multiCursorModifier: 'ctrlCmd',     // Ctrl/Cmd for multi-cursor
    mouseWheelZoom: true,               // Ctrl+wheel to zoom
    formatOnPaste: true,                // Auto-format
    formatOnType: true,                 // Format as you type
    
    // Scrolling
    scrollBeyondLastLine: false,        // Can't scroll past last line
    smoothScrolling: true,              // Smooth scrolling
    
    // Read-only mode (if needed)
    readOnly: false,                    // Set to true to disable editing
});
```

---

### **Supported Languages:**

**Built-in support for 50+ languages:**

| Category | Languages |
|----------|-----------|
| **Web** | JavaScript, TypeScript, HTML, CSS, SCSS, Less, JSON, XML |
| **Systems** | C, C++, C#, Go, Rust, Swift, Objective-C |
| **Scripts** | Python, Ruby, PHP, Perl, Lua, Shell, PowerShell, Batch |
| **JVM** | Java, Kotlin, Scala, Groovy |
| **Data** | SQL, GraphQL, YAML, TOML |
| **Functional** | F#, Haskell, Clojure, R |
| **Other** | Markdown, Dockerfile, Makefile, Redis, Solidity |

---

### **Monaco API - Key Methods:**

```javascript
// Get/Set Content
editor.getValue()                       // Get all text
editor.setValue('new content')          // Set all text

// Cursor & Selection
editor.getPosition()                    // Get cursor position
editor.setPosition({ lineNumber: 1, column: 1 })
editor.getSelection()                   // Get selected text
editor.setSelection(range)

// Language
const model = editor.getModel()
model.getLanguageId()                   // Get current language
monaco.editor.setModelLanguage(model, 'python')  // Change language

// Theme
monaco.editor.setTheme('vs-dark')

// Layout
editor.layout()                         // Force resize

// Focus
editor.focus()                          // Focus editor

// Events
editor.onDidChangeModelContent(callback)  // Content changed
editor.onDidChangeCursorPosition(callback)  // Cursor moved
editor.onDidChangeModel(callback)       // Model changed
```

---

## ⚠️ **Challenges & Solutions**

### **Challenge 1: Large Bundle Size**

**Problem:** Monaco is ~5MB, slow to load

**Solutions:**
1. **Lazy Loading:**
   ```javascript
   // Only load Monaco when user enters room
   require(['vs/editor/editor.main'], function() {
       // Initialize here
   });
   ```

2. **Gzip Compression:**
   Configure Django to serve Monaco files with gzip:
   ```python
   # settings.py
   MIDDLEWARE = [
       'django.middleware.gzip.GZipMiddleware',  # Add this
       # ... other middleware
   ]
   ```

3. **CDN Fallback:**
   ```html
   <!-- Try CDN first, fallback to local -->
   <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js"
           onerror="this.src='{% static "collab/monaco/vs/loader.js" %}'">
   </script>
   ```

---

### **Challenge 2: Cursor Position on Updates**

**Problem:** Cursor jumps when receiving remote updates

**Solution:** Use operational transformation or delta updates

**Simple Approach:**
```javascript
// Only update if content actually changed
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (editor.getValue() !== data.text) {
        const position = editor.getPosition();
        isReceivingUpdate = true;
        editor.setValue(data.text);
        editor.setPosition(position);
        setTimeout(() => { isReceivingUpdate = false; }, 50);
    }
};
```

**Advanced Approach (Y.js):**
```javascript
// Use y-monaco for CRDT-based sync
import * as Y from 'yjs'
import { MonacoBinding } from 'y-monaco'

const ydoc = new Y.Doc()
const ytext = ydoc.getText('monaco')
const binding = new MonacoBinding(ytext, editor.getModel())
```

---

### **Challenge 3: Language Synchronization**

**Problem:** Users may have different languages selected

**Solution:** Broadcast language changes

```javascript
// Backend stores room language
// consumers.py - extend to handle language
class CollaborationConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data=None):
        data = json.loads(text_data)
        
        if data.get('type') == 'language_change':
            # Save to room
            await self.save_language(data['language'])
        
        # Broadcast to all
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'collaboration_message', 'text_data': text_data}
        )
```

---

### **Challenge 4: IntelliSense in Collaborative Mode**

**Problem:** IntelliSense suggestions may conflict with incoming updates

**Solution:**
- Disable IntelliSense temporarily while receiving
- Or use Y.js with proper CRDT integration

```javascript
let receivingUpdate = false;

const editor = monaco.editor.create(container, {
    quickSuggestions: {
        other: () => !receivingUpdate,
        comments: false,
        strings: false
    }
});
```

---

### **Challenge 5: Performance with Large Files**

**Problem:** Monaco can be slow with files >10,000 lines

**Solutions:**
1. Warn users about large files
2. Implement chunked loading
3. Use Monaco's built-in virtualization (it handles this)

```javascript
// Add file size warning
if (content.split('\n').length > 5000) {
    console.warn('Large file detected, performance may be affected');
}
```

---

## 💻 **Complete Code Example**

### **room_monaco.html** (Simplified)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Monaco Editor - Room {{ room_name }}</title>
    {% load static %}
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; height: 100vh; }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .toolbar {
            background: #2d2d30;
            color: white;
            padding: 10px 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .toolbar select {
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #555;
            background: #3c3c3c;
            color: white;
        }
        
        #editor-container {
            flex: 1;
            overflow: hidden;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4ade80;
        }
        
        .status-dot.disconnected {
            background: #ef4444;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div>
            <h1>🚀 Monaco Editor - Room: {{ room_name }}</h1>
        </div>
        <div class="status">
            <span class="status-dot" id="statusDot"></span>
            <span id="statusText">Connecting...</span>
        </div>
    </div>
    
    <!-- Toolbar -->
    <div class="toolbar">
        <label>Language:</label>
        <select id="languageSelector">
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="csharp">C#</option>
            <option value="html">HTML</option>
            <option value="css">CSS</option>
        </select>
        
        <label>Theme:</label>
        <select id="themeSelector">
            <option value="vs-dark">Dark</option>
            <option value="vs">Light</option>
            <option value="hc-black">High Contrast</option>
        </select>
        
        <span style="margin-left: auto;">
            👤 {{ username }}
        </span>
    </div>
    
    <!-- Monaco Editor Container -->
    <div id="editor-container"></div>
    
    <!-- Monaco Loader -->
    <script src="{% static 'collab/monaco/vs/loader.js' %}"></script>
    <script>
        const roomName = '{{ room_name }}';
        
        // Configure Monaco loader
        require.config({ 
            paths: { 
                vs: '{% static "collab/monaco/vs" %}'.replace(/\/?$/, '')
            }
        });
        
        // Load Monaco Editor
        require(['vs/editor/editor.main'], function() {
            console.log('✓ Monaco Editor loaded');
            
            // Create editor instance
            const editor = monaco.editor.create(document.getElementById('editor-container'), {
                value: '// Welcome to Monaco Editor!\n// Start coding...\n',
                language: 'javascript',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: true },
                quickSuggestions: true,
                folding: true,
                lineNumbers: 'on',
                wordWrap: 'on',
                mouseWheelZoom: true,
            });
            
            console.log('✓ Editor created');
            
            // WebSocket setup
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/collab/${roomName}/`;
            let ws = null;
            let isReceivingUpdate = false;
            let sendTimeout = null;
            
            function connect() {
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    console.log('✓ WebSocket connected');
                    document.getElementById('statusDot').classList.remove('disconnected');
                    document.getElementById('statusText').textContent = 'Connected';
                };
                
                ws.onclose = () => {
                    console.log('✗ WebSocket disconnected');
                    document.getElementById('statusDot').classList.add('disconnected');
                    document.getElementById('statusText').textContent = 'Reconnecting...';
                    setTimeout(connect, 2000);
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    // Don't update if we're the sender
                    if (isReceivingUpdate) return;
                    
                    isReceivingUpdate = true;
                    
                    // Save cursor position
                    const position = editor.getPosition();
                    const selection = editor.getSelection();
                    
                    // Update content
                    if (data.text !== undefined && data.text !== editor.getValue()) {
                        editor.setValue(data.text);
                        
                        // Restore cursor
                        if (position) editor.setPosition(position);
                        if (selection) editor.setSelection(selection);
                    }
                    
                    // Update language
                    if (data.language) {
                        monaco.editor.setModelLanguage(editor.getModel(), data.language);
                        document.getElementById('languageSelector').value = data.language;
                    }
                    
                    setTimeout(() => { isReceivingUpdate = false; }, 50);
                };
            }
            
            // Listen for content changes
            editor.onDidChangeModelContent((event) => {
                if (isReceivingUpdate) return;
                
                clearTimeout(sendTimeout);
                sendTimeout = setTimeout(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            text: editor.getValue(),
                            language: editor.getModel().getLanguageId()
                        }));
                        console.log('✓ Sent update');
                    }
                }, 300);
            });
            
            // Language selector
            document.getElementById('languageSelector').addEventListener('change', (e) => {
                const language = e.target.value;
                monaco.editor.setModelLanguage(editor.getModel(), language);
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        language: language,
                        text: editor.getValue()
                    }));
                }
            });
            
            // Theme selector
            document.getElementById('themeSelector').addEventListener('change', (e) => {
                monaco.editor.setTheme(e.target.value);
                localStorage.setItem('monacoTheme', e.target.value);
            });
            
            // Restore saved theme
            const savedTheme = localStorage.getItem('monacoTheme');
            if (savedTheme) {
                monaco.editor.setTheme(savedTheme);
                document.getElementById('themeSelector').value = savedTheme;
            }
            
            // Connect WebSocket
            connect();
            
            // Cleanup
            window.addEventListener('beforeunload', () => {
                if (ws) ws.close();
                editor.dispose();
            });
        });
    </script>
</body>
</html>
```

---

## 🧪 **Testing Plan**

### **Test Cases:**

1. **Basic Functionality:**
   - [ ] Editor loads correctly
   - [ ] Can type and edit code
   - [ ] Syntax highlighting works
   - [ ] Line numbers visible
   - [ ] Minimap displays

2. **Collaboration:**
   - [ ] Two users can connect to same room
   - [ ] Changes sync in real-time
   - [ ] Cursor position maintained
   - [ ] Language changes sync
   - [ ] No race conditions

3. **Language Support:**
   - [ ] JavaScript highlighting works
   - [ ] Python highlighting works
   - [ ] Language selector changes syntax
   - [ ] IntelliSense appears (for JS/TS)

4. **UI/UX:**
   - [ ] Theme selector works
   - [ ] Theme preference saved
   - [ ] Responsive on different screens
   - [ ] Connection status accurate

5. **Performance:**
   - [ ] Loads within 3 seconds
   - [ ] No lag when typing
   - [ ] Works with 1000+ line files
   - [ ] Multiple users don't slow down

---

## 🎯 **Step-by-Step Implementation Checklist**

### **Preparation:**
- [ ] Read Monaco Editor documentation
- [ ] Understand AMD module loading
- [ ] Review current WebSocket implementation

### **Phase 2A: Setup (1 hour)**
- [ ] Download Monaco Editor (~5MB)
- [ ] Create `collab/static/collab/monaco/` directory
- [ ] Extract Monaco files to static folder
- [ ] Test static file serving
- [ ] Create `room_monaco.html` template
- [ ] Add URL route in `urls.py`
- [ ] Add view function in `views.py`
- [ ] Test Monaco loads (even without WebSocket)

### **Phase 2B: Integration (1 hour)**
- [ ] Add WebSocket connection code
- [ ] Implement content sync (send on change)
- [ ] Implement content sync (receive updates)
- [ ] Add cursor position preservation
- [ ] Test with 2 browser tabs
- [ ] Add language selector
- [ ] Sync language changes
- [ ] Test language switching

### **Phase 2C: Polish (30-60 min)**
- [ ] Add theme selector
- [ ] Save theme preference
- [ ] Add connection status indicator
- [ ] Improve UI/styling
- [ ] Add error handling
- [ ] Test reconnection logic
- [ ] Add loading indicator
- [ ] Mobile responsiveness check

### **Testing:**
- [ ] Test all languages (5-10 languages)
- [ ] Test with large files (1000+ lines)
- [ ] Test with 3+ concurrent users
- [ ] Test connection drop/reconnect
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Mobile testing
- [ ] Performance profiling

### **Documentation:**
- [ ] Update README with Monaco setup
- [ ] Document Monaco-specific features
- [ ] Create user guide
- [ ] Document limitations

---

## 🔮 **Future Enhancements**

### **Phase 3: Advanced Monaco Features**

1. **Multi-File Support:**
   ```javascript
   // Switch between multiple files in same room
   const models = {
       'index.js': monaco.editor.createModel('', 'javascript'),
       'styles.css': monaco.editor.createModel('', 'css'),
       'index.html': monaco.editor.createModel('', 'html'),
   };
   
   editor.setModel(models['index.js']);
   ```

2. **Diff Editor:**
   ```javascript
   // Show changes between versions
   const diffEditor = monaco.editor.createDiffEditor(container);
   diffEditor.setModel({
       original: originalModel,
       modified: modifiedModel
   });
   ```

3. **Custom Commands:**
   ```javascript
   // Add custom keyboard shortcuts
   editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
       // Custom save logic
       saveDocument();
   });
   ```

4. **User Cursors (CRDT):**
   ```javascript
   // Show where other users are typing
   // Requires Y.js integration with y-monaco
   import { MonacoBinding } from 'y-monaco'
   
   const binding = new MonacoBinding(
       ytext,
       editor.getModel(),
       new Set([editor]),
       provider.awareness  // Shows remote cursors
   );
   ```

5. **Code Execution:**
   ```javascript
   // Run code directly in browser
   document.getElementById('runButton').addEventListener('click', () => {
       const code = editor.getValue();
       try {
           eval(code);  // For JavaScript (unsafe, needs sandboxing)
       } catch (e) {
           console.error(e);
       }
   });
   ```

6. **Linting Integration:**
   ```javascript
   // Show real-time linting errors
   monaco.languages.registerCodeActionProvider('javascript', {
       provideCodeActions: function(model, range, context, token) {
           // Return code fixes
       }
   });
   ```

---

## 📊 **Comparison: Simple Sync vs Y.js with Monaco**

| Feature | Simple Sync (Phase 2) | Y.js CRDT (Phase 4) |
|---------|----------------------|---------------------|
| **Setup Complexity** | Medium | Hard |
| **Cursor Preservation** | Manual (tricky) | Automatic |
| **Simultaneous Edits** | Last-write-wins | Merges perfectly |
| **Remote Cursors** | Not supported | ✅ Shows others' cursors |
| **Offline Support** | ❌ No | ✅ Yes |
| **Bandwidth** | Higher (full text) | Lower (diffs only) |
| **Conflict Resolution** | Overwrites | CRDT merge |

**Recommendation:** Start with Simple Sync (Phase 2), upgrade to Y.js (Phase 4) if needed.

---

## 🎓 **Learning Resources**

### **Monaco Editor:**
- Official Docs: https://microsoft.github.io/monaco-editor/
- API Reference: https://microsoft.github.io/monaco-editor/api/index.html
- Playground: https://microsoft.github.io/monaco-editor/playground.html
- GitHub: https://github.com/microsoft/monaco-editor

### **Y.js with Monaco:**
- y-monaco: https://github.com/yjs/y-monaco
- Y.js Docs: https://docs.yjs.dev/
- Examples: https://github.com/yjs/yjs-demos

### **Monaco Examples:**
- Basic Usage: https://github.com/microsoft/monaco-editor-samples
- Advanced: https://github.com/microsoft/vscode (VS Code source)

---

## 🎯 **Timeline Estimate**

| Phase | Time | Tasks |
|-------|------|-------|
| **Download & Setup** | 30 min | Download Monaco, organize files, test serving |
| **Basic Integration** | 1 hour | Create template, initialize editor, basic styling |
| **WebSocket Sync** | 1 hour | Connect WebSocket, send/receive, handle updates |
| **Language/Theme** | 30 min | Add selectors, sync language changes |
| **Polish & Testing** | 30 min | Error handling, reconnection, cross-browser test |
| **Total** | **3-3.5 hours** | Full Monaco implementation |

---

## ✅ **Success Criteria**

**Phase 2 is complete when:**
- ✅ Monaco Editor loads and displays properly
- ✅ Can type code with syntax highlighting
- ✅ Changes sync between 2+ users in real-time
- ✅ Language selector works and syncs
- ✅ Theme selector works
- ✅ Connection status indicator accurate
- ✅ No major bugs or crashes
- ✅ Performance acceptable (<3s load time)

---

## 🚀 **Getting Started**

**Ready to implement?** Here's what to do:

1. **Download Monaco:**
   ```bash
   # Visit: https://github.com/microsoft/monaco-editor/releases
   # Download latest release (e.g., monaco-editor-0.44.0.zip)
   # Extract to: collab/static/collab/monaco/
   ```

2. **Test Static Files:**
   ```bash
   python manage.py collectstatic --noinput
   python manage.py runserver
   # Visit: http://127.0.0.1:8000/static/collab/monaco/vs/loader.js
   # Should download the file
   ```

3. **Create Template:**
   - Copy the complete code example above
   - Save as `collab/templates/collab/room_monaco.html`

4. **Add Route & View:**
   - Update `urls.py` and `views.py` as shown
   - Test route works

5. **Test:**
   - Visit: `http://127.0.0.1:8000/collab/room-monaco/test/`
   - Should see Monaco editor
   - Open in 2 tabs, test sync

---

**Good luck with Phase 2! Monaco Editor will give you a professional, VS Code-like experience! 🚀**

*Document created: October 8, 2025*  
*Project: Django Site - Phase 2 Monaco Implementation*  
*Estimated completion time: 3-3.5 hours*

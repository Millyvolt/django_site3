# Collaborative Editor Planning Guide

## Overview
This document contains planning and architectural discussions for implementing a collaborative (coworking) editor system for the Django site, with support for both code/plain text editing and Microsoft Office documents.

---

## Table of Contents
1. [Code/Plain Text Collaborative Editor](#codeплain-text-collaborative-editor)
2. [Microsoft Office Format Support](#microsoft-office-format-support)
3. [Y.js vs Third-Party Services](#yjs-vs-third-party-services)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Technical Stack Summary](#technical-stack-summary)

---

## Code/Plain Text Collaborative Editor

### Architecture Overview

#### Core Technology Stack

**WebSocket Layer:**
- **Django Channels** - Adds WebSocket support to Django (extends ASGI)
- **Redis** (or in-memory layer) - Message broker for handling multiple connections
- **Channel Layers** - Enables communication between different WebSocket consumers

**Operational Transformation (OT) or CRDT:**
- **Y.js** - A CRDT library that handles conflict-free collaborative editing (RECOMMENDED)
- **ShareDB** - Real-time database with OT built-in
- Custom Operational Transformation implementations

### System Components

**Backend (Django):**
- **WebSocket Consumers** - Handle connections, receive/broadcast changes
- **Room/Session Management** - Track which users are in which editing sessions
- **User Presence** - Show active users (cursors, selections, online status)
- **Document Versioning** - Store document states and history
- **Permissions System** - Handle private/public rooms, ownership, access control

**Frontend (JavaScript):**
- **CodeMirror with collaborative extensions** or **Monaco Editor**
- **WebSocket client** - Maintain persistent connection to server
- **Change detection & transformation** - Capture local edits, apply remote edits
- **Cursor tracking** - Display other users' cursors and selections
- **Presence indicators** - User avatars, activity status
- **Conflict resolution UI** - Handle edge cases visually

### Data Flow Architecture

```
User A types → Local editor updates → Generate change operation → 
Send via WebSocket → Django Channels Consumer → Broadcast to room → 
Other users receive → Transform operation → Apply to their editors
```

### Key Technical Challenges

**Synchronization Issues:**
- **Race conditions** - Two users edit same text simultaneously
- **Network latency** - Operations arrive out of order
- **Reconnection** - User loses connection and needs to sync state

**Solutions:**
- **Operational Transformation (OT)** - Transform operations based on concurrent changes
- **Conflict-free Replicated Data Types (CRDT)** - Mathematically guarantee convergence
- **Vector clocks / Lamport timestamps** - Determine operation ordering
- **Acknowledgment system** - Confirm operations received/applied

### Database Schema Needs

**Models to Create:**
- `CollaborativeSession` - Room/document metadata
- `SessionParticipant` - Track who's in which session
- `DocumentVersion` - Snapshot history for recovery
- `Operation` - Log of all changes (for debugging/replay)
- `SessionPermission` - Access control (view/edit/admin)

### Feature Set

**Core Features:**
- Real-time text synchronization
- Multi-user cursor/selection display
- User presence indicators
- Auto-save and conflict resolution

**Enhanced Features:**
- Chat sidebar within editor
- Code execution in collaborative mode
- Session recording/replay
- Branching/forking sessions
- Code review annotations
- Time-travel debugging (view history)

### Security Considerations

- **Authentication** - Only logged-in users can create/join sessions
- **Authorization** - Room owners control access
- **Rate limiting** - Prevent spam/abuse via WebSocket
- **Input validation** - Sanitize all operations
- **Session encryption** - Protect sensitive code
- **Audit logs** - Track who changed what

### Scalability Considerations

- **Horizontal scaling** - Use Redis Cluster for channel layer
- **Session sharding** - Distribute rooms across servers
- **Connection pooling** - Manage WebSocket connections efficiently
- **Caching** - Store document state in Redis
- **CDN** - Serve static assets (CodeMirror libraries)

---

## Microsoft Office Format Support

### File Format Types

**Modern Office Formats (Office 2007+):**
- `.docx` - Word documents (OpenXML format, essentially zipped XML)
- `.xlsx` - Excel spreadsheets (OpenXML format)
- `.pptx` - PowerPoint presentations (OpenXML format)

**Legacy Formats (Office 97-2003):**
- `.doc` - Word (binary format, harder to parse)
- `.xls` - Excel (binary format)
- `.ppt` - PowerPoint (binary format)

### Python Libraries

**For Word Documents:**
- `python-docx` - Read/write .docx files (most popular, well-maintained)
- `python-docx2txt` - Extract text from .docx
- `docx2pdf` - Convert to PDF
- `mammoth` - Convert .docx to HTML (preserves styling better)

**For Excel Spreadsheets:**
- `openpyxl` - Read/write .xlsx files (most comprehensive)
- `xlsxwriter` - Write-only, faster for large files
- `pandas` - Read Excel with data manipulation (uses openpyxl)
- `xlrd` / `xlwt` - Legacy .xls support
- `pyexcel` - Unified API for multiple formats

**For PowerPoint Presentations:**
- `python-pptx` - Read/write .pptx files (official library)

**Legacy Binary Formats:**
- `pywin32` - Windows only, uses COM automation (requires Office installed)
- `antiword` - .doc to text (command-line tool)
- `olefile` - Read binary Office formats

**Universal/Conversion:**
- `LibreOffice` (headless) - Convert any Office format via command line
- `unoconv` - Python wrapper for LibreOffice conversion
- `pypandoc` - Universal document converter (uses Pandoc)

### Feature Capabilities

**python-docx (Word):**
- ✅ Read/write paragraphs, runs, styles
- ✅ Tables, images, headers/footers
- ✅ Character/paragraph formatting (bold, italic, fonts)
- ❌ Complex layouts (text boxes, shapes)
- ❌ Track changes, comments
- ⚠️ Limited: equations, SmartArt

**openpyxl (Excel):**
- ✅ Read/write cells, formulas, formatting
- ✅ Charts, images, pivot tables (limited)
- ✅ Multiple sheets, named ranges
- ✅ Conditional formatting, data validation
- ❌ Macros (VBA code)
- ⚠️ Limited: complex charts, slicers

**python-pptx (PowerPoint):**
- ✅ Read/write slides, shapes, text
- ✅ Images, tables, charts
- ✅ Layout templates, themes
- ❌ Animations, transitions
- ❌ Embedded media (video/audio)
- ⚠️ Limited: SmartArt, complex graphics

### Collaborative Editing Challenges

**Major Issues:**

**Binary/Complex Structure:**
- Office files aren't plain text - can't apply simple OT/CRDT
- Changes affect XML structure, not just content
- Formatting metadata is complex

**Granularity:**
- Define "operation" unit: character, word, paragraph, cell?
- Cell formulas in Excel depend on other cells
- Slide order matters in PowerPoint

**Conflict Types:**
- Formatting conflicts (both users change font of same text)
- Structural conflicts (delete table row others are editing)
- Formula conflicts (circular dependencies)

### Architecture Approaches for Office Documents

**Approach A: View-Only (Easiest)**
- Convert Office files to PDF/HTML for viewing
- Users download original for editing
- No real-time collaboration
- **Libraries**: `unoconv`, `mammoth`, `pypandoc`

**Approach B: Text-Only Extraction**
- Extract text content for collaborative editing
- Lose all formatting
- Save back as plain text or simple format
- **Libraries**: `python-docx2txt`, `openpyxl` (values only)

**Approach C: Limited Collaborative Editing**
- Support specific features (e.g., spreadsheet cells only)
- Ignore advanced features
- Simpler conflict resolution
- **Best for**: Excel with cell-level locking

**Approach D: Full Collaborative Editing (Complex)**
- Parse Office file to internal structure
- Apply OT/CRDT at structural level
- Reconstruct Office file from structure
- **Like**: Google Docs/Sheets approach
- **Effort**: Very high, requires deep expertise

**Approach E: Use Third-Party Service**
- Microsoft Office Online (requires license)
- OnlyOffice (open-source, self-hosted)
- Collabora Online (LibreOffice-based)
- Google Workspace APIs

### Recommended Workflow Examples

**For Word Documents:**
1. User uploads .docx
2. Backend converts to HTML using `mammoth`
3. Store HTML in database
4. Use rich text editor (Quill) for collaborative editing
5. On export: Convert HTML back to .docx (lossy but functional)

**For Excel Spreadsheets:**
1. User uploads .xlsx
2. Backend parses to JSON using `openpyxl`
3. Store cell data in database or Redis
4. Use Handsontable/Luckysheet for editing
5. Real-time sync via WebSockets (easier than Word)
6. Export back to .xlsx using `openpyxl`

**For PowerPoint:**
1. User uploads .pptx
2. Backend extracts slides as images/HTML
3. Store slide structure in database
4. View-only mode (simplest)
5. Or: Decompose to editable elements
6. Rebuild .pptx on export

### Frontend Components for Office Support

**For Word-like Editing:**
- **Quill Editor** - WYSIWYG with Office-like toolbar
- **TinyMCE** - Feature-rich, Office-like
- **ProseMirror** - Structured editing with collaboration
- **Slate.js** - Customizable React editor

**For Spreadsheets:**
- **Handsontable** - Excel-like grid (commercial license for full features)
- **Luckysheet** - Open-source, Excel-like (Chinese origin)
- **jExcel/jSpreadsheet** - Lightweight grid
- **ag-Grid** - Enterprise grid (commercial)

**For Presentations:**
- **Reveal.js** - HTML presentations
- **Impress.js** - 3D presentations
- Custom canvas/SVG renderer

### Self-Hosted Office Solutions

- **OnlyOffice Document Server** - Full Office suite, WebSocket-based
- **Collabora Online** - LibreOffice-based, feature-complete
- **Etherpad** - Real-time text (not Office, but collaborative)

---

## Y.js vs Third-Party Services

### Three Main Approaches Explained

#### Approach A: Build with Y.js (RECOMMENDED)

**What Y.js Does FOR You:**
- ✅ Handles all CRDT conflict resolution automatically
- ✅ Manages synchronization logic
- ✅ Provides peer-to-peer or client-server communication
- ✅ Supports offline editing and reconnection
- ✅ Works with CodeMirror, Monaco, Quill, ProseMirror out-of-the-box
- ✅ Battle-tested by major companies

**What YOU Still Need to Build:**
1. **WebSocket Server** (Django Channels)
   - Accept connections
   - Route messages between clients
   - Handle authentication

2. **Y.js Integration** (Frontend + Backend)
   - Connect Y.js to your WebSocket
   - Bind Y.js to CodeMirror
   - Set up Y.js awareness (cursors, presence)

3. **Room/Session Management**
   - Create/join collaborative sessions
   - Permissions (who can access)
   - Store session state

4. **UI/UX Features**
   - User list display
   - Cursor colors and labels
   - Session controls (share link, lock/unlock)

5. **Persistence** (Optional)
   - Save document state to database
   - Load existing documents into Y.js

**Complexity: Medium** (Much easier than custom OT!)

**Architecture with Y.js:**
```
Frontend (Browser):
├── CodeMirror Editor
├── Y.js CRDT Document
├── y-codemirror (binding)
├── y-websocket (provider)
└── WebSocket Client

Backend (Django):
├── Django Channels
├── WebSocket Consumer
├── y-py (Python Y.js adapter) [OPTIONAL]
├── Redis (channel layer)
└── Database (persistence) [OPTIONAL]
```

**Workflow:**
1. User opens editor page
2. Frontend creates Y.js document
3. Connects to Django WebSocket (with session ID)
4. Django broadcasts messages between connected users
5. Y.js handles merging changes automatically
6. Cursors/selections shared via Y.js awareness protocol

**Cost:** Free (open-source), you host it
**Control:** Full control over data and infrastructure
**Scaling:** You manage (but Y.js is efficient)
**Effort:** Medium (2-4 weeks for MVP)

---

#### Approach B: Fully Managed Third-Party Services

**Examples:**
- **Liveblocks** - Commercial service, real-time collaboration API
- **Convergence** - Real-time collaboration platform (was open-source, now limited)
- **PubNub** - Real-time messaging with collaborative editing features
- **Ably** - Real-time messaging platform
- **Firebase Realtime Database** - Google's real-time sync
- **CodeSandbox API** - If specifically for code
- **Firepad** - Google's library (discontinued but still usable)

**What They Do FOR You:**
- ✅ Host all infrastructure (no server setup)
- ✅ Handle scaling automatically
- ✅ Provide APIs/SDKs
- ✅ Manage WebSocket connections
- ✅ Built-in presence and awareness
- ✅ Usually have admin dashboards

**What YOU Still Need to Build:**
1. Frontend integration with their SDK
2. Your UI around their components
3. User authentication (integrate with your Django auth)
4. Pay for usage (usually)

**Architecture with Third-Party:**
```
Frontend (Browser):
├── CodeMirror Editor
├── Liveblocks Client SDK
├── Liveblocks-CodeMirror binding
└── WebSocket to Liveblocks servers (not yours)

Backend (Django):
├── Minimal: Just generate auth tokens
└── API calls to Liveblocks for room management
```

**Cost:** Paid (typically $0-99/month starter, scales with usage)
**Control:** Limited (data goes through their servers)
**Scaling:** Automatic (they handle it)
**Effort:** Low (1-2 weeks for MVP)

---

#### Approach C: Full Custom Implementation (NOT RECOMMENDED)

**You Build Everything:**
- Custom Operational Transformation algorithm
- WebSocket infrastructure
- Conflict resolution logic
- State synchronization
- Reconnection handling
- All the edge cases

**Complexity: Very High** (Not recommended unless you have specific needs)
**Effort:** 3-6 months for production-ready system

---

### Comparison Table

| Feature | Y.js (Self-hosted) | Third-Party Service | Custom OT |
|---------|-------------------|---------------------|-----------|
| **Initial Effort** | Medium (2-3 weeks) | Low (1 week) | Very High (3-6 months) |
| **Cost** | Server hosting only | $50-500+/month | Server hosting only |
| **Control** | Full | Limited | Full |
| **Scalability** | You manage | Automatic | You manage |
| **Offline Support** | ✅ Yes | ⚠️ Varies | ✅ Possible |
| **Data Privacy** | ✅ Your servers | ⚠️ Their servers | ✅ Your servers |
| **Customization** | ✅ High | ⚠️ Limited | ✅ Unlimited |
| **Maintenance** | You update | They handle | You maintain |
| **Learning Curve** | Medium | Low | Very High |
| **Production Ready** | ✅ Yes | ✅ Yes | ⚠️ Need extensive testing |

---

## Implementation Roadmap

### Recommended Approach: Y.js with Django Channels

**Why Y.js:**
1. **Existing infrastructure** - Uvicorn/ASGI already configured
2. **Free and open-source** - No recurring costs
3. **Full control** - Data stays on your servers
4. **Better learning** - Understand how collaboration works
5. **More flexible** - Customize everything
6. **Production-ready** - Used by major products (Linear, Notion-like apps)

### Simplified Phases with Y.js

#### Phase 1: Basic Y.js Setup (1-2 days)
- Install Django Channels
- Create WebSocket consumer
- Install Y.js on frontend
- Connect Y.js to WebSocket
- Basic text sync works

**What Django Does:**
```python
# Simple WebSocket relay
class CollaborationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authenticate user
        # Join room group
        
    async def receive(self, bytes_data):
        # Forward Y.js messages to room
        
    async def disconnect(self):
        # Remove from room
```

**That's it!** Django just relays messages. Y.js does all the hard work.

#### Phase 2: CodeMirror Integration (1-2 days)
- Bind Y.js to your existing CodeMirror editor
- Test multi-user text editing
- Handle reconnection

#### Phase 3: User Presence (2-3 days)
- Implement Y.js awareness protocol
- Show user cursors with colors
- Display user list with names/avatars
- Show who's typing

#### Phase 4: Room Management (3-5 days)
- Create/join session endpoints
- Session permissions (private/public)
- Share session links
- Session list for user

#### Phase 5: Persistence & Polish (3-5 days)
- Save Y.js document state to database
- Load existing documents
- History/versioning
- UI improvements

**Total: 2-3 weeks for fully featured system**

---

## Technical Stack Summary

### Dependencies to Add

**Python (requirements.txt):**
```
# Collaborative Editor - Code/Plain Text
channels==4.0.0
channels-redis==4.1.0
redis==5.0.1
daphne==4.0.0  # Alternative ASGI server

# Office Document Support (Phase 2)
python-docx==0.8.11
openpyxl==3.1.2
python-pptx==0.6.21
mammoth==1.6.0
pandas==2.2.0
Pillow==10.2.0
celery==5.3.4  # Background tasks for conversion
```

**Frontend (JavaScript via npm or CDN):**
```javascript
// Y.js for collaborative editing
yjs
y-websocket
y-codemirror  // or y-codemirror.next for CodeMirror 6

// Already have: CodeMirror 5

// For Office documents (future):
// - Quill or TinyMCE (rich text)
// - Handsontable or Luckysheet (spreadsheet)
```

**System Dependencies (for Office support):**
```bash
# LibreOffice (for conversions)
libreoffice-headless

# Pandoc (universal converter)
pandoc
```

### Integration with Current System

**Existing Assets to Leverage:**
- Your CodeMirror setup in `editor.html`
- User authentication system
- ASGI/Uvicorn already configured
- Profile system for user avatars/names

---

## Summary & Recommendations

### For Code/Plain Text Editor:
✅ **Use Y.js with Django Channels**
- Best balance of control and ease
- Free and open-source
- 2-3 weeks implementation time
- Full control over data and infrastructure

### For Office Documents:
✅ **Start Simple, Then Expand**
1. **Phase 1**: View-only (convert to PDF/HTML)
2. **Phase 2**: Excel collaborative editing (easiest to implement)
3. **Phase 3**: Word as rich text (lose some formatting)
4. **Consider**: OnlyOffice integration for full Office support

### Development Strategy:
1. **Implement code editor first** (higher value, easier)
2. **Add basic Office viewing** (upload, convert, download)
3. **Add Excel collaboration** (good ROI for effort)
4. **Consider full Office** (evaluate if needed based on usage)

---

## Next Steps (When Ready to Code)

1. Install Django Channels + Redis
2. Create basic WebSocket consumer
3. Add Y.js to frontend
4. Connect them together
5. Test with 2 browser windows
6. Add user presence (cursors)
7. Add room management
8. Polish UI

---

## Additional Resources

### Y.js Documentation:
- Official docs: https://docs.yjs.dev/
- Examples: https://github.com/yjs/yjs-demos

### Django Channels:
- Official docs: https://channels.readthedocs.io/
- Tutorial: https://channels.readthedocs.io/en/stable/tutorial/

### Alternative Solutions:
- OnlyOffice: https://www.onlyoffice.com/developer-edition.aspx
- Collabora Online: https://www.collaboraoffice.com/code/
- Liveblocks: https://liveblocks.io/

---

*Document created: October 7, 2025*
*Project: Django Site - Collaborative Editor Planning*


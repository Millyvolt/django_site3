/**
 * Minimal Y.js-like CRDT implementation for collaborative text editing
 * Provides basic conflict-free replicated data type functionality
 */

class YText {
    constructor() {
        this.items = [];
        this.length = 0;
    }

    insert(index, text) {
        if (text.length === 0) return;
        
        const item = {
            id: this.generateId(),
            content: text,
            length: text.length,
            index: index
        };
        
        this.items.push(item);
        this.items.sort((a, b) => a.index - b.index);
        this.length += text.length;
    }

    delete(index, length) {
        if (length <= 0) return;
        
        // Remove items that overlap with the deletion range
        this.items = this.items.filter(item => {
            const itemEnd = item.index + item.length;
            const deleteEnd = index + length;
            
            // If item is completely within deletion range, remove it
            if (item.index >= index && itemEnd <= deleteEnd) {
                this.length -= item.length;
                return false;
            }
            
            // If item overlaps with deletion range, truncate it
            if (item.index < deleteEnd && itemEnd > index) {
                if (item.index < index) {
                    // Truncate from the end
                    const newLength = index - item.index;
                    item.content = item.content.substring(0, newLength);
                    item.length = newLength;
                    this.length -= (item.length - newLength);
                } else {
                    // Truncate from the beginning
                    const startOffset = deleteEnd - item.index;
                    item.content = item.content.substring(startOffset);
                    item.index = deleteEnd;
                    item.length = item.content.length;
                    this.length -= startOffset;
                }
            }
            
            return true;
        });
    }

    toString() {
        return this.items
            .sort((a, b) => a.index - b.index)
            .map(item => item.content)
            .join('');
    }

    applyUpdate(update) {
        try {
            const operations = JSON.parse(update);
            for (const op of operations) {
                if (op.type === 'insert') {
                    this.insert(op.index, op.content);
                } else if (op.type === 'delete') {
                    this.delete(op.index, op.length);
                }
            }
        } catch (e) {
            console.error('Failed to apply update:', e);
        }
    }

    getUpdate() {
        const operations = this.items.map(item => ({
            type: 'insert',
            index: item.index,
            content: item.content
        }));
        return JSON.stringify(operations);
    }

    generateId() {
        return Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

class YDoc {
    constructor() {
        this.texts = new Map();
    }

    getText(name) {
        if (!this.texts.has(name)) {
            this.texts.set(name, new YText());
        }
        return this.texts.get(name);
    }

    transact(callback) {
        callback();
    }
}

// Global Y object
window.Y = {
    Doc: YDoc,
    Text: YText
};

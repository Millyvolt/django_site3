/**
 * Workout Sync Manager
 * Handles background sync and request queuing for offline support
 */

class WorkoutSync {
    constructor() {
        this.queueKey = 'workout:sync:queue';
        this.syncing = false;
        this.retryDelay = 5000; // 5 seconds
        this.maxRetries = 3;
    }

    /**
     * Get sync queue
     */
    _getQueue() {
        try {
            const queue = localStorage.getItem(this.queueKey);
            return queue ? JSON.parse(queue) : [];
        } catch (e) {
            console.error('Sync queue get error:', e);
            return [];
        }
    }

    /**
     * Save sync queue
     */
    _saveQueue(queue) {
        try {
            localStorage.setItem(this.queueKey, JSON.stringify(queue));
            return true;
        } catch (e) {
            console.error('Sync queue save error:', e);
            return false;
        }
    }

    /**
     * Add request to sync queue
     */
    queueRequest(method, url, data, options = {}) {
        const request = {
            id: this._generateId(),
            method: method,
            url: url,
            data: data,
            options: options,
            timestamp: Date.now(),
            retries: 0,
            status: 'pending'
        };

        const queue = this._getQueue();
        queue.push(request);
        this._saveQueue(queue);

        // Try to sync immediately if online
        if (navigator.onLine) {
            this.sync();
        }

        return request.id;
    }

    /**
     * Generate unique ID for request
     */
    _generateId() {
        return `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Check if online
     */
    isOnline() {
        return navigator.onLine;
    }

    /**
     * Process sync queue
     */
    async sync() {
        if (this.syncing) return;
        if (!this.isOnline()) return;

        this.syncing = true;
        const queue = this._getQueue();

        if (queue.length === 0) {
            this.syncing = false;
            return;
        }

        const processed = [];
        const failed = [];

        for (const request of queue) {
            if (request.status === 'completed') {
                processed.push(request.id);
                continue;
            }

            if (request.retries >= this.maxRetries) {
                // Max retries reached, mark as failed
                failed.push(request.id);
                continue;
            }

            try {
                const success = await this._processRequest(request);
                if (success) {
                    processed.push(request.id);
                } else {
                    request.retries++;
                    if (request.retries < this.maxRetries) {
                        // Keep in queue for retry
                        continue;
                    } else {
                        failed.push(request.id);
                    }
                }
            } catch (e) {
                console.error('Sync request error:', e);
                request.retries++;
                if (request.retries >= this.maxRetries) {
                    failed.push(request.id);
                }
            }
        }

        // Remove processed requests
        const updatedQueue = queue.filter(req => 
            !processed.includes(req.id) && !failed.includes(req.id)
        );
        this._saveQueue(updatedQueue);

        // Trigger event for processed requests
        if (processed.length > 0) {
            this._triggerEvent('synced', { count: processed.length });
        }

        // Trigger event for failed requests
        if (failed.length > 0) {
            this._triggerEvent('syncFailed', { count: failed.length });
        }

        this.syncing = false;

        // If queue still has items, schedule retry
        if (updatedQueue.length > 0) {
            setTimeout(() => this.sync(), this.retryDelay);
        }
    }

    /**
     * Process a single request
     */
    async _processRequest(request) {
        try {
            const options = {
                method: request.method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCSRFToken()
                },
                credentials: 'same-origin'
            };

            if (request.method !== 'GET' && request.data) {
                options.body = JSON.stringify(request.data);
            }

            const response = await fetch(request.url, options);

            if (response.ok) {
                request.status = 'completed';
                return true;
            } else {
                // Server error, will retry
                return false;
            }
        } catch (e) {
            // Network error, will retry
            console.error('Request processing error:', e);
            return false;
        }
    }

    /**
     * Get CSRF token
     */
    _getCSRFToken() {
        const cookie = document.cookie.match(/csrftoken=([^;]+)/);
        if (cookie) return cookie[1];
        
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.content;
        
        const input = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (input) return input.value;
        
        return '';
    }

    /**
     * Trigger custom event
     */
    _triggerEvent(eventName, detail) {
        const event = new CustomEvent(`workout:${eventName}`, { detail });
        window.dispatchEvent(event);
    }

    /**
     * Get queue status
     */
    getQueueStatus() {
        const queue = this._getQueue();
        return {
            pending: queue.filter(r => r.status === 'pending').length,
            total: queue.length
        };
    }

    /**
     * Clear completed requests from queue
     */
    clearCompleted() {
        const queue = this._getQueue();
        const active = queue.filter(r => r.status !== 'completed');
        this._saveQueue(active);
    }
}

// Create global instance
const workoutSync = new WorkoutSync();

// Auto-sync when coming online
if (typeof window !== 'undefined') {
    window.addEventListener('online', () => {
        workoutSync.sync();
    });

    // Periodic sync check (every 30 seconds)
    setInterval(() => {
        if (workoutSync.isOnline() && workoutSync.getQueueStatus().pending > 0) {
            workoutSync.sync();
        }
    }, 30000);
}


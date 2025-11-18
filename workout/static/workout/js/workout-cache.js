/**
 * Workout Cache Manager
 * Handles client-side caching of workout data using localStorage
 */

class WorkoutCache {
    constructor() {
        this.prefix = 'workout:';
        this.defaultTTL = {
            'sessions:list': 300000,  // 5 minutes
            'session': 60000,          // 1 minute
            'exercises:list': 600000,   // 10 minutes
            'sets': 60000,              // 1 minute
        };
    }

    /**
     * Generate cache key
     */
    _getKey(type, identifier = '') {
        const userId = this._getUserId();
        if (identifier) {
            return `${this.prefix}${type}:${identifier}`;
        }
        if (userId) {
            return `${this.prefix}${type}:${userId}`;
        }
        return `${this.prefix}${type}`;
    }

    /**
     * Get user ID from page (if available)
     */
    _getUserId() {
        // Try to get from meta tag or data attribute
        const meta = document.querySelector('meta[name="user-id"]');
        if (meta) return meta.content;
        
        // Try to get from body data attribute
        const body = document.body;
        if (body && body.dataset.userId) return body.dataset.userId;
        
        return null;
    }

    /**
     * Check if cache entry is expired
     */
    _isExpired(entry) {
        if (!entry || !entry.timestamp) return true;
        const now = Date.now();
        return (now - entry.timestamp) > entry.ttl;
    }

    /**
     * Get data from cache
     */
    get(type, identifier = '') {
        try {
            const key = this._getKey(type, identifier);
            const cached = localStorage.getItem(key);
            
            if (!cached) return null;
            
            const entry = JSON.parse(cached);
            
            if (this._isExpired(entry)) {
                localStorage.removeItem(key);
                return null;
            }
            
            return entry.data;
        } catch (e) {
            console.error('Cache get error:', e);
            return null;
        }
    }

    /**
     * Set data in cache
     */
    set(type, data, identifier = '', ttl = null) {
        try {
            const key = this._getKey(type, identifier);
            const cacheTTL = ttl || this.defaultTTL[type] || 60000;
            
            const entry = {
                data: data,
                timestamp: Date.now(),
                ttl: cacheTTL
            };
            
            localStorage.setItem(key, JSON.stringify(entry));
            return true;
        } catch (e) {
            console.error('Cache set error:', e);
            // If quota exceeded, try to clean old entries
            if (e.name === 'QuotaExceededError') {
                this._cleanOldEntries();
                // Retry once
                try {
                    localStorage.setItem(key, JSON.stringify(entry));
                    return true;
                } catch (e2) {
                    console.error('Cache set retry failed:', e2);
                    return false;
                }
            }
            return false;
        }
    }

    /**
     * Remove data from cache
     */
    remove(type, identifier = '') {
        try {
            const key = this._getKey(type, identifier);
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Cache remove error:', e);
            return false;
        }
    }

    /**
     * Invalidate cache entries matching pattern
     */
    invalidate(pattern) {
        try {
            const keys = Object.keys(localStorage);
            const regex = new RegExp(pattern);
            
            keys.forEach(key => {
                if (regex.test(key)) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (e) {
            console.error('Cache invalidate error:', e);
            return false;
        }
    }

    /**
     * Clean old/expired entries
     */
    _cleanOldEntries() {
        try {
            const keys = Object.keys(localStorage);
            const prefix = this.prefix;
            let cleaned = 0;
            
            keys.forEach(key => {
                if (key.startsWith(prefix)) {
                    try {
                        const cached = localStorage.getItem(key);
                        if (cached) {
                            const entry = JSON.parse(cached);
                            if (this._isExpired(entry)) {
                                localStorage.removeItem(key);
                                cleaned++;
                            }
                        }
                    } catch (e) {
                        // Invalid entry, remove it
                        localStorage.removeItem(key);
                        cleaned++;
                    }
                }
            });
            
            if (cleaned > 0) {
                console.log(`Cleaned ${cleaned} expired cache entries`);
            }
        } catch (e) {
            console.error('Cache clean error:', e);
        }
    }

    /**
     * Get cache timestamp (last sync time)
     */
    getTimestamp(type, identifier = '') {
        try {
            const key = this._getKey(type, identifier);
            const cached = localStorage.getItem(key);
            
            if (!cached) return null;
            
            const entry = JSON.parse(cached);
            return entry.timestamp;
        } catch (e) {
            return null;
        }
    }

    /**
     * Clear all workout cache
     */
    clearAll() {
        try {
            const keys = Object.keys(localStorage);
            const prefix = this.prefix;
            
            keys.forEach(key => {
                if (key.startsWith(prefix)) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (e) {
            console.error('Cache clearAll error:', e);
            return false;
        }
    }
}

// Create global instance
const workoutCache = new WorkoutCache();

// Auto-clean on load
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        workoutCache._cleanOldEntries();
    });
}


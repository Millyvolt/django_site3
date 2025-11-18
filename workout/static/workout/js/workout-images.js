/**
 * Workout Image Cache Manager
 * Handles caching of exercise images and GIFs using Service Worker Cache API
 */

class WorkoutImageCache {
    constructor() {
        this.cacheName = 'workout-images-v1';
        this.maxCacheSize = 50 * 1024 * 1024; // 50MB
        this.imageQueue = [];
        this.preloading = false;
    }

    /**
     * Check if Service Worker is available
     */
    isAvailable() {
        return 'serviceWorker' in navigator && 'caches' in window;
    }

    /**
     * Preload images for exercises
     */
    async preloadImages(imageUrls) {
        if (!this.isAvailable()) return;
        if (this.preloading) return;

        this.preloading = true;
        const cache = await caches.open(this.cacheName);

        // Filter out already cached images
        const uncached = [];
        for (const url of imageUrls) {
            if (url) {
                const cached = await cache.match(url);
                if (!cached) {
                    uncached.push(url);
                }
            }
        }

        // Preload in batches to avoid overwhelming
        const batchSize = 5;
        for (let i = 0; i < uncached.length; i += batchSize) {
            const batch = uncached.slice(i, i + batchSize);
            await Promise.allSettled(
                batch.map(url => this._cacheImage(url, cache))
            );
        }

        this.preloading = false;
    }

    /**
     * Cache a single image
     */
    async _cacheImage(url, cache) {
        try {
            const response = await fetch(url, { mode: 'no-cors' });
            if (response && response.ok) {
                await cache.put(url, response.clone());
                return true;
            }
        } catch (e) {
            // Ignore errors (CORS, network, etc.)
            console.debug('Image cache error:', url, e);
        }
        return false;
    }

    /**
     * Get cached image URL (cache-first strategy)
     */
    async getCachedImageUrl(originalUrl) {
        if (!this.isAvailable() || !originalUrl) {
            return originalUrl;
        }

        try {
            const cache = await caches.open(this.cacheName);
            const cached = await cache.match(originalUrl);
            
            if (cached) {
                // Return blob URL for cached image
                const blob = await cached.blob();
                return URL.createObjectURL(blob);
            } else {
                // Cache the image for next time
                this._cacheImageInBackground(originalUrl, cache);
                return originalUrl;
            }
        } catch (e) {
            console.error('Image cache get error:', e);
            return originalUrl;
        }
    }

    /**
     * Cache image in background
     */
    async _cacheImageInBackground(url, cache) {
        try {
            const response = await fetch(url, { mode: 'no-cors' });
            if (response && response.ok) {
                await cache.put(url, response.clone());
            }
        } catch (e) {
            // Ignore errors
        }
    }

    /**
     * Update image element with cached version
     */
    async updateImageElement(imgElement, originalUrl) {
        if (!imgElement || !originalUrl) return;

        // Show placeholder while loading
        const placeholder = imgElement.getAttribute('data-placeholder') || '';
        if (placeholder) {
            imgElement.src = placeholder;
        }

        try {
            const cachedUrl = await this.getCachedImageUrl(originalUrl);
            imgElement.src = cachedUrl;
            
            // Clean up blob URL when image loads
            imgElement.addEventListener('load', () => {
                if (cachedUrl.startsWith('blob:')) {
                    // Don't revoke immediately, let browser handle it
                    setTimeout(() => URL.revokeObjectURL(cachedUrl), 1000);
                }
            }, { once: true });
        } catch (e) {
            // Fallback to original URL
            imgElement.src = originalUrl;
        }
    }

    /**
     * Extract image URLs from exercise data
     */
    extractImageUrls(exercises) {
        const urls = [];
        exercises.forEach(exercise => {
            if (exercise.image) {
                urls.push(exercise.image);
            }
        });
        return urls;
    }

    /**
     * Clean old cache entries (if cache is too large)
     */
    async cleanCache() {
        if (!this.isAvailable()) return;

        try {
            const cache = await caches.open(this.cacheName);
            const keys = await cache.keys();
            
            // Simple cleanup: remove oldest 20% if we have many entries
            if (keys.length > 50) {
                const toRemove = Math.floor(keys.length * 0.2);
                const sorted = keys.sort((a, b) => {
                    // Sort by URL (simple heuristic)
                    return a.url.localeCompare(b.url);
                });
                
                for (let i = 0; i < toRemove; i++) {
                    await cache.delete(sorted[i]);
                }
            }
        } catch (e) {
            console.error('Cache clean error:', e);
        }
    }

    /**
     * Get cache size estimate
     */
    async getCacheSize() {
        if (!this.isAvailable()) return 0;

        try {
            const cache = await caches.open(this.cacheName);
            const keys = await cache.keys();
            let totalSize = 0;

            for (const key of keys) {
                const response = await cache.match(key);
                if (response) {
                    const blob = await response.blob();
                    totalSize += blob.size;
                }
            }

            return totalSize;
        } catch (e) {
            console.error('Cache size error:', e);
            return 0;
        }
    }

    /**
     * Clear all cached images
     */
    async clearCache() {
        if (!this.isAvailable()) return;

        try {
            const deleted = await caches.delete(this.cacheName);
            if (deleted) {
                // Recreate cache
                await caches.open(this.cacheName);
            }
            return deleted;
        } catch (e) {
            console.error('Cache clear error:', e);
            return false;
        }
    }
}

// Create global instance
const workoutImageCache = new WorkoutImageCache();

// Auto-clean cache periodically (once per day)
if (typeof window !== 'undefined') {
    const lastClean = localStorage.getItem('workout:imageCache:lastClean');
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;

    if (!lastClean || (now - parseInt(lastClean)) > oneDay) {
        workoutImageCache.cleanCache().then(() => {
            localStorage.setItem('workout:imageCache:lastClean', now.toString());
        });
    }
}


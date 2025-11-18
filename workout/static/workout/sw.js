/**
 * Service Worker for Workout App
 * Handles offline support, caching, and background sync
 */

const CACHE_VERSION = 'workout-v1';
const CACHE_NAMES = {
    pages: 'workout-pages-v1',
    images: 'workout-images-v1',
    api: 'workout-api-v1',
    static: 'workout-static-v1'
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAMES.static).then((cache) => {
            // Cache critical static files
            return cache.addAll([
                '/static/workout/js/workout-cache.js',
                '/static/workout/js/workout-sync.js',
                '/static/workout/js/workout-images.js'
            ]).catch(err => {
                console.log('Cache addAll error (some files may not exist):', err);
            });
        })
    );
    
    // Activate immediately
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches that don't match current version
                    if (!Object.values(CACHE_NAMES).includes(cacheName) && 
                        cacheName.startsWith('workout-')) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    // Take control of all pages immediately
    return self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // Handle image requests (cache-first)
    if (url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) || 
        url.pathname.startsWith('/media/exercises/')) {
        event.respondWith(handleImageRequest(event.request));
        return;
    }
    
    // Handle API/JSON requests (network-first with cache fallback)
    if (url.pathname.startsWith('/workout/') && 
        event.request.headers.get('accept')?.includes('application/json')) {
        event.respondWith(handleApiRequest(event.request));
        return;
    }
    
    // Handle HTML page requests (cache-first for offline)
    if (event.request.mode === 'navigate' || 
        event.request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(handlePageRequest(event.request));
        return;
    }
    
    // Handle static assets (cache-first)
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(handleStaticRequest(event.request));
        return;
    }
});

/**
 * Handle image requests - cache-first strategy
 */
async function handleImageRequest(request) {
    const cache = await caches.open(CACHE_NAMES.images);
    const cached = await cache.match(request);
    
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            // Cache successful responses
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Network error - return placeholder if available
        return new Response('', { status: 404 });
    }
}

/**
 * Handle API requests - network-first with cache fallback
 */
async function handleApiRequest(request) {
    const cache = await caches.open(CACHE_NAMES.api);
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            // Cache successful GET requests
            if (request.method === 'GET') {
                cache.put(request, response.clone());
            }
        }
        return response;
    } catch (error) {
        // Network error - try cache
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        // Return error response
        return new Response(JSON.stringify({ error: 'Network error and no cache' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Handle page requests - cache-first for offline support
 */
async function handlePageRequest(request) {
    const cache = await caches.open(CACHE_NAMES.pages);
    const cached = await cache.match(request);
    
    if (cached) {
        // Try to update cache in background
        fetch(request).then(response => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
        }).catch(() => {
            // Ignore fetch errors
        });
        
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Network error - return offline page if available
        const offlinePage = await cache.match('/workout/offline/');
        if (offlinePage) {
            return offlinePage;
        }
        return new Response('Offline', { status: 503 });
    }
}

/**
 * Handle static asset requests - cache-first
 */
async function handleStaticRequest(request) {
    const cache = await caches.open(CACHE_NAMES.static);
    const cached = await cache.match(request);
    
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('Asset not found', { status: 404 });
    }
}

/**
 * Background sync for queued requests
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'workout-sync') {
        event.waitUntil(syncWorkoutData());
    }
});

async function syncWorkoutData() {
    // This will be called by the sync manager
    // The actual sync logic is in workout-sync.js
    console.log('Background sync triggered');
}

/**
 * Message handler for cache management
 */
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        const cacheName = event.data.cacheName;
        if (cacheName) {
            caches.delete(cacheName).then(() => {
                event.ports[0].postMessage({ success: true });
            });
        } else {
            // Clear all workout caches
            Promise.all(
                Object.values(CACHE_NAMES).map(name => caches.delete(name))
            ).then(() => {
                event.ports[0].postMessage({ success: true });
            });
        }
    }
    
    if (event.data && event.data.type === 'CACHE_IMAGE') {
        const url = event.data.url;
        if (url) {
            caches.open(CACHE_NAMES.images).then(cache => {
                return fetch(url).then(response => {
                    if (response.ok) {
                        cache.put(url, response.clone());
                        event.ports[0].postMessage({ success: true });
                    }
                });
            }).catch(err => {
                event.ports[0].postMessage({ success: false, error: err.message });
            });
        }
    }
});


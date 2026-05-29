/**
 * Gaze Authentication - Service Worker
 * =====================================
 * Provides offline capability and caching for PWA
 */

const CACHE_NAME = 'gaze-auth-v2';
const DYNAMIC_CACHE = 'gaze-dynamic-v2';

// Install event - skip caching, let dynamic cache handle it
self.addEventListener('install', event => {
    console.log('[SW] Installing Service Worker...');
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activating Service Worker...');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME && key !== DYNAMIC_CACHE)
                    .map(key => {
                        console.log('[SW] Removing old cache:', key);
                        return caches.delete(key);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, cache fallback
self.addEventListener('fetch', event => {
    const { request } = event;

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip API requests
    if (request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        fetch(request)
            .then(response => {
                // Cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(DYNAMIC_CACHE).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Fallback to cache when offline
                return caches.match(request);
            })
    );
});

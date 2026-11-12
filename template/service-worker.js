const CACHE_NAME = 'mechanic-cache-v3';
const urlsToCache = [
    '/managers',
    '/managers/',
];

// Install event: Pre-cache the `/managers` page
self.addEventListener('install', event => {
    console.log('[Service Worker] Install');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Caching:', urlsToCache);
                return cache.addAll(urlsToCache);
            })
            .catch(error => console.error('[Service Worker] Caching failed:', error))
    );
    self.skipWaiting(); // Activate the service worker immediately
});

// Activate event: Clear old caches
self.addEventListener('activate', event => {
    console.log('[Service Worker] Activate');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log(`[Service Worker] Deleting old cache: ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim(); // Start controlling pages immediately
});

// Fetch event: Serve from cache or fetch from the network
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return; // Only cache GET requests

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Serve from cache if available
                if (cachedResponse) return cachedResponse;

                // Fetch from network if not cached
                return fetch(event.request).catch(() => {
                    // Return `/managers` page if offline and not cached
                    if (event.request.url.endsWith('/managers')) {
                        return caches.match('/managers');
                    }
                });
            })
    );
});

// Optional: Message listener for manual cache updates or skip waiting
self.addEventListener('message', event => {
    if (event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
});





// const CACHE_NAME = 'mechanic-cache-v2'; // Increment version for updates
// const urlsToCache = [
//     '/managers',
// ];

// // Install event: Pre-cache static assets
// self.addEventListener('install', event => {
//     console.log('[Service Worker] Install');
//     event.waitUntil(
//         caches.open(CACHE_NAME)
//             .then(cache => {
//                 console.log('[Service Worker] Caching static assets');
//                 return cache.addAll(urlsToCache);
//             })
//             .catch(error => console.error('[Service Worker] Caching failed:', error))
//     );
//     self.skipWaiting(); // Activate this service worker immediately
// });

// // Activate event: Clean up old caches
// self.addEventListener('activate', event => {
//     console.log('[Service Worker] Activate');
//     event.waitUntil(
//         caches.keys().then(cacheNames => {
//             return Promise.all(
//                 cacheNames.map(cacheName => {
//                     if (cacheName !== CACHE_NAME) {
//                         console.log(`[Service Worker] Deleting old cache: ${cacheName}`);
//                         return caches.delete(cacheName);
//                     }
//                 })
//             );
//         })
//     );
//     self.clients.claim(); // Start controlling pages immediately
// });

// // Fetch event: Serve from cache or fetch from network
// self.addEventListener('fetch', event => {
//     if (event.request.method !== 'GET') {
//         return; // Only cache GET requests
//     }

//     event.respondWith(
//         caches.match(event.request)
//             .then(cachedResponse => {
//                 if (cachedResponse) {
//                     return cachedResponse; // Serve from cache
//                 }

//                 return fetch(event.request)
//                     .then(networkResponse => {
//                         // Optionally cache dynamic responses
//                         if (event.request.url.startsWith(self.origin)) {
//                             return caches.open(CACHE_NAME).then(cache => {
//                                 cache.put(event.request, networkResponse.clone());
//                                 return networkResponse;
//                             });
//                         }
//                         return networkResponse;
//                     });
//             })
//             .catch(() => caches.match('/managers')) // Serve offline page on failure
//     );
// });

// // Message listener: Optional for manual cache updates or client communication
// self.addEventListener('message', event => {
//     if (event.data.action === 'skipWaiting') {
//         self.skipWaiting();
//     }
// });





// const CACHE_NAME = 'mechanic-cache-v1';
// const urlsToCache = [
//     '/',
//     '/offline',
//     '/static/css/chatBot.css',
//     '/static/css/chatgpt.css',
//     '/static/css/dashboard.css',
//     '/static/css/index.css',
//     '/static/css/mechanic.css',
//     '/static/css/signup.css',
//     '/static/css/UserLogin.css',
//     '/static/js/bank.js',
//     '/static/js/chatBot.js',
//     '/static/js/chatgpt.js',
//     '/static/js/dashboard.js',
//     '/static/js/datatable.js',
//     '/static/js/index.js',
//     '/static/js/mechanic.js',
//     '/static/js/questions.js',
//     '/static/js/signup.js'
// ];

// self.addEventListener('install', event => {
//     event.waitUntil(
//         caches.open(CACHE_NAME)
//             .then(cache => cache.addAll(urlsToCache))
//             .catch(error => console.error('Caching failed:', error))
//     );
// });

// self.addEventListener('fetch', event => {
//     event.respondWith(
//         caches.match(event.request)
//             .then(response => response || fetch(event.request))
//             .catch(() => caches.match('/offline'))
//     );
// });

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('autoaid-cache').then((cache) => {
            return cache.addAll([
                '/',
                '/offline/',
                '/static/css/chatBot.css',
                '/static/js/chatBot.js'
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        }).catch(() => caches.match('/offline/'));
    );
});

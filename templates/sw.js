importScripts("https://cdn.pushalert.co/sw-88225.js");

/**
 * Service Worker for Chrome Push Notifications
 * Handles background notifications, clicks, and analytics
 */

// Service Worker install event
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    self.skipWaiting();
});

// Service Worker activate event
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(clients.claim());
});

// Handle messages from client
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SEND_NOTIFICATION') {
        const { title, options } = event.data;
        self.registration.showNotification(title, {
            icon: '/static/img/logo.png',
            badge: '/static/img/favicon.png',
            tag: 'charlady-notification',
            ...options
        });
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then((windowClients) => {
            // Check if there's already a window/tab open with the target URL
            for (let i = 0; i < windowClients.length; i++) {
                const client = windowClients[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // If not, open a new window/tab
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );

    // Send analytics
    fetch('/notifications/api/event/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'notification_clicked',
            title: event.notification.title,
            timestamp: new Date().toISOString()
        })
    }).catch(err => console.error('Analytics tracking failed:', err));
});

// Handle notification close
self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed:', event.notification.title);

    // Send analytics
    fetch('/notifications/api/event/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'notification_closed',
            title: event.notification.title,
            timestamp: new Date().toISOString()
        })
    }).catch(err => console.error('Analytics tracking failed:', err));
});

// Handle push events (for background notifications)
self.addEventListener('push', (event) => {
    console.log('Push notification received:', event);

    let notificationData = {
        title: 'Charlady',
        options: {
            icon: '/static/img/logo.png',
            badge: '/static/img/favicon.png',
            tag: 'charlady-notification',
            requireInteraction: false
        }
    };

    if (event.data) {
        try {
            const data = event.data.json();
            notificationData.title = data.title || notificationData.title;
            notificationData.options = {
                ...notificationData.options,
                body: data.body || 'New notification from Charlady',
                data: data.data || {}
            };
        } catch (e) {
            notificationData.options.body = event.data.text();
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData.options)
    );
});

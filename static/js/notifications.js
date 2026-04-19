/**
 * Chrome Notifications Manager
 * Handles browser push notifications, permissions, and service worker registration
 */

class NotificationManager {
    constructor() {
        this.serviceWorkerRegistered = false;
        this.notificationPermission = this.getNotificationPermission();
    }

    /**
     * Get current notification permission status
     */
    getNotificationPermission() {
        if (!('Notification' in window)) {
            console.warn('Browser does not support notifications');
            return 'denied';
        }
        return Notification.permission;
    }

    /**
     * Request notification permission from user
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('Notifications not supported by this browser');
            return false;
        }

        if (Notification.permission === 'granted') {
            console.log('Notification permission already granted');
            return true;
        }

        if (Notification.permission === 'denied') {
            console.log('Notification permission denied by user');
            this.showPermissionDeniedMessage();
            return false;
        }

        // Permission is 'default', ask user
        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;

            if (permission === 'granted') {
                console.log('Notification permission granted by user');
                this.showPermissionGrantedMessage();
                // Send analytics
                this.trackPermissionGranted();
                return true;
            } else {
                console.log('Notification permission denied by user');
                this.showPermissionDeniedMessage();
                this.trackPermissionDenied();
                return false;
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }

    /**
     * Register service worker for push notifications
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Workers not supported by this browser');
            return false;
        }

        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });
            console.log('Service Worker registered successfully:', registration);
            this.serviceWorkerRegistered = true;

            // Handle service worker updates
            registration.addEventListener('updatefound', () => {
                console.log('Service Worker update found');
            });

            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    /**
     * Send a browser notification
     */
    sendNotification(title, options = {}) {
        if (this.notificationPermission !== 'granted') {
            console.warn('Notification permission not granted');
            return null;
        }

        try {
            const notification = new Notification(title, {
                icon: '/static/img/logo.png',
                badge: '/static/img/favicon.png',
                tag: 'charlady-notification',
                requireInteraction: false,
                ...options
            });

            // Handle notification click
            notification.addEventListener('click', () => {
                window.focus();
                notification.close();
                if (options.url) {
                    window.location.href = options.url;
                }
            });

            // Handle notification close
            notification.addEventListener('close', () => {
                this.trackNotificationClosed(title);
            });

            return notification;
        } catch (error) {
            console.error('Failed to send notification:', error);
            return null;
        }
    }

    /**
     * Send notification via service worker (for background notifications)
     */
    async sendServiceWorkerNotification(title, options = {}) {
        if (!this.serviceWorkerRegistered) {
            console.warn('Service Worker not registered');
            return null;
        }

        try {
            const registration = await navigator.serviceWorker.ready;
            if (registration.active) {
                registration.active.postMessage({
                    type: 'SEND_NOTIFICATION',
                    title: title,
                    options: options
                });
                return true;
            }
        } catch (error) {
            console.error('Failed to send service worker notification:', error);
            return false;
        }
    }

    /**
     * Show banner prompting user to enable notifications
     */
    showNotificationBanner() {
        if (this.notificationPermission !== 'default') {
            return;
        }

        const banner = document.getElementById('notification-permission-banner');
        if (!banner) {
            this.createNotificationBanner();
        } else {
            banner.style.display = 'flex';
        }
    }

    /**
     * Create notification permission banner
     */
    createNotificationBanner() {
        const banner = document.createElement('div');
        banner.id = 'notification-permission-banner';
        banner.className = 'fixed top-0 left-0 right-0 bg-gradient-to-r from-emerald-600 to-green-600 text-white shadow-lg flex items-center justify-between px-6 py-4 z-50 animate-slideDown';
        banner.innerHTML = `
            <div class="flex items-center gap-4">
                <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <div>
                    <p class="font-semibold">Enable Notifications</p>
                    <p class="text-sm text-emerald-50">Stay updated with job offers and messages</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <button id="notification-enable-btn" class="bg-white text-emerald-600 px-6 py-2 rounded-lg font-semibold hover:bg-emerald-50 transition">
                    Enable
                </button>
                <button id="notification-dismiss-btn" class="text-white hover:text-emerald-100 transition">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </button>
            </div>
        `;

        document.body.insertBefore(banner, document.body.firstChild);

        // Event listeners
        document.getElementById('notification-enable-btn').addEventListener('click', async () => {
            const granted = await this.requestPermission();
            if (granted) {
                banner.style.display = 'none';
                banner.remove();
            }
        });

        document.getElementById('notification-dismiss-btn').addEventListener('click', () => {
            banner.style.display = 'none';
            localStorage.setItem('notification-banner-dismissed', 'true');
        });
    }

    /**
     * Show "Permission Granted" toast message
     */
    showPermissionGrantedMessage() {
        this.showToast('Notifications Enabled! 🔔', 'You will now receive job updates and messages.', 'success');
    }

    /**
     * Show "Permission Denied" toast message
     */
    showPermissionDeniedMessage() {
        this.showToast('Notifications Disabled', 'You can enable notifications in your browser settings.', 'info');
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        const toast = document.createElement('div');
        const bgColor = {
            success: 'bg-emerald-600',
            error: 'bg-red-600',
            info: 'bg-blue-600',
            warning: 'bg-amber-600'
        }[type] || 'bg-blue-600';

        toast.className = `fixed bottom-6 right-6 ${bgColor} text-white px-6 py-4 rounded-lg shadow-2xl z-50 animate-slideUp`;
        toast.innerHTML = `
            <p class="font-semibold">${title}</p>
            <p class="text-sm opacity-90">${message}</p>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    /**
     * Track permission granted
     */
    trackPermissionGranted() {
        fetch('/notifications/api/permission/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                action: 'permission_granted',
                browser: this.getBrowserName()
            })
        }).catch(err => console.error('Analytics tracking failed:', err));
    }

    /**
     * Track permission denied
     */
    trackPermissionDenied() {
        fetch('/notifications/api/permission/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                action: 'permission_denied',
                browser: this.getBrowserName()
            })
        }).catch(err => console.error('Analytics tracking failed:', err));
    }

    /**
     * Track notification closed
     */
    trackNotificationClosed(title) {
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/notifications/api/event/', JSON.stringify({
                action: 'notification_closed',
                title: title
            }));
        }
    }

    /**
     * Get CSRF token from cookie
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Get browser name
     */
    getBrowserName() {
        const ua = navigator.userAgent;
        if (ua.indexOf('Firefox') > -1) return 'Firefox';
        if (ua.indexOf('Chrome') > -1) return 'Chrome';
        if (ua.indexOf('Safari') > -1) return 'Safari';
        if (ua.indexOf('Edge') > -1) return 'Edge';
        return 'Unknown';
    }

    /**
     * Initialize notifications system
     */
    async init() {
        console.log('Initializing Notification Manager...');

        // Register service worker
        await this.registerServiceWorker();

        // Show banner if permission is not yet requested
        if (this.notificationPermission === 'default') {
            // Delay showing banner to avoid immediate popup
            setTimeout(() => this.showNotificationBanner(), 3000);
        }

        // Check notification permission status and log
        console.log('Notification permission status:', this.notificationPermission);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    const notificationManager = new NotificationManager();
    window.notificationManager = notificationManager;
    await notificationManager.init();
});

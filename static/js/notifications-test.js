/**
 * Chrome Notifications Testing Script
 * Include this in DevTools Console to test the notification system
 */

console.log('=== CHARLADY CHROME NOTIFICATIONS TEST SUITE ===\n');

// Test 1: Check Notification Support
console.log('TEST 1: Browser Notification Support');
if ('Notification' in window) {
    console.log('✅ Notifications supported');
    console.log(`   Permission: ${Notification.permission}`);
} else {
    console.error('❌ Notifications NOT supported');
}

// Test 2: Check Service Worker Support
console.log('\nTEST 2: Service Worker Support');
if ('serviceWorker' in navigator) {
    console.log('✅ Service Workers supported');
} else {
    console.error('❌ Service Workers NOT supported');
}

// Test 3: Check NotificationManager
console.log('\nTEST 3: NotificationManager Availability');
if (window.notificationManager) {
    console.log('✅ NotificationManager initialized');
    console.log(`   Permission: ${window.notificationManager.notificationPermission}`);
    console.log(`   Service Worker Registered: ${window.notificationManager.serviceWorkerRegistered}`);
} else {
    console.error('❌ NotificationManager NOT found');
}

// Test 4: Check Service Worker Registration
console.log('\nTEST 4: Service Worker Registration');
navigator.serviceWorker.getRegistrations().then(regs => {
    if (regs.length > 0) {
        console.log('✅ Service Worker registered');
        regs.forEach(reg => {
            console.log(`   Scope: ${reg.scope}`);
            console.log(`   Active: ${reg.active ? '✅' : '❌'}`);
        });
    } else {
        console.warn('⚠️  No Service Workers registered');
    }
});

// Test 5: Request Permissions
console.log('\nTEST 5: Request Permissions');
console.log('To test permission request, run: await notificationManager.requestPermission()');

// Test 6: Send Test Notification
console.log('\nTEST 6: Send Test Notification');
console.log('To send a test notification, run:');
console.log('  notificationManager.sendNotification("Test!", { body: "Testing notifications" })');

// Test 7: Check CSRF Token
console.log('\nTEST 7: CSRF Token');
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                  document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
if (csrfToken) {
    console.log('✅ CSRF Token found');
} else {
    console.warn('⚠️  CSRF Token not found (might be OK if not in form)');
}

// Test 8: Analytics Endpoints
console.log('\nTEST 8: Analytics Endpoints');
console.log('Testing analytics endpoints...');
fetch('/notifications/api/permission/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || ''
    },
    body: JSON.stringify({
        action: 'test_connection',
        browser: 'Chrome'
    })
}).then(res => {
    if (res.ok || res.status === 403) {
        console.log('✅ Analytics endpoints accessible');
    } else {
        console.error(`❌ Analytics endpoint returned ${res.status}`);
    }
}).catch(err => console.error(`❌ Analytics endpoint error: ${err.message}`));

// Helper Functions
window.notificationTestHelpers = {
    /**
     * Test sending notifications
     */
    testNotification: async () => {
        console.log('Sending test notification...');
        const notif = notificationManager.sendNotification('Test Notification! 🎉', {
            body: 'This is a test notification from Charlady',
            icon: '/static/img/logo.png',
            badge: '/static/img/favicon.png',
            tag: 'test-notification'
        });
        if (notif) {
            console.log('✅ Test notification sent');
        } else {
            console.error('❌ Failed to send notification');
        }
    },

    /**
     * Test permission request
     */
    testPermission: async () => {
        console.log('Testing permission request...');
        const granted = await notificationManager.requestPermission();
        console.log(`Permission result: ${granted ? '✅ Granted' : '❌ Denied'}`);
    },

    /**
     * Full system test
     */
    fullTest: async () => {
        console.log('Starting full system test...\n');
        
        // Check support
        console.log('1️⃣  Checking browser support...');
        if (!('Notification' in window) || !('serviceWorker' in navigator)) {
            console.error('Browser does not support required features');
            return;
        }
        console.log('✅ Browser supported\n');
        
        // Check manager
        console.log('2️⃣  Checking NotificationManager...');
        if (!window.notificationManager) {
            console.error('NotificationManager not initialized');
            return;
        }
        console.log('✅ NotificationManager ready\n');
        
        // Request permission
        console.log('3️⃣  Requesting permission...');
        const granted = await notificationManager.requestPermission();
        if (!granted) {
            console.warn('Permission not granted, skipping notification test');
            return;
        }
        console.log('✅ Permission granted\n');
        
        // Send test notification
        console.log('4️⃣  Sending test notification...');
        const notif = notificationManager.sendNotification('Full Test Complete! ✨', {
            body: 'All systems operational'
        });
        if (notif) {
            console.log('✅ Notification sent\n');
            console.log('🎉 All tests passed!');
        } else {
            console.error('Failed to send notification');
        }
    },

    /**
     * Show system info
     */
    sysInfo: () => {
        console.log('=== SYSTEM INFO ===\n');
        console.log(`Browser: ${navigator.userAgent}`);
        console.log(`Notifications: ${Notification.permission}`);
        console.log(`Service Workers: ${navigator.serviceWorker ? 'Supported' : 'Not Supported'}`);
        console.log(`NotificationManager: ${window.notificationManager ? 'Ready' : 'Not Initialized'}`);
        console.log(`\nTo run full test, execute: notificationTestHelpers.fullTest()`);
    }
};

console.log('\n=== TEST SUITE LOADED ===');
console.log('Helper functions available:');
console.log('  - notificationTestHelpers.testNotification()');
console.log('  - notificationTestHelpers.testPermission()');
console.log('  - notificationTestHelpers.fullTest()');
console.log('  - notificationTestHelpers.sysInfo()');
console.log('\nFor detailed guide, see: CHROME_NOTIFICATIONS_GUIDE.md');

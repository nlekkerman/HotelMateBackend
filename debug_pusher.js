// Debug Pusher connection in browser console
// Paste this in your browser's developer console

console.log('=== PUSHER DEBUG ===');

// Check if Pusher is available
if (typeof Pusher !== 'undefined') {
    console.log('✅ Pusher is loaded');
    
    // Check if there's a global pusher instance
    if (window.pusher) {
        console.log('✅ Pusher instance found');
        console.log('Connection state:', window.pusher.connection.state);
        console.log('Socket ID:', window.pusher.connection.socket_id);
        
        // List all subscribed channels
        console.log('Subscribed channels:', Object.keys(window.pusher.channels.channels));
        
        // Debug connection events
        window.pusher.connection.bind('connected', function() {
            console.log('🔵 Pusher connected with socket ID:', window.pusher.connection.socket_id);
        });
        
        window.pusher.connection.bind('disconnected', function() {
            console.log('🔴 Pusher disconnected');
        });
        
        window.pusher.connection.bind('error', function(err) {
            console.log('❌ Pusher connection error:', err);
        });
        
    } else {
        console.log('❌ No pusher instance found on window object');
        console.log('Available globals:', Object.keys(window).filter(k => k.toLowerCase().includes('pusher')));
    }
} else {
    console.log('❌ Pusher not loaded');
}

// Function to subscribe to a channel and listen for events
function debugChannel(channelName) {
    if (!window.pusher) {
        console.log('❌ No pusher instance available');
        return;
    }
    
    console.log(`🔍 Debugging channel: ${channelName}`);
    const channel = window.pusher.subscribe(channelName);
    
    channel.bind('pusher:subscription_succeeded', function() {
        console.log(`✅ Successfully subscribed to ${channelName}`);
    });
    
    channel.bind('pusher:subscription_error', function(err) {
        console.log(`❌ Failed to subscribe to ${channelName}:`, err);
    });
    
    // Listen for realtime_event (based on your logs)
    channel.bind('realtime_event', function(data) {
        console.log(`📨 Received realtime_event on ${channelName}:`, data);
    });
    
    // Listen for all events on this channel
    channel.bind_global(function(eventName, data) {
        console.log(`📨 Event '${eventName}' on ${channelName}:`, data);
    });
}

// Test with the channel from your logs
debugChannel('private-hotel-hotel-killarney-guest-chat-booking-BK-2026-0001');

console.log('=== DEBUG FUNCTIONS READY ===');
console.log('Use: debugChannel("your-channel-name") to test specific channels');
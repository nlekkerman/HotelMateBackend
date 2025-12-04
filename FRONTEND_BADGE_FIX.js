// FRONTEND FIX - Staff Badge Real-time Updates

// 1. PUSHER SUBSCRIPTION (add this to your main app or staff list component)
import Pusher from 'pusher-js';

const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
    cluster: process.env.REACT_APP_PUSHER_CLUSTER,
    encrypted: true
});

// Subscribe to hotel events
const hotelSlug = localStorage.getItem('hotelSlug'); // "hotel-killarney"
const channel = pusher.subscribe(`hotel-${hotelSlug}`);

// Listen for clock status updates
channel.bind('clock-status-updated', (data) => {
    console.log('🔔 Clock status update received:', data);
    
    // Update staff list/badge immediately
    updateStaffStatus(data.staff_id, {
        duty_status: data.duty_status,
        current_status: data.current_status,
        is_on_duty: data.is_on_duty,
        is_on_break: data.is_on_break,
        status_label: data.status_label
    });
});

// 2. STAFF STATUS UPDATE FUNCTION
function updateStaffStatus(staffId, statusData) {
    // If you're using React state management
    setStaffList(prevList => 
        prevList.map(staff => 
            staff.id === staffId 
                ? { ...staff, ...statusData }
                : staff
        )
    );
    
    // Or if using Redux/Zustand, dispatch update action
    // dispatch(updateStaffStatus({ staffId, statusData }));
    
    // Force re-render of specific badge component
    const badgeElement = document.querySelector(`[data-staff-id="${staffId}"]`);
    if (badgeElement) {
        // Trigger badge refresh
        badgeElement.dispatchEvent(new CustomEvent('statusUpdate', { 
            detail: statusData 
        }));
    }
}

// 3. STAFF BADGE COMPONENT FIX
// Update your StaffBadge component to listen for real-time updates

const StaffBadge = ({ staff }) => {
    const [currentStatus, setCurrentStatus] = useState(staff.duty_status);
    const [statusLabel, setStatusLabel] = useState(staff.current_status?.label || 'Off Duty');
    
    useEffect(() => {
        // Listen for custom status update events
        const handleStatusUpdate = (event) => {
            const { duty_status, status_label } = event.detail;
            setCurrentStatus(duty_status);
            setStatusLabel(status_label);
        };
        
        const element = document.querySelector(`[data-staff-id="${staff.id}"]`);
        if (element) {
            element.addEventListener('statusUpdate', handleStatusUpdate);
            return () => element.removeEventListener('statusUpdate', handleStatusUpdate);
        }
    }, [staff.id]);
    
    // Use currentStatus instead of staff.duty_status
    const badgeColor = {
        'on_duty': 'green',
        'off_duty': 'gray', 
        'on_break': 'yellow'
    }[currentStatus] || 'gray';
    
    return (
        <div data-staff-id={staff.id} className={`badge badge-${badgeColor}`}>
            {statusLabel}
        </div>
    );
};

// 4. FORCE REFRESH STAFF LIST
// Add this function to manually refresh staff data
async function refreshStaffData() {
    const hotelSlug = localStorage.getItem('hotelSlug');
    const token = localStorage.getItem('authToken');
    
    try {
        const response = await fetch(`/api/staff/hotel/${hotelSlug}/staff/`, {
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const freshStaffData = await response.json();
            setStaffList(freshStaffData.results || freshStaffData);
            console.log('✅ Staff data refreshed');
        }
    } catch (error) {
        console.error('❌ Failed to refresh staff data:', error);
    }
}

// 5. DEBUG PUSHER CONNECTION
// Add this to check if Pusher is working
function debugPusherConnection() {
    console.log('🔍 Pusher Debug Info:');
    console.log('- Pusher state:', pusher.connection.state);
    console.log('- Subscribed channels:', Object.keys(pusher.channels.channels));
    
    const hotelSlug = localStorage.getItem('hotelSlug');
    const channel = pusher.channels.channels[`hotel-${hotelSlug}`];
    
    if (channel) {
        console.log('- Hotel channel found:', `hotel-${hotelSlug}`);
        console.log('- Channel state:', channel.state);
        console.log('- Bound events:', Object.keys(channel.callbacks));
    } else {
        console.log('❌ Hotel channel NOT found:', `hotel-${hotelSlug}`);
    }
}

// Call this in your dev tools: debugPusherConnection()

// 6. QUICK TEST - MANUAL BADGE UPDATE
// Test if badges can update by running this in console:
function testBadgeUpdate(staffId) {
    updateStaffStatus(staffId, {
        duty_status: 'on_duty',
        current_status: { status: 'on_duty', label: 'On Duty', is_on_break: false },
        status_label: 'On Duty'
    });
}

// Usage: testBadgeUpdate(35) // Nikola's staff ID
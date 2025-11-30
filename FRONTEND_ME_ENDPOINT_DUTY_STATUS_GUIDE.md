# Frontend Guide: Using /me Endpoint with Duty Status System

This guide explains how to use the enhanced `/me` endpoint that now includes the new duty status system with real-time Pusher updates.

## 📋 Overview

The `/me` endpoint has been enhanced to provide comprehensive staff status information including:
- **duty_status**: New choices field (off_duty, on_duty, on_break)
- **current_status**: Detailed status object with break information
- **Real-time updates**: Pusher WebSocket events for live UI updates

## 🚀 API Endpoint

### Get Staff Profile
```http
GET /api/staff/hotel/{hotel_slug}/me/
Authorization: Token your_auth_token
```

### Response Structure
```json
{
    "id": 123,
    "user": {
        "id": 456,
        "username": "john_doe",
        "email": "john@hotel.com",
        "is_active": true
    },
    "first_name": "John",
    "last_name": "Doe",
    "department": {
        "id": 1,
        "name": "Front Desk",
        "slug": "front-desk"
    },
    "role": {
        "id": 2,
        "name": "Receptionist",
        "slug": "receptionist"
    },
    "email": "john@hotel.com",
    "phone_number": "+1234567890",
    "is_active": true,
    "duty_status": "on_duty",
    "is_on_duty": true,
    "hotel": {
        "id": 1,
        "name": "Grand Hotel",
        "slug": "grand-hotel"
    },
    "profile_image_url": "https://cloudinary.com/...",
    "has_registered_face": true,
    "allowed_navs": ["home", "chat", "bookings"],
    "current_status": {
        "status": "on_duty",
        "label": "On Duty",
        "is_on_break": false
    }
}
```

## 🎯 Duty Status Values

### Status Options
| Value | Label | Description |
|-------|-------|-------------|
| `off_duty` | Off Duty | Staff member is not working |
| `on_duty` | On Duty | Staff member is actively working |
| `on_break` | On Break | Staff member is on break during work hours |

### Current Status Object
```typescript
interface CurrentStatus {
    status: 'off_duty' | 'on_duty' | 'on_break';
    label: string;
    is_on_break: boolean;
    break_start?: string;  // ISO datetime when on break
    total_break_minutes?: number;  // Total break time today
}
```

## 🔄 Real-time Updates with Pusher

### Subscribe to Status Updates
```javascript
// Initialize Pusher
const pusher = new Pusher('your_pusher_key', {
    cluster: 'your_cluster',
    encrypted: true
});

// Subscribe to hotel channel
const channel = pusher.subscribe(`hotel-${hotelSlug}`);

// Listen for clock status updates
channel.bind('clock-status-updated', (data) => {
    console.log('Status update:', data);
    
    // Update UI based on data.staff_id and current user
    if (data.staff_id === currentStaff.id) {
        updateStaffStatus(data);
    }
});
```

### Pusher Event Data Structure
```json
{
    "user_id": 456,
    "staff_id": 123,
    "duty_status": "on_break",
    "is_on_duty": true,
    "is_on_break": true,
    "status_label": "On Break",
    "clock_time": "2025-11-30T15:30:00Z",
    "first_name": "John",
    "last_name": "Doe",
    "action": "start_break",
    "department": "Front Desk",
    "department_slug": "front-desk",
    "current_status": {
        "status": "on_break",
        "label": "On Break",
        "is_on_break": true,
        "break_start": "2025-11-30T15:30:00Z",
        "total_break_minutes": 45
    }
}
```

## 💻 Frontend Implementation Examples

### React Component with Real-time Updates

```jsx
import { useState, useEffect } from 'react';
import Pusher from 'pusher-js';

const StaffStatusComponent = ({ hotelSlug, authToken }) => {
    const [staffData, setStaffData] = useState(null);
    const [loading, setLoading] = useState(true);

    // Fetch initial staff data
    useEffect(() => {
        fetchStaffData();
    }, []);

    // Setup Pusher for real-time updates
    useEffect(() => {
        if (!staffData) return;

        const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
            cluster: process.env.REACT_APP_PUSHER_CLUSTER,
            encrypted: true
        });

        const channel = pusher.subscribe(`hotel-${hotelSlug}`);
        
        channel.bind('clock-status-updated', (data) => {
            // Update if this is the current user
            if (data.staff_id === staffData.id) {
                setStaffData(prev => ({
                    ...prev,
                    duty_status: data.duty_status,
                    is_on_duty: data.is_on_duty,
                    current_status: data.current_status
                }));
            }
        });

        return () => {
            channel.unbind_all();
            pusher.unsubscribe(`hotel-${hotelSlug}`);
        };
    }, [staffData, hotelSlug]);

    const fetchStaffData = async () => {
        try {
            const response = await fetch(`/api/staff/hotel/${hotelSlug}/me/`, {
                headers: {
                    'Authorization': `Token ${authToken}`
                }
            });
            const data = await response.json();
            setStaffData(data);
        } catch (error) {
            console.error('Failed to fetch staff data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (dutyStatus) => {
        const statusConfig = {
            off_duty: { color: 'gray', text: 'Off Duty' },
            on_duty: { color: 'green', text: 'On Duty' },
            on_break: { color: 'orange', text: 'On Break' }
        };
        
        return statusConfig[dutyStatus] || statusConfig.off_duty;
    };

    const formatBreakTime = (breakStart) => {
        if (!breakStart) return '';
        const start = new Date(breakStart);
        const now = new Date();
        const minutes = Math.floor((now - start) / 60000);
        return `${minutes} min`;
    };

    if (loading) return <div>Loading...</div>;

    const badge = getStatusBadge(staffData.duty_status);

    return (
        <div className="staff-status-card">
            <div className="staff-info">
                <img 
                    src={staffData.profile_image_url} 
                    alt={`${staffData.first_name} ${staffData.last_name}`}
                />
                <div>
                    <h3>{staffData.first_name} {staffData.last_name}</h3>
                    <p>{staffData.department?.name} - {staffData.role?.name}</p>
                </div>
            </div>
            
            <div className="status-section">
                <span 
                    className={`status-badge status-${badge.color}`}
                >
                    {badge.text}
                </span>
                
                {staffData.duty_status === 'on_break' && staffData.current_status.break_start && (
                    <div className="break-info">
                        <small>
                            Break: {formatBreakTime(staffData.current_status.break_start)}
                        </small>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StaffStatusComponent;
```

### Vue.js Implementation

```vue
<template>
    <div class="staff-status" v-if="staffData">
        <div class="staff-profile">
            <img :src="staffData.profile_image_url" :alt="fullName" />
            <div class="staff-details">
                <h3>{{ fullName }}</h3>
                <p>{{ departmentRole }}</p>
            </div>
        </div>
        
        <div class="status-indicator">
            <span :class="statusClass">{{ statusLabel }}</span>
            <div v-if="isOnBreak" class="break-time">
                Break: {{ breakDuration }}
            </div>
        </div>
    </div>
</template>

<script>
import Pusher from 'pusher-js';

export default {
    name: 'StaffStatusWidget',
    props: {
        hotelSlug: String,
        authToken: String
    },
    data() {
        return {
            staffData: null,
            pusher: null,
            channel: null
        };
    },
    computed: {
        fullName() {
            return `${this.staffData.first_name} ${this.staffData.last_name}`;
        },
        departmentRole() {
            const dept = this.staffData.department?.name || 'No Department';
            const role = this.staffData.role?.name || 'No Role';
            return `${dept} - ${role}`;
        },
        statusLabel() {
            return this.staffData.current_status?.label || 'Unknown';
        },
        statusClass() {
            const status = this.staffData.duty_status;
            return `status-badge status-${status.replace('_', '-')}`;
        },
        isOnBreak() {
            return this.staffData.duty_status === 'on_break';
        },
        breakDuration() {
            if (!this.staffData.current_status?.break_start) return '';
            const start = new Date(this.staffData.current_status.break_start);
            const now = new Date();
            const minutes = Math.floor((now - start) / 60000);
            return `${minutes} min`;
        }
    },
    async mounted() {
        await this.fetchStaffData();
        this.setupPusher();
    },
    beforeDestroy() {
        this.cleanup();
    },
    methods: {
        async fetchStaffData() {
            try {
                const response = await fetch(`/api/staff/hotel/${this.hotelSlug}/me/`, {
                    headers: {
                        'Authorization': `Token ${this.authToken}`
                    }
                });
                this.staffData = await response.json();
            } catch (error) {
                console.error('Failed to fetch staff data:', error);
            }
        },
        setupPusher() {
            if (!this.staffData) return;

            this.pusher = new Pusher(process.env.VUE_APP_PUSHER_KEY, {
                cluster: process.env.VUE_APP_PUSHER_CLUSTER,
                encrypted: true
            });

            this.channel = this.pusher.subscribe(`hotel-${this.hotelSlug}`);
            this.channel.bind('clock-status-updated', this.handleStatusUpdate);
        },
        handleStatusUpdate(data) {
            if (data.staff_id === this.staffData.id) {
                this.staffData = {
                    ...this.staffData,
                    duty_status: data.duty_status,
                    is_on_duty: data.is_on_duty,
                    current_status: data.current_status
                };
            }
        },
        cleanup() {
            if (this.channel) {
                this.channel.unbind_all();
                this.pusher.unsubscribe(`hotel-${this.hotelSlug}`);
            }
        }
    }
};
</script>

<style scoped>
.status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
}

.status-off-duty { background: #e5e7eb; color: #6b7280; }
.status-on-duty { background: #dcfce7; color: #16a34a; }
.status-on-break { background: #fed7aa; color: #ea580c; }

.break-time {
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 4px;
}
</style>
```

## 🎨 CSS Styling Examples

```css
/* Status Badge Styles */
.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.status-off-duty {
    background-color: #f3f4f6;
    color: #6b7280;
    border: 1px solid #d1d5db;
}

.status-on-duty {
    background-color: #dcfce7;
    color: #16a34a;
    border: 1px solid #bbf7d0;
}

.status-on-break {
    background-color: #fed7aa;
    color: #ea580c;
    border: 1px solid #fdba74;
}

/* Staff Status Card */
.staff-status-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 16px;
}

.staff-info {
    display: flex;
    align-items: center;
    gap: 12px;
}

.staff-info img {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    object-fit: cover;
}

.staff-info h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
}

.staff-info p {
    margin: 4px 0 0 0;
    font-size: 0.875rem;
    color: #6b7280;
}

.break-info {
    margin-top: 8px;
}

.break-info small {
    color: #ea580c;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Real-time update animation */
@keyframes pulse-update {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.status-updated {
    animation: pulse-update 0.3s ease-in-out;
}
```

## 📱 Mobile-First Implementation

```javascript
// Mobile-optimized status component
class MobileStaffStatus {
    constructor(hotelSlug, authToken) {
        this.hotelSlug = hotelSlug;
        this.authToken = authToken;
        this.staffData = null;
        this.pusher = null;
        this.init();
    }

    async init() {
        await this.fetchStaffData();
        this.setupPusher();
        this.render();
    }

    async fetchStaffData() {
        try {
            const response = await fetch(`/api/staff/hotel/${this.hotelSlug}/me/`, {
                headers: { 'Authorization': `Token ${this.authToken}` }
            });
            this.staffData = await response.json();
        } catch (error) {
            console.error('Failed to fetch staff data:', error);
        }
    }

    setupPusher() {
        this.pusher = new Pusher(window.PUSHER_KEY, {
            cluster: window.PUSHER_CLUSTER,
            encrypted: true
        });

        const channel = this.pusher.subscribe(`hotel-${this.hotelSlug}`);
        channel.bind('clock-status-updated', (data) => {
            if (data.staff_id === this.staffData.id) {
                this.updateStaffData(data);
                this.render();
                this.showUpdateNotification(data.action);
            }
        });
    }

    updateStaffData(data) {
        this.staffData = {
            ...this.staffData,
            duty_status: data.duty_status,
            is_on_duty: data.is_on_duty,
            current_status: data.current_status
        };
    }

    showUpdateNotification(action) {
        const messages = {
            'clock_in': 'You are now on duty',
            'clock_out': 'You are now off duty',
            'start_break': 'Break started',
            'end_break': 'Break ended - back on duty'
        };

        const message = messages[action] || 'Status updated';
        
        // Show toast notification
        this.showToast(message);
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'status-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    getStatusConfig(dutyStatus) {
        return {
            off_duty: { icon: '⭕', color: '#6b7280', text: 'Off Duty' },
            on_duty: { icon: '✅', color: '#16a34a', text: 'On Duty' },
            on_break: { icon: '☕', color: '#ea580c', text: 'On Break' }
        }[dutyStatus] || { icon: '❓', color: '#6b7280', text: 'Unknown' };
    }

    render() {
        const container = document.getElementById('staff-status-container');
        if (!container || !this.staffData) return;

        const config = this.getStatusConfig(this.staffData.duty_status);
        
        container.innerHTML = `
            <div class="mobile-staff-status">
                <div class="staff-avatar">
                    <img src="${this.staffData.profile_image_url}" 
                         alt="${this.staffData.first_name} ${this.staffData.last_name}" />
                    <span class="status-indicator" style="color: ${config.color}">
                        ${config.icon}
                    </span>
                </div>
                <div class="staff-details">
                    <h3>${this.staffData.first_name} ${this.staffData.last_name}</h3>
                    <p class="department">${this.staffData.department?.name || 'No Department'}</p>
                    <div class="status-row">
                        <span class="status-text" style="color: ${config.color}">
                            ${config.text}
                        </span>
                        ${this.staffData.duty_status === 'on_break' ? 
                            `<span class="break-time">
                                ${this.formatBreakTime(this.staffData.current_status.break_start)}
                            </span>` : ''
                        }
                    </div>
                </div>
            </div>
        `;
    }

    formatBreakTime(breakStart) {
        if (!breakStart) return '';
        const start = new Date(breakStart);
        const now = new Date();
        const minutes = Math.floor((now - start) / 60000);
        return `${minutes}min`;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new MobileStaffStatus(window.HOTEL_SLUG, window.AUTH_TOKEN);
});
```

## 🔧 Error Handling

### Comprehensive Error Handling Example
```javascript
class StaffStatusManager {
    constructor(config) {
        this.config = config;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000;
    }

    async fetchWithRetry() {
        try {
            const response = await fetch(`/api/staff/hotel/${this.config.hotelSlug}/me/`, {
                headers: { 'Authorization': `Token ${this.config.authToken}` }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.retryCount = 0; // Reset on success
            return data;
        } catch (error) {
            console.error('Fetch error:', error);
            
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`Retrying... (${this.retryCount}/${this.maxRetries})`);
                
                await new Promise(resolve => 
                    setTimeout(resolve, this.retryDelay * this.retryCount)
                );
                
                return this.fetchWithRetry();
            }
            
            throw error;
        }
    }

    setupPusherWithFallback() {
        try {
            this.pusher = new Pusher(this.config.pusherKey, {
                cluster: this.config.pusherCluster,
                encrypted: true,
                enabledTransports: ['ws', 'wss'],
                disabledTransports: []
            });

            this.pusher.connection.bind('error', (error) => {
                console.error('Pusher connection error:', error);
                this.handlePusherError(error);
            });

            this.pusher.connection.bind('disconnected', () => {
                console.warn('Pusher disconnected, attempting to reconnect...');
                setTimeout(() => {
                    this.pusher.connect();
                }, 5000);
            });

            const channel = this.pusher.subscribe(`hotel-${this.config.hotelSlug}`);
            
            channel.bind('pusher:subscription_error', (error) => {
                console.error('Channel subscription error:', error);
                this.fallbackToPolling();
            });

            return channel;
        } catch (error) {
            console.error('Pusher setup failed:', error);
            this.fallbackToPolling();
        }
    }

    fallbackToPolling() {
        console.log('Falling back to polling for updates...');
        
        // Poll every 30 seconds as fallback
        this.pollingInterval = setInterval(async () => {
            try {
                const data = await this.fetchWithRetry();
                this.updateUI(data);
            } catch (error) {
                console.error('Polling failed:', error);
            }
        }, 30000);
    }

    handlePusherError(error) {
        if (error.error && error.error.data && error.error.data.code === 4004) {
            console.error('Pusher: Over connection limit');
            this.fallbackToPolling();
        }
    }

    cleanup() {
        if (this.pusher) {
            this.pusher.disconnect();
        }
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
    }
}
```

## 🚀 Performance Tips

1. **Debounce Updates**: Prevent excessive re-renders during rapid status changes
2. **Connection Pooling**: Reuse Pusher connections across components
3. **Local Caching**: Cache staff data in localStorage for offline scenarios
4. **Lazy Loading**: Load status data only when component is visible
5. **Batch Updates**: Group multiple status updates together

## 📋 Checklist for Implementation

- [ ] Set up authentication with proper token handling
- [ ] Initialize Pusher connection with error handling
- [ ] Subscribe to hotel-specific channels
- [ ] Implement status badge UI with proper colors
- [ ] Handle break time display and formatting
- [ ] Add real-time update animations
- [ ] Test offline scenarios and fallbacks
- [ ] Implement proper cleanup on component unmount
- [ ] Add accessibility features (ARIA labels, keyboard navigation)
- [ ] Test on mobile devices and different screen sizes

## 🔍 Troubleshooting

### Common Issues
1. **Token Expires**: Implement token refresh logic
2. **Pusher Connection Fails**: Always have polling fallback
3. **Status Not Updating**: Check Pusher channel subscription
4. **Break Time Wrong**: Ensure proper timezone handling
5. **UI Flickering**: Debounce status updates

### Debug Commands
```javascript
// Check current staff data
console.log('Staff Data:', staffData);

// Verify Pusher connection
console.log('Pusher State:', pusher.connection.state);

// Test API endpoint
fetch('/api/staff/hotel/your-hotel/me/', {
    headers: { 'Authorization': 'Token your_token' }
}).then(r => r.json()).then(console.log);
```

This guide provides everything needed to implement the enhanced `/me` endpoint with real-time duty status updates in your frontend application.
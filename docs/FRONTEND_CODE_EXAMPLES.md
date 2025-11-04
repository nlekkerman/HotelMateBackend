# Frontend Code Examples - Multiple Frameworks

## 🎨 Implementation Examples for Popular Frameworks

This document provides ready-to-use code examples for React, Vue.js, and vanilla JavaScript.

---

## 📱 React / React Native Examples

### Complete React Component

```jsx
// BreakfastOrderSystem.jsx
import React, { useState, useEffect } from 'react';
import Pusher from 'pusher-js';

const API_BASE = 'https://your-backend.com/room_services';

const BreakfastOrderSystem = () => {
  const [step, setStep] = useState('loading'); // loading, pin, menu, checkout, confirmation
  const [hotelSlug, setHotelSlug] = useState(null);
  const [roomNumber, setRoomNumber] = useState(null);
  const [menuItems, setMenuItems] = useState({});
  const [cart, setCart] = useState([]);
  const [order, setOrder] = useState(null);
  const [deliveryTime, setDeliveryTime] = useState('');
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // Parse QR code from URL or props
    const urlParams = new URLSearchParams(window.location.search);
    const slug = urlParams.get('hotel');
    const room = urlParams.get('room');
    
    if (slug && room) {
      setHotelSlug(slug);
      setRoomNumber(room);
      setStep('pin');
    }
  }, []);

  const validatePin = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/${hotelSlug}/room/${roomNumber}/validate-pin/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin: pin.toLowerCase() })
        }
      );

      const data = await response.json();
      
      if (data.valid) {
        sessionStorage.setItem('guestPin', pin);
        await loadMenu();
        setStep('menu');
        setError('');
      } else {
        setError('Invalid PIN. Please try again.');
        setPin('');
      }
    } catch (err) {
      setError('Connection error. Please try again.');
    }
  };

  const loadMenu = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/${hotelSlug}/room/${roomNumber}/breakfast/`
      );
      const items = await response.json();
      
      // Group by category
      const grouped = items.reduce((acc, item) => {
        if (item.is_on_stock) {
          if (!acc[item.category]) acc[item.category] = [];
          acc[item.category].push(item);
        }
        return acc;
      }, {});
      
      setMenuItems(grouped);
    } catch (err) {
      setError('Failed to load menu');
    }
  };

  const addToCart = (item) => {
    setCart(prev => {
      const existing = prev.find(i => i.item_id === item.id);
      if (existing) {
        return prev.map(i => 
          i.item_id === item.id 
            ? { ...i, quantity: i.quantity + 1 }
            : i
        );
      }
      return [...prev, { item_id: item.id, quantity: 1, item }];
    });
  };

  const updateQuantity = (itemId, quantity) => {
    if (quantity === 0) {
      setCart(prev => prev.filter(i => i.item_id !== itemId));
    } else {
      setCart(prev => prev.map(i => 
        i.item_id === itemId ? { ...i, quantity } : i
      ));
    }
  };

  const submitOrder = async () => {
    try {
      const orderData = {
        room_number: parseInt(roomNumber),
        delivery_time: deliveryTime,
        items: cart.map(item => ({
          item_id: item.item_id,
          quantity: item.quantity
        }))
      };

      const response = await fetch(
        `${API_BASE}/${hotelSlug}/breakfast-orders/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(orderData)
        }
      );

      if (!response.ok) throw new Error('Order failed');

      const newOrder = await response.json();
      setOrder(newOrder);
      setCart([]);
      setStep('confirmation');
      
      // Subscribe to order updates
      subscribeToOrderUpdates(newOrder.id);
    } catch (err) {
      setError('Failed to place order. Please try again.');
    }
  };

  const subscribeToOrderUpdates = (orderId) => {
    const pusher = new Pusher(process.env.REACT_APP_PUSHER_KEY, {
      cluster: process.env.REACT_APP_PUSHER_CLUSTER
    });

    const channel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}`);
    
    channel.bind('order-status-update', (data) => {
      if (data.updated_order_id === orderId) {
        setOrder(prev => ({ ...prev, status: data.new_status }));
      }
    });
  };

  // Render different steps
  if (step === 'pin') {
    return (
      <div className="pin-screen">
        <h2>Welcome to Room {roomNumber}</h2>
        <p>Enter your 4-character PIN to order breakfast</p>
        <input
          type="text"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          maxLength={4}
          placeholder="PIN"
        />
        {error && <p className="error">{error}</p>}
        <button onClick={validatePin} disabled={pin.length !== 4}>
          Verify
        </button>
      </div>
    );
  }

  if (step === 'menu') {
    return (
      <div className="menu-screen">
        <h1>Breakfast Menu</h1>
        {Object.entries(menuItems).map(([category, items]) => (
          <div key={category}>
            <h2>{category}</h2>
            <div className="items-grid">
              {items.map(item => (
                <div key={item.id} className="menu-item">
                  <img src={item.image} alt={item.name} />
                  <h3>{item.name}</h3>
                  <p>{item.description}</p>
                  <button onClick={() => addToCart(item)}>Add</button>
                </div>
              ))}
            </div>
          </div>
        ))}
        
        {cart.length > 0 && (
          <div className="cart-summary">
            <h3>Your Order</h3>
            {cart.map(item => (
              <div key={item.item_id}>
                <span>{item.item.name}</span>
                <input
                  type="number"
                  value={item.quantity}
                  onChange={(e) => updateQuantity(item.item_id, parseInt(e.target.value))}
                  min="0"
                />
              </div>
            ))}
            <button onClick={() => setStep('checkout')}>
              Proceed to Checkout
            </button>
          </div>
        )}
      </div>
    );
  }

  if (step === 'checkout') {
    return (
      <div className="checkout-screen">
        <h2>Complete Your Order</h2>
        
        <div className="order-summary">
          {cart.map(item => (
            <div key={item.item_id}>
              <span>{item.item.name} x{item.quantity}</span>
            </div>
          ))}
        </div>

        <select 
          value={deliveryTime} 
          onChange={(e) => setDeliveryTime(e.target.value)}
        >
          <option value="">Select delivery time</option>
          <option value="7:00-8:00">7:00 AM - 8:00 AM</option>
          <option value="8:00-8:30">8:00 AM - 8:30 AM</option>
          <option value="8:30-9:00">8:30 AM - 9:00 AM</option>
          <option value="9:00-9:30">9:00 AM - 9:30 AM</option>
          <option value="9:30-10:00">9:30 AM - 10:00 AM</option>
          <option value="10:00-10:30">10:00 AM - 10:30 AM</option>
        </select>

        {error && <p className="error">{error}</p>}

        <button 
          onClick={submitOrder}
          disabled={!deliveryTime}
        >
          Place Order
        </button>
      </div>
    );
  }

  if (step === 'confirmation') {
    return (
      <div className="confirmation-screen">
        <div className="success-icon">✓</div>
        <h2>Order Confirmed!</h2>
        <p>Order #{order.id}</p>
        <p>Delivery: {order.delivery_time}</p>
        <p>Status: <StatusBadge status={order.status} /></p>
      </div>
    );
  }

  return <div>Loading...</div>;
};

const StatusBadge = ({ status }) => {
  const colors = {
    pending: 'orange',
    accepted: 'blue',
    completed: 'green'
  };

  return (
    <span style={{ 
      backgroundColor: colors[status], 
      color: 'white',
      padding: '4px 8px',
      borderRadius: '4px'
    }}>
      {status.toUpperCase()}
    </span>
  );
};

export default BreakfastOrderSystem;
```

---

## 🌿 Vue.js 3 Example

### Complete Vue Component

```vue
<!-- BreakfastOrder.vue -->
<template>
  <div class="breakfast-order">
    <!-- PIN Validation -->
    <div v-if="step === 'pin'" class="pin-screen">
      <h2>Welcome to Room {{ roomNumber }}</h2>
      <p>Enter your PIN to order breakfast</p>
      <input
        v-model="pin"
        type="text"
        maxlength="4"
        placeholder="Enter PIN"
        @keyup.enter="validatePin"
      />
      <p v-if="error" class="error">{{ error }}</p>
      <button @click="validatePin" :disabled="pin.length !== 4">
        Verify
      </button>
    </div>

    <!-- Menu Display -->
    <div v-if="step === 'menu'" class="menu-screen">
      <h1>Breakfast Menu</h1>
      
      <div v-for="(items, category) in menuItems" :key="category">
        <h2>{{ category }}</h2>
        <div class="items-grid">
          <div 
            v-for="item in items" 
            :key="item.id"
            class="menu-item"
          >
            <img :src="item.image" :alt="item.name" />
            <h3>{{ item.name }}</h3>
            <p>{{ item.description }}</p>
            <button @click="addToCart(item)">Add to Cart</button>
          </div>
        </div>
      </div>

      <!-- Cart Summary -->
      <div v-if="cart.length > 0" class="cart-summary">
        <h3>Your Order</h3>
        <div v-for="cartItem in cart" :key="cartItem.item_id">
          <span>{{ cartItem.item.name }}</span>
          <input
            v-model.number="cartItem.quantity"
            type="number"
            min="0"
            @change="updateCart"
          />
        </div>
        <button @click="step = 'checkout'">Checkout</button>
      </div>
    </div>

    <!-- Checkout -->
    <div v-if="step === 'checkout'" class="checkout-screen">
      <h2>Complete Your Order</h2>
      
      <div class="order-summary">
        <div v-for="item in cart" :key="item.item_id">
          {{ item.item.name }} x{{ item.quantity }}
        </div>
      </div>

      <select v-model="deliveryTime">
        <option value="">Select delivery time</option>
        <option value="7:00-8:00">7:00 AM - 8:00 AM</option>
        <option value="8:00-8:30">8:00 AM - 8:30 AM</option>
        <option value="8:30-9:00">8:30 AM - 9:00 AM</option>
        <option value="9:00-9:30">9:00 AM - 9:30 AM</option>
        <option value="9:30-10:00">9:30 AM - 10:00 AM</option>
        <option value="10:00-10:30">10:00 AM - 10:30 AM</option>
      </select>

      <p v-if="error" class="error">{{ error }}</p>

      <button @click="submitOrder" :disabled="!deliveryTime">
        Place Order
      </button>
    </div>

    <!-- Confirmation -->
    <div v-if="step === 'confirmation'" class="confirmation-screen">
      <div class="success-icon">✓</div>
      <h2>Order Confirmed!</h2>
      <p>Order #{{ order.id }}</p>
      <p>Delivery: {{ order.delivery_time }}</p>
      <p>Status: <span :class="`status-${order.status}`">
        {{ order.status.toUpperCase() }}
      </span></p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import Pusher from 'pusher-js';

const API_BASE = 'https://your-backend.com/room_services';

const step = ref('loading');
const hotelSlug = ref(null);
const roomNumber = ref(null);
const menuItems = ref({});
const cart = ref([]);
const order = ref(null);
const deliveryTime = ref('');
const pin = ref('');
const error = ref('');

onMounted(() => {
  // Parse from URL
  const urlParams = new URLSearchParams(window.location.search);
  hotelSlug.value = urlParams.get('hotel');
  roomNumber.value = urlParams.get('room');
  
  if (hotelSlug.value && roomNumber.value) {
    step.value = 'pin';
  }
});

const validatePin = async () => {
  try {
    const response = await fetch(
      `${API_BASE}/${hotelSlug.value}/room/${roomNumber.value}/validate-pin/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin: pin.value.toLowerCase() })
      }
    );

    const data = await response.json();
    
    if (data.valid) {
      sessionStorage.setItem('guestPin', pin.value);
      await loadMenu();
      step.value = 'menu';
      error.value = '';
    } else {
      error.value = 'Invalid PIN. Please try again.';
      pin.value = '';
    }
  } catch (err) {
    error.value = 'Connection error. Please try again.';
  }
};

const loadMenu = async () => {
  try {
    const response = await fetch(
      `${API_BASE}/${hotelSlug.value}/room/${roomNumber.value}/breakfast/`
    );
    const items = await response.json();
    
    // Group by category
    const grouped = items.reduce((acc, item) => {
      if (item.is_on_stock) {
        if (!acc[item.category]) acc[item.category] = [];
        acc[item.category].push(item);
      }
      return acc;
    }, {});
    
    menuItems.value = grouped;
  } catch (err) {
    error.value = 'Failed to load menu';
  }
};

const addToCart = (item) => {
  const existing = cart.value.find(i => i.item_id === item.id);
  if (existing) {
    existing.quantity++;
  } else {
    cart.value.push({
      item_id: item.id,
      quantity: 1,
      item: item
    });
  }
};

const updateCart = () => {
  cart.value = cart.value.filter(item => item.quantity > 0);
};

const submitOrder = async () => {
  try {
    const orderData = {
      room_number: parseInt(roomNumber.value),
      delivery_time: deliveryTime.value,
      items: cart.value.map(item => ({
        item_id: item.item_id,
        quantity: item.quantity
      }))
    };

    const response = await fetch(
      `${API_BASE}/${hotelSlug.value}/breakfast-orders/`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      }
    );

    if (!response.ok) throw new Error('Order failed');

    const newOrder = await response.json();
    order.value = newOrder;
    cart.value = [];
    step.value = 'confirmation';
    
    subscribeToOrderUpdates(newOrder.id);
  } catch (err) {
    error.value = 'Failed to place order. Please try again.';
  }
};

const subscribeToOrderUpdates = (orderId) => {
  const pusher = new Pusher(import.meta.env.VITE_PUSHER_KEY, {
    cluster: import.meta.env.VITE_PUSHER_CLUSTER
  });

  const channel = pusher.subscribe(
    `${hotelSlug.value}-room-${roomNumber.value}`
  );
  
  channel.bind('order-status-update', (data) => {
    if (data.updated_order_id === orderId) {
      order.value.status = data.new_status;
    }
  });
};
</script>

<style scoped>
.breakfast-order {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.menu-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin: 10px 0;
}

.menu-item img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  border-radius: 4px;
}

.cart-summary {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 2px solid #333;
  padding: 20px;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}

.error {
  color: red;
  margin: 10px 0;
}

.status-pending { color: orange; }
.status-accepted { color: blue; }
.status-completed { color: green; }
</style>
```

---

## 🍦 Vanilla JavaScript Example

### Vanilla JS Implementation

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Breakfast Order</title>
  <script src="https://js.pusher.com/7.2/pusher.min.js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
    }
    .hidden { display: none; }
    .menu-item {
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 16px;
      margin: 10px 0;
    }
    .menu-item img {
      width: 100%;
      max-height: 200px;
      object-fit: cover;
    }
    button {
      background: #007bff;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
    }
    button:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
    .error {
      color: red;
      margin: 10px 0;
    }
    .cart-summary {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: white;
      border-top: 2px solid #333;
      padding: 20px;
      box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
    }
  </style>
</head>
<body>
  <!-- PIN Screen -->
  <div id="pin-screen" class="hidden">
    <h2>Welcome to Room <span id="room-display"></span></h2>
    <p>Enter your 4-character PIN to order breakfast</p>
    <input type="text" id="pin-input" maxlength="4" placeholder="PIN" />
    <p id="pin-error" class="error hidden"></p>
    <button id="pin-submit" disabled>Verify</button>
  </div>

  <!-- Menu Screen -->
  <div id="menu-screen" class="hidden">
    <h1>Breakfast Menu</h1>
    <div id="menu-container"></div>
    <div id="cart-summary" class="cart-summary hidden">
      <h3>Your Order</h3>
      <div id="cart-items"></div>
      <button id="checkout-btn">Checkout</button>
    </div>
  </div>

  <!-- Checkout Screen -->
  <div id="checkout-screen" class="hidden">
    <h2>Complete Your Order</h2>
    <div id="checkout-summary"></div>
    <select id="delivery-time">
      <option value="">Select delivery time</option>
      <option value="7:00-8:00">7:00 AM - 8:00 AM</option>
      <option value="8:00-8:30">8:00 AM - 8:30 AM</option>
      <option value="8:30-9:00">8:30 AM - 9:00 AM</option>
      <option value="9:00-9:30">9:00 AM - 9:30 AM</option>
      <option value="9:30-10:00">9:30 AM - 10:00 AM</option>
      <option value="10:00-10:30">10:00 AM - 10:30 AM</option>
    </select>
    <p id="checkout-error" class="error hidden"></p>
    <button id="place-order-btn" disabled>Place Order</button>
  </div>

  <!-- Confirmation Screen -->
  <div id="confirmation-screen" class="hidden">
    <div style="font-size: 48px; color: green;">✓</div>
    <h2>Order Confirmed!</h2>
    <p>Order #<span id="order-id"></span></p>
    <p>Delivery: <span id="order-time"></span></p>
    <p>Status: <span id="order-status"></span></p>
  </div>

  <script>
    const API_BASE = 'https://your-backend.com/room_services';
    const PUSHER_KEY = 'your-pusher-key';
    const PUSHER_CLUSTER = 'your-cluster';

    let hotelSlug, roomNumber;
    let cart = [];
    let currentOrder = null;

    // Initialize
    window.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      hotelSlug = urlParams.get('hotel');
      roomNumber = urlParams.get('room');

      if (hotelSlug && roomNumber) {
        showScreen('pin-screen');
        document.getElementById('room-display').textContent = roomNumber;
        setupPinScreen();
      }
    });

    function showScreen(screenId) {
      ['pin-screen', 'menu-screen', 'checkout-screen', 'confirmation-screen']
        .forEach(id => {
          document.getElementById(id).classList.add('hidden');
        });
      document.getElementById(screenId).classList.remove('hidden');
    }

    function setupPinScreen() {
      const input = document.getElementById('pin-input');
      const button = document.getElementById('pin-submit');

      input.addEventListener('input', () => {
        button.disabled = input.value.length !== 4;
      });

      button.addEventListener('click', validatePin);
    }

    async function validatePin() {
      const pin = document.getElementById('pin-input').value.toLowerCase();
      const errorEl = document.getElementById('pin-error');

      try {
        const response = await fetch(
          `${API_BASE}/${hotelSlug}/room/${roomNumber}/validate-pin/`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin })
          }
        );

        const data = await response.json();

        if (data.valid) {
          sessionStorage.setItem('guestPin', pin);
          errorEl.classList.add('hidden');
          await loadMenu();
          showScreen('menu-screen');
        } else {
          errorEl.textContent = 'Invalid PIN. Please try again.';
          errorEl.classList.remove('hidden');
          document.getElementById('pin-input').value = '';
        }
      } catch (err) {
        errorEl.textContent = 'Connection error. Please try again.';
        errorEl.classList.remove('hidden');
      }
    }

    async function loadMenu() {
      try {
        const response = await fetch(
          `${API_BASE}/${hotelSlug}/room/${roomNumber}/breakfast/`
        );
        const items = await response.json();

        // Group by category
        const grouped = items.reduce((acc, item) => {
          if (item.is_on_stock) {
            if (!acc[item.category]) acc[item.category] = [];
            acc[item.category].push(item);
          }
          return acc;
        }, {});

        displayMenu(grouped);
      } catch (err) {
        console.error('Failed to load menu:', err);
      }
    }

    function displayMenu(menuItems) {
      const container = document.getElementById('menu-container');
      container.innerHTML = '';

      Object.entries(menuItems).forEach(([category, items]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.innerHTML = `<h2>${category}</h2>`;

        items.forEach(item => {
          const itemDiv = document.createElement('div');
          itemDiv.className = 'menu-item';
          itemDiv.innerHTML = `
            <img src="${item.image}" alt="${item.name}" />
            <h3>${item.name}</h3>
            <p>${item.description}</p>
            <button onclick="addToCart(${JSON.stringify(item).replace(/"/g, '&quot;')})">
              Add to Cart
            </button>
          `;
          categoryDiv.appendChild(itemDiv);
        });

        container.appendChild(categoryDiv);
      });

      document.getElementById('checkout-btn').addEventListener('click', () => {
        showCheckout();
      });
    }

    function addToCart(item) {
      const existing = cart.find(i => i.item_id === item.id);
      if (existing) {
        existing.quantity++;
      } else {
        cart.push({ item_id: item.id, quantity: 1, item });
      }
      updateCartDisplay();
    }

    function updateCartDisplay() {
      const cartEl = document.getElementById('cart-items');
      const summaryEl = document.getElementById('cart-summary');

      if (cart.length === 0) {
        summaryEl.classList.add('hidden');
        return;
      }

      summaryEl.classList.remove('hidden');
      cartEl.innerHTML = cart.map(item => `
        <div>
          ${item.item.name} x
          <input 
            type="number" 
            value="${item.quantity}" 
            min="0"
            onchange="updateQuantity(${item.item_id}, this.value)"
            style="width: 50px;"
          />
        </div>
      `).join('');
    }

    function updateQuantity(itemId, quantity) {
      const qty = parseInt(quantity);
      if (qty === 0) {
        cart = cart.filter(i => i.item_id !== itemId);
      } else {
        const item = cart.find(i => i.item_id === itemId);
        if (item) item.quantity = qty;
      }
      updateCartDisplay();
    }

    function showCheckout() {
      const summaryEl = document.getElementById('checkout-summary');
      summaryEl.innerHTML = cart.map(item => `
        <div>${item.item.name} x${item.quantity}</div>
      `).join('');

      const timeSelect = document.getElementById('delivery-time');
      const placeOrderBtn = document.getElementById('place-order-btn');

      timeSelect.addEventListener('change', () => {
        placeOrderBtn.disabled = !timeSelect.value;
      });

      placeOrderBtn.addEventListener('click', submitOrder);

      showScreen('checkout-screen');
    }

    async function submitOrder() {
      const deliveryTime = document.getElementById('delivery-time').value;
      const errorEl = document.getElementById('checkout-error');

      try {
        const orderData = {
          room_number: parseInt(roomNumber),
          delivery_time: deliveryTime,
          items: cart.map(item => ({
            item_id: item.item_id,
            quantity: item.quantity
          }))
        };

        const response = await fetch(
          `${API_BASE}/${hotelSlug}/breakfast-orders/`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData)
          }
        );

        if (!response.ok) throw new Error('Order failed');

        const order = await response.json();
        currentOrder = order;
        cart = [];

        document.getElementById('order-id').textContent = order.id;
        document.getElementById('order-time').textContent = order.delivery_time;
        document.getElementById('order-status').textContent = order.status.toUpperCase();

        showScreen('confirmation-screen');
        subscribeToOrderUpdates(order.id);

      } catch (err) {
        errorEl.textContent = 'Failed to place order. Please try again.';
        errorEl.classList.remove('hidden');
      }
    }

    function subscribeToOrderUpdates(orderId) {
      const pusher = new Pusher(PUSHER_KEY, { cluster: PUSHER_CLUSTER });
      const channel = pusher.subscribe(`${hotelSlug}-room-${roomNumber}`);

      channel.bind('order-status-update', (data) => {
        if (data.updated_order_id === orderId) {
          document.getElementById('order-status').textContent = 
            data.new_status.toUpperCase();
        }
      });
    }

    // Make functions globally accessible
    window.addToCart = addToCart;
    window.updateQuantity = updateQuantity;
  </script>
</body>
</html>
```

---

## 📱 React Native Example (Bonus)

```jsx
// BreakfastOrderScreen.js
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Button,
  FlatList,
  Image,
  StyleSheet,
  Alert
} from 'react-native';
import { Camera } from 'expo-camera';

const API_BASE = 'https://your-backend.com/room_services';

export default function BreakfastOrderScreen({ navigation, route }) {
  const [step, setStep] = useState('scan'); // scan, pin, menu, checkout, confirmation
  const [hotelSlug, setHotelSlug] = useState(null);
  const [roomNumber, setRoomNumber] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [cart, setCart] = useState([]);
  const [pin, setPin] = useState('');
  const [deliveryTime, setDeliveryTime] = useState('');

  const handleQRScan = ({ data }) => {
    // Parse QR code URL
    const match = data.match(/room_services\/([^/]+)\/room\/(\d+)\/breakfast/);
    if (match) {
      setHotelSlug(match[1]);
      setRoomNumber(match[2]);
      setStep('pin');
    }
  };

  const validatePin = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/${hotelSlug}/room/${roomNumber}/validate-pin/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pin: pin.toLowerCase() })
        }
      );

      const data = await response.json();

      if (data.valid) {
        await loadMenu();
        setStep('menu');
      } else {
        Alert.alert('Error', 'Invalid PIN');
        setPin('');
      }
    } catch (err) {
      Alert.alert('Error', 'Connection failed');
    }
  };

  const loadMenu = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/${hotelSlug}/room/${roomNumber}/breakfast/`
      );
      const items = await response.json();
      setMenuItems(items.filter(item => item.is_on_stock));
    } catch (err) {
      Alert.alert('Error', 'Failed to load menu');
    }
  };

  const addToCart = (item) => {
    setCart(prev => {
      const existing = prev.find(i => i.item_id === item.id);
      if (existing) {
        return prev.map(i => 
          i.item_id === item.id 
            ? { ...i, quantity: i.quantity + 1 }
            : i
        );
      }
      return [...prev, { item_id: item.id, quantity: 1, item }];
    });
  };

  const submitOrder = async () => {
    try {
      const orderData = {
        room_number: parseInt(roomNumber),
        delivery_time: deliveryTime,
        items: cart.map(item => ({
          item_id: item.item_id,
          quantity: item.quantity
        }))
      };

      const response = await fetch(
        `${API_BASE}/${hotelSlug}/breakfast-orders/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(orderData)
        }
      );

      if (!response.ok) throw new Error('Order failed');

      const order = await response.json();
      Alert.alert('Success', `Order #${order.id} placed!`);
      setCart([]);
      setStep('confirmation');
    } catch (err) {
      Alert.alert('Error', 'Failed to place order');
    }
  };

  if (step === 'scan') {
    return (
      <View style={styles.container}>
        <Camera 
          style={styles.camera}
          onBarCodeScanned={handleQRScan}
        />
      </View>
    );
  }

  if (step === 'pin') {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Room {roomNumber}</Text>
        <Text>Enter your PIN</Text>
        <TextInput
          style={styles.input}
          value={pin}
          onChangeText={setPin}
          maxLength={4}
          placeholder="PIN"
          autoCapitalize="none"
        />
        <Button 
          title="Verify" 
          onPress={validatePin}
          disabled={pin.length !== 4}
        />
      </View>
    );
  }

  if (step === 'menu') {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Breakfast Menu</Text>
        <FlatList
          data={menuItems}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <View style={styles.menuItem}>
              <Image source={{ uri: item.image }} style={styles.itemImage} />
              <Text style={styles.itemName}>{item.name}</Text>
              <Text>{item.description}</Text>
              <Button title="Add" onPress={() => addToCart(item)} />
            </View>
          )}
        />
        {cart.length > 0 && (
          <Button 
            title={`Checkout (${cart.length} items)`}
            onPress={() => setStep('checkout')}
          />
        )}
      </View>
    );
  }

  // Add checkout and confirmation screens similarly...

  return <View><Text>Loading...</Text></View>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 10,
    marginVertical: 10,
    borderRadius: 4
  },
  menuItem: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 16,
    marginBottom: 10
  },
  itemImage: {
    width: '100%',
    height: 150,
    borderRadius: 4
  },
  itemName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginVertical: 8
  },
  camera: {
    flex: 1
  }
});
```

---

**You now have complete code examples for all major frameworks! 🎉**

Choose the one that fits your tech stack and customize as needed.

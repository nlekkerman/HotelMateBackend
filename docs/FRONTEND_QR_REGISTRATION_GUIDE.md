# Frontend Integration Guide: QR Code Staff Registration System

## 📋 Overview

We've implemented a **two-factor registration security system** for staff onboarding that combines registration codes with QR codes. This prevents unauthorized registrations and ensures that only employees who receive the complete registration package can create accounts.

---

## 🎯 What Changed and Why

### **Problem We Solved**
Previously, registration codes could be shared or leaked, allowing unauthorized registrations. Anyone with just the code could register.

### **New Solution**
Now, staff registration requires **BOTH**:
1. **Registration Code** (manually entered by user)
2. **QR Token** (embedded in QR code URL, automatically captured when QR is scanned)

Even if someone obtains just the QR code OR just the registration code, they **cannot register** without both pieces.

---

## 🔧 Backend Changes Summary

### **1. Database Changes**
- `RegistrationCode` model now includes:
  - `qr_token` - Unique cryptographic token (32 bytes)
  - `qr_code_url` - Cloudinary URL of the generated QR code image

### **2. New API Endpoint**
**Endpoint:** `POST /api/staff/registration-package/`

**Purpose:** Generate registration package for new employees

**Authentication:** Required (only staff admins and super staff admins)

**Request:**
```json
{
  "hotel_slug": "grand-plaza",
  "code": "STAFF2024"  // Optional: provide specific code, otherwise auto-generated
}
```

**Response:**
```json
{
  "registration_code": "STAFF2024",
  "qr_token": "xJ8kL9mN...", // Hidden from UI, embedded in QR
  "qr_code_url": "https://res.cloudinary.com/.../qr_code.png",
  "hotel_slug": "grand-plaza",
  "hotel_name": "Grand Plaza Hotel",
  "message": "Registration package created successfully...",
  "package_details": {
    "id": 123,
    "code": "STAFF2024",
    "hotel_slug": "grand-plaza",
    "qr_token": "xJ8kL9mN...",
    "qr_code_url": "https://res.cloudinary.com/.../qr_code.png",
    "created_at": "2025-11-03T12:00:00Z",
    "used_at": null,
    "used_by": null
  }
}
```

**GET Endpoint:** `GET /api/staff/registration-package/`
- Returns all registration codes for the authenticated user's hotel

### **3. Updated Registration Logic**
**Endpoint:** `POST /api/staff/register/` *(modified)*

**New Request Format:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123!",
  "registration_code": "STAFF2024",  // User enters manually
  "qr_token": "xJ8kL9mN..."          // From QR code URL
}
```

**Validation:**
- If registration code has a `qr_token` → both code AND token must match
- Old codes without tokens → still work with just the code (backward compatible)

---

## 🎨 Frontend Implementation Requirements

### **1. Add to Hotel Settings Page (Settings.jsx)**

Create a new section in the hotel settings page for **"Staff Registration Management"**

#### **Component Structure:**

```jsx
// Settings.jsx or new component: StaffRegistrationManager.jsx

import React, { useState } from 'react';
import axios from 'axios';

const StaffRegistrationManager = ({ hotelSlug }) => {
  const [loading, setLoading] = useState(false);
  const [registrationPackage, setRegistrationPackage] = useState(null);
  const [customCode, setCustomCode] = useState('');

  const generateRegistrationPackage = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/staff/registration-package/', {
        hotel_slug: hotelSlug,
        code: customCode || undefined, // Optional custom code
      }, {
        headers: {
          Authorization: `Token ${localStorage.getItem('authToken')}`
        }
      });
      
      setRegistrationPackage(response.data);
      setCustomCode(''); // Reset input
    } catch (error) {
      console.error('Error generating registration package:', error);
      alert(error.response?.data?.error || 'Failed to generate package');
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = () => {
    if (registrationPackage?.qr_code_url) {
      // Open QR code in new tab for download
      window.open(registrationPackage.qr_code_url, '_blank');
    }
  };

  const printRegistrationPackage = () => {
    // Create printable version with both code and QR
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write(`
      <html>
        <head>
          <title>Staff Registration Package</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
            .header { margin-bottom: 30px; }
            .code-section { margin: 30px 0; padding: 20px; background: #f0f0f0; border-radius: 8px; }
            .code { font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #2196F3; }
            .qr-section { margin: 30px 0; }
            .instructions { text-align: left; margin-top: 40px; padding: 20px; background: #fff3cd; border-left: 4px solid #ffc107; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>${registrationPackage.hotel_name}</h1>
            <h2>Staff Registration Package</h2>
          </div>
          
          <div class="code-section">
            <h3>Registration Code</h3>
            <div class="code">${registrationPackage.registration_code}</div>
          </div>
          
          <div class="qr-section">
            <h3>Scan QR Code to Register</h3>
            <img src="${registrationPackage.qr_code_url}" alt="QR Code" style="max-width: 300px;" />
          </div>
          
          <div class="instructions">
            <h3>Instructions for New Employee:</h3>
            <ol>
              <li>Scan the QR code above with your mobile device</li>
              <li>This will open the registration page</li>
              <li>Enter the registration code shown above</li>
              <li>Complete your account details</li>
              <li>Submit to create your account</li>
            </ol>
            <p><strong>⚠ Security Note:</strong> Both the QR code and registration code are required to complete registration.</p>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  return (
    <div className="staff-registration-manager">
      <h2>Staff Registration Management</h2>
      <p>Generate registration packages for new employees</p>
      
      <div className="generate-section">
        <input
          type="text"
          placeholder="Custom code (optional)"
          value={customCode}
          onChange={(e) => setCustomCode(e.target.value.toUpperCase())}
          maxLength={20}
        />
        <button onClick={generateRegistrationPackage} disabled={loading}>
          {loading ? 'Generating...' : 'Generate New Package'}
        </button>
      </div>

      {registrationPackage && (
        <div className="package-display">
          <h3>✅ Registration Package Created</h3>
          
          <div className="package-info">
            <div className="code-display">
              <h4>Registration Code</h4>
              <div className="code">{registrationPackage.registration_code}</div>
              <button onClick={() => {
                navigator.clipboard.writeText(registrationPackage.registration_code);
                alert('Code copied to clipboard!');
              }}>
                📋 Copy Code
              </button>
            </div>

            <div className="qr-display">
              <h4>QR Code</h4>
              <img 
                src={registrationPackage.qr_code_url} 
                alt="Registration QR Code" 
                style={{ maxWidth: '250px' }}
              />
              <div className="qr-actions">
                <button onClick={downloadQRCode}>⬇️ Download QR</button>
                <button onClick={printRegistrationPackage}>🖨️ Print Package</button>
              </div>
            </div>
          </div>

          <div className="warning-box">
            <strong>⚠️ Important:</strong> Provide BOTH the registration code and QR code to the new employee. 
            They need both to complete registration.
          </div>
        </div>
      )}
    </div>
  );
};

export default StaffRegistrationManager;
```

#### **Add to Settings.jsx:**

```jsx
// In your Settings.jsx file, add this section:

import StaffRegistrationManager from './components/StaffRegistrationManager';

// Inside your Settings component:
<section>
  <h2>Staff Registration</h2>
  <StaffRegistrationManager hotelSlug={currentHotel.slug} />
</section>
```

---

### **2. Update Registration Page (Register.jsx)**

Modify the registration page to handle QR code scanning:

```jsx
// Register.jsx

import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

const Register = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    registration_code: '',
    qr_token: '' // Hidden field
  });

  // Extract QR token from URL on component mount
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    const hotelSlug = params.get('hotel');
    
    if (token) {
      setFormData(prev => ({
        ...prev,
        qr_token: token
      }));
      
      // Optionally show a success message that QR was scanned
      console.log('QR Code scanned successfully!', { token, hotelSlug });
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match!');
      return;
    }

    try {
      const response = await axios.post('/api/staff/register/', {
        username: formData.username,
        password: formData.password,
        registration_code: formData.registration_code,
        qr_token: formData.qr_token || undefined, // Include if present
      });

      alert('Registration successful! Please wait for approval.');
      navigate('/login');
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Registration failed';
      alert(errorMsg);
    }
  };

  return (
    <div className="register-page">
      <h1>Staff Registration</h1>
      
      {formData.qr_token && (
        <div className="qr-success-banner">
          ✅ QR Code scanned successfully! Please enter your registration code below.
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Registration Code *</label>
          <input
            type="text"
            value={formData.registration_code}
            onChange={(e) => setFormData({
              ...formData, 
              registration_code: e.target.value.toUpperCase()
            })}
            placeholder="Enter your registration code"
            required
          />
          <small>Enter the code provided by HR</small>
        </div>

        <div className="form-group">
          <label>Username *</label>
          <input
            type="text"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label>Password *</label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
        </div>

        <div className="form-group">
          <label>Confirm Password *</label>
          <input
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
            required
          />
        </div>

        <button type="submit">Register</button>
      </form>

      <div className="info-box">
        <h3>ℹ️ Registration Requirements</h3>
        <ul>
          <li>Scan the QR code provided by HR</li>
          <li>Enter the registration code (also provided by HR)</li>
          <li>Both are required for security</li>
        </ul>
      </div>
    </div>
  );
};

export default Register;
```

---

### **3. Update Routing**

Make sure your React Router can handle the registration URL with query parameters:

```jsx
// App.jsx or Routes.jsx

<Route path="/register" element={<Register />} />
```

The URL will be: `https://hotelsmates.com/register?token=xyz&hotel=grand-plaza`

---

## 🔒 Security Features

### **Two-Factor Registration**
- **Factor 1:** QR Token (automatically captured from URL)
- **Factor 2:** Registration Code (manually entered)
- Both must match for successful registration

### **Backward Compatibility**
- Old registration codes without QR tokens still work
- Only codes with tokens require both pieces
- Gradual migration path for existing codes

### **Token Security**
- 32-byte cryptographically secure tokens
- Unique per registration code
- Not exposed in frontend (only in QR URL)

---

## 📱 User Flow

### **For HR/Admin:**
1. Navigate to Settings → Staff Registration
2. Click "Generate New Package"
3. Optionally enter custom code or let system generate
4. Download/Print the package (includes both code and QR)
5. Give package to new employee

### **For New Employee:**
1. Receive registration package from HR (paper/email)
2. Scan QR code with mobile device
3. Opens: `https://hotelsmates.com/register?token=xyz&hotel=slug`
4. See confirmation that QR was scanned
5. Manually enter registration code from package
6. Fill in username, password, etc.
7. Submit registration
8. Backend validates both code and token match
9. Registration successful!

---

## 🎨 Suggested UI/UX Enhancements

### **Settings Page:**
- Add visual card-based layout for registration packages
- Show list of previously generated codes
- Add filter for used/unused codes
- Show QR code preview thumbnails
- Add bulk actions (generate multiple codes)

### **Registration Page:**
- Show checkmark when QR is scanned
- Clear visual indicator if both code and QR are present
- Show hotel name/logo when QR is scanned
- Add "Don't have a QR code?" help section

### **Print Template:**
- Professional looking package template
- Include hotel branding
- Clear step-by-step instructions
- Tear-off sections for code and QR

---

## ✅ Testing Checklist

### **Backend Testing:**
- [ ] Generate registration package via API
- [ ] Verify QR code image uploaded to Cloudinary
- [ ] Test registration with matching code + token
- [ ] Test registration fails with mismatched token
- [ ] Test old codes still work (backward compatibility)

### **Frontend Testing:**
- [ ] QR code scan populates token in form
- [ ] Manual code entry works
- [ ] Form submission includes both fields
- [ ] Error messages display correctly
- [ ] Print package displays properly
- [ ] Download QR code works
- [ ] Mobile responsive design

---

## 🚀 Deployment Steps

1. **Backend:** ✅ Already deployed (migrations run)
2. **Frontend:** 
   - Add StaffRegistrationManager component
   - Update Register.jsx to handle QR tokens
   - Add route handling for `/register?token=...`
   - Deploy to production

---

## 📞 Support

If you have questions or need clarification:
- Check the API endpoint responses for detailed error messages
- Review the backend admin panel (`/admin/staff/registrationcode/`)
- Test with the development API first before production

---

## 🔄 Migration Notes

All existing registration codes have been automatically assigned unique QR tokens during migration. However, QR code images are generated on-demand when:
1. Admin uses the "Generate Registration Package" API
2. Admin uses the Django admin bulk action

**Action Required:** 
- Inform admins to regenerate QR codes for existing unused registration codes
- Or use Django admin bulk action: "Generate QR codes for selected registration codes"

---

**Last Updated:** November 3, 2025
**Backend Version:** Compatible with Django 5.2.4
**Frontend Requirements:** React Router v6+

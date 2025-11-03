# QR Code Registration - Quick Reference

## 🎯 TL;DR

**What:** Two-factor staff registration using Registration Code + QR Token  
**Why:** Prevent unauthorized registrations  
**Where:** Settings.jsx (generate) + Register.jsx (use)

---

## 📝 Quick Implementation Checklist

### Backend (✅ Done)
- [x] Added `qr_token` and `qr_code_url` fields to `RegistrationCode` model
- [x] Created migration + data migration
- [x] Updated registration validation logic
- [x] Created API endpoint: `POST /api/staff/registration-package/`
- [x] Updated Django admin with QR preview

### Frontend (⚠️ Todo)
- [ ] Add registration package generator to Settings.jsx
- [ ] Update Register.jsx to capture QR token from URL
- [ ] Include `qr_token` in registration API call
- [ ] Add print/download functionality for packages
- [ ] Test QR code scanning flow

---

## 🔌 API Endpoints

### Generate Package
```bash
POST /api/staff/registration-package/
Authorization: Token <your-token>
Content-Type: application/json

{
  "hotel_slug": "grand-plaza",
  "code": "STAFF2024"  # Optional
}
```

**Response:**
```json
{
  "registration_code": "STAFF2024",
  "qr_code_url": "https://res.cloudinary.com/.../qr.png",
  "hotel_slug": "grand-plaza",
  "hotel_name": "Grand Plaza Hotel"
}
```

### Register with QR
```bash
POST /api/staff/register/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!",
  "registration_code": "STAFF2024",
  "qr_token": "xJ8kL9mN..."  # From QR URL
}
```

---

## 🎨 Frontend Code Snippets

### Extract Token from URL (Register.jsx)
```jsx
useEffect(() => {
  const params = new URLSearchParams(location.search);
  const token = params.get('token');
  const hotel = params.get('hotel');
  
  setFormData(prev => ({ ...prev, qr_token: token }));
}, [location]);
```

### Generate Package (Settings.jsx)
```jsx
const generatePackage = async () => {
  const res = await axios.post('/api/staff/registration-package/', {
    hotel_slug: hotelSlug
  });
  setPackage(res.data);
};
```

### Submit Registration (Register.jsx)
```jsx
await axios.post('/api/staff/register/', {
  username,
  password,
  registration_code,
  qr_token  // From URL
});
```

---

## 🔍 QR Code URL Format

```
https://hotelsmates.com/register?token={QR_TOKEN}&hotel={HOTEL_SLUG}
```

**Example:**
```
https://hotelsmates.com/register?token=xJ8kL9mN&hotel=grand-plaza
```

**Note:** Registration code is NOT in the URL - user enters manually

---

## 🧪 Testing

### Test Scenarios:
1. **Valid:** Correct code + correct token → ✅ Success
2. **Invalid:** Correct code + wrong token → ❌ Error
3. **Invalid:** Wrong code + correct token → ❌ Error
4. **Backward:** Old code (no token) + no token → ✅ Success (compatibility)
5. **Invalid:** Old code + token provided → ❌ Error

---

## 🎨 UI Components Needed

1. **StaffRegistrationManager** (Settings.jsx)
   - Generate button
   - QR code display
   - Registration code display
   - Print/Download buttons

2. **Register Form Updates** (Register.jsx)
   - QR success banner
   - Hidden qr_token field
   - Registration code input

---

## 🚨 Common Issues & Solutions

### Issue: QR code not generating
**Solution:** Check Cloudinary credentials in environment variables

### Issue: Token mismatch error
**Solution:** Ensure QR token from URL is included in registration POST

### Issue: Old codes not working
**Solution:** Backward compatible - old codes work without token

### Issue: QR URL not opening registration page
**Solution:** Check React Router configuration for `/register` route

---

## 📱 User Experience Flow

```
HR/Admin → Settings → Generate Package → Print/Download
                                              ↓
                                    Give to New Employee
                                              ↓
Employee → Scan QR → Opens Register Page → Enter Code → Submit
                                              ↓
                                      Backend Validates Both
                                              ↓
                                    Registration Success! ✅
```

---

## 🎯 Where to Add in Frontend

### Settings.jsx
```jsx
<section className="staff-registration">
  <h2>Staff Registration Management</h2>
  <StaffRegistrationManager hotelSlug={hotel.slug} />
</section>
```

**Location:** After other settings sections (e.g., hotel info, rooms)

**Permissions:** Only show to staff_admin and super_staff_admin

---

## 📋 Implementation Priority

1. **High Priority:**
   - Update Register.jsx to capture token ✨
   - Include qr_token in registration API call ✨

2. **Medium Priority:**
   - Add basic package generator to Settings.jsx
   - Simple QR code display

3. **Low Priority:**
   - Fancy print templates
   - Package history/list view
   - Bulk generation

---

## 🔐 Security Notes

- QR token is 32-byte cryptographically secure
- Token never displayed to user (only in QR URL)
- Both code and token required for new codes
- Old codes without tokens still work (migration support)

---

## 📞 Need Help?

- Check Django admin: `/admin/staff/registrationcode/`
- View QR codes and tokens in admin panel
- Test API with Postman/Thunder Client first
- Check browser console for URL parameter capture

---

**Quick Start:** Just add token capture to Register.jsx and you're 80% done! 🚀

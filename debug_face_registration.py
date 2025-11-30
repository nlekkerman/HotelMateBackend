#!/usr/bin/env python
"""
Debug script for face registration API - shows correct request format
"""
import json

def show_correct_request_format():
    """Show the correct format for face registration API"""
    
    print("🔍 FACE REGISTRATION API DEBUG")
    print("=" * 60)
    
    print("\n❌ CURRENT ERROR:")
    print('400 Bad Request: {"error": "Validation failed", "details": {"encoding": ["This field is required."]}}')
    
    print("\n✅ REQUIRED REQUEST FORMAT:")
    print("POST https://hotel-porter-d25ad83b12cf.herokuapp.com/api/staff/hotel/hotel-killarney/attendance/face-management/register-face/")
    
    print("\nHeaders:")
    print("  Authorization: Token <your_auth_token>")
    print("  Content-Type: application/json")
    
    print("\nRequest Body (JSON):")
    example_request = {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQ...",
        "encoding": [
            -0.123, 0.456, -0.789, 0.234, -0.567, 0.891, -0.345, 0.678,
            0.901, -0.234, 0.567, -0.890, 0.345, -0.678, 0.123, -0.456,
            # ... continue for 128 total float values
            0.111, -0.222, 0.333, -0.444, 0.555, -0.666, 0.777, -0.888
        ],
        "staff_id": 123,  # Optional - omit to register for current user
        "consent_given": True  # Optional - defaults to true
    }
    
    print(json.dumps(example_request, indent=2))
    
    print("\n📋 FIELD SPECIFICATIONS:")
    print("• image: Base64 encoded image with data URL prefix")
    print("• encoding: Array of EXACTLY 128 float values (-10.0 to +10.0 range)")
    print("• staff_id: Integer (optional, defaults to requesting user)")
    print("• consent_given: Boolean (optional, defaults to true)")
    
    print("\n🔧 FRONTEND FIXES NEEDED:")
    print("1. Extract face encoding from uploaded image using face-api.js or similar")
    print("2. Ensure encoding array has exactly 128 float values")
    print("3. Include both 'image' and 'encoding' in request body")
    print("4. Use proper base64 data URL format for image")
    
    print("\n💡 EXAMPLE FACE-API.JS CODE:")
    print("""
// Using face-api.js to get encoding
const detection = await faceapi
  .detectSingleFace(image, new faceapi.TinyFaceDetectorOptions())
  .withFaceLandmarks()
  .withFaceDescriptor();

if (detection) {
  const encoding = Array.from(detection.descriptor); // This gives you the 128 floats
  
  const requestBody = {
    image: imageDataURL, // base64 data URL
    encoding: encoding,  // 128-dimensional array
    consent_given: true
  };
  
  // Make the API call...
}
""")

    print("\n⚠️  COMMON ISSUES:")
    print("• Missing encoding field (current error)")
    print("• Wrong encoding array length (must be exactly 128)")
    print("• Invalid image format (must be data URL)")
    print("• Missing authentication token")
    print("• Encoding values out of range (-10 to +10)")

if __name__ == '__main__':
    show_correct_request_format()
# Quiz Game QR Code - Implementation Guide

## 🎯 Overview

Each quiz now has its own QR code that points directly to the quiz game. No hotel or room tracking required - fully anonymous!

---

## 📱 QR Code Features

### What the QR Code Does
- Points to: `https://hotelsmates.com/games/quiz/{quiz-slug}`
- Works for any user (anonymous access)
- Can be printed, displayed on screens, or shared digitally
- Each quiz has its own unique QR code

### Use Cases
- Print QR codes on hotel room cards
- Display on lobby screens
- Share on social media
- Include in promotional materials
- Place on table tents in restaurants/bars

---

## 🔧 Backend API

### 1. Get Quiz with QR Code

```http
GET /api/entertainment/quizzes/
```

**Response:**
```json
[
  {
    "id": 1,
    "slug": "classic-trivia-easy",
    "title": "Classic Trivia - Easy",
    "difficulty_level": 1,
    "difficulty_display": "Classic Trivia (Easy)",
    "is_active": true,
    "qr_code_url": "https://res.cloudinary.com/.../quiz_qr/classic-trivia-easy.png",
    "qr_generated_at": "2025-11-13T20:00:00Z"
  }
]
```

---

### 2. Generate QR Code for Quiz

```http
POST /api/entertainment/quizzes/{slug}/generate_qr_code/
```

**Example:**
```http
POST /api/entertainment/quizzes/classic-trivia-easy/generate_qr_code/
```

**Response:**
```json
{
  "message": "QR code generated successfully",
  "qr_code_url": "https://res.cloudinary.com/.../quiz_qr/classic-trivia-easy.png",
  "quiz_url": "https://hotelsmates.com/games/quiz/classic-trivia-easy",
  "generated_at": "2025-11-13T20:00:00Z"
}
```

---

### 3. Get Single Quiz Details

```http
GET /api/entertainment/quizzes/{slug}/
```

**Response:**
```json
{
  "id": 1,
  "slug": "classic-trivia-easy",
  "title": "Classic Trivia - Easy",
  "description": "Test your general knowledge!",
  "difficulty_level": 1,
  "difficulty_display": "Classic Trivia (Easy)",
  "max_questions": 10,
  "is_active": true,
  "qr_code_url": "https://res.cloudinary.com/.../quiz_qr/classic-trivia-easy.png",
  "qr_generated_at": "2025-11-13T20:00:00Z",
  "questions": [...]
}
```

---

## 🎨 Frontend Implementation

### Display QR Code in Quiz List

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function QuizListWithQR() {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadQuizzes();
  }, []);

  const loadQuizzes = async () => {
    try {
      const { data } = await axios.get('/api/entertainment/quizzes/');
      setQuizzes(data.filter(q => q.is_active));
    } catch (error) {
      console.error('Failed to load quizzes:', error);
    }
  };

  const generateQRCode = async (quiz) => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `/api/entertainment/quizzes/${quiz.slug}/generate_qr_code/`
      );
      
      // Update quiz in state with new QR code
      setQuizzes(prev => prev.map(q => 
        q.id === quiz.id 
          ? { ...q, qr_code_url: data.qr_code_url, qr_generated_at: data.generated_at }
          : q
      ));
      
      alert('QR Code generated successfully!');
    } catch (error) {
      console.error('Failed to generate QR code:', error);
      alert('Failed to generate QR code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = async (quiz) => {
    if (!quiz.qr_code_url) {
      alert('No QR code available. Generate one first.');
      return;
    }

    try {
      // Fetch the image
      const response = await fetch(quiz.qr_code_url);
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${quiz.slug}-qr-code.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download QR code:', error);
      alert('Failed to download QR code.');
    }
  };

  return (
    <div>
      <h1>Quiz Games</h1>
      
      <div className="quiz-grid">
        {quizzes.map(quiz => (
          <div key={quiz.id} className="quiz-card">
            <h3>{quiz.title}</h3>
            <p>{quiz.description}</p>
            <p>Difficulty: {quiz.difficulty_display}</p>
            <p>Questions: {quiz.question_count}</p>
            
            {/* QR Code Section */}
            <div className="qr-section">
              {quiz.qr_code_url ? (
                <div>
                  <img 
                    src={quiz.qr_code_url} 
                    alt={`${quiz.title} QR Code`}
                    style={{ width: '200px', height: '200px' }}
                  />
                  <p>
                    Generated: {new Date(quiz.qr_generated_at).toLocaleDateString()}
                  </p>
                  <div>
                    <button onClick={() => generateQRCode(quiz)} disabled={loading}>
                      Regenerate QR Code
                    </button>
                    <button onClick={() => downloadQRCode(quiz)}>
                      Download QR Code
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <p>No QR code generated yet</p>
                  <button onClick={() => generateQRCode(quiz)} disabled={loading}>
                    Generate QR Code
                  </button>
                </div>
              )}
            </div>
            
            <button onClick={() => window.location.href = `/games/quiz/${quiz.slug}`}>
              Play Now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default QuizListWithQR;
```

---

### Admin Panel - Bulk QR Generation

```jsx
function QuizAdminPanel() {
  const [quizzes, setQuizzes] = useState([]);
  const [generating, setGenerating] = useState(false);

  const generateAllQRCodes = async () => {
    setGenerating(true);
    const results = {
      success: 0,
      failed: 0
    };

    for (const quiz of quizzes) {
      try {
        await axios.post(`/api/entertainment/quizzes/${quiz.slug}/generate_qr_code/`);
        results.success++;
      } catch (error) {
        console.error(`Failed for ${quiz.title}:`, error);
        results.failed++;
      }
    }

    setGenerating(false);
    alert(`Generated ${results.success} QR codes. Failed: ${results.failed}`);
    
    // Reload quizzes
    loadQuizzes();
  };

  return (
    <div>
      <h1>Quiz Management</h1>
      <button onClick={generateAllQRCodes} disabled={generating}>
        {generating ? 'Generating...' : 'Generate All QR Codes'}
      </button>
      {/* Rest of admin panel */}
    </div>
  );
}
```

---

### Print-Ready QR Code Page

```jsx
function PrintableQRCode({ quizSlug }) {
  const [quiz, setQuiz] = useState(null);

  useEffect(() => {
    loadQuiz();
  }, [quizSlug]);

  const loadQuiz = async () => {
    const { data } = await axios.get(`/api/entertainment/quizzes/${quizSlug}/`);
    setQuiz(data);
  };

  const handlePrint = () => {
    window.print();
  };

  if (!quiz) return <div>Loading...</div>;

  return (
    <div className="printable-qr" style={{ textAlign: 'center', padding: '40px' }}>
      <style>{`
        @media print {
          .no-print { display: none; }
        }
      `}</style>
      
      <h1>{quiz.title}</h1>
      <p style={{ fontSize: '18px', marginBottom: '30px' }}>
        {quiz.description}
      </p>
      
      {quiz.qr_code_url ? (
        <div>
          <img 
            src={quiz.qr_code_url} 
            alt="Quiz QR Code"
            style={{ width: '400px', height: '400px', margin: '20px auto' }}
          />
          <h2>Scan to Play!</h2>
          <p style={{ fontSize: '14px', color: '#666' }}>
            Or visit: hotelsmates.com/games/quiz/{quiz.slug}
          </p>
        </div>
      ) : (
        <p>No QR code available</p>
      )}
      
      <button className="no-print" onClick={handlePrint}>
        Print This Page
      </button>
    </div>
  );
}
```

---

## 🖨️ Django Admin Usage

### Generate QR Codes from Admin Panel

1. **Navigate to Quiz Admin**
   - Go to Django Admin → Entertainment → Quizzes

2. **Select Quizzes**
   - Check the boxes next to quizzes you want to generate QR codes for

3. **Choose Action**
   - From the "Action" dropdown, select **"Generate QR codes"**
   - Click "Go"

4. **View Results**
   - Success message shows how many QR codes were generated
   - QR codes are immediately available

5. **View QR Code**
   - Click on a quiz to view details
   - QR Code section shows the generated QR code URL
   - You can copy the URL to use elsewhere

---

## 📋 QR Code URL Structure

### Generated Files
- **Cloudinary Path**: `quiz_qr/{quiz-slug}.png`
- **Example**: `quiz_qr/classic-trivia-easy.png`
- **Overwrite**: Yes (regenerating updates the same file)

### Target URL
- **Format**: `https://hotelsmates.com/games/quiz/{quiz-slug}`
- **Example**: `https://hotelsmates.com/games/quiz/classic-trivia-easy`

---

## 🎯 Complete Workflow

### For Hotel Staff

1. **Generate QR Codes** (One-time setup)
   ```bash
   # Via Django Admin: Select quizzes → Generate QR codes
   ```

2. **Download QR Images**
   ```jsx
   // Frontend: Click "Download QR Code" button
   // Or: Copy URL from admin and download directly
   ```

3. **Print & Display**
   - Print on room cards
   - Display on screens
   - Add to promotional materials

### For Guests

1. **Scan QR Code** with phone camera
2. **Redirected to**: `https://hotelsmates.com/games/quiz/{quiz-slug}`
3. **Enter Name** and choose game mode (Casual or Tournament)
4. **Play Quiz** - Fully anonymous, no login required!

---

## 🔄 Regenerating QR Codes

### When to Regenerate
- Quiz slug changed (rare)
- QR code image corrupted
- Want to refresh the image

### How to Regenerate
- **Admin**: Select quiz → Generate QR codes action
- **API**: `POST /api/entertainment/quizzes/{slug}/generate_qr_code/`
- **Frontend**: Click "Regenerate QR Code" button

**Note**: Regenerating overwrites the old QR code with the same filename.

---

## 📊 Summary

### ✅ Benefits
- **Simple**: One QR code per quiz
- **Anonymous**: No authentication required
- **Flexible**: Print, display, or share digitally
- **Persistent**: QR codes work indefinitely
- **Manageable**: Easy bulk generation from admin

### 🔑 Key Points
1. Each quiz has its own QR code
2. QR codes point to anonymous game URLs
3. Generate from Django admin or via API
4. Download and print for physical distribution
5. No hotel or room tracking needed

### 📱 Mobile-First
- QR codes open directly in mobile browsers
- Responsive game interface
- Touch-friendly controls
- Works offline after initial load

---

## 🚀 Next Steps

1. **Generate QR codes** for all active quizzes
2. **Download images** for printing
3. **Distribute** to hotels/locations
4. **Monitor usage** via leaderboards
5. **Add new quizzes** and generate QR codes as needed

# Quiz Game UI Components

## Backend Change ✅
- **Streak reset on refresh**: When a session is resumed, `consecutive_correct` and `is_turbo_active` are reset to 0/false

---

## Frontend UI Components Needed

### 1. Battery Progress Indicator (Red to Green)

Replace the two progress bars with a single battery-like charging indicator that changes color based on progress.

```jsx
const BatteryProgressIndicator = ({ currentQuestion, totalQuestions }) => {
  const progress = (currentQuestion / totalQuestions) * 100;
  
  // Calculate color from red to green
  const getColor = (percent) => {
    if (percent < 33) return '#ef4444'; // red
    if (percent < 66) return '#f59e0b'; // orange/yellow
    return '#22c55e'; // green
  };
  
  return (
    <div className="battery-container">
      <div className="battery-body">
        <div 
          className="battery-fill"
          style={{
            width: `${progress}%`,
            backgroundColor: getColor(progress),
            transition: 'all 0.3s ease'
          }}
        >
          <div className="battery-shine"></div>
        </div>
        <span className="battery-text">
          {currentQuestion} / {totalQuestions}
        </span>
      </div>
      <div className="battery-tip"></div>
    </div>
  );
};
```

#### CSS for Battery

```css
.battery-container {
  display: flex;
  align-items: center;
  gap: 2px;
  margin: 1rem 0;
}

.battery-body {
  position: relative;
  width: 200px;
  height: 40px;
  border: 3px solid #333;
  border-radius: 8px;
  background: #f3f4f6;
  overflow: hidden;
}

.battery-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: 5px;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.battery-shine {
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  height: 40%;
  background: linear-gradient(to bottom, rgba(255,255,255,0.3), transparent);
  border-radius: 3px;
}

.battery-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: bold;
  font-size: 14px;
  color: #1f2937;
  z-index: 10;
  text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}

.battery-tip {
  width: 8px;
  height: 24px;
  background: #333;
  border-radius: 0 4px 4px 0;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .battery-body {
    width: 150px;
    height: 32px;
  }
  
  .battery-text {
    font-size: 12px;
  }
  
  .battery-tip {
    width: 6px;
    height: 18px;
  }
}
```

---

### 2. Wall Clock Timer (5 seconds countdown)

Circular clock that visually counts down from 5 to 0 seconds.

```jsx
const WallClockTimer = ({ timeLeft, maxTime = 5 }) => {
  const progress = (timeLeft / maxTime) * 100;
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (progress / 100) * circumference;
  
  // Color changes as time runs out
  const getColor = () => {
    if (timeLeft <= 1) return '#ef4444'; // red
    if (timeLeft <= 2) return '#f59e0b'; // orange
    return '#22c55e'; // green
  };
  
  return (
    <div className="clock-container">
      <svg width="120" height="120" viewBox="0 0 120 120">
        {/* Clock face background */}
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="white"
          stroke="#e5e7eb"
          strokeWidth="2"
        />
        
        {/* Clock border */}
        <circle
          cx="60"
          cy="60"
          r="56"
          fill="none"
          stroke="#9ca3af"
          strokeWidth="3"
        />
        
        {/* Progress circle */}
        <circle
          cx="60"
          cy="60"
          r="45"
          fill="none"
          stroke={getColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.3s ease' }}
        />
        
        {/* Clock center dot */}
        <circle cx="60" cy="60" r="4" fill="#1f2937" />
        
        {/* Clock hand (rotates) */}
        <line
          x1="60"
          y1="60"
          x2="60"
          y2="25"
          stroke="#1f2937"
          strokeWidth="3"
          strokeLinecap="round"
          transform={`rotate(${(timeLeft / maxTime) * 360} 60 60)`}
          style={{ transition: 'transform 1s linear' }}
        />
      </svg>
      
      {/* Time display */}
      <div className="clock-time">
        {timeLeft}s
      </div>
    </div>
  );
};
```

#### CSS for Clock Timer

```css
.clock-container {
  position: relative;
  display: inline-block;
  margin: 1rem;
}

.clock-time {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  font-weight: bold;
  color: #1f2937;
  pointer-events: none;
}

/* Pulse animation when time is running out */
@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.1); }
}

.clock-time.urgent {
  animation: pulse 0.5s infinite;
  color: #ef4444;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .clock-container svg {
    width: 100px;
    height: 100px;
  }
  
  .clock-time {
    font-size: 20px;
  }
}
```

---

### 3. Usage Example

```jsx
const QuizGame = () => {
  const [timeLeft, setTimeLeft] = useState(5);
  const [currentQuestion, setCurrentQuestion] = useState(1);
  const totalQuestions = 50; // 5 categories × 10 questions
  
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleTimeout();
          return 5; // Reset for next question
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(timer);
  }, [currentQuestion]);
  
  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <BatteryProgressIndicator 
          currentQuestion={currentQuestion}
          totalQuestions={totalQuestions}
        />
        
        <WallClockTimer 
          timeLeft={timeLeft}
          maxTime={5}
        />
      </div>
      
      {/* Question and answers */}
    </div>
  );
};
```

---

## Summary

✅ **Backend**: Streak resets on page refresh/resume
🎨 **Frontend**: 
- Battery charging indicator (red → orange → green)
- Wall clock timer (circular countdown)
- Both are mobile responsive
- Smooth animations and transitions

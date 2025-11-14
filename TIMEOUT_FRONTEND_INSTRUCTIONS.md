# Frontend Instructions: Timeout Handling

## Issue Description
When a question times out (5+ seconds with no answer), the same question should NOT be reloaded. The timeout should be treated as a wrong answer, and the game should automatically move to the next question.

## Backend Behavior (Already Correct ✅)

The backend correctly handles timeouts:

1. **Timeout Detection**: 
   - `time_taken_seconds > 5` OR
   - `selected_answer === "TIMEOUT"`

2. **Timeout Consequences**:
   - ✅ `is_correct = false`
   - ✅ `points_awarded = 0`
   - ✅ `consecutive_correct = 0` (streak reset)
   - ✅ `is_turbo_active = false` (turbo mode disabled)
   - ✅ Answer recorded as "TIMEOUT"

3. **Response Structure**:
```json
{
  "success": true,
  "submission": {
    "is_correct": false,
    "points_awarded": 0,
    "selected_answer": "TIMEOUT",
    "correct_answer": "The Right Answer",
    "time_taken_seconds": 6
  },
  "session_updated": {
    "score": 150,
    "consecutive_correct": 0,
    "is_turbo_active": false,
    "total_questions_answered": 15
  }
}
```

## Frontend Implementation Required

### 1. Question Timer Component

```javascript
class QuestionTimer {
  constructor(timeLimit = 5, onTimeout) {
    this.timeLimit = timeLimit;
    this.onTimeout = onTimeout;
    this.startTime = null;
    this.timerId = null;
    this.hasTimedOut = false;
  }
  
  start() {
    this.startTime = Date.now();
    this.hasTimedOut = false;
    
    // Set timeout callback
    this.timerId = setTimeout(() => {
      this.hasTimedOut = true;
      this.onTimeout();
    }, this.timeLimit * 1000);
  }
  
  stop() {
    if (this.timerId) {
      clearTimeout(this.timerId);
      this.timerId = null;
    }
  }
  
  getElapsedSeconds() {
    if (!this.startTime) return 0;
    return Math.floor((Date.now() - this.startTime) / 1000);
  }
  
  hasExpired() {
    return this.hasTimedOut;
  }
}
```

### 2. Question State Manager

```javascript
class QuizQuestionManager {
  constructor(questions) {
    this.questions = questions;
    this.currentIndex = 0;
    this.timer = null;
  }
  
  getCurrentQuestion() {
    if (this.currentIndex >= this.questions.length) {
      return null; // All questions answered
    }
    return this.questions[this.currentIndex];
  }
  
  moveToNextQuestion() {
    this.currentIndex++;
    if (this.timer) {
      this.timer.stop();
    }
  }
  
  hasMoreQuestions() {
    return this.currentIndex < this.questions.length;
  }
  
  async handleTimeout(sessionId, categorySlug) {
    const question = this.getCurrentQuestion();
    if (!question) return;
    
    console.log(`⏰ Timeout on question ${this.currentIndex + 1}`);
    
    // Submit timeout to backend
    const response = await fetch('/api/entertainment/quiz/game/submit_answer/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        category_slug: categorySlug,
        question_id: question.id,
        question_text: question.text,
        question_data: question.question_data, // For math questions
        selected_answer: 'TIMEOUT',
        selected_answer_id: null,
        time_taken_seconds: 6 // Over the limit
      })
    });
    
    const result = await response.json();
    
    // CRITICAL: Move to next question regardless of response
    this.moveToNextQuestion();
    
    return result;
  }
  
  async handleAnswer(sessionId, categorySlug, selectedAnswer, selectedAnswerId) {
    const question = this.getCurrentQuestion();
    if (!question) return;
    
    const elapsedSeconds = this.timer ? this.timer.getElapsedSeconds() : 0;
    
    // Submit answer to backend
    const response = await fetch('/api/entertainment/quiz/game/submit_answer/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        category_slug: categorySlug,
        question_id: question.id,
        question_text: question.text,
        question_data: question.question_data,
        selected_answer: selectedAnswer,
        selected_answer_id: selectedAnswerId,
        time_taken_seconds: elapsedSeconds
      })
    });
    
    const result = await response.json();
    
    // CRITICAL: Move to next question after submission
    this.moveToNextQuestion();
    
    return result;
  }
  
  startTimer(onTimeout) {
    if (this.timer) {
      this.timer.stop();
    }
    
    this.timer = new QuestionTimer(5, async () => {
      // Auto-submit timeout when timer expires
      await this.handleTimeout(
        this.sessionId,
        this.categorySlug
      );
      
      // Trigger UI update
      onTimeout();
    });
    
    this.timer.start();
  }
}
```

### 3. React/Vue Component Example

```javascript
// React Component
function QuizQuestion({ sessionId, categorySlug, questions, onCategoryComplete }) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isAnswering, setIsAnswering] = useState(false);
  const [timeLeft, setTimeLeft] = useState(5);
  const timerRef = useRef(null);
  const timeoutIdRef = useRef(null);
  
  const currentQuestion = questions[currentQuestionIndex];
  
  useEffect(() => {
    // Start timer when question loads
    startQuestionTimer();
    
    return () => {
      // Cleanup on unmount
      if (timerRef.current) {
        timerRef.current.stop();
      }
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
      }
    };
  }, [currentQuestionIndex]);
  
  const startQuestionTimer = () => {
    setTimeLeft(5);
    
    // Update display every 100ms
    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const remaining = Math.max(0, 5 - elapsed);
      setTimeLeft(remaining);
    }, 100);
    
    // Set timeout for 5 seconds
    timeoutIdRef.current = setTimeout(() => {
      handleTimeout();
    }, 5000);
  };
  
  const stopQuestionTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }
  };
  
  const handleTimeout = async () => {
    if (isAnswering) return; // Prevent double submission
    setIsAnswering(true);
    
    stopQuestionTimer();
    
    console.log('⏰ Question timed out');
    
    try {
      // Submit timeout to backend
      const response = await fetch('/api/entertainment/quiz/game/submit_answer/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          category_slug: categorySlug,
          question_id: currentQuestion.id,
          question_text: currentQuestion.text,
          question_data: currentQuestion.question_data,
          selected_answer: 'TIMEOUT',
          selected_answer_id: null,
          time_taken_seconds: 6
        })
      });
      
      const result = await response.json();
      
      // Show timeout feedback
      showFeedback({
        isCorrect: false,
        message: 'Time\'s up!',
        correctAnswer: result.submission.correct_answer,
        points: 0
      });
      
      // Wait 2 seconds, then move to next question
      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);
      
    } catch (error) {
      console.error('Error submitting timeout:', error);
      // Still move to next question even on error
      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);
    }
  };
  
  const handleAnswerSelection = async (answer, answerId) => {
    if (isAnswering) return; // Prevent double submission
    setIsAnswering(true);
    
    stopQuestionTimer();
    
    const elapsedSeconds = Math.min(5, 5 - timeLeft);
    
    try {
      const response = await fetch('/api/entertainment/quiz/game/submit_answer/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          category_slug: categorySlug,
          question_id: currentQuestion.id,
          question_text: currentQuestion.text,
          question_data: currentQuestion.question_data,
          selected_answer: answer,
          selected_answer_id: answerId,
          time_taken_seconds: elapsedSeconds
        })
      });
      
      const result = await response.json();
      
      // Show feedback
      showFeedback({
        isCorrect: result.submission.is_correct,
        message: result.submission.is_correct ? 'Correct!' : 'Wrong!',
        correctAnswer: result.submission.correct_answer,
        points: result.submission.points_awarded
      });
      
      // Wait 2 seconds, then move to next question
      setTimeout(() => {
        moveToNextQuestion();
      }, 2000);
      
    } catch (error) {
      console.error('Error submitting answer:', error);
      setIsAnswering(false);
    }
  };
  
  const moveToNextQuestion = () => {
    setIsAnswering(false);
    
    // Check if more questions in this category
    if (currentQuestionIndex + 1 < questions.length) {
      // Move to next question
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // Category complete
      onCategoryComplete();
    }
  };
  
  const showFeedback = (feedback) => {
    // Show feedback UI (toast, modal, etc.)
    console.log('Feedback:', feedback);
  };
  
  if (!currentQuestion) {
    return <div>Loading...</div>;
  }
  
  return (
    <div className="quiz-question">
      <div className="timer">
        <span className={timeLeft <= 1 ? 'timer-critical' : ''}>
          {timeLeft}s
        </span>
      </div>
      
      <div className="question-text">
        {currentQuestion.text}
      </div>
      
      <div className="answers">
        {currentQuestion.answers.map(answer => (
          <button
            key={answer.id}
            onClick={() => handleAnswerSelection(answer.text, answer.id)}
            disabled={isAnswering}
          >
            {answer.text}
          </button>
        ))}
      </div>
      
      <div className="progress">
        Question {currentQuestionIndex + 1} of {questions.length}
      </div>
    </div>
  );
}
```

### 4. Critical Rules

**DO:**
- ✅ Start timer immediately when question displays
- ✅ Submit timeout automatically when timer expires
- ✅ Move to next question after ANY submission (correct, wrong, or timeout)
- ✅ Stop timer when user selects an answer
- ✅ Show feedback for 1-2 seconds before moving to next question
- ✅ Clear all timers on component unmount

**DON'T:**
- ❌ Reload the same question after timeout
- ❌ Wait for user action after timeout
- ❌ Allow answer selection after timeout
- ❌ Show the same question twice
- ❌ Let multiple timers run simultaneously

### 5. Testing Checklist

Test these scenarios:

1. **Normal Answer**: User answers within 5 seconds
   - ✅ Timer stops
   - ✅ Answer submitted
   - ✅ Move to next question

2. **Timeout**: No answer for 5+ seconds
   - ✅ Timer expires
   - ✅ "TIMEOUT" submitted automatically
   - ✅ Show timeout feedback
   - ✅ Move to next question (NOT reload same question)

3. **Last-Second Answer**: User answers at 4.9 seconds
   - ✅ Answer submitted (not timeout)
   - ✅ Move to next question

4. **Race Condition**: Timeout and user click at same time
   - ✅ Only one submission sent
   - ✅ Use `isAnswering` flag to prevent double submission

5. **Category Completion**: Last question times out
   - ✅ Submit timeout
   - ✅ Move to next category (not reload same question)

### 6. Common Mistakes to Avoid

**Mistake 1: Not moving to next question after timeout**
```javascript
// ❌ WRONG
const handleTimeout = async () => {
  await submitTimeout();
  // Missing: moveToNextQuestion()
};

// ✅ CORRECT
const handleTimeout = async () => {
  await submitTimeout();
  setTimeout(() => moveToNextQuestion(), 2000);
};
```

**Mistake 2: Not stopping timer when answer selected**
```javascript
// ❌ WRONG
const handleAnswer = async (answer) => {
  await submitAnswer(answer);
  // Timer still running!
};

// ✅ CORRECT
const handleAnswer = async (answer) => {
  stopTimer(); // Stop immediately
  await submitAnswer(answer);
  moveToNextQuestion();
};
```

**Mistake 3: Allowing clicks during/after timeout**
```javascript
// ❌ WRONG
<button onClick={handleAnswer}>
  {answer.text}
</button>

// ✅ CORRECT
<button 
  onClick={handleAnswer}
  disabled={isAnswering || hasTimedOut}
>
  {answer.text}
</button>
```

## Summary

The backend correctly treats timeouts as wrong answers with 0 points. The frontend must:

1. **Auto-submit** timeout after 5 seconds
2. **Always move** to next question (never reload same question)
3. **Prevent double submission** with proper state management
4. **Stop timers** when answer is selected or component unmounts

Follow the code examples above to ensure proper timeout handling!

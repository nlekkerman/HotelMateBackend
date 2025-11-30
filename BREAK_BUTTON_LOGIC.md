# Break Button Logic

## Staff NOT on break:
Backend sends you these buttons in `available_actions`:
```javascript
{
  "label": "Clock Out",        // <- USE THIS TEXT
  "endpoint": "/confirm-clock-out/"
},
{
  "label": "Start Break",      // <- USE THIS TEXT  
  "endpoint": "/toggle-break/"
}
```

## Staff ON break:
Backend sends you this button in `available_actions`:
```javascript
{
  "label": "Resume Shift",     // <- USE THIS TEXT
  "endpoint": "/toggle-break/"
}
```

## Key Facts:
- **Same endpoint** `/toggle-break/` for both start/end break
- Backend checks `is_on_break` status to determine action
- Button labels change automatically based on break status
- Frontend renders buttons from `available_actions` array in API response
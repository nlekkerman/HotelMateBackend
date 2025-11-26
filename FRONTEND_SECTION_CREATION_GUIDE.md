# Frontend Guide: Section Creation Modal

## Overview
This guide explains how to implement the section creation modal flow in the frontend.

## API Endpoint
```
POST /api/staff/hotel/{hotel_slug}/sections/create/
```

## Modal Flow

### Step 1: Select Section Type
Show the user 4 section type options:

| Type | Label | Needs Container Name? |
|------|-------|----------------------|
| `hero` | Hero Section | No |
| `gallery` | Gallery Section | Yes |
| `list` | List Section | Yes |
| `news` | News Section | No |

### Step 2: Collect Names Based on Type

#### For Hero Section
- **No additional input needed**
- Show confirmation: "Create Hero Section?"
- API call: `{ section_type: "hero" }`

#### For Gallery Section
Show 2 input fields:
1. **Section Name** (optional)
   - Label: "Section Name"
   - Placeholder: "e.g., Hotel Photos"
   - Default if empty: "Gallery Section"

2. **Gallery Name** (optional)
   - Label: "First Gallery Name"
   - Placeholder: "e.g., Lobby & Reception"
   - Default if empty: "Gallery 1"

#### For List Section
Show 2 input fields:
1. **Section Name** (optional)
   - Label: "Section Name"
   - Placeholder: "e.g., Hotel Amenities"
   - Default if empty: "List Section"

2. **List Title** (optional)
   - Label: "First List Title"
   - Placeholder: "e.g., Room Features"
   - Default if empty: "" (empty string)

#### For News Section
Show 1 input field:
- **Section Name** (optional)
  - Label: "Section Name"
  - Placeholder: "e.g., Latest Updates"
  - Default if empty: "News Section"

## Request Payload Structure

```typescript
interface CreateSectionRequest {
  section_type: 'hero' | 'gallery' | 'list' | 'news';  // Required
  name?: string;                                        // Optional
  container_name?: string;                              // Optional (gallery/list only)
  position?: number;                                    // Optional (defaults to end)
}
```

## Example Payloads

### Hero Section (Minimal)
```json
{
  "section_type": "hero"
}
```

### Gallery Section (With Names)
```json
{
  "section_type": "gallery",
  "name": "Hotel Photos",
  "container_name": "Lobby & Reception"
}
```

### Gallery Section (Minimal)
```json
{
  "section_type": "gallery"
}
```
*Results in: Section named "Gallery Section" with container named "Gallery 1"*

### List Section (With Names)
```json
{
  "section_type": "list",
  "name": "Hotel Amenities",
  "container_name": "Room Features"
}
```

### List Section (Only Section Name)
```json
{
  "section_type": "list",
  "name": "Amenities"
}
```
*Results in: Section named "Amenities" with empty container title*

### News Section
```json
{
  "section_type": "news",
  "name": "Latest Updates"
}
```

## Implementation Example (React/TypeScript)

```typescript
const CreateSectionModal = ({ hotelSlug, onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [sectionType, setSectionType] = useState('');
  const [sectionName, setSectionName] = useState('');
  const [containerName, setContainerName] = useState('');

  const sectionTypes = [
    { value: 'hero', label: 'Hero Section', needsContainer: false },
    { value: 'gallery', label: 'Gallery Section', needsContainer: true },
    { value: 'list', label: 'List Section', needsContainer: true },
    { value: 'news', label: 'News Section', needsContainer: false }
  ];

  const handleSubmit = async () => {
    const payload = { section_type: sectionType };
    
    // Add optional fields only if provided
    if (sectionName.trim()) {
      payload.name = sectionName.trim();
    }
    
    if (containerName.trim() && (sectionType === 'gallery' || sectionType === 'list')) {
      payload.container_name = containerName.trim();
    }

    try {
      const response = await fetch(
        `/api/staff/hotel/${hotelSlug}/sections/create/`,
        {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        }
      );

      if (response.ok) {
        const data = await response.json();
        onSuccess(data);
        onClose();
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to create section');
      }
    } catch (err) {
      console.error('Error creating section:', err);
      alert('Failed to create section');
    }
  };

  return (
    <Modal>
      {step === 1 && (
        <div>
          <h2>Select Section Type</h2>
          {sectionTypes.map(type => (
            <button 
              key={type.value}
              onClick={() => {
                setSectionType(type.value);
                // For hero, skip to submission
                if (type.value === 'hero') {
                  handleSubmit();
                } else {
                  setStep(2);
                }
              }}
            >
              {type.label}
            </button>
          ))}
        </div>
      )}

      {step === 2 && (
        <div>
          <h2>Section Details</h2>
          
          <label>
            Section Name (optional)
            <input
              type="text"
              value={sectionName}
              onChange={(e) => setSectionName(e.target.value)}
              placeholder={`e.g., ${sectionType === 'gallery' ? 'Hotel Photos' : 'Hotel Amenities'}`}
            />
          </label>

          {(sectionType === 'gallery' || sectionType === 'list') && (
            <label>
              {sectionType === 'gallery' ? 'First Gallery Name' : 'First List Title'} (optional)
              <input
                type="text"
                value={containerName}
                onChange={(e) => setContainerName(e.target.value)}
                placeholder={sectionType === 'gallery' ? 'e.g., Lobby & Reception' : 'e.g., Room Features'}
              />
            </label>
          )}

          <button onClick={handleSubmit}>Create Section</button>
          <button onClick={() => setStep(1)}>Back</button>
        </div>
      )}
    </Modal>
  );
};
```

## Response Format

### Success Response (201 Created)
```json
{
  "message": "Gallery section created successfully",
  "section": {
    "id": 15,
    "position": 2,
    "name": "Hotel Photos",
    "is_active": true,
    "element": {
      "id": 15,
      "section_type": "gallery",
      "galleries": [
        {
          "id": 8,
          "name": "Lobby & Reception",
          "sort_order": 0,
          "images": []
        }
      ]
    }
  }
}
```

### Error Response (400 Bad Request)
```json
{
  "error": "section_type is required"
}
```

## Key Points

1. **Only `section_type` is required** - all other fields are optional
2. **Hero sections** can be created with a single click (no modal needed)
3. **Gallery/List sections** benefit from asking for names upfront
4. **All name fields are optional** - backend provides sensible defaults
5. **container_name** only applies to gallery and list types
6. **Position is auto-calculated** if not provided (section added to end)

## UI/UX Recommendations

- Show a 2-step modal for gallery/list/news types
- For hero, show a simple confirmation or create directly
- Mark all input fields as "optional" with placeholders showing examples
- Show default values that will be used if fields are left empty
- Validate that section_type is selected before proceeding

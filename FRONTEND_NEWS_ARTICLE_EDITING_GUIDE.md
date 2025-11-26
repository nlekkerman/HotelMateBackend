# Frontend Guide: Editing News Articles

## Overview
This guide explains how to update placeholder text and images in news articles.

## News Article Structure

When a news section is created, it includes one article with:
- **Article metadata**: title, date, summary
- **Content blocks**: ordered mix of text and image blocks

## Fetching Article Data

```typescript
// Get section with news items
GET /api/staff/hotel/{hotel_slug}/sections/{section_id}/

// Response includes news_items array
{
  "section": {
    "id": 15,
    "name": "News Section",
    "news_items": [
      {
        "id": 1,
        "title": "Update Article Title",
        "date": "2025-11-26",
        "summary": "Add a brief summary of this article here.",
        "sort_order": 0,
        "content_blocks": [
          {
            "id": 1,
            "block_type": "image",
            "image": null,  // Empty - needs upload
            "image_url": null,
            "image_position": "full_width",
            "image_caption": "Add cover image",
            "body": "",
            "sort_order": 0
          },
          {
            "id": 2,
            "block_type": "text",
            "body": "Add your article introduction text here. This is the opening paragraph.",
            "image": null,
            "image_url": null,
            "sort_order": 1
          },
          {
            "id": 3,
            "block_type": "image",
            "image": null,
            "image_url": null,
            "image_position": "right",
            "image_caption": "Add first inline image",
            "body": "",
            "sort_order": 2
          },
          // ... more blocks
        ]
      }
    ]
  }
}
```

## Updating Article Metadata

### Update Title, Date, or Summary

```typescript
PATCH /api/staff/hotel/{hotel_slug}/news-items/{news_item_id}/

{
  "title": "Grand Opening Celebration",
  "date": "2025-12-01",
  "summary": "Join us for our grand opening celebration with special offers!"
}
```

## Updating Text Blocks

### Update Text Content

```typescript
PATCH /api/staff/hotel/{hotel_slug}/content-blocks/{block_id}/

{
  "body": "We are thrilled to announce our grand opening on December 1st. Join us for an unforgettable celebration with exclusive opening offers, live entertainment, and complimentary refreshments."
}
```

## Updating Image Blocks

### Upload Image to Empty Block

```typescript
POST /api/staff/hotel/{hotel_slug}/content-blocks/{block_id}/upload-image/

// FormData with image file
const formData = new FormData();
formData.append('image', imageFile);

// Optional: Update caption
formData.append('image_caption', 'Our beautiful hotel entrance');
```

### Replace Existing Image

```typescript
// Same endpoint - replaces existing image
POST /api/staff/hotel/{hotel_slug}/content-blocks/{block_id}/upload-image/

const formData = new FormData();
formData.append('image', newImageFile);
formData.append('image_caption', 'Updated hotel lobby photo');
```

### Update Image Caption or Position

```typescript
PATCH /api/staff/hotel/{hotel_slug}/content-blocks/{block_id}/

{
  "image_caption": "Stunning lobby view at sunset",
  "image_position": "left"  // Options: full_width, left, right, inline_grid
}
```

## Frontend UI Implementation

### Rendering Content Blocks

```typescript
const NewsArticleEditor = ({ newsItem }) => {
  return (
    <div className="news-article-editor">
      {/* Article Header */}
      <ArticleMetaEditor 
        title={newsItem.title}
        date={newsItem.date}
        summary={newsItem.summary}
        onUpdate={(data) => updateArticleMeta(newsItem.id, data)}
      />

      {/* Content Blocks */}
      <div className="content-blocks">
        {newsItem.content_blocks.map(block => (
          <div key={block.id} className="content-block">
            {block.block_type === 'text' ? (
              <TextBlockEditor 
                block={block}
                onUpdate={(body) => updateTextBlock(block.id, body)}
              />
            ) : (
              <ImageBlockEditor 
                block={block}
                onUpload={(file) => uploadImage(block.id, file)}
                onUpdateCaption={(caption) => updateImageCaption(block.id, caption)}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

### Text Block Editor Component

```typescript
const TextBlockEditor = ({ block, onUpdate, onDelete }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [text, setText] = useState(block.body);

  const handleSave = async () => {
    await onUpdate(text);
    setShowEditModal(false);
  };

  const handleDelete = async () => {
    if (confirm('Delete this text block?')) {
      await onDelete(block.id);
    }
  };

  const isPlaceholder = text.startsWith('Add your');

  return (
    <div className={`text-block ${isPlaceholder ? 'placeholder' : ''}`}>
      {/* Always visible action icons */}
      <div className="block-actions">
        <button 
          className="icon-btn edit-btn"
          onClick={() => setShowEditModal(true)}
          title="Edit text"
        >
          ✏️
        </button>
        <button 
          className="icon-btn delete-btn"
          onClick={handleDelete}
          title="Delete block"
        >
          🗑️
        </button>
      </div>

      {/* Text preview */}
      <div className="text-preview">
        <p className={isPlaceholder ? 'text-gray-400 italic' : ''}>
          {text}
        </p>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <Modal onClose={() => setShowEditModal(false)}>
          <h3>Edit Text Block</h3>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="w-full"
            placeholder="Enter your text..."
          />
          <div className="modal-actions">
            <button onClick={handleSave} className="btn-primary">
              Save Changes
            </button>
            <button onClick={() => setShowEditModal(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
};
```

### Image Block Editor Component

```typescript
const ImageBlockEditor = ({ block, onUpload, onDelete }) => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [caption, setCaption] = useState(block.image_caption);
  const [position, setPosition] = useState(block.image_position);

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploadingImage(true);
    try {
      await onUpload(file);
      setShowEditModal(false);
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleSaveSettings = async () => {
    await onUpdateCaption(caption, position);
    setShowEditModal(false);
  };

  const handleDelete = async () => {
    if (confirm('Delete this image block?')) {
      await onDelete(block.id);
    }
  };

  const hasImage = !!block.image_url;

  return (
    <div className={`image-block position-${block.image_position}`}>
      {/* Always visible action icons */}
      <div className="block-actions">
        <button 
          className="icon-btn edit-btn"
          onClick={() => setShowEditModal(true)}
          title="Edit image"
        >
          ✏️
        </button>
        <button 
          className="icon-btn delete-btn"
          onClick={handleDelete}
          title="Delete block"
        >
          🗑️
        </button>
      </div>

      {/* Image Display */}
      {hasImage ? (
        <div className="image-preview">
          <img src={block.image_url} alt={block.image_caption} />
          <p className="caption">{block.image_caption}</p>
        </div>
      ) : (
        <div className="image-placeholder">
          <div className="upload-icon">📷</div>
          <p>{block.image_caption}</p>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <Modal onClose={() => setShowEditModal(false)}>
          <h3>Edit Image Block</h3>
          
          {/* Image Upload */}
          <div className="form-group">
            <label>Image</label>
            {hasImage && (
              <div className="current-image">
                <img src={block.image_url} alt="" style={{ maxWidth: '100%' }} />
              </div>
            )}
            <label className="file-upload-btn">
              {hasImage ? 'Replace Image' : 'Upload Image'}
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                style={{ display: 'none' }}
              />
            </label>
            {isUploadingImage && <div className="spinner">Uploading...</div>}
          </div>

          {/* Caption */}
          <div className="form-group">
            <label>Caption</label>
            <input
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Image caption"
            />
          </div>

          {/* Position */}
          <div className="form-group">
            <label>Position</label>
            <select 
              value={position} 
              onChange={(e) => setPosition(e.target.value)}
            >
              <option value="full_width">Full Width</option>
              <option value="left">Left (text wraps right)</option>
              <option value="right">Right (text wraps left)</option>
              <option value="inline_grid">Inline Grid</option>
            </select>
          </div>

          <div className="modal-actions">
            <button onClick={handleSaveSettings} className="btn-primary">
              Save Changes
            </button>
            <button onClick={() => setShowEditModal(false)} className="btn-secondary">
              Cancel
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
};
```

## API Endpoints Summary

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| Get article | GET | `/api/staff/hotel/{slug}/news-items/{id}/` | - |
| Update article meta | PATCH | `/api/staff/hotel/{slug}/news-items/{id}/` | `{title, date, summary}` |
| Update text block | PATCH | `/api/staff/hotel/{slug}/content-blocks/{id}/` | `{body}` |
| Upload/replace image | POST | `/api/staff/hotel/{slug}/content-blocks/{id}/upload-image/` | FormData with `image` |
| Update image caption | PATCH | `/api/staff/hotel/{slug}/content-blocks/{id}/` | `{image_caption}` |
| Update image position | PATCH | `/api/staff/hotel/{slug}/content-blocks/{id}/` | `{image_position}` |
| Add new block | POST | `/api/staff/hotel/{slug}/news-items/{id}/add-block/` | `{block_type, body/image}` |
| Delete block | DELETE | `/api/staff/hotel/{slug}/content-blocks/{id}/` | - |
| Reorder blocks | POST | `/api/staff/hotel/{slug}/news-items/{id}/reorder-blocks/` | `{block_ids: [1,3,2]}` |

## Identifying Placeholders

### Text Placeholders
Text blocks starting with:
- `"Add your article introduction..."`
- `"Add more article content..."`
- `"Add your closing paragraph..."`

Display these with:
- Gray/italic styling
- "Click to edit" hint
- Clear visual indication they're placeholders

### Image Placeholders
Image blocks with:
- `image: null` or `image_url: null`
- Caption starting with `"Add cover image"` or `"Add ... inline image"`

Display these as:
- Dashed border upload box
- Upload icon (📷 or similar)
- Caption text as placeholder text
- "Click to upload" hint

## Styling Recommendations

```css
/* Content block wrapper */
.content-block {
  position: relative;
  margin: 1.5rem 0;
  padding: 1rem;
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.2s;
}

.content-block:hover {
  border-color: #e5e7eb;
  background: #f9fafb;
}

/* Action icons - hidden initially, show on hover */
.block-actions {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  display: none;
  gap: 0.5rem;
}

.content-block:hover .block-actions {
  display: flex;
}

.icon-btn {
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 0.2s;
}

.icon-btn:hover {
  background: #f3f4f6;
  transform: scale(1.1);
}

.edit-btn:hover {
  border-color: #6366f1;
}

.delete-btn:hover {
  border-color: #ef4444;
}

/* Placeholder text */
.text-block.placeholder p {
  color: #9ca3af;
  font-style: italic;
}

/* Image placeholder */
.image-placeholder {
  border: 2px dashed #d1d5db;
  background: #f9fafb;
  padding: 3rem;
  text-align: center;
  transition: all 0.2s;
}

.content-block:hover .image-placeholder {
  border-color: #6366f1;
  background: #eef2ff;
}

/* Position-specific styles */
.image-block.position-full_width {
  width: 100%;
  margin: 2rem 0;
}

.image-block.position-right {
  float: right;
  width: 50%;
  margin-left: 2rem;
}

.image-block.position-left {
  float: left;
  width: 50%;
  margin-right: 2rem;
}
```

## Key Points

1. **All fields are editable** - title, date, summary, text blocks, images, captions
2. **Images are null initially** - show upload placeholders
3. **Text has placeholder content** - style differently to indicate needs editing
4. **Captions help staff** - they describe what should go in each slot
5. **Image positions** - full_width (cover), right, left (inline)
6. **Click to edit pattern** - makes editing intuitive
7. **Inline editing** - no modal needed for text updates

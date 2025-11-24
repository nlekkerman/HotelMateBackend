# Hotels Landing Page – Simple Filters

Context:
- Public landing page shows a list of hotel cards.
- No booking search here, just basic filtering of the hotel list.

## Requirements

### 1. Filter bar above the hotels list
- Text search input: filters by hotel name and city.
- City dropdown: populated from distinct `Hotel.city` values (plus "All towns").
- (Optional) Country dropdown if we store `Hotel.country`.
- (Optional) Tag chips (e.g. "Family", "Spa", "Business") using `Hotel.tags` or similar.
- Sort dropdown: "Featured" (default) and "Name A–Z".

### 2. Backend API ✅ IMPLEMENTED

#### Hotels List with Filters
**Endpoint:** `GET /api/hotel/public/`

**Supported query params:**
- `q` (optional): search in name, city, country (case-insensitive)
- `city` (optional): exact city match (case-insensitive)
- `country` (optional): exact country match (case-insensitive)
- `tags` (optional): comma-separated list (e.g., "Family,Spa")
- `sort` (optional): `name_asc` or `featured` (default)

**Example requests:**
```
GET /api/hotel/public/?q=killarney
GET /api/hotel/public/?city=Dublin&sort=name_asc
GET /api/hotel/public/?tags=Family,Spa
GET /api/hotel/public/?q=luxury&city=Cork&tags=Spa
```

**Response:** Array of hotel objects with basic info (see `HotelPublicSerializer`)

#### Filter Options Endpoint
**Endpoint:** `GET /api/hotel/public/filters/`

**Purpose:** Get all available filter options to populate dropdowns/chips

**Response:**
```json
{
  "cities": ["Dublin", "Cork", "Killarney", "Galway"],
  "countries": ["Ireland", "UK"],
  "tags": ["Business", "Family", "Luxury", "Spa"]
}
```

**Usage:** Call this once on page load to populate filter dropdowns and tag chips.

### 3. Frontend Implementation Guide

#### Step 1: Fetch Filter Options on Mount
```javascript
const [filterOptions, setFilterOptions] = useState({
  cities: [],
  countries: [],
  tags: []
});

useEffect(() => {
  fetch('/api/hotel/public/filters/')
    .then(res => res.json())
    .then(data => setFilterOptions(data));
}, []);
```

#### Step 2: Build Filter State
```javascript
const [filters, setFilters] = useState({
  q: '',
  city: '',
  country: '',
  tags: [],
  sort: 'featured'
});
```

#### Step 3: Fetch Hotels with Filters
```javascript
const fetchHotels = async () => {
  const params = new URLSearchParams();
  
  if (filters.q) params.append('q', filters.q);
  if (filters.city) params.append('city', filters.city);
  if (filters.country) params.append('country', filters.country);
  if (filters.tags.length) params.append('tags', filters.tags.join(','));
  if (filters.sort) params.append('sort', filters.sort);
  
  const response = await fetch(`/api/hotel/public/?${params}`);
  const hotels = await response.json();
  setHotels(hotels);
};

useEffect(() => {
  fetchHotels();
}, [filters]);
```

#### Step 4: Filter UI Components

**Search Input:**
```jsx
<input 
  type="text"
  placeholder="Search hotels or cities..."
  value={filters.q}
  onChange={(e) => setFilters({...filters, q: e.target.value})}
/>
```

**City Dropdown:**
```jsx
<select 
  value={filters.city}
  onChange={(e) => setFilters({...filters, city: e.target.value})}
>
  <option value="">All Cities</option>
  {filterOptions.cities.map(city => (
    <option key={city} value={city}>{city}</option>
  ))}
</select>
```

**Country Dropdown:**
```jsx
<select 
  value={filters.country}
  onChange={(e) => setFilters({...filters, country: e.target.value})}
>
  <option value="">All Countries</option>
  {filterOptions.countries.map(country => (
    <option key={country} value={country}>{country}</option>
  ))}
</select>
```

**Tag Chips:**
```jsx
<div className="tag-filters">
  {filterOptions.tags.map(tag => (
    <button
      key={tag}
      className={filters.tags.includes(tag) ? 'active' : ''}
      onClick={() => {
        const newTags = filters.tags.includes(tag)
          ? filters.tags.filter(t => t !== tag)
          : [...filters.tags, tag];
        setFilters({...filters, tags: newTags});
      }}
    >
      {tag}
    </button>
  ))}
</div>
```

**Sort Dropdown:**
```jsx
<select 
  value={filters.sort}
  onChange={(e) => setFilters({...filters, sort: e.target.value})}
>
  <option value="featured">Featured</option>
  <option value="name_asc">Name A–Z</option>
</select>
```

#### Step 5: Display Results
```jsx
{hotels.length === 0 ? (
  <div className="no-results">
    No hotels found for your filters.
  </div>
) : (
  <div className="hotels-grid">
    {hotels.map(hotel => (
      <HotelCard key={hotel.slug} hotel={hotel} />
    ))}
  </div>
)}
```

### 4. Hotel Model Fields for Filtering

#### Hotel Type Classification
Hotels now have a `hotel_type` field with predefined choices:

**Available hotel types:**
- Resort
- Spa Hotel
- Wellness Hotel
- Family Hotel
- Business Hotel
- Luxury Hotel
- Boutique Hotel
- Budget Hotel
- Hostel
- Aparthotel
- Eco Hotel
- Conference Hotel
- Beach Hotel
- Mountain Hotel
- Casino Hotel
- Golf Hotel
- Airport Hotel
- Adventure Hotel
- City Hotel
- Historic Hotel

**Usage in API:**
```
GET /api/hotel/public/?hotel_type=FamilyHotel
GET /api/hotel/public/?hotel_type=Resort&city=Dublin
```

**Filter options endpoint returns:**
```json
{
  "hotel_types": ["FamilyHotel", "Resort", "SpaHotel", ...]
}
```

#### Tags Field
Hotels also support a `tags` JSON field for flexible filtering:

```python
# In Django admin or via API:
hotel.tags = ["Family", "Spa", "Business"]
hotel.save()
```

**Common tag suggestions:**
- "Family"
- "Spa"
- "Business"
- "Luxury"
- "Budget"
- "Pet-Friendly"
- "Beach"
- "City Center"
- "Airport"
- "Romantic"

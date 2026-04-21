# Jaguar Re-Identification System Improvements

## Issues Fixed

### 1. **Similar Position Recognition Failure**
- **Problem**: Pictures of the same jaguar (Lwazo) from similar angles weren't being recognized
- **Root Cause**: Threshold set at 70% may be too strict for some viewing angles
- **Solution**: 
  - Now shows top 5 matching jaguars ranked by similarity
  - Allows manual linking to existing jaguars even below threshold
  - Users can make informed decisions based on similarity scores

### 2. **No Option to Link to Existing Jaguar**
- **Problem**: When similarity was below 70%, only option was to create a new jaguar
- **Solution**: Added comprehensive manual linking workflow:
  - Dialog shows top 5 most similar jaguars with their similarity scores
  - Each match displays thumbnail (if available), name, times seen, and similarity %
  - Warning indicator for jaguars without reference images
  - Click to link directly to any existing jaguar

### 3. **Jaguars Without Images**
- **Problem**: "Test 2" showed 42% match but had no image in database
- **Impact**: Made it hard to verify if it was actually the same jaguar
- **Solution**: 
  - Visual indicators show which jaguars lack reference images (⚠️ No reference image)
  - Users can still link to them but are warned
  - Database properly tracks images for each jaguar

## Technical Implementation

### Backend Changes

#### 1. **New Database Method: `get_top_matches()`**
**File**: `src/backend/database/database_sqlalchemy.py`
```python
def get_top_matches(self, query_embedding: List[float], top_n: int = 5) -> List[Dict]:
    """Get top N most similar jaguars ranked by similarity"""
```
- Computes similarity against all jaguars in database
- Returns sorted list with jaguar info, similarity scores, and image availability
- Includes `has_image` flag to indicate if jaguar has reference photos

#### 2. **New Database Method: `link_image_to_jaguar()`**
**File**: `src/backend/database/database_sqlalchemy.py`
```python
def link_image_to_jaguar(self, jaguar_id: str, image_url: Optional[str], 
                         local_path: Optional[str], similarity_score: float) -> bool:
    """Link an image to an existing jaguar (manual matching)"""
```
- Creates image record linked to existing jaguar
- Records sighting with similarity score
- Updates jaguar's last_seen and times_seen counters

#### 3. **Updated Classification Pipeline**
**File**: `src/backend/preprocessing.py`
- Now calls `get_top_matches()` during Stage 3 (Re-ID)
- Returns top matches in classification response
- Logs top 3 matches for debugging

#### 4. **New API Endpoint: `/link-to-existing`**
**File**: `src/backend/main.py`
```python
@app.post("/link-to-existing")
async def link_to_existing_jaguar(file, image_url, jaguar_id):
    """Link an uploaded image to an existing jaguar"""
```
- Validates image contains a jaguar
- Stores image in Azure Blob Storage or locally
- Links to specified jaguar in database
- Returns success confirmation

### Frontend Changes

#### 1. **Enhanced API Service**
**File**: `src/frontend/src/services/api.ts`
- Added `top_matches` to `identifyJaguar()` return type
- New function: `linkToExistingJaguar(file, jaguarId, imageUrl)`

#### 2. **Improved Naming Dialog**
**File**: `src/frontend/src/pages/JaguarReIdPage.tsx`

**New Features**:
- Displays top 5 matching jaguars from database
- Shows thumbnail, name, similarity %, times seen for each match
- Click any match to link current image to that jaguar
- Visual warning for jaguars without images
- Expanded dialog to accommodate match list (max-w-2xl, scrollable)

**New Handler**:
```typescript
const handleLinkToExisting = async (jaguarId: string, jaguarName: string) => {
  // Downloads image if URL, links to existing jaguar
}
```

## User Experience Improvements

### Before
1. Upload image of Lwazo from right side
2. System: "New jaguar detected (42% match with Test 2)"
3. Only option: Register as new jaguar
4. No way to see what "Test 2" looks like
5. Could create duplicate entry for same jaguar

### After
1. Upload image of Lwazo from right side
2. System: "New jaguar detected"
3. Dialog shows:
   - **Top Matches**:
     - Test 2: 42% similarity, 3 sightings ⚠️ No reference image
     - Lwazo: 38% similarity, 5 sightings [thumbnail shown]
     - Shadow: 31% similarity, 2 sightings [thumbnail shown]
   - Option to register as new
   - Option to link to any existing match
4. User clicks on existing jaguar → links image automatically
5. Avoids duplicates, builds better jaguar history

## Configuration

**Similarity Threshold**: 70% (unchanged)
- Location: `src/backend/config.py`
- Variable: `STAGE3_SIMILARITY_THRESHOLD = 0.70`
- Auto-match threshold remains at 70%
- Manual linking allowed at any similarity level

## Testing Recommendations

1. **Test with Lwazo images**:
   - Upload multiple angles of same jaguar
   - Verify top matches show correct individual
   - Test manual linking workflow

2. **Test with "Test 2"**:
   - Upload image that matches at 42%
   - Verify warning about no reference image
   - Link image to see if it adds reference photo

3. **Test threshold edge cases**:
   - Upload at 69% similarity (just below threshold)
   - Verify auto-match doesn't trigger
   - Verify manual link option available

## Database Schema Impact

**No schema changes required** - all existing tables support new functionality:
- `images` table links images to jaguars
- `sightings` table records all matches (auto and manual)
- `jaguars` table tracks times_seen and last_seen

## Performance Considerations

- `get_top_matches()` computes similarity for all jaguars in database
- For large databases (>1000 jaguars), may add ~1-2 seconds to classification
- Consider adding indices or caching if performance degrades
- Current implementation fine for <500 jaguars

## Future Enhancements

1. **Adjustable Threshold**: Let users adjust similarity threshold in UI
2. **Batch Linking**: Link multiple images to one jaguar at once
3. **Similarity Heatmap**: Visualize which body parts contribute to similarity score
4. **Merge Jaguars**: Tool to merge duplicate jaguar entries
5. **Confidence Badges**: Visual indicators for high/medium/low confidence matches

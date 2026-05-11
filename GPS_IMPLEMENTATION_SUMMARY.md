# GPS Extraction Implementation - Complete Flow

## What's Been Fixed

### 1. Backend (`/classify` endpoint) - NEW
- Extracts GPS coordinates from image EXIF after classification
- Logs GPS extraction:
  ```
  [Detector] ✓ GPS Coordinates Found:
  [Detector]   Latitude:  -1.2921°
  [Detector]   Longitude: 36.8219°
  ```
- Returns GPS in response:
  ```json
  {
    "success": true,
    "match": true,
    "jaguar_id": "...",
    "gps": {
      "latitude": -1.2921,
      "longitude": 36.8219,
      "has_gps": true
    }
  }
  ```

### 2. Backend (`/register` endpoint) - UPDATED
- Already extracted GPS, now logs it clearly
- Returns GPS in response with same structure

### 3. Backend (`/link-to-existing` endpoint) - UPDATED  
- Extracts GPS from image
- Returns GPS in response

### 4. Frontend (ResultsDisplay) - UPDATED
- Added GPS display section with MapPin icon
- Shows latitude and longitude to 4 decimal places
- Includes Google Maps link to view exact location
- Only displays if GPS data is available

### 5. Frontend (JaguarReIdPage) - UPDATED
- When identifying: GPS from `/classify` response is passed to ResultsDisplay
- When registering: GPS from `/register` response is passed to ResultsDisplay
- When linking: GPS from `/link-to-existing` response is passed to ResultsDisplay

## Two Main Scenarios

### Scenario 1: Identifying Existing Jaguar (MATCH FOUND)
Flow:
1. Upload image → API calls `/classify`
2. Backend extracts GPS from EXIF + performs classification
3. Returns: match info + GPS coordinates
4. Frontend shows "Match Found!" dialog **WITH GPS**
5. User sees: location coordinates + Google Maps link

### Scenario 2: Registering New Jaguar
Flow:
1. Upload image → API calls `/register`
2. Backend extracts GPS + validates jaguar + creates embedding
3. Saves to database with GPS coordinates
4. Returns: jaguar_id + GPS coordinates
5. Frontend shows registration dialog **WITH GPS**
6. User confirms and jaguar is registered with location data

## Database Storage
GPS data is saved in `image_metadata` table:
```
image_metadata:
  - image_id (FK to images)
  - latitude (float)
  - longitude (float)
  - location_name (optional)
  - camera_trap_id (optional)
  - photographer (optional)
  - notes (optional)
  - tags (optional)
```

## Test Your Image
Your test image has GPS coordinates:
- **Latitude**: -1.2921° (1° 17' 31.56" S)
- **Longitude**: 36.8219° (36° 49' 18.83" E)
- **Location**: Near Kenya/Tanzania border (Serengeti-Masai Mara region)

When you classify/register it, you'll see these exact coordinates displayed!

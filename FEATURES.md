# Jaguar Re-ID Features

## Recent Enhancements

### 1. Pre-Segmented Image Detection ✅
The system now intelligently detects if an image has already been segmented to avoid redundant processing:

**Detection Criteria:**
- **Transparency**: Checks for RGBA or LA image modes with transparent pixels
- **Size**: Images smaller than 500x500px are assumed to be cropped
- **Background Uniformity**: Checks if background has low variance (< 100), indicating a solid background

**Benefits:**
- Skips expensive SAM segmentation on pre-processed images
- Dramatically reduces processing time on CPU (30+ seconds → instant)
- Maintains quality for raw images that need full pipeline

**Implementation:** `backend/preprocessing.py::is_already_segmented()`

### 2. URL Image Loading ✅
Both frontend and backend now support loading images directly from URLs:

**Backend API:**
```python
POST /predict
- files: Optional[List[UploadFile]] - Traditional file uploads
- url1: Optional[str] - URL for first image
- url2: Optional[str] - URL for second image
```

**Frontend Features:**
- URL input field with link icon in each image uploader
- Press Enter or click "Load" to fetch image from URL
- Shows "Loaded from URL" indicator badge
- Automatically uses URLs if files not provided

**Use Cases:**
- Quick testing with online jaguar images
- Sharing comparisons via URLs
- Integration with external image databases

### 3. UI State Management ✅
Prevents data loss during analysis:

**Loading State Protection:**
- Image removal buttons disabled during analysis
- Drag-and-drop disabled while processing
- URL input disabled while loading
- Visual feedback with opacity and cursor changes

**User Experience:**
- Clear "Analysis in progress..." message on hover
- Loading spinner on submit button
- Can't accidentally remove images mid-analysis

### 4. Smart Processing Pipeline

**Full Pipeline** (Raw Images):
1. YOLO Detection → Bounding box around jaguar
2. SAM Segmentation → Precise mask with transparent background
3. Crop & Resize → 224x224 normalized tensor
4. ConvNeXT Embedding → 512-dim feature vector

**Fast Track** (Pre-Segmented):
1. ~~YOLO Detection~~ (skipped - already cropped)
2. ~~SAM Segmentation~~ (skipped - detected pre-processed)
3. Resize & Normalize → 224x224 tensor
4. ConvNeXT Embedding → 512-dim feature vector

## Performance Comparison

| Image Type | Detection | Segmentation | Total Time (CPU) |
|------------|-----------|--------------|------------------|
| Raw Image  | ~1-2s     | ~30-45s      | ~35-50s          |
| Pre-Segmented | Skipped | Skipped    | ~0.5-1s          |

**Speedup:** ~50x faster for pre-processed images!

## API Usage Examples

### File Upload (Original)
```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);

fetch('http://localhost:8000/predict', {
    method: 'POST',
    body: formData
});
```

### URL Loading (New)
```javascript
const formData = new FormData();
formData.append('url1', 'https://example.com/jaguar1.jpg');
formData.append('url2', 'https://example.com/jaguar2.jpg');

fetch('http://localhost:8000/predict', {
    method: 'POST',
    body: formData
});
```

### Mixed Mode
```javascript
const formData = new FormData();
formData.append('files', file1);  // Local file
formData.append('url2', 'https://example.com/jaguar2.jpg');  // URL

fetch('http://localhost:8000/predict', {
    method: 'POST',
    body: formData
});
```

## Configuration

### Backend Environment
```python
# config.py
DEVICE = get_device()  # Auto-detects CUDA/CPU
SAM_MODEL_PATH = "sam_vit_b_01ec64.pth"
YOLO_MODEL_PATH = "yolov8n.pt"
REID_MODEL_PATH = "models/convnext_arcface_jaguar_final.pth"
```

### Frontend Environment
```bash
# Development (.env)
VITE_API_URL=http://localhost:8000

# Production (.env.production)
VITE_API_URL=http://backend:8000
```

## Architecture

```
┌─────────────────┐
│   Frontend UI   │
│ React + Vite    │
└────────┬────────┘
         │ FormData (files OR urls)
         ↓
┌─────────────────┐
│   FastAPI API   │
│  /predict POST  │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
[Files]   [URLs]
    │         │ httpx.AsyncClient
    │    ┌────┴────┐
    │    │ Download│
    │    └────┬────┘
    └────┬────┘
         ↓
┌─────────────────────┐
│ is_already_segmented│
└────────┬────────────┘
         │
    ┌────┴────┐
    ↓         ↓
 [Yes]      [No]
Skip SAM   Full Pipeline
    │         │
    │    ┌────┴────┐
    │    │  YOLO   │
    │    │  SAM    │
    │    └────┬────┘
    └────┬────┘
         ↓
┌─────────────────┐
│ ConvNeXT Embed  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Cosine Similarity│
└─────────────────┘
```

## Testing

### Test with Pre-Segmented Images
```bash
# Both images already segmented (fast)
curl -X POST http://localhost:8000/predict \
  -F "url1=https://your-domain.com/jaguar_segmented_1.png" \
  -F "url2=https://your-domain.com/jaguar_segmented_2.png"
```

### Test with Raw Images
```bash
# Both images raw from camera trap (slow on CPU)
curl -X POST http://localhost:8000/predict \
  -F "url1=https://your-domain.com/jaguar_raw_1.jpg" \
  -F "url2=https://your-domain.com/jaguar_raw_2.jpg"
```

### Test Mixed
```bash
# One raw, one segmented (mixed performance)
curl -X POST http://localhost:8000/predict \
  -F "url1=https://your-domain.com/jaguar_raw.jpg" \
  -F "url2=https://your-domain.com/jaguar_segmented.png"
```

## Known Limitations

1. **SAM on CPU**: Still slow for raw images. Use GPU for production with raw camera-trap images.
2. **URL Timeout**: 30-second timeout for URL downloads. Very large images may fail.
3. **CORS**: Backend must allow frontend origin. Update `config.py::CORS_ORIGINS` if needed.
4. **False Positives**: Very small cropped images without transparency might trigger re-segmentation.

## Future Enhancements

- [ ] Batch processing support (multiple pairs)
- [ ] Progress indicators for SAM segmentation
- [ ] YOLOv8-seg as faster alternative to SAM
- [ ] GPU optimization guide for production
- [ ] Caching for frequently compared URLs
- [ ] Support for additional formats (WEBP, HEIC)

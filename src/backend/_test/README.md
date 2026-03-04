# Wildlife Classification System - Test Suite

## 📁 Project Structure

```
_test/
├── __init__.py                 # Test package initialization
├── pytest.ini                  # Pytest configuration
├── conftest.py                 # Shared pytest fixtures and configuration
├── README.md                   # This file
│
├── fixtures/                   # Test data and fixtures
│   ├── __init__.py
│   ├── test_images.py          # Image test data configuration
│   ├── test_videos.py          # Video test data configuration
│   └── test_image_urls.txt     # URLs for test images
│
├── unit/                       # Unit tests for individual components
│   ├── __init__.py
│   ├── test_stage1_pytest.py   # Stage 1 binary classifier tests
│   └── test_stage2_pytest.py   # Stage 2 species classifier tests
│
├── integration/                # Integration and end-to-end tests
│   ├── __init__.py
│   ├── test_api_endpoints.py   # API endpoint tests
│   ├── test_api_integration.py # Full API integration tests
│   ├── test_comprehensive.py   # Comprehensive system tests
│   ├── test_stage1_videos.py   # Stage 1 video processing tests
│   ├── test_stage2_videos.py   # Stage 2 video processing tests
│   └── test_combined_videos.py # Combined video pipeline tests
│
├── utils/                      # Test utilities and helpers
│   ├── __init__.py
│   ├── display_results.py      # Result display utilities
│   ├── display_stage2_results.py # Stage 2 specific displays
│   └── run_all_tests.py        # Test suite runner
│
└── reports/                    # Test reports and documentation
    └── TEST_RESULTS.md         # Detailed test results
```

## 🎯 Test Categories

### Unit Tests (`unit/`)
Tests for individual model stages in isolation:
- **Stage 1 Binary Classifier**: Tests big cat vs non-big-cat classification
- **Stage 2 Species Classifier**: Tests species identification for confirmed big cats

### Integration Tests (`integration/`)
End-to-end tests for the complete system:
- **API Endpoints**: Tests all FastAPI endpoints
- **Full Pipeline**: Tests the complete three-stage pipeline
- **Video Processing**: Tests video frame extraction and batch processing

### Test Fixtures (`fixtures/`)
Reusable test data:
- Image URLs from various sources (iNaturalist, stock photos)
- Video file paths and metadata
- Expected classification results

## 🚀 Running Tests

### Run All Tests
```bash
cd src/backend/_test
python -m pytest -v
```

### Run Specific Test Categories

**Unit Tests Only:**
```bash
python -m pytest unit/ -v
```

**Integration Tests Only:**
```bash
python -m pytest integration/ -v
```

**API Tests Only:**
```bash
python -m pytest integration/test_api_endpoints.py -v
```

### Run with Coverage
```bash
python -m pytest --cov=../ --cov-report=html
```

### Run with Verbose Output
```bash
python -m pytest -v -s
```

### Run Specific Test
```bash
python -m pytest unit/test_stage1_pytest.py::test_specific_function -v
```

## 📊 Test Summary

### Current Test Coverage

**Unit Tests:**
- ✅ Stage 1 Binary Classifier: 7 test images (100% big cat detection)
- ✅ Stage 2 Species Classifier: 5 species across multiple test cases

**Integration Tests:**
- ✅ API Health Endpoints: 2 tests
- ✅ URL Predictions: 2 tests (jaguar, dog)
- ✅ Binary Classification: 1 test
- ✅ Species Classification: 1 test
- ✅ File Upload: 2 tests (image, video)
- ✅ Batch Predictions: 1 test
- ✅ Error Handling: 3 tests
- ✅ Response Schema: 1 test

**Total: 20+ automated tests**

## 🎨 Test Data

### Image Test Sets
1. **Big Cats** (5 species):
   - Jaguar
   - Tiger  
   - Lion
   - Leopard
   - Cheetah

2. **Non-Big-Cats**:
   - Dog (Golden Retriever)
   - Elephant
   - Human
   - Inanimate objects (table, chair)

### Video Test Sets
Located in `../assets/videos/`:
- `cheetah.mp4` - Cheetah footage
- `leopard.mp4` - Leopard footage
- `lion.mp4` - Lion footage
- `elephant.mp4` - Elephant (non-big-cat)
- `gazelle.mp4` - Gazelle (non-big-cat)

## 🔧 Configuration

### pytest.ini
Global pytest configuration including:
- Test discovery patterns
- Asyncio mode settings
- Warning filters
- Output formatting

### conftest.py
Shared fixtures and setup:
- API client fixtures
- Test data loaders
- Cleanup handlers

## 📈 Performance Benchmarks

**Average Response Times (CPU):**
- Image prediction: ~4-5 seconds
- Video frame (first): ~17 seconds (model warmup)
- Subsequent requests: ~3 seconds

**Accuracy:**
- Big cat detection (Stage 1): 100%
- Species classification (Stage 2): 95-99%
- Overall system accuracy: 100% (on test set)

## 🛠️ Development Workflow

### Adding New Tests

1. **Unit Test**: Add to `unit/` for testing individual components
   ```python
   # unit/test_new_feature.py
   import pytest
   
   def test_new_functionality():
       # Your test here
       assert True
   ```

2. **Integration Test**: Add to `integration/` for end-to-end testing
   ```python
   # integration/test_new_integration.py
   import pytest
   import httpx
   
   def test_api_feature():
       # Your API test here
       pass
   ```

3. **Test Data**: Add to `fixtures/` for reusable test data
   ```python
   # fixtures/test_new_data.py
   TEST_DATA = {
       # Your test data
   }
   ```

### Test Best Practices

- ✅ Use descriptive test names: `test_classify_jaguar_image_returns_correct_species()`
- ✅ Group related tests in classes: `class TestBinaryClassifier:`
- ✅ Use fixtures for setup/teardown and data
- ✅ Test both success and failure cases
- ✅ Include performance/timeout tests for async operations
- ✅ Document expected behavior in docstrings
- ✅ Keep tests independent and idempotent

## 🐛 Debugging Tests

### Run with Debugging
```bash
python -m pytest -v -s --pdb
```

### Show Print Statements
```bash
python -m pytest -v -s
```

### Run Last Failed Tests
```bash
python -m pytest --lf
```

### Generate HTML Report
```bash
python -m pytest --html=reports/test_report.html --self-contained-html
```

## 📝 Documentation

- **Test Results**: See `reports/TEST_RESULTS.md` for detailed results
- **API Docs**: http://localhost:8000/docs when server is running
- **Pipeline Docs**: See `../docs/` for architecture documentation

## 🤝 Contributing

When adding tests:
1. Follow the existing structure
2. Add documentation to relevant README sections
3. Ensure all tests pass before committing
4. Update `reports/TEST_RESULTS.md` with new results

## 📞 Support

For issues or questions about tests:
1. Check test output and error messages
2. Review the test documentation
3. Verify server is running for integration tests
4. Check model files are properly loaded

---

**Last Updated**: March 1, 2026
**Test Suite Version**: 2.0
**Python Version**: 3.9+
**Pytest Version**: 8.4+

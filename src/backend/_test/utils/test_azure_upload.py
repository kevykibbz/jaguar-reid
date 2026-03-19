"""Test Azure Storage connection and upload"""
import sys
import io
from PIL import Image
from services.azure_storage import AzureStorageManager

print("="*70)
print("TESTING AZURE STORAGE CONNECTION")
print("="*70)

try:
    # Initialize Azure Storage
    print("\n1. Initializing Azure Storage Manager...")
    azure_storage = AzureStorageManager()
    
    print(f"\n2. Checking if Azure Storage is available...")
    if not azure_storage.is_available():
        print("✗ Azure Storage is NOT available")
        print("  Check your .env file for AZURE_STORAGE_CONNECTION_STRING")
        sys.exit(1)
    
    print("✓ Azure Storage is available!")
    
    # Create a small test image
    print("\n3. Creating test image...")
    test_image = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    test_image.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()
    print(f"✓ Test image created ({len(image_bytes)} bytes)")
    
    # Test upload
    print("\n4. Testing upload to Azure Blob Storage...")
    try:
        success, blob_url = azure_storage.upload_image(
            image_bytes=image_bytes,
            jaguar_id="test_jaguar",
            filename="test.jpg"
        )
        
        if success:
            print(f"✓ Upload successful!")
            print(f"  Blob URL: {blob_url}")
        else:
            print(f"✗ Upload failed (no URL returned)")
    except Exception as upload_error:
        print(f"✗ Upload failed with exception:")
        print(f"  Error: {upload_error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED - Azure Storage is working!")
    print("="*70)
    
except Exception as e:
    print(f"\n✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

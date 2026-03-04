"""
Image metadata extraction utilities.
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_image_metadata(image_bytes: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
    """
    Extract metadata from image bytes.
    
    Args:
        image_bytes: Image file content as bytes
        filename: Original filename
    
    Returns:
        Dictionary with image metadata
    """
    metadata = {
        'file_name': filename,
        'file_size': len(image_bytes),
        'format': None,
        'width': None,
        'height': None,
        'latitude': None,
        'longitude': None,
        'camera_model': None,
        'date_taken': None,
        'location_name': None
    }
    
    try:
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Basic info
        metadata['format'] = image.format
        metadata['width'] = image.width
        metadata['height'] = image.height
        
        # EXIF data
        exif_data = image._getexif() if hasattr(image, '_getexif') else None
        
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                
                # Camera model
                if tag_name == 'Model':
                    metadata['camera_model'] = str(value)
                
                # Date taken
                elif tag_name == 'DateTimeOriginal' or tag_name == 'DateTime':
                    metadata['date_taken'] = str(value)
                
                # GPS data
                elif tag_name == 'GPSInfo':
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag_name] = value[gps_tag_id]
                    
                    # Extract latitude/longitude
                    if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                        lat = _convert_to_degrees(gps_data['GPSLatitude'])
                        if gps_data['GPSLatitudeRef'] == 'S':
                            lat = -lat
                        metadata['latitude'] = lat
                    
                    if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                        lon = _convert_to_degrees(gps_data['GPSLongitude'])
                        if gps_data['GPSLongitudeRef'] == 'W':
                            lon = -lon
                        metadata['longitude'] = lon
        
        logger.info(f"Extracted metadata: {metadata['width']}x{metadata['height']} {metadata['format']}")
        
    except Exception as e:
        logger.warning(f"Failed to extract some metadata: {e}")
    
    return metadata


def _convert_to_degrees(value) -> float:
    """Convert GPS coordinates to degrees."""
    try:
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    except:
        return 0.0


def get_location_name(latitude: float, longitude: float) -> Optional[str]:
    """
    Get location name from coordinates using reverse geocoding.
    This is a placeholder - you would use an actual geocoding service.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Location name or None
    """
    # TODO: Implement reverse geocoding using a service like:
    # - OpenStreetMap Nominatim (free)
    # - Google Maps Geocoding API
    # - Azure Maps
    
    if latitude and longitude:
        return f"Location: {latitude:.6f}, {longitude:.6f}"
    return None

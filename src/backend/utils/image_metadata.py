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
        
        logger.info(f"EXIF data present: {exif_data is not None}")
        if exif_data:
            logger.info(f"EXIF tags found: {list(exif_data.keys())}")
        
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
                    logger.info(f"GPSInfo found: {value}")
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag_name] = value[gps_tag_id]
                    
                    logger.info(f"GPS data extracted: {gps_data}")
                    
                    # Extract latitude/longitude
                    if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                        lat = _convert_to_degrees(gps_data['GPSLatitude'])
                        if gps_data['GPSLatitudeRef'] == 'S':
                            lat = -lat
                        metadata['latitude'] = lat
                        logger.info(f"Latitude extracted: {lat}")
                    
                    if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                        lon = _convert_to_degrees(gps_data['GPSLongitude'])
                        if gps_data['GPSLongitudeRef'] == 'W':
                            lon = -lon
                        metadata['longitude'] = lon
                        logger.info(f"Longitude extracted: {lon}")
        
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


async def get_location_name(latitude: float, longitude: float) -> Optional[str]:
    """
    Reverse geocode coordinates to a human-readable location name using
    OpenStreetMap Nominatim (free, no API key required).
    Returns city/town + country, or None on failure.
    """
    try:
        import httpx
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": latitude, "lon": longitude, "format": "json"}
        headers = {"User-Agent": "patterns-ai-wildlife/1.0 (jaguar-reid)"}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
        address = data.get("address", {})
        # Build a short readable name: city/town/village + country
        place = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
            or address.get("state")
        )
        country = address.get("country")
        if place and country:
            return f"{place}, {country}"
        return data.get("display_name", "").split(",")[0] or None
    except Exception as e:
        logger.warning(f"Reverse geocoding failed for ({latitude}, {longitude}): {e}")
        return None

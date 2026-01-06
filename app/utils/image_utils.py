"""
Image utilities for multimodal chat support.

Handles image encoding, validation, and format conversion for AI APIs.
"""

import base64
import io
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image


# Supported image formats
SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "gif", "webp"]
MAX_IMAGE_SIZE_MB = 20  # Maximum image size in MB
MAX_DIMENSION = 4096  # Maximum width/height


def encode_image_to_base64(image_bytes: bytes) -> str:
    """
    Encode image bytes to base64 string.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def get_image_media_type(image_bytes: bytes) -> str:
    """
    Detect image media type from bytes.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Media type string (e.g., 'image/png')
    """
    # Check magic bytes
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif image_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "image/webp"
    else:
        # Default to PNG
        return "image/png"


def validate_image(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Validate image for API submission.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"Image too large ({size_mb:.1f}MB). Max: {MAX_IMAGE_SIZE_MB}MB"

    # Try to open with PIL
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return False, f"Image too large ({width}x{height}). Max: {MAX_DIMENSION}x{MAX_DIMENSION}"

    except Exception as e:
        return False, f"Invalid image: {str(e)}"

    return True, None


def resize_image_if_needed(image_bytes: bytes, max_dim: int = 2048) -> bytes:
    """
    Resize image if it exceeds maximum dimensions.

    Args:
        image_bytes: Raw image bytes
        max_dim: Maximum dimension (width or height)

    Returns:
        Resized image bytes (or original if no resize needed)
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        if width <= max_dim and height <= max_dim:
            return image_bytes

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))

        # Resize
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        img_format = img.format or "PNG"
        img.save(output, format=img_format)
        return output.getvalue()

    except Exception:
        return image_bytes


def prepare_image_for_openai(image_bytes: bytes) -> Dict[str, Any]:
    """
    Prepare image for OpenAI API (GPT-4V, GPT-5, etc).

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary in OpenAI image format
    """
    media_type = get_image_media_type(image_bytes)
    base64_data = encode_image_to_base64(image_bytes)

    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{media_type};base64,{base64_data}",
            "detail": "auto"
        }
    }


def prepare_image_for_anthropic(image_bytes: bytes) -> Dict[str, Any]:
    """
    Prepare image for Anthropic API (Claude).

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary in Anthropic image format
    """
    media_type = get_image_media_type(image_bytes)
    base64_data = encode_image_to_base64(image_bytes)

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64_data
        }
    }


def prepare_image_for_google(image_bytes: bytes) -> Dict[str, Any]:
    """
    Prepare image for Google Gemini API.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary in Gemini format (for inline_data)
    """
    media_type = get_image_media_type(image_bytes)
    base64_data = encode_image_to_base64(image_bytes)

    return {
        "inline_data": {
            "mime_type": media_type,
            "data": base64_data
        }
    }


def build_multimodal_message_openai(text: str, images: List[bytes]) -> List[Dict[str, Any]]:
    """
    Build multimodal message content for OpenAI.

    Args:
        text: Text message
        images: List of image bytes

    Returns:
        List of content parts for OpenAI messages
    """
    content = []

    # Add images first
    for img_bytes in images:
        content.append(prepare_image_for_openai(img_bytes))

    # Add text
    if text:
        content.append({
            "type": "text",
            "text": text
        })

    return content


def build_multimodal_message_anthropic(text: str, images: List[bytes]) -> List[Dict[str, Any]]:
    """
    Build multimodal message content for Anthropic.

    Args:
        text: Text message
        images: List of image bytes

    Returns:
        List of content parts for Anthropic messages
    """
    content = []

    # Add images first
    for img_bytes in images:
        content.append(prepare_image_for_anthropic(img_bytes))

    # Add text
    if text:
        content.append({
            "type": "text",
            "text": text
        })

    return content


def build_multimodal_parts_google(text: str, images: List[bytes]) -> List[Any]:
    """
    Build multimodal parts for Google Gemini.

    Args:
        text: Text message
        images: List of image bytes

    Returns:
        List of parts for Gemini content
    """
    parts = []

    # Add images first
    for img_bytes in images:
        parts.append(prepare_image_for_google(img_bytes))

    # Add text
    if text:
        parts.append(text)

    return parts


def get_image_info(image_bytes: bytes) -> Dict[str, Any]:
    """
    Get image information for display.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dictionary with image info
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return {
            "width": img.size[0],
            "height": img.size[1],
            "format": img.format,
            "mode": img.mode,
            "size_kb": len(image_bytes) / 1024
        }
    except Exception as e:
        return {
            "error": str(e),
            "size_kb": len(image_bytes) / 1024
        }

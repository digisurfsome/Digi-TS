"""
Utility modules for Digi-TS.
"""

from app.utils.image_utils import (
    encode_image_to_base64,
    get_image_media_type,
    validate_image,
    resize_image_if_needed,
    prepare_image_for_openai,
    prepare_image_for_anthropic,
    prepare_image_for_google,
    build_multimodal_message_openai,
    build_multimodal_message_anthropic,
    build_multimodal_parts_google,
    get_image_info,
    SUPPORTED_FORMATS,
)

__all__ = [
    "encode_image_to_base64",
    "get_image_media_type",
    "validate_image",
    "resize_image_if_needed",
    "prepare_image_for_openai",
    "prepare_image_for_anthropic",
    "prepare_image_for_google",
    "build_multimodal_message_openai",
    "build_multimodal_message_anthropic",
    "build_multimodal_parts_google",
    "get_image_info",
    "SUPPORTED_FORMATS",
]

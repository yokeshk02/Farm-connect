import os
import uuid
from io import BytesIO
from PIL import Image
from werkzeug.datastructures import FileStorage
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PHOTOS_PER_MACHINERY = 5


def is_allowed_extension(filename: str) -> bool:
    """Check if the filename has an allowed image extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_photo(
    file_storage: FileStorage,
    upload_dir: str | None = None,
    storage_backend=None,
) -> str:
    """Validate image type, file size, and image content, then save with a generated UUID filename.
    
    Returns:
        The web-accessible relative or absolute URL.
        
    Raises:
        ValueError: If file is missing, exceeds size, has invalid extension, or corrupt image content.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file uploaded.")

    filename = file_storage.filename.strip()
    if not is_allowed_extension(filename):
        raise ValueError("Invalid image type. Allowed formats: PNG, JPG, JPEG, WEBP.")

    # Check file size by seeking
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    if file_size <= 0:
        raise ValueError("Uploaded file is empty.")

    if file_size > MAX_FILE_SIZE:
        raise ValueError("Image file size exceeds the 5 MB limit.")

    # Validate image data using Pillow
    try:
        img = Image.open(file_storage.stream)
        img.verify()  # Verify integrity without decoding fully
        img_format = (img.format or "").upper()
        if img_format not in ("PNG", "JPEG", "WEBP"):
            raise ValueError("File content is not a supported image format.")
    except Exception as e:
        raise ValueError(f"Corrupt or invalid image file: {str(e)}")

    # Rewind stream before saving
    file_storage.seek(0)
    # Reopen image to re-encode safely (stripping any potential malicious payloads or EXIF metadata)
    img_to_save = Image.open(file_storage.stream)

    # Determine safe extension and MIME type
    orig_ext = filename.rsplit(".", 1)[1].lower()
    safe_ext = "jpg" if orig_ext in ("jpg", "jpeg") else orig_ext
    unique_filename = f"{uuid.uuid4().hex}.{safe_ext}"

    # Re-encode to in-memory BytesIO buffer
    buffer = BytesIO()
    content_type = "image/jpeg"
    if safe_ext == "jpg":
        if img_to_save.mode in ("RGBA", "P"):
            img_to_save = img_to_save.convert("RGB")
        img_to_save.save(buffer, format="JPEG", quality=85, optimize=True)
    elif safe_ext == "webp":
        img_to_save.save(buffer, format="WEBP", quality=85)
        content_type = "image/webp"
    else:
        img_to_save.save(buffer, format="PNG", optimize=True)
        content_type = "image/png"

    buffer.seek(0)

    # Delegate storage persistence to pluggable storage backend
    from app.services.storage_service import get_storage_backend, LocalStorageBackend

    if storage_backend is not None:
        storage = storage_backend
    else:
        try:
            storage = get_storage_backend()
            if upload_dir and isinstance(storage, LocalStorageBackend):
                storage = LocalStorageBackend(base_dir=upload_dir)
        except Exception:
            storage = LocalStorageBackend(base_dir=upload_dir)

    return storage.save(buffer, unique_filename, content_type)


def delete_machinery_photo(photo_url: str) -> bool:
    """Safely delete a machinery photo using the active storage backend."""
    if not photo_url:
        return False
    try:
        from app.services.storage_service import get_storage_backend
        backend = get_storage_backend()
        return backend.delete(photo_url)
    except Exception as e:
        try:
            current_app.logger.warning(f"Could not delete machinery photo {photo_url}: {e}")
        except Exception:
            pass
        return False

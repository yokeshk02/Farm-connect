import os
import uuid
from PIL import Image
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PHOTOS_PER_MACHINERY = 5


def is_allowed_extension(filename: str) -> bool:
    """Check if the filename has an allowed image extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_photo(file_storage: FileStorage, upload_dir: str) -> str:
    """Validate image type, file size, and image content, then save with a generated UUID filename.
    
    Returns:
        The web-accessible relative URL (e.g. '/static/uploads/machinery/<uuid>.jpg').
        
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
    # Reopen image to save safely (stripping any potential malicious payloads)
    img_to_save = Image.open(file_storage.stream)

    # Determine safe extension
    orig_ext = filename.rsplit(".", 1)[1].lower()
    safe_ext = "jpg" if orig_ext in ("jpg", "jpeg") else orig_ext

    # Generate unique UUID filename
    unique_filename = f"{uuid.uuid4().hex}.{safe_ext}"
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = os.path.join(upload_dir, unique_filename)

    # Save safely
    if safe_ext == "jpg":
        # Convert RGBA to RGB for JPEG compatibility
        if img_to_save.mode in ("RGBA", "P"):
            img_to_save = img_to_save.convert("RGB")
        img_to_save.save(destination_path, format="JPEG", quality=85, optimize=True)
    elif safe_ext == "webp":
        img_to_save.save(destination_path, format="WEBP", quality=85)
    else:
        img_to_save.save(destination_path, format="PNG", optimize=True)

    return f"/static/uploads/machinery/{unique_filename}"

from pathlib import Path

# 配置文件上传路径
Base_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Base_DIR / "uploads"

# SET 集合 可去重
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif",".docx",".pdf"}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg", 
    "image/png", 
    "image/gif",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/pdf"
}

MAX_FILE_SIZE = 1024 * 1024 * 10  # 10MB 最大文件大小

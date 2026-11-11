from fastapi import HTTPException, UploadFile, status
from pathlib import Path
# from config import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE
from ..config import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE

def validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required",
        )
    # 拿到文件扩展名 后缀 并转换为小写
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{ext}",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{file.content_type}",
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            # 413 请求实体过大
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="文件大小不能超过10MB",
        )

def save_file(file: UploadFile) -> dict:
    # 保存文件到指定目录
    return {
        "filename": file.filename
    }

from fastapi import HTTPException, UploadFile, status
from pathlib import Path
# from config import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE
from ..config import ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE, UPLOAD_DIR
# python 内置模块 用于生成唯一标识符
import uuid

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

# dict 返回值 包含文件名和文件路径的字典
# Parents 父目录 没有自动创建父级目录 exist_ok=True 存在则不创建
def save_file(file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    original_name = Path(file.filename).name
    # 生成唯一标识符
    # stem 文件名 不包含扩展名
    # uuid4().hex 生成 32位的十六进制字符串 随机数
    # suffix 文件扩展名
    # avatar.png -> avatar_1234567890abcdef.png
    unique_name = f"{Path(original_name).stem}_{uuid.uuid4().hex}{Path(original_name).suffix}"
    target_path = UPLOAD_DIR / unique_name

    # 创建一个写入流
    # with 语句 上下文管理器 会自动关闭文件
    # as 取个别名 用于在 with 语句中引用文件对象
    with target_path.open("wb") as buffer:
        # 每次读取 1MB 数据 写入到缓冲区
        # := 同时完成赋值和判断 赋值并且判断是否为空
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)

    return {
        "original_name": original_name,
        "saved_name": unique_name,
        "size": target_path.stat().st_size,
    }

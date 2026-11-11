from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.file_service import validate_file, save_file

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload")
# UploadFile 是 FastAPI 用来接收上传文件的对象
# 它把客户端通过 multipart/form-data 格式上传的文件封装成一个带元数据的文件句柄
# 也就是说 UploadFile 会把前端传过来的文件处理好 你可以直接使用 file 来读取文件内容
# ... 说明参数是必填的 取自 form-data 中的 file 字段
async def upload_file(file: UploadFile = File(...)):
    # 验证文件类型
    validate_file(file)
    result = save_file(file)
    return {
        "code":0,
        "message":"成功",
        "data":result
    }

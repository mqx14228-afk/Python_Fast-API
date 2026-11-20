from fastapi import FastAPI
# cors 跨域资源中间件
# from fastapi.middleware.cors import CORSMiddleware
# 当前目录 相对路径
from .routers import upload
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="File Upload API")

# 中间件
app.add_middleware(
    CORSMiddleware,
    # 允许的来源 白名单
    # Access-Control-Allow-Origin: * 允许所有来源访问
    allow_origins=["http://localhost:5173"],
    # 是否允许携带凭证 cookie
    allow_credentials=True,
    # 允许的请求方法
    # Access-Control-Allow-Methods: * 允许所有请求方法
    allow_methods=["POST","GET"], 
    # 允许的请求头
    # Access-Control-Allow-Headers: * 允许所有请求头 
    # Authorization
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"message":"File Upload API","docs":"/docs"}

app.include_router(upload.router)

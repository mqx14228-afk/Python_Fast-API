from fastapi import FastAPI
# cors 跨域资源中间件
# from fastapi.middleware.cors import CORSMiddleware
# 当前目录 相对路径
from .routers import upload

app = FastAPI(title="File Upload API")

@app.get("/")
def root():
    return {"message":"File Upload API","docs":"/docs"}

app.include_router(upload.router)

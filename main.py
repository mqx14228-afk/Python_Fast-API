from fastapi import FastAPI
# 引入数据库模块
from database import engine, Base
from routers import users, posts

import models

# 实例化 FastAPI 应用实例
# python 实例化不用 new
# 自动地将 __init__ 方法调用 便捷

# ORM 自动根据模型类创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blog API",
    description="FastAPI + SQLAlchemy 博客系统",
    version="1.0.0",
)

# 装饰器模式
@app.get("/")
def read_root():
    return {"message":"Blog API","docs":"/docs"}

# 模块路由 包含 users 模块的路由
app.include_router(users.router)
# 模块路由 包含 posts 模块的路由
app.include_router(posts.router)

# Depends 依赖注入 从依赖注入容器中获取依赖项
# HTTPException 异常处理 用来抛出 HTTP 异常 用于处理错误情况
from fastapi import APIRouter, Depends, HTTPException, status
from schemas import UserCreate, UserResponse, UserUpdate
from database import get_db
from sqlalchemy.orm import Session
from models import User
from schemas import UserCreate, UserResponse, UserUpdate

import crud

# fastapi 自带 api 文档 swagger ui
router = APIRouter(prefix="/users", tags=["用户管理"])

# 路由装饰器 + restful 资源
# 201 创建成功
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# Depends 才是让 FastAPI 去调用 get_db() 方法的开关
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """创建用户"""
    # controller 控制器
    # 分层架构 controller -> service -> repository
    existing = crud.get_user_by_email(db, user_in.email)
    if(existing):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已经注册",
        )
    return crud.create_user(db, user_in)

# 查用户列表 分页查询
@router.get("/", response_model=list[UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取所有用户"""
    return crud.get_users(db, skip=skip, limit=limit)

# 用户详情
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user

# 修改用户
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    """更新用户"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return crud.update_user(db, user, user_in)

# 删除用户
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    user = crud.get_user(db, user_id)
    print(f"delete_user:user_id = {user_id},user = {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    crud.delete_user(db, user)

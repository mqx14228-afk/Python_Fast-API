from sqlalchemy.orm import Session
from models import User, Post
from sqlalchemy import select
from schemas import UserCreate, UserResponse, UserUpdate, PostCreate, PostResponse, PostUpdate
# 导入 bcrypt 模块 密码加密
import bcrypt

def get_user_by_email(db: Session, email: str) -> User | None:
    # orm 映射 查询 sql 语句 根据邮箱查询用户
    stmt = select(User).where(User.email == email)
    # 执行查询 拿到第一个结果
    return db.scalars(stmt).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    # orm 映射 创建用户
    """创建用户"""
    hashed = bcrypt.hashpw(
        user_in.password.encode("utf-8"), 
        bcrypt.gensalt()
    ).decode("utf-8")

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed,
        is_active=True,
    )
    # 执行创建
    db.add(db_user) # insert
    db.commit() # 提交事务
    db.refresh(db_user) # 刷新用户实例 获取最新数据
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    # orm 映射 查询所有用户 分页查询
    """获取所有用户"""
    stmt = select(User).offset(skip).limit(limit)
    return db.scalars(stmt).all()

def get_user(db: Session, user_id: int) -> User | None:
    # orm 映射 查询用户详情
    """获取用户详情"""
    stmt = select(User).where(User.id == user_id)
    return db.scalars(stmt).first()

def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    # orm 映射 更新用户信息
    """更新用户信息"""
    if user_in.username:
        user.username = user_in.username
    if user_in.email:
        user.email = user_in.email
    if user_in.password:
        hashed = bcrypt.hashpw(
            user_in.password.encode("utf-8"), 
            bcrypt.gensalt()
        ).decode("utf-8")
        user.hashed_password = hashed
    db.commit()
    db.refresh(user)
    return user

# 删除用户
def delete_user(db: Session, user: User) -> None:
    # orm 映射 删除用户
    """删除用户"""
    db.delete(user)
    db.commit()

def create_post(db: Session, post_in: PostCreate, user_id: int) -> Post:
    # orm 映射 创建文章 为指定用户创建
    """创建文章"""
    db_post = Post(
        title=post_in.title,
        content=post_in.content,
        published=post_in.published,
        user_id=user_id,
    )
    db.add(db_post) # orm sql 处理 变成了对象上的方法 简化了 sql 编写 面向对象操作
    db.commit()
    db.refresh(db_post)
    return db_post

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> list[Post]:
    # orm 映射 查询文章列表 分页查询
    """获取文章列表"""
    stmt = select(Post).offset(skip).limit(limit)
    return list[Post](db.scalars(stmt).all())

def get_post(db: Session, post_id: int) -> Post | None:
    # 根据文章 id 查询文章
    return db.get(Post, post_id)

def delete_post(db: Session, post: Post) -> None:
    # orm 映射 删除文章
    """删除文章"""
    db.delete(post)
    db.commit()

def get_user_posts(db: Session, user_id: int) -> list[Post]:
    # orm 映射 查询指定用户的文章列表
    """获取指定用户的所有文章"""
    stmt = select(Post).where(Post.user_id == user_id)
    return list[Post](db.scalars(stmt).all())

def update_post(db: Session, post: Post, post_in: PostUpdate) -> Post:
    # orm 映射 更新文章信息
    """更新文章信息（只更新传了的字段）"""
    update_data = post_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    # 提交事务
    db.commit()
    db.refresh(post)
    return post

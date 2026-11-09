# 定义数据库表模型类

# datetime 模块 python 内置模块
# 内置模块 安装的第三方模块 自定义模块
from datetime import datetime
# 定义数据库表字段类型
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
# Mapped 定义数据库表字段类型 int str datetime bool list
# mapped_column 定义这一列的约束（主键、非空等）
# relationship 定义数据库表字段关联关系 跨表关联
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    # 关联关系 拿到一个作者 访问其所有文章
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(5000))
    # 是否发布 默认不发布
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    # 真正负责两张表绑定的，是 Post 里的 user_id = ForeignKey("users.id") 外键
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # 关联关系 拿到一篇文章 访问其作者
    author: Mapped["User"] = relationship(
        back_populates="posts"
    )

# crud 操作 请求体 查询参数 路由 params 是否符合 schema 约束
# 输出的约束
from datetime import datetime
# pydantic 模型 用来定义请求体 查询参数 路由 params 是否符合 schema 约束
from pydantic import BaseModel, Field,EmailStr,ConfigDict

class UserCreate(BaseModel):
    username:str = Field(min_length=3,max_length=50,example=["zhangsan"])
    email:EmailStr = Field(example=["zhang@example.com"])
    password:str = Field(min_length=8,max_length=100)

# UserResponse 用户响应模型 用来定义用户响应的字段和约束
class UserResponse(BaseModel):
    # 直接把 SQLAlchemy ORM 的数据库实体 User 对象丢给它，不需要手动转字典，Pydantic 自动去读对象上的 .id、.username 这些属性
    # from_attributes=True 从数据库实体对象中读取属性值 而不是从模型定义中读取
    # 过滤某些字段 不返回密码字段
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

class UserUpdate(BaseModel):
    username: str | None = Field(default=None,min_length=3,max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None,min_length=8,max_length=100)
    is_active: bool | None = None

# 文章创建模型
class PostCreate(BaseModel):
    title: str = Field(min_length=1,max_length=200,example=["文章标题"])
    content: str = Field(min_length=1,max_length=5000,example=["文章内容"])
    published: bool = Field(default=False)

class PostResponse(BaseModel):
    """返回的文章数据"""
    # 从对象中读取属性值 
    # 过滤某些字段 不返回密码字段
    # Post 实例 -> ConfigDict 转化为 dict 格式
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    published: bool
    created_at: datetime
    updated_at: datetime
    user_id: int

# 文章更新模型 所有字段都可选
class PostUpdate(BaseModel):
    title: str | None = Field(default=None,min_length=1,max_length=200)
    content: str | None = Field(default=None,min_length=1,max_length=5000)
    published: bool | None = Field(default=None)

# 文章详情模型
class PostWithAuthor(PostResponse):
    """文章 + 作者信息（用于列表展示）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    published: bool
    created_at: datetime
    author: UserResponse # 嵌套另一个 Pydantic 模型

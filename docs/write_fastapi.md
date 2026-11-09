# 写 FastAPI 接口的流程

> 一句话：一个接口 = 路由（收请求）+ schema（校验入参 / 过滤出参）+ crud（读写数据库）+ model（表结构）。
> 本文以「创建用户」「分页查询用户」为例，代码全部对应当前项目。

## 一、请求走一遍的链路

```text
HTTP 请求
   │
   ▼
routers/users.py     路由：URL、方法、状态码，Depends(get_db) 拿会话
   │
   ▼
schemas.py           校验请求体；response_model 过滤返回字段
   │
   ▼
crud.py              真正读写库：select / add / commit / refresh
   │
   ▼
models.py            ORM 实体，映射到 users 表
   │
   ▼
database.py          engine / SessionLocal
```

分层职责：**路由只管流程和报错，crud 只管数据库，schema 只管格式**。别把 SQL 写进路由，也别在 crud 里抛 HTTP 异常。

## 二、写代码的顺序

| 顺序 | 文件 | 写什么 | 缺了会怎样 |
| --- | --- | --- | --- |
| 0 | `database.py` | engine、SessionLocal、Base、get_db | 已有，前置地基 |
| 1 | `models.py` | `class User(Base)`，表结构 | 没有表，crud 无从下手 |
| 2 | `schemas.py` | `UserCreate`、`UserResponse`、`UserUpdate` | 入参无法校验，密码会泄露 |
| 3 | `crud.py` | `create_user`、`get_users` 等函数 | 路由里会堆满 SQL |
| 4 | `routers/users.py` | `APIRouter` + `@router.post/get` | 没有 URL 可访问 |
| 5 | `main.py` | `include_router(users.router)` | 路由写了但访问不到 |
| 6 | 运行验证 | `uvicorn main:app --reload` | —— |

口诀：**表 → 格式 → 操作 → 接口 → 注册 → 验证**。

## 三、第 1 步 models.py：先有表

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

注意列名是 `hashed_password`，不是 `password`：**数据库里只存哈希**，明文密码不落库、不返回。

## 四、第 2 步 schemas.py：三个模型各司其职

同一个用户，三种用途要拆成三个类：

```python
class UserCreate(BaseModel):          # 入参：注册时提交的字段
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)   # 明文，只在入参出现

class UserResponse(BaseModel):        # 出参：返回给前端的字段
    model_config = ConfigDict(from_attributes=True)       # 允许直接传 ORM 对象
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    # 没有 password / hashed_password → 永远不会返回

class UserUpdate(BaseModel):          # 入参：补丁式更新，全部可选
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
```

两个关键点：

- `from_attributes=True`：让 Pydantic 直接读 ORM 对象的 `.id`、`.username`，不用手动转字典
- **入参和出参必须分开**，否则 `UserResponse` 会把 `hashed_password` 一起吐给前端

## 五、第 3 步 crud.py：只做数据库操作

```python
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalars(select(User).where(User.email == email)).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed = bcrypt.hashpw(
        user_in.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed,
        is_active=True,
    )
    db.add(db_user)        # INSERT
    db.commit()            # 提交事务
    db.refresh(db_user)    # 回读数据库生成的 id、created_at
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.scalars(select(User).offset(skip).limit(limit)).all()
```

- `commit` 只有写操作才需要，查询不要 commit
- `refresh` 不能省：不然返回的对象里 `id`、`created_at` 还是 None
- 分页就是 `offset(skip).limit(limit)`，数据库层分页，不要把全表查出来再切片

## 六、第 4 步 routers/users.py：接口层

```python
router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已经注册")
    return crud.create_user(db, user_in)

@router.get("/", response_model=list[UserResponse])
def get_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)
```

逐项解释：

| 写法 | 作用 |
| --- | --- |
| `prefix="/users"` | 路由里不用重复写 `/users` |
| `response_model=UserResponse` | 按 schema 序列化并**过滤多余字段** |
| `status_code=201` | 创建成功用 201，不是 200 |
| `user_in: UserCreate` | 请求体（JSON）自动校验，不合格直接 422 |
| `skip: int = 0` | 普通参数默认当**查询参数**，即 `?skip=0` |
| `Depends(get_db)` | 让 FastAPI 调用 `get_db()`，请求结束自动关会话 |
| `raise HTTPException` | 业务错误用 4xx，别 return 一个 `{"error": ...}` |

`return` 的是 ORM 对象：因为 `response_model` + `from_attributes=True`，FastAPI 会自动把它转成 JSON 并丢掉 `hashed_password`。

## 七、第 5 步 main.py：注册路由

```python
from routers import users, posts

Base.metadata.create_all(bind=engine)   # 建表

app.include_router(users.router)
app.include_router(posts.router)
```

`include_router` 一行，这个文件里所有接口就都挂到 app 上了。

## 八、第 6 步：运行与验证

```bash
uvicorn main:app --reload
```

打开 `http://127.0.0.1:8000/docs`，Swagger 里可以直接点「Try it out」。

```bash
# 创建用户 → 201
curl -X POST http://127.0.0.1:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"zhangsan","email":"zhang@example.com","password":"12345678"}'

# 分页查询 → 200
curl "http://127.0.0.1:8000/users/?skip=0&limit=10"
```

返回：

```json
{
  "id": 1,
  "username": "zhangsan",
  "email": "zhang@example.com",
  "is_active": true,
  "created_at": "2026-11-08T12:00:00"
}
```

## 九、创建用户时，一次请求发生了什么

1. 前端 POST `/users/`，body 三个字段
2. FastAPI 用 `UserCreate` 校验：用户名太短、邮箱格式错、密码不足 8 位 → **422**，函数根本不执行
3. `Depends(get_db)` 打开一个会话
4. 路由先用 email 查重，已存在 → **400**
5. `crud.create_user` 加密密码 → `add` → `commit` → `refresh`
6. `response_model=UserResponse` 序列化，`hashed_password` 被丢掉
7. 返回 **201** + 用户 JSON

## 十、分页查询的三个要点

1. **参数**：`skip`（跳过多少条）和 `limit`（取多少条），语义是 offset/limit
2. **SQL**：`select(User).offset(skip).limit(limit)`
3. **类型**：返回列表要写 `response_model=list[UserResponse]`

生产上通常还要：

- 给参数加上限：`limit: int = Query(100, ge=1, le=100)`，防止一次拉全表
- 返回总数：再查一次 `select(func.count()).select_from(User)`，组成 `{items, total}` 结构
- 数据量大时改用游标分页（按 `id > last_id`），避免深分页 `offset` 越来越慢

## 十一、常见坑

| 现象 | 原因 |
| --- | --- |
| 返回里出现了密码哈希 | 没写 `response_model`，或返回 schema 里带了密码字段 |
| 接口参数变成了查询参数 | 忘了写 `Depends(get_db)`，`db` 就被当成普通参数 |
| 创建后 `id` 是 null | `commit` 后没 `refresh` |
| 访问 `/users` 被 307 跳转 | 路由写的是 `@router.get("/")`，完整路径是 `/users/` |
| 校验失败返回 422 而不是 400 | 422 是 schema 校验失败，说明入参本身不合法，属正常行为 |
| URL 变成 `/users/users` | `prefix` 和装饰器路径重复写了 |
| 查询接口很慢 | 没分页，或 `where` 用到的列没建索引 |

## 十二、新增一个接口的清单

以「按 id 查用户」为例，只改两个文件：

1. `crud.py`：加 `get_user(db, user_id)`
2. `routers/users.py`：加 `@router.get("/{user_id}")`，查不到 `raise HTTPException(404)`

新增一张表才需要五步全走：`models.py` → `schemas.py` → `crud.py` → `routers/` → `main.py`。

> 附：本项目当前缺口 —— `routers/posts.py` 用到了 `PostCreate / PostUpdate / PostResponse / PostWithAuthor` 和 `crud.create_post` 等函数，但 `schemas.py`、`crud.py` 里还没有定义，启动会 `ImportError`。补上这两处才能跑起来。

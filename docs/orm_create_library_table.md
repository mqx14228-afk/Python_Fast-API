# ORM 创建数据库表流程

> 一句话原理：表不用手写 `CREATE TABLE`。写一个继承 `Base` 的类，再调用 `Base.metadata.create_all()`，SQLAlchemy 就会把类翻译成建表 SQL。

```text
models.py: class User(Base)   ──注册──▶  Base.metadata
                                              │
database.py: engine（连哪个库）  ─────────────┤  create_all(bind=engine)
                                              ▼
                                    CREATE TABLE users (...)
```

## 一、三个文件的分工

| 文件 | 职责 | 与建表的关系 |
| --- | --- | --- |
| `database.py` | 引擎、会话工厂、`Base`、`get_db` | 必须，地基 |
| `models.py` | 表结构（类 = 表，属性 = 列） | 必须，表从这里来 |
| `main.py` | 导入模型 + 执行 `create_all` | 必须，触发建表 |
| `schemas.py` | 请求 / 响应校验（Pydantic） | 无关，不是表 |
| `crud.py` | 增删改查 | 无关，表建好后才会用到 |
| `routers/*.py` | HTTP 接口 | 无关 |

书写顺序：`database.py` → `models.py` → `main.py` → `schemas.py` → `crud.py` → `routers/`。
`models.py` 里要 `from database import Base`，所以 `database.py` 必须最先写好。

## 二、第一步：database.py，先打地基

四个对象，缺一不可：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. 数据库地址：sqlite 协议 + 文件路径
DATABASE_URL = "sqlite:///./blog.db"

# 2. 引擎：真正连库的驱动，echo=True 会把 SQL 打到控制台
engine = create_engine(DATABASE_URL, echo=True)

# 3. 会话工厂：每个请求造一个会话
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 4. Base：所有表模型的父类，继承它就变成 ORM 实体
class Base(DeclarativeBase):
    pass
```

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # 交给路由使用，函数在这里暂停
    finally:
        db.close()        # 请求结束，无论成败都关闭
```

## 三、第二步：models.py，写表结构

一个类 = 一张表，一个属性 = 一列。

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Library(Base):
    __tablename__ = "library"                    # 数据库里的真实表名

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(100))
    isbn: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    stock: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

常用写法对照：

| 写法 | 含义 |
| --- | --- |
| `Mapped[int]` | 列类型（Python 类型 + 库里的列类型） |
| `mapped_column(...)` | 这一列的约束 |
| `primary_key=True` | 主键 |
| `unique=True` | 唯一约束 |
| `index=True` | 额外建索引，如 `ix_library_isbn` |
| `default=0` | **Python 层**默认值，只有经 ORM 插入才生效 |
| `server_default=func.now()` | **数据库层**默认值，写进 DDL，任何方式插入都生效 |
| `ForeignKey("users.id")` | 外键，真正把两张表绑在一起的就是它 |
| `relationship(...)` | 只影响 ORM 对象之间的导航，**不生成任何列** |
| `__tablename__` | 表名，漏写会报错 |

## 四、第三步：main.py，触发建表

```python
from database import engine, Base
import models                                    # ① 必须先导入

Base.metadata.create_all(bind=engine)            # ② 再建表

app = FastAPI(...)
```

> **最容易踩的坑**：这两行顺序不能反。
> `create_all` 只是遍历 `Base.metadata` 里已经注册的表，而模型类只有被 `import` 过才会注册进去。
> 少了 `import models`，代码不报错，但**一张表都不会建**。

## 五、第四步：验证表建出来了

启动时控制台有 `echo=True` 的日志，直接能看到：

```sql
CREATE TABLE library (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    ...
)
```

或查询 sqlite 元数据表：

```python
import sqlite3
conn = sqlite3.connect("blog.db")
print(conn.execute("select name from sqlite_master where type='table'").fetchall())
```

```bash
sqlite3 blog.db ".tables"
sqlite3 blog.db ".schema library"
```

`create_all` 是幂等的：表已存在就跳过，反复启动不会报错，也不会重复建表。

## 六、新增一张表的完整清单

以 `library` 表为例，一共动 5 个地方：

1. **`models.py`**：加 `class Library(Base)`（见上）
2. **`schemas.py`**：加请求 / 响应模型

```python
class LibraryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    isbn: str = Field(min_length=10, max_length=20)
    stock: int = Field(default=0, ge=0)

class LibraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # 直接从 ORM 对象读属性
    id: int
    title: str
    author: str
    isbn: str
    stock: int
    created_at: datetime
```

3. **`crud.py`**：加数据库操作函数

```python
def create_library(db: Session, data: LibraryCreate) -> Library:
    obj = Library(**data.model_dump())
    db.add(obj)          # INSERT
    db.commit()          # 提交事务
    db.refresh(obj)      # 回读数据库生成的主键和默认值
    return obj

def get_libraries(db: Session, skip: int = 0, limit: int = 100) -> list[Library]:
    return db.scalars(select(Library).offset(skip).limit(limit)).all()
```

4. **`routers/library.py`**：加路由

```python
router = APIRouter(prefix="/library", tags=["图书管理"])

@router.post("/", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
def create_library(data: LibraryCreate, db: Session = Depends(get_db)):
    return crud.create_library(db, data)
```

5. **`main.py`**：注册路由

```python
from routers import users, posts, library
app.include_router(library.router)
```

注意 1、2、3、4、5 里，只有第 1 步和第 5 步（`import models` 已存在）影响建表，其余是让这张表能被接口用起来。

## 七、改表结构怎么办

`create_all` **只创建，不修改**。给 `Library` 加一个字段后重启，旧表结构不会变，新字段永远读不到。

- 开发阶段：删掉 `blog.db` 重启，让 ORM 重新建表（数据会丢）
- 正式项目：用 Alembic 做迁移，生成 `ALTER TABLE` 脚本
- 临时验证：手写 `ALTER TABLE library ADD COLUMN ...`，同时把模型类补上

## 八、常见错误速查

| 现象 | 原因 |
| --- | --- |
| 启动不报错，但没有表 | `create_all` 之前没 `import models` |
| 报 `__tablename__` 相关错误 | 类里漏写表名 |
| 表建到了别的地方 | `sqlite:///./blog.db` 是相对**启动目录**的，在哪个目录执行 `uvicorn`，文件就生成在哪 |
| 加了字段不生效 | `create_all` 不会改已存在的表，见第七节 |
| 插入时不填 `created_at` 报非空 | 用了 `default` 而不是 `server_default`，非 ORM 方式插入不会触发 Python 默认值 |

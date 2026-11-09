# 向外输出 egine Base import export default ?
# 导入 SQLAlchemy 相关模块 ORM 工具
from sqlalchemy import create_engine
# sessionmaker 会话工厂 造出数据库会话对象
# DeclarativeBase 用来当所有数据库表类型的父类 继承它就能变成 ORM 实体
# Session 数据库会话 用来操作数据库 增删改查
from sqlalchemy.orm import sessionmaker,DeclarativeBase,Session
# DeclarativeBase -> class 字段属性 -> ORM 所有能力

# 数据库连接地址
# sqlite:// 协议，代表使用 SQLite 数据库
# / 第一个 / 是 URL 格式要求
# ./blog.db 是数据库文件路径 相对路径 ./ 当前目录
DATABASE_URL = "sqlite:///./blog.db"
# create数据库引擎 传入数据库连接地址 echo=True 打印数据库操作日志 方便调试上线后关闭
engine = create_engine(DATABASE_URL, echo=True)
# 绑定数据库引擎 生成会话工厂 便于后面创建数据库会话对象
# 事务 多个动作放进一个事务 保证数据的一致性 一个动作失败 事务回滚 要么都成功要么都回滚
# autoflush=False 不自动刷新数据库会话中的数据 避免意外触发数据库操作造成不必要的数据库请求
# autocommit=False 不自动提交事务 避免事务回滚时 数据库操作被提交
SessionLocal = sessionmaker(bind=engine,autoflush=False,autocommit=False)

# python 没有 export default 语法 顶层变量自动导出
# 导出 engine Base

# 继承 DeclarativeBase 类 变成 ORM 实体
class Base(DeclarativeBase):
    pass

def get_db():
    # 从会话工厂创建数据库会话对象
    db = SessionLocal()
    try:
        # yield 会把会话交给 FastAPI 路由使用，函数在这里暂停，等待路由执行完成
        yield db
    finally:
        # 请求处理完成 不管成功失败 都关闭数据库会话释放资源
        db.close()

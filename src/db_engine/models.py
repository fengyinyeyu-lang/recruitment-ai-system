"""
SQLAlchemy ORM 模型定义（加分项 10）
定义岗位表、用户表、对话日志表，替代原有的 CSV 读写。
"""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'recruitment.db')

# 创建 SQLite 数据库引擎
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False, pool_pre_ping=True, connect_args={'check_same_thread': False})
Base = declarative_base()
Session = sessionmaker(bind=ENGINE)


class Job(Base):
    """岗位表"""
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_name = Column(String(200), nullable=False, index=True)
    city = Column(String(50), index=True)
    salary = Column(String(50))
    salary_low = Column(Float)
    salary_high = Column(Float)
    salary_avg = Column(Float, index=True)
    education = Column(String(20))
    work_year = Column(String(30))
    keyword = Column(String(100), index=True)
    company_short_name = Column(String(100))
    company_full_name = Column(String(200))
    company_size = Column(String(50))
    industry_field = Column(String(200))
    finance_stage = Column(String(50))
    position_detail = Column(Text)
    position_advantage = Column(Text)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    """用户表"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatLog(Base):
    """AI 对话记录表"""
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(ENGINE)
    print(f"[OK] Database initialized: {DB_PATH}")


def get_session():
    """获取数据库会话"""
    return Session()


if __name__ == "__main__":
    init_db()

"""FastAPI 入口 - 招聘数据智能分析系统后端"""
import sys
import os

# 将项目根目录加入 sys.path，确保 src 模块可被导入
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import DATA_DIR
from backend.routers import auth, data, visualization, ml, ai, resume, company, report

app = FastAPI(
    title="招聘数据智能分析系统 API",
    description="基于 FastAPI 的招聘数据分析后端服务",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(visualization.router)
app.include_router(ml.router)
app.include_router(ai.router)
app.include_router(resume.router)
app.include_router(company.router)
app.include_router(report.router)

# 挂载静态文件目录
if os.path.exists(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


@app.on_event("startup")
def startup():
    """启动时初始化数据库"""
    try:
        from src.db_engine.models import init_db
        init_db()
    except Exception as e:
        print(f"[WARN] 数据库初始化失败: {e}")


@app.get("/")
def root():
    return {"code": 200, "data": None, "message": "招聘数据智能分析系统 API 服务运行中"}


@app.get("/health")
def health_check():
    return {"code": 200, "data": {"status": "healthy"}, "message": "success"}

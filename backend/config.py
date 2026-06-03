"""FastAPI 后端配置管理"""
import os

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# JWT 配置
SECRET_KEY = "recruitment-ai-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 数据库路径
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'recruitment.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# API 前缀
API_PREFIX = "/api"

# 数据路径
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
CLEANED_CSV_PATH = os.path.join(PROCESSED_DIR, 'cleaned_jobs.csv')
COUNT_CSV_PATH = os.path.join(PROCESSED_DIR, 'count_positions.csv')

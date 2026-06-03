"""依赖注入：数据库会话、认证、数据加载"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS, PROJECT_ROOT

# 确保 src 模块可导入
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

security = HTTPBearer()


def get_db_session():
    """获取数据库会话"""
    from src.db_engine.models import Session
    session = Session()
    try:
        yield session
    finally:
        session.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """从 JWT token 解析当前用户"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据或 token 已过期",
        )


def get_data_df(city: str = None, keyword: str = None, education: str = None, work_year: str = None):
    """获取数据 DataFrame（优先数据库，回退CSV）"""
    try:
        from src.db_engine.repository import load_jobs_df, get_job_stats
        stats = get_job_stats()
        if stats['total'] > 0:
            return load_jobs_df(city=city, keyword=keyword, education=education, work_year=work_year)
    except Exception:
        pass
    # 回退到 CSV
    try:
        from src.data_pipeline.cleaner import load_processed_data
        df = load_processed_data()
        if df is not None and city:
            df = df[df['city'] == city]
        if df is not None and keyword:
            df = df[df['keyword'] == keyword]
        if df is not None and education:
            df = df[df['education'] == education]
        if df is not None and work_year:
            work_year_col = 'workYear' if 'workYear' in df.columns else 'work_year'
            if work_year_col in df.columns:
                df = df[df[work_year_col] == work_year]
        return df
    except Exception:
        return pd.DataFrame()


def get_count_df():
    """获取岗位统计 DataFrame"""
    try:
        from src.data_pipeline.cleaner import load_count_positions
        return load_count_positions()
    except Exception:
        return pd.DataFrame()

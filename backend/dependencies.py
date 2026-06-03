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


# ============ 全局数据缓存 ============
# 避免每次 API 请求都重新从数据库/CSV 加载 15000+ 行 DataFrame
_df_cache: dict = {"data": None, "loaded": False}


def invalidate_data_cache():
    """清除数据缓存（数据变更时调用）"""
    _df_cache["data"] = None
    _df_cache["loaded"] = False


def _load_full_df() -> pd.DataFrame:
    """加载完整 DataFrame（内部函数，带缓存）"""
    if _df_cache["loaded"] and _df_cache["data"] is not None:
        return _df_cache["data"]

    df = pd.DataFrame()

    # 优先从数据库加载
    try:
        from src.db_engine.repository import load_jobs_df, get_job_stats
        stats = get_job_stats()
        if stats['total'] > 0:
            df = load_jobs_df()
    except Exception:
        pass

    # 回退到 CSV
    if df.empty:
        try:
            from src.data_pipeline.cleaner import load_processed_data
            loaded = load_processed_data()
            if loaded is not None:
                df = loaded
        except Exception:
            pass

    _df_cache["data"] = df
    _df_cache["loaded"] = True
    return df


def get_data_df(city: str = None, keyword: str = None, education: str = None, work_year: str = None):
    """获取数据 DataFrame（使用内存缓存，按需过滤）"""
    df = _load_full_df()
    if df is None or df.empty:
        return pd.DataFrame()

    # 根据筛选条件在缓存上过滤（返回副本，不修改缓存）
    if city:
        df = df[df['city'] == city]
    if keyword:
        df = df[df['keyword'] == keyword]
    if education:
        df = df[df['education'] == education]
    if work_year:
        work_year_col = 'workYear' if 'workYear' in df.columns else 'work_year'
        if work_year_col in df.columns:
            df = df[df[work_year_col] == work_year]
    return df


def get_count_df():
    """获取岗位统计 DataFrame"""
    try:
        from src.data_pipeline.cleaner import load_count_positions
        return load_count_positions()
    except Exception:
        return pd.DataFrame()

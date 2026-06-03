"""认证路由 - 用户登录、注册、信息获取"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_db_session, create_access_token, get_current_user
from backend.schemas.models import LoginRequest, RegisterRequest, AuthResponse, UserResponse, ApiResponse

router = APIRouter(prefix="/api/auth", tags=["认证"])


def _hash_password(password: str) -> str:
    """使用 SHA256 对密码进行哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


@router.post("/login", response_model=ApiResponse)
def login(req: LoginRequest):
    """用户登录，返回 JWT token"""
    from src.db_engine.repository import get_user

    user = get_user(req.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    password_hash = _hash_password(req.password)
    if user.password_hash != password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(data={"sub": user.username})
    return ApiResponse(
        data=AuthResponse(token=token, username=user.username).model_dump()
    )


@router.post("/register", response_model=ApiResponse)
def register(req: RegisterRequest):
    """用户注册"""
    from src.db_engine.repository import get_user, save_user

    if not req.username or len(req.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名长度不能少于3个字符",
        )
    if not req.password or len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能少于6个字符",
        )

    existing = get_user(req.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    password_hash = _hash_password(req.password)
    user_id = save_user(req.username, password_hash)

    token = create_access_token(data={"sub": req.username})
    return ApiResponse(
        data=AuthResponse(token=token, username=req.username).model_dump()
    )


@router.get("/me", response_model=ApiResponse)
def get_me(username: str = Depends(get_current_user)):
    """获取当前用户信息（需认证）"""
    from src.db_engine.repository import get_user

    user = get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return ApiResponse(
        data=UserResponse(id=user.id, username=user.username).model_dump()
    )

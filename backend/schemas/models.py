"""Pydantic 数据模型定义"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# ============ 认证相关 ============
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


class UserResponse(BaseModel):
    id: int
    username: str


# ============ 数据相关 ============
class OverviewStats(BaseModel):
    total_jobs: int
    avg_salary: float
    city_count: int
    company_count: int
    keyword_count: int


# ============ 可视化相关 ============
class SalaryDistribution(BaseModel):
    bins: list
    counts: list
    kde_x: list
    kde_y: list
    mean: float
    median: float
    p25: float
    p75: float


class CitySalary(BaseModel):
    cities: list
    salaries: list
    counts: list


class EducationDistribution(BaseModel):
    labels: list
    values: list
    percentages: list


class ExperienceSalary(BaseModel):
    categories: list
    data: list  # 每个类别包含 min, q1, median, q3, max, mean


class PositionDemand(BaseModel):
    keywords: list
    counts: list


# ============ 词云相关 ============
class WordCloudData(BaseModel):
    words: list  # [{text, weight}]


class CityDemand(BaseModel):
    cities: list
    counts: list


class IndustryDistribution(BaseModel):
    industries: list
    counts: list


# ============ ML相关 ============
class KMeansRequest(BaseModel):
    n_clusters: int = 5


class KMeansResult(BaseModel):
    keywords: dict
    pca_data: list
    sample_data: list


class NNTrainRequest(BaseModel):
    k: int = 5
    epochs: int = 30
    learning_rate: float = 0.001


class NNTrainResult(BaseModel):
    accuracy: float
    history: dict
    report: str
    cluster_names: dict


class NNPredictRequest(BaseModel):
    description: str


class NNPredictResult(BaseModel):
    cluster: int
    cluster_name: str


class SalaryPredictRequest(BaseModel):
    city: str = "北京"
    education: str = "本科"
    workYear: str = "3-5年"
    keyword: str = "Java"


class SalaryPredictResult(BaseModel):
    predicted_salary: float
    confidence: str


# ============ AI相关 ============
class ChatRequest(BaseModel):
    message: str
    history: list = []
    rag_mode: bool = False


class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    sources: list = []
    followup_questions: list = []
    session_id: Optional[str] = None


# ============ 简历相关 ============
class ResumeParseResult(BaseModel):
    education: str
    experience: int
    skills: list
    raw_text: str


class JobRecommendation(BaseModel):
    position_name: str
    city: str
    salary: str
    company: str
    industry: str
    education: str
    work_year: str
    keyword: str
    match_score: float
    matched_skills: list


# ============ 企业画像 ============
class CompanyProfile(BaseModel):
    name: str
    short_name: str
    job_count: int
    avg_salary: float
    city_count: int
    keyword_count: int
    keywords: dict
    cities: dict
    education: dict
    salary_distribution: dict
    experience: dict
    industries: dict
    jobs: list


# ============ 报告 ============
class ReportRequest(BaseModel):
    city: str = "全国"
    keyword: str = "全部岗位"


class ReportResponse(BaseModel):
    html_content: str
    filename: str


# ============ 通用响应 ============
class ApiResponse(BaseModel):
    code: int = 200
    data: Any = None
    message: str = "success"

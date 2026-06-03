"""简历解析路由 - 上传 PDF 简历、岗位推荐"""
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from backend.dependencies import get_data_df, get_current_user
from backend.schemas.models import ResumeParseResult, JobRecommendation, ApiResponse

router = APIRouter(prefix="/api/resume", tags=["简历解析"])


@router.post("/upload", response_model=ApiResponse)
def upload_resume(file: UploadFile = File(...), username: str = Depends(get_current_user)):
    """上传 PDF 简历，解析并返回结果"""
    from src.feature.resume_parser import extract_text_from_pdf, parse_resume_info

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式简历")

    try:
        content = file.file.read()
        file_stream = io.BytesIO(content)
        text = extract_text_from_pdf(file_stream)

        if not text:
            raise HTTPException(status_code=400, detail="简历解析失败，可能是加密 PDF 或扫描版图片")

        info = parse_resume_info(text)

        return ApiResponse(data=ResumeParseResult(
            education=info.get("education", ""),
            experience=info.get("experience", 0),
            skills=info.get("skills", []),
            raw_text=info.get("raw", ""),
        ).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败: {str(e)}")


@router.post("/recommend", response_model=ApiResponse)
def recommend_jobs(
    education: str = "",
    experience: int = 0,
    skills: str = "",
    username: str = Depends(get_current_user),
):
    """根据解析结果推荐岗位"""
    from src.feature.resume_parser import recommend_jobs as do_recommend

    df = get_data_df()
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="暂无岗位数据")

    skills_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []

    resume_info = {
        "education": education,
        "experience": experience,
        "skills": skills_list,
    }

    if not skills_list:
        return ApiResponse(data=[])

    try:
        recommended_df = do_recommend(resume_info, df, top_n=10)

        if recommended_df.empty:
            return ApiResponse(data=[])

        results = []
        for _, row in recommended_df.iterrows():
            position_name = row.get('positionName', row.get('position_name', ''))
            company_name = row.get('companyFullName', row.get('company_full_name', row.get('companyShortName', '')))
            industry = row.get('industryField', row.get('industry_field', ''))
            work_year = row.get('workYear', row.get('work_year', ''))
            match_score = row.get('_match_score', 0)
            matched_skills = row.get('_matched_skills', [])

            if hasattr(match_score, 'item'):
                match_score = match_score.item()

            results.append(JobRecommendation(
                position_name=str(position_name),
                city=str(row.get('city', '')),
                salary=str(row.get('salary', '')),
                company=str(company_name),
                industry=str(industry),
                education=str(row.get('education', '不限')),
                work_year=str(work_year),
                keyword=str(row.get('keyword', '')),
                match_score=float(match_score),
                matched_skills=matched_skills if isinstance(matched_skills, list) else [],
            ).model_dump())

        return ApiResponse(data=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"岗位推荐失败: {str(e)}")

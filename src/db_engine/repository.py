"""
数据库操作层（Repository 模式）
封装对岗位、用户、对话记录的 CRUD 操作。
"""
import pandas as pd
import logging
from sqlalchemy import text
from .models import ENGINE, Session, Job, User, ChatLog

logging.basicConfig(level=logging.INFO)


def csv_to_db(csv_path=None, batch_size=500):
    """
    将清洗后的 CSV 数据批量导入数据库。
    使用 pandas read_csv + to_sql 高效迁移。
    """
    if csv_path is None:
        import os
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        csv_path = os.path.join(PROJECT_ROOT, 'data', 'processed', 'cleaned_jobs.csv')

    logging.info(f"📥 开始从 CSV 导入数据库: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 字段映射（CSV 列名 -> DB 列名）
    col_mapping = {
        'positionName': 'position_name',
        'city': 'city',
        'salary': 'salary',
        'salary_low': 'salary_low',
        'salary_high': 'salary_high',
        'salary_avg': 'salary_avg',
        'education': 'education',
        'workYear': 'work_year',
        'keyword': 'keyword',
        'companyShortName': 'company_short_name',
        'companyFullName': 'company_full_name',
        'companySize': 'company_size',
        'industryField': 'industry_field',
        'financeStage': 'finance_stage',
        'positionDetail': 'position_detail',
        'positionAdvantage': 'position_advantage',
    }

    df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})
    # 只保留模型中存在的列
    valid_cols = [c for c in df.columns if c in Job.__table__.columns.keys()]
    df = df[valid_cols]

    # 使用 pandas to_sql 批量写入（chunksize 避免 SQLite 变量超限）
    df.to_sql('jobs', con=ENGINE, if_exists='replace', index=False, chunksize=500)
    logging.info(f"[OK] Imported {len(df)} job records to database")
    return len(df)


def load_jobs_df(city=None, keyword=None, education=None, work_year=None, limit=None):
    """
    使用 ORM/SQL 从数据库加载岗位数据，返回 DataFrame。
    支持条件过滤。
    """
    query = "SELECT * FROM jobs WHERE 1=1"
    params = {}

    if city:
        query += " AND city = :city"
        params['city'] = city
    if keyword:
        query += " AND keyword = :keyword"
        params['keyword'] = keyword
    if education:
        query += " AND education = :education"
        params['education'] = education
    if work_year:
        query += " AND work_year = :work_year"
        params['work_year'] = work_year
    if limit:
        query += " LIMIT :limit"
        params['limit'] = limit

    df = pd.read_sql(text(query), ENGINE, params=params)

    # 列名映射（DB -> 原始 CSV 列名，保持下游代码兼容）
    col_mapping = {
        'position_name': 'positionName',
        'city': 'city',
        'salary': 'salary',
        'salary_low': 'salary_low',
        'salary_high': 'salary_high',
        'salary_avg': 'salary_avg',
        'education': 'education',
        'work_year': 'workYear',
        'keyword': 'keyword',
        'company_short_name': 'companyShortName',
        'company_full_name': 'companyFullName',
        'company_size': 'companySize',
        'industry_field': 'industryField',
        'finance_stage': 'financeStage',
        'position_detail': 'positionDetail',
        'position_advantage': 'positionAdvantage',
    }
    df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})
    return df


def save_user(username, password_hash):
    """保存用户到数据库"""
    with Session() as s:
        user = User(username=username, password_hash=password_hash)
        s.add(user)
        s.commit()
        return user.id


def get_user(username):
    """根据用户名查询用户"""
    with Session() as s:
        return s.query(User).filter_by(username=username).first()


def save_chat_log(username, question, answer):
    """保存对话记录到数据库"""
    with Session() as s:
        log = ChatLog(username=username, question=question, answer=answer)
        s.add(log)
        s.commit()
        return log.id


def get_user_chat_history(username, limit=20):
    """获取用户历史对话记录"""
    with Session() as s:
        return (s.query(ChatLog)
                 .filter_by(username=username)
                 .order_by(ChatLog.created_at.desc())
                 .limit(limit)
                 .all())


def delete_chat_log(log_id):
    """删除单条对话记录"""
    with Session() as s:
        log = s.query(ChatLog).filter_by(id=log_id).first()
        if log:
            s.delete(log)
            s.commit()
            return True
        return False


def delete_all_chat_logs(username):
    """删除用户的所有对话记录"""
    with Session() as s:
        deleted = s.query(ChatLog).filter_by(username=username).delete()
        s.commit()
        return deleted


def get_job_stats():
    """获取数据库中的岗位统计信息（使用原生 SQL 兼容 to_sql 创建的表）"""
    with ENGINE.connect() as conn:
        from sqlalchemy import text
        total = conn.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
        city_count = conn.execute(text("SELECT COUNT(DISTINCT city) FROM jobs")).scalar()
        company_count = conn.execute(text("SELECT COUNT(DISTINCT company_full_name) FROM jobs")).scalar()
        keyword_count = conn.execute(text("SELECT COUNT(DISTINCT keyword) FROM jobs")).scalar()
        return {
            'total': total,
            'cities': city_count,
            'companies': company_count,
            'keywords': keyword_count,
        }


if __name__ == "__main__":
    csv_to_db()
    stats = get_job_stats()
    print(f"📊 数据库统计: {stats}")

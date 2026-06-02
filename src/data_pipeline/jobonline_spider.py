# -*- coding: utf-8 -*-
"""
JobOnline (www.jobonline.cn) 招聘数据爬虫 v3
=============================================
修复记录：
  v1: 使用 /joblist 路径（404错误）
  v2: 修复为 /findPositions?q=关键词，但 URL 参数翻页无效
  v3: 翻页改为点击页面内 button.btn-next 按钮（Element UI 分页组件）
"""
import os
import csv
import time
import random
import logging
import urllib.parse
from DrissionPage import ChromiumPage, ChromiumOptions

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class JobOnlineSpider:
    """JobOnline 招聘数据爬虫 v3"""

    # 搜索关键词列表（79个），覆盖各行各业确保数据量充足
    KEYWORDS = [
        'Python', 'Java', '前端', '后端', '测试', '运维',
        '数据分析', '产品经理', 'UI设计', '算法',
        '销售', '客服', '人力资源', '财务', '行政',
        '机械', '电气', '土木', '化工', '生物',
        '市场营销', '新媒体', '内容运营', '项目管理',
        '教师', '医生', '护士', '律师', '翻译',
        '嵌入式', 'C++', 'Go', '大数据', '云计算',
        '网络安全', '人工智能', '机器学习', '深度学习',
        '电商', '物流', '供应链', '采购',
        '会计', '审计', '金融', '银行', '保险',
        '设计', '文案', '编辑', '记者',
        '厨师', '技工', '焊工', '司机', '保安',
        '建筑', '装修', '水电', '暖通',
        '外贸', '报关', '跨境电商',
        '游戏', '动画', '影视', '摄影',
        '药剂', '检验', '康复', '营养',
        '农业', '畜牧', '园林', '环保',
        '航空', '铁路', '船舶', '汽车',
        '实习', '兼职', '助理', '文员',
        '仓管', '质检', '安全',
    ]

    CSV_FIELDS = [
        'keyword', 'positionName', 'companyFullName', 'companySize',
        'industryField', 'companyNature', 'city', 'district', 'province',
        'salary', 'lowSalary', 'highSalary', 'workYear', 'education',
        'positionId', 'address', 'publishTime', 'channelNumber',
    ]

    TARGET_COUNT = 15500

    def __init__(self):
        self.output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../data/raw')
        )
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, 'jobonline_scraped_jobs.csv')

        self.seen_ids = set()
        self.total_saved = 0

        # 断点续爬：读取已有数据的 ID
        if os.path.exists(self.output_file):
            try:
                import pandas as pd
                existing = pd.read_csv(self.output_file, encoding='utf-8')
                self.seen_ids = set(existing['positionId'].astype(str).tolist())
                self.total_saved = len(existing)
                logger.info(f"🔄 断点续爬：已有 {self.total_saved} 条数据。")
            except Exception:
                pass

    def _init_csv(self):
        """初始化 CSV 文件"""
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
                writer.writeheader()
            logger.info(f"📝 创建 CSV: {self.output_file}")

    def _append_rows(self, rows: list[dict]):
        """追加写入 CSV"""
        if not rows:
            return
        with open(self.output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDS)
            for row in rows:
                writer.writerow(row)
        self.total_saved += len(rows)

    def _parse_api_response(self, resp_body: dict, keyword: str) -> list[dict]:
        """解析 API 响应 JSON"""
        rows = []
        if not isinstance(resp_body, dict):
            return rows

        obj = resp_body.get('object')
        if not isinstance(obj, dict):
            return rows

        items = obj.get('searchList') or obj.get('rows') or []
        if not isinstance(items, list):
            return rows

        for item in items:
            if not isinstance(item, dict):
                continue

            pos_id = str(item.get('id', ''))
            if not pos_id or pos_id in self.seen_ids:
                continue

            self.seen_ids.add(pos_id)

            low = item.get('lowSalary', '')
            high = item.get('highSalary', '')
            salary_text = f"{low}-{high}" if low and high else str(low or high or '面议')

            row = {
                'keyword': keyword,
                'positionName': item.get('positionName', ''),
                'companyFullName': item.get('companyName') or item.get('aliasName', ''),
                'companySize': item.get('size', ''),
                'industryField': item.get('industryName', ''),
                'companyNature': item.get('nature', ''),
                'city': item.get('cityName', ''),
                'district': item.get('areaName', ''),
                'province': item.get('provinceName', ''),
                'salary': salary_text,
                'lowSalary': str(low),
                'highSalary': str(high),
                'workYear': item.get('jobAge', ''),
                'education': item.get('eduDegree', ''),
                'positionId': pos_id,
                'address': item.get('address', ''),
                'publishTime': item.get('publishTime', ''),
                'channelNumber': item.get('channelNumber', ''),
            }
            rows.append(row)

        return rows

    def run(self):
        """主执行入口"""
        logger.info("=" * 60)
        logger.info("🚀 JobOnline 招聘数据爬虫 v3 启动")
        logger.info(f"🎯 目标: {self.TARGET_COUNT} 条")
        logger.info(f"📂 输出: {self.output_file}")
        logger.info(f"🔑 关键词: {len(self.KEYWORDS)} 个")
        logger.info("=" * 60)

        self._init_csv()

        if self.total_saved >= self.TARGET_COUNT:
            logger.info(f"✅ 已达标 ({self.total_saved} >= {self.TARGET_COUNT})。")
            return

        co = ChromiumOptions()
        co.headless(False)
        page = ChromiumPage(co)

        try:
            for kw_idx, keyword in enumerate(self.KEYWORDS):
                if self.total_saved >= self.TARGET_COUNT:
                    logger.info(f"🎉 数据量达标 ({self.total_saved} 条)！")
                    break

                logger.info(f"\n{'─' * 50}")
                logger.info(f"📌 [{kw_idx + 1}/{len(self.KEYWORDS)}] 关键词: '{keyword}'")
                logger.info(f"📊 进度: {self.total_saved} / {self.TARGET_COUNT}")

                self._crawl_keyword(page, keyword)

        except KeyboardInterrupt:
            logger.info("\n⚠️ 用户中断！")
        except Exception as e:
            logger.error(f"❌ 异常: {e}", exc_info=True)
        finally:
            try:
                page.quit()
            except Exception:
                pass
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🏁 结束，共 {self.total_saved} 条数据。")
            logger.info(f"📂 文件: {self.output_file}")
            logger.info(f"{'=' * 60}")

    def _crawl_keyword(self, page: ChromiumPage, keyword: str):
        """
        对单个关键词执行搜索 + 翻页。
        策略：
          1. 导航到 /findPositions?q=关键词
          2. 拦截 API 响应获取第 1 页数据
          3. 点击 button.btn-next 翻到下一页，继续拦截
          4. 当 btn-next 被 disabled 或连续无新数据时停止
        """
        # 第 1 步：导航到搜索结果页
        page.listen.start('showlist')
        encoded_kw = urllib.parse.quote(keyword)
        url = f'https://www.jobonline.cn/findPositions?q={encoded_kw}'
        page.get(url)
        time.sleep(random.uniform(3.5, 5.0))

        # 第 2 步：收集第 1 页数据
        first_count = self._collect_api_data(page, keyword)
        if first_count > 0:
            logger.info(f"  📄 第 1 页: 新增 {first_count} 条 | 总计 {self.total_saved}")
        else:
            logger.info(f"  ⚠️ 关键词 '{keyword}' 第 1 页无数据，跳过。")
            return

        # 第 3 步：循环点击"下一页"翻页
        consecutive_empty = 0
        max_pages = 30  # 每个关键词最多翻 30 页

        for page_num in range(2, max_pages + 1):
            if self.total_saved >= self.TARGET_COUNT:
                break

            # ★ 关键修复：先滚动到页面底部，确保分页组件进入视口
            try:
                page.scroll.to_bottom()
                time.sleep(1)
            except Exception:
                pass

            # 查找"下一页"按钮（多种备用选择器）
            next_btn = None
            for selector in ['button.btn-next', 'css:button.btn-next',
                             'text:下一页', 'tag:button@@class=btn-next']:
                next_btn = page.ele(selector, timeout=2)
                if next_btn:
                    break

            if not next_btn:
                logger.info(f"  📄 找不到下一页按钮，翻页结束。")
                break

            # 检查是否被禁用（到达最后一页）
            disabled_attr = next_btn.attr('disabled')
            btn_class = next_btn.attr('class') or ''
            if disabled_attr is not None or 'disabled' in btn_class:
                logger.info(f"  📄 已到最后一页 (第 {page_num - 1} 页)。")
                break

            # 重新启动监听（清除旧数据包）
            page.listen.start('showlist')

            # 滚动到按钮位置并点击
            try:
                next_btn.scroll.to_see()
                time.sleep(0.3)
                next_btn.click()
            except Exception as e:
                logger.warning(f"  ⚠️ 点击下一页失败: {e}")
                break

            # 等待页面加载
            time.sleep(random.uniform(2.5, 4.0))

            # 收集数据
            count = self._collect_api_data(page, keyword)

            if count > 0:
                consecutive_empty = 0
                logger.info(f"  📄 第 {page_num} 页: 新增 {count} 条 | 总计 {self.total_saved}")
            else:
                consecutive_empty += 1
                logger.info(f"  📄 第 {page_num} 页: 无新数据 (连续空: {consecutive_empty})")
                if consecutive_empty >= 2:
                    logger.info(f"  ⏭️ 连续无新数据，切换下一个关键词。")
                    break

    def _collect_api_data(self, page: ChromiumPage, keyword: str) -> int:
        """从监听的数据包中提取数据"""
        count = 0
        try:
            packets = page.listen.steps(timeout=8)
            for p in packets:
                url = p.url or ''
                if 'showlist' in url:
                    try:
                        resp_body = p.response.body
                        rows = self._parse_api_response(resp_body, keyword)
                        if rows:
                            self._append_rows(rows)
                            count += len(rows)
                    except Exception as e:
                        logger.debug(f"  解析异常: {e}")
        except Exception as e:
            logger.debug(f"  监听超时: {e}")

        return count


if __name__ == '__main__':
    spider = JobOnlineSpider()
    spider.run()

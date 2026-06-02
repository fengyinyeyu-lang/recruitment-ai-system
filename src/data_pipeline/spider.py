import os
import csv
import time
import random
import logging
from DrissionPage import ChromiumPage, ChromiumOptions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BossSpider:
    def __init__(self, target_count=15000):
        self.target_count = target_count
        self.current_count = 0
        
        self.output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/raw'))
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, 'boss_scraped_jobs.csv')
        
        self.keywords = ['Python', 'Java', '数据分析', '算法', '前端', '测试', '后端']
        
        co = ChromiumOptions()
        co.set_local_port(9222)
        self.page = ChromiumPage(co)

    def save_jobs(self, jobs):
        if not jobs:
            return
        file_exists = os.path.isfile(self.output_file)
        with open(self.output_file, mode='a', encoding='utf-8', newline='') as f:
            fieldnames = ['positionName', 'companyName', 'salary', 'city', 'education', 'workYear', 'positionDetail']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(jobs)

    def wait_for_human_verification(self):
        logging.info("如果页面未加载出职位列表，请在浏览器中操作过验证...")
        while True:
            # 兼容：有时候 class 是 job-list-box，有时是直接搜 .job-card-wrapper
            if self.page.ele('.job-card-wrapper', timeout=1) or self.page.ele('.job-name', timeout=1):
                logging.info("✅ 成功检测到职位列表，准备抓取...")
                break
            time.sleep(3)
            logging.info("⏳ 仍在等待页面加载职位列表...")

    def run(self, max_pages=30):
        logging.info(f"🚀 开始 Boss 直聘自动化爬虫 (接管模式)")
        
        for kw in self.keywords:
            if self.current_count >= self.target_count:
                break
                
            logging.info(f"==== 正在搜索关键词: {kw} ====")
            url = f"https://www.zhipin.com/web/geek/job?query={kw}&city=100010000"
            self.page.get(url)
            self.page.wait.load_start()
            
            self.wait_for_human_verification()
            
            for page_num in range(1, max_pages + 1):
                if self.current_count >= self.target_count:
                    break
                    
                logging.info(f"正在抓取 {kw} 第 {page_num} 页...")
                time.sleep(random.uniform(1.0, 3.0))
                self.page.scroll.to_bottom()
                time.sleep(2)
                
                # Boss 直聘的卡片 class 通常为 job-card-wrapper 或者 li.job-card-box
                job_cards = self.page.eles('.job-card-wrapper') or self.page.eles('.job-card-box')
                if not job_cards:
                    logging.warning("当前页面未找到职位卡片，可能被反爬或到底了。跳出此关键词。")
                    break
                    
                jobs = []
                for card in job_cards:
                    try:
                        position_name = card.ele('.job-name', timeout=1).text
                        company_name = card.ele('.company-name', timeout=1).text
                        salary = card.ele('.salary', timeout=1).text
                        
                        info_tags = card.ele('.job-info', timeout=1).eles('t:li') if card.ele('.job-info', timeout=1) else card.eles('t:li')
                        info_texts = [tag.text for tag in info_tags]
                        
                        city = info_texts[0] if len(info_texts) > 0 else "未知"
                        work_year = info_texts[1] if len(info_texts) > 1 else "不限"
                        education = info_texts[2] if len(info_texts) > 2 else "不限"
                        
                        welfare = card.ele('.info-desc', timeout=1)
                        position_detail = welfare.text if welfare else ""
                        
                        jobs.append({
                            'positionName': position_name,
                            'companyName': company_name,
                            'salary': salary,
                            'city': city,
                            'education': education,
                            'workYear': work_year,
                            'positionDetail': position_detail
                        })
                    except Exception:
                        continue
                        
                if jobs:
                    self.save_jobs(jobs)
                    self.current_count += len(jobs)
                    logging.info(f"✅ 成功提取 {len(jobs)} 条职位，总计: {self.current_count} / {self.target_count}")
                
                try:
                    next_btn = self.page.ele('.ui-icon-arrow-right', timeout=2)
                    if next_btn and next_btn.parent() and 'disabled' not in next_btn.parent().attr('class'):
                        next_btn.click()
                        time.sleep(random.uniform(3.5, 6.5))
                    else:
                        logging.info("下一页按钮不可用，已达到最后一页。")
                        break
                except Exception:
                    logging.warning("尝试翻页时出错，结束当前关键词。")
                    break

        logging.info("🎉 数据抓取完成！您现在可以关闭自动控制的浏览器了。")

if __name__ == '__main__':
    spider = BossSpider(target_count=15000)
    spider.run(max_pages=200) # Boss一般每个关键词最多10页-30页，调大一点以防万一

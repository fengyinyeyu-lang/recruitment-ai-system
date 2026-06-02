"""Generate a sample computer science resume PDF for testing."""
from fpdf import FPDF
import os

FONT_PATH = "C:/Windows/Fonts/simhei.ttf"


class ResumePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("simhei", "", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Page {self.page_no() - 1}", align="C")


def _section_title(pdf, title):
    x = pdf.get_x()
    y = pdf.get_y()
    w = pdf.get_string_width(title) + 10
    pdf.line(x + 2, y + 6, x + 2 + w, y + 6)
    pdf.set_font("simhei", "B", 13)
    pdf.set_text_color(40, 80, 180)
    pdf.cell(w, 7, title)
    pdf.ln(1)
    pdf.set_text_color(30, 30, 30)


def _bullet_point(pdf, text, indent=8):
    pdf.set_left_margin(indent)
    pdf.set_font("simhei", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(5, 5, "● ", new_x="END", new_y="NEXT")
    pdf.multi_cell(0, 5, text)
    pdf.ln(1)
    pdf.set_left_margin(0)


def build_resume():
    pdf = ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Register Chinese font
    pdf.add_font("simhei", "", FONT_PATH)
    pdf.add_font("simhei", "B", FONT_PATH)

    pdf.add_page()

    pdf.set_font("simhei", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "李明", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("simhei", "", 11)
    pdf.set_text_color(100, 100, 100)
    info_line = "手机: 138-0000-8888  |  邮箱: liming@example.com  |  GitHub: github.com/liming-dev  |  求职意向: Python后端/全栈工程师"
    pdf.cell(0, 7, info_line, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # Education
    _section_title(pdf, "教育背景")
    pdf.set_font("simhei", "B", 11)
    pdf.cell(90, 6, "华中科技大学", new_x="RIGHT", new_y="NEXT", align="L")
    pdf.cell(0, 6, "计算机科学与技术 硕士", align="R")
    pdf.set_font("simhei", "", 10)
    pdf.cell(0, 5, "2019.09 - 2022.06", align="R")
    pdf.ln(3)
    pdf.set_font("simhei", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, "GPA: 3.7/4.0 | 研究方向: NLP与大模型应用 | 学历: 硕士")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(3)

    pdf.set_font("simhei", "B", 11)
    pdf.cell(90, 6, "浙江大学", new_x="RIGHT", new_y="NEXT", align="L")
    pdf.cell(0, 6, "软件工程 学士", align="R")
    pdf.set_font("simhei", "", 10)
    pdf.cell(0, 5, "2015.09 - 2019.06", align="R")
    pdf.ln(3)
    pdf.set_font("simhei", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, "GPA: 3.6/4.0 | ACM校队成员 | 省级优秀毕业生")
    pdf.set_text_color(30, 30, 30)

    pdf.ln(6)

    # Work Experience
    _section_title(pdf, "工作经历")
    pdf.set_font("simhei", "B", 11)
    pdf.cell(75, 6, "字节跳动 - 抖音电商团队", new_x="RIGHT", new_y="NEXT", align="L")
    pdf.cell(0, 6, "北京", align="R")
    pdf.set_font("simhei", "", 10)
    pdf.cell(0, 5, "2022.07 - 至今 (3年工作经验)", align="R")
    pdf.ln(3)

    items = [
        ("主导电商推荐系统重构", "使用 Python + FastAPI 搭建微服务架构，引入 Redis 缓存层与 Kafka 消息队列，将接口响应从 280ms 降至 90ms"),
        ("大模型智能客服系统", "基于 Transformer 架构微调 LLM，利用 PyTorch 构建对话 Pipeline，集成 LangChain RAG 检索增强生成，解决率提升 42%"),
        ("高并发订单处理", "采用 Docker + K8s 容器化部署，设计 MySQL 分库分表方案"),
        ("CI/CD 流水线建设", "编写 Git + Jenkins 自动化部署脚本，Linux 环境代码审查规范"),
    ]
    for title, desc in items:
        _bullet_point(pdf, f"{title}: {desc}")

    pdf.ln(5)

    # Projects
    _section_title(pdf, "项目经验")
    pdf.set_font("simhei", "B", 11)
    pdf.cell(75, 6, "开源项目: NLP知识图谱问答系统", new_x="RIGHT", new_y="NEXT", align="L")
    pdf.set_font("simhei", "", 10)
    pdf.cell(0, 5, "个人项目 · 2023", align="R")
    pdf.ln(3)

    skills_items = [
        "技术栈: Python, PyTorch, Vue.js, MongoDB, Docker",
        "使用 BERT embedding 进行意图识别，Neo4j存储三元组关系",
        "前端 Vue.js + CSS 可视化交互界面，GitHub Star 1.2k",
    ]
    for item in skills_items:
        _bullet_point(pdf, item)

    pdf.ln(5)
    _section_title(pdf, "专业技能")
    prof_skills = [
        "编程语言: Python, Java, JavaScript",
        "后端框架: Flask, FastAPI",
        "数据库: MySQL, Redis, MongoDB",
        "机器学习: PyTorch, TensorFlow, NLP, Deep Learning",
        "工程工具: Docker, Linux, Git, Kafka",
        "前端基础: HTML, CSS, Vue",
    ]
    for s in prof_skills:
        _bullet_point(pdf, s)

    out_path = os.path.join(os.path.dirname(__file__), "data", "resume_test_li_ming.pdf")
    pdf.output(out_path)
    print(f"Done! Saved to {out_path}")


if __name__ == "__main__":
    build_resume()

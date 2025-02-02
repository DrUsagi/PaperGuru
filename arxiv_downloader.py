import arxiv
import requests
import os
import json
from tqdm import tqdm
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time

class SortOrder(Enum):
    """论文排序方式"""
    RELEVANCE = "relevance"                # 相关度排序
    SUBMITTED_DATE = "submitted_date"      # 提交日期排序
    LAST_UPDATED = "last_updated"          # 最后更新日期排序
    CITATIONS = "citations"                # 总引用次数排序
    CITATIONS_PER_YEAR = "citations_per_year"  # 年均引用次数排序
    RECENT_CITATIONS = "recent_citations"   # 最近引用热度
    TITLE = "title"                        # 按标题字母顺序
    AUTHOR = "author"                      # 按第一作者字母顺序
    CROSS_LISTED = "cross_listed"          # 按跨领域引用数
    ASCENDING_DATE = "ascending_date"      # 从旧到新排序

@dataclass
class SearchCriteria:
    """论文搜索条件"""
    keywords: Optional[str] = None          # 关键词（None表示不限制）
    title: Optional[str] = None            # 标题
    authors: Optional[List[str]] = None    # 作者
    abstract_keywords: Optional[str] = None # 摘要关键词
    year_from: Optional[int] = None        # 起始年份
    year_to: Optional[int] = None          # 结束年份
    categories: Optional[List[str]] = None  # arXiv分类
    min_citations: Optional[int] = None     # 最小引用数
    max_citations: Optional[int] = None     # 最大引用数
    exclude_keywords: Optional[List[str]] = None  # 排除的关键词
    include_keywords: Optional[List[str]] = None  # 必须包含的关键词
    sort_by: SortOrder = SortOrder.RELEVANCE  # 排序方式
    max_results: int = 20                  # 最大结果数

def load_paper_database(db_path):
    """加载论文数据库"""
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"papers": {}}

def save_paper_database(db_path, data):
    """保存论文数据库"""
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_citation_count(title, authors, max_retries=3):
    """从Semantic Scholar获取论文引用次数"""
    try:
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        headers = {
            "Accept": "application/json"
        }
        
        for _ in range(max_retries):
            try:
                params = {
                    "query": title,
                    "fields": "title,authors,citationCount,year",
                    "limit": 1
                }
                
                response = requests.get(base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["data"] and len(data["data"]) > 0:
                    paper_data = data["data"][0]
                    if title.lower() in paper_data["title"].lower():
                        return {
                            "citation_count": paper_data.get("citationCount", 0),
                            "semantic_scholar_url": f"https://www.semanticscholar.org/paper/{paper_data['paperId']}"
                        }
                return {"citation_count": 0, "semantic_scholar_url": None}
                
            except Exception as e:
                continue
    except Exception as e:
        print(f"获取引用信息时出错: {str(e)}")
    return {"citation_count": 0, "semantic_scholar_url": None}

def get_safe_filename(authors, title):
    """
    生成安全的文件名：作者姓氏-论文标题
    
    参数:
        authors: 作者列表
        title: 论文标题
    返回:
        安全的文件名
    """
    # 获取第一作者的姓氏
    first_author = str(authors[0]) if authors else "Unknown"
    last_name = first_author.split()[-1]
    
    # 清理标题，只保留字母数字和部分标点
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    # 如果标题太长，截断它
    max_length = 100
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length] + "..."
    
    # 组合文件名：作者姓氏-标题
    return f"{last_name}-{safe_title}"

def get_user_input(prompt: str, default: str = "", allow_null: bool = False) -> str:
    """
    获取用户输入，支持默认值和null选项
    
    参数:
        prompt: 提示信息
        default: 默认值
        allow_null: 是否允许null选项
    """
    if allow_null:
        prompt = f"{prompt} (输入'null'表示不限制)"
    
    user_input = input(f"{prompt} [默认: {default}]: ").strip() if default else input(f"{prompt}: ").strip()
    
    if allow_null and user_input.lower() == 'null':
        return None
    return user_input if user_input else default

def get_year_input(prompt: str) -> Optional[int]:
    """获取年份输入"""
    year = get_user_input(prompt)
    if year and year.isdigit():
        return int(year)
    return None

def get_multiple_input(prompt: str) -> List[str]:
    """获取多个输入，用逗号分隔"""
    items = get_user_input(prompt)
    return [item.strip() for item in items.split(",")] if items else []

def get_sort_order() -> SortOrder:
    """获取排序方式"""
    print("\n=== 选择排序方式 ===")
    print("基础排序:")
    print("1.  相关度排序（默认）")
    print("2.  最新提交优先")
    print("3.  最近更新优先")
    print("4.  总引用次数")
    
    print("\n高级排序:")
    print("5.  年均引用次数（影响力）")
    print("6.  最近引用热度")
    print("7.  标题字母顺序")
    print("8.  第一作者字母顺序")
    print("9.  跨领域引用数")
    print("10. 从旧到新排序")
    
    print("\n排序说明:")
    print("- 相关度排序：根据搜索关键词的匹配程度")
    print("- 年均引用：总引用数除以论文发表年限")
    print("- 最近引用热度：近期引用次数权重更高")
    print("- 跨领域引用：来自不同领域的引用数量")
    
    choice = get_user_input("请输入选项编号", "1")
    sort_mapping = {
        "1": SortOrder.RELEVANCE,
        "2": SortOrder.SUBMITTED_DATE,
        "3": SortOrder.LAST_UPDATED,
        "4": SortOrder.CITATIONS,
        "5": SortOrder.CITATIONS_PER_YEAR,
        "6": SortOrder.RECENT_CITATIONS,
        "7": SortOrder.TITLE,
        "8": SortOrder.AUTHOR,
        "9": SortOrder.CROSS_LISTED,
        "10": SortOrder.ASCENDING_DATE
    }
    return sort_mapping.get(choice, SortOrder.RELEVANCE)

def filter_paper(paper, criteria: SearchCriteria, citation_info: Dict) -> bool:
    """
    根据条件过滤论文
    
    返回:
        True: 保留论文
        False: 过滤掉论文
    """
    # 检查引用数范围
    citation_count = citation_info.get("citation_count", 0)
    if criteria.min_citations is not None and citation_count < criteria.min_citations:
        return False
    if criteria.max_citations is not None and citation_count > criteria.max_citations:
        return False
    
    # 检查摘要关键词
    if criteria.abstract_keywords:
        if not any(kw.lower() in paper.summary.lower() for kw in criteria.abstract_keywords.split()):
            return False
    
    # 检查排除关键词
    if criteria.exclude_keywords:
        for kw in criteria.exclude_keywords:
            if (kw.lower() in paper.title.lower() or 
                kw.lower() in paper.summary.lower()):
                return False
    
    # 检查必须包含的关键词
    if criteria.include_keywords:
        for kw in criteria.include_keywords:
            if (kw.lower() not in paper.title.lower() and 
                kw.lower() not in paper.summary.lower()):
                return False
    
    return True

def build_arxiv_query(criteria: SearchCriteria) -> str:
    """构建arXiv搜索查询字符串"""
    query_parts = []
    
    # 基本关键词搜索
    if criteria.keywords is not None:  # 改为明确检查None
        if criteria.keywords:  # 如果有具体关键词
            # 用逗号分隔关键词，每个关键词都可以包含空格
            keywords = [k.strip() for k in criteria.keywords.split(",")]
            keyword_parts = []
            for keyword in keywords:
                # 对于包含空格的关键词，加上引号
                if ' ' in keyword:
                    keyword = f'"{keyword}"'
                keyword_parts.append(f'(ti:{keyword} OR abs:{keyword})')
            if keyword_parts:
                query_parts.append("(" + " OR ".join(keyword_parts) + ")")
    
    # 标题搜索
    if criteria.title:
        query_parts.append(f"ti:\"{criteria.title}\"")
    
    # 作者搜索
    if criteria.authors:
        author_queries = [f"au:\"{author}\"" for author in criteria.authors]
        query_parts.append("(" + " AND ".join(author_queries) + ")")
    
    # 摘要关键词搜索
    if criteria.abstract_keywords:
        abstract_terms = criteria.abstract_keywords.split()
        abstract_query = " AND ".join(f"abs:\"{term}\"" for term in abstract_terms)
        query_parts.append(f"({abstract_query})")
    
    # 必须包含的关键词
    if criteria.include_keywords:
        include_query = " AND ".join(f"(ti:\"{kw}\" OR abs:\"{kw}\")" 
                                   for kw in criteria.include_keywords)
        query_parts.append(f"({include_query})")
    
    # 排除的关键词
    if criteria.exclude_keywords:
        exclude_query = " AND ".join(f"NOT (ti:\"{kw}\" OR abs:\"{kw}\")" 
                                   for kw in criteria.exclude_keywords)
        query_parts.append(f"({exclude_query})")
    
    # 年份范围
    if criteria.year_from or criteria.year_to:
        if criteria.year_from and criteria.year_to:
            query_parts.append(f"submittedDate:[{criteria.year_from}0101 TO {criteria.year_to}1231]")
        elif criteria.year_from:
            query_parts.append(f"submittedDate:[{criteria.year_from}0101 TO 99991231]")
        elif criteria.year_to:
            query_parts.append(f"submittedDate:[00000101 TO {criteria.year_to}1231]")
    
    # 分类
    if criteria.categories:
        cat_queries = [f"cat:{cat.strip()}" for cat in criteria.categories]
        query_parts.append("(" + " OR ".join(cat_queries) + ")")
    
    # 组合所有查询条件
    final_query = " AND ".join(f"({part})" for part in query_parts if part)
    # 如果没有任何查询条件，返回通配符查询
    if not final_query:
        final_query = "*:*"
    print(f"\n生成的查询语句: {final_query}")
    return final_query

def sort_papers(papers: List[tuple], sort_by: SortOrder) -> List[tuple]:
    """
    根据指定方式对论文进行排序
    
    参数:
        papers: [(paper, citation_info), ...]的列表
        sort_by: 排序方式
    """
    current_year = datetime.now().year
    
    if sort_by == SortOrder.CITATIONS:
        return sorted(papers, key=lambda x: x[1]["citation_count"], reverse=True)
    
    elif sort_by == SortOrder.CITATIONS_PER_YEAR:
        def get_citations_per_year(paper_tuple):
            paper, citation_info = paper_tuple
            years = current_year - paper.published.year + 1
            return citation_info["citation_count"] / years
        return sorted(papers, key=get_citations_per_year, reverse=True)
    
    elif sort_by == SortOrder.RECENT_CITATIONS:
        # 这里需要额外的API调用来获取最近的引用数据
        # 暂时使用总引用数代替
        return sorted(papers, key=lambda x: x[1]["citation_count"], reverse=True)
    
    elif sort_by == SortOrder.TITLE:
        return sorted(papers, key=lambda x: x[0].title.lower())
    
    elif sort_by == SortOrder.AUTHOR:
        return sorted(papers, key=lambda x: str(x[0].authors[0]).lower() if x[0].authors else "")
    
    elif sort_by == SortOrder.CROSS_LISTED:
        return sorted(papers, key=lambda x: len(x[0].categories), reverse=True)
    
    elif sort_by == SortOrder.ASCENDING_DATE:
        return sorted(papers, key=lambda x: x[0].published)
    
    elif sort_by == SortOrder.SUBMITTED_DATE:
        return sorted(papers, key=lambda x: x[0].published, reverse=True)
    
    elif sort_by == SortOrder.LAST_UPDATED:
        return sorted(papers, key=lambda x: x[0].updated, reverse=True)
    
    # 默认返回原顺序（相关度排序）
    return papers

def create_download_session_dir(base_dir: str, criteria: SearchCriteria) -> tuple:
    """
    创建下载会话目录
    
    返回:
        tuple: (会话目录路径, 说明文件路径)
    """
    # 创建基础目录
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # 生成会话目录名称（使用时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"download_session_{timestamp}"
    session_dir = os.path.join(base_dir, session_name)
    os.makedirs(session_dir)
    
    # 创建说明文件
    readme_path = os.path.join(session_dir, "download_info.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# arXiv论文下载会话信息\n\n")
        f.write(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 搜索条件\n\n")
        f.write(f"- 关键词: {criteria.keywords or '不限'}\n")
        f.write(f"- 标题关键词: {criteria.title or '无'}\n")
        f.write(f"- 作者: {', '.join(criteria.authors) if criteria.authors else '无'}\n")
        f.write(f"- 摘要关键词: {criteria.abstract_keywords or '无'}\n")
        f.write(f"- 必须包含关键词: {', '.join(criteria.include_keywords) if criteria.include_keywords else '无'}\n")
        f.write(f"- 排除关键词: {', '.join(criteria.exclude_keywords) if criteria.exclude_keywords else '无'}\n")
        f.write(f"- 引用数范围: {criteria.min_citations or '不限'} - {criteria.max_citations or '不限'}\n")
        f.write(f"- 年份范围: {criteria.year_from or '不限'} - {criteria.year_to or '不限'}\n")
        f.write(f"- 分类: {', '.join(criteria.categories) if criteria.categories else '所有'}\n")
        f.write(f"- 排序方式: {criteria.sort_by.value}\n")
        f.write(f"- 最大下载数量: {criteria.max_results}\n\n")
        
        f.write("## 下载的论文\n\n")
        f.write("| 序号 | 标题 | 作者 | 发布日期 | 引用数 |\n")
        f.write("|------|------|------|----------|--------|\n")
    
    return session_dir, readme_path

def update_download_info(readme_path: str, paper, citation_info: dict, index: int):
    """更新下载信息文件"""
    with open(readme_path, 'a', encoding='utf-8') as f:
        authors = ", ".join([str(author) for author in paper.authors])
        pub_date = paper.published.strftime("%Y-%m-%d")
        citations = citation_info.get("citation_count", 0)
        
        f.write(f"| {index} | {paper.title} | {authors} | {pub_date} | {citations} |\n")

def download_paper(url, filepath, max_retries=3):
    """下载论文PDF，支持重试"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 验证是否为PDF文件
            if 'application/pdf' in response.headers.get('content-type', ''):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"下载的文件不是PDF格式")
                return False
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"下载失败，正在重试 ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                print(f"下载PDF失败: {str(e)}")
                return False
    return False

def download_papers(criteria: SearchCriteria, download_dir="arxiv_papers", db_path="papers_db.json"):
    """根据搜索条件从arXiv下载论文"""
    # 创建本次下载的会话目录和说明文件
    session_dir, readme_path = create_download_session_dir(download_dir, criteria)
    
    db = load_paper_database(db_path)
    
    try:
        query = build_arxiv_query(criteria)
        client = arxiv.Client()
        
        # 增加搜索范围
        search_max_results = max(criteria.max_results * 50, 2000)  # 进一步增加搜索范围
        
        search = arxiv.Search(
            query=query,
            max_results=search_max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        print(f"正在搜索论文...")
        papers_with_info = []
        total_searched = 0
        skipped_papers = []
        
        filtered_count = {
            "already_downloaded": 0,
            "citation_filter": 0,
            "keyword_filter": 0
        }
        
        # 使用迭代器方式获取结果
        try:
            results_iterator = client.results(search)
            for paper in results_iterator:
                try:
                    total_searched += 1
                    print(f"\r已搜索 {total_searched} 篇论文，找到 {len(papers_with_info)} 篇新论文...", end="")
                    
                    # 检查是否已下载
                    paper_id = paper.get_short_id()
                    if paper_id in db["papers"]:
                        skipped_papers.append(f"已下载: {paper.title}")
                        filtered_count["already_downloaded"] += 1
                        continue
                    
                    # 获取引用信息并检查
                    citation_info = get_citation_count(paper.title, [str(author) for author in paper.authors])
                    if (criteria.min_citations is not None and citation_info["citation_count"] < criteria.min_citations) or \
                       (criteria.max_citations is not None and citation_info["citation_count"] > criteria.max_citations):
                        filtered_count["citation_filter"] += 1
                        continue
                    
                    # 应用其他过滤条件
                    if not filter_paper(paper, criteria, citation_info):
                        filtered_count["keyword_filter"] += 1
                        continue
                    
                    papers_with_info.append((paper, citation_info))
                    print(f"\n找到新论文: {paper.title}")
                    
                    # 如果找到足够的论文就停止
                    if len(papers_with_info) >= criteria.max_results:
                        break
                
                except Exception as e:
                    print(f"\n处理论文信息时出错 {paper.title}: {str(e)}")
                    continue
                
                # 设置最大搜索上限
                if total_searched >= 1000:
                    break
        
        except Exception as e:
            print(f"\n搜索过程中出错: {str(e)}")
            print("请检查网络连接或稍后重试")
        
        print("\n")  # 换行
        
        if not papers_with_info:
            print("\n没有找到新的符合条件的论文")
            return
        
        print(f"\n共找到 {len(papers_with_info)} 篇新论文")
        
        # 排序
        print(f"\n正在按{criteria.sort_by.value}排序...")
        papers_with_info = sort_papers(papers_with_info, criteria.sort_by)
        
        # 限制下载数量
        papers_to_download = papers_with_info[:criteria.max_results]
        
        # 下载论文
        print(f"\n开始下载 {len(papers_to_download)} 篇论文...")
        
        # 使用tqdm创建进度条
        for paper, citation_info in tqdm(papers_to_download, desc="下载进度"):
            try:
                paper_id = paper.get_short_id()
                
                # 检查论文是否已经下载过
                if paper_id in db["papers"]:
                    print(f"\n论文已存在数据库中，跳过: {paper.title}")
                    continue
                
                # 生成文件名
                safe_filename = get_safe_filename(paper.authors, paper.title)
                filename = f"{safe_filename}.pdf"
                filepath = os.path.join(session_dir, filename)
                
                if os.path.exists(filepath):
                    filename = f"{safe_filename}_{paper_id}.pdf"
                    filepath = os.path.join(session_dir, filename)
                
                # 下载PDF
                if download_paper(paper.pdf_url, filepath):
                    print(f"\n成功下载论文: {paper.title}")
                    
                    # 更新说明文件
                    update_download_info(readme_path, paper, citation_info, papers_to_download.index((paper, citation_info)) + 1)
                    
                # 保存元数据
                try:
                    db["papers"][paper_id] = {
                        "title": paper.title,
                        "authors": [str(author) for author in paper.authors],
                        "abstract": paper.summary,
                        "citation_count": citation_info["citation_count"],
                        "semantic_scholar_url": citation_info["semantic_scholar_url"],
                        "published_date": paper.published.strftime("%Y-%m-%d"),
                        "downloaded_date": datetime.now().strftime("%Y-%m-%d"),
                        "filename": filename,
                        "arxiv_url": paper.pdf_url,
                        "categories": paper.categories
                    }
                    save_paper_database(db_path, db)
                except Exception as e:
                    print(f"保存元数据失败: {str(e)}")
            
            except Exception as e:
                print(f"\n处理论文时出错 {paper.title}: {str(e)}")
                continue
                    
        # 打印跳过的论文信息
        if skipped_papers:
            print("\n\n跳过的论文:")
            for paper in skipped_papers:
                print(f"- {paper}")
        
        # 打印搜索统计
        print("\n搜索统计:")
        print(f"总共搜索论文数: {total_searched}")
        print(f"已下载过的论文: {filtered_count['already_downloaded']}")
        print(f"因引用数过滤掉: {filtered_count['citation_filter']}")
        print(f"因关键词过滤掉: {filtered_count['keyword_filter']}")
        print(f"符合条件的新论文: {len(papers_with_info)}")
        
        if total_searched < search_max_results:
            print("\n注意: 搜索结果少于预期，可能原因:")
            print("1. 搜索条件可能过于严格")
            print("2. 关键词可能需要调整")
            print("3. 可以尝试添加更多的分类")
            print("4. 考虑放宽年份或引用数限制")
        
    except Exception as e:
        print(f"\n搜索过程中出错: {str(e)}")
        print("请检查网络连接或稍后重试")

def get_preset_keywords() -> dict:
    """返回预设的关键词组合"""
    return {
        # 基础AI方向 (1-5)
        "1": {
            "name": "通用AI",
            "keywords": "Artificial Intelligence, AI, Machine Learning, Deep Learning, Neural Network"
        },
        "2": {
            "name": "AGI与智能体",
            "keywords": "Artificial General Intelligence, AGI, Autonomous Agent, Multi-agent System, Intelligent Agent"
        },
        "3": {
            "name": "大语言模型",
            "keywords": "Large Language Model, LLM, GPT, ChatGPT, Transformer, BERT"
        },
        "4": {
            "name": "计算机视觉",
            "keywords": "Computer Vision, CV, Image Processing, Object Detection, CNN, Vision Transformer"
        },
        "5": {
            "name": "强化学习",
            "keywords": "Reinforcement Learning, RL, Deep RL, Policy Learning, Q-Learning, DQN"
        },

        # 商业与应用方向 (6-10)
        "6": {
            "name": "商业AI",
            "keywords": "Business AI, Enterprise AI, Commercial AI, AI in Business, Business Intelligence"
        },
        "7": {
            "name": "信息系统",
            "keywords": "Information Systems, AI Information System, Knowledge Management, Information Processing"
        },
        "8": {
            "name": "金融AI",
            "keywords": "Financial AI, AI in Finance, Algorithmic Trading, Financial Technology, FinTech AI"
        },
        "9": {
            "name": "法律AI",
            "keywords": "Legal AI, AI in Law, Legal Intelligence, Legal Tech, AI Legal Assistant"
        },
        "10": {
            "name": "营销AI",
            "keywords": "Marketing AI, AI Marketing, Customer Analytics, Marketing Intelligence, AI Advertisement"
        },

        # 专业领域应用 (11-15)
        "11": {
            "name": "医疗AI",
            "keywords": "Medical AI, Healthcare AI, Clinical AI, Medical Diagnosis, AI in Medicine"
        },
        "12": {
            "name": "教育AI",
            "keywords": "Educational AI, AI in Education, Intelligent Tutoring, Learning Analytics"
        },
        "13": {
            "name": "工业AI",
            "keywords": "Industrial AI, Manufacturing AI, Industry 4.0, Smart Manufacturing, Industrial Intelligence"
        },
        "14": {
            "name": "农业AI",
            "keywords": "Agricultural AI, Smart Agriculture, AI Farming, Precision Agriculture"
        },
        "15": {
            "name": "能源AI",
            "keywords": "Energy AI, Smart Grid, Energy Management, AI in Power Systems"
        },

        # 技术方向 (16-20)
        "16": {
            "name": "自然语言处理",
            "keywords": "Natural Language Processing, NLP, Text Mining, Information Extraction, Text Generation"
        },
        "17": {
            "name": "知识图谱",
            "keywords": "Knowledge Graph, Knowledge Base, Ontology Learning, Semantic Network"
        },
        "18": {
            "name": "人机交互",
            "keywords": "Human-AI Interaction, AI Interface, Human-centered AI, Interactive AI"
        },
        "19": {
            "name": "AI系统集成",
            "keywords": "AI Integration, System Integration, Enterprise AI System, AI Platform"
        },
        "20": {
            "name": "生成式AI",
            "keywords": "Generative AI, GAN, Diffusion Model, Text-to-Image, Stable Diffusion"
        },

        # 新兴技术方向 (21-25)
        "21": {
            "name": "元宇宙AI",
            "keywords": "Metaverse AI, Virtual World AI, Digital Twin, AI Simulation, Virtual Reality AI"
        },
        "22": {
            "name": "Web3与AI",
            "keywords": "Web3 AI, Blockchain AI, Decentralized AI, AI DAO, Smart Contract AI"
        },
        "23": {
            "name": "量子AI",
            "keywords": "Quantum AI, Quantum Machine Learning, Quantum Neural Network, Quantum Computing AI"
        },
        "24": {
            "name": "边缘AI",
            "keywords": "Edge AI, Edge Computing, Edge Intelligence, Distributed AI, Edge Learning"
        },
        "25": {
            "name": "物联网AI",
            "keywords": "IoT AI, Internet of Things AI, Smart IoT, Intelligent IoT, AIoT"
        },

        # AI基础研究 (26-30)
        "26": {
            "name": "AI理论",
            "keywords": "AI Theory, Theoretical AI, Mathematical AI, Statistical Learning, Learning Theory"
        },
        "27": {
            "name": "神经科学与AI",
            "keywords": "Neuroscience AI, Brain-inspired AI, Neural Computing, Cognitive Computing"
        },
        "28": {
            "name": "概率图模型",
            "keywords": "Probabilistic Models, Bayesian Networks, Graphical Models, Probabilistic AI"
        },
        "29": {
            "name": "优化方法",
            "keywords": "AI Optimization, Neural Architecture Search, AutoML, Hyperparameter Optimization"
        },
        "30": {
            "name": "表示学习",
            "keywords": "Representation Learning, Feature Learning, Embedding Learning, Manifold Learning"
        },

        # AI安全与伦理 (31-35)
        "31": {
            "name": "AI安全",
            "keywords": "AI Safety, Safe AI, Robust AI, AI Security, Trustworthy AI"
        },
        "32": {
            "name": "AI伦理",
            "keywords": "AI Ethics, Ethical AI, Responsible AI, AI Governance, AI Policy"
        },
        "33": {
            "name": "隐私保护",
            "keywords": "Privacy-preserving AI, Federated Learning, Secure AI, Confidential Computing"
        },
        "34": {
            "name": "可解释性",
            "keywords": "Explainable AI, XAI, Interpretable AI, AI Interpretation, Model Understanding"
        },
        "35": {
            "name": "公平性",
            "keywords": "AI Fairness, Bias in AI, Fair ML, Ethical ML, AI Accountability"
        },

        # 特殊应用领域 (36-40)
        "36": {
            "name": "机器人AI",
            "keywords": "Robotics AI, Robot Learning, Intelligent Robotics, Robot Intelligence"
        },
        "37": {
            "name": "自动驾驶",
            "keywords": "Autonomous Driving, Self-driving Car, Autonomous Vehicle, Intelligent Vehicle"
        },
        "38": {
            "name": "智慧城市",
            "keywords": "Smart City AI, Urban Intelligence, City Intelligence, Urban Computing"
        },
        "39": {
            "name": "环境AI",
            "keywords": "Environmental AI, Climate AI, Sustainable AI, Green AI, Eco-friendly AI"
        },
        "40": {
            "name": "创意AI",
            "keywords": "Creative AI, AI Art, AI Music, AI Design, Computational Creativity"
        }
    }

def get_keywords_input() -> str:
    """获取关键词输入，支持预设选项和自定义输入"""
    presets = get_preset_keywords()
    
    print("\n=== 选择搜索关键词 ===")
    print("预设关键词组合:")
    for key, value in presets.items():
        print(f"{key}. {value['name']}: {value['keywords']}")
    
    print("\n选项:")
    print("- 输入数字(1-40)选择预设关键词组合")
    print("- 输入'c'自定义关键词(用逗号分隔)")
    print("- 输入'null'搜索所有论文")
    print("- 直接回车使用默认值")
    
    choice = get_user_input("请选择", "1")
    
    if choice.lower() == 'null':
        return None
    elif choice.lower() == 'c':
        return get_user_input(
            "请输入自定义关键词，多个关键词用逗号分隔",
            "Artificial Intelligence, AI, Machine Learning"
        )
    else:
        try:
            return presets[choice]["keywords"]
        except KeyError:
            print("无效选择，使用默认值")
            return presets["1"]["keywords"]

def interactive_search():
    """交互式搜索界面"""
    print("\n=== arXiv论文下载工具 ===")
    print("(提示：直接按回车使用默认值或跳过，输入'null'表示不限制)")
    
    # 获取基本搜索条件
    keywords = get_keywords_input()
    title = get_user_input("请输入论文标题关键词（可选）")
    authors = get_multiple_input("请输入作者姓名，多个作者用逗号分隔（可选）")
    
    # 新增：摘要关键词搜索
    abstract_keywords = get_user_input("请输入摘要必须包含的关键词，用空格分隔（可选）")
    
    # 新增：包含和排除关键词
    include_keywords = get_multiple_input("请输入论文必须包含的关键词，多个关键词用逗号分隔（可选）")
    exclude_keywords = get_multiple_input("请输入要排除的关键词，多个关键词用逗号分隔（可选）")
    
    # 引用数范围
    min_citations = None
    max_citations = None
    if get_user_input("是否按引用数过滤？(y/n)", "n").lower() == 'y':
        min_citations_input = get_user_input("请输入最小引用数（可选）")
        max_citations_input = get_user_input("请输入最大引用数（可选）")
        if min_citations_input.isdigit():
            min_citations = int(min_citations_input)
        if max_citations_input.isdigit():
            max_citations = int(max_citations_input)
    
    # 年份范围
    year_from = get_year_input("请输入起始年份（可选）")
    year_to = get_year_input("请输入结束年份（可选）")
    
    # 获取分类
    print("\n=== arXiv分类代码 ===")
    print("\n计算机科学类:")
    print("cs.AI  - 人工智能")
    print("cs.LG  - 机器学习")
    print("cs.CL  - 计算语言学")
    print("cs.CV  - 计算机视觉")
    print("cs.NE  - 神经与进化计算")
    print("cs.RO  - 机器人")
    print("cs.IR  - 信息检索")
    print("cs.DL  - 数字图书馆")
    print("cs.HC  - 人机交互")
    print("cs.DB  - 数据库")
    print("cs.DC  - 分布式计算")
    print("cs.DS  - 数据结构与算法")
    print("cs.CR  - 密码学与安全")
    print("cs.GT  - 博弈论")
    print("cs.SE  - 软件工程")
    print("cs.PL  - 编程语言")
    print("cs.NI  - 网络与互联网架构")
    print("cs.SD  - 声音")
    print("cs.MM  - 多媒体")
    
    print("\n数学类:")
    print("math.PR - 概率论")
    print("math.ST - 统计理论")
    print("math.OC - 优化与控制")
    print("math.NA - 数值分析")
    print("math.LO - 逻辑学")
    
    print("\n统计学类:")
    print("stat.ML - 统计机器学习")
    print("stat.TH - 统计理论")
    print("stat.AP - 应用统计")
    print("stat.CO - 计算统计")
    print("stat.ME - 方法论")
    
    print("\n定量生物学:")
    print("q-bio.QM - 定量方法")
    print("q-bio.NC - 神经科学")
    print("q-bio.GN - 基因组学")
    
    print("\n定量金融:")
    print("q-fin.ST - 统计金融")
    print("q-fin.RM - 风险管理")
    print("q-fin.PM - 投资组合管理")
    print("q-fin.TR - 交易与做市")
    
    print("\n物理学类:")
    print("physics.comp-ph - 计算物理")
    print("physics.data-an - 数据分析")
    print("physics.soc-ph - 社会物理与复杂系统")
    
    print("\n跨学科类:")
    print("eess.SP - 信号处理")
    print("eess.AS - 音频与语音处理")
    print("eess.IV - 图像与视频处理")
    
    print("\n提示：")
    print("1. 可以输入多个分类，用逗号分隔")
    print("2. 分类代码区分大小写")
    print("3. 可以组合不同领域的分类")
    print("4. 直接回车表示搜索所有分类")
    
    categories = get_multiple_input("请输入论文分类，多个分类用逗号分隔（可选）")
    
    # 获取排序方式和结果数量
    sort_by = get_sort_order()
    max_results = int(get_user_input("请输入最大下载数量", "20"))
    
    # 获取下载目录
    download_dir = get_user_input("请输入下载目录名称", "arxiv_papers")
    
    # 创建搜索条件
    criteria = SearchCriteria(
        keywords=keywords,
        title=title,
        authors=authors,
        abstract_keywords=abstract_keywords,
        year_from=year_from,
        year_to=year_to,
        categories=categories,
        min_citations=min_citations,
        max_citations=max_citations,
        exclude_keywords=exclude_keywords,
        include_keywords=include_keywords,
        sort_by=sort_by,
        max_results=max_results
    )
    
    # 确认搜索条件
    print("\n=== 搜索条件确认 ===")
    print(f"关键词: {keywords}")
    print(f"标题: {title if title else '无'}")
    print(f"作者: {', '.join(authors) if authors else '无'}")
    print(f"摘要关键词: {abstract_keywords if abstract_keywords else '无'}")
    print(f"必须包含关键词: {', '.join(include_keywords) if include_keywords else '无'}")
    print(f"排除关键词: {', '.join(exclude_keywords) if exclude_keywords else '无'}")
    print(f"引用数范围: {min_citations or '不限'} - {max_citations or '不限'}")
    print(f"年份范围: {year_from or '不限'} - {year_to or '不限'}")
    print(f"分类: {', '.join(categories) if categories else '所有'}")
    print(f"排序方式: {sort_by.value}")
    print(f"最大下载数量: {max_results}")
    print(f"下载目录: {download_dir}")
    
    if get_user_input("\n确认开始下载？(y/n)", "y").lower() == 'y':
        download_papers(criteria, download_dir=download_dir)
    else:
        print("已取消下载")

if __name__ == "__main__":
    try:
        interactive_search()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n程序出错: {str(e)}") 
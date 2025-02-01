import requests
import os
import json
import time
from datetime import datetime
from tqdm import tqdm
from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum

class SortOrder(Enum):
    """论文排序方式"""
    RELEVANCE = "relevance"
    CITATIONS = "citations"
    YEAR = "year"
    LAST_UPDATED = "lastUpdated"
    CITATIONS_PER_YEAR = "citationsPerYear"
    RECENT_CITATIONS = "recentCitations"
    TITLE = "title"
    AUTHOR = "author"

@dataclass
class SearchCriteria:
    """论文搜索条件"""
    keywords: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract_keywords: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    min_citations: Optional[int] = None
    max_citations: Optional[int] = None
    exclude_keywords: Optional[List[str]] = None
    include_keywords: Optional[List[str]] = None
    sort_by: SortOrder = SortOrder.RELEVANCE
    max_results: int = 20

def get_preset_keywords() -> dict:
    """返回预设的关键词组合"""
    return {
        # 基础AI方向 (1-5)
        "1": {
            "name": "通用AI",
            "keywords": "Artificial Intelligence, AI, Machine Learning, Deep Learning, Neural Network"
        },
        "2": {
            "name": "大语言模型",
            "keywords": "Large Language Model, LLM, GPT, ChatGPT, Transformer, BERT, Language Model"
        },
        "3": {
            "name": "计算机视觉",
            "keywords": "Computer Vision, CV, Image Processing, Object Detection, CNN, Vision Transformer"
        },
        "4": {
            "name": "强化学习",
            "keywords": "Reinforcement Learning, RL, Deep RL, Policy Learning, Q-Learning, DQN"
        },
        "5": {
            "name": "自然语言处理",
            "keywords": "Natural Language Processing, NLP, Text Mining, Information Extraction, Text Generation"
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

        # 新兴技术方向 (11-15)
        "11": {
            "name": "元宇宙AI",
            "keywords": "Metaverse AI, Virtual World AI, Digital Twin, AI Simulation, Virtual Reality AI"
        },
        "12": {
            "name": "Web3与AI",
            "keywords": "Web3 AI, Blockchain AI, Decentralized AI, AI DAO, Smart Contract AI"
        },
        "13": {
            "name": "量子AI",
            "keywords": "Quantum AI, Quantum Machine Learning, Quantum Neural Network, Quantum Computing AI"
        },
        "14": {
            "name": "边缘AI",
            "keywords": "Edge AI, Edge Computing, Edge Intelligence, Distributed AI, Edge Learning"
        },
        "15": {
            "name": "物联网AI",
            "keywords": "IoT AI, Internet of Things AI, Smart IoT, Intelligent IoT, AIoT"
        },

        # AI基础研究 (16-20)
        "16": {
            "name": "AI理论",
            "keywords": "AI Theory, Theoretical AI, Mathematical AI, Statistical Learning, Learning Theory"
        },
        "17": {
            "name": "神经科学与AI",
            "keywords": "Neuroscience AI, Brain-inspired AI, Neural Computing, Cognitive Computing"
        },
        "18": {
            "name": "概率图模型",
            "keywords": "Probabilistic Models, Bayesian Networks, Graphical Models, Probabilistic AI"
        },
        "19": {
            "name": "优化方法",
            "keywords": "AI Optimization, Neural Architecture Search, AutoML, Hyperparameter Optimization"
        },
        "20": {
            "name": "表示学习",
            "keywords": "Representation Learning, Feature Learning, Embedding Learning, Manifold Learning"
        },

        # AI安全与伦理 (21-25)
        "21": {
            "name": "AI安全",
            "keywords": "AI Safety, Safe AI, Robust AI, AI Security, Trustworthy AI"
        },
        "22": {
            "name": "AI伦理",
            "keywords": "AI Ethics, Ethical AI, Responsible AI, AI Governance, AI Policy"
        },
        "23": {
            "name": "隐私保护",
            "keywords": "Privacy-preserving AI, Federated Learning, Secure AI, Confidential Computing"
        },
        "24": {
            "name": "可解释性",
            "keywords": "Explainable AI, XAI, Interpretable AI, AI Interpretation, Model Understanding"
        },
        "25": {
            "name": "公平性",
            "keywords": "AI Fairness, Bias in AI, Fair ML, Ethical ML, AI Accountability"
        },

        # 特殊应用领域 (26-30)
        "26": {
            "name": "机器人AI",
            "keywords": "Robotics AI, Robot Learning, Intelligent Robotics, Robot Intelligence"
        },
        "27": {
            "name": "自动驾驶",
            "keywords": "Autonomous Driving, Self-driving Car, Autonomous Vehicle, Intelligent Vehicle"
        },
        "28": {
            "name": "智慧城市",
            "keywords": "Smart City AI, Urban Intelligence, City Intelligence, Urban Computing"
        },
        "29": {
            "name": "环境AI",
            "keywords": "Environmental AI, Climate AI, Sustainable AI, Green AI, Eco-friendly AI"
        },
        "30": {
            "name": "创意AI",
            "keywords": "Creative AI, AI Art, AI Music, AI Design, Computational Creativity"
        },

        # 新增领域 (31-35)
        "31": {
            "name": "Agent AI",
            "keywords": "AI Agent, Autonomous Agent, Multi-agent System, Agent Learning, Intelligent Agent"
        },
        "32": {
            "name": "医疗AI",
            "keywords": "Medical AI, Healthcare AI, Clinical AI, Medical Diagnosis, AI in Medicine"
        },
        "33": {
            "name": "教育AI",
            "keywords": "Educational AI, AI in Education, Intelligent Tutoring, Learning Analytics"
        },
        "34": {
            "name": "推荐系统",
            "keywords": "Recommender System, Recommendation AI, Personalization, Collaborative Filtering"
        },
        "35": {
            "name": "知识图谱",
            "keywords": "Knowledge Graph, Knowledge Base, Ontology Learning, Semantic Network"
        },

        # 企业应用 (36-40)
        "36": {
            "name": "企业AI",
            "keywords": "Enterprise AI, Business Intelligence, Corporate AI, AI Solution, AI Strategy"
        },
        "37": {
            "name": "AI系统",
            "keywords": "AI System, Machine Learning System, AI Infrastructure, AI Platform"
        },
        "38": {
            "name": "AI工具",
            "keywords": "AI Tools, AI Development, AI Framework, AI Library, AI SDK"
        },
        "39": {
            "name": "AI服务",
            "keywords": "AI Service, AI as a Service, Cloud AI, AI Platform as a Service"
        },
        "40": {
            "name": "AI集成",
            "keywords": "AI Integration, AI Deployment, AI Implementation, Enterprise AI Integration"
        }
    }

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

def get_user_input(prompt: str, default: str = "", allow_null: bool = False) -> str:
    """获取用户输入"""
    if allow_null:
        prompt = f"{prompt} (输入'null'表示不限制)"
    
    user_input = input(f"{prompt} [默认: {default}]: ").strip() if default else input(f"{prompt}: ").strip()
    
    if allow_null and user_input.lower() == 'null':
        return None
    return user_input if user_input else default

def get_multiple_input(prompt: str) -> List[str]:
    """获取多个输入，用逗号分隔"""
    items = get_user_input(prompt)
    return [item.strip() for item in items.split(",")] if items else []

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

def get_paper_categories() -> List[str]:
    """返回论文分类列表"""
    return [
        "Computer Science",
        "Mathematics",
        "Physics",
        "Engineering",
        "Biology",
        "Medicine",
        "Economics",
        "Business",
        "Psychology",
        "Social Sciences"
    ]

def get_sort_order() -> SortOrder:
    """获取排序方式"""
    print("\n=== 选择排序方式 ===")
    print("基础排序:")
    print("1. 相关度排序（默认）")
    print("2. 引用次数")
    print("3. 发表时间")
    print("4. 最近更新")
    
    print("\n高级排序:")
    print("5. 年均引用次数")
    print("6. 最近引用热度")
    print("7. 标题字母顺序")
    print("8. 作者字母顺序")
    
    print("\n排序说明:")
    print("- 相关度排序：根据搜索关键词的匹配程度")
    print("- 年均引用：总引用数除以论文发表年限")
    print("- 最近引用热度：近期引用次数权重更高")
    
    choice = get_user_input("请选择排序方式", "1")
    sort_mapping = {
        "1": SortOrder.RELEVANCE,
        "2": SortOrder.CITATIONS,
        "3": SortOrder.YEAR,
        "4": SortOrder.LAST_UPDATED,
        "5": SortOrder.CITATIONS_PER_YEAR,
        "6": SortOrder.RECENT_CITATIONS,
        "7": SortOrder.TITLE,
        "8": SortOrder.AUTHOR
    }
    return sort_mapping.get(choice, SortOrder.RELEVANCE)

def display_paper_info(paper: Dict):
    """显示论文详细信息"""
    print("\n论文信息:")
    print(f"标题: {paper['title']}")
    print(f"作者: {', '.join(paper['authors'])}")
    print(f"年份: {paper.get('year', 'Unknown')}")
    print(f"引用数: {paper.get('citations', 0)}")
    print(f"来源: {paper.get('venue', 'N/A')}")
    if paper.get('abstract'):
        print(f"\n摘要: {paper['abstract'][:300]}...")

def build_search_query(criteria: SearchCriteria) -> str:
    """构建搜索查询字符串，与arxiv_downloader保持一致"""
    query_parts = []
    
    # 基本关键词搜索
    if criteria.keywords:
        # 分别处理每个关键词，支持OR操作符
        keywords = [k.strip('"').strip() for k in criteria.keywords.split(" OR ")]
        keyword_parts = []
        for keyword in keywords:
            # 对于包含空格的关键词，加上引号
            if ' ' in keyword:
                keyword = f'"{keyword}"'
            keyword_parts.append(f'({keyword})')
        if keyword_parts:
            query_parts.append("(" + " OR ".join(keyword_parts) + ")")
    
    # 标题搜索
    if criteria.title:
        title_parts = [f'title:"{t.strip()}"' for t in criteria.title.split(" OR ")]
        query_parts.append("(" + " OR ".join(title_parts) + ")")
    
    # 作者搜索
    if criteria.authors:
        author_parts = [f'author:"{author.strip()}"' for author in criteria.authors]
        query_parts.append("(" + " OR ".join(author_parts) + ")")
    
    # 摘要关键词搜索
    if criteria.abstract_keywords:
        abstract_parts = [f'abstract:"{k.strip()}"' for k in criteria.abstract_keywords.split(" OR ")]
        query_parts.append("(" + " OR ".join(abstract_parts) + ")")
    
    # 年份限制
    if criteria.year_from or criteria.year_to:
        year_from = criteria.year_from or 1900
        year_to = criteria.year_to or datetime.now().year
        query_parts.append(f'year:[{year_from} TO {year_to}]')
    
    # 组合所有查询条件
    final_query = " AND ".join(f"({part})" for part in query_parts) if query_parts else "*"
    print(f"\n生成的查询语句: {final_query}")
    return final_query

def validate_pdf(filepath: str) -> bool:
    """验证下载的文件是否为有效的PDF"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header.startswith(b'%PDF')
    except Exception:
        return False

def download_paper(url: str, filepath: str, timeout: int = 30) -> bool:
    """下载论文，带有重试机制和PDF验证"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # 验证Content-Type
            if 'application/pdf' not in response.headers.get('content-type', ''):
                print(f"警告：响应不是PDF格式 (Content-Type: {response.headers.get('content-type')})")
                return False
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # 验证PDF文件
            if not validate_pdf(filepath):
                print("警告：下载的文件不是有效的PDF格式")
                os.remove(filepath)  # 删除无效文件
                return False
                
            return True
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                return False
            print(f"下载失败，正在重试 ({attempt + 1}/{max_retries})...")
            time.sleep(2 ** attempt)  # 指数退避
    return False

def create_session_dir(base_dir: str, criteria: SearchCriteria) -> tuple:
    """创建下载会话目录并生成说明文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(base_dir, f"semantic_scholar_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)
    
    # 创建说明文件
    readme_path = os.path.join(session_dir, "download_info.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"# Semantic Scholar论文下载会话信息\n\n")
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
        f.write(f"- 排序方式: {criteria.sort_by.value}\n")
        f.write(f"- 最大下载数量: {criteria.max_results}\n\n")
        
        f.write("## 下载的论文\n\n")
        f.write("| 序号 | 标题 | 作者 | 年份 | 引用数 | 来源 | 下载状态 |\n")
        f.write("|------|------|------|------|--------|------|----------|\n")
    
    return session_dir, readme_path

def update_download_info(readme_path: str, paper: dict, index: int, status: str = "成功"):
    """更新下载信息文件"""
    with open(readme_path, 'a', encoding='utf-8') as f:
        authors = ", ".join(paper['authors'][:3])
        if len(paper['authors']) > 3:
            authors += " et al."
        f.write(f"| {index} | {paper['title']} | {authors} | {paper['year']} | "
               f"{paper['citations']} | {paper.get('venue', 'N/A')} | {status} |\n")

def search_semantic_scholar(criteria: SearchCriteria) -> List[Dict]:
    """从Semantic Scholar搜索论文"""
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    query = build_search_query(criteria)
    
    # 初始化结果列表
    all_papers = []
    total_results = 0
    page_size = 100  # Semantic Scholar的最大页面大小
    max_pages = 10   # 最多获取10页结果
    
    for page in range(max_pages):
        offset = page * page_size
        
        params = {
            "query": query,
            "limit": page_size,
            "offset": offset,
            "fields": "title,authors,year,abstract,citationCount,openAccessPdf,venue,references",
            "sort": criteria.sort_by.value
        }
        
        try:
            print(f"\r正在获取第 {page + 1} 页结果...", end="")
            response = requests.get(base_url, headers=headers, params=params, timeout=30)
            
            # 处理频率限制
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 5))
                print(f"\n达到API访问限制，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # 获取总结果数
            if total_results == 0:
                total_results = data.get('total', 0)
                print(f"\n找到 {total_results} 篇相关论文")
            
            # 处理当前页的论文
            current_papers = []
            for paper in data.get('data', []):
                # 不再只过滤有PDF的论文
                paper_info = {
                    'title': paper.get('title'),
                    'authors': [author.get('name') for author in paper.get('authors', [])],
                    'year': paper.get('year'),
                    'citations': paper.get('citationCount', 0),
                    'abstract': paper.get('abstract'),
                    'venue': paper.get('venue'),
                    'source_id': paper.get('paperId'),
                    'has_pdf': bool(paper.get('openAccessPdf'))
                }
                
                if paper.get('openAccessPdf'):
                    paper_info['pdf_url'] = paper['openAccessPdf'].get('url')
                
                current_papers.append(paper_info)
            
            all_papers.extend(current_papers)
            
            # 检查是否已经获取足够的论文
            if len(all_papers) >= criteria.max_results * 2:  # 获取两倍于需求的论文以便后续过滤
                break
                
            # 检查是否还有更多结果
            if len(data.get('data', [])) < page_size:
                break
                
            time.sleep(1)  # 添加延迟避免触发频率限制
            
        except requests.exceptions.RequestException as e:
            print(f"\n搜索论文时出错: {str(e)}")
            break
    
    print(f"\n共获取到 {len(all_papers)} 篇论文")
    return all_papers

def filter_papers(papers: List[Dict], criteria: SearchCriteria) -> List[Dict]:
    """过滤论文"""
    filtered_count = {
        "total": len(papers),
        "year_filter": 0,
        "citation_filter": 0,
        "keyword_filter": 0,
        "no_pdf": 0,
        "final": 0
    }
    
    filtered = []
    for paper in papers:
        # 检查是否有PDF
        if not paper.get('has_pdf'):
            filtered_count["no_pdf"] += 1
            continue
            
        # 年份过滤
        if criteria.year_from and paper.get('year', 0) < criteria.year_from:
            filtered_count["year_filter"] += 1
            continue
        if criteria.year_to and paper.get('year', 9999) > criteria.year_to:
            filtered_count["year_filter"] += 1
            continue
            
        # 引用数过滤
        if criteria.min_citations and paper.get('citations', 0) < criteria.min_citations:
            filtered_count["citation_filter"] += 1
            continue
        if criteria.max_citations and paper.get('citations', 0) > criteria.max_citations:
            filtered_count["citation_filter"] += 1
            continue
            
        # 关键词过滤
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        if criteria.include_keywords and not all(k.lower() in text.lower() for k in criteria.include_keywords):
            filtered_count["keyword_filter"] += 1
            continue
        if criteria.exclude_keywords and any(k.lower() in text.lower() for k in criteria.exclude_keywords):
            filtered_count["keyword_filter"] += 1
            continue
            
        filtered.append(paper)
    
    filtered_count["final"] = len(filtered)
    
    # 打印过滤统计
    print("\n过滤统计:")
    print(f"初始论文数: {filtered_count['total']}")
    print(f"无PDF下载链接: {filtered_count['no_pdf']}")
    print(f"因年份过滤: {filtered_count['year_filter']}")
    print(f"因引用数过滤: {filtered_count['citation_filter']}")
    print(f"因关键词过滤: {filtered_count['keyword_filter']}")
    print(f"符合条件的论文: {filtered_count['final']}")
    
    return filtered[:criteria.max_results]

def search_papers(criteria: SearchCriteria) -> List[Dict]:
    """统一的论文搜索函数"""
    papers = search_semantic_scholar(criteria)
    
    # 过滤论文
    filtered_papers = filter_papers(papers, criteria)
    
    # 按指定方式排序
    sorted_papers = sort_papers(filtered_papers, criteria.sort_by)
    
    return sorted_papers[:criteria.max_results]

def sort_papers(papers: List[Dict], sort_by: SortOrder) -> List[Dict]:
    """根据指定方式排序论文"""
    if sort_by == SortOrder.CITATIONS:
        return sorted(papers, key=lambda x: x.get('citations', 0), reverse=True)
    elif sort_by == SortOrder.YEAR:
        return sorted(papers, key=lambda x: x.get('year', 0), reverse=True)
    elif sort_by == SortOrder.CITATIONS_PER_YEAR:
        current_year = datetime.now().year
        return sorted(papers, 
                     key=lambda x: x.get('citations', 0) / (current_year - x.get('year', current_year) + 1) 
                     if x.get('year', current_year) < current_year else 0, 
                     reverse=True)
    elif sort_by == SortOrder.TITLE:
        return sorted(papers, key=lambda x: x.get('title', '').lower())
    elif sort_by == SortOrder.AUTHOR:
        return sorted(papers, key=lambda x: x.get('authors', [''])[0].lower() if x.get('authors') else '')
    else:  # SortOrder.RELEVANCE
        return papers  # 保持API返回的顺序

def interactive_search():
    """交互式搜索界面"""
    print("\n=== Semantic Scholar论文下载工具 ===")
    print("(提示：直接按回车使用默认值或跳过，输入'null'表示不限制)")
    print("(关键词提示：使用 OR 连接多个关键词，如 'AI OR Artificial Intelligence')")
    
    # 获取搜索条件
    keywords = get_keywords_input()
    title = get_user_input("请输入论文标题关键词（可选）")
    authors = get_multiple_input("请输入作者姓名，多个作者用逗号分隔（可选）")
    abstract_keywords = get_user_input("请输入摘要关键词（可选）")
    
    # 获取分类
    print("\n可用的论文分类:")
    categories = get_paper_categories()
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category}")
    selected_categories = get_multiple_input("请输入分类编号，多个分类用逗号分隔（可选）")
    selected_categories = [categories[int(i)-1] for i in selected_categories if i.isdigit() and 1 <= int(i) <= len(categories)]
    
    include_keywords = get_multiple_input("请输入必须包含的关键词，用逗号分隔（可选）")
    exclude_keywords = get_multiple_input("请输入要排除的关键词，用逗号分隔（可选）")
    
    year_from = get_user_input("请输入起始年份（可选）")
    year_to = get_user_input("请输入结束年份（可选）")
    
    min_citations = get_user_input("请输入最小引用数（可选）")
    max_citations = get_user_input("请输入最大引用数（可选）")
    max_results = int(get_user_input("请输入最大下载数量", "20"))
    
    sort_by = get_sort_order()
    
    # 确认搜索条件
    print("\n=== 搜索条件确认 ===")
    print(f"关键词: {keywords}")
    print(f"标题: {title if title else '无'}")
    print(f"作者: {', '.join(authors) if authors else '无'}")
    print(f"摘要关键词: {abstract_keywords if abstract_keywords else '无'}")
    print(f"分类: {', '.join(selected_categories) if selected_categories else '所有'}")
    print(f"必须包含关键词: {', '.join(include_keywords) if include_keywords else '无'}")
    print(f"排除关键词: {', '.join(exclude_keywords) if exclude_keywords else '无'}")
    print(f"引用数范围: {min_citations or '不限'} - {max_citations or '不限'}")
    print(f"年份范围: {year_from or '不限'} - {year_to or '不限'}")
    print(f"排序方式: {sort_by.value}")
    print(f"最大下载数量: {max_results}")
    
    if get_user_input("\n确认开始搜索？(y/n)", "y").lower() != 'y':
        print("已取消搜索")
        return
    
    # 创建下载目录
    base_dir = "semantic_scholar_papers"
    session_dir, readme_path = create_session_dir(base_dir, SearchCriteria(
        keywords=keywords,
        title=title,
        authors=authors,
        abstract_keywords=abstract_keywords,
        year_from=int(year_from) if year_from and year_from.isdigit() else None,
        year_to=int(year_to) if year_to and year_to.isdigit() else None,
        min_citations=int(min_citations) if min_citations and min_citations.isdigit() else None,
        max_citations=int(max_citations) if max_citations and max_citations.isdigit() else None,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        sort_by=sort_by,
        max_results=max_results
    ))
    db_path = "papers_db.json"
    
    # 加载数据库
    db = load_paper_database(db_path)
    
    # 搜索论文
    print("\n正在搜索论文...")
    criteria = SearchCriteria(
        keywords=keywords,
        title=title,
        authors=authors,
        abstract_keywords=abstract_keywords,
        year_from=int(year_from) if year_from and year_from.isdigit() else None,
        year_to=int(year_to) if year_to and year_to.isdigit() else None,
        min_citations=int(min_citations) if min_citations and min_citations.isdigit() else None,
        max_citations=int(max_citations) if max_citations and max_citations.isdigit() else None,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        sort_by=sort_by,
        max_results=max_results
    )
    
    papers = search_papers(criteria)
    
    if not papers:
        print("没有找到符合条件的论文")
        return
    
    print(f"\n找到 {len(papers)} 篇符合条件的论文")
    
    # 确认下载
    if get_user_input("\n确认开始下载？(y/n)", "y").lower() != 'y':
        print("已取消下载")
        return
    
    # 下载论文并更新数据库
    print("\n开始下载论文...")
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, paper in enumerate(tqdm(papers), 1):
        if paper['source_id'] in db["papers"]:
            print(f"\n论文已存在数据库中，跳过: {paper['title']}")
            update_download_info(readme_path, paper, i, "已存在")
            skip_count += 1
            continue
            
        title = paper['title']
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{i:02d}-{safe_title[:100]}.pdf"
        filepath = os.path.join(session_dir, filename)
        
        if download_paper(paper['pdf_url'], filepath):
            update_download_info(readme_path, paper, i, "成功")
            success_count += 1
            
            # 更新数据库
            db["papers"][paper['source_id']] = {
                "title": paper['title'],
                "authors": paper['authors'],
                "year": paper['year'],
                "citations": paper['citations'],
                "abstract": paper.get('abstract'),
                "venue": paper.get('venue'),
                "filename": filename,
                "downloaded_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "semantic_scholar"
            }
            save_paper_database(db_path, db)
            
            print(f"\n成功下载: {title}")
        else:
            update_download_info(readme_path, paper, i, "失败")
            fail_count += 1
            print(f"\n下载失败: {title}")
    
    # 添加下载统计信息
    with open(readme_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## 下载统计\n\n")
        f.write(f"- 总论文数: {len(papers)}\n")
        f.write(f"- 成功下载: {success_count}\n")
        f.write(f"- 已存在跳过: {skip_count}\n")
        f.write(f"- 下载失败: {fail_count}\n")

if __name__ == "__main__":
    try:
        interactive_search()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
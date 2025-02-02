import json
import os
import requests
import time
from tqdm import tqdm
import arxiv

def validate_pdf(filepath: str) -> bool:
    """验证文件是否为有效的PDF"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header.startswith(b'%PDF')
    except Exception:
        return False

def download_paper(url: str, filepath: str, max_retries=3) -> bool:
    """下载论文PDF，支持重试"""
    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 验证是否为PDF文件
            content_type = response.headers.get('content-type', '').lower()
            if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                if validate_pdf(filepath):
                    return True
                else:
                    os.remove(filepath)
                    print(f"下载的文件不是有效的PDF格式")
            else:
                print(f"下载的文件不是PDF格式 (Content-Type: {content_type})")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"下载失败，正在重试 ({attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                print(f"下载PDF失败: {str(e)}")
    return False

def search_semantic_scholar(title: str) -> str:
    """从Semantic Scholar搜索论文并返回PDF链接"""
    try:
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        headers = {"Accept": "application/json"}
        params = {
            "query": title,
            "fields": "title,openAccessPdf",
            "limit": 1
        }
        
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("data") and len(data["data"]) > 0:
            paper = data["data"][0]
            if paper.get("openAccessPdf"):
                return paper["openAccessPdf"].get("url")
    except Exception as e:
        print(f"从Semantic Scholar搜索时出错: {str(e)}")
    return None

def search_arxiv(title: str) -> str:
    """从arXiv搜索论文并返回PDF链接"""
    try:
        # 清理标题，移除特殊字符
        clean_title = ' '.join(c for c in title if c.isalnum() or c.isspace())
        
        client = arxiv.Client(
            page_size=1,
            delay_seconds=3,  # 添加延迟避免触发限制
            num_retries=5     # 增加重试次数
        )
        search = arxiv.Search(
            query=f'ti:"{clean_title}"',
            max_results=1
        )
        
        results = list(client.results(search))
        if results:
            paper = results[0]
            # 构建备用URL
            paper_id = paper.get_short_id()
            urls = [
                paper.pdf_url,
                f"https://arxiv.org/pdf/{paper_id}",
                f"https://arxiv.org/pdf/{paper_id}.pdf"
            ]
            return urls
    except Exception as e:
        print(f"从arXiv搜索时出错: {str(e)}")
    return []

def try_alternative_download(paper_info: dict, filepath: str) -> bool:
    """尝试从多个来源下载论文"""
    title = paper_info["title"]
    print(f"\n尝试从其他来源下载: {title}")
    
    # 首先尝试从Semantic Scholar下载
    pdf_url = search_semantic_scholar(title)
    if pdf_url and download_paper(pdf_url, filepath):
        print(f"从Semantic Scholar成功下载")
        return True
    
    # 然后尝试从arXiv下载，尝试多个可能的URL
    urls = search_arxiv(title)
    for url in urls:
        if url and download_paper(url, filepath):
            print(f"从arXiv成功下载")
            return True
    
    print("所有来源都下载失败")
    return False

def clean_database(db_path: str, missing_papers: list):
    """从数据库中移除无法下载的论文记录"""
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        removed_papers = []
        for paper_id, paper_info in missing_papers:
            if paper_id in db["papers"]:
                removed_papers.append(paper_info["title"])
                del db["papers"][paper_id]
        
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        print("\n已从数据库中移除以下无法下载的论文:")
        for title in removed_papers:
            print(f"- {title}")
            
    except Exception as e:
        print(f"清理数据库时出错: {str(e)}")

def check_and_fix_papers():
    """检查论文数据库和实际下载文件的统计，并尝试重新下载缺失的PDF"""
    try:
        # 加载数据库
        db_path = "papers_db.json"
        if not os.path.exists(db_path):
            print("未找到papers_db.json文件")
            return
            
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        # 统计数据库中的论文数量
        db_count = len(db["papers"])
        print(f"\n数据库中记录的论文数量: {db_count}")
        
        # 获取所有PDF文件的路径
        pdf_files = {}
        
        # 检查arxiv文件夹
        arxiv_dir = "arxiv_papers"
        if os.path.exists(arxiv_dir):
            for root, _, files in os.walk(arxiv_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        pdf_files[file] = os.path.join(root, file)
        
        # 检查semantic scholar文件夹
        semantic_dir = "Semantic_scholar_papers"
        if os.path.exists(semantic_dir):
            for root, _, files in os.walk(semantic_dir):
                for file in files:
                    if file.endswith('.pdf'):
                        pdf_files[file] = os.path.join(root, file)
        
        print(f"实际下载的PDF文件数量: {len(pdf_files)}")
        
        # 找出缺失的PDF文件
        missing_papers = []
        for paper_id, paper_info in db["papers"].items():
            filename = paper_info.get("filename")
            if filename and filename not in pdf_files:
                missing_papers.append((paper_id, paper_info))
        
        if missing_papers:
            print(f"\n发现 {len(missing_papers)} 篇论文的PDF文件缺失:")
            for paper_id, paper_info in missing_papers:
                print(f"- {paper_info['title']}")
            
            try:
                print("\n开始自动尝试重新下载缺失的论文...")
                
                # 创建新的下载会话目录
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                session_dir = os.path.join(arxiv_dir, f"download_session_{timestamp}")
                os.makedirs(session_dir, exist_ok=True)
                
                success_count = 0
                failed_papers = []
                for paper_id, paper_info in tqdm(missing_papers, desc="下载进度"):
                    filepath = os.path.join(session_dir, paper_info["filename"])
                    
                    # 首先尝试原始URL
                    original_url = paper_info.get("arxiv_url") or paper_info.get("pdf_url")
                    if original_url and download_paper(original_url, filepath):
                        print(f"\n使用原始链接成功下载: {paper_info['title']}")
                        success_count += 1
                        continue
                    
                    # 如果原始URL失败，尝试其他来源
                    if try_alternative_download(paper_info, filepath):
                        success_count += 1
                    else:
                        failed_papers.append((paper_id, paper_info))
                
                print(f"\n重新下载完成: 成功 {success_count} 篇，失败 {len(missing_papers) - success_count} 篇")
                
                # 如果有下载失败的论文，询问是否从数据库中移除
                if failed_papers:
                    try:
                        choice = input("\n是否从数据库中移除无法下载的论文记录？(y/n): ").lower().strip()
                        if choice == 'y':
                            clean_database(db_path, failed_papers)
                    except (KeyboardInterrupt, EOFError):
                        print("\n操作已取消")
                        
            except (KeyboardInterrupt, EOFError):
                print("\n操作已取消")
        else:
            print("\n所有论文PDF文件都已正确下载")
    
    except Exception as e:
        print(f"\n程序执行出错: {str(e)}")
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")

if __name__ == "__main__":
    try:
        check_and_fix_papers()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n程序出错: {str(e)}") 
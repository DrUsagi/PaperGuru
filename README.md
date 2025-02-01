# PaperGuru

## 项目简介
该项目旨在从arXiv和Semantic Scholar下载学术论文，并将其存储在本地文件夹中。
因为法律合规问题本项目暂不支持从Scihub下载论文。
本项目旨在成为世界上最好用的批量下载论文助手。若觉得好用烦请给个star。

![项目图片](readme.jpg) 
## 依赖安装


1. 确保已安装Python 3.x。
2. 使用以下命令安装所需的Python库：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 在Terminal或CMD中运行`python open_papers_downloader.py`以启动Semantic Scholar下载器。
2. 或运行 `python arxiv_downloader.py` 以启动arXiv下载器。
3. 之后在Terminal或CMD中根据提示输入所需的下载参数。
4. 这两个下载器都支持一次性下载大量论文。 
5. 脚本连接到arXiv和Semantic Scholar API以检索论文信息。
6. 下载的论文存储在`arxiv_papers`和`Semantic_scholar_papers`文件夹中。
7. 每一次下载任务会在上述文件夹中单独生成一个文件夹，并在里面生成一个md记录下本次任务的搜索条件。
8. 下载的Citation信息记录在`papers_db.json`中。每次执行下载任务时会检索json的信息，如果论文已经被下载过，则不会重复下载。


## 注意事项

若大量下载有被arxiv API或Semantic Scholar API封禁的风险。请合理使用本项目。
本项目遵守GPL-3.0许可证。只限开源社区使用，严格禁止商用。

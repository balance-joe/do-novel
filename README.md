# do-novel
使用大模型下载小说网站


```shell

# 创建环境
conda create -n do_novel_env python=3.12 -y

# 激活环境
conda activate do_novel_env

# 使用清华源安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

```


# 小说下载器开发文档

## 1. 项目概述

### 1.1 项目背景
开发一个基于配置文件的多源小说下载器，通过YAML配置文件适配不同小说网站结构，实现统一的小说内容抓取功能。

### 1.2 项目目标
- 通过配置文件适配多个小说网站
- 支持常见网站结构差异（分页、查看更多、动态加载等）
- 提供简洁易用的下载接口
- 可选的大模型辅助配置生成功能

### 1.3 核心价值
- **用户价值**：一个工具解决多网站小说下载需求
- **技术价值**：配置驱动架构，易于维护和扩展
- **创新价值**：AI辅助配置生成，降低使用门槛

## 2. 功能需求

### 2.1 核心功能
- [ ] 配置文件解析与管理
- [ ] 小说元信息提取（标题、作者、简介等）
- [ ] 章节列表抓取（支持分页和查看更多）
- [ ] 章节内容抓取（支持多页内容合并）
- [ ] 内容过滤和清理
- [ ] 下载进度显示
- [ ] 文件保存和管理

### 2.2 扩展功能
- [ ] 并发下载支持
- [ ] 断点续传
- [ ] 多格式输出（TXT、EPUB、PDF）
- [ ] 配置验证工具
- [ ] 大模型辅助配置生成
- [ ] 配置共享平台集成

## 3. 系统架构

### 3.1 架构图
```
+----------------+     +----------------+     +----------------+
|   配置文件      |     |   下载引擎      |     |   输出处理      |
|   Config      |---->|   Downloader   |---->|   Output       |
|   Manager     |     |   Engine       |     |   Processor    |
+----------------+     +----------------+     +----------------+
         |                      |                      |
         v                      v                      v
+----------------+     +----------------+     +----------------+
|   配置验证      |     |   网络请求      |     |   文件保存      |
|   Validator   |     |   Fetcher      |     |   Saver        |
+----------------+     +----------------+     +----------------+
```

### 3.2 组件说明
- **配置管理器**：加载、验证、管理站点配置文件
- **下载引擎**：核心下载逻辑，协调各组件工作
- **网络请求器**：处理HTTP请求和响应
- **内容解析器**：根据配置解析HTML内容
- **输出处理器**：处理下载结果的保存和格式化

## 4. 配置文件设计

### 4.1 配置结构
```yaml
# 必需配置
name: "网站名称"
base_url: "https://example.com"
encoding: "utf-8"

# 小说信息提取
novel:
  title: "//h1/text()"
  author: "regex:作者[:：]\\s*([^<]+)"
  update_time: "//span[@class='time']/text()"
  intro: "//div[@class='intro']/text()"

# 章节列表配置
chapters:
  container: "//div[@class='chapter-list']"
  item: "a"
  title: "text()"
  url: "@href"
  has_more: true
  more_url: "//a[@class='more']/@href"

# 章节内容配置
content:
  container: "//div[@id='content']"
  text: "p/text()"
  has_pages: true
  page_pattern: "{url}_{page}.html"
  page_start: 0
  page_end: 2

# 过滤规则
filters:
  - "本站所有内容"
  - "regex:请[勿勿]开启浏览器"
```

### 4.2 配置示例
提供多个典型网站的配置示例：
- 简单单页结构网站
- 需要查看更多按钮的网站
- 内容分页的网站
- 动态加载的网站

## 5. 技术选型

### 5.1 核心技术
- **编程语言**: Python 3.8+
- **异步框架**: asyncio + aiohttp
- **HTML解析**: lxml + BeautifulSoup
- **配置解析**: PyYAML
- **正则引擎**: re

## 6. 开发计划

### Phase 1: 核心功能 (1-2周)
- [ ] 基础配置文件解析
- [ ] 简单网站适配（单页结构）
- [ ] 基础下载功能
- [ ] 命令行界面

### Phase 2: 高级功能 (2-3周)
- [ ] 复杂网站支持（分页、查看更多）
- [ ] 内容过滤和清理
- [ ] 进度显示和错误处理
- [ ] 配置验证工具

## 7. 接口设计

### 7.1 核心类接口
```python
class NovelDownloader:
    def __init__(self, config_path: str):
        """初始化下载器"""
        pass
    
    async def download(self, url: str) -> Dict:
        """下载小说"""
        pass
    
    async def get_novel_info(self, url: str) -> Dict:
        """获取小说信息"""
        pass
    
    async def get_chapter_list(self, url: str) -> List[Dict]:
        """获取章节列表"""
        pass
    
    async def get_chapter_content(self, url: str) -> str:
        """获取章节内容"""
        pass
```

### 7.2 工具接口
```python
class ConfigValidator:
    def validate(self, config: Dict) -> bool:
        """验证配置有效性"""
        pass
    
    def test_config(self, config: Dict, test_url: str) -> Dict:
        """测试配置效果"""
        pass
```
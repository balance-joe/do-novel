import json
import os
from dotenv import load_dotenv
from parsel import Selector
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from models.data_models import ChapterListConfig, XPathTemplate
from service import novel_service
from service.agent.generator_chapter_agent import XPathGeneratorChapterAgent
from service.agent.generator_content_agent import XPathGeneratorContentAgent
from service.agent.generator_novel_agent import XPathGeneratorNovelAgent
from service.config_service import ConfigService
from service.crawl_service import CrawlService



if __name__ == "__main__":
    
    load_dotenv()


    # 读取本地 HTML 文件内容
    content_path = './doc/content.html'
    with open(content_path, 'r', encoding='utf-8') as file:
        content_html = file.read()    

    # 读取本地 HTML 文件内容
    chpter_path = './doc/chapter.html'
    with open(chpter_path, 'r', encoding='utf-8') as file:
        chapter_html = file.read()    
    
    # 创建 CrawlService 实例并清理HTML
    crawl_service = CrawlService()
    clean_content_html = crawl_service.extract_clean_body(content_html)
    
    clean_chapter_html = crawl_service.extract_clean_body(chapter_html)
    
    
    model_name= os.getenv("MODEL_NAME")  # 直接获取字符串
    model_key=os.getenv("MODEL_KEY")    # 直接获取字符串
    print(f"使用模型: {model_name}")
    print(f"使用密钥: {model_key}")
    
    # 1. 初始化 ConfigService
    config_service = ConfigService()
    
    # 2. 加载配置字典
    # 这一步返回的是一个字典 (dict)
    raw_config_dict = config_service.load_config("https://templat.com")

    # 3. 【关键修正】将字典转换为 Pydantic 对象
    # 现在 config_temple 才是 XPathTemplate 实例，拥有 .site, .novel 等属性
    try:
        # 假设使用 Pydantic V2，使用 model_validate
        config_temple: XPathTemplate = XPathTemplate.model_validate(raw_config_dict)
    except Exception as e:
        print(f"❌ 严重错误: 无法将加载的配置转换为 XPathTemplate 对象。请检查模板JSON结构是否与Pydantic模型完全匹配。")
        print(f"原始错误: {e}")
        # 停止执行
        exit()

    # 4. 赋值站点信息 (现在可以安全地使用点号访问 .site 属性)
    config_temple.site.name = "测试站点" 
    config_temple.site.base_url = "https://www.cansy.cn/"
    config_temple.site.encoding = "utf-8"
    config_temple.site.user_agent = "Custom UA String"
    config_temple.site.delay = 1.0

    # # 获取小说详情
    print(f"✅ 小说详情页面xpath规则生成结果:")
    generatorNovel = XPathGeneratorNovelAgent(model_name, model_key)
    novel = generatorNovel.generate_rules(html=clean_chapter_html)

    # 获取章节列表    
    print(f"✅ 章节页面xpath规则生成结果:") 
    generatorChapter = XPathGeneratorChapterAgent(model_name, model_key)
    chapters = generatorChapter.generate_rules(html=clean_chapter_html)

    # print(f"✅ 内容页面xpath规则生成结果:")    
    generatorContent = XPathGeneratorContentAgent(model_name, model_key)
    content = generatorContent.generate_rules(html=clean_content_html)

    # 5. 覆盖 AI 生成的规则
    config_temple.novel = json.loads(novel)
    config_temple.chapters = json.loads(chapters)
    config_temple.content = json.loads(content)

    print("✅ 最终合并的配置对象:")
    print(config_temple)
    config_service.save_config_to_json(config_temple)
    
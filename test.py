import os
from dotenv import load_dotenv
from parsel import Selector
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from models.data_models import ChapterListConfig
from service import novel_service
from service.agent.generator_chapter_agent import XPathGeneratorChapterAgent
from service.agent.generator_content_agent import XPathGeneratorContentAgent
from service.agent.generator_novel_agent import XPathGeneratorNovelAgent
from service.crawl_service import CrawlService



if __name__ == "__main__":
    
    load_dotenv()

#  # 测试 HTML 内容
#     test_html = """
#     <html>
#         <body>
#             <div class="container">
#                 <h1>测试标题</h1>
#                 <ul>
#                     <li>项目1</li>
#                     <li>项目2</li>
#                     <li>项目3</li>
#                 </ul>
#                 <a href="https://example.com" class="link">示例链接</a>
#             </div>
#         </body>
#     </html>
#     """
    


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
    
    
    novel_service = novel_service.NovelService('aaa.com')
    
    
    
    # 示例使用
    html_content_1 = """
        <div id="listtj">
                &nbsp;推荐阅读：
                <a href='//www.tzkczc.com/22_22520/' title="楚君归是哪部小说的主角">楚君归是哪部小说的主角</a>
                <a href='//www.tzkczc.com/26_26023/' style="font-weight:bold" title="醉虎作品">醉虎作品</a>
                <a href='//www.tzkczc.com/29_29865/' title="九龙归一诀魔风烈">九龙归一诀魔风烈</a>
                <a href='//www.tzkczc.com/40_40889/' style="font-weight:bold" title="楚辞琛沈若京小说免费阅读">楚辞琛沈若京小说免费阅读</a>
                <a href='//www.tzkczc.com/47_47574/' title="李五丫时柳李七郎寒门大俗人免费全文阅读">李五丫时柳李七郎寒门大俗人免费全文阅读</a>
                <a href='//www.tzkczc.com/65_65410/' style="font-weight:bold" title="篮坛科学家">篮坛科学家</a>
                <a href='//www.tzkczc.com/77_77391/' title="大明烟火在线全文阅读">大明烟火在线全文阅读</a>
                <a href='//www.tzkczc.com/92_92638/' style="font-weight:bold" title="林夜小说免费阅读">林夜小说免费阅读</a>
                <a href='//www.tzkczc.com/114_114672/' title="黎明之剑高文小说全文免费阅读完整版">黎明之剑高文小说全文免费阅读完整版</a>
                <a href='//www.tzkczc.com/160_160439/' style="font-weight:bold" title="绝世龙王齐天沈秋水全文阅读完整版大结局">绝世龙王齐天沈秋水全文阅读完整版大结局</a>
                <a href='//www.tzkczc.com/162_162517/' title="上门龙婿叶辰最新更新章节免费阅读">上门龙婿叶辰最新更新章节免费阅读</a>
            </div>
    """

    # 使用正则表达式版本
    compressed_1_regex = novel_service.compress_html(html_content_1)
    print("正则表达式版本 - 压缩后的导航 (移除重复链接):")
    print(compressed_1_regex)


    # 获取小说详情
    # print(f"✅ 小说详情页面xpath规则生成结果:")    
    # generatorNovel = XPathGeneratorNovelAgent(model_name, model_key)
    # print(generatorNovel.generate_rules(html=clean_chapter_html))
    
    # # 获取章节列表    
    # print(f"✅ 章节页面xpath规则生成结果:")    
    # generatorChapter = XPathGeneratorChapterAgent(model_name, model_key)
    # print(generatorChapter.generate_rules(html=clean_chapter_html))
        
    # print(f"✅ 内容页面xpath规则生成结果:")    
    # generatorContent = XPathGeneratorContentAgent(model_name, model_key)
    # print(generatorContent.generate_rules(html=clean_content_html))

    
    
    # novel_service = novel_service.NovelService()

    # 测试 1：提取 h1 标题文本
    # xpath1 = "//h1/text()"
    # print("h1标题：", novel_service.extract_by_xpath(xpath1, test_html))  # 输出：['测试标题']
    
    # # 测试 2：提取所有 li 文本
    # xpath2 = "//ul/li"
    # print("li列表：", novel_service.extract_by_xpath(xpath2, test_html))  # 输出：['项目1', '项目2', '项目3']
    
    # # 测试 3：提取 a 标签的 href 属性
    # xpath3 = "//a/@href"
    # print("链接地址：", novel_service.extract_by_xpath(xpath3, test_html))  # 输出：['https://example.com']
    
    # # 测试 4：无效 XPath（语法错误）
    # xpath4 = "//div[@class=container]"  # 缺少引号
    # print("无效XPath结果：", novel_service.extract_by_xpath(xpath4, test_html))  # 输出错误提示和空列表

    
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from models.data_models import ChapterListConfig
from service import novel_service
from service.agent.generator_chapter_agent import XPathGeneratorChapterAgent
from service.agent.generator_content_agent import XPathGeneratorContentAgent
from service.crawl_service import CrawlService



if __name__ == "__main__":
    
    load_dotenv()

 # 测试 HTML 内容
    test_html = """
    <html>
        <body>
            <div class="container">
                <h1>测试标题</h1>
                <ul>
                    <li>项目1</li>
                    <li>项目2</li>
                    <li>项目3</li>
                </ul>
                <a href="https://example.com" class="link">示例链接</a>
            </div>
        </body>
    </html>
    """
    novel_service = novel_service.NovelService()
    
    # 测试 1：提取 h1 标题文本
    xpath1 = "//h1/text()"
    print("h1标题：", novel_service.extract_by_xpath(xpath1, test_html))  # 输出：['测试标题']
    
    # 测试 2：提取所有 li 文本
    xpath2 = "//ul/li"
    print("li列表：", novel_service.extract_by_xpath(xpath2, test_html))  # 输出：['项目1', '项目2', '项目3']
    
    # 测试 3：提取 a 标签的 href 属性
    xpath3 = "//a/@href"
    print("链接地址：", novel_service.extract_by_xpath(xpath3, test_html))  # 输出：['https://example.com']
    
    # 测试 4：无效 XPath（语法错误）
    xpath4 = "//div[@class=container]"  # 缺少引号
    print("无效XPath结果：", novel_service.extract_by_xpath(xpath4, test_html))  # 输出错误提示和空列表



    # # 读取本地 HTML 文件内容
    # path = './doc/content.html'
    # with open(path, 'r', encoding='utf-8') as file:
    #     html_content = file.read()
    

    # print(f"✅ 成功读取HTML文件，长度: {len(html_content)} 字符")
    
    # # 创建 CrawlService 实例并清理HTML
    # crawl_service = CrawlService()
    # clean_html = crawl_service.extract_clean_body(html_content)
    
    # model_name= os.getenv("MODEL_NAME")  # 直接获取字符串
    # model_key=os.getenv("MODEL_KEY")    # 直接获取字符串
    # print(f"使用模型: {model_name}")
    # print(f"使用密钥: {model_key}")
    # return
    # generator = XPathGeneratorContentAgent(model_name, model_key)
    # print(generator.generate_rules(html=clean_html))
    
    
    # template = main()
    
    # if template:
    #     print("\n🎉 XPath模板生成完成！")
    #     print("您可以复制上面的模板用于您的爬虫配置。")
    #     print(template)
    # else:
    #     print("\n💥 XPath模板生成失败。")
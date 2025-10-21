import os
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from models.data_models import ChapterListConfig
from service.agent.generator_chapter_agent import XPathGeneratorChapterAgent
from service.agent.generator_content_agent import XPathGeneratorContentAgent
from service.crawl_service import CrawlService

# # 设置 DeepSeek API 密钥
# os.environ['DEEPSEEK_API_KEY'] = 'sk-e1e6d80ddacf4e279462a15d96b1d7ba'

# # 创建XPath分析Agent
# xpath_agent = Agent(
#     'deepseek:deepseek-chat',
#     deps_type=int,
#     output_type=ChapterListConfig,
#     system_prompt=(
#         '你是一个专业的XPath分析专家。'
#         '请仔细分析用户提供的HTML代码结构，从中识别出章节目录部分。'
#         '你的任务是生成精确的XPath表达式来定位以下元素：'
#         '1. container: 包含所有章节的容器元素'
#         '2. item: 单个章节条目'
#         '3. title: 章节标题文本'
#         '4. url: 章节链接地址'
#         '5. pagination: 判断是否有分页（true/false）'
#         '5. more_url: 如果有分页，提供“更多章节”或下一页的XPath，否则为null。'
#         '请基于HTML的实际结构生成XPath，确保表达式能够准确匹配目标元素。'
#         '对于pagination字段，如果发现"下一页"、"下一章"等分页元素，返回true，否则返回false。'
#     ),
# )


# def main():
#     """主函数：读取HTML文件，分析结构并生成XPath模板"""
#     path = './doc/chapter.html'
    
#     try:
#         # 读取本地 HTML 文件内容
#         with open(path, 'r', encoding='utf-8') as file:
#             html_content = file.read()
        
#         print(f"✅ 成功读取HTML文件，长度: {len(html_content)} 字符")
        
#         # 创建 CrawlService 实例并清理HTML
#         crawl_service = CrawlService()
#         clean_html = crawl_service.extract_clean_body(html_content)
#         print(f"✅ HTML清理完成，长度: {len(clean_html)} 字符")
        
#         # 构建分析提示
#         prompt = f"""
# 请分析以下HTML代码结构，生成章节目录的XPath选择器：

# HTML内容:
# {clean_html}...

# [完整HTML内容共{len(clean_html)}字符]

# 请重点分析：
# 1. 章节列表的容器（通常是ul、ol、div等包含多个章节的元素）
# 2. 单个章节条目的结构
# 3. 章节标题的显示方式
# 4. 章节链接的定位
# 5. 是否存在分页导航

# 请基于实际HTML结构生成精确的XPath表达式。
# """
        
#         print("🔍 开始分析HTML结构并生成XPath模板...")
        
#         # 使用Agent分析HTML并生成XPath模板
#         result = xpath_agent.run_sync(prompt)
#         print(result)
#         extracted_template = result.output
        
#         # # 输出生成的模板
#         # print("\n" + "="*60)
#         # print("# 章节目录XPath模板（章节列表页）")
#         # print("="*60)
#         # print("chapters:")
#         # print(f"  container: \"{extracted_template.container}\"")
#         # print(f"  item: \"{extracted_template.item}\"") 
#         # print(f"  title: \"{extracted_template.title}\"")
#         # print(f"  url: \"{extracted_template.url}\"")
#         # print(f"  pagination: {str(extracted_template.pagination).lower()}      # 章节列表是否分页")
#         # print(f"  more_url: {str(extracted_template.more_url).lower()}      # 章节列表是否分页")
        
#         return extracted_template
        
#     except FileNotFoundError:
#         print(f"❌ 错误：找不到文件 {path}")
#         print("请确保doc/content.html文件存在")
#         return None
#     except Exception as e:
#         print(f"❌ 发生错误: {str(e)}")
#         return None

if __name__ == "__main__":
    
    # 读取本地 HTML 文件内容
    path = './doc/content.html'
    with open(path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    

    print(f"✅ 成功读取HTML文件，长度: {len(html_content)} 字符")
    
    # 创建 CrawlService 实例并清理HTML
    crawl_service = CrawlService()
    clean_html = crawl_service.extract_clean_body(html_content)
    
    
    model_name='deepseek:deepseek-chat'
    model_key='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    generator = XPathGeneratorContentAgent(model_name, model_key)
        
    print(generator.generate_rules(html=clean_html))
    
    
    # template = main()
    
    # if template:
    #     print("\n🎉 XPath模板生成完成！")
    #     print("您可以复制上面的模板用于您的爬虫配置。")
    #     print(template)
    # else:
    #     print("\n💥 XPath模板生成失败。")
from lxml import html
from lxml.etree import XPathError, ParserError


def extract_by_xpath(xpath_rule: str, html_content: str):
    """
    从 HTML 中提取符合 XPath 规则的内容
    
    参数:
        xpath_rule: XPath 提取规则（字符串）
        html_content: 待解析的 HTML 字符串
    
    返回:
        list: 提取到的内容列表（元素可能是文本、属性值或节点对象，根据 XPath 规则而定）
              若解析失败或无结果，返回空列表
    """
    if not isinstance(xpath_rule, str) or not xpath_rule.strip():
        print("错误：XPath 规则不能为空字符串")
        return []
    
    if not isinstance(html_content, str) or not html_content.strip():
        print("错误：HTML 内容不能为空字符串")
        return []
    
    try:
        # 解析 HTML 内容为可 XPath 查询的对象
        tree = html.fromstring(html_content)
    except ParserError as e:
        print(f"HTML 解析失败：{str(e)}")
        return []
    
    try:
        # 执行 XPath 查询
        results = tree.xpath(xpath_rule)
        # 对结果进行简单格式化（可选，根据需求调整）
        formatted_results = []
        for item in results:
            # 若结果是元素节点，提取其文本（可根据需求修改，比如保留节点对象）
            if hasattr(item, 'text'):
                formatted_results.append(item.text.strip() if item.text else '')
            else:
                # 非元素节点（如属性值、文本节点等）直接保留
                formatted_results.append(str(item).strip())
        return formatted_results
    except XPathError as e:
        print(f"XPath 语法错误：{str(e)}")
        return []
    except Exception as e:
        print(f"提取过程出错：{str(e)}")
        return []


# 示例用法
if __name__ == "__main__":
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
    
    # 测试 1：提取 h1 标题文本
    xpath1 = "//h1/text()"
    print("h1标题：", extract_by_xpath(xpath1, test_html))  # 输出：['测试标题']
    
    # 测试 2：提取所有 li 文本
    xpath2 = "//ul/li"
    print("li列表：", extract_by_xpath(xpath2, test_html))  # 输出：['项目1', '项目2', '项目3']
    
    # 测试 3：提取 a 标签的 href 属性
    xpath3 = "//a/@href"
    print("链接地址：", extract_by_xpath(xpath3, test_html))  # 输出：['https://example.com']
    
    # 测试 4：无效 XPath（语法错误）
    xpath4 = "//div[@class=container]"  # 缺少引号
    print("无效XPath结果：", extract_by_xpath(xpath4, test_html))  # 输出错误提示和空列表

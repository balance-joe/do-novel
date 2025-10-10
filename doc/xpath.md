# XPath 核心操作指南

## 1️⃣ XPath 核心概念

* **目的**：用于在 XML 或 HTML 文档树中导航和定位节点（元素、属性、文本等）。
* **节点类型**：

  * 元素节点：HTML 或 XML 元素，例如 `<book>`
  * 属性节点：元素属性，如 `lang="en"`
  * 文本节点：元素或属性的文本内容，如 `Harry Potter`
  * 命名空间节点：XML 中的命名空间声明
  * 处理指令节点（Processing Instruction）：例如 `<?xml-stylesheet ...?>`
  * 注释节点：`<!-- comment -->`
  * 文档（根）节点：整个 XML/HTML 文档的根
* **基本值（Atomic value）**：无父或无子节点的节点值，如文本或属性值
* **项目（Item）**：基本值或节点
* **节点关系**：父节点、子节点、同胞节点、先辈节点、后代节点

### 节点关系示例

```xml
<bookstore> <!-- 文档节点 -->
  <book> <!-- 元素节点 -->
    <title lang="eng">Harry Potter</title> <!-- 元素节点 -->
    <price>29.99</price>
  </book>
  <book>
    <title lang="eng">Learning XML</title>
    <price>39.95</price>
  </book>
</bookstore>
```

* **父节点（Parent）**：`book` 是 `title` 和 `price` 的父节点
* **子节点（Children）**：`title` 和 `price` 是 `book` 的子节点
* **同胞节点（Sibling）**：`title` 和 `price` 互为同胞
* **先辈节点（Ancestor）**：`title` 的先辈是 `book` 和 `bookstore`
* **后代节点（Descendant）**：`bookstore` 的后代是 `book`、`title` 和 `price`

## 2️⃣ 路径表达式语法（核心）

| 表达式      | 描述              | 示例（假设基于提供的 bookstore XML）    |
| -------- | --------------- | ---------------------------- |
| nodename | 选取此节点的所有子节点     | book 选取所有属于当前节点子元素的 book 节点  |
| /        | 从根节点开始选取（绝对路径）  | /bookstore 选取根元素 bookstore   |
| //       | 从任意位置开始选取（相对路径） | //book 选取文档中所有的 book 元素      |
| .        | 选取当前节点          | ./title 选取当前节点下的 title 子节点   |
| ..       | 选取当前节点的父节点      | //title/.. 选取所有 title 元素的父节点 |
| @        | 选取属性            | //@lang 选取所有名为 lang 的属性      |

## 3️⃣ 谓语（Predicates）

* 谓语写在方括号 [] 中，用于查找特定节点或包含指定值的节点。

示例：

```xpath
/bookstore/book[1]               # 第一个 book 元素
/bookstore/book[last()]           # 最后一个 book 元素
/bookstore/book[last()-1]         # 倒数第二个 book 元素
/bookstore/book[position()<3]     # 前两个 book 元素
//title[@lang]                    # 所有拥有 lang 属性的 title 元素
//title[@lang='eng']              # lang='eng' 的 title 元素
/bookstore/book[price>35.00]      # price>35 的 book 元素
/bookstore/book[price>35.00]//title # price>35 的 book 中所有 title 元素
```

## 4️⃣ 通配符

| 通配符    | 描述         | 示例            |
| ------ | ---------- | ------------- |
| *      | 匹配任何元素节点   | /bookstore/*  |
| @*     | 匹配任何属性节点   | //title[@*]   |
| node() | 匹配任何类型的节点  | //book/node() |
| //*    | 选取文档中的所有元素 | //*           |

## 5️⃣ 轴（Axes）

轴可定义相对于当前节点的节点集。

| 轴名称                | 描述                    | 示例                          |
| ------------------ | --------------------- | --------------------------- |
| ancestor           | 选取当前节点的所有先辈（父、祖父等）    | ancestor::bookstore         |
| ancestor-or-self   | 选取当前节点的所有先辈以及当前节点本身   | ancestor-or-self::bookstore |
| attribute          | 选取当前节点的所有属性           | @lang                       |
| child              | 选取当前节点的所有子元素          | child::book                 |
| descendant         | 选取当前节点的所有后代元素（子、孙等）   | descendant::title           |
| descendant-or-self | 选取当前节点的所有后代元素以及当前节点本身 | descendant-or-self::book    |
| following          | 选取文档中当前节点结束标签之后的所有节点  | following::price            |
| following-sibling  | 选取当前节点之后的所有同级节点       | following-sibling::book     |
| namespace          | 选取当前节点的所有命名空间节点       | namespace::*                |
| parent             | 选取当前节点的父节点            | parent::book                |
| preceding          | 选取文档中当前节点开始标签之前的所有节点  | preceding::title            |
| preceding-sibling  | 选取当前节点之前的所有同级节点       | preceding-sibling::book     |
| self               | 选取当前节点本身              | self::book                  |

## 6️⃣ 运算符

XPath 表达式可返回节点集、字符串、逻辑值以及数字。

| 运算符   | 描述    | 示例                        | 返回值        |      |                  |
| ----- | ----- | ------------------------- | ---------- | ---- | ---------------- |
| `     | `     | 节点集并集                     | //book     | //cd | 所有 book 和 cd 节点集 |
| `+`   | 加法    | 6 + 4                     | 10         |      |                  |
| `-`   | 减法    | 6 - 4                     | 2          |      |                  |
| `*`   | 乘法    | 6 * 4                     | 24         |      |                  |
| `div` | 除法    | 8 div 4                   | 2          |      |                  |
| `mod` | 求余    | 5 mod 2                   | 1          |      |                  |
| `=`   | 等于    | price=9.80                | true/false |      |                  |
| `!=`  | 不等于   | price!=9.80               | true/false |      |                  |
| `<`   | 小于    | price<9.80                | true/false |      |                  |
| `<=`  | 小于或等于 | price<=9.80               | true/false |      |                  |
| `>`   | 大于    | price>9.80                | true/false |      |                  |
| `>=`  | 大于或等于 | price>=9.80               | true/false |      |                  |
| `and` | 逻辑与   | price>9.00 and price<9.90 | true/false |      |                  |
| `or`  | 逻辑或   | price=9.80 or price=9.70  | true/false |      |                  |

## 7️⃣ 常用函数

```xpath
text()                       # 获取文本节点，如 //title/text()
contains(@attr, 'str')       # 属性包含指定字符串，如 //title[contains(@lang, 'eng')]
starts-with(@attr, 'str')    # 属性值以字符串开头
normalize-space([string])     # 去除首尾空白，内部连续空格合并为1
count()                        # 节点数量，如 count(//book)
name()                        # 返回节点名称
substring(string, start, length)  # 截取字符串
substring-before(string, substring) / substring-after(string, substring) # 截取特定部分
boolean(expr)                 # 转布尔值
not(expr)                     # 逻辑非
```

## 8️⃣ 组合路径

```xpath
//book/title | //book/price               # 多路径并集
//title | //price                           # 文档中所有 title 和 price 元素
/bookstore/book/title | //price            # bookstore 下 book 的 title 和所有 price 元素
//div[@class='content']/a[text()='下一页'] # 属性+文本组合匹配
```

## 9️⃣ 提示与性能优化

1. 绝对路径 `/html/body/div` 从根开始，依赖结构；相对路径 `//div[@class='content']` 更灵活。
2. 性能优化：

   * 避免遍历整个文档，尽量结合标签名和属性，如 `//div[@id='main']` 优于 `//*[@id='main']`
   * 避免连续使用 `//`，推荐使用轴定位或组合路径
   * 使用唯一属性（id/class）快速定位
3. 文本提取：在定位元素后加 `/text()`。
4. 命名空间：处理 XML 时，如有命名空间需绑定前缀再使用，如 `//x:book`。

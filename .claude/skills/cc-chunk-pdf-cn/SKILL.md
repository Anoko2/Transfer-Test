---
name: cc-chunk-pdf-cn
description: 索引和分拆大型 PDF 课程资料。当用户需要将大型 PDF 教材或课件拆分成小章节、创建章节索引、或者让 AI 更容易阅读大型 PDF 时使用此技能。支持自动识别章节结构并生成索引文件和分拆后的小 PDF 文件。
argument-hint: <PDF文件路径>
---

# PDF 索引与分拆工具

## 功能概述

此技能用于处理大型 PDF 课程资料，提供两个核心功能：

1. **生成章节索引** - 创建 `{pdf名}-index.md` 索引文件
2. **分拆 PDF 文件** - 按章节将大 PDF 拆分成多个小 PDF 文件

## 使用方法

### 输入参数

- `$ARGUMENTS` - PDF 文件的路径（必需）

### 使用示例

```
/cc-chunk-pdf-cn references/textbooks/filename.pdf
```

## 执行步骤

### 步骤 1: 分析 PDF 结构

首先使用 pdfplumber 或 pypdf 读取 PDF，获取：
- 总页数
- PDF 书签/大纲（如果有）
- 各页面的标题文本（用于识别章节）

```python
from pypdf import PdfReader
import pdfplumber

# 读取 PDF 基本信息
reader = PdfReader("$ARGUMENTS")
total_pages = len(reader.pages)

# 尝试获取书签大纲
outline = reader.outline if reader.outline else None

# 如果没有书签，需要通过页面内容识别章节
with pdfplumber.open("$ARGUMENTS") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        # 分析首行或大字体文本找章节标题
```

### 步骤 2: 智能识别章节

章节识别策略（按优先级）：

1. **使用 PDF 书签** - 如果 PDF 有书签/大纲，直接使用
2. **识别章节标题模式** - 查找如 "Chapter 1", "第一章", "Section 1.1" 等模式
3. **分析页面布局** - 查找大字体标题、页面顶部的独立文本
4. **按固定页数分割** - 如果无法识别章节，按每 10-15 页分割

**章节粒度目标**: 每个章节约 10-20 页，便于 AI 一次性阅读

### 步骤 3: 生成索引文件

创建 `{原文件名}-index.md` 文件，格式如下：

```markdown
# {PDF文件名} 章节索引

**总页数**: {total_pages}
**分拆章节数**: {chapter_count}
**生成时间**: {timestamp}

## 章节列表

- **01 - {章节标题}** (第 1-15 页)
  - 内容简介：{章节内容的 1-2 句话概述}

- **02 - {章节标题}** (第 16-28 页)
  - 内容简介：{章节内容的 1-2 句话概述}

...
```

### 步骤 4: 分拆 PDF 文件

使用 pypdf 按章节页码范围分拆 PDF：

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("$ARGUMENTS")

# 对每个章节
for chapter in chapters:
    writer = PdfWriter()
    for page_num in range(chapter['start'] - 1, chapter['end']):
        writer.add_page(reader.pages[page_num])

    # 输出文件名格式:
    # {原文件名}-{章节序号zfill2}-{章节名}-{起始页zfill4}-to-{结束页zfill4}.pdf
    output_name = f"{base_name}-{str(idx).zfill(2)}-{chapter_name}-{str(start).zfill(4)}-to-{str(end).zfill(4)}.pdf"

    with open(output_name, "wb") as f:
        writer.write(f)
```

## 输出文件

### 索引文件
- 文件名: `{原PDF名}-index.md`
- 位置: 与原 PDF 同目录

### 分拆后的 PDF 文件
- 文件名格式: `{原PDF名}-{序号}-{章节名}-{起始页}-to-{结束页}.pdf`
- 示例: `CS261CourseNotes-01-Introduction-0001-to-0015.pdf`
- 位置: 与原 PDF 同目录下的 `{原PDF名}-chapters/` 子目录

## 依赖库

确保以下 Python 库已安装：

```bash
pip install pypdf pdfplumber
```

## 章节内容简介生成

对于每个章节，提取前 500 字符的文本，用于生成简介。简介应该：
- 简洁明了（1-2 句话）
- 概括章节主要内容
- 包含关键术语

## 处理特殊情况

### PDF 无书签时
1. 扫描每页开头查找章节标题模式
2. 常见模式: "Chapter", "Section", "Part", "Unit", "Module", "第.*章", "第.*节"
3. 如果仍无法识别，按 15 页为单位分割

### 章节过大时
如果单个章节超过 30 页，考虑按子章节进一步分拆

### 章节名称清理
- 移除特殊字符，只保留字母、数字、中文、连字符
- 截断过长的章节名（最多 50 字符）
- 处理空格为连字符

## 补充资源

详细的 Python 脚本实现请参考 `scripts/` 目录：
- `scripts/index_pdf.py` - 索引生成脚本
- `scripts/split_pdf.py` - PDF 分拆脚本

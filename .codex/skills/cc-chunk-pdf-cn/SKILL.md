---
name: cc-chunk-pdf-cn
description: 索引和分拆大型 PDF 课程资料。当用户需要将大型 PDF 教材或课件拆分成小章节、创建章节索引、或者让 AI 更容易阅读大型 PDF 时使用此技能。支持自动识别章节结构并生成索引文件和分拆后的小 PDF 文件。
---

# PDF 索引与分拆工具

## 功能概述

此技能用于处理大型 PDF 课程资料，提供两个核心功能：

1. **生成章节索引** - 创建 `{pdf名}-index.md` 索引文件
2. **分拆 PDF 文件** - 按章节将大 PDF 拆分成多个小 PDF 文件

## 使用方法

### 输入参数

- 用户提供的参数 ($ARGUMENTS) - PDF 文件的路径（必需）

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

使用 pypdf 按章节页码范围分拆 PDF。

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
- <!-- BEGIN imported from cc-chunk-pdf-cn/index_pdf.py -->
#!/usr/bin/env python3
"""
PDF 章节索引生成脚本

功能：
- 分析 PDF 结构，识别章节
- 生成 Markdown 格式的章节索引
- 提取每个章节的内容简介

使用方法：
    python index_pdf.py <PDF文件路径> [--output <输出文件路径>]

输出：
    {原文件名}-index.md - 章节索引文件
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    print("错误: 请安装 pypdf: pip install pypdf")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("错误: 请安装 pdfplumber: pip install pdfplumber")
    sys.exit(1)


# 章节标题识别模式
CHAPTER_PATTERNS = [
    # 英文模式
    r'^Chapter\s+(\d+)',
    r'^CHAPTER\s+(\d+)',
    r'^Section\s+(\d+(?:\.\d+)*)',
    r'^Part\s+(\d+|[IVX]+)',
    r'^Unit\s+(\d+)',
    r'^Module\s+(\d+)',
    r'^Lesson\s+(\d+)',
    r'^Lecture\s+(\d+)',
    # 中文模式
    r'^第[一二三四五六七八九十百千\d]+章',
    r'^第[一二三四五六七八九十百千\d]+节',
    r'^第[一二三四五六七八九十百千\d]+部分',
    r'^第[一二三四五六七八九十百千\d]+单元',
    r'^第[一二三四五六七八九十百千\d]+课',
    # 数字开头的标题
    r'^(\d+(?:\.\d+)*)\s+[A-Z\u4e00-\u9fff]',
]


def clean_chapter_name(name: str, max_length: int = 50) -> str:
    """
    清理章节名称，使其适合用作文件名

    Args:
        name: 原始章节名称
        max_length: 最大长度限制

    Returns:
        清理后的章节名称
    """
    # 移除或替换不适合文件名的字符
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    cleaned = re.sub(r'\s+', '-', cleaned.strip())
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = cleaned.strip('-')

    # 截断过长的名称
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip('-')

    return cleaned or "untitled"


def extract_chapter_title(text: str) -> Optional[str]:
    """
    从页面文本中提取章节标题

    Args:
        text: 页面文本内容

    Returns:
        识别到的章节标题，如果没有识别到则返回 None
    """
    if not text:
        return None

    # 取前几行文本进行分析
    lines = text.strip().split('\n')[:5]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否匹配章节模式
        for pattern in CHAPTER_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE):
                # 返回整行作为标题，但限制长度
                return line[:100].strip()

    return None


def extract_page_summary(text: str, max_chars: int = 300) -> str:
    """
    提取页面内容摘要

    Args:
        text: 页面文本内容
        max_chars: 最大字符数

    Returns:
        内容摘要
    """
    if not text:
        return "（无文本内容）"

    # 清理文本
    text = re.sub(r'\s+', ' ', text).strip()

    # 跳过标题行，取正文内容
    lines = text.split('\n')
    content_lines = []
    for line in lines:
        line = line.strip()
        # 跳过可能是标题的行
        if line and not any(re.match(p, line, re.IGNORECASE) for p in CHAPTER_PATTERNS):
            content_lines.append(line)

    content = ' '.join(content_lines)

    if len(content) > max_chars:
        # 尝试在句子边界截断
        truncated = content[:max_chars]
        last_period = max(
            truncated.rfind('。'),
            truncated.rfind('.'),
            truncated.rfind('！'),
            truncated.rfind('？')
        )
        if last_period > max_chars * 0.5:
            return truncated[:last_period + 1]
        return truncated.rstrip() + "..."

    return content


def extract_outline_chapters(reader: PdfReader) -> list:
    """
    从 PDF 书签/大纲中提取章节信息

    Args:
        reader: pypdf PdfReader 对象

    Returns:
        章节列表，每个章节包含 title, page, level
    """
    chapters = []

    def process_outline_item(item, level=0):
        if isinstance(item, list):
            for sub_item in item:
                process_outline_item(sub_item, level + 1)
        else:
            try:
                # 获取书签指向的页码
                page_num = reader.get_destination_page_number(item)
                if page_num is not None:
                    chapters.append({
                        'title': item.title,
                        'page': page_num + 1,  # 转换为 1-based
                        'level': level
                    })
            except Exception:
                pass

    if reader.outline:
        process_outline_item(reader.outline)

    return chapters


def split_large_chapters(chapters: list, target_chapter_size: int) -> list:
    """
    将过大的章节进一步分割

    Args:
        chapters: 原始章节列表
        target_chapter_size: 目标章节页数

    Returns:
        分割后的章节列表
    """
    final_chapters = []
    for ch in chapters:
        chapter_size = ch['end'] - ch['start'] + 1
        # 如果章节超过目标大小的两倍，则进行分割
        if chapter_size > target_chapter_size * 2:
            num_splits = (chapter_size + target_chapter_size - 1) // target_chapter_size
            pages_per_split = chapter_size // num_splits
            
            # 确保 pages_per_split 不为 0
            if pages_per_split == 0:
                pages_per_split = 1
                num_splits = chapter_size

            for j in range(num_splits):
                split_start = ch['start'] + j * pages_per_split
                if j == num_splits - 1:
                    split_end = ch['end']
                else:
                    split_end = ch['start'] + (j + 1) * pages_per_split - 1
                
                # 再次确认 split_end 不超过 ch['end']
                split_end = min(split_end, ch['end'])
                
                if split_start > split_end:
                    continue

                final_chapters.append({
                    'title': f"{ch['title']} (Part {j + 1})",
                    'start': split_start,
                    'end': split_end,
                    'summary': ch['summary'] if j == 0 else f"继续 {ch['title']} 的内容"
                })
        else:
            final_chapters.append(ch)
    return final_chapters


def analyze_pdf_structure(pdf_path: str, target_chapter_size: int = 15) -> list:
    """
    分析 PDF 结构，识别章节

    Args:
        pdf_path: PDF 文件路径
        target_chapter_size: 目标章节页数

    Returns:
        章节列表，每个章节包含 title, start, end, summary
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    print(f"正在分析 PDF: {pdf_path}")
    print(f"总页数: {total_pages}")

    chapters = []

    # 1. 首先尝试从书签提取章节
    outline_chapters = extract_outline_chapters(reader)

    if outline_chapters:
        print(f"从书签中识别到 {len(outline_chapters)} 个书签")
        # 过滤只保留顶级或次级章节
        top_chapters = [c for c in outline_chapters if c['level'] <= 1]
        if len(top_chapters) >= 3:
            for i, ch in enumerate(top_chapters):
                next_page = top_chapters[i + 1]['page'] if i + 1 < len(top_chapters) else total_pages + 1
                chapters.append({
                    'title': ch['title'],
                    'start': ch['page'],
                    'end': next_page - 1,
                    'summary': ''
                })

            # 提取每个章节的摘要
            with pdfplumber.open(pdf_path) as pdf:
                for ch in chapters:
                    if ch['start'] - 1 < len(pdf.pages):
                        page_text = pdf.pages[ch['start'] - 1].extract_text() or ''
                        ch['summary'] = extract_page_summary(page_text)

    # 2. 如果没有识别到足够的书签，通过页面内容识别章节
    if len(chapters) < 3:
        print("书签不足，正在通过页面内容识别章节...")
        detected_chapters = []

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ''
                title = extract_chapter_title(text)

                if title:
                    detected_chapters.append({
                        'title': title,
                        'page': i + 1,
                        'text': text
                    })

        if detected_chapters:
            print(f"从内容中识别到 {len(detected_chapters)} 个章节")
            chapters = []
            for i, ch in enumerate(detected_chapters):
                next_page = detected_chapters[i + 1]['page'] if i + 1 < len(detected_chapters) else total_pages + 1
                chapters.append({
                    'title': ch['title'],
                    'start': ch['page'],
                    'end': next_page - 1,
                    'summary': extract_page_summary(ch['text'])
                })

    # 3. 如果仍然无法识别，按固定页数分割
    if not chapters:
        print(f"无法识别章节结构，按每 {target_chapter_size} 页分割...")
        with pdfplumber.open(pdf_path) as pdf:
            for start in range(0, total_pages, target_chapter_size):
                end = min(start + target_chapter_size, total_pages)

                # 尝试从第一页提取标题
                page_text = pdf.pages[start].extract_text() or ''
                lines = page_text.strip().split('\n')
                first_line = lines[0] if lines else ''
                title = first_line[:50] if first_line else f"Section {start // target_chapter_size + 1}"

                chapters.append({
                    'title': title,
                    'start': start + 1,
                    'end': end,
                    'summary': extract_page_summary(page_text)
                })

    # 最后，确保所有章节都符合大小限制
    return split_large_chapters(chapters, target_chapter_size)


def generate_index(pdf_path: str, chapters: list, output_path: Optional[str] = None) -> str:
    """
    生成章节索引 Markdown 文件

    Args:
        pdf_path: 原始 PDF 文件路径
        chapters: 章节列表
        output_path: 输出文件路径（可选）

    Returns:
        生成的索引文件路径
    """
    pdf_path = Path(pdf_path)

    if output_path:
        output_path = Path(output_path)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}-index.md"

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    # 生成 Markdown 内容
    lines = [
        f"# {pdf_path.stem} 章节索引",
        "",
        f"**原文件**: `{pdf_path.name}`",
        f"**总页数**: {total_pages}",
        f"**分拆章节数**: {len(chapters)}",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 章节列表",
        "",
    ]

    for i, ch in enumerate(chapters, 1):
        chapter_name = clean_chapter_name(ch['title'])
        page_count = ch['end'] - ch['start'] + 1

        lines.append(f"### {str(i).zfill(2)} - {ch['title']}")
        lines.append("")
        lines.append(f"- **页码范围**: 第 {ch['start']}-{ch['end']} 页 ({page_count} 页)")
        lines.append(f"- **分拆文件**: `{pdf_path.stem}-{str(i).zfill(2)}-{chapter_name}-{str(ch['start']).zfill(4)}-to-{str(ch['end']).zfill(4)}.pdf`")

        if ch.get('summary'):
            lines.append(f"- **内容简介**: {ch['summary']}")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## 使用说明",
        "",
        "1. 每个章节已被分拆成独立的 PDF 文件",
        "2. 分拆后的文件位于 `{原文件名}-chapters/` 目录下",
        "3. 文件命名格式: `{原文件名}-{序号}-{章节名}-{起始页}-to-{结束页}.pdf`",
        "4. 可以按需阅读特定章节，无需加载整个大文件",
        "",
    ])

    content = '\n'.join(lines)

    output_path.write_text(content, encoding='utf-8')
    print(f"\n索引文件已生成: {output_path}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='PDF 章节索引生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python index_pdf.py document.pdf
    python index_pdf.py document.pdf --output custom-index.md
    python index_pdf.py document.pdf --chapter-size 20
        """
    )

    parser.add_argument('pdf_path', help='PDF 文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径（默认为 {原文件名}-index.md）')
    parser.add_argument('--chapter-size', '-s', type=int, default=15,
                        help='目标章节页数（默认 15 页）')

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"错误: 文件不存在: {args.pdf_path}")
        sys.exit(1)

    # 分析 PDF 结构
    chapters = analyze_pdf_structure(args.pdf_path, args.chapter_size)

    if not chapters:
        print("错误: 无法分析 PDF 结构")
        sys.exit(1)

    # 生成索引
    generate_index(args.pdf_path, chapters, args.output)

    # 输出章节信息供后续使用
    print("\n章节列表:")
    for i, ch in enumerate(chapters, 1):
        print(f"  {i:2d}. [{ch['start']:4d}-{ch['end']:4d}] {ch['title']}")


if __name__ == '__main__':
    main()
<!-- END imported from cc-chunk-pdf-cn/index_pdf.py -->
- <!-- BEGIN imported from cc-chunk-pdf-cn/split_pdf.py -->
#!/usr/bin/env python3
"""
PDF 章节分拆脚本

功能：
- 根据章节信息将大 PDF 分拆成多个小 PDF
- 自动创建输出目录
- 生成符合命名规范的文件名

使用方法：
    python split_pdf.py <PDF文件路径> [--chapter-size <页数>]

输出：
    在原文件同目录下创建 {原文件名}-chapters/ 目录，
    包含分拆后的小 PDF 文件

依赖：
    pip install pypdf pdfplumber
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("错误: 请安装 pypdf: pip install pypdf")
    sys.exit(1)

# 导入索引脚本的功能
from index_pdf import analyze_pdf_structure, clean_chapter_name, generate_index


def split_pdf(
    pdf_path: str,
    chapters: list,
    output_dir: Optional[str] = None,
    also_generate_index: bool = True
) -> list:
    """
    按章节分拆 PDF 文件

    Args:
        pdf_path: 原始 PDF 文件路径
        chapters: 章节列表，每个章节包含 title, start, end
        output_dir: 输出目录（可选，默认为 {原文件名}-chapters/）
        also_generate_index: 是否同时生成索引文件

    Returns:
        生成的文件路径列表
    """
    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))

    # 设置输出目录
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = pdf_path.parent / f"{pdf_path.stem}-chapters"

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {output_dir}")

    generated_files = []

    for i, ch in enumerate(chapters, 1):
        # 清理章节名称用于文件名
        chapter_name = clean_chapter_name(ch['title'])

        # 生成输出文件名
        # 格式: {原文件名}-{序号zfill2}-{章节名}-{起始页zfill4}-to-{结束页zfill4}.pdf
        output_filename = (
            f"{pdf_path.stem}-"
            f"{str(i).zfill(2)}-"
            f"{chapter_name}-"
            f"{str(ch['start']).zfill(4)}-to-"
            f"{str(ch['end']).zfill(4)}.pdf"
        )
        output_path = output_dir / output_filename

        # 创建新的 PDF
        writer = PdfWriter()

        # 添加页面（注意 pypdf 页码是 0-based）
        for page_num in range(ch['start'] - 1, ch['end']):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        # 写入文件
        with open(output_path, 'wb') as f:
            writer.write(f)

        generated_files.append(str(output_path))
        page_count = ch['end'] - ch['start'] + 1
        print(f"  ✓ [{i:2d}/{len(chapters)}] {output_filename} ({page_count} 页)")

    # 生成索引文件
    if also_generate_index:
        index_path = generate_index(str(pdf_path), chapters)
        generated_files.append(index_path)

    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='PDF 章节分拆工具 - 将大 PDF 按章节拆分成多个小文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python split_pdf.py textbook.pdf
    python split_pdf.py textbook.pdf --chapter-size 20
    python split_pdf.py textbook.pdf --output ./output/chapters

输出文件命名格式:
    {原文件名}-{序号}-{章节名}-{起始页}-to-{结束页}.pdf

示例输出:
    CS261CourseNotes-01-Introduction-0001-to-0015.pdf
    CS261CourseNotes-02-Data-Structures-0016-to-0032.pdf
        """
    )

    parser.add_argument('pdf_path', help='PDF 文件路径')
    parser.add_argument('--output', '-o', help='输出目录（默认为 {原文件名}-chapters/）')
    parser.add_argument('--chapter-size', '-s', type=int, default=15,
                        help='目标章节页数（默认 15 页，用于无法自动识别章节时）')
    parser.add_argument('--no-index', action='store_true',
                        help='不生成索引文件')

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"错误: 文件不存在: {args.pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"错误: 不是 PDF 文件: {args.pdf_path}")
        sys.exit(1)

    print(f"正在处理: {pdf_path}")
    print("=" * 60)

    # 分析 PDF 结构
    chapters = analyze_pdf_structure(str(pdf_path), args.chapter_size)

    if not chapters:
        print("错误: 无法分析 PDF 结构")
        sys.exit(1)

    print(f"\n识别到 {len(chapters)} 个章节:")
    for i, ch in enumerate(chapters, 1):
        page_count = ch['end'] - ch['start'] + 1
        print(f"  {i:2d}. [{ch['start']:4d}-{ch['end']:4d}] ({page_count:3d}页) {ch['title'][:50]}")

    print("\n开始分拆 PDF...")

    # 分拆 PDF
    generated_files = split_pdf(
        str(pdf_path),
        chapters,
        args.output,
        also_generate_index=not args.no_index
    )

    print("\n" + "=" * 60)
    print(f"完成! 共生成 {len(generated_files)} 个文件")
    print(f"输出目录: {Path(generated_files[0]).parent if generated_files else 'N/A'}")


if __name__ == '__main__':
    main()
<!-- END imported from cc-chunk-pdf-cn/split_pdf.py -->

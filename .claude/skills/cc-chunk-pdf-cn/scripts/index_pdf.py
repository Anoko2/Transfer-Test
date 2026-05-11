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

    # 首先尝试从书签提取章节
    outline_chapters = extract_outline_chapters(reader)

    if outline_chapters:
        print(f"从书签中识别到 {len(outline_chapters)} 个章节")
        # 过滤只保留顶级或次级章节
        top_chapters = [c for c in outline_chapters if c['level'] <= 1]
        if len(top_chapters) >= 3:
            chapters = []
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

            return chapters

    # 如果没有书签，通过页面内容识别章节
    print("无书签，正在通过页面内容识别章节...")

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

        # 如果章节过大，可能需要进一步分割
        final_chapters = []
        for ch in chapters:
            chapter_size = ch['end'] - ch['start'] + 1
            if chapter_size > target_chapter_size * 2:
                # 章节过大，按目标大小分割
                num_splits = (chapter_size + target_chapter_size - 1) // target_chapter_size
                pages_per_split = chapter_size // num_splits

                for j in range(num_splits):
                    split_start = ch['start'] + j * pages_per_split
                    split_end = ch['start'] + (j + 1) * pages_per_split - 1 if j < num_splits - 1 else ch['end']

                    final_chapters.append({
                        'title': f"{ch['title']} (Part {j + 1})",
                        'start': split_start,
                        'end': split_end,
                        'summary': ch['summary'] if j == 0 else f"继续 {ch['title']} 的内容"
                    })
            else:
                final_chapters.append(ch)

        return final_chapters

    # 如果仍然无法识别，按固定页数分割
    print(f"无法识别章节结构，按每 {target_chapter_size} 页分割...")

    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        for start in range(0, total_pages, target_chapter_size):
            end = min(start + target_chapter_size, total_pages)

            # 尝试从第一页提取标题
            page_text = pdf.pages[start].extract_text() or ''
            first_line = page_text.strip().split('\n')[0] if page_text else ''
            title = first_line[:50] if first_line else f"Section {start // target_chapter_size + 1}"

            chapters.append({
                'title': title,
                'start': start + 1,
                'end': end,
                'summary': extract_page_summary(page_text)
            })

    return chapters


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

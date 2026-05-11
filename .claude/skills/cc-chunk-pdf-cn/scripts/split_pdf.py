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
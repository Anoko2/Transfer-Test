#!/usr/bin/env python3
"""
PDF Chapter Index Generation Script

Features:
- Analyze PDF structure and identify chapters
- Generate Markdown-formatted chapter index
- Extract content summary for each chapter

Usage:
    python index_pdf.py <PDF-file-path> [--output <output-file-path>]

Output:
    {original-filename}-index.md - Chapter index file
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
    print("Error: Please install pypdf: pip install pypdf")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("Error: Please install pdfplumber: pip install pdfplumber")
    sys.exit(1)


# Chapter title recognition patterns
CHAPTER_PATTERNS = [
    # English patterns
    r'^Chapter\s+(\d+)',
    r'^CHAPTER\s+(\d+)',
    r'^Section\s+(\d+(?:\.\d+)*)',
    r'^Part\s+(\d+|[IVX]+)',
    r'^Unit\s+(\d+)',
    r'^Module\s+(\d+)',
    r'^Lesson\s+(\d+)',
    r'^Lecture\s+(\d+)',
    # Chinese patterns
    r'^第[一二三四五六七八九十百千\d]+章',
    r'^第[一二三四五六七八九十百千\d]+节',
    r'^第[一二三四五六七八九十百千\d]+部分',
    r'^第[一二三四五六七八九十百千\d]+单元',
    r'^第[一二三四五六七八九十百千\d]+课',
    # Titles starting with numbers
    r'^(\d+(?:\.\d+)*)\s+[A-Z\u4e00-\u9fff]',
]


def clean_chapter_name(name: str, max_length: int = 50) -> str:
    """
    Clean chapter name to make it suitable for use as a filename

    Args:
        name: Original chapter name
        max_length: Maximum length limit

    Returns:
        Cleaned chapter name
    """
    # Remove or replace characters unsuitable for filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
    cleaned = re.sub(r'\s+', '-', cleaned.strip())
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = cleaned.strip('-')

    # Truncate overly long names
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip('-')

    return cleaned or "untitled"


def extract_chapter_title(text: str) -> Optional[str]:
    """
    Extract chapter title from page text

    Args:
        text: Page text content

    Returns:
        Identified chapter title, or None if not found
    """
    if not text:
        return None

    # Take the first few lines for analysis
    lines = text.strip().split('\n')[:5]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if it matches chapter patterns
        for pattern in CHAPTER_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE):
                # Return the entire line as title, but limit length
                return line[:100].strip()

    return None


def extract_page_summary(text: str, max_chars: int = 300) -> str:
    """
    Extract page content summary

    Args:
        text: Page text content
        max_chars: Maximum number of characters

    Returns:
        Content summary
    """
    if not text:
        return "(No text content)"

    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()

    # Skip title lines, take body content
    lines = text.split('\n')
    content_lines = []
    for line in lines:
        line = line.strip()
        # Skip lines that are likely titles
        if line and not any(re.match(p, line, re.IGNORECASE) for p in CHAPTER_PATTERNS):
            content_lines.append(line)

    content = ' '.join(content_lines)

    if len(content) > max_chars:
        # Try to truncate at sentence boundaries
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
    Extract chapter information from PDF bookmarks/outline

    Args:
        reader: pypdf PdfReader object

    Returns:
        Chapter list, each chapter contains title, page, level
    """
    chapters = []

    def process_outline_item(item, level=0):
        if isinstance(item, list):
            for sub_item in item:
                process_outline_item(sub_item, level + 1)
        else:
            try:
                # Get the page number the bookmark points to
                page_num = reader.get_destination_page_number(item)
                if page_num is not None:
                    chapters.append({
                        'title': item.title,
                        'page': page_num + 1,  # Convert to 1-based
                        'level': level
                    })
            except Exception:
                pass

    if reader.outline:
        process_outline_item(reader.outline)

    return chapters


def analyze_pdf_structure(pdf_path: str, target_chapter_size: int = 15) -> list:
    """
    Analyze PDF structure and identify chapters

    Args:
        pdf_path: PDF file path
        target_chapter_size: Target chapter page count

    Returns:
        Chapter list, each chapter contains title, start, end, summary
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    print(f"Analyzing PDF: {pdf_path}")
    print(f"Total pages: {total_pages}")

    # First try to extract chapters from bookmarks
    outline_chapters = extract_outline_chapters(reader)

    if outline_chapters:
        print(f"Identified {len(outline_chapters)} chapters from bookmarks")
        # Filter to keep only top-level or second-level chapters
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

            # Extract summary for each chapter
            with pdfplumber.open(pdf_path) as pdf:
                for ch in chapters:
                    if ch['start'] - 1 < len(pdf.pages):
                        page_text = pdf.pages[ch['start'] - 1].extract_text() or ''
                        ch['summary'] = extract_page_summary(page_text)

            return chapters

    # If no bookmarks, identify chapters through page content
    print("No bookmarks found, identifying chapters through page content...")

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
        print(f"Identified {len(detected_chapters)} chapters from content")
        chapters = []
        for i, ch in enumerate(detected_chapters):
            next_page = detected_chapters[i + 1]['page'] if i + 1 < len(detected_chapters) else total_pages + 1
            chapters.append({
                'title': ch['title'],
                'start': ch['page'],
                'end': next_page - 1,
                'summary': extract_page_summary(ch['text'])
            })

        # If chapters are too large, may need further splitting
        final_chapters = []
        for ch in chapters:
            chapter_size = ch['end'] - ch['start'] + 1
            if chapter_size > target_chapter_size * 2:
                # Chapter too large, split by target size
                num_splits = (chapter_size + target_chapter_size - 1) // target_chapter_size
                pages_per_split = chapter_size // num_splits

                for j in range(num_splits):
                    split_start = ch['start'] + j * pages_per_split
                    split_end = ch['start'] + (j + 1) * pages_per_split - 1 if j < num_splits - 1 else ch['end']

                    final_chapters.append({
                        'title': f"{ch['title']} (Part {j + 1})",
                        'start': split_start,
                        'end': split_end,
                        'summary': ch['summary'] if j == 0 else f"Continuation of {ch['title']}"
                    })
            else:
                final_chapters.append(ch)

        return final_chapters

    # If still unable to identify, split by fixed page count
    print(f"Unable to identify chapter structure, splitting every {target_chapter_size} pages...")

    chapters = []
    with pdfplumber.open(pdf_path) as pdf:
        for start in range(0, total_pages, target_chapter_size):
            end = min(start + target_chapter_size, total_pages)

            # Try to extract title from first page
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
    Generate chapter index Markdown file

    Args:
        pdf_path: Original PDF file path
        chapters: Chapter list
        output_path: Output file path (optional)

    Returns:
        Generated index file path
    """
    pdf_path = Path(pdf_path)

    if output_path:
        output_path = Path(output_path)
    else:
        output_path = pdf_path.parent / f"{pdf_path.stem}-index.md"

    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)

    # Generate Markdown content
    lines = [
        f"# {pdf_path.stem} Chapter Index",
        "",
        f"**Original File**: `{pdf_path.name}`",
        f"**Total Pages**: {total_pages}",
        f"**Number of Chapters**: {len(chapters)}",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Chapter List",
        "",
    ]

    for i, ch in enumerate(chapters, 1):
        chapter_name = clean_chapter_name(ch['title'])
        page_count = ch['end'] - ch['start'] + 1

        lines.append(f"### {str(i).zfill(2)} - {ch['title']}")
        lines.append("")
        lines.append(f"- **Page Range**: Pages {ch['start']}-{ch['end']} ({page_count} pages)")
        lines.append(f"- **Chunked File**: `{pdf_path.stem}-{str(i).zfill(2)}-{chapter_name}-{str(ch['start']).zfill(4)}-to-{str(ch['end']).zfill(4)}.pdf`")

        if ch.get('summary'):
            lines.append(f"- **Summary**: {ch['summary']}")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Usage Instructions",
        "",
        "1. Each chapter has been chunked into an independent PDF file",
        "2. Chunked files are located in the `{original-filename}-chapters/` directory",
        "3. File naming format: `{original-filename}-{number}-{chapter-name}-{start-page}-to-{end-page}.pdf`",
        "4. You can read specific chapters as needed without loading the entire large file",
        "",
    ])

    content = '\n'.join(lines)

    output_path.write_text(content, encoding='utf-8')
    print(f"\nIndex file generated: {output_path}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='PDF Chapter Index Generation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python index_pdf.py document.pdf
    python index_pdf.py document.pdf --output custom-index.md
    python index_pdf.py document.pdf --chapter-size 20
        """
    )

    parser.add_argument('pdf_path', help='PDF file path')
    parser.add_argument('--output', '-o', help='Output file path (default: {original-filename}-index.md)')
    parser.add_argument('--chapter-size', '-s', type=int, default=15,
                        help='Target chapter page count (default: 15 pages)')

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Analyze PDF structure
    chapters = analyze_pdf_structure(args.pdf_path, args.chapter_size)

    if not chapters:
        print("Error: Unable to analyze PDF structure")
        sys.exit(1)

    # Generate index
    generate_index(args.pdf_path, chapters, args.output)

    # Output chapter information for subsequent use
    print("\nChapter List:")
    for i, ch in enumerate(chapters, 1):
        print(f"  {i:2d}. [{ch['start']:4d}-{ch['end']:4d}] {ch['title']}")


if __name__ == '__main__':
    main()

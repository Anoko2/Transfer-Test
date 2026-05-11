---
name: cc-chunk-pdf
description: Index and chunk large PDF course materials. Use when you need to split large PDF textbooks or lecture notes into smaller chapter-based files, create chapter indexes, or make large PDFs more accessible for AI reading. Automatically identifies chapter structure and generates index files and chunked PDF files.
---

# PDF Indexing and Chunking Tool

## Feature Overview

This skill is used to process large PDF course materials, providing two core functions:

1. **Generate Chapter Index** - Create a `{pdf-name}-index.md` index file
2. **Chunk PDF Files** - Split large PDFs into multiple smaller PDF files by chapter

## Usage

### Input Parameters

- User-provided arguments ($ARGUMENTS) - Path to the PDF file (required)

### Usage Example

```
/cc-chunk-pdf references/textbooks/filename.pdf
```

## Execution Steps

### Step 1: Analyze PDF Structure

First, use pdfplumber or pypdf to read the PDF and obtain:
- Total page count
- PDF bookmarks/outline (if available)
- Title text from each page (for chapter identification)

### Step 2: Intelligent Chapter Recognition

Chapter recognition strategies (by priority):

1. **Use PDF Bookmarks** - If the PDF has bookmarks/outline, use them directly
2. **Identify Chapter Title Patterns** - Look for patterns like "Chapter 1", "Section 1.1", etc.
3. **Analyze Page Layout** - Look for large font titles, standalone text at the top of pages
4. **Split by Fixed Page Count** - If unable to identify chapters, split every 10-15 pages

**Target Chapter Granularity**: Each chapter should be approximately 10-20 pages for optimal AI readability

### Step 3: Generate Index File

Create a `{original-filename}-index.md` file with the following format:

```markdown
# {PDF Filename} Chapter Index

**Total Pages**: {total_pages}
**Number of Chapters**: {chapter_count}
**Generated**: {timestamp}

## Chapter List

- **01 - {Chapter Title}** (Pages 1-15)
  - Summary: {1-2 sentence overview of chapter content}

- **02 - {Chapter Title}** (Pages 16-28)
  - Summary: {1-2 sentence overview of chapter content}

...
```

### Step 4: Chunk PDF Files

Use pypdf to split PDF by chapter page ranges.

## Output Files

### Index File
- Filename: `{original-PDF-name}-index.md`
- Location: Same directory as the original PDF

### Chunked PDF Files
- Filename format: `{original-PDF-name}-{number}-{chapter-name}-{start-page}-to-{end-page}.pdf`
- Example: `CS261CourseNotes-01-Introduction-0001-to-0015.pdf`
- Location: `{original-PDF-name}-chapters/` subdirectory in the same directory as the original PDF

## Dependencies

Ensure the following Python libraries are installed:

```bash
pip install pypdf pdfplumber
```

## Chapter Summary Generation

For each chapter, extract the first 500 characters of text to generate a summary. The summary should:
- Be concise (1-2 sentences)
- Summarize the main content of the chapter
- Include key terms

## Handling Special Cases

### When PDF Has No Bookmarks
1. Scan the beginning of each page for chapter title patterns
2. Common patterns: "Chapter", "Section", "Part", "Unit", "Module", "Lesson", "Lecture"
3. If still unable to identify, split by 15-page units

### When Chapters Are Too Large
If a single chapter exceeds 30 pages, consider further splitting by sub-chapters

### Chapter Name Cleaning
- Remove special characters, keep only letters, numbers, and hyphens
- Truncate overly long chapter names (maximum 50 characters)
- Replace spaces with hyphens

## Additional Resources

For detailed Python script implementations, see the scripts directory:
- <!-- BEGIN imported from cc-chunk-pdf/index_pdf.py -->
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
<!-- END imported from cc-chunk-pdf/index_pdf.py -->
- <!-- BEGIN imported from cc-chunk-pdf/split_pdf.py -->
#!/usr/bin/env python3
"""
PDF Chapter Chunking Script

Features:
- Chunk large PDFs into multiple smaller PDFs based on chapter information
- Automatically create output directory
- Generate filenames following naming conventions

Usage:
    python split_pdf.py <PDF-file-path> [--chapter-size <page-count>]

Output:
    Creates {original-filename}-chapters/ directory in the same location,
    containing the chunked smaller PDF files

Dependencies:
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
    print("Error: Please install pypdf: pip install pypdf")
    sys.exit(1)

# Import functions from index script
from index_pdf import analyze_pdf_structure, clean_chapter_name, generate_index


def split_pdf(
    pdf_path: str,
    chapters: list,
    output_dir: Optional[str] = None,
    also_generate_index: bool = True
) -> list:
    """
    Chunk PDF file by chapters

    Args:
        pdf_path: Original PDF file path
        chapters: Chapter list, each chapter contains title, start, end
        output_dir: Output directory (optional, defaults to {original-filename}-chapters/)
        also_generate_index: Whether to also generate index file

    Returns:
        List of generated file paths
    """
    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))

    # Set output directory
    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = pdf_path.parent / f"{pdf_path.stem}-chapters"

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    generated_files = []

    for i, ch in enumerate(chapters, 1):
        # Clean chapter name for filename
        chapter_name = clean_chapter_name(ch['title'])

        # Generate output filename
        # Format: {original-filename}-{number-zfill2}-{chapter-name}-{start-page-zfill4}-to-{end-page-zfill4}.pdf
        output_filename = (
            f"{pdf_path.stem}-"
            f"{str(i).zfill(2)}-"
            f"{chapter_name}-"
            f"{str(ch['start']).zfill(4)}-to-"
            f"{str(ch['end']).zfill(4)}.pdf"
        )
        output_path = output_dir / output_filename

        # Create new PDF
        writer = PdfWriter()

        # Add pages (note pypdf page numbers are 0-based)
        for page_num in range(ch['start'] - 1, ch['end']):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        # Write file
        with open(output_path, 'wb') as f:
            writer.write(f)

        generated_files.append(str(output_path))
        page_count = ch['end'] - ch['start'] + 1
        print(f"  ✓ [{i:2d}/{len(chapters)}] {output_filename} ({page_count} pages)")

    # Generate index file
    if also_generate_index:
        index_path = generate_index(str(pdf_path), chapters)
        generated_files.append(index_path)

    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='PDF Chapter Chunking Tool - Split large PDFs into multiple smaller files by chapter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python split_pdf.py textbook.pdf
    python split_pdf.py textbook.pdf --chapter-size 20
    python split_pdf.py textbook.pdf --output ./output/chapters

Output file naming format:
    {original-filename}-{number}-{chapter-name}-{start-page}-to-{end-page}.pdf

Example output:
    CS261CourseNotes-01-Introduction-0001-to-0015.pdf
    CS261CourseNotes-02-Data-Structures-0016-to-0032.pdf
        """
    )

    parser.add_argument('pdf_path', help='PDF file path')
    parser.add_argument('--output', '-o', help='Output directory (default: {original-filename}-chapters/)')
    parser.add_argument('--chapter-size', '-s', type=int, default=15,
                        help='Target chapter page count (default: 15 pages, used when chapters cannot be auto-identified)')
    parser.add_argument('--no-index', action='store_true',
                        help='Do not generate index file')

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"Error: Not a PDF file: {args.pdf_path}")
        sys.exit(1)

    print(f"Processing: {pdf_path}")
    print("=" * 60)

    # Analyze PDF structure
    chapters = analyze_pdf_structure(str(pdf_path), args.chapter_size)

    if not chapters:
        print("Error: Unable to analyze PDF structure")
        sys.exit(1)

    print(f"\nIdentified {len(chapters)} chapters:")
    for i, ch in enumerate(chapters, 1):
        page_count = ch['end'] - ch['start'] + 1
        print(f"  {i:2d}. [{ch['start']:4d}-{ch['end']:4d}] ({page_count:3d} pages) {ch['title'][:50]}")

    print("\nStarting PDF chunking...")

    # Chunk PDF
    generated_files = split_pdf(
        str(pdf_path),
        chapters,
        args.output,
        also_generate_index=not args.no_index
    )

    print("\n" + "=" * 60)
    print(f"Complete! Generated {len(generated_files)} files")
    print(f"Output directory: {Path(generated_files[0]).parent if generated_files else 'N/A'}")


if __name__ == '__main__':
    main()
<!-- END imported from cc-chunk-pdf/split_pdf.py -->

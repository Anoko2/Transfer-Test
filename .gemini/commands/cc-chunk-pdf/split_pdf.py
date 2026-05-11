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

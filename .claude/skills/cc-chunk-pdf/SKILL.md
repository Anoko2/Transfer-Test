---
name: cc-chunk-pdf
description: Index and chunk large PDF course materials. Use when you need to split large PDF textbooks or lecture notes into smaller chapter-based files, create chapter indexes, or make large PDFs more accessible for AI reading. Automatically identifies chapter structure and generates index files and chunked PDF files.
argument-hint: <PDF-file-path>
---

# PDF Indexing and Chunking Tool

## Feature Overview

This skill is used to process large PDF course materials, providing two core functions:

1. **Generate Chapter Index** - Create a `{pdf-name}-index.md` index file
2. **Chunk PDF Files** - Split large PDFs into multiple smaller PDF files by chapter

## Usage

### Input Parameters

- `$ARGUMENTS` - Path to the PDF file (required)

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

```python
from pypdf import PdfReader
import pdfplumber

# Read PDF basic information
reader = PdfReader("$ARGUMENTS")
total_pages = len(reader.pages)

# Try to get bookmark outline
outline = reader.outline if reader.outline else None

# If no bookmarks, identify chapters through page content
with pdfplumber.open("$ARGUMENTS") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        # Analyze first line or large font text to find chapter titles
```

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

Use pypdf to split PDF by chapter page ranges:

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("$ARGUMENTS")

# For each chapter
for chapter in chapters:
    writer = PdfWriter()
    for page_num in range(chapter['start'] - 1, chapter['end']):
        writer.add_page(reader.pages[page_num])

    # Output filename format:
    # {original-filename}-{chapter-number-zfill2}-{chapter-name}-{start-page-zfill4}-to-{end-page-zfill4}.pdf
    output_name = f"{base_name}-{str(idx).zfill(2)}-{chapter_name}-{str(start).zfill(4)}-to-{str(end).zfill(4)}.pdf"

    with open(output_name, "wb") as f:
        writer.write(f)
```

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

For detailed Python script implementations, see the `scripts/` directory:
- `scripts/index_pdf.py` - Index generation script
- `scripts/split_pdf.py` - PDF chunking script

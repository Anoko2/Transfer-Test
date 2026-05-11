---
name: cc-extract-to-md
description: Extract text from URLs, PDFs, or any source files and convert to clean Markdown format. Extracts and formats only - never translates. Use when user wants to convert files or web pages to Markdown.
---

# Extract to Markdown

Extract text from URLs, PDFs, or any source files and convert to Markdown format.

**Critical**: Extract and format only. Never translate. Keep original language as-is.

## Usage

```
/cc-extract-to-md                           # No args, will prompt
/cc-extract-to-md file1.pdf file2.txt       # Extract specific files
/cc-extract-to-md https://example.com/page  # Extract URL content
```

## Execution Flow

### Step 1: Determine Sources

**With arguments ($ARGUMENTS)**:
- Arguments are the files or URLs to extract
- Distinguish between file paths and URLs

**Without arguments**:
- Use AskUserQuestion to ask user for file paths or URLs

### Step 2: Process Each Source

#### For Local Files (PDF, TXT, DOC, etc.):

1. **Read source file** using Read tool (PDFs are auto-parsed)

2. **Generate Markdown file**
   - Output: Create `.md` file with same name in same directory
   - Example: `/path/to/document.pdf` → `/path/to/document.md`
   - If source is already `.md`, skip or prompt user

3. **Extraction rules**:
   - **Never translate** - keep original language exactly as-is
   - Format to Markdown based on your judgment of the content structure
   - Remove headers, footers, page numbers if present
   - Use placeholders for images/figures: `[Image: description]` or `[Figure: description]`
   - Rebuild tables as Markdown tables when possible

#### For URLs:

1. **Fetch content** using WebFetch with prompt: "Extract all text content from this page, preserving structure"

2. **Determine output path** based on content type (reference directory-structure.md):
   - Course materials → appropriate subdirectory under `references/`
   - Assignments → `assignments/`
   - General resources → `references/supplementary/`
   - Filename format: `YYYY-MM-DD-title.md`

3. **Extraction rules**: Same as local files - extract and format only, never translate

### Step 3: Report Results

Report:
- Successfully extracted sources and their output paths
- Any failures with reasons

---

**Execute**: $ARGUMENTS

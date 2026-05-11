---
name: cc-find
description: Search text content in the course repository. Find textbooks, lectures, notes, assignments, emails, phone records, etc. Automatically lists files and searches by filename, extension, and content layer by layer. Use when users need to find information.
---

# Course Content Search System

Intelligently search all text content in the course repository. Supports two modes:
- **With arguments**: User describes directly, system searches immediately
- **Without arguments**: System asks what to find, gives options, or lets user input freely

## Core Capabilities

### File Discovery Logic

Search flow: **List → Filter by name → Filter by extension → Search content**

1. **List all files**: Use find/ls to list all files in target directory
2. **Filter by filename**: Check if filename contains user's keywords
3. **Categorize by extension**: Understand the 70%-30% principle
   - **70% text content** (textbooks, lectures, assignments): `.md`, `.txt`, `.pdf`, `.docx`, `.pptx`
   - **30% data/code** (code, data, emails, phone records): `.py`, `.c`, `.cpp`, `.js`, `.json`, `.csv`, `.log`, `.eml`, `.txt`
4. **Search content**: Use grep/rg to search keywords in relevant files

### PDF Handling Rules

**Do not read PDF text content directly**. Instead, tell the user:
- To extract text: Use `/cc-extract-to-md` to convert PDF to Markdown
- To translate content: Use `/cc-translate-to-${lang}` to translate to other languages

## Execution Modes

### Mode 1: With Arguments (User specifies search content)

**User input**: `/cc-find week 3 lecture` or `/cc-find hash table implementation code`

**Execution steps**:
1. Understand user query (materials, code, emails, etc.)
2. Read INDEX.md to understand directory structure and categories
3. Decide search scope based on query type:
   - Looking for materials/lectures → Search references/ first
   - Looking for code/data → Search assignments/ or references/ first
   - Looking for notes → Search notes/
   - Looking for emails/call records → Search communication/
   - Other → Global search
4. In the decided directory:
   - List all files
   - Sort by filename match relevance
   - Show top 10-15 relevant files (with file type markers)
5. If content relevance exists, use grep to search and show snippets

### Mode 2: Without Arguments (System asks user)

**User input**: `/cc-find`

**Execution steps**:

#### Step 1: Ask search type

Use AskUserQuestion to ask what the user wants to find, give 4 options + Other:

```
What type of information are you looking for?

□ 📚 Textbooks, lectures, reference materials
□ 📝 Assignments, projects, exercises
□ 💻 Code examples, program implementations
□ 📧 Emails, phone records, announcements
□ Other: Enter your own description
```

#### Step 2: Ask search scope

Based on user selection, ask whether to search in specific directory or globally:

```
Where do you want to search?

□ Specific directory (faster)
□ Global search (comprehensive)
□ Other: I want to search in [directory name]
```

#### Step 3: Ask search keywords

```
Now tell me what you're looking for.
You can use:
  • Specific names: like "hash table"
  • Time: like "week 3"
  • Topics: like "binary search tree"
  • Filename fragments: like "assignment3"
```

#### Step 4: Execute search

After user inputs keywords, execute steps 4-5 from "Mode 1".

## Search Results Display

### Format

```
================================================================================
        🔍 Search Results: [keyword] in [directory]
================================================================================

📂 Relevant Files (N total):

[1] 📄 references/lectures/week-03-hashing.md
    └─ Match: filename contains "hashing"

[2] 📘 references/readings/chapter-7-hash-tables.pdf
    └─ Match: filename contains "hash"
    └─ 💡 Tip: PDF file, use /cc-extract-to-md to extract text

[3] 💻 assignments/assignment-3-hashtable-impl.c
    └─ Match: filename and content contain related keywords
    └─ Snippet: "...implement a hash table with..."

[4] 📝 notes/2026-03-05-hash-table-notes.md
    └─ Match: content contains "hash table"
    └─ Snippet: "A hash table is a fast lookup data structure..."

================================================================================

Next steps?
  • Enter number 1-4 to view detailed content
  • Enter new search term to continue searching
  • Enter /cc-find-back to return to previous menu
  • Ask me directly about something (e.g., "tell me about this hash table implementation")
```

### File Type Markers

- `📄` = .md, .txt (text documents)
- `📘` = .pdf (PDF, needs /cc-extract-to-md)
- `📊` = .pptx, .docx (presentations/documents)
- `💻` = .py, .c, .cpp, .js (code)
- `📧` = .eml, .log (emails/logs)
- `📝` = notes-related files

## Smart Routing (Read INDEX.md)

The skill will automatically:
1. Read INDEX.md to understand directory structure
2. Parse the purpose of each directory:
   - `references/` → Course materials
   - `assignments/` → Assignments
   - `notes/` → Personal notes
   - `communication/` → Emails, phone calls
   - `study/` → Study sessions
   - `exams/` → Exam preparation
   - `team/` → Team projects
3. Intelligently recommend search scope based on user query

## Special Case Handling

### User selected a PDF file

Display:
```
📘 references/textbooks/DS-textbook.pdf

This is a PDF file. To read its content, please:

1️⃣  Extract to Markdown:
   /cc-extract-to-md references/textbooks/DS-textbook.pdf

2️⃣  Translate to another language:
   /cc-translate-to-cn references/textbooks/DS-textbook.pdf

3️⃣  Ask me questions about the PDF content:
   I can help you analyze or discuss this file, just tell me what you want to know
```

### Multiple similar results

Show top 10-15, then give filtering options:
```
Found 45 relevant files, showing top 15 here.

Would you like to:
  • See more results
  • Narrow down (enter more specific keywords)
  • Only see certain file types (code/notes/PDF etc.)
```

## Argument Handling

$ARGUMENTS

## Tips and Best Practices

1. **Filename first**: Same keywords, filename matches are usually more relevant than content matches
2. **Support fuzzy matching**: "week3" "week-3" "week 3" should all match the same files
3. **Case insensitive**: Ignore case when searching
4. **Preserve original paths**: Show full relative paths in results for easy copying
5. **Encourage follow-up questions**: After searching, user can directly ask "tell me about this file" or "explain..."

---

## Internal Tools and Methods

Use these tools to implement search:
- **Glob** - Fast file pattern matching
- **Grep** - Content search
- **Read** - Read INDEX.md and file snippets
- **AskUserQuestion** - Interactive inquiry for both modes

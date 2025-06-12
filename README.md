# Obsidian Inbox Organizer

This Python application helps organize notes from a main Markdown (`.md`) file into separate files based on predefined headers.

## Features

-   Define header-to-file mappings: Specify which notes (identified by their headers) should be moved to which target files.
-   Automatic Note Processing: Scans a main notes file, identifies notes by their headers, removes their original headers, prepends a new timestamp (`YYYY-MM-DD HH:MM:SS (auto)`), and moves them to their designated files.
-   Logging: Keeps a detailed log of all note movements, including timestamp, the *original* header, and a snippet of the note content.
-   GUI: A simple graphical user interface to manage mappings and trigger the organization process.

## How Notes are Identified

-   Notes in the main `.md` file are assumed to be separated by one or more empty lines.
-   The header of a note is determined as follows:
    -   If the first line of a note block is a date in the format `YYYY-MM-DD HH:MM:SS` (e.g., `2025-06-12 09:59:29`), then the second line is considered the header.
    -   Otherwise, the first line of the note block is considered the header.

## Configuration

The application uses a `config.json` file to store header-to-file mappings and the path to the last used main notes file. This file is automatically created and managed by the application.

Example `config.json`:
```json
{
  "mappings": [
    {
      "header": "Project Alpha Ideas",
      "target_file": "notes/project_alpha.md"
    },
    {
      "header": "Book Summaries",
      "target_file": "notes/reading/summaries.md"
    }
  ],
  "last_notes_file": "/path/to/your/main_notes.md"
}
```

## Logging

All note organization activities are logged in `organizer.log`. Each log entry includes:
-   Timestamp of the operation.
-   The header of the note that was moved.
-   The first 30 characters of the moved note's content.
-   The source file (main notes file).
-   The destination file.

Example `organizer.log` entry:
```
2025-06-12 10:30:00 | HEADER: Project Alpha Ideas | NOTE_SNIPPET: Initial thoughts on the new UI... | MOVED_FROM: main_notes.md | MOVED_TO: notes/project_alpha.md
```

## Prerequisites

-   Python 3.x
-   Tkinter (usually included with Python standard library)

## How to Run

1.  Ensure Python 3 is installed.
2.  Run the application:
    ```bash
    python note_organizer_app.py
    ```
3.  In the GUI:
    -   Specify the path to your main notes `.md` file.
    -   Add header-file mappings.
    -   Click "Organize Notes" to process your notes.

## Important Note on Data Safety

This application MODIFIES your main notes file by moving notes out of it. It is **STRONGLY RECOMMENDED** to:
1.  **Backup your main notes file** before running the organization process for the first time or when unsure.
2.  Test the application with a copy of your notes file first to ensure it behaves as expected.

---
*README.md last updated: 2025-06-12 10:59:47 (Self-generated timestamp)*
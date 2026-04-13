# ClaritySort

**ClaritySort** is a desktop application for automatic file sorting into customizable categories.  
It helps you organize folders in a few clicks: documents, images, videos, archives, and other files are distributed into folders according to user-defined rules.

> The program is displayed under the short name **Clarity** in the interface.

[Русская версия](README.md)

---

## ⚠️ Disclaimer

**Use the program consciously and at your own risk.** ClaritySort moves files according to the rules you define in the settings. The developers **do not guarantee** the absence of classification errors, operating system or hardware failures, and **assume no responsibility** for data loss, damage, or inaccessibility.

**Always back up important directories before sorting.** The application has **no** built-in backup functionality and **no** undo for completed moves.

---

## ✨ Features

- 🎯 **Flexible categories** — define file extensions and keywords (searched in filenames) for each category. Keywords take precedence.
- ⚙️ **GUI-based configuration** — add, delete, rename categories, manage keywords and extensions through a convenient settings window.
- 📦 **Large file check** — before sorting, a list of files exceeding a configurable threshold (500 MB by default) is shown. Choose to move or skip them.
- 📋 **Detailed logging** — every operation is saved to a JSON journal (`data/logs`). The main window also features a text log with copy support.
- 🌓 **Two themes** — light and dark, switchable in one click.
- 💾 **Persistent settings** — categories, theme, and safety parameters are automatically saved to `data/config.json`.
- 🔄 **Duplicate handling** — name collisions are resolved by creating numbered copies `(1)`, `(2)`, etc.
- 🖥️ **Cross-platform** — works on Windows, Linux, and macOS (Python 3 + Tkinter).

> ⚡ **Important:** if the same extension is assigned to multiple categories, the **last** match in the configuration order applies. Avoid duplicating extensions.

---

## 🌐 Interface Language

By default, the language is determined automatically: Russian on a Russian system, English otherwise.

To **force a specific language**:

1. Open `main.py`
2. Find:
   FORCE_APP_LANG = None
3. Replace with `"en"` or `"ru"`
4. Save and restart the application

Alternatively, set an environment variable:

Windows:
set CLARITY_LANG=en

Linux/macOS:
export CLARITY_LANG=en

---

## 📸 Screenshots

### Main Window
![Main Window](screenshots/main_window.png)

### Settings Window
![Settings Window](screenshots/settings_window.png)

### Large Files Dialog
![Large Files Dialog](screenshots/show_large_files_dialog.png)

---

## 🚀 Installation and Usage

### 📦 Repositories

- GitHub: https://github.com/ClaritySort/ClaritySort
- GitVerse: https://gitverse.ru/ClaritySort/ClaritySort

---

### 👨‍💻 For Developers (from source)

1. Ensure Python 3.9+ is installed

2. Clone the repository:

# GitHub
git clone https://github.com/ClaritySort/ClaritySort.git

# GitVerse
git clone https://gitverse.ru/ClaritySort/ClaritySort.git

cd ClaritySort

3. Run:

python main.py

No additional dependencies are required — only the standard library and Tkinter.

---

### 🧑‍💻 For Regular Users (Windows)

Download the ready-to-run executable **ClaritySort.exe**:  
[**Download latest version**](https://github.com/ClaritySort/ClaritySort/releases/latest/download/ClaritySort.exe)  
*(No installation required — just run the file.)*

---

## 📚 Quick Start Guide

### 1. Folder Selection

- **Source sector** — folder with files to sort
- **Destination sector** — folder where files will be moved

If the option **"Create folder inside source sector"** is enabled, a subfolder *Sorted* (or *Отсортированное*) will be created automatically.

---

### 2. Category Configuration

Click **⚙️ Settings**

You can:
- add categories
- rename them
- delete (except "Miscellaneous")

Each category has:
- **Keywords** (higher priority)
- **Extensions** (e.g. `.pdf`, `.jpg`)

---

### 3. Safety Settings

You can:
- enable/disable file size check
- set threshold (1–102400 MB)

If enabled, a dialog with large files appears before sorting.

---

### 4. Start and Stop

- Click **⚡ Start**
- Progress is shown
- **⛔ Stop**:
  - cancels scanning
  - or stops after current file

---

### 5. Logs

- Text log in main window
- Full report saved to:

data/logs/sort_YYYY-MM-DD_HH-MM-SS.json

Last **50 logs** are stored.

---

## 📁 Project Structure
```text
ClaritySort/
├── core/                     # Core logic
│   ├── config_manager.py
│   ├── localization.py
│   ├── operation_logger.py
│   ├── paths.py
│   ├── sorter_engine.py
│   └── utils.py
├── ui/                       # GUI (Tkinter)
│   ├── main_window.py
│   ├── settings_window.py
│   └── theme_styles.py
├── data/                     # User data
│   ├── config.example.json
│   └── logs/
├── screenshots/
├── packaging/
├── main.py
├── app_icon.ico
├── README.md
├── README_EN.md
├── LICENSE
└── requirements.txt
```
---

## 🔧 Building EXE (Windows)

1. Install PyInstaller:

pip install pyinstaller

2. Build:

pyinstaller --onefile --windowed --icon=app_icon.ico --add-data "data;data" --manifest packaging/app_long_paths.manifest main.py

For Linux/macOS:
- replace `;` with `:`
- remove `--manifest` if unused

Output will be in:

dist/

Recommended name:

ClaritySort.exe

---

## 📄 License

This project is licensed under the **MIT License**.  
See the `LICENSE` file for details.

---

© 2026 ClaritySort

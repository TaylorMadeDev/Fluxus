# ◈ Fluxus — Minecraft Scripting IDE

A feature-rich, dark-themed desktop IDE built for writing, managing, and running **Minescript** scripts inside Minecraft.  
Built with **PySide6** (Qt for Python) and designed as a companion tool for the [Minescript](https://minescript.net/) mod.

![Version](https://img.shields.io/badge/version-0.1-blue)
![Python](https://img.shields.io/badge/python-3.10+-brightgreen)
![Minescript](https://img.shields.io/badge/minescript-v5.0-orange)
![Framework](https://img.shields.io/badge/framework-PySide6-41cd52)

---

## Features

### Code Editor
- Full **Python syntax highlighting** — keywords, builtins, strings, numbers, comments, decorators, self, classes, and functions
- **Line number gutter** that scales with document length
- **New / Open / Save / Save As** toolbar actions
- **Modification indicator** (●) and file name display
- Cursor position tracking (Ln / Col) and encoding label
- Monospaced `Consolas 11pt` font, no word-wrap by default

### Script Browser
- Recursively discovers all `.py` and `.pyj` files in the Minescript directory
- **Live search** — filter scripts by name or path as you type
- **Sort** by Name, Modified date, or Size (ascending/descending)
- **New Script** dialog with auto-generated Minescript boilerplate
- Double-click any script to open it directly in the editor

### Script Runner
- Dropdown selector listing every script in the workspace
- **Run**, **Edit**, and **Refresh** buttons
- **Execution history** — tracks the last 50 runs with timestamps and exit codes
- Quick actions: *Run Last Script*, *Run All Tests* (`test_*.py`), *Open Scripts Folder*

### Console
- Embedded output console with **colored log levels** (info / success / warning / error)
- Runs scripts via `subprocess.Popen` in a background thread — UI never blocks
- **Thread-safe** output using Qt signals
- **Stop** button to terminate running processes
- **Command input line** for sending stdin to the running process
- Integrated into the Editor page as a vertical splitter (editor top, console bottom)
- Also available as a dedicated standalone Console page

### Packages Panel
- Lists **Block Packs** from the `blockpacks/` directory
- Lists **System Modules** from `system/lib/` and `system/exec/`
- Lists **Mappings** from `system/mappings/` with file counts
- **Open Minescript Folder** button for quick Explorer access

### Settings
- Persisted to `fluxus_settings.json` (auto-created)
- **Editor**: Font family, font size, tab size, word wrap, line numbers, highlight current line
- **Execution**: Python executable path, run-in-script-directory toggle
- **Auto-Save**: Enable/disable and interval (5–600 seconds)
- **Console**: Max output lines (100–100,000)
- Save and Reset buttons

### Custom Window Chrome
- **Frameless window** with custom top bar: logo (◈), centered title ("Fluxus | V0.1"), and window controls
- **Drag-to-move** from the title bar
- **Minimize / Maximize / Close** buttons
- **Pin (Always-on-Top)** using native Win32 `SetWindowPos` via ctypes — **zero flicker**
- SVG pin/unpin icons

### Status Bar
- Shows current page, loaded script name, run status, and app version

### Styling
- ~620 lines of **centralized QSS** dark-mode stylesheet
- **50-color palette** with dedicated syntax-highlighting tokens
- Smooth hover/press/focus transitions across every widget
- Custom scrollbars, splitter handles, combo-box dropdowns, and checkbox indicators

---

## Project Structure

```
minescript/
├── main.py                         # Entry point
├── config.txt                      # Minescript config (Python path)
├── README.md                       # This file
│
├── lib/
│   └── ui/
│       ├── __init__.py             # Exports FluxusApp
│       ├── app.py                  # Main window shell & signal wiring
│       │
│       ├── Components/
│       │   ├── __init__.py         # Component exports
│       │   ├── top_bar.py          # Custom frameless title bar
│       │   ├── sidebar.py          # Left navigation rail (6 pages)
│       │   ├── code_editor.py      # Editor + syntax highlighter + line numbers
│       │   ├── script_browser.py   # File browser with search & sort
│       │   ├── script_runner.py    # Run scripts + execution history
│       │   ├── console.py          # Output console + subprocess runner
│       │   ├── settings_panel.py   # App settings with JSON persistence
│       │   ├── packages_panel.py   # BlockPacks / modules / mappings viewer
│       │   └── status_bar.py       # Bottom status bar
│       │
│       ├── Colors/
│       │   └── palette.py          # Centralized color definitions (~50 tokens)
│       │
│       ├── Styling/
│       │   ├── stylesheet.py       # Global QSS stylesheet (~620 lines)
│       │   └── theme.py            # Window title, geometry, bar height
│       │
│       └── Icons/
│           ├── Topbar-Pin.svg      # Pin icon (white)
│           └── Topbar-Unpin.svg    # Unpin icon (white)
│
├── blockpacks/                     # Minescript block-pack data
│
└── system/
    ├── version.txt                 # Minescript version (5.0b11)
    ├── exec/                       # Built-in executable scripts
    ├── lib/                        # Core Minescript Python libraries
    ├── mappings/                   # Minecraft version mappings
    └── pyj/                        # .pyj compatibility shims
```

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.10+ |
| PySide6 | 6.x |
| Minescript mod | 5.0+ |

---

## Installation

1. **Install Python 3.10+** — [python.org](https://www.python.org/downloads/)

2. **Install PySide6**:
   ```
   pip install PySide6
   ```

3. **Install the Minescript mod** into your Minecraft instance via [Modrinth](https://modrinth.com/mod/minescript) or CurseForge.

4. **Clone or copy** this project into your Minescript profile's `minescript/` directory:
   ```
   %appdata%\ModrinthApp\profiles\<profile>\minescript\
   ```

5. **Configure Python path** in `config.txt` if needed:
   ```
   python="%userprofile%\AppData\Local\Programs\Python\Python310\python.exe"
   ```

---

## Usage

### Launch the IDE

```
cd <minescript-directory>
python main.py
```

Or from the project root:

```
py.exe .\main.py
```

### Navigation

Use the **sidebar** on the left to switch between pages:

| Icon | Page | Description |
|---|---|---|
| 📝 | **Editor** | Write and edit scripts with syntax highlighting |
| 📁 | **Scripts** | Browse, search, and sort all scripts |
| ▶ | **Runner** | Select and run scripts, view history |
| 📋 | **Console** | Standalone console output |
| 📦 | **Packages** | View installed blockpacks and modules |
| ⚙ | **Settings** | Configure editor, execution, and auto-save |

### Workflow

1. Open the **Scripts** page → double-click a script to open it in the editor
2. Edit in the **Editor** — syntax highlighting and line numbers are automatic
3. Click **Save** or use the **Runner** page to execute
4. Output appears in the **Console** panel below the editor
5. Check execution history in the **Runner** page

### Pin Window

Click the **pin icon** in the top bar to keep Fluxus always-on-top while playing Minecraft. Click again to unpin. This uses the native Win32 API for flicker-free toggling.

---

## Configuration

### `config.txt`

```
# Minescript configuration
python="%userprofile%\AppData\Local\Programs\Python\Python310\python.exe"
```

### `fluxus_settings.json` (auto-generated)

```json
{
  "python_exe": "",
  "font_size": 11,
  "font_family": "Consolas",
  "tab_size": 4,
  "word_wrap": false,
  "auto_save": true,
  "auto_save_interval": 30,
  "show_line_numbers": true,
  "highlight_current_line": true,
  "theme": "Dark (Default)",
  "console_max_lines": 5000,
  "run_in_cwd": true
}
```

---

## Color Palette

The dark theme is built around a carefully tuned palette defined in `lib/ui/Colors/palette.py`:

| Category | Examples |
|---|---|
| **Backgrounds** | `#0d0f12` root, `#161b22` topbar, `#0e1117` editor, `#0a0c10` console |
| **Text** | `#e8edf3` primary, `#c0c8d4` secondary, `#9aa6b2` muted, `#6b7685` dim |
| **Accents** | `#4da3ff` blue, `#4ade80` green, `#f0b429` warning, `#e25a5a` danger |
| **Syntax** | `#c678dd` keywords, `#98c379` strings, `#61afef` functions, `#e5c07b` classes |

---

## Architecture

```
main.py
  └── FluxusApp
        ├── QApplication (singleton)
        └── FluxusWindow (QWidget, frameless)
              ├── TopBar         — custom title bar + window controls
              ├── Sidebar        — emits page_changed(tag)
              ├── QStackedWidget — 6 pages:
              │     ├── [0] Editor page (QSplitter: CodeEditor + ConsolePanel)
              │     ├── [1] ScriptBrowser
              │     ├── [2] ScriptRunner
              │     ├── [3] ConsolePanel (standalone)
              │     ├── [4] PackagesPanel
              │     └── [5] SettingsPanel
              └── StatusBar
```

**Signal wiring** (in `app.py`):
- `Sidebar.page_changed` → switch `QStackedWidget` index + update status bar
- `ScriptBrowser.script_selected` → load file into `CodeEditor` + switch to editor page
- `ScriptRunner.run_requested` → execute in `ConsolePanel`
- `ScriptRunner.open_requested` → load file into `CodeEditor`
- `ConsolePanel.process_finished` → update `StatusBar` + add history entry

---

## License

This project is provided as-is. Minescript is developed by [minescript.net](https://minescript.net/).

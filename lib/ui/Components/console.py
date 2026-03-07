import datetime
import queue
import subprocess
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout,
)

from ..Colors.palette import COLORS


def _minescript_available() -> bool:
    """Return True when running inside Minecraft via the Minescript mod."""
    try:
        import minescript  # noqa: F401
        return True
    except Exception:
        return False


class _OutputSignals(QObject):
    append_text = Signal(str, str)  # text, color_key
    process_finished = Signal(int)


class ConsolePanel(QFrame):
    """Output console showing script execution results and logs."""

    def __init__(self, minescript_root: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ConsolePanel")
        self._minescript_root = minescript_root
        self._process: subprocess.Popen | None = None
        self._signals = _OutputSignals()
        self._signals.append_text.connect(self._do_append)
        self._signals.process_finished.connect(self._on_finished)
        self._timestamps_enabled = True
        self._filter_level = "All"
        self._log_entries: list[dict] = []  # {"text", "color_key", "level", "timestamp"}
        self._script_queue: list[str] = []
        self._repl_mode = False
        self._cmd_history: list[str] = []
        self._cmd_history_idx = -1
        self._chat_listener_started = False
        self._chat_listener_stop = threading.Event()
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame(self)
        header.setObjectName("ConsoleHeader")
        header.setFixedHeight(36)
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(12, 0, 12, 0)
        h_layout.setSpacing(8)
        header.setLayout(h_layout)

        title = QLabel("📋  Console Output")
        title.setObjectName("PanelTitle")
        h_layout.addWidget(title)
        h_layout.addStretch()

        self._status_label = QLabel("Idle")
        self._status_label.setObjectName("ConsoleStatus")
        h_layout.addWidget(self._status_label)

        # Timestamps toggle
        self._ts_btn = QPushButton("🕐")
        self._ts_btn.setObjectName("SmallButton")
        self._ts_btn.setCursor(Qt.PointingHandCursor)
        self._ts_btn.setToolTip("Toggle timestamps")
        self._ts_btn.setFixedWidth(28)
        self._ts_btn.setCheckable(True)
        self._ts_btn.setChecked(True)
        self._ts_btn.clicked.connect(lambda: setattr(self, '_timestamps_enabled', self._ts_btn.isChecked()))
        h_layout.addWidget(self._ts_btn)

        # Log level filter
        self._filter_combo = QComboBox()
        self._filter_combo.setObjectName("SortCombo")
        self._filter_combo.addItems(["All", "Info", "Success", "Warning", "Error"])
        self._filter_combo.setFixedWidth(80)
        self._filter_combo.currentTextChanged.connect(self._apply_filter)
        h_layout.addWidget(self._filter_combo)

        # Export button
        export_btn = QPushButton("📤")
        export_btn.setObjectName("SmallButton")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setToolTip("Export console to .log file")
        export_btn.setFixedWidth(28)
        export_btn.clicked.connect(self._export_log)
        h_layout.addWidget(export_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("SmallButton")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self.clear)
        h_layout.addWidget(clear_btn)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setObjectName("DangerSmallButton")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(self.stop_process)
        self._stop_btn.setEnabled(False)
        h_layout.addWidget(self._stop_btn)

        layout.addWidget(header)

        # Find bar (hidden by default)
        self._find_bar = QFrame(self)
        self._find_bar.setObjectName("ConsoleFindBar")
        self._find_bar.setFixedHeight(30)
        self._find_bar.setVisible(False)
        fb_layout = QHBoxLayout()
        fb_layout.setContentsMargins(8, 2, 8, 2)
        fb_layout.setSpacing(4)
        self._find_bar.setLayout(fb_layout)

        fb_layout.addWidget(QLabel("🔍"))
        self._find_input = QLineEdit()
        self._find_input.setObjectName("ConsoleInput")
        self._find_input.setPlaceholderText("Search output…")
        self._find_input.textChanged.connect(self._highlight_search)
        fb_layout.addWidget(self._find_input)

        find_close = QPushButton("✕")
        find_close.setObjectName("SmallButton")
        find_close.setFixedWidth(24)
        find_close.clicked.connect(lambda: self._find_bar.setVisible(False))
        fb_layout.addWidget(find_close)
        layout.addWidget(self._find_bar)

        # Output area
        self._output = QPlainTextEdit(self)
        self._output.setObjectName("ConsoleOutput")
        self._output.setReadOnly(True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._output.setFont(font)
        layout.addWidget(self._output, 1)

        # Script queue info
        self._queue_label = QLabel("")
        self._queue_label.setObjectName("ConsoleStatus")
        self._queue_label.setContentsMargins(10, 2, 10, 2)
        self._queue_label.setVisible(False)
        layout.addWidget(self._queue_label)

        # Command input
        input_bar = QFrame(self)
        input_bar.setObjectName("ConsoleInputBar")
        input_bar.setFixedHeight(34)
        ib_layout = QHBoxLayout()
        ib_layout.setContentsMargins(8, 2, 8, 4)
        ib_layout.setSpacing(6)
        input_bar.setLayout(ib_layout)

        self._prompt = QLabel("❯")
        self._prompt.setObjectName("ConsolePrompt")
        ib_layout.addWidget(self._prompt)

        self._input = QLineEdit()
        self._input.setObjectName("ConsoleInput")
        self._input.setPlaceholderText("Type command and press Enter…")
        self._input.returnPressed.connect(self._send_input)
        ib_layout.addWidget(self._input)

        # REPL toggle
        self._repl_btn = QPushButton("REPL")
        self._repl_btn.setObjectName("SmallButton")
        self._repl_btn.setCursor(Qt.PointingHandCursor)
        self._repl_btn.setToolTip("Toggle Python REPL mode")
        self._repl_btn.setCheckable(True)
        self._repl_btn.clicked.connect(self._toggle_repl)
        ib_layout.addWidget(self._repl_btn)

        layout.addWidget(input_bar)

    def toggle_find(self) -> None:
        """Show/hide the console search bar."""
        visible = not self._find_bar.isVisible()
        self._find_bar.setVisible(visible)
        if visible:
            self._find_input.setFocus()

    # --- Public API ---

    def _level_for_key(self, color_key: str) -> str:
        """Map a color_key to a log level for filtering."""
        _map = {
            "info": "Info", "success": "Success", "warning": "Warning",
            "danger": "Error", "text_secondary": "Info", "text_muted": "Info",
            "accent": "Info",
        }
        return _map.get(color_key, "Info")

    def log(self, text: str, color_key: str = "text_secondary") -> None:
        self._signals.append_text.emit(text, color_key)

    def log_info(self, text: str) -> None:
        self.log(text, "info")

    def log_success(self, text: str) -> None:
        self.log(text, "success")

    def log_warning(self, text: str) -> None:
        self.log(text, "warning")

    def log_error(self, text: str) -> None:
        self.log(text, "danger")

    def clear(self) -> None:
        self._output.clear()
        self._log_entries.clear()

    def queue_script(self, script_path: str) -> None:
        """Add a script to the execution queue."""
        self._script_queue.append(script_path)
        self._update_queue_label()
        # If nothing running, start
        if not self._process or self._process.poll() is not None:
            self._run_next_queued()

    def _run_next_queued(self) -> None:
        if self._script_queue:
            path = self._script_queue.pop(0)
            self._update_queue_label()
            self.run_script(path)

    def _update_queue_label(self) -> None:
        if self._script_queue:
            self._queue_label.setText(f"Queue: {len(self._script_queue)} script(s) pending")
            self._queue_label.setVisible(True)
        else:
            self._queue_label.setVisible(False)

    def _apply_filter(self, level: str) -> None:
        """Re-render output based on selected log level."""
        self._filter_level = level
        self._output.clear()
        for entry in self._log_entries:
            if level == "All" or entry["level"] == level:
                self._render_entry(entry)

    def _export_log(self) -> None:
        """Export console output to a .log file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Console Log", "console_output.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    for entry in self._log_entries:
                        ts = entry.get("timestamp", "")
                        level = entry.get("level", "")
                        text = entry.get("text", "")
                        f.write(f"[{ts}] [{level}] {text}\n")
            except Exception:
                pass

    def _highlight_search(self, text: str) -> None:
        """Highlight matching text in the console output."""
        from PySide6.QtWidgets import QTextEdit
        extras = []
        if text.strip():
            doc = self._output.document()
            cursor = QTextCursor(doc)
            while True:
                cursor = doc.find(text, cursor)
                if cursor.isNull():
                    break
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(QColor(COLORS.get("warning", "#f0a030")))
                sel.format.setForeground(QColor("#000000"))
                sel.cursor = cursor
                extras.append(sel)
        self._output.setExtraSelections(extras)

    def _toggle_repl(self) -> None:
        """Toggle REPL mode — runs Python expressions directly."""
        self._repl_mode = self._repl_btn.isChecked()
        if self._repl_mode:
            self._prompt.setText(">>>")
            self._input.setPlaceholderText("Python expression…")
            self.log_info("REPL mode enabled. Type Python expressions to evaluate.")
        else:
            self._prompt.setText("❯")
            self._input.setPlaceholderText("Type command and press Enter…")

    def run_script(self, script_path: str, python_exe: str | None = None,
                   execution_method: str = "minescript") -> None:
        if self._process and self._process.poll() is None:
            self.log_warning("A script is already running. Stop it first.")
            return

        # ── Minescript path: launch as a new Minescript job ─────────
        if execution_method == "minescript" and self._minescript_root:
            self._ensure_chat_listener()
            self._run_via_minescript(script_path)
            return

        # ── Fallback: plain subprocess ─────────────────────────────
        exe = python_exe or sys.executable
        self.log_info(f"▶ Running: {Path(script_path).name}")
        self._status_label.setText("Running…")
        self._stop_btn.setEnabled(True)

        def _run():
            try:
                self._process = subprocess.Popen(
                    [exe, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(Path(script_path).parent),
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
                for line in self._process.stdout:
                    self._signals.append_text.emit(line.rstrip("\n"), "text_secondary")
                self._process.wait()
                self._signals.process_finished.emit(self._process.returncode)
            except Exception as e:
                self._signals.append_text.emit(f"Error: {e}", "danger")
                self._signals.process_finished.emit(-1)

        threading.Thread(target=_run, daemon=True).start()

    # ── Minescript job launcher ────────────────────────────────────
    def _ensure_chat_listener(self) -> None:
        """Start a background chat listener once, forwarding Minecraft chat to console."""
        if self._chat_listener_started:
            return
        if not _minescript_available():
            return

        self._chat_listener_started = True
        self._chat_listener_stop.clear()

        def _listen_chat() -> None:
            try:
                import minescript

                with minescript.EventQueue() as event_queue:
                    event_queue.register_chat_listener()
                    self._signals.append_text.emit("🎧 Chat listener active (Minecraft → Console)", "text_muted")

                    while not self._chat_listener_stop.is_set():
                        try:
                            event = event_queue.get(timeout=0.5)
                        except queue.Empty:
                            continue
                        except Exception as e:
                            self._signals.append_text.emit(f"Chat listener error: {e}", "warning")
                            break

                        message = str(getattr(event, "message", "")).strip()
                        if not message:
                            continue
                        self._signals.append_text.emit(f"[MC Chat] {message}", "text_secondary")
            except Exception as e:
                self._signals.append_text.emit(f"Chat listener unavailable: {e}", "warning")
            finally:
                self._chat_listener_started = False

        threading.Thread(target=_listen_chat, daemon=True).start()

    def _run_via_minescript(self, script_path: str) -> None:
        """Launch a script as a new Minescript job via ``minescript.execute()``."""
        import minescript

        script = Path(script_path)
        root = Path(self._minescript_root)

        # Build the relative path without .py extension, using forward slashes
        try:
            rel = script.relative_to(root)
        except ValueError:
            rel = script  # absolute fallback (unlikely)

        # Strip the .py / .pyj suffix
        rel_no_ext = str(rel.with_suffix("")).replace("\\", "/")
        command = f"\\{rel_no_ext}"

        name = script.name
        self.log_info(f"⚡ Launching as Minescript job: {name}")
        self.log(f"   Command: {command}", "text_muted")
        self._status_label.setText("Minescript Job")

        try:
            minescript.execute(command)
            self.log_success(f"✓ Job started — output will appear in Minecraft chat")

            # Show current job that was just created
            try:
                jobs = minescript.job_info()
                for job in jobs:
                    cmd = getattr(job, "command", [])
                    cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
                    if rel_no_ext in cmd_str or name.replace(".py", "") in cmd_str:
                        jid = getattr(job, "job_id", "?")
                        status = getattr(job, "status", "?")
                        self.log(f"   Job #{jid}  status: {status}", "accent")
                        break
            except Exception:
                pass  # job_info might not find it immediately

        except Exception as e:
            self.log_error(f"✗ Failed to launch job: {e}")

    def stop_process(self) -> None:
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self.log_warning("⏹ Process terminated.")

    def _on_finished(self, code: int) -> None:
        if code == 0:
            self.log_success(f"✓ Finished (exit code 0)")
        else:
            self.log_error(f"✗ Finished (exit code {code})")
        self._status_label.setText("Idle")
        self._stop_btn.setEnabled(False)
        # Run next queued script
        self._run_next_queued()

    def _do_append(self, text: str, color_key: str) -> None:
        now = datetime.datetime.now()
        ts = now.strftime("%H:%M:%S")
        level = self._level_for_key(color_key)

        entry = {"text": text, "color_key": color_key, "level": level, "timestamp": ts}
        self._log_entries.append(entry)

        if self._filter_level == "All" or level == self._filter_level:
            self._render_entry(entry)

    def _render_entry(self, entry: dict) -> None:
        """Render a single log entry to the output widget."""
        color = COLORS.get(entry["color_key"], COLORS["text_secondary"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)

        if self._timestamps_enabled:
            ts_fmt = QTextCharFormat()
            ts_fmt.setForeground(QColor(COLORS.get("text_dim", "#6a6a8a")))
            cursor.insertText(f"[{entry['timestamp']}] ", ts_fmt)

        cursor.insertText(entry["text"] + "\n", fmt)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _send_input(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()

        # REPL mode: evaluate Python expressions
        if self._repl_mode:
            self.log(f">>> {text}", "accent")
            self._cmd_history.insert(0, text)
            try:
                result = eval(text)
                if result is not None:
                    self.log(repr(result), "text_secondary")
            except SyntaxError:
                try:
                    exec(text)
                except Exception as e:
                    self.log_error(f"{type(e).__name__}: {e}")
            except Exception as e:
                self.log_error(f"{type(e).__name__}: {e}")
            return

        # Normal mode
        self.log(f"❯ {text}", "accent")
        self._cmd_history.insert(0, text)
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.write(text + "\n")
                self._process.stdin.flush()
            except Exception:
                pass

    def closeEvent(self, event) -> None:
        self._chat_listener_stop.set()
        super().closeEvent(event)

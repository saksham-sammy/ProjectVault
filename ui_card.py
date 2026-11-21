import os
import subprocess
import webbrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget
)

STATUS_COLORS = {
    "Completed": "#10b981",    # Emerald
    "Needs Work": "#f59e0b",   # Amber
    "In Progress": "#06b6d4",  # Cyan
    "Pending": "#8b5cf6",      # Violet
    "Idea": "#ec4899"          # Pink
}


class ProjectCard(QFrame):
    def __init__(self, project: dict, on_edit_callback=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.on_edit = on_edit_callback
        self.setObjectName("ProjectCard")
        self._init_ui()

    def _init_ui(self):
        status = self.project.get("status", "In Progress")
        color = STATUS_COLORS.get(status, "#06b6d4")

        self.setStyleSheet(f"""
            QFrame#ProjectCard {{
                background-color: #121824;
                border: 1px solid #1f293d;
                border-radius: 10px;
                padding: 14px;
            }}
            QFrame#ProjectCard:hover {{
                border: 1px solid {color};
                background-color: #151c2a;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Top Row: Title + Status Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        title_lbl = QLabel(self.project.get("name", ""))
        title_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #ffffff;")
        top_row.addWidget(title_lbl)

        top_row.addStretch()

        status_badge = QLabel(f"● {status}")
        status_badge.setStyleSheet(
            f"background-color: #0d121c; color: {color}; font-size: 11px; "
            f"font-weight: bold; padding: 4px 10px; border-radius: 12px; border: 1px solid {color};"
        )
        top_row.addWidget(status_badge)

        layout.addLayout(top_row)

        # 2. Description
        desc_text = self.project.get("description", "")
        if desc_text:
            desc_lbl = QLabel(desc_text)
            desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        # 3. Progress Bar Row
        prog_row = QHBoxLayout()
        prog_row.setSpacing(10)

        prog_val = int(self.project.get("progress_pct", 50))
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(prog_val)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #0b0e14;
                border: 1px solid #1f293d;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        prog_row.addWidget(bar, 1)

        pct_lbl = QLabel(f"<b>{prog_val}%</b>")
        pct_lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        prog_row.addWidget(pct_lbl)

        layout.addLayout(prog_row)

        # 4. Tech Stack Tags + Git info
        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        for t in self.project.get("tech_stack", [])[:4]:
            tag = QLabel(t)
            tag.setStyleSheet("background-color: #0d121c; color: #38bdf8; font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid #1e293d;")
            meta_row.addWidget(tag)

        meta_row.addStretch()

        last_commit = self.project.get("last_commit_date") or self.project.get("last_modified") or ""
        if last_commit:
            date_lbl = QLabel(f"📅 {last_commit}")
            date_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            meta_row.addWidget(date_lbl)

        layout.addLayout(meta_row)

        # 5. Actions Row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        vscode_btn = QPushButton("💻 VS Code")
        vscode_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2e3b52; }
        """)
        vscode_btn.clicked.connect(self._open_in_vscode)
        action_row.addWidget(vscode_btn)

        folder_btn = QPushButton("📁 Folder")
        folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #2e3b52; }
        """)
        folder_btn.clicked.connect(self._open_in_explorer)
        action_row.addWidget(folder_btn)

        edit_btn = QPushButton("📝 Edit Status & Todos")
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1e293b;
                color: {color};
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #2e3b52; }}
        """)
        edit_btn.clicked.connect(lambda: self.on_edit(self.project) if self.on_edit else None)
        action_row.addWidget(edit_btn)

        if self.project.get("git_remote"):
            gh_btn = QPushButton("🌐 GitHub")
            gh_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #cbd5e1;
                    border: 1px solid #334155;
                    border-radius: 5px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #2e3b52; }
            """)
            gh_btn.clicked.connect(self._open_github)
            action_row.addWidget(gh_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

    def _open_in_vscode(self):
        try:
            subprocess.Popen(["code", self.project["path"]], shell=True)
        except Exception:
            pass

    def _open_in_explorer(self):
        try:
            os.startfile(self.project["path"])
        except Exception:
            pass

    def _open_github(self):
        rem = self.project.get("git_remote", "")
        if rem:
            if rem.endswith(".git"):
                rem = rem[:-4]
            webbrowser.open(rem)

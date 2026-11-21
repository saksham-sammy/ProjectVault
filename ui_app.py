import os
import subprocess
import sys
import webbrowser

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QSlider, QSplitter, QSystemTrayIcon, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from paths import APP_ICON_ICO, APP_LOGO_PNG, DEFAULT_PROJECTS_DIR
from project_scanner import ProjectScanner

STATUS_COLORS = {
    "Completed": "#10b981",    # Emerald
    "In Progress": "#06b6d4",  # Cyan
    "Needs Work": "#f59e0b",   # Amber
    "Pending": "#8b5cf6",      # Purple
    "Idea": "#a855f7"          # Violet
}

PRIORITY_COLORS = {
    "High": "#ef4444",
    "Medium": "#f59e0b",
    "Low": "#10b981"
}

STYLESHEET = """
QMainWindow {
    background-color: #0b0e14;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, sans-serif;
}
QWidget {
    color: #cbd5e1;
    font-size: 13px;
}
QFrame#MetricCard {
    background-color: #121824;
    border: 1px solid #1f293d;
    border-radius: 10px;
    padding: 8px 14px;
}
QFrame#MetricCard:hover {
    border: 1px solid #8b5cf6;
}
QLabel#MetricValue {
    font-size: 18px;
    font-weight: bold;
    color: #8b5cf6;
}
QLabel#MetricLabel {
    font-size: 10px;
    color: #94a3b8;
    font-weight: 600;
    text-transform: uppercase;
}
QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6d28d9);
    color: #ffffff;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 7px 15px;
    font-size: 12px;
}
QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #8b5cf6);
}
QPushButton#ActionBtn {
    background-color: #1e293b;
    color: #e2e8f0;
    font-weight: 600;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#ActionBtn:hover {
    background-color: #334155;
    border-color: #8b5cf6;
    color: #ffffff;
}
QPushButton#SecondaryBtn {
    background-color: #1a2233;
    color: #e2e8f0;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton#SecondaryBtn:hover {
    background-color: #242f45;
}
QLineEdit, QComboBox {
    background-color: #121824;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #8b5cf6;
}
QTableWidget {
    background-color: #0d111a;
    border: 1px solid #1f293d;
    border-radius: 8px;
    gridline-color: #1f293d;
    color: #e2e8f0;
}
QHeaderView::section {
    background-color: #161f30;
    color: #94a3b8;
    font-weight: bold;
    border: 1px solid #1f293d;
    padding: 6px;
}
QProgressBar {
    background-color: #1a2233;
    border-radius: 4px;
    border: 1px solid #2d3748;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: bold;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #06b6d4);
    border-radius: 3px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #0b0e14;
    width: 8px;
}
QScrollBar::handle:vertical {
    background: #1f293d;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #8b5cf6;
}
"""


class ProjectVaultApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scanner = ProjectScanner(DEFAULT_PROJECTS_DIR)
        self.all_projects = []
        self.current_filter = "all"
        self.search_query = ""
        self.sort_mode = "progress"
        self.selected_project = None

        self.setWindowTitle("ProjectVault · Visual Portfolio & Project Lifecycle Hub")
        self.resize(1240, 880)
        self.setStyleSheet(STYLESHEET)

        icon = self._make_app_icon()
        self.setWindowIcon(icon)
        self._setup_tray(icon)
        self._init_ui()

        # Immediate synchronous scan
        self.refresh_projects()

    def _make_app_icon(self) -> QIcon:
        if os.path.isfile(APP_ICON_ICO):
            return QIcon(APP_ICON_ICO)
        if os.path.isfile(APP_LOGO_PNG):
            return QIcon(APP_LOGO_PNG)
        pix = QPixmap(32, 32)
        pix.fill(QColor(139, 92, 246))
        return QIcon(pix)

    def _setup_tray(self, icon: QIcon):
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("ProjectVault · Visual Project Hub")
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        open_action = QAction("Open ProjectVault", self)
        open_action.triggered.connect(self.show_and_activate)
        menu.addAction(open_action)

        menu.addSeparator()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # ── 1. Top Bar ─────────────────────────────────────────────
        top_bar = QHBoxLayout()

        logo_lbl = QLabel()
        if os.path.isfile(APP_LOGO_PNG):
            pix = QPixmap(APP_LOGO_PNG).scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        top_bar.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        t_lbl = QLabel("ProjectVault")
        t_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        s_lbl = QLabel("Visual Project Management, Completion Progress & Lifecycle Dashboard · Saksham Sharma")
        s_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(t_lbl)
        title_box.addWidget(s_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.btn_rescan = QPushButton("↻ Rescan Repos")
        self.btn_rescan.setObjectName("PrimaryBtn")
        self.btn_rescan.clicked.connect(self.refresh_projects)
        top_bar.addWidget(self.btn_rescan)

        root.addLayout(top_bar)

        # ── 2. Metric Cards ────────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        self.card_total_val, card_total = self._create_metric_card("Total Projects", "0 Repos", "#8b5cf6")
        self.card_comp_val, card_comp = self._create_metric_card("Completed", "0 Shipped", "#10b981")
        self.card_prog_val, card_prog = self._create_metric_card("In Progress", "0 Active", "#06b6d4")
        self.card_work_val, card_work = self._create_metric_card("Needs Work", "0 Polishing", "#f59e0b")

        cards_layout.addWidget(card_total)
        cards_layout.addWidget(card_comp)
        cards_layout.addWidget(card_prog)
        cards_layout.addWidget(card_work)
        root.addLayout(cards_layout)

        # ── 3. Filter Bar & Search ─────────────────────────────────
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self.tab_all = QPushButton("All Projects")
        self.tab_all.setObjectName("SecondaryBtn")
        self.tab_all.clicked.connect(lambda: self._set_filter("all", self.tab_all))
        filter_bar.addWidget(self.tab_all)

        self.tab_comp = QPushButton("🟢 Completed")
        self.tab_comp.setObjectName("SecondaryBtn")
        self.tab_comp.clicked.connect(lambda: self._set_filter("Completed", self.tab_comp))
        filter_bar.addWidget(self.tab_comp)

        self.tab_prog = QPushButton("🔵 In Progress")
        self.tab_prog.setObjectName("SecondaryBtn")
        self.tab_prog.clicked.connect(lambda: self._set_filter("In Progress", self.tab_prog))
        filter_bar.addWidget(self.tab_prog)

        self.tab_work = QPushButton("🟠 Needs Work")
        self.tab_work.setObjectName("SecondaryBtn")
        self.tab_work.clicked.connect(lambda: self._set_filter("Needs Work", self.tab_work))
        filter_bar.addWidget(self.tab_work)

        self.tab_pending = QPushButton("🟣 Ideas / Concept")
        self.tab_pending.setObjectName("SecondaryBtn")
        self.tab_pending.clicked.connect(lambda: self._set_filter("Pending", self.tab_pending))
        filter_bar.addWidget(self.tab_pending)

        filter_bar.addStretch()

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Sort by Progress %", "progress")
        self.sort_combo.addItem("Sort by Name (A-Z)", "name")
        self.sort_combo.addItem("Sort by Recently Modified", "date")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        filter_bar.addWidget(self.sort_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search project name or tech...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(self.search_input)

        root.addLayout(filter_bar)
        self._highlight_tab(self.tab_all)

        # ── 4. Splitter Master-Detail Layout ───────────────────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(8)

        # Left Column: Compact Projects Table (390px)
        left_box = QWidget()
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(3)
        self.projects_table.setHorizontalHeaderLabels(["Project Name", "Status", "Progress"])
        self.projects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.projects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.projects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.projects_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.projects_table.setSelectionMode(QTableWidget.SingleSelection)
        self.projects_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        left_lay.addWidget(self.projects_table)

        self.splitter.addWidget(left_box)

        # Right Column: Project Control Center Inspector in ScrollArea
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_widget = QWidget()
        self.detail_lay = QVBoxLayout(self.detail_widget)
        self.detail_lay.setContentsMargins(8, 0, 8, 8)
        self.detail_lay.setSpacing(12)
        right_scroll.setWidget(self.detail_widget)

        self.splitter.addWidget(right_scroll)
        self.splitter.setSizes([400, 780])

        root.addWidget(self.splitter, 1)

    def _create_metric_card(self, label: str, default_val: str, color_hex: str):
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setObjectName("MetricLabel")
        val = QLabel(default_val)
        val.setObjectName("MetricValue")
        val.setStyleSheet(f"color: {color_hex}; font-size: 18px; font-weight: bold;")

        layout.addWidget(lbl)
        layout.addWidget(val)
        return val, card

    def _set_filter(self, filter_name: str, btn: QPushButton):
        self.current_filter = filter_name
        for b in (self.tab_all, self.tab_comp, self.tab_prog, self.tab_work, self.tab_pending):
            b.setStyleSheet("")
        self._highlight_tab(btn)
        self._render_table()

    def _highlight_tab(self, btn: QPushButton):
        btn.setStyleSheet("background-color: #8b5cf6; color: #ffffff; font-weight: bold;")

    def _on_search_changed(self, text: str):
        self.search_query = text.strip().lower()
        self._render_table()

    def _on_sort_changed(self):
        self.sort_mode = self.sort_combo.currentData()
        self._render_table()

    def refresh_projects(self):
        projects = self.scanner.scan_all_projects()
        self.all_projects = projects

        total = len(projects)
        comp = sum(1 for p in projects if p.get("status") == "Completed")
        prog = sum(1 for p in projects if p.get("status") == "In Progress")
        work = sum(1 for p in projects if p.get("status") == "Needs Work")

        self.card_total_val.setText(f"{total} Repos")
        self.card_comp_val.setText(f"{comp} Shipped")
        self.card_prog_val.setText(f"{prog} Active")
        self.card_work_val.setText(f"{work} Polishing")

        if self.all_projects and not self.selected_project:
            self.selected_project = self.all_projects[0]

        self._render_table()
        self._render_detail_pane()

    def _get_filtered_projects(self):
        filtered = []
        for p in self.all_projects:
            st = p.get("status", "")
            if self.current_filter == "Completed" and st != "Completed":
                continue
            if self.current_filter == "In Progress" and st != "In Progress":
                continue
            if self.current_filter == "Needs Work" and st != "Needs Work":
                continue
            if self.current_filter == "Pending" and st not in ("Pending", "Idea"):
                continue

            if self.search_query:
                n = p.get("name", "").lower()
                desc = p.get("description", "").lower()
                stack_str = " ".join(p.get("tech_stack", [])).lower()
                if self.search_query not in n and self.search_query not in desc and self.search_query not in stack_str:
                    continue

            filtered.append(p)

        if self.sort_mode == "progress":
            filtered.sort(key=lambda x: x.get("progress_pct", 0), reverse=True)
        elif self.sort_mode == "name":
            filtered.sort(key=lambda x: x.get("name", "").lower())
        elif self.sort_mode == "date":
            filtered.sort(key=lambda x: x.get("last_commit_date") or x.get("last_modified") or "", reverse=True)

        return filtered

    def _render_table(self):
        self.projects_table.blockSignals(True)
        filtered = self._get_filtered_projects()
        self.projects_table.setRowCount(len(filtered))

        select_row = 0
        for row, p in enumerate(filtered):
            # 0: Name
            name_item = QTableWidgetItem(p.get("name", ""))
            name_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.projects_table.setItem(row, 0, name_item)

            # 1: Status
            st = p.get("status", "In Progress")
            st_color = STATUS_COLORS.get(st, "#8b5cf6")
            st_item = QTableWidgetItem(f"● {st}")
            st_item.setForeground(QColor(st_color))
            self.projects_table.setItem(row, 1, st_item)

            # 2: Progress %
            pct = int(p.get("progress_pct", 0))
            prog_item = QTableWidgetItem(f"{pct}%")
            self.projects_table.setItem(row, 2, prog_item)

            if self.selected_project and p.get("folder_name") == self.selected_project.get("folder_name"):
                select_row = row

        self.projects_table.blockSignals(False)
        if len(filtered) > 0:
            self.projects_table.selectRow(select_row)

    def _on_table_selection_changed(self):
        row = self.projects_table.currentRow()
        filtered = self._get_filtered_projects()
        if 0 <= row < len(filtered):
            self.selected_project = filtered[row]
            self._render_detail_pane()

    def _render_detail_pane(self):
        while self.detail_lay.count() > 0:
            child = self.detail_lay.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    sub = child.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        p = self.selected_project
        if not p:
            placeholder = QLabel("Select a project from the left list to view control center.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #64748b; font-size: 15px; padding: 40px;")
            self.detail_lay.addWidget(placeholder)
            return

        folder_name = p.get("folder_name", p.get("name", ""))
        st = p.get("status", "In Progress")
        st_color = STATUS_COLORS.get(st, "#8b5cf6")
        prio = p.get("priority", "Medium")
        prio_color = PRIORITY_COLORS.get(prio, "#f59e0b")

        # ═════════════════════════════════════════════════════════════
        # CARD 1: Executive Header & Action Launch Hub
        # ═════════════════════════════════════════════════════════════
        hdr_card = QFrame()
        hdr_card.setStyleSheet("""
            QFrame {
                background-color: #121824;
                border: 1px solid #1f293d;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        h_lay = QVBoxLayout(hdr_card)
        h_lay.setSpacing(12)

        # Top row: Status, Priority & Title
        title_row = QHBoxLayout()
        title_v = QVBoxLayout()
        title_v.setSpacing(4)

        badges_h = QHBoxLayout()
        badges_h.setSpacing(8)

        status_pill = QLabel(f"● {st.upper()}")
        status_pill.setStyleSheet(f"background-color: #0b1329; color: {st_color}; font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid {st_color}44;")
        badges_h.addWidget(status_pill)

        prio_pill = QLabel(f"PRIORITY: {prio.upper()}")
        prio_pill.setStyleSheet(f"background-color: #0b1329; color: {prio_color}; font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid {prio_color}44;")
        badges_h.addWidget(prio_pill)

        if p.get("is_git"):
            git_pill = QLabel(f"🌿 {p.get('git_branch', 'main')}")
            git_pill.setStyleSheet("background-color: #0b1329; color: #38bdf8; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px; border: 1px solid #38bdf844;")
            badges_h.addWidget(git_pill)

        badges_h.addStretch()
        title_v.addLayout(badges_h)

        title_lbl = QLabel(p.get("name", ""))
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        title_v.addWidget(title_lbl)

        # Path bar with copy button
        path_box = QHBoxLayout()
        path_box.setSpacing(6)
        path_lbl = QLabel(p.get("path", ""))
        path_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-family: Consolas;")
        path_box.addWidget(path_lbl, 1)

        copy_path_btn = QPushButton("📋 Copy Path")
        copy_path_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a2233; color: #94a3b8; border: 1px solid #2d3748;
                border-radius: 4px; padding: 2px 8px; font-size: 11px;
            }
            QPushButton:hover { color: #ffffff; border-color: #8b5cf6; }
        """)
        copy_path_btn.clicked.connect(lambda: (QApplication.clipboard().setText(p.get("path", "")), copy_path_btn.setText("✔ Copied!")))
        path_box.addWidget(copy_path_btn)
        title_v.addLayout(path_box)

        title_row.addLayout(title_v, 1)

        # Quick Actions Grid/Box
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        vs_btn = QPushButton("💻 VS Code")
        vs_btn.setObjectName("PrimaryBtn")
        vs_btn.clicked.connect(lambda: self._open_vscode(p.get("path")))
        btn_box.addWidget(vs_btn)

        dir_btn = QPushButton("📂 Folder")
        dir_btn.setObjectName("ActionBtn")
        dir_btn.clicked.connect(lambda: os.startfile(p.get("path")))
        btn_box.addWidget(dir_btn)

        term_btn = QPushButton("⚡ Terminal")
        term_btn.setObjectName("ActionBtn")
        term_btn.clicked.connect(lambda: self._open_terminal(p.get("path")))
        btn_box.addWidget(term_btn)

        run_btn = QPushButton("🚀 Run App")
        run_btn.setObjectName("ActionBtn")
        run_btn.clicked.connect(lambda: self._try_run_project(p.get("path")))
        btn_box.addWidget(run_btn)

        dl_btn = QPushButton("📦 Download ZIP")
        dl_btn.setObjectName("ActionBtn")
        dl_btn.clicked.connect(lambda: self._download_project_zip(p.get("path"), p.get("name")))
        btn_box.addWidget(dl_btn)

        if p.get("git_remote"):
            gh_btn = QPushButton("🌐 GitHub")
            gh_btn.setObjectName("ActionBtn")
            gh_btn.clicked.connect(lambda: self._open_github(p.get("git_remote")))
            btn_box.addWidget(gh_btn)

        title_row.addLayout(btn_box)
        h_lay.addLayout(title_row)
        self.detail_lay.addWidget(hdr_card)

        # ═════════════════════════════════════════════════════════════
        # CARD 2: Lifecycle & Git Insights (Balanced 2-Column Grid)
        # ═════════════════════════════════════════════════════════════
        grid_row = QHBoxLayout()
        grid_row.setSpacing(12)

        # Left Column: Lifecycle & Completion
        lifecycle_box = QFrame()
        lifecycle_box.setStyleSheet("background-color: #121824; border: 1px solid #1f293d; border-radius: 12px; padding: 14px;")
        l_lay = QVBoxLayout(lifecycle_box)
        l_lay.setSpacing(10)

        l_head = QLabel("🎯 Lifecycle Status & Progress")
        l_head.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        l_lay.addWidget(l_head)

        # Selectors row
        sel_row = QHBoxLayout()
        sel_row.setSpacing(10)

        st_col = QVBoxLayout()
        st_col.setSpacing(3)
        st_col.addWidget(QLabel("Status:"))
        combo_status = QComboBox()
        for s in ("Completed", "In Progress", "Needs Work", "Pending", "Idea"):
            combo_status.addItem(s)
        combo_status.setCurrentText(st)
        st_col.addWidget(combo_status)
        sel_row.addLayout(st_col, 1)

        prio_col = QVBoxLayout()
        prio_col.setSpacing(3)
        prio_col.addWidget(QLabel("Priority:"))
        combo_prio = QComboBox()
        for pr in ("High", "Medium", "Low"):
            combo_prio.addItem(pr)
        combo_prio.setCurrentText(prio)
        prio_col.addWidget(combo_prio)
        sel_row.addLayout(prio_col, 1)

        l_lay.addLayout(sel_row)

        # Progress slider & bar
        pct = int(p.get("progress_pct", 50))
        pct_lbl = QLabel(f"Completion: {pct}%")
        pct_lbl.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 13px;")
        l_lay.addWidget(pct_lbl)

        p_bar = QProgressBar()
        p_bar.setRange(0, 100)
        p_bar.setValue(pct)
        p_bar.setFixedHeight(12)
        p_bar.setTextVisible(False)
        l_lay.addWidget(p_bar)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(pct)
        slider.valueChanged.connect(lambda v: (pct_lbl.setText(f"Completion: {v}%"), p_bar.setValue(v)))
        l_lay.addWidget(slider)

        save_meta_btn = QPushButton("💾 Save Lifecycle Changes")
        save_meta_btn.setObjectName("PrimaryBtn")
        save_meta_btn.clicked.connect(lambda: self._save_meta_changes(p, combo_status.currentText(), combo_prio.currentText(), slider.value(), save_meta_btn))
        l_lay.addWidget(save_meta_btn)

        grid_row.addWidget(lifecycle_box, 1)

        # Right Column: Git & Version Control Analytics
        git_box = QFrame()
        git_box.setStyleSheet("background-color: #121824; border: 1px solid #1f293d; border-radius: 12px; padding: 14px;")
        g_lay = QVBoxLayout(git_box)
        g_lay.setSpacing(8)

        g_head = QLabel("🌿 Git & Workspace Telemetry")
        g_head.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        g_lay.addWidget(g_head)

        def make_kv(k, v):
            row = QHBoxLayout()
            row.setSpacing(6)
            k_lbl = QLabel(k)
            k_lbl.setStyleSheet("color: #64748b; font-size: 12px; min-width: 100px;")
            v_lbl = QLabel(v or "—")
            v_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 500;")
            v_lbl.setWordWrap(True)
            row.addWidget(k_lbl)
            row.addWidget(v_lbl, 1)
            return row

        branch = p.get("git_branch", "None (No Git)")
        g_lay.addLayout(make_kv("Active Branch:", branch))

        last_date = p.get("last_commit_date") or p.get("last_modified") or "Unknown"
        g_lay.addLayout(make_kv("Last Commit:", last_date))

        commit_msg = p.get("last_commit_msg", "Working tree modifications")
        g_lay.addLayout(make_kv("Commit Msg:", commit_msg[:60] + ("..." if len(commit_msg) > 60 else "")))

        remote_url = p.get("git_remote", "")
        clean_remote = remote_url.split("/")[-1] if "/" in remote_url else (remote_url or "Local workspace only")
        g_lay.addLayout(make_kv("Origin Remote:", clean_remote))

        last_mod = p.get("last_modified", "Recent")
        g_lay.addLayout(make_kv("File Modified:", last_mod))

        g_lay.addStretch()
        grid_row.addWidget(git_box, 1)

        self.detail_lay.addLayout(grid_row)

        # ═════════════════════════════════════════════════════════════
        # CARD 3: Tech Stack & Architecture Overview
        # ═════════════════════════════════════════════════════════════
        tech_card = QFrame()
        tech_card.setStyleSheet("background-color: #121824; border: 1px solid #1f293d; border-radius: 12px; padding: 14px;")
        t_lay = QVBoxLayout(tech_card)
        t_lay.setSpacing(10)

        t_head = QLabel("🛠 Detected Tech Stack & Project Overview")
        t_head.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        t_lay.addWidget(t_head)

        # Chips row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        for tech in p.get("tech_stack", []):
            chip = QLabel(tech)
            chip.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: 600; font-size: 12px; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155;")
            chips_row.addWidget(chip)
        chips_row.addStretch()
        t_lay.addLayout(chips_row)

        # Description block
        desc_text = p.get("description", "A local software development project.")
        desc_box = QFrame()
        desc_box.setStyleSheet("background-color: #0b111e; border: 1px solid #1e293d; border-radius: 8px; padding: 10px 12px;")
        db_lay = QVBoxLayout(desc_box)
        db_lay.setContentsMargins(4, 4, 4, 4)
        desc_lbl = QLabel(desc_text)
        desc_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        desc_lbl.setWordWrap(True)
        db_lay.addWidget(desc_lbl)
        t_lay.addWidget(desc_box)

        self.detail_lay.addWidget(tech_card)

        # ═════════════════════════════════════════════════════════════
        # CARD 4: Interactive Project Milestones & Checklist
        # ═════════════════════════════════════════════════════════════
        todo_card = QFrame()
        todo_card.setStyleSheet("background-color: #121824; border: 1px solid #1f293d; border-radius: 12px; padding: 14px;")
        td_lay = QVBoxLayout(todo_card)
        td_lay.setSpacing(8)

        td_head = QLabel("🗺 Actionable Roadmap & Milestones")
        td_head.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        td_lay.addWidget(td_head)

        todos = p.get("todos", [])
        for idx, item in enumerate(todos):
            cb = QCheckBox(item.get("text", ""))
            cb.setChecked(item.get("done", False))
            cb.setStyleSheet("color: #e2e8f0; font-size: 13px;")
            cb.toggled.connect(lambda chk, i=idx: self._toggle_todo(p, i, chk))
            td_lay.addWidget(cb)

        # Add task input
        add_task_row = QHBoxLayout()
        add_task_row.setSpacing(8)
        new_task_input = QLineEdit()
        new_task_input.setPlaceholderText("➕ Add new milestone or next step...")
        add_task_row.addWidget(new_task_input, 1)

        add_task_btn = QPushButton("Add Milestone")
        add_task_btn.setObjectName("SecondaryBtn")
        add_task_btn.clicked.connect(lambda: self._add_todo(p, new_task_input.text().strip(), new_task_input))
        add_task_row.addWidget(add_task_btn)
        td_lay.addLayout(add_task_row)

        self.detail_lay.addWidget(todo_card)

        # ═════════════════════════════════════════════════════════════
        # CARD 5: Developer Notes & Next Milestones
        # ═════════════════════════════════════════════════════════════
        notes_card = QFrame()
        notes_card.setStyleSheet("background-color: #121824; border: 1px solid #1f293d; border-radius: 12px; padding: 14px;")
        n_lay = QVBoxLayout(notes_card)
        n_lay.setSpacing(8)

        n_head = QLabel("📝 Developer Notes & Engineering Journal")
        n_head.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        n_lay.addWidget(n_head)

        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Write project notes, ideas, edge cases to fix, or next architecture steps...")
        notes_edit.setText(p.get("notes", ""))
        notes_edit.setFixedHeight(110)
        notes_edit.setStyleSheet("background-color: #0b111e; border: 1px solid #1f293d; border-radius: 8px; color: #f1f5f9; padding: 8px;")
        n_lay.addWidget(notes_edit)

        save_notes_row = QHBoxLayout()
        save_notes_btn = QPushButton("💾 Save Developer Notes")
        save_notes_btn.setObjectName("PrimaryBtn")
        save_notes_btn.setFixedWidth(180)
        save_notes_btn.clicked.connect(lambda: self._save_notes(p, notes_edit.toPlainText(), save_notes_btn))
        save_notes_row.addWidget(save_notes_btn)
        save_notes_row.addStretch()
        n_lay.addLayout(save_notes_row)

        self.detail_lay.addWidget(notes_card)

    def _open_vscode(self, project_path: str):
        try:
            subprocess.Popen(f'code "{project_path}"', shell=True)
        except Exception as e:
            QMessageBox.warning(self, "VS Code", f"Failed to launch VS Code: {e}")

    def _open_terminal(self, project_path: str):
        try:
            subprocess.Popen(f'cmd /c start wt -d "{project_path}"', shell=True)
        except Exception:
            try:
                subprocess.Popen(f'start cmd /k "cd /d {project_path}"', shell=True)
            except Exception as e:
                QMessageBox.warning(self, "Terminal", f"Failed to open terminal: {e}")

    def _open_github(self, remote_url: str):
        if not remote_url:
            return
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
        webbrowser.open(remote_url)

    def _try_run_project(self, project_path: str):
        for f in os.listdir(project_path):
            if f.endswith(".bat") and "run" in f.lower():
                os.startfile(os.path.join(project_path, f))
                return
        main_py = os.path.join(project_path, "main.py")
        if os.path.isfile(main_py):
            subprocess.Popen(f'python "{main_py}"', cwd=project_path, shell=True)
            return

        QMessageBox.information(self, "Run Project", "No 'Run *.bat' or 'main.py' found in project root. Opening in VS Code instead.")
        self._open_vscode(project_path)

    def _download_project_zip(self, project_path: str, project_name: str):
        import zipfile
        try:
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_", " ")).strip()
            zip_path = os.path.join(downloads_dir, f"{safe_name}.zip")
            
            ignore_dirs = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".next", "dist", "build"}
            ignore_exts = {".pyc", ".pyo", ".pyd"}

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(project_path):
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in ignore_exts:
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, project_path)
                        zf.write(full_path, os.path.join(safe_name, rel_path))

            QMessageBox.information(
                self,
                "Download ZIP Complete",
                f"Project successfully exported to:\n{zip_path}\n\nOpening Downloads folder..."
            )
            subprocess.Popen(f'explorer /select,"{zip_path}"', shell=True)
        except Exception as e:
            QMessageBox.warning(self, "Download ZIP Failed", f"Could not create zip: {e}")

    def _save_meta_changes(self, p: dict, status: str, priority: str, progress_pct: int, btn: QPushButton = None):
        p["status"] = status
        p["priority"] = priority
        p["progress_pct"] = progress_pct
        folder_name = p.get("folder_name", p.get("name"))
        self.scanner.update_metadata(folder_name, {
            "status": status,
            "priority": priority,
            "progress_pct": progress_pct
        })
        self.refresh_projects()
        if btn:
            btn.setText("✔ Changes Saved!")
            QTimer.singleShot(1800, lambda: btn.setText("💾 Save Lifecycle Changes"))

    def _save_notes(self, p: dict, notes: str, btn: QPushButton = None):
        p["notes"] = notes
        folder_name = p.get("folder_name", p.get("name"))
        self.scanner.update_metadata(folder_name, {"notes": notes})
        if btn:
            btn.setText("✔ Notes Saved!")
            QTimer.singleShot(1800, lambda: btn.setText("💾 Save Developer Notes"))

    def _toggle_todo(self, p: dict, index: int, done: bool):
        todos = p.get("todos", [])
        if 0 <= index < len(todos):
            todos[index]["done"] = done
            p["todos"] = todos
            folder_name = p.get("folder_name", p.get("name"))
            self.scanner.update_metadata(folder_name, {"todos": todos})

    def _add_todo(self, p: dict, text: str, line_edit: QLineEdit):
        if not text:
            return
        todos = p.setdefault("todos", [])
        todos.append({"text": text, "done": False})
        folder_name = p.get("folder_name", p.get("name"))
        self.scanner.update_metadata(folder_name, {"todos": todos})
        line_edit.clear()
        self._render_detail_pane()


def run_app():
    app = QApplication(sys.argv)
    app.setApplicationName("ProjectVault")
    win = ProjectVaultApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()

import os
import json
import datetime

UI_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(UI_DIR)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QLabel, QSpinBox, QFileDialog, QProgressBar, QGridLayout, 
    QFrame, QMessageBox, QScrollArea, QSlider, QButtonGroup, 
    QRadioButton, QSplitter, QPlainTextEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QStackedWidget, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from engine.runner_engine import RunnerEngine

class RunnerWidget(QFrame):
    """A horizontal gray container card mapping live thread stats and sub-counters inline."""
    remove_requested = pyqtSignal(QWidget)
    clicked_signal = pyqtSignal(object)
    checked_line_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    cpm_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    hit_found_signal = pyqtSignal(str, str, str, str)
    
    def __init__(self, settings_tab, proxies_tab, wordlists_tab, configs_dir, runner_id, parent=None):
        super().__init__(parent)
        self.settings_tab = settings_tab
        self.proxies_tab = proxies_tab
        self.wordlists_tab = wordlists_tab
        self.configs_dir = configs_dir
        self.runner_id = runner_id
        
        self.wordlist_lines = []
        self.wordlist_path = ""
        self.engine = None
        self.check_history = []
        self.log_history = []
        self.forced_proxy_mode = "DEF"
        self.start_index = 1
        
        self.init_ui()
        self.refresh_configs()
        self.refresh_wordlists()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.clicked_signal.emit(self)
        super().mouseDoubleClickEvent(event)

    def init_ui(self):
        self.setObjectName("RunnerCard")
        self.setStyleSheet("""
            QFrame#RunnerCard {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                padding: 10px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QComboBox, QSpinBox {
                background-color: #0b0f19;
                border: 1px solid #1c273a;
                border-radius: 3px;
                color: #ffffff;
                font-size: 10px;
                padding: 2px;
                min-width: 100px;
            }
            QPushButton {
                background-color: #1e283d;
                border: 1px solid #232f44;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
                color: #ffffff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #283552;
                border-color: #00e5ff;
            }
            QPushButton#StartBtn {
                background-color: #1b5e20;
                border-color: #2e7d32;
            }
            QPushButton#StopBtn {
                background-color: #b71c1c;
                border-color: #c62828;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # 1. Left Section: Config and wordlist dropdowns, bots, proxies, status
        left_layout = QGridLayout()
        left_layout.setSpacing(6)
        
        left_layout.addWidget(QLabel("Config:"), 0, 0)
        self.cb_config = QComboBox()
        left_layout.addWidget(self.cb_config, 0, 1)
        
        left_layout.addWidget(QLabel("Wordlist:"), 1, 0)
        self.cb_wordlist = QComboBox()
        self.cb_wordlist.currentIndexChanged.connect(self.on_wordlist_combo_changed)
        left_layout.addWidget(self.cb_wordlist, 1, 1)
        
        left_layout.addWidget(QLabel("Bots:"), 0, 2)
        self.spin_bots = QSpinBox()
        self.spin_bots.setRange(1, 200)
        self.spin_bots.setValue(1)
        left_layout.addWidget(self.spin_bots, 0, 3)
        
        left_layout.addWidget(QLabel("Proxies:"), 1, 2)
        self.cb_proxies = QComboBox()
        self.cb_proxies.addItems(["Default", "Working Proxies"])
        left_layout.addWidget(self.cb_proxies, 1, 3)
        
        self.lbl_status = QLabel("STATUS: Idle")
        self.lbl_status.setStyleSheet("color: #ffeb3b; font-weight: bold; font-size: 12px;") # Yellow for Idle
        left_layout.addWidget(self.lbl_status, 0, 4, 2, 1)
        
        layout.addLayout(left_layout)
        
        # 2. Middle Section: Counters and Progress Bar
        mid_layout = QGridLayout()
        mid_layout.setSpacing(8)
        
        self.lbl_hits = QLabel("Hits: 0")
        self.lbl_hits.setStyleSheet("color: #81c784; font-weight: bold;") # Green
        mid_layout.addWidget(self.lbl_hits, 0, 0)
        
        self.lbl_custom = QLabel("Custom: 0")
        self.lbl_custom.setStyleSheet("color: #ffb74d; font-weight: bold;") # Orange
        mid_layout.addWidget(self.lbl_custom, 0, 1)
        
        self.lbl_tocheck = QLabel("ToCheck: 0")
        mid_layout.addWidget(self.lbl_tocheck, 0, 2)
        
        self.lbl_progress = QLabel("Progress: 0 / 0")
        mid_layout.addWidget(self.lbl_progress, 1, 0)
        
        self.lbl_cpm = QLabel("CPM: 0")
        mid_layout.addWidget(self.lbl_cpm, 1, 1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #111;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #2e7d32;
            }
        """)
        mid_layout.addWidget(self.progress_bar, 1, 2)
        
        layout.addLayout(mid_layout)
        
        # 3. Right Section: Inline Start/Stop and Remove
        right_layout = QHBoxLayout()
        right_layout.setSpacing(6)
        
        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.clicked.connect(self.start_runner)
        right_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_runner)
        right_layout.addWidget(self.btn_stop)
        
        self.btn_remove = QPushButton("✖")
        self.btn_remove.setStyleSheet("background-color: #c62828; color: white;")
        self.btn_remove.clicked.connect(self.on_remove)
        right_layout.addWidget(self.btn_remove)
        
        layout.addLayout(right_layout)

    def refresh_configs(self):
        self.cb_config.clear()
        if os.path.exists(self.configs_dir):
            for file in os.listdir(self.configs_dir):
                if file.endswith(".zan") or file.endswith(".json"):
                    name_without_ext = file[:-4] if file.endswith(".zan") else file[:-5]
                    self.cb_config.addItem(name_without_ext)

    def refresh_wordlists(self):
        self.cb_wordlist.blockSignals(True)
        self.cb_wordlist.clear()
        self.cb_wordlist.addItem("[Browse...]", None)
        for wl in self.wordlists_tab.wordlists:
            self.cb_wordlist.addItem(f"{wl['name']} ({wl['total']})", wl)
        self.cb_wordlist.blockSignals(False)

    def on_wordlist_combo_changed(self, idx):
        if idx == 0: # Quick Browse
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist", "", "Text Files (*.txt);;All Files (*)")
            if file_path:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        self.wordlist_lines = f.read().splitlines()
                    self.wordlist_path = file_path
                    filename = os.path.basename(file_path)
                    wl_info = {"name": filename, "path": file_path, "type": "Default", "total": len(self.wordlist_lines)}
                    self.cb_wordlist.setItemData(0, wl_info)
                    self.cb_wordlist.setItemText(0, f"[Quick: {filename} ({len(self.wordlist_lines)})]")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load wordlist: {str(e)}")
            else:
                self.cb_wordlist.setItemText(0, "[Browse...]")
                self.cb_wordlist.setItemData(0, None)
                self.wordlist_lines = []
                self.wordlist_path = ""
        else:
            wl_info = self.cb_wordlist.itemData(idx)
            if wl_info and isinstance(wl_info, dict):
                path = wl_info.get("path", "")
                if path and os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            self.wordlist_lines = f.read().splitlines()
                        self.wordlist_path = path
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to read wordlist: {str(e)}")
                else:
                    QMessageBox.warning(self, "Warning", f"Wordlist file not found at: {path}")

    def read_config_file(self, filepath) -> dict:
        from engine.selenium_engine import OneScriptCompiler
        if filepath.endswith(".zan"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            settings_part = ""
            script_part = ""
            if "[SCRIPT]" in content:
                parts = content.split("[SCRIPT]", 1)
                settings_part = parts[0].replace("[SETTINGS]", "").strip()
                script_part = parts[1].strip()
            else:
                settings_part = content.strip()
                
            try:
                data = json.loads(settings_part)
            except:
                data = {}
                
            if script_part:
                data["blocks"] = OneScriptCompiler.decompile_to_blocks(script_part)
            else:
                data["blocks"] = []
            return data
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

    def start_runner(self):
        if not self.cb_config.currentText():
            QMessageBox.warning(self, "Warning", "Please select a config first.")
            return
            
        if not self.wordlist_lines:
            QMessageBox.warning(self, "Warning", "Please load a wordlist first.")
            return
            
        config_name = self.cb_config.currentText()
        zan_path = os.path.join(self.configs_dir, f"{config_name}.zan")
        json_path = os.path.join(self.configs_dir, f"{config_name}.json")
        if os.path.exists(zan_path):
            config_path = zan_path
        else:
            config_path = json_path
            
        try:
            config_data = self.read_config_file(config_path)
            blocks = config_data.get("blocks", [])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read config file: {str(e)}")
            return
            
        if not blocks:
            QMessageBox.warning(self, "Warning", "Selected config has no blocks.")
            return
            
        settings = config_data.get("selenium_settings", {})
        if not settings:
            settings = self.settings_tab.get_settings()
        # Merge use_selenium from configuration metadata
        settings["use_selenium"] = config_data.get("use_selenium", True)
        settings["save_empty_captures"] = config_data.get("save_empty_captures", False)
        
        forced_mode = getattr(self, "forced_proxy_mode", "DEF")
        if forced_mode == "ON":
            settings["use_proxies"] = True
            proxies = [p for p in self.proxies_tab.proxies if p['status'] == "Working"]
            if not proxies:
                proxies = self.proxies_tab.proxies
        elif forced_mode == "OFF":
            settings["use_proxies"] = False
            proxies = []
        else: # DEF
            if self.cb_proxies.currentText() == "Working Proxies":
                settings["use_proxies"] = True
                proxies = [p for p in self.proxies_tab.proxies if p['status'] == "Working"]
            else:
                settings["use_proxies"] = False
                proxies = []
            
        # Lock controls
        self.cb_config.setEnabled(False)
        self.cb_wordlist.setEnabled(False)
        self.spin_bots.setEnabled(False)
        self.cb_proxies.setEnabled(False)
        
        # Start Index Slicing
        start_idx = max(0, getattr(self, "start_index", 1) - 1)
        lines_to_check = self.wordlist_lines[start_idx:]
        if not lines_to_check:
            QMessageBox.warning(self, "Warning", "Start index is beyond wordlist length.")
            # Unlock controls
            self.cb_config.setEnabled(True)
            self.cb_wordlist.setEnabled(True)
            self.spin_bots.setEnabled(True)
            self.cb_proxies.setEnabled(True)
            return
            
        # Reset counters
        self.lbl_hits.setText("Hits: 0")
        self.lbl_custom.setText("Custom: 0")
        self.lbl_tocheck.setText("ToCheck: 0")
        self.lbl_progress.setText(f"Progress: 0 / {len(lines_to_check)}")
        self.lbl_cpm.setText("CPM: 0")
        self.progress_bar.setValue(0)
        
        self.lbl_status.setText("STATUS: Running")
        self.lbl_status.setStyleSheet("color: #81c784; font-weight: bold; font-size: 12px;") # Green for Running
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        wl_type = "Default"
        wl_format = None
        wl_info = self.cb_wordlist.itemData(self.cb_wordlist.currentIndex())
        if isinstance(wl_info, dict):
            wl_type = wl_info.get("type", "Default")
            wl_format = wl_info.get("format", None)
            
        if wl_type == "Custom" and not wl_format:
            d_set = config_data.get("data_settings", {})
            wl_format = d_set.get("custom_format", None)

        self.check_history = []
        self.log_history = []

        self.engine = RunnerEngine(
            blocks, 
            settings, 
            lines_to_check, 
            proxies, 
            self.spin_bots.value(),
            wordlist_type=wl_type,
            wordlist_format=wl_format
        )
        
        self.engine.hit_signal.connect(self.on_engine_hit)
        self.engine.custom_signal.connect(self.on_engine_custom)
        self.engine.tocheck_signal.connect(self.on_engine_tocheck)
        self.engine.cpm_signal.connect(self.on_engine_cpm)
        self.engine.progress_signal.connect(self.on_engine_progress)
        self.engine.finished_signal.connect(self.on_engine_finished)
        self.engine.checked_line_signal.connect(self.on_line_checked)
        self.engine.log_signal.connect(self.on_engine_log)
        self.engine.hit_found_signal.connect(self.on_engine_hit_found)
        
        self.engine.start()

    def stop_runner(self):
        if self.engine:
            self.engine.stop()
            self.btn_stop.setEnabled(False)

    def on_engine_hit(self):
        self.lbl_hits.setText(f"Hits: {self.engine.hits}")

    def on_engine_hit_found(self, line, status, capture_str, proxy_str):
        # Save hits only in txt file
        if status == "SUCCESS":
            txt_hits_file = os.path.join(PROJECT_DIR, "hits.txt")
            try:
                with open(txt_hits_file, "a", encoding="utf-8") as f:
                    f.write(f"{line} | {proxy_str} | {status} | {capture_str}\n")
            except Exception as e:
                print("Error writing to hits.txt:", e)
        elif status == "CUSTOM":
            txt_custom_file = os.path.join(PROJECT_DIR, "custom.txt")
            try:
                with open(txt_custom_file, "a", encoding="utf-8") as f:
                    f.write(f"{line} | {proxy_str} | {status} | {capture_str}\n")
            except Exception as e:
                print("Error writing to custom.txt:", e)
            
        self.hit_found_signal.emit(line, status, capture_str, proxy_str)

    def on_engine_custom(self):
        self.lbl_custom.setText(f"Custom: {self.engine.custom}")

    def on_engine_tocheck(self):
        self.lbl_tocheck.setText(f"ToCheck: {self.engine.tocheck}")

    def on_engine_cpm(self, cpm):
        self.lbl_cpm.setText(f"CPM: {cpm}")
        self.cpm_signal.emit(cpm)

    def on_engine_progress(self, current, total):
        pct = int((current / total) * 100) if total > 0 else 0
        self.lbl_progress.setText(f"Progress: {current} / {total}")
        self.progress_bar.setValue(pct)
        self.progress_signal.emit(current, total)

    def on_engine_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        self.cb_config.setEnabled(True)
        self.cb_wordlist.setEnabled(True)
        self.spin_bots.setEnabled(True)
        self.cb_proxies.setEnabled(True)
        
        self.lbl_status.setText("STATUS: Idle")
        self.lbl_status.setStyleSheet("color: #ffeb3b; font-weight: bold; font-size: 12px;") # Yellow for Idle
        if self.engine:
            self.start_index = self.start_index + self.engine.completed
        self.engine = None
        self.finished_signal.emit()

    def on_remove(self):
        self.stop_runner()
        self.remove_requested.emit(self)

    def on_line_checked(self, res):
        self.check_history.append(res)
        self.checked_line_signal.emit(res)
        
    def on_engine_log(self, msg):
        self.log_history.append(msg)
        self.log_signal.emit(msg)


class RunnerDetailWorkspace(QWidget):
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.runner = None
        self.init_ui()
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 1. Top Controls Layout
        top_group = QGroupBox("Execution Controller")
        top_layout = QHBoxLayout(top_group)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(12)
        top_group.setStyleSheet("""
            QGroupBox {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #00e5ff;
            }
        """)
        
        # Start Index
        lbl_start = QLabel("Start:")
        lbl_start.setStyleSheet("font-weight: bold; color: #b0bec5;")
        top_layout.addWidget(lbl_start)
        
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 9999999)
        self.spin_start.setValue(1)
        self.spin_start.setMinimumWidth(80)
        self.spin_start.valueChanged.connect(self.on_start_index_changed)
        self.spin_start.setStyleSheet("""
            QSpinBox {
                background-color: #0b0f19;
                border: 1px solid #1c273a;
                color: #ffffff;
                padding: 4px;
                border-radius: 3px;
                font-size: 11px;
            }
            QSpinBox:focus {
                border-color: #00e5ff;
            }
        """)
        top_layout.addWidget(self.spin_start)
        
        # Bots Slider
        self.lbl_bots = QLabel("Bots: 1")
        self.lbl_bots.setStyleSheet("font-weight: bold; color: #b0bec5;")
        top_layout.addWidget(self.lbl_bots)
        
        self.slider_bots = QSlider(Qt.Orientation.Horizontal)
        self.slider_bots.setRange(1, 200)
        self.slider_bots.setValue(1)
        self.slider_bots.setFixedWidth(150)
        self.slider_bots.valueChanged.connect(self.on_bots_slider_changed)
        self.slider_bots.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #1c273a;
                height: 6px;
                background: #0b0f19;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00e5ff;
                border: 1px solid #00e5ff;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        top_layout.addWidget(self.slider_bots)
        
        # Proxy Radio Buttons
        lbl_proxies = QLabel("Proxies:")
        lbl_proxies.setStyleSheet("font-weight: bold; color: #b0bec5;")
        top_layout.addWidget(lbl_proxies)
        
        self.proxy_group = QButtonGroup(self)
        
        self.rad_def = QRadioButton("DEF")
        self.rad_def.setChecked(True)
        self.rad_def.toggled.connect(self.on_proxy_mode_changed)
        self.rad_def.setStyleSheet("QRadioButton { color: #ffffff; font-weight: bold; }")
        self.proxy_group.addButton(self.rad_def)
        top_layout.addWidget(self.rad_def)
        
        self.rad_on = QRadioButton("ON")
        self.rad_on.toggled.connect(self.on_proxy_mode_changed)
        self.rad_on.setStyleSheet("QRadioButton { color: #ffffff; font-weight: bold; }")
        self.proxy_group.addButton(self.rad_on)
        top_layout.addWidget(self.rad_on)
        
        self.rad_off = QRadioButton("OFF")
        self.rad_off.toggled.connect(self.on_proxy_mode_changed)
        self.rad_off.setStyleSheet("QRadioButton { color: #ffffff; font-weight: bold; }")
        self.proxy_group.addButton(self.rad_off)
        top_layout.addWidget(self.rad_off)
        
        top_layout.addStretch()
        
        # Massive Launch Button
        self.btn_start = QPushButton("START")
        self.btn_start.setObjectName("HugeStartBtn")
        self.btn_start.setMinimumHeight(45)
        self.btn_start.setMinimumWidth(150)
        self.btn_start.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_start.setStyleSheet("""
            QPushButton#HugeStartBtn {
                background-color: #2e7d32;
                border: 1px solid #388e3c;
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton#HugeStartBtn:hover {
                background-color: #388e3c;
            }
        """)
        top_layout.addWidget(self.btn_start)
        
        self.main_layout.addWidget(top_group)
        
        # 2. Middle Bilateral Split
        split_layout = QHBoxLayout()
        split_layout.setSpacing(10)
        
        # Left Monitor Deck
        left_group = QGroupBox("Checked Spreadsheet")
        left_group.setStyleSheet("""
            QGroupBox {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #00e5ff;
            }
        """)
        left_box = QVBoxLayout(left_group)
        left_box.setContentsMargins(6, 12, 6, 6)
        
        self.tbl_left = QTableWidget()
        self.tbl_left.setColumnCount(4)
        self.tbl_left.setHorizontalHeaderLabels(["Id", "Data", "Proxy", "Status"])
        self.tbl_left.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_left.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_left.setFont(QFont("Consolas", 8))
        self.tbl_left.setStyleSheet("""
            QTableWidget {
                background-color: #0b0f19;
                gridline-color: #1c273a;
                color: #e0e0e0;
                border: 1px solid #1c273a;
            }
            QHeaderView::section {
                background-color: #0d121a;
                color: #00e5ff;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #1c273a;
            }
        """)
        left_box.addWidget(self.tbl_left)
        split_layout.addWidget(left_group, stretch=1)
        
        # Right Monitor Deck
        right_group = QGroupBox("Live Activity Logs")
        right_group.setStyleSheet("""
            QGroupBox {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #00e5ff;
            }
        """)
        right_box = QVBoxLayout(right_group)
        right_box.setContentsMargins(6, 12, 6, 6)
        right_box.setSpacing(6)
        
        self.tbl_right = QTableWidget()
        self.tbl_right.setColumnCount(5)
        self.tbl_right.setHorizontalHeaderLabels(["Time", "Data", "Proxy", "Type", "Capture"])
        self.tbl_right.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_right.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_right.setFont(QFont("Consolas", 8))
        self.tbl_right.setStyleSheet("""
            QTableWidget {
                background-color: #0b0f19;
                gridline-color: #1c273a;
                color: #e0e0e0;
                border: 1px solid #1c273a;
            }
            QHeaderView::section {
                background-color: #0d121a;
                color: #00e5ff;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #1c273a;
            }
        """)
        right_box.addWidget(self.tbl_right)
        
        # Lower Filter & Countdown row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        
        self.btn_filter_hits = QPushButton("Hits")
        self.btn_filter_hits.setCheckable(True)
        self.btn_filter_hits.setChecked(True)
        self.btn_filter_hits.toggled.connect(self.filter_right_table)
        self.btn_filter_hits.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #2e7d32;
                color: #81c784;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 10px;
                border-radius: 2px;
            }
            QPushButton:checked {
                background-color: #2e7d32;
                color: white;
            }
        """)
        filter_row.addWidget(self.btn_filter_hits)
        
        self.btn_filter_custom = QPushButton("Custom")
        self.btn_filter_custom.setCheckable(True)
        self.btn_filter_custom.setChecked(True)
        self.btn_filter_custom.toggled.connect(self.filter_right_table)
        self.btn_filter_custom.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #ef6c00;
                color: #ffb74d;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 10px;
                border-radius: 2px;
            }
            QPushButton:checked {
                background-color: #ef6c00;
                color: white;
            }
        """)
        filter_row.addWidget(self.btn_filter_custom)
        
        self.btn_filter_tocheck = QPushButton("ToCheck")
        self.btn_filter_tocheck.setCheckable(True)
        self.btn_filter_tocheck.setChecked(True)
        self.btn_filter_tocheck.toggled.connect(self.filter_right_table)
        self.btn_filter_tocheck.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #37474f;
                color: #b0bec5;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 10px;
                border-radius: 2px;
            }
            QPushButton:checked {
                background-color: #37474f;
                color: white;
            }
        """)
        filter_row.addWidget(self.btn_filter_tocheck)
        
        filter_row.addStretch()
        
        self.lbl_time_left = QLabel("Time Left: Unknown time left")
        self.lbl_time_left.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 10px;")
        filter_row.addWidget(self.lbl_time_left)
        
        right_box.addLayout(filter_row)
        
        split_layout.addWidget(right_group, stretch=1)
        self.main_layout.addLayout(split_layout, stretch=1)
        
        # 3. Footer controls
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        
        # Lower Left Config Dock
        config_dock = QGroupBox("Configuration Dock")
        config_dock.setStyleSheet("""
            QGroupBox {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #00e5ff;
            }
        """)
        config_layout = QVBoxLayout(config_dock)
        config_layout.setContentsMargins(10, 15, 10, 10)
        config_layout.setSpacing(6)
        
        combo_row = QHBoxLayout()
        lbl_cfg = QLabel("Select CFG:")
        lbl_cfg.setStyleSheet("font-weight: bold; color: #b0bec5;")
        combo_row.addWidget(lbl_cfg)
        
        self.cb_cfg = QComboBox()
        self.cb_cfg.currentIndexChanged.connect(self.on_cfg_changed)
        self.cb_cfg.setStyleSheet("""
            QComboBox {
                background-color: #0b0f19;
                border: 1px solid #1c273a;
                color: #ffffff;
                padding: 4px;
                border-radius: 3px;
            }
            QComboBox:focus {
                border-color: #00e5ff;
            }
        """)
        combo_row.addWidget(self.cb_cfg)
        
        lbl_list = QLabel("Select List:")
        lbl_list.setStyleSheet("font-weight: bold; color: #b0bec5;")
        combo_row.addWidget(lbl_list)
        
        self.cb_list = QComboBox()
        self.cb_list.currentIndexChanged.connect(self.on_list_changed)
        self.cb_list.setStyleSheet("""
            QComboBox {
                background-color: #0b0f19;
                border: 1px solid #1c273a;
                color: #ffffff;
                padding: 4px;
                border-radius: 3px;
            }
            QComboBox:focus {
                border-color: #00e5ff;
            }
        """)
        combo_row.addWidget(self.cb_list)
        
        config_layout.addLayout(combo_row)
        
        # Diagnostic console
        self.txt_console = QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setFont(QFont("Consolas", 8))
        self.txt_console.setPlaceholderText("Runner diagnostic console logs will appear here...")
        self.txt_console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #06090f;
                border: 1px solid #1c273a;
                color: #00ff00; /* Rolling matrix green text */
                border-radius: 3px;
            }
        """)
        config_layout.addWidget(self.txt_console)
        footer_layout.addWidget(config_dock, stretch=1)
        
        # Lower Right Metric Counter Form
        stats_group = QGroupBox("Metric Status Counters")
        stats_group.setStyleSheet("""
            QGroupBox {
                background-color: #151b27;
                border: 1px solid #1c273a;
                border-radius: 6px;
                margin-top: 8px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #00e5ff;
            }
        """)
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setContentsMargins(10, 15, 10, 10)
        stats_layout.setSpacing(10)
        
        # Data Stats Frame
        data_frame = QFrame()
        data_frame.setStyleSheet("background-color: #0b0f19; border: 1px solid #1c273a; border-radius: 4px; padding: 6px;")
        data_grid = QGridLayout(data_frame)
        data_grid.setSpacing(4)
        
        lbl_d_header = QLabel("DATA STATS")
        lbl_d_header.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 11px;")
        data_grid.addWidget(lbl_d_header, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        def add_stat_row(grid, label_text, row, style_color=None):
            lbl_name = QLabel(label_text)
            lbl_name.setStyleSheet("color: #90a4ae; font-size: 10px;")
            lbl_val = QLabel("0")
            lbl_val.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 10px;")
            if style_color:
                lbl_val.setStyleSheet(f"color: {style_color}; font-weight: bold; font-size: 10px;")
            grid.addWidget(lbl_name, row, 0)
            grid.addWidget(lbl_val, row, 1, Qt.AlignmentFlag.AlignRight)
            return lbl_val
            
        self.lbl_val_total = add_stat_row(data_grid, "Total:", 1)
        self.lbl_val_hits = add_stat_row(data_grid, "Hits:", 2, "#81c784") # Green
        self.lbl_val_custom = add_stat_row(data_grid, "Custom:", 3, "#ffb74d") # Orange
        self.lbl_val_bad = add_stat_row(data_grid, "Bad:", 4, "#e57373") # Red
        self.lbl_val_retries = add_stat_row(data_grid, "Retries:", 5, "#cfd8dc")
        self.lbl_val_tocheck = add_stat_row(data_grid, "To Check:", 6, "#ffd54f") # Yellow
        
        stats_layout.addWidget(data_frame)
        
        # Proxy Stats Frame
        proxy_frame = QFrame()
        proxy_frame.setStyleSheet("background-color: #0b0f19; border: 1px solid #1c273a; border-radius: 4px; padding: 6px;")
        proxy_grid = QGridLayout(proxy_frame)
        proxy_grid.setSpacing(4)
        
        lbl_p_header = QLabel("PROXIES STATS")
        lbl_p_header.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 11px;")
        proxy_grid.addWidget(lbl_p_header, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_val_p_total = add_stat_row(proxy_grid, "Total:", 1)
        self.lbl_val_p_alive = add_stat_row(proxy_grid, "Alive:", 2, "#81c784")
        self.lbl_val_p_banned = add_stat_row(proxy_grid, "Banned:", 3, "#e57373")
        self.lbl_val_p_bad = add_stat_row(proxy_grid, "Bad:", 4, "#e57373")
        self.lbl_val_p_cpm = add_stat_row(proxy_grid, "CPM:", 5, "#00e5ff")
        self.lbl_val_p_credit = add_stat_row(proxy_grid, "Credit:", 6, "#b0bec5")
        
        stats_layout.addWidget(proxy_frame)
        footer_layout.addWidget(stats_group, stretch=1)
        self.main_layout.addLayout(footer_layout)
        
        # 4. Back Navigation
        bottom_row = QHBoxLayout()
        self.btn_back = QPushButton("⬅ Back")
        self.btn_back.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #151b27;
                border: 1px solid #232f44;
                border-radius: 4px;
                padding: 6px 16px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #1e283d;
                border-color: #00e5ff;
            }
        """)
        self.btn_back.clicked.connect(self.back_requested.emit)
        bottom_row.addWidget(self.btn_back)
        bottom_row.addStretch()
        self.main_layout.addLayout(bottom_row)

    def bind_runner(self, runner):
        self.runner = runner
        
        self.cb_cfg.blockSignals(True)
        self.cb_list.blockSignals(True)
        self.spin_start.blockSignals(True)
        self.slider_bots.blockSignals(True)
        self.rad_def.blockSignals(True)
        self.rad_on.blockSignals(True)
        self.rad_off.blockSignals(True)
        
        self.cb_cfg.clear()
        for i in range(runner.cb_config.count()):
            self.cb_cfg.addItem(runner.cb_config.itemText(i), runner.cb_config.itemData(i))
        self.cb_cfg.setCurrentText(runner.cb_config.currentText())
        
        self.cb_list.clear()
        for i in range(runner.cb_wordlist.count()):
            self.cb_list.addItem(runner.cb_wordlist.itemText(i), runner.cb_wordlist.itemData(i))
        self.cb_list.setCurrentIndex(runner.cb_wordlist.currentIndex())
        
        self.spin_start.setValue(getattr(runner, "start_index", 1))
        self.slider_bots.setValue(runner.spin_bots.value())
        self.lbl_bots.setText(f"Bots: {runner.spin_bots.value()}")
        
        mode = getattr(runner, "forced_proxy_mode", "DEF")
        if mode == "ON":
            self.rad_on.setChecked(True)
        elif mode == "OFF":
            self.rad_off.setChecked(True)
        else:
            self.rad_def.setChecked(True)
            
        running = runner.engine is not None and runner.engine.is_running
        self.cb_cfg.setEnabled(not running)
        self.cb_list.setEnabled(not running)
        self.spin_start.setEnabled(not running)
        self.slider_bots.setEnabled(not running)
        self.rad_def.setEnabled(not running)
        self.rad_on.setEnabled(not running)
        self.rad_off.setEnabled(not running)
        
        if running:
            self.btn_start.setText("STOP")
            self.btn_start.setStyleSheet("background-color: #c62828; color: white;")
        else:
            self.btn_start.setText("START")
            self.btn_start.setStyleSheet("background-color: #2e7d32; color: white;")
            
        self.cb_cfg.blockSignals(False)
        self.cb_list.blockSignals(False)
        self.spin_start.blockSignals(False)
        self.slider_bots.blockSignals(False)
        self.rad_def.blockSignals(False)
        self.rad_on.blockSignals(False)
        self.rad_off.blockSignals(False)
        
        self.tbl_left.setRowCount(0)
        self.tbl_right.setRowCount(0)
        for res in runner.check_history:
            self.add_result_to_tables(res)
            
        self.txt_console.clear()
        for log in runner.log_history:
            self.txt_console.appendPlainText(log)
            
        self.update_stats_display()
        
        try:
            runner.checked_line_signal.disconnect()
        except:
            pass
        try:
            runner.log_signal.disconnect()
        except:
            pass
        try:
            runner.progress_signal.disconnect()
        except:
            pass
        try:
            runner.cpm_signal.disconnect()
        except:
            pass
        try:
            runner.finished_signal.disconnect()
        except:
            pass
            
        runner.checked_line_signal.connect(self.on_line_checked)
        runner.log_signal.connect(self.on_log_received)
        runner.progress_signal.connect(self.on_progress_update)
        runner.cpm_signal.connect(self.on_cpm_update)
        runner.finished_signal.connect(self.on_runner_finished)

    def on_start_clicked(self):
        if self.runner is None:
            return
            
        running = self.runner.engine is not None and self.runner.engine.is_running
        if running:
            self.runner.stop_runner()
            self.btn_start.setEnabled(False)
        else:
            self.runner.cb_config.setCurrentText(self.cb_cfg.currentText())
            self.runner.cb_wordlist.setCurrentIndex(self.cb_list.currentIndex())
            self.runner.start_runner()
            
            if self.runner.engine and self.runner.engine.is_running:
                self.btn_start.setText("STOP")
                self.btn_start.setStyleSheet("background-color: #c62828; color: white;")
                self.cb_cfg.setEnabled(False)
                self.cb_list.setEnabled(False)
                self.spin_start.setEnabled(False)
                self.slider_bots.setEnabled(False)
                self.rad_def.setEnabled(False)
                self.rad_on.setEnabled(False)
                self.rad_off.setEnabled(False)
                
    def on_start_index_changed(self, val):
        if self.runner:
            self.runner.start_index = val
            
    def on_bots_slider_changed(self, val):
        self.lbl_bots.setText(f"Bots: {val}")
        if self.runner:
            self.runner.spin_bots.setValue(val)
            
    def on_proxy_mode_changed(self):
        if self.runner:
            if self.rad_on.isChecked():
                self.runner.forced_proxy_mode = "ON"
            elif self.rad_off.isChecked():
                self.runner.forced_proxy_mode = "OFF"
            else:
                self.runner.forced_proxy_mode = "DEF"
                
    def on_cfg_changed(self, idx):
        if self.runner and idx >= 0:
            self.runner.cb_config.setCurrentIndex(idx)
            
    def on_list_changed(self, idx):
        if self.runner and idx >= 0:
            self.runner.cb_wordlist.setCurrentIndex(idx)

    def add_result_to_tables(self, res):
        # Left table
        row_l = self.tbl_left.rowCount()
        self.tbl_left.insertRow(row_l)
        
        id_item = QTableWidgetItem(str(res["id"]))
        data_item = QTableWidgetItem(res["line"])
        proxy_item = QTableWidgetItem(res["proxy"])
        status_item = QTableWidgetItem(res["status"])
        
        status = res["status"]
        if status == "SUCCESS":
            status_item.setForeground(QColor("#81c784"))
        elif status == "CUSTOM":
            status_item.setForeground(QColor("#ffb74d"))
        elif status in ("FAIL", "ERROR"):
            status_item.setForeground(QColor("#e57373"))
        elif status == "BAN":
            status_item.setForeground(QColor("#ef5350"))
        elif status == "RETRY":
            status_item.setForeground(QColor("#ffd54f"))
            
        self.tbl_left.setItem(row_l, 0, id_item)
        self.tbl_left.setItem(row_l, 1, data_item)
        self.tbl_left.setItem(row_l, 2, proxy_item)
        self.tbl_left.setItem(row_l, 3, status_item)
        self.tbl_left.scrollToBottom()
        
        # Right table
        row_r = self.tbl_right.rowCount()
        self.tbl_right.insertRow(row_r)
        
        time_item = QTableWidgetItem(res["time"])
        data_r_item = QTableWidgetItem(res["line"])
        proxy_r_item = QTableWidgetItem(res["proxy"])
        type_item = QTableWidgetItem(res["status"])
        capture_item = QTableWidgetItem(res["capture"])
        
        if status == "SUCCESS":
            type_item.setForeground(QColor("#81c784"))
        elif status == "CUSTOM":
            type_item.setForeground(QColor("#ffb74d"))
        elif status in ("FAIL", "ERROR"):
            type_item.setForeground(QColor("#e57373"))
        elif status == "BAN":
            type_item.setForeground(QColor("#ef5350"))
        elif status == "RETRY":
            type_item.setForeground(QColor("#ffd54f"))
            
        self.tbl_right.setItem(row_r, 0, time_item)
        self.tbl_right.setItem(row_r, 1, data_r_item)
        self.tbl_right.setItem(row_r, 2, proxy_r_item)
        self.tbl_right.setItem(row_r, 3, type_item)
        self.tbl_right.setItem(row_r, 4, capture_item)
        
        self.apply_filter_to_row(row_r, status)
        self.tbl_right.scrollToBottom()

    def filter_right_table(self):
        for row in range(self.tbl_right.rowCount()):
            type_item = self.tbl_right.item(row, 3)
            if type_item:
                self.apply_filter_to_row(row, type_item.text())
                
    def apply_filter_to_row(self, row, status):
        show = True
        if status == "SUCCESS":
            show = self.btn_filter_hits.isChecked()
        elif status == "CUSTOM":
            show = self.btn_filter_custom.isChecked()
        else:
            show = self.btn_filter_tocheck.isChecked()
        self.tbl_right.setRowHidden(row, not show)

    def on_line_checked(self, res):
        self.add_result_to_tables(res)
        self.update_stats_display()
        
    def on_log_received(self, msg):
        self.txt_console.appendPlainText(msg)
        
    def on_progress_update(self, completed, total):
        self.update_stats_display()
        
    def on_cpm_update(self, cpm):
        self.lbl_val_p_cpm.setText(str(cpm))
        if self.runner and self.runner.engine:
            remaining = self.runner.engine.total - self.runner.engine.completed
            if cpm > 0 and remaining > 0:
                mins = int(remaining / cpm)
                self.lbl_time_left.setText(f"Time Left: ~{mins} mins ({remaining} left)")
            else:
                self.lbl_time_left.setText("Time Left: Unknown time left")
                
    def on_runner_finished(self):
        self.btn_start.setText("START")
        self.btn_start.setStyleSheet("background-color: #2e7d32; color: white;")
        self.btn_start.setEnabled(True)
        
        self.cb_cfg.setEnabled(True)
        self.cb_list.setEnabled(True)
        self.spin_start.setEnabled(True)
        self.slider_bots.setEnabled(True)
        self.rad_def.setEnabled(True)
        self.rad_on.setEnabled(True)
        self.rad_off.setEnabled(True)
        self.update_stats_display()

    def update_stats_display(self):
        if self.runner is None:
            return
            
        import time
        total_val = len(self.runner.wordlist_lines)
        self.lbl_val_total.setText(str(total_val))
        
        if self.runner.engine:
            self.lbl_val_hits.setText(str(self.runner.engine.hits))
            self.lbl_val_custom.setText(str(self.runner.engine.custom))
            self.lbl_val_bad.setText(str(self.runner.engine.bad))
            self.lbl_val_retries.setText(str(self.runner.engine.retries))
            self.lbl_val_tocheck.setText(str(self.runner.engine.tocheck))
        else:
            hits = sum(1 for r in self.runner.check_history if r["status"] == "SUCCESS")
            custom = sum(1 for r in self.runner.check_history if r["status"] == "CUSTOM")
            bad = sum(1 for r in self.runner.check_history if r["status"] == "FAIL")
            retries = sum(1 for r in self.runner.check_history if r["status"] == "RETRY")
            tocheck = sum(1 for r in self.runner.check_history if r["status"] not in ("SUCCESS", "CUSTOM", "FAIL", "RETRY"))
            
            self.lbl_val_hits.setText(str(hits))
            self.lbl_val_custom.setText(str(custom))
            self.lbl_val_bad.setText(str(bad))
            self.lbl_val_retries.setText(str(retries))
            self.lbl_val_tocheck.setText(str(tocheck))
            
        p_total = len(self.runner.proxies_tab.proxies)
        self.lbl_val_p_total.setText(str(p_total))
        
        p_alive = sum(1 for p in self.runner.proxies_tab.proxies if p.get("status") == "Working")
        self.lbl_val_p_alive.setText(str(p_alive))
        
        p_banned = sum(1 for p in self.runner.proxies_tab.proxies if p.get("status") == "Failed")
        self.lbl_val_p_banned.setText(str(p_banned))
        self.lbl_val_p_bad.setText(str(p_banned))
        
        cpm = 0
        if self.runner.engine:
            elapsed = time.time() - self.runner.engine.start_time
            if elapsed > 0:
                cpm = int((self.runner.engine.completed / elapsed) * 60)
        self.lbl_val_p_cpm.setText(str(cpm))
        self.lbl_val_p_credit.setText("100%")


class RunnerTab(QWidget):
    """Main panel displaying top control buttons [+ New], [▶ Start All], [■ Stop All], [✖ Remove All] and list of Runners."""
    def __init__(self, settings_tab, proxies_tab, wordlists_tab, parent=None):
        super().__init__(parent)
        self.settings_tab = settings_tab
        self.proxies_tab = proxies_tab
        self.wordlists_tab = wordlists_tab
        self.configs_dir = os.path.join(PROJECT_DIR, "configs")
        self.runner_counter = 0
        self.runners = []
        
        self.init_ui()
        self.load_runners()
        
    def init_ui(self):
        # Main layout of RunnerTab contains just the stacked widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget(self)
        self.main_layout.addWidget(self.stacked_widget)
        
        # Page 0: Overview
        self.overview_widget = QWidget()
        overview_layout = QVBoxLayout(self.overview_widget)
        overview_layout.setContentsMargins(10, 10, 10, 10)
        overview_layout.setSpacing(10)
        
        # Top Control Row
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        
        self.btn_new = QPushButton("+ New")
        self.btn_new.setStyleSheet("background-color: #1976d2; font-weight: bold; color: white;")
        self.btn_new.clicked.connect(self.on_new_runner)
        top_bar.addWidget(self.btn_new)
        
        self.btn_start_all = QPushButton("▶ Start All")
        self.btn_start_all.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
        self.btn_start_all.clicked.connect(self.on_start_all)
        top_bar.addWidget(self.btn_start_all)
        
        self.btn_stop_all = QPushButton("■ Stop All")
        self.btn_stop_all.setStyleSheet("background-color: #c62828; font-weight: bold; color: white;")
        self.btn_stop_all.clicked.connect(self.on_stop_all)
        top_bar.addWidget(self.btn_stop_all)
        
        self.btn_remove_all = QPushButton("✖ Remove All")
        self.btn_remove_all.setStyleSheet("background-color: #d32f2f; font-weight: bold; color: white;")
        self.btn_remove_all.clicked.connect(self.on_remove_all)
        top_bar.addWidget(self.btn_remove_all)
        
        top_bar.addStretch()
        overview_layout.addLayout(top_bar)
        
        # Scroll Area for Runner cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(10)
        self.scroll_content.setLayout(self.scroll_layout)
        
        self.scroll.setWidget(self.scroll_content)
        overview_layout.addWidget(self.scroll)
        
        self.stacked_widget.addWidget(self.overview_widget)
        
        # Page 1: Detail Workspace
        self.detail_workspace = RunnerDetailWorkspace(self)
        self.detail_workspace.back_requested.connect(self.show_overview)
        self.stacked_widget.addWidget(self.detail_workspace)
        
        # Listen for wordlists changes
        self.wordlists_tab.wordlists_changed.connect(self.refresh_all_runners_wordlists)
        
    def show_overview(self):
        self.stacked_widget.setCurrentIndex(0)
        
    def show_runner_details(self, runner):
        self.detail_workspace.bind_runner(runner)
        self.stacked_widget.setCurrentIndex(1)
        
    def on_new_runner(self):
        self.runner_counter += 1
        runner = RunnerWidget(
            self.settings_tab, 
            self.proxies_tab, 
            self.wordlists_tab,
            self.configs_dir, 
            self.runner_counter
        )
        runner.remove_requested.connect(self.remove_runner)
        runner.clicked_signal.connect(self.show_runner_details)
        self.runners.append(runner)
        self.scroll_layout.addWidget(runner)
        
    def remove_runner(self, runner):
        if runner in self.runners:
            if self.detail_workspace.runner == runner:
                self.stacked_widget.setCurrentIndex(0)
                self.detail_workspace.runner = None
            self.runners.remove(runner)
            self.scroll_layout.removeWidget(runner)
            runner.deleteLater()
            
    def on_start_all(self):
        for runner in self.runners:
            if not (runner.engine and runner.engine.is_running):
                runner.start_runner()
                
    def on_stop_all(self):
        for runner in self.runners:
            runner.stop_runner()
            
    def on_remove_all(self):
        self.stacked_widget.setCurrentIndex(0)
        self.detail_workspace.runner = None
        for runner in list(self.runners):
            self.remove_runner(runner)
        self.runner_counter = 0

    def refresh_all_runners_wordlists(self):
        for r in self.runners:
            r.refresh_wordlists()

    def refresh_configs(self):
        for r in self.runners:
            r.refresh_configs()

    def save_runners(self):
        import json
        states = []
        for r in self.runners:
            current_start = getattr(r, "start_index", 1)
            if r.engine:
                current_start = current_start + r.engine.completed
            state = {
                "config": r.cb_config.currentText(),
                "wordlist_path": r.wordlist_path,
                "bots": r.spin_bots.value(),
                "proxy_mode": r.cb_proxies.currentText(),
                "forced_proxy_mode": getattr(r, "forced_proxy_mode", "DEF"),
                "start_index": current_start
            }
            states.append(state)
        path = os.path.join(PROJECT_DIR, "runners_state.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(states, f, indent=4)
        except Exception as e:
            print("Failed to save runners:", e)

    def load_runners(self):
        import json
        path = os.path.join(PROJECT_DIR, "runners_state.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                states = json.load(f)
            for state in states:
                self.on_new_runner()
                if self.runners:
                    r = self.runners[-1]
                    # Restore runner state
                    cfg = state.get("config")
                    if cfg:
                        idx = r.cb_config.findText(cfg)
                        if idx >= 0:
                            r.cb_config.setCurrentIndex(idx)
                        else:
                            r.cb_config.setCurrentText(cfg)
                    wl_path = state.get("wordlist_path")
                    if wl_path and os.path.exists(wl_path):
                        found_idx = -1
                        for i in range(1, r.cb_wordlist.count()):
                            wl_info = r.cb_wordlist.itemData(i)
                            if wl_info and wl_info.get("path") == wl_path:
                                found_idx = i
                                break
                        if found_idx >= 0:
                            r.cb_wordlist.setCurrentIndex(found_idx)
                        else:
                            try:
                                with open(wl_path, "r", encoding="utf-8", errors="ignore") as f:
                                    r.wordlist_lines = f.read().splitlines()
                                r.wordlist_path = wl_path
                                filename = os.path.basename(wl_path)
                                wl_info = {"name": filename, "path": wl_path, "type": "Default", "total": len(r.wordlist_lines)}
                                r.cb_wordlist.setItemData(0, wl_info)
                                r.cb_wordlist.setItemText(0, f"[Quick: {filename} ({len(r.wordlist_lines)})]")
                                r.cb_wordlist.setCurrentIndex(0)
                            except:
                                pass
                    r.spin_bots.setValue(state.get("bots", 1))
                    p_mode = state.get("proxy_mode", "Default")
                    idx = r.cb_proxies.findText(p_mode)
                    if idx >= 0:
                        r.cb_proxies.setCurrentIndex(idx)
                    r.forced_proxy_mode = state.get("forced_proxy_mode", "DEF")
                    r.start_index = state.get("start_index", 1)
        except Exception as e:
            print("Error loading runners:", e)

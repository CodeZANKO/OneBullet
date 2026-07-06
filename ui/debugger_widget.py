import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QPlainTextEdit, QFrame, QTextBrowser, QCheckBox, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextDocument
from engine.selenium_engine import SeleniumEngine, OneScriptCompiler

class DebuggerWidget(QWidget):
    def __init__(self, configs_tab, parent=None):
        super().__init__(parent)
        self.configs_tab = configs_tab
        self.engine = None
        self.init_ui()
        
    def init_ui(self):
        self.setObjectName("DebuggerWidget")
        self.setStyleSheet("""
            QWidget#DebuggerWidget {
                background-color: #1a1a1a;
                color: #d3d3d3;
            }
            QLabel {
                color: #c0c0c0;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton {
                background-color: #3e4248;
                border: 1px solid #4f535a;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
                color: #ffffff;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4f535a;
            }
            QPushButton#StartBtn {
                background-color: #2e7d32;
                border-color: #388e3c;
            }
            QPushButton#StepBtn {
                background-color: #1976d2;
                border-color: #1e88e5;
            }
            QCheckBox {
                color: #d3d3d3;
                font-weight: bold;
                font-size: 11px;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #d3d3d3;
                font-size: 10px;
                padding: 2px;
            }
            QTableWidget {
                background-color: #151515;
                border: 1px solid #2d2d2d;
                gridline-color: #2d2d2d;
                color: #d3d3d3;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #c0c0c0;
                padding: 4px;
                border: 1px solid #2d2d2d;
                font-weight: bold;
            }
            QPlainTextEdit, QTextBrowser, QTextEdit {
                background-color: #151515;
                border: 1px solid #2d2d2d;
                color: #d3d3d3;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QTabWidget::pane {
                border: 1px solid #2d2d2d;
                background-color: #151515;
            }
            QTabBar::tab {
                background: #252525;
                border: 1px solid #2d2d2d;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 10px;
            }
            QTabBar::tab:selected {
                background: #1a1a1a;
                border-bottom-color: #1a1a1a;
                color: #00e5ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # 1. Top Row controls: [Start] button, [ ] SBS checkbox, [Step] label/button, and a "Data" dropdown.
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.clicked.connect(self.on_start)
        top_row.addWidget(self.btn_start)
        
        self.chk_sbs = QCheckBox("SBS")
        self.chk_sbs.stateChanged.connect(self.on_sbs_changed)
        top_row.addWidget(self.chk_sbs)
        
        self.btn_step = QPushButton("Step")
        self.btn_step.setObjectName("StepBtn")
        self.btn_step.setEnabled(False)
        self.btn_step.clicked.connect(self.on_step)
        top_row.addWidget(self.btn_step)
        
        top_row.addWidget(QLabel("Data:"))
        self.cb_data_type = QComboBox()
        self.cb_data_type.addItems(["Default", "Credentials", "Card", "Numeric", "URLs", "Extended", "Custom"])
        top_row.addWidget(self.cb_data_type)
        
        layout.addLayout(top_row)
        
        # 2. Middle Row: "Proxy: OFF" and "Http" type selectors.
        mid_row = QHBoxLayout()
        mid_row.setSpacing(6)
        
        self.cb_proxy_status = QComboBox()
        self.cb_proxy_status.addItems(["Proxy: OFF", "Proxy: ON"])
        mid_row.addWidget(self.cb_proxy_status)
        
        self.cb_proxy_type = QComboBox()
        self.cb_proxy_type.addItems(["Http", "Socks4", "Socks5"])
        mid_row.addWidget(self.cb_proxy_type)
        
        layout.addLayout(mid_row)
        
        # 3. Lower Tabbed Frame: [ Data ] [ Log ] [ HTML View ]
        self.tabs = QTabWidget()
        
        # Data Tab
        data_tab_widget = QWidget()
        data_tab_layout = QVBoxLayout(data_tab_widget)
        data_tab_layout.setContentsMargins(4, 4, 4, 4)
        data_tab_layout.setSpacing(6)
        
        test_data_layout = QHBoxLayout()
        test_data_layout.addWidget(QLabel("Test Line:"))
        self.txt_test_data = QLineEdit()
        self.txt_test_data.setPlaceholderText("e.g. zannko.hatam@gmail.com:Zanko1234")
        test_data_layout.addWidget(self.txt_test_data)
        data_tab_layout.addLayout(test_data_layout)
        
        self.dbg_data_table = QTableWidget()
        self.dbg_data_table.setColumnCount(3)
        self.dbg_data_table.setHorizontalHeaderLabels(["Variable Name", "Value", "Type"])
        self.dbg_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.dbg_data_table.setFont(QFont("Consolas", 8))
        data_tab_layout.addWidget(self.dbg_data_table)
        
        self.tabs.addTab(data_tab_widget, "Data")
        
        # Log Tab
        self.dbg_logs = QPlainTextEdit()
        self.dbg_logs.setReadOnly(True)
        self.dbg_logs.setFont(QFont("Consolas", 8))
        self.tabs.addTab(self.dbg_logs, "Log")
        
        # HTML View Tab with Search Bar
        html_tab = QWidget()
        html_tab_layout = QVBoxLayout(html_tab)
        html_tab_layout.setContentsMargins(4, 4, 4, 4)
        html_tab_layout.setSpacing(6)
        
        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)
        
        self.txt_search_html = QLineEdit()
        self.txt_search_html.setPlaceholderText("Search in HTML source...")
        self.txt_search_html.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #ffffff;
                font-size: 11px;
                padding: 4px;
            }
        """)
        self.txt_search_html.returnPressed.connect(lambda: self.find_in_html(backward=False))
        search_layout.addWidget(self.txt_search_html)
        
        self.btn_find_prev = QPushButton("Find Prev")
        self.btn_find_prev.clicked.connect(lambda: self.find_in_html(backward=True))
        search_layout.addWidget(self.btn_find_prev)
        
        self.btn_find_next = QPushButton("Find Next")
        self.btn_find_next.clicked.connect(lambda: self.find_in_html(backward=False))
        search_layout.addWidget(self.btn_find_next)
        
        self.lbl_search_status = QLabel("")
        self.lbl_search_status.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        search_layout.addWidget(self.lbl_search_status)
        
        html_tab_layout.addLayout(search_layout)
        
        self.dbg_html = QTextBrowser()
        self.dbg_html.setReadOnly(True)
        self.dbg_html.setFont(QFont("Consolas", 8))
        html_tab_layout.addWidget(self.dbg_html)
        
        self.tabs.addTab(html_tab, "HTML View")
        
        layout.addWidget(self.tabs)

    def on_sbs_changed(self, state):
        is_sbs = (state == Qt.CheckState.Checked.value or state == True)
        self.btn_step.setEnabled(is_sbs)

    def on_step(self):
        if self.engine and self.engine.isRunning():
            self.engine.resume_execution() # Resume for one block step

    def on_start(self):
        if self.engine and self.engine.isRunning():
            self.log_message("[DEBUGGER] Stopping execution...")
            self.engine.stop_execution()
            self.btn_start.setText("Start")
            self.btn_start.setStyleSheet("background-color: #2e7d32;")
            return
            
        self.dbg_logs.clear()
        self.dbg_html.clear()
        self.dbg_data_table.setRowCount(0)
        
        if self.configs_tab.btn_view_text.isChecked():
            self.configs_tab.blocks = OneScriptCompiler.decompile_to_blocks(self.configs_tab.text_editor.toPlainText())
            self.configs_tab.sync_blocks_to_ui()
            
        if not self.configs_tab.blocks:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "No blocks to debug.")
            return
            
        self.log_message("[DEBUGGER] Initializing SeleniumEngine...")
        
        # Setup settings dictionary
        settings = {
            "always_open": self.configs_tab.opt_always_open.isChecked(),
            "always_quit": self.configs_tab.opt_always_quit.isChecked(),
            "quit_on_ban_retry": self.configs_tab.opt_quit_ban_retry.isChecked(),
            "headless": self.configs_tab.opt_headless.isChecked(),
            "disable_notifications": self.configs_tab.opt_disable_notifications.isChecked(),
            "custom_args": self.configs_tab.opt_custom_args.text(),
            "user_agent": self.configs_tab.opt_user_agent.text(),
            "use_random_ua": self.configs_tab.opt_random_ua.isChecked(),
            "max_cpm": self.configs_tab.opt_gen_max_cpm.value(),
            "save_empty_captures": self.configs_tab.opt_gen_empty_caps.isChecked(),
            "continue_custom": self.configs_tab.opt_gen_continue_custom.isChecked(),
            "save_hits_to_file": self.configs_tab.opt_gen_save_to_file.isChecked(),
            "use_selenium": self.configs_tab.opt_use_selenium.isChecked(),
            "proxy_settings": {
                "needs_proxies": (self.cb_proxy_status.currentText() == "Proxy: ON"),
                "only_socks": (self.cb_proxy_type.currentText() != "Http"),
                "only_ssl": False,
                "ban_after_good": self.configs_tab.opt_prox_ban_after_good.isChecked(),
                "max_uses": self.configs_tab.opt_prox_max_uses.value(),
                "ban_loop": self.configs_tab.opt_prox_ban_loop.value()
            },
            "data_settings": {
                "allowed_wl_type": self.cb_data_type.currentText(),
                "urlencode": self.configs_tab.opt_data_urlencode.isChecked()
            }
        }
        
        working_proxies = [p for p in self.configs_tab.proxies_tab.proxies if p['status'] == "Working"]
        
        # Get and parse test data line
        test_line = self.txt_test_data.text().strip()
        wl_type = self.cb_data_type.currentText()
        wl_format = self.configs_tab.opt_data_custom_format.text().strip() if wl_type == "Custom" else None
        
        # Default fallbacks if empty
        if not test_line:
            if wl_type == "Custom":
                test_line = "zannko.hatam@gmail.com:Zanko1234"
            elif wl_type in ["Credentials", "Email", "Default"]:
                test_line = "zannko.hatam@gmail.com:Zanko1234"
            elif wl_type == "Card":
                test_line = "4111222233334444:12/28:123"
            elif wl_type == "Numeric":
                test_line = "123456789"
            elif wl_type == "URLs":
                test_line = "https://example.com"
            else:
                test_line = "test"
                
        from utils.helpers import parse_wordlist_line
        parsed_vars = parse_wordlist_line(test_line, wl_type, wl_format)
        
        self.engine = SeleniumEngine(
            self.configs_tab.blocks, 
            settings, 
            variables_input=parsed_vars,
            proxies=working_proxies
        )
        
        self.engine.log_signal.connect(self.log_message)
        self.engine.html_signal.connect(self.dbg_html.setPlainText)
        self.engine.state_signal.connect(self.on_engine_block_state)
        self.engine.variables_signal.connect(self.on_dbg_variables_updated)
        self.engine.finished_signal.connect(self.on_engine_finished)
        
        # SBS handler setup
        if self.chk_sbs.isChecked():
            # Connect sequence step to pause engine after each block execution
            self.engine.state_signal.connect(self.on_block_executed_sbs)
            
        self.btn_start.setText("Stop")
        self.btn_start.setStyleSheet("background-color: #c62828;")
        
        self.engine.start()

    def on_block_executed_sbs(self, index, state):
        if state == "COMPLETED" or state == "FAILED":
            if self.engine and self.engine.isRunning() and self.chk_sbs.isChecked():
                self.engine.pause_execution()

    def log_message(self, msg):
        self.dbg_logs.appendPlainText(msg)

    def on_engine_block_state(self, index, state):
        if index < self.configs_tab.blocks_list.count():
            item = self.configs_tab.blocks_list.item(index)
            if state == "RUNNING":
                item.setBackground(QColor("#ffb74d"))
                self.configs_tab.blocks_list.setCurrentRow(index)
            elif state == "COMPLETED":
                item.setBackground(QColor("#81c784"))
            elif state == "FAILED":
                item.setBackground(QColor("#e57373"))

    def on_engine_finished(self, success, message):
        self.log_message(f"[DEBUGGER] Engine execution complete. Status: {'Success' if success else 'Failed'} - {message}")
        self.btn_start.setText("Start")
        self.btn_start.setStyleSheet("background-color: #2e7d32;")
        
        for i in range(self.configs_tab.blocks_list.count()):
            self.configs_tab.blocks_list.item(i).setBackground(QColor("transparent"))
        self.engine = None

    def on_dbg_variables_updated(self, variables):
        self.dbg_data_table.setRowCount(0)
        for k, v in variables.items():
            if k.startswith("<") and k.endswith(">"):
                continue
            row = self.dbg_data_table.rowCount()
            self.dbg_data_table.insertRow(row)
            
            val_str = str(v)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            
            self.dbg_data_table.setItem(row, 0, QTableWidgetItem(str(k)))
            self.dbg_data_table.setItem(row, 1, QTableWidgetItem(val_str))
            self.dbg_data_table.setItem(row, 2, QTableWidgetItem("Variable"))

    def cleanup(self):
        if self.engine and self.engine.isRunning():
            self.engine.stop_execution()
            self.engine.wait()

    def find_in_html(self, backward=False):
        query = self.txt_search_html.text()
        if not query:
            self.lbl_search_status.setText("")
            return
            
        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindFlag.FindBackward
            
        # Try to find next/prev match
        found = self.dbg_html.find(query, flags)
        
        # Wrap around logic if not found
        if not found:
            cursor = self.dbg_html.textCursor()
            if backward:
                cursor.movePosition(cursor.MoveOperation.End)
            else:
                cursor.movePosition(cursor.MoveOperation.Start)
            self.dbg_html.setTextCursor(cursor)
            
            # Try finding again
            found = self.dbg_html.find(query, flags)
            
        if found:
            self.lbl_search_status.setText("Found")
            self.lbl_search_status.setStyleSheet("color: #81c784;")
        else:
            self.lbl_search_status.setText("Not Found")
            self.lbl_search_status.setStyleSheet("color: #e57373;")

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QGroupBox
from utils.helpers import kill_chromedrivers, kill_chrome_browsers, delete_chrome_profiles

class SeleniumUtilitiesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Utilities Actions Group
        actions_group = QGroupBox("System Cleanup Tools")
        actions_layout = QHBoxLayout()
        
        self.btn_kill_drivers = QPushButton("Kill Chromedrivers")
        self.btn_kill_drivers.clicked.connect(self.on_kill_drivers)
        actions_layout.addWidget(self.btn_kill_drivers)
        
        self.btn_kill_chrome = QPushButton("Kill ALL Chrome Browsers")
        self.btn_kill_chrome.clicked.connect(self.on_kill_chrome)
        actions_layout.addWidget(self.btn_kill_chrome)
        
        self.btn_clean_cache = QPushButton("Delete Chrome Cache Folders")
        self.btn_clean_cache.clicked.connect(self.on_clean_cache)
        actions_layout.addWidget(self.btn_clean_cache)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Log Output Area
        log_group = QGroupBox("Action Output Logs")
        log_layout = QVBoxLayout()
        
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setPlaceholderText("Output logs from running utilities will be shown here...")
        log_layout.addWidget(self.txt_logs)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
    def log(self, message: str):
        self.txt_logs.append(message)
        
    def on_kill_drivers(self):
        self.log("[ACTION] Running: Kill Chromedrivers...")
        result = kill_chromedrivers()
        self.log(result)
        
    def on_kill_chrome(self):
        self.log("[ACTION] Running: Kill ALL Chrome Browsers...")
        result = kill_chrome_browsers()
        self.log(result)
        
    def on_clean_cache(self):
        self.log("[ACTION] Running: Delete Chrome Cache Folders...")
        base_dir = os.getcwd()
        result = delete_chrome_profiles(base_dir)
        self.log(result)

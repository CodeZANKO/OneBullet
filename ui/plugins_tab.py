from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class PluginsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_title = QLabel("Default Plugins Set")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00e5ff;")
        layout.addWidget(lbl_title)
        
        lbl_desc = QLabel("These plugins are loaded dynamically into the One Script execution framework.")
        lbl_desc.setStyleSheet("color: #90a4ae;")
        layout.addWidget(lbl_desc)
        
        # Plugins Table
        self.table = QTableWidget(3, 4)
        self.table.setHorizontalHeaderLabels(["Plugin Name", "Version", "Author", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0b0f19;
                border: 1px solid #1c273a;
                gridline-color: #1c273a;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #0d121a;
                color: #00e5ff;
                padding: 6px;
                border: 1px solid #1c273a;
                font-weight: bold;
            }
        """)
        
        plugins = [
            ("Selenium WebDriver Ext", "1.0.0", "One Bullet Dev Team", "Active"),
            ("Cloudflare Bypass Solver", "1.1.2", "One Bullet Dev Team", "Active"),
            ("TCP/IP Connection Socket", "1.0.0", "One Bullet Dev Team", "Active")
        ]
        
        for row, (name, ver, author, status) in enumerate(plugins):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(ver))
            self.table.setItem(row, 2, QTableWidgetItem(author))
            self.table.setItem(row, 3, QTableWidgetItem(status))
            
        layout.addWidget(self.table)

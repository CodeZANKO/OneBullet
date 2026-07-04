import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QLabel, QLineEdit,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

class HitsDbTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_file = os.path.join(os.getcwd(), "hits.json")
        self.hits = []
        self.init_ui()
        self.load_hits()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        # Header Card
        header_card = QFrame()
        header_card.setObjectName("ContainmentCard")
        header_card.setStyleSheet("QFrame#ContainmentCard { background-color: #151b27; border: 1px solid #1c273a; border-radius: 8px; }")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_title = QLabel("Hits Database Manager")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00e5ff;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_hits)
        header_layout.addWidget(self.btn_refresh)
        
        self.btn_delete_selected = QPushButton("Delete Selected")
        self.btn_delete_selected.setStyleSheet("background-color: #cf6679; color: white;")
        self.btn_delete_selected.clicked.connect(self.on_delete_selected)
        header_layout.addWidget(self.btn_delete_selected)
        
        self.btn_clear_all = QPushButton("Clear Database")
        self.btn_clear_all.setStyleSheet("background-color: #b00020; color: white;")
        self.btn_clear_all.clicked.connect(self.on_clear_all)
        header_layout.addWidget(self.btn_clear_all)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search hits...")
        self.txt_search.textChanged.connect(self.filter_hits)
        self.txt_search.setFixedWidth(250)
        header_layout.addWidget(self.txt_search)
        
        layout.addWidget(header_card)
        
        # Main Table Card
        table_card = QFrame()
        table_card.setObjectName("TableCard")
        table_card.setStyleSheet("QFrame#TableCard { background-color: #151b27; border: 1px solid #1c273a; border-radius: 8px; }")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Config", "Data", "Variables"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("border: none; background-color: transparent;")
        table_layout.addWidget(self.table)
        
        layout.addWidget(table_card)
        
    def load_hits(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.hits = json.load(f)
            except Exception:
                self.hits = []
        else:
            self.hits = []
            
        self.populate_table()
        
    def populate_table(self):
        self.table.setRowCount(0)
        for h in self.hits:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Use non-editable cells
            item_ts = QTableWidgetItem(h.get("timestamp", "-"))
            item_cfg = QTableWidgetItem(h.get("config", "-"))
            item_data = QTableWidgetItem(h.get("data", "-"))
            item_vars = QTableWidgetItem(h.get("variables", "-"))
            
            # Neon highlight for config name
            item_cfg.setForeground(Qt.GlobalColor.cyan)
            
            for item in [item_ts, item_cfg, item_data, item_vars]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
            self.table.setItem(row, 0, item_ts)
            self.table.setItem(row, 1, item_cfg)
            self.table.setItem(row, 2, item_data)
            self.table.setItem(row, 3, item_vars)
            
    def on_delete_selected(self):
        selected_rows = sorted(list(set(idx.row() for idx in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select at least one row to delete.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete the {len(selected_rows)} selected hit(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        for row in selected_rows:
            self.hits.pop(row)
            self.table.removeRow(row)
            
        self.save_hits()
        
    def on_clear_all(self):
        if not self.hits:
            return
        confirm = QMessageBox.question(
            self, "Confirm Clear", "Are you sure you want to delete ALL hits from the database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        self.hits.clear()
        self.table.setRowCount(0)
        self.save_hits()
        
    def save_hits(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.hits, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save database: {str(e)}")
            
    def filter_hits(self):
        query = self.txt_search.text().lower()
        for r in range(self.table.rowCount()):
            ts = self.table.item(r, 0).text().lower() if self.table.item(r, 0) else ""
            cfg = self.table.item(r, 1).text().lower() if self.table.item(r, 1) else ""
            data = self.table.item(r, 2).text().lower() if self.table.item(r, 2) else ""
            match = query in ts or query in cfg or query in data
            self.table.setRowHidden(r, not match)

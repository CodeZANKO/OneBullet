import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QLabel, QLineEdit, 
    QFileDialog, QMessageBox, QInputDialog, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class WordlistsTab(QWidget):
    # Signal emitted when wordlists are modified, so Runner widgets can reload
    wordlists_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_file = os.path.join(os.getcwd(), "wordlists.json")
        self.wordlists = [] # List of dicts: {name, path, type, purpose, total}
        
        self.init_ui()
        self.load_from_db()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Action controls top bar
        controls_group = QGroupBox("Wordlist Manager Controls")
        controls_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Add Wordlist")
        self.btn_add.clicked.connect(self.on_add_wordlist)
        controls_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.clicked.connect(self.on_delete)
        controls_layout.addWidget(self.btn_delete)
        
        self.btn_delete_all = QPushButton("Delete All")
        self.btn_delete_all.clicked.connect(self.on_delete_all)
        controls_layout.addWidget(self.btn_delete_all)
        
        self.btn_delete_missing = QPushButton("Delete Not Found")
        self.btn_delete_missing.clicked.connect(self.on_delete_missing)
        controls_layout.addWidget(self.btn_delete_missing)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search wordlists...")
        self.txt_search.textChanged.connect(self.filter_wordlists)
        controls_layout.addWidget(self.txt_search)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Table Grid Layout
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Name", "Path", "Type", "Purpose", "Total Entries"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
    def load_from_db(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.wordlists = json.load(f)
                self.populate_table()
            except Exception:
                pass

    def save_to_db(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.wordlists, f, indent=4)
        except Exception:
            pass
        self.wordlists_changed.emit()

    def populate_table(self):
        self.table.setRowCount(0)
        for wl in self.wordlists:
            self.add_row_to_table(wl)

    def add_row_to_table(self, wl: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(wl["name"]))
        self.table.setItem(row, 1, QTableWidgetItem(wl["path"]))
        self.table.setItem(row, 2, QTableWidgetItem(wl["type"]))
        self.table.setItem(row, 3, QTableWidgetItem(wl["purpose"]))
        self.table.setItem(row, 4, QTableWidgetItem(str(wl["total"])))

    def on_add_wordlist(self):
        # Open file browser to select wordlist target text file
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Wordlist File", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Select Wordlist properties
        w_name, ok = QInputDialog.getText(self, "Wordlist Name", "Enter Wordlist Name:", QLineEdit.EchoMode.Normal, name)
        if not ok or not w_name.strip():
            return
            
        w_type, ok = QInputDialog.getItem(
            self, "Wordlist Type", "Select type:", 
            ["Default", "Credentials", "Card", "Numeric", "URLs", "Extended"], 0, False
        )
        if not ok:
            return
            
        w_purpose, ok = QInputDialog.getText(self, "Wordlist Purpose", "Enter purpose (e.g. Brute forcing):")
        if not ok:
            w_purpose = "Testing"
            
        # Count lines
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
            total = len(lines)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to count lines: {str(e)}")
            return
            
        self.add_wordlist_record(w_name.strip(), file_path, w_type, w_purpose, total)
        QMessageBox.information(self, "Success", f"Wordlist '{w_name}' added successfully with {total} entries.")

    def add_wordlist_record(self, name: str, path: str, w_type: str, purpose: str, total: int):
        record = {
            "name": name,
            "path": path,
            "type": w_type,
            "purpose": purpose,
            "total": total
        }
        self.wordlists.append(record)
        self.add_row_to_table(record)
        self.save_to_db()

    def on_delete(self):
        selected_rows = sorted(list(set(idx.row() for idx in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Select a row to delete.")
            return
            
        for row in selected_rows:
            self.table.removeRow(row)
            self.wordlists.pop(row)
            
        self.save_to_db()

    def on_delete_all(self):
        confirm = QMessageBox.question(
            self, "Confirm Delete All", "Are you sure you want to clear all wordlists references?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.wordlists.clear()
            self.table.setRowCount(0)
            self.save_to_db()

    def on_delete_missing(self):
        # Checks if wordlist file exists on disk, deletes if missing
        missing_count = 0
        retained = []
        for wl in self.wordlists:
            if os.path.exists(wl["path"]):
                retained.append(wl)
            else:
                missing_count += 1
                
        if missing_count == 0:
            QMessageBox.information(self, "Status", "All wordlists are present on disk.")
            return
            
        self.wordlists = retained
        self.populate_table()
        self.save_to_db()
        QMessageBox.information(self, "Deleted", f"Removed {missing_count} wordlists references because files no longer exist.")

    def filter_wordlists(self):
        query = self.txt_search.text().lower()
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text().lower()
            wtype = self.table.item(r, 2).text().lower()
            match = query in name or query in wtype
            self.table.setRowHidden(r, not match)

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QLabel, QLineEdit, 
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class AddWordlistDialog(QDialog):
    def __init__(self, default_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Wordlist")
        self.resize(500, 320)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form_layout = QFormLayout()
        
        self.txt_name = QLineEdit(default_name)
        form_layout.addRow("Wordlist Name:", self.txt_name)
        
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Default", "Credentials", "Card", "Numeric", "URLs", "Extended", "Custom"])
        form_layout.addRow("Wordlist Type:", self.cb_type)
        
        # Custom format section
        self.custom_format_widget = QWidget()
        custom_format_layout = QVBoxLayout()
        custom_format_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_format_widget.setLayout(custom_format_layout)
        
        self.txt_format = QLineEdit()
        self.txt_format.setPlaceholderText("<NAME>:<EMAIL>:<PASSWORD>:<DD>/<MM>/<YYYY>")
        custom_format_layout.addWidget(QLabel("Custom Format Pattern:"))
        custom_format_layout.addWidget(self.txt_format)
        
        # Preset buttons
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        
        btn_email_pass = QPushButton("EMAIL:PASS")
        btn_email_pass.setToolTip("Sets format to <EMAIL>:<PASSWORD>")
        btn_email_pass.clicked.connect(lambda: self.txt_format.setText("<EMAIL>:<PASSWORD>"))
        presets_layout.addWidget(btn_email_pass)
        
        btn_phone = QPushButton("PHONE")
        btn_phone.setToolTip("Sets format to <PHONE>")
        btn_phone.clicked.connect(lambda: self.txt_format.setText("<PHONE>"))
        presets_layout.addWidget(btn_phone)
        
        btn_cc = QPushButton("CCNUM:MM/YY:CVV")
        btn_cc.setToolTip("Sets format to <CCNUM>:<MM>/<YY>:<CVV>")
        btn_cc.clicked.connect(lambda: self.txt_format.setText("<CCNUM>:<MM>/<YY>:<CVV>"))
        presets_layout.addWidget(btn_cc)
        
        btn_urls = QPushButton("URLs")
        btn_urls.setToolTip("Sets format to <URL>")
        btn_urls.clicked.connect(lambda: self.txt_format.setText("<URL>"))
        presets_layout.addWidget(btn_urls)
        
        custom_format_layout.addLayout(presets_layout)
        
        # Styling presets
        button_style = """
            QPushButton {
                background-color: #232f44;
                color: #00e5ff;
                border: 1px solid #1c273a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1e283d;
                border-color: #00e5ff;
            }
            QPushButton:pressed {
                background-color: #00e5ff;
                color: #080b11;
            }
        """
        btn_email_pass.setStyleSheet(button_style)
        btn_phone.setStyleSheet(button_style)
        btn_cc.setStyleSheet(button_style)
        btn_urls.setStyleSheet(button_style)
        
        form_layout.addRow(self.custom_format_widget)
        self.custom_format_widget.hide()
        
        self.cb_type.currentTextChanged.connect(self.on_type_changed)
        
        self.txt_purpose = QLineEdit("Testing")
        form_layout.addRow("Purpose:", self.txt_purpose)
        
        layout.addLayout(form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def on_type_changed(self, text):
        if text == "Custom":
            self.custom_format_widget.show()
            self.adjustSize()
        else:
            self.custom_format_widget.hide()
            self.adjustSize()
            
    def get_values(self):
        return {
            "name": self.txt_name.text().strip(),
            "type": self.cb_type.currentText(),
            "format": self.txt_format.text().strip() if self.cb_type.currentText() == "Custom" else "",
            "purpose": self.txt_purpose.text().strip()
        }

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
        
        display_type = wl["type"]
        if wl["type"] == "Custom" and "format" in wl:
            display_type = f"Custom ({wl['format']})"
            
        self.table.setItem(row, 2, QTableWidgetItem(display_type))
        self.table.setItem(row, 3, QTableWidgetItem(wl["purpose"]))
        self.table.setItem(row, 4, QTableWidgetItem(str(wl["total"])))

    def on_add_wordlist(self):
        # Open file browser to select wordlist target text file
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Wordlist File", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        default_name = os.path.splitext(os.path.basename(file_path))[0]
        
        dialog = AddWordlistDialog(default_name, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
            
        values = dialog.get_values()
        w_name = values["name"]
        w_type = values["type"]
        w_format = values["format"]
        w_purpose = values["purpose"]
        
        if not w_name:
            QMessageBox.warning(self, "Warning", "Wordlist name cannot be empty.")
            return
            
        if w_type == "Custom" and not w_format:
            QMessageBox.warning(self, "Warning", "Custom format cannot be empty.")
            return
            
        # Count lines
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.read().splitlines()
            total = len(lines)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to count lines: {str(e)}")
            return
            
        self.add_wordlist_record(w_name, file_path, w_type, w_purpose, total, w_format)
        QMessageBox.information(self, "Success", f"Wordlist '{w_name}' added successfully with {total} entries.")

    def add_wordlist_record(self, name: str, path: str, w_type: str, purpose: str, total: int, w_format: str = ""):
        record = {
            "name": name,
            "path": path,
            "type": w_type,
            "purpose": purpose,
            "total": total
        }
        if w_type == "Custom" and w_format:
            record["format"] = w_format
            
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

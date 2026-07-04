import os
import json
import itertools
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QLabel, QLineEdit, QCheckBox, QFileDialog, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt

def is_luhn_valid(n_str: str) -> bool:
    """Verifies credit card or numeric digits using the Luhn Algorithm."""
    digits = [int(c) for c in n_str if c.isdigit()]
    if not digits:
        return False
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(divmod(d * 2, 10))
    return checksum % 10 == 0


class ToolsTab(QWidget):
    def __init__(self, wordlists_tab, parent=None):
        super().__init__(parent)
        self.wordlists_tab = wordlists_tab
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tools Sub-Tabs
        self.sub_tabs = QTabWidget()
        layout.addWidget(self.sub_tabs)
        
        # Tab 1: List Generator
        self.init_generator_tab()
        
        # Tab 2: Selenium Tools (System info utility placeholders)
        self.init_selenium_tools_tab()
        
        # Tab 3: Database View (Displaying Hits)
        self.init_database_tab()
        
    def init_generator_tab(self):
        tab_widget = QWidget()
        lay = QVBoxLayout(tab_widget)
        
        form_group = QGroupBox("List Generator Parameters")
        form_layout = QFormLayout()
        
        # Mask
        self.txt_mask = QLineEdit("657438923467423847****:**")
        self.txt_mask.textChanged.connect(self.update_stats)
        form_layout.addRow(QLabel("Mask (use '*' for wild characters):"), self.txt_mask)
        
        # Allowed Chars
        self.txt_allowed = QLineEdit("0123456789")
        self.txt_allowed.textChanged.connect(self.update_stats)
        form_layout.addRow(QLabel("Allowed Characters:"), self.txt_allowed)
        
        # Quick Add Characters Layout
        quick_layout = QHBoxLayout()
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(lambda: self.txt_allowed.setText(""))
        btn_digits = QPushButton("Digits (0-9)")
        btn_digits.clicked.connect(lambda: self.txt_allowed.setText(self.txt_allowed.text() + "0123456789"))
        btn_lower = QPushButton("Lowercase (a-z)")
        btn_lower.clicked.connect(lambda: self.txt_allowed.setText(self.txt_allowed.text() + "abcdefghijklmnopqrstuvwxyz"))
        btn_upper = QPushButton("Uppercase (A-Z)")
        btn_upper.clicked.connect(lambda: self.txt_allowed.setText(self.txt_allowed.text() + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        
        quick_layout.addWidget(btn_clear)
        quick_layout.addWidget(btn_digits)
        quick_layout.addWidget(btn_lower)
        quick_layout.addWidget(btn_upper)
        form_layout.addRow(QLabel("Quick Presets:"), quick_layout)
        
        # Config options
        self.chk_luhn = QCheckBox("Only output Luhn-valid numbers")
        self.chk_luhn.stateChanged.connect(self.update_stats)
        form_layout.addRow(self.chk_luhn)
        
        self.chk_auto_add = QCheckBox("Automatically Add to Wordlist Manager")
        self.chk_auto_add.setChecked(True)
        form_layout.addRow(self.chk_auto_add)
        
        # Statistics Labels
        self.lbl_exp_lines = QLabel("Expected Number of Lines: 100")
        self.lbl_exp_size = QLabel("Expected FileSize: ~2.5 KB")
        form_layout.addRow(self.lbl_exp_lines)
        form_layout.addRow(self.lbl_exp_size)
        
        form_group.setLayout(form_layout)
        lay.addWidget(form_group)
        
        # Generate Action button
        self.btn_generate = QPushButton("Generate List")
        self.btn_generate.setStyleSheet("background-color: #f57c00; font-weight: bold; color: white; padding: 12px;")
        self.btn_generate.clicked.connect(self.on_generate)
        lay.addWidget(self.btn_generate)
        
        lay.addStretch()
        self.sub_tabs.addTab(tab_widget, "List Generator")
        self.update_stats()

    def init_selenium_tools_tab(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        
        box = QGroupBox("Helper Utilities")
        box_lay = QVBoxLayout()
        
        box_lay.addWidget(QLabel("This tab provides system-wide developer automation checks and controls."))
        box_lay.addWidget(QLabel("- Check ChromeDriver compatibility versions."))
        box_lay.addWidget(QLabel("- Delete isolated temp workspace cache browser user dirs."))
        box_lay.addWidget(QLabel("- View background chrome thread logs."))
        
        box.setLayout(box_lay)
        lay.addWidget(box)
        lay.addStretch()
        
        self.sub_tabs.addTab(widget, "Selenium Tools")

    def init_database_tab(self):
        widget = QWidget()
        lay = QVBoxLayout(widget)
        
        box = QGroupBox("Captured Success Hits Database")
        box_lay = QVBoxLayout()
        
        self.btn_refresh_db = QPushButton("Refresh Hits Database")
        self.btn_refresh_db.clicked.connect(self.refresh_database_table)
        box_lay.addWidget(self.btn_refresh_db)
        
        self.db_table = QTableWidget(0, 4)
        self.db_table.setHorizontalHeaderLabels(["Timestamp", "Config Name", "Output Data Check", "Variables Log"])
        self.db_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        box_lay.addWidget(self.db_table)
        
        box.setLayout(box_lay)
        lay.addWidget(box)
        
        self.sub_tabs.addTab(widget, "Database Viewer")
        self.refresh_database_table()

    def refresh_database_table(self):
        self.db_table.setRowCount(0)
        hits_file = os.path.join(os.getcwd(), "hits.json")
        if os.path.exists(hits_file):
            try:
                with open(hits_file, "r", encoding="utf-8") as f:
                    hits = json.load(f)
                for h in hits:
                    row = self.db_table.rowCount()
                    self.db_table.insertRow(row)
                    self.db_table.setItem(row, 0, QTableWidgetItem(h.get("timestamp", "")))
                    self.db_table.setItem(row, 1, QTableWidgetItem(h.get("config", "")))
                    self.db_table.setItem(row, 2, QTableWidgetItem(h.get("data", "")))
                    self.db_table.setItem(row, 3, QTableWidgetItem(str(h.get("variables", ""))))
            except Exception:
                pass

    def get_wildcard_combinations_count(self) -> int:
        mask = self.txt_mask.text()
        allowed = self.txt_allowed.text()
        wildcards = mask.count('*')
        if not allowed:
            return 0
        return len(allowed) ** wildcards

    def update_stats(self):
        lines = self.get_wildcard_combinations_count()
        mask_len = len(self.txt_mask.text())
        
        # Estimate size (chars + newline character)
        size_bytes = lines * (mask_len + 1)
        size_kb = size_bytes / 1024.0
        
        if size_kb > 1024:
            size_str = f"{size_kb/1024.0:.2f} MB"
        else:
            size_str = f"{size_kb:.2f} KB"
            
        self.lbl_exp_lines.setText(f"Expected Number of Lines: {lines:,}")
        self.lbl_exp_size.setText(f"Expected FileSize: ~{size_str}")

    def on_generate(self):
        mask = self.txt_mask.text()
        allowed = self.txt_allowed.text()
        lines = self.get_wildcard_combinations_count()
        
        if not allowed:
            QMessageBox.warning(self, "Warning", "Allowed Characters cannot be empty.")
            return
            
        if lines == 0:
            QMessageBox.warning(self, "Warning", "No wild characters '*' found in Mask.")
            return
            
        if lines > 2000000:
            confirm = QMessageBox.question(
                self, "Confirm Large List", 
                f"Generating {lines:,} lines might freeze the interface for a moment. Do you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
                
        # Ask where to save generated list file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Generated List", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        # Run generator
        wildcards_count = mask.count('*')
        combinations = itertools.product(allowed, repeat=wildcards_count)
        
        luhn_check = self.chk_luhn.isChecked()
        count = 0
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for comb in combinations:
                    temp = mask
                    for char in comb:
                        temp = temp.replace('*', char, 1)
                    
                    if luhn_check:
                        if is_luhn_valid(temp):
                            f.write(temp + "\n")
                            count += 1
                    else:
                        f.write(temp + "\n")
                        count += 1
                        
            QMessageBox.information(self, "Success", f"Successfully generated {count:,} lines to {os.path.basename(file_path)}.")
            
            # Automatically add generated wordlist to wordlist manager
            if self.chk_auto_add.isChecked():
                wl_name = os.path.splitext(os.path.basename(file_path))[0]
                self.wordlists_tab.add_wordlist_record(wl_name, file_path, "Numeric Mask", "Generated", count)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate: {str(e)}")

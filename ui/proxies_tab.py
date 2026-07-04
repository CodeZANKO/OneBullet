import time
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QLabel, QLineEdit, 
    QSpinBox, QComboBox, QFileDialog, QMessageBox, QInputDialog
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

def test_proxy(proxy_dict: dict, test_url: str, timeout: int, success_key: str) -> tuple[bool, int]:
    """Tests a single proxy and returns a tuple (success: bool, ping_ms: int)."""
    ptype = proxy_dict['type'].lower()
    host = proxy_dict['host']
    port = proxy_dict['port']
    user = proxy_dict.get('username', '')
    password = proxy_dict.get('password', '')
    
    auth_part = ""
    if user and password:
        auth_part = f"{user}:{password}@"
        
    proxy_url = f"{ptype}://{auth_part}{host}:{port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    start_time = time.time()
    try:
        r = requests.get(test_url, proxies=proxies, timeout=timeout, allow_redirects=True)
        elapsed = int((time.time() - start_time) * 1000)
        if success_key:
            if success_key in r.text:
                return True, elapsed
            else:
                return False, elapsed
        return r.status_code == 200, elapsed
    except Exception:
        return False, -1


class ProxyCheckWorker(QThread):
    """Worker thread that executes a proxy test and reports back."""
    result_signal = pyqtSignal(int, bool, int) # index, success, ping
    
    def __init__(self, index: int, proxy_dict: dict, test_url: str, timeout: int, success_key: str):
        super().__init__()
        self.index = index
        self.proxy_dict = proxy_dict
        self.test_url = test_url
        self.timeout = timeout
        self.success_key = success_key
        
    def run(self):
        success, ping = test_proxy(self.proxy_dict, self.test_url, self.timeout, self.success_key)
        self.result_signal.emit(self.index, success, ping)


class ProxiesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxies = [] # List of dicts: {type, host, port, username, password, country, status, ping}
        self.active_workers = []
        self.check_queue = []
        self.is_checking = False
        
        # PERSISTENCE
        import os
        ui_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(ui_dir)
        self.db_file = os.path.join(self.project_dir, "proxies.json")
        
        self.init_ui()
        self.load_proxies_from_file()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Left Side: Controls & Table
        left_layout = QVBoxLayout()
        
        # Action Buttons & Input configs
        controls_group = QGroupBox("Proxy Controls")
        controls_layout = QHBoxLayout()
        
        self.btn_import = QPushButton("Import Proxies")
        self.btn_import.clicked.connect(self.on_import)
        controls_layout.addWidget(self.btn_import)
        
        self.btn_import_url = QPushButton("Import from URL")
        self.btn_import_url.clicked.connect(self.on_import_url)
        controls_layout.addWidget(self.btn_import_url)
        
        self.btn_export = QPushButton("Export Proxies")
        self.btn_export.clicked.connect(self.on_export)
        controls_layout.addWidget(self.btn_export)
        
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.clicked.connect(self.on_delete)
        controls_layout.addWidget(self.btn_delete)
        
        self.btn_check = QPushButton("CHECK Proxies")
        self.btn_check.clicked.connect(self.on_check_start)
        self.btn_check.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
        controls_layout.addWidget(self.btn_check)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)
        
        # Check Settings Group
        settings_group = QGroupBox("Check Settings")
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("Test URL:"))
        self.txt_test_url = QLineEdit("https://www.google.com")
        settings_layout.addWidget(self.txt_test_url)
        
        settings_layout.addWidget(QLabel("Key check:"))
        self.txt_key = QLineEdit("google")
        settings_layout.addWidget(self.txt_key)
        
        settings_layout.addWidget(QLabel("Timeout (s):"))
        self.spin_timeout = QSpinBox()
        self.spin_timeout.setRange(1, 30)
        self.spin_timeout.setValue(5)
        settings_layout.addWidget(self.spin_timeout)
        
        settings_layout.addWidget(QLabel("Threads:"))
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 100)
        self.spin_threads.setValue(10)
        settings_layout.addWidget(self.spin_threads)
        
        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group)
        
        # Proxy Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Type", "Host", "Port", "Username", "Password", "Country", "Status/Ping"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.table)
        
        main_layout.addLayout(left_layout, 4)
        
        # Right Side: Statistics Sidebar
        right_panel = QGroupBox("Proxy Statistics")
        right_layout = QVBoxLayout()
        
        self.lbl_total = QLabel("Total: 0")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.lbl_tested = QLabel("Tested: 0")
        self.lbl_tested.setStyleSheet("font-size: 14px;")
        self.lbl_working = QLabel("Working: 0")
        self.lbl_working.setStyleSheet("font-size: 14px; color: #81c784;")
        self.lbl_failed = QLabel("Not Working: 0")
        self.lbl_failed.setStyleSheet("font-size: 14px; color: #e57373;")
        
        right_layout.addWidget(self.lbl_total)
        right_layout.addWidget(self.lbl_tested)
        right_layout.addWidget(self.lbl_working)
        right_layout.addWidget(self.lbl_failed)
        right_layout.addStretch()
        
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 1)

    def update_stats(self):
        total = len(self.proxies)
        tested = sum(1 for p in self.proxies if p['status'] != "Untested")
        working = sum(1 for p in self.proxies if p['status'] == "Working")
        failed = sum(1 for p in self.proxies if p['status'] == "Failed")
        
        self.lbl_total.setText(f"Total: {total}")
        self.lbl_tested.setText(f"Tested: {tested}")
        self.lbl_working.setText(f"Working: {working}")
        self.lbl_failed.setText(f"Not Working: {failed}")

    def on_import(self):
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Proxies", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read proxy file: {str(e)}")
            return
            
        # Select proxy type default
        ptype, ok = QInputDialog.getItem(
            self, "Select Proxy Type", "Select the protocol of imported proxies:", 
            ["HTTP", "SOCKS5"], 0, False
        )
        if not ok:
            return
            
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Supported formats:
            # host:port
            # host:port:user:pass
            # user:pass@host:port
            proxy_info = {}
            if "@" in line:
                # user:pass@host:port
                try:
                    auth, conn = line.split("@", 1)
                    user, pwd = auth.split(":", 1)
                    host, port = conn.split(":", 1)
                    proxy_info = {"host": host, "port": port, "username": user, "password": pwd}
                except:
                    continue
            else:
                parts = line.split(":")
                if len(parts) == 2:
                    proxy_info = {"host": parts[0], "port": parts[1], "username": "", "password": ""}
                elif len(parts) == 4:
                    proxy_info = {"host": parts[0], "port": parts[1], "username": parts[2], "password": parts[3]}
                else:
                    continue
                    
            proxy_info["type"] = ptype
            proxy_info["country"] = "Unknown"
            proxy_info["status"] = "Untested"
            proxy_info["ping"] = -1
            
            self.proxies.append(proxy_info)
            self.add_proxy_to_table(proxy_info)
            count += 1
            
        self.update_stats()
        self.save_proxies_to_file()
        QMessageBox.information(self, "Success", f"Successfully imported {count} proxies.")

    def add_proxy_to_table(self, proxy):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(proxy["type"]))
        self.table.setItem(row, 1, QTableWidgetItem(proxy["host"]))
        self.table.setItem(row, 2, QTableWidgetItem(proxy["port"]))
        self.table.setItem(row, 3, QTableWidgetItem(proxy["username"]))
        self.table.setItem(row, 4, QTableWidgetItem(proxy["password"]))
        self.table.setItem(row, 5, QTableWidgetItem(proxy["country"]))
        
        status_item = QTableWidgetItem(proxy["status"])
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 6, status_item)

    def update_proxy_row(self, row, proxy):
        status = proxy["status"]
        ping = proxy["ping"]
        
        status_text = f"Working ({ping}ms)" if status == "Working" else "Failed"
        status_item = self.table.item(row, 6)
        if status_item:
            status_item.setText(status_text)
            if status == "Working":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.red)

    def on_export(self):
        if not self.proxies:
            QMessageBox.warning(self, "Warning", "No proxies to export.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Proxies", "", "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for p in self.proxies:
                    if p.get("username") and p.get("password"):
                        f.write(f"{p['host']}:{p['port']}:{p['username']}:{p['password']}\n")
                    else:
                        f.write(f"{p['host']}:{p['port']}\n")
            QMessageBox.information(self, "Success", "Proxies exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def on_delete(self):
        selected_rows = sorted(list(set(index.row() for index in self.table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select at least one row to delete.")
            return
            
        for row in selected_rows:
            self.table.removeRow(row)
            self.proxies.pop(row)
            
        self.update_stats()
        self.save_proxies_to_file()

    def on_check_start(self):
        if self.is_checking:
            # Stop checker
            self.is_checking = False
            self.check_queue.clear()
            for worker in self.active_workers:
                worker.terminate()
            self.active_workers.clear()
            self.btn_check.setText("CHECK Proxies")
            self.btn_check.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
            self.save_proxies_to_file()
            return
            
        if not self.proxies:
            QMessageBox.warning(self, "Warning", "No proxies loaded to check.")
            return
            
        self.is_checking = True
        self.btn_check.setText("STOP Check")
        self.btn_check.setStyleSheet("background-color: #c62828; font-weight: bold; color: white;")
        
        # Populate Queue
        self.check_queue = list(range(len(self.proxies)))
        
        # Reset Status in memory & table
        for i in range(len(self.proxies)):
            self.proxies[i]["status"] = "Untested"
            self.proxies[i]["ping"] = -1
            item = self.table.item(i, 6)
            if item:
                item.setText("Checking...")
                item.setForeground(Qt.GlobalColor.white)
                
        self.update_stats()
        
        # Spawn initial workers
        max_threads = self.spin_threads.value()
        for _ in range(min(max_threads, len(self.check_queue))):
            self.spawn_next_worker()

    def spawn_next_worker(self):
        if not self.is_checking or not self.check_queue:
            if not self.active_workers and self.is_checking:
                # Finished checking all
                self.is_checking = False
                self.btn_check.setText("CHECK Proxies")
                self.btn_check.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
                self.save_proxies_to_file()
                QMessageBox.information(self, "Success", "Proxy verification completed.")
            return
            
        idx = self.check_queue.pop(0)
        proxy = self.proxies[idx]
        
        worker = ProxyCheckWorker(
            idx, proxy, 
            self.txt_test_url.text(), 
            self.spin_timeout.value(), 
            self.txt_key.text()
        )
        worker.result_signal.connect(self.on_worker_result)
        worker.finished.connect(lambda: self.on_worker_finished(worker))
        
        self.active_workers.append(worker)
        worker.start()

    def on_worker_result(self, index, success, ping):
        if index < len(self.proxies):
            self.proxies[index]["status"] = "Working" if success else "Failed"
            self.proxies[index]["ping"] = ping
            self.update_proxy_row(index, self.proxies[index])
            self.update_stats()

    def on_worker_finished(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        self.spawn_next_worker()

    def cleanup(self):
        self.is_checking = False
        self.check_queue.clear()
        for worker in list(self.active_workers):
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        self.active_workers.clear()

    def save_proxies_to_file(self):
        import json
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.proxies, f, indent=4)
        except Exception as e:
            print("Failed to save proxies:", e)

    def load_proxies_from_file(self):
        import json
        import os
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.proxies = json.load(f)
                self.table.setRowCount(0)
                for p in self.proxies:
                    self.add_proxy_to_table(p)
                    row = self.table.rowCount() - 1
                    status = p.get("status", "Untested")
                    ping = p.get("ping", -1)
                    
                    status_text = f"Working ({ping}ms)" if status == "Working" else ("Failed" if status == "Failed" else "Untested")
                    status_item = self.table.item(row, 6)
                    if status_item:
                        status_item.setText(status_text)
                        if status == "Working":
                            status_item.setForeground(Qt.GlobalColor.green)
                        elif status == "Failed":
                            status_item.setForeground(Qt.GlobalColor.red)
                self.update_stats()
            except Exception as e:
                print("Failed to load proxies:", e)

    def on_import_url(self):
        url, ok = QInputDialog.getText(
            self, "Import from URL/API", "Enter proxy API/URL:", QLineEdit.EchoMode.Normal, ""
        )
        if not ok or not url.strip():
            return
            
        url = url.strip()
        try:
            self.lbl_total.setText("Fetching...")
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                QMessageBox.critical(self, "Error", f"Failed to fetch proxies. Server returned status code: {response.status_code}")
                self.update_stats()
                return
            lines = response.text.splitlines()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect/fetch: {str(e)}")
            self.update_stats()
            return
            
        # Select proxy type default
        ptype, ok = QInputDialog.getItem(
            self, "Select Proxy Type", "Select the protocol of imported proxies:", 
            ["HTTP", "SOCKS5"], 0, False
        )
        if not ok:
            self.update_stats()
            return
            
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            proxy_info = {}
            if "@" in line:
                try:
                    auth, conn = line.split("@", 1)
                    user, pwd = auth.split(":", 1)
                    host, port = conn.split(":", 1)
                    proxy_info = {"host": host, "port": port, "username": user, "password": pwd}
                except:
                    continue
            else:
                parts = line.split(":")
                if len(parts) == 2:
                    proxy_info = {"host": parts[0], "port": parts[1], "username": "", "password": ""}
                elif len(parts) == 4:
                    proxy_info = {"host": parts[0], "port": parts[1], "username": parts[2], "password": parts[3]}
                else:
                    continue
                    
            proxy_info["type"] = ptype
            proxy_info["country"] = "Unknown"
            proxy_info["status"] = "Untested"
            proxy_info["ping"] = -1
            
            self.proxies.append(proxy_info)
            self.add_proxy_to_table(proxy_info)
            count += 1
            
        self.update_stats()
        self.save_proxies_to_file()
        QMessageBox.information(self, "Success", f"Successfully imported {count} proxies from URL/API.")

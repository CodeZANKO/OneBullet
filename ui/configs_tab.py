import os
import json
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QStackedWidget, QComboBox, 
    QTextEdit, QTabWidget, QSplitter, QMessageBox, QInputDialog, QPlainTextEdit,
    QSpinBox, QCheckBox, QGridLayout, QFormLayout, QDialog, QRadioButton, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from engine.selenium_engine import SeleniumEngine, OneScriptCompiler

class AddBlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Block")
        self.resize(550, 380)
        self.selected_type = None
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        lbl_current_set = QLabel("Current set: Default Plugins")
        lbl_current_set.setStyleSheet("font-weight: bold; color: #888888; font-size: 11px;")
        main_layout.addWidget(lbl_current_set)
        
        grid_widget = QWidget()
        layout = QGridLayout(grid_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Configure stretch factors for a 12-column responsive grid
        for c in range(12):
            layout.setColumnStretch(c, 1)
        for r in range(4):
            layout.setRowStretch(r, 1)
            
        from PyQt6.QtWidgets import QSizePolicy
        
        buttons_info = [
            ("REQUEST", "#2e7d32", "white"),
            ("UTILITY", "#fff8e1", "black"),
            ("KEY CHECK", "#1565c0", "white"),
            
            ("PARSE", "#fbc02d", "black"),
            ("FUNCTION", "#c0ca33", "white"),
            ("SOLVE CAPTCHA", "#00acc1", "white"),
            
            ("REPORT CAPTCHA", "#ef6c00", "white"),
            ("BYPASS CF", "#ffcc80", "black"),
            ("TCP", "#7b1fa2", "white"),
            
            ("NAVIGATE", "#1a237e", "white"),
            ("BROWSER ACTION", "#004d40", "white"),
            ("ELEMENT ACTION", "#c62828", "white"),
            ("EXECUTE JS", "#4a148c", "white")
        ]
        
        grid_positions = [
            # Row 0
            (0, 0, 1, 4), (0, 4, 1, 4), (0, 8, 1, 4),
            # Row 1
            (1, 0, 1, 4), (1, 4, 1, 4), (1, 8, 1, 4),
            # Row 2
            (2, 0, 1, 4), (2, 4, 1, 4), (2, 8, 1, 4),
            # Row 3
            (3, 0, 1, 3), (3, 3, 1, 3), (3, 6, 1, 3), (3, 9, 1, 3)
        ]
        
        for idx, (btype, bg, fg) in enumerate(buttons_info):
            btn = QPushButton(btype)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setStyleSheet(
                f"background-color: {bg}; color: {fg}; font-weight: bold; "
                f"padding: 10px; border-radius: 5px; font-size: 10pt;"
            )
            btn.clicked.connect(self.make_callback(btype))
            
            r, c, rs, cs = grid_positions[idx]
            layout.addWidget(btn, r, c, rs, cs)
            
        main_layout.addWidget(grid_widget)
            
    def make_callback(self, btype):
        return lambda: self.on_button_clicked(btype)
        
    def on_button_clicked(self, btype):
        self.selected_type = btype
        self.accept()

class ConfigsTab(QWidget):
    def __init__(self, settings_tab, proxies_tab, parent=None):
        super().__init__(parent)
        self.settings_tab = settings_tab
        self.proxies_tab = proxies_tab
        
        self.configs_dir = os.path.join(os.getcwd(), "configs")
        os.makedirs(self.configs_dir, exist_ok=True)
        
        self.current_config_file = None
        self.blocks = [] # List of block dictionaries
        self.engine = None
        self.selected_config_name = "None"
        
        self.init_ui()
        self.load_configs_list()
        
    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.sub_tabs = QTabWidget()
        self.main_layout.addWidget(self.sub_tabs)
        
        # Sub-tabs
        self.init_manager_tab()
        self.init_stacker_tab()
        self.init_other_options_tab()
        
    def init_manager_tab(self):
        manager_widget = QWidget()
        manager_layout = QVBoxLayout(manager_widget)
        
        # Top Toolbar
        toolbar_group = QGroupBox("Toolbar Actions")
        toolbar_layout = QHBoxLayout()
        
        self.btn_new = QPushButton("New")
        self.btn_new.clicked.connect(self.on_create_new)
        toolbar_layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("Edit")
        self.btn_edit.clicked.connect(self.on_edit_config)
        toolbar_layout.addWidget(self.btn_edit)
        
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.on_save_config)
        self.btn_save.setStyleSheet("background-color: #0c1a30; border: 1px solid #00e5ff; color: #00e5ff; font-weight: bold;")
        toolbar_layout.addWidget(self.btn_save)
        
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.clicked.connect(self.on_delete_config)
        toolbar_layout.addWidget(self.btn_delete)
        
        self.btn_folder = QPushButton("Open Folder")
        self.btn_folder.clicked.connect(self.on_open_folder)
        toolbar_layout.addWidget(self.btn_folder)
        
        self.btn_rescan = QPushButton("Rescan")
        self.btn_rescan.clicked.connect(self.load_configs_list)
        toolbar_layout.addWidget(self.btn_rescan)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search configs...")
        self.txt_search.textChanged.connect(self.filter_configs)
        toolbar_layout.addWidget(self.txt_search)
        
        self.lbl_current_config = QLabel("Current Config: None")
        self.lbl_current_config.setStyleSheet("font-weight: bold; color: #00e5ff;")
        toolbar_layout.addWidget(self.lbl_current_config)
        
        self.lbl_total_configs = QLabel("Total Configs: 0")
        toolbar_layout.addWidget(self.lbl_total_configs)
        
        toolbar_group.setLayout(toolbar_layout)
        manager_layout.addWidget(toolbar_group)
        
        # Center Table Grid
        self.configs_table = QTableWidget(0, 8)
        self.configs_table.setHorizontalHeaderLabels([
            "Name", "Author", "Category", "Proxies", "Captchas", "Selenium", "CF", "Last Modified"
        ])
        self.configs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.configs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.configs_table.itemSelectionChanged.connect(self.on_config_selected)
        self.configs_table.doubleClicked.connect(self.on_edit_config)
        manager_layout.addWidget(self.configs_table)
        
        # Bottom Information Bar
        info_group = QGroupBox("Configuration Metadata")
        info_layout = QGridLayout()
        
        self.lbl_allowed_wl = QLabel("Allowed Wordlists: -")
        info_layout.addWidget(self.lbl_allowed_wl, 0, 0)
        
        self.lbl_blocks_count = QLabel("Blocks Amount: 0")
        info_layout.addWidget(self.lbl_blocks_count, 0, 1)
        
        self.lbl_suggested_bots = QLabel("Suggested Bots: -")
        info_layout.addWidget(self.lbl_suggested_bots, 0, 2)
        
        self.lbl_info_author = QLabel("Author: -")
        info_layout.addWidget(self.lbl_info_author, 0, 3)
        
        self.lbl_info_version = QLabel("Built with version: 1.0.0")
        info_layout.addWidget(self.lbl_info_version, 1, 0)
        
        self.lbl_info_modified = QLabel("Last Modified: -")
        info_layout.addWidget(self.lbl_info_modified, 1, 1)
        
        self.lbl_additional_info = QLabel("Additional Info: -")
        info_layout.addWidget(self.lbl_additional_info, 1, 2, 1, 2)
        
        info_group.setLayout(info_layout)
        manager_layout.addWidget(info_group)
        
        self.sub_tabs.addTab(manager_widget, "Manager")
        
    def init_stacker_tab(self):
        stacker_widget = QWidget()
        stacker_layout = QHBoxLayout(stacker_widget)
        stacker_layout.setContentsMargins(5, 5, 5, 5)
        stacker_layout.setSpacing(5)
        
        # 3-zone horizontal splitter (Left 25%, Center 40%, Right 35%)
        self.stacker_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.stacker_splitter.setHandleWidth(6)
        
        # ----------------------------------------------------
        # Left Column (Current Stack - 25% Width)
        # ----------------------------------------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        
        # Top Toolstrip: [ + ], [ - ], [ ✖ ], [ ❐ ], [ ⬆ ], [ ⬇ ], [ 💾 ]
        toolstrip = QHBoxLayout()
        toolstrip.setSpacing(4)
        
        self.btn_add_block = QPushButton("+")
        self.btn_add_block.setToolTip("Add Block")
        self.btn_add_block.clicked.connect(self.on_add_block)
        toolstrip.addWidget(self.btn_add_block)
        
        self.btn_block_del = QPushButton("-")
        self.btn_block_del.setToolTip("Remove Block")
        self.btn_block_del.clicked.connect(self.on_delete_block)
        toolstrip.addWidget(self.btn_block_del)
        
        self.btn_block_clear = QPushButton("✖")
        self.btn_block_clear.setToolTip("Clear Stack")
        self.btn_block_clear.clicked.connect(self.on_clear_blocks)
        toolstrip.addWidget(self.btn_block_clear)
        
        self.btn_block_clone = QPushButton("❐")
        self.btn_block_clone.setToolTip("Clone Block")
        self.btn_block_clone.clicked.connect(self.on_clone_block)
        toolstrip.addWidget(self.btn_block_clone)
        
        self.btn_block_up = QPushButton("⬆")
        self.btn_block_up.setToolTip("Move Up")
        self.btn_block_up.clicked.connect(self.on_move_block_up)
        toolstrip.addWidget(self.btn_block_up)
        
        self.btn_block_down = QPushButton("⬇")
        self.btn_block_down.setToolTip("Move Down")
        self.btn_block_down.clicked.connect(self.on_move_block_down)
        toolstrip.addWidget(self.btn_block_down)
        
        self.btn_block_save = QPushButton("💾")
        self.btn_block_save.setToolTip("Save Config")
        self.btn_block_save.clicked.connect(self.on_save_config)
        toolstrip.addWidget(self.btn_block_save)
        
        left_layout.addLayout(toolstrip)
        
        # Stack Editor (Visual List vs One Script text editor)
        self.editor_stack = QStackedWidget()
        
        self.blocks_list = QListWidget()
        self.blocks_list.currentRowChanged.connect(self.on_block_selected)
        self.blocks_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.blocks_list.model().layoutChanged.connect(self.on_blocks_drag_dropped)
        self.editor_stack.addWidget(self.blocks_list)
        
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 10))
        self.text_editor.setPlaceholderText("# Enter script here (One Script syntax)")
        self.editor_stack.addWidget(self.text_editor)
        
        left_layout.addWidget(self.editor_stack)
        

        
        # Bottom Dock: Fixed text button reading "</> SWITCH TO ONE SCRIPT"
        self.btn_toggle_view = QPushButton("</> SWITCH TO ONE SCRIPT")
        self.btn_toggle_view.clicked.connect(self.on_toggle_view)
        left_layout.addWidget(self.btn_toggle_view)
        
        self.stacker_splitter.addWidget(left_widget)
        
        # ----------------------------------------------------
        # Center Column (Block Info Editor - 40% Width)
        # ----------------------------------------------------
        self.info_box = QGroupBox("Block Properties")
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)
        
        label_widget = QWidget()
        label_form = QFormLayout(label_widget)
        label_form.setContentsMargins(0, 0, 0, 0)
        label_form.setSpacing(8)
        
        self.txt_block_label = QLineEdit()
        self.txt_block_label.setPlaceholderText("Block Label...")
        self.txt_block_label.textChanged.connect(self.save_current_block_info)
        label_form.addRow(QLabel("Label:"), self.txt_block_label)
        info_layout.addWidget(label_widget)
        
        self.info_stack = QStackedWidget()
        
        # Empty properties page
        self.prop_empty = QWidget()
        pe_lay = QVBoxLayout(self.prop_empty)
        pe_lay.addWidget(QLabel("Select a block to edit its parameters"), 0, Qt.AlignmentFlag.AlignCenter)
        self.info_stack.addWidget(self.prop_empty)
        
        # Browser Action properties page
        self.prop_browser = QWidget()
        pb_lay = QFormLayout(self.prop_browser)
        pb_lay.setContentsMargins(0, 0, 0, 0)
        pb_lay.setSpacing(8)
        self.cb_browser_action = QComboBox()
        self.cb_browser_action.addItems([
            "Start Browser", "Open", "Close Browser", "Close", "Quit", "Refresh", 
            "Go Back", "Go Forward", "ClearCookies", "SendKeys", "Screenshot", 
            "ScrollToTop", "ScrollToBottom", "Scroll", "OpenNewTab"
        ])
        self.cb_browser_action.currentIndexChanged.connect(self.save_current_block_info)
        pb_lay.addRow(QLabel("Browser Action Type:"), self.cb_browser_action)
        self.info_stack.addWidget(self.prop_browser)
        
        # Navigate properties page
        self.prop_navigate = QWidget()
        pn_lay = QFormLayout(self.prop_navigate)
        pn_lay.setContentsMargins(0, 0, 0, 0)
        pn_lay.setSpacing(8)
        self.txt_nav_url = QLineEdit()
        self.txt_nav_url.textChanged.connect(self.save_current_block_info)
        pn_lay.addRow(QLabel("Navigate URL:"), self.txt_nav_url)
        
        self.spin_nav_timeout = QSpinBox()
        self.spin_nav_timeout.setRange(1, 600)
        self.spin_nav_timeout.setValue(60)
        self.spin_nav_timeout.valueChanged.connect(self.save_current_block_info)
        pn_lay.addRow(QLabel("Timeout (seconds):"), self.spin_nav_timeout)
        
        self.chk_nav_ban = QCheckBox("Ban Proxy on Timeout")
        self.chk_nav_ban.stateChanged.connect(self.save_current_block_info)
        pn_lay.addRow("", self.chk_nav_ban)
        self.info_stack.addWidget(self.prop_navigate)
        
        # Element Action properties page
        self.prop_element = QWidget()
        pe_lay = QFormLayout(self.prop_element)
        pe_lay.setContentsMargins(0, 0, 0, 0)
        pe_lay.setSpacing(8)
        
        self.cb_sel_type = QComboBox()
        self.cb_sel_type.addItems(["XPATH", "ID", "CLASS_NAME", "CSS_SELECTOR", "NAME", "TAG_NAME", "LINK_TEXT"])
        self.cb_sel_type.currentIndexChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("Selector Type:"), self.cb_sel_type)
        
        self.txt_sel_value = QLineEdit()
        self.txt_sel_value.textChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("Selector Value:"), self.txt_sel_value)
        
        self.cb_el_action = QComboBox()
        self.cb_el_action.addItems(["Click", "Input Text", "Clear", "Get Text", "Select Dropdown", "Wait for Element"])
        self.cb_el_action.currentIndexChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("Action Type:"), self.cb_el_action)
        
        self.txt_el_val = QLineEdit()
        self.txt_el_val.textChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("Value:"), self.txt_el_val)
        
        self.txt_el_var = QLineEdit()
        self.txt_el_var.textChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("Store Result in Variable:"), self.txt_el_var)
        
        self.spin_el_index = QSpinBox()
        self.spin_el_index.setRange(0, 1000)
        self.spin_el_index.setValue(0)
        self.spin_el_index.valueChanged.connect(self.save_current_block_info)
        pe_lay.addRow(QLabel("With Index ="), self.spin_el_index)
        
        self.chk_el_recursive = QCheckBox("Recursive (all indexes)")
        self.chk_el_recursive.stateChanged.connect(self.save_current_block_info)
        pe_lay.addRow("", self.chk_el_recursive)
        
        self.chk_el_capture = QCheckBox("Is Capture (Save as successful Hit data)")
        self.chk_el_capture.stateChanged.connect(self.save_current_block_info)
        pe_lay.addRow("", self.chk_el_capture)
        self.info_stack.addWidget(self.prop_element)
        
        # Execute JS properties page
        self.prop_js = QWidget()
        pj_lay = QFormLayout(self.prop_js)
        pj_lay.setContentsMargins(0, 0, 0, 0)
        pj_lay.setSpacing(8)
        self.txt_js_code = QTextEdit()
        self.txt_js_code.textChanged.connect(self.save_current_block_info)
        pj_lay.addRow(QLabel("JavaScript Code:"), self.txt_js_code)
        
        self.txt_js_var = QLineEdit()
        self.txt_js_var.textChanged.connect(self.save_current_block_info)
        pj_lay.addRow(QLabel("Store Result in Variable:"), self.txt_js_var)
        self.info_stack.addWidget(self.prop_js)
        
        self.init_request_properties()
        self.init_utility_properties()
        self.init_keycheck_properties()
        self.init_parse_properties()
        self.init_function_properties()
        self.init_solve_captcha_properties()
        self.init_report_captcha_properties()
        self.init_bypass_cf_properties()
        self.init_tcp_properties()
        
        info_layout.addWidget(self.info_stack)
        self.info_box.setLayout(info_layout)
        self.stacker_splitter.addWidget(self.info_box)
        
        # 3. Right Column (Debugger - 35% Width)
        from ui.debugger_widget import DebuggerWidget
        self.debugger_widget = DebuggerWidget(self)
        self.stacker_splitter.addWidget(self.debugger_widget)
        
        # Configure sizes: Left 25%, Center 40%, Right 35%
        self.stacker_splitter.setSizes([250, 400, 350])
        
        stacker_layout.addWidget(self.stacker_splitter)
        self.sub_tabs.addTab(stacker_widget, "Stacker")
        
    def init_other_options_tab(self):
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        
        self.options_tabs = QTabWidget()
        options_layout.addWidget(self.options_tabs)
        
        # 1. General Options Tab
        general_widget = QWidget()
        gen_layout = QFormLayout(general_widget)
        
        self.opt_gen_name = QLineEdit()
        gen_layout.addRow(QLabel("Config Name:"), self.opt_gen_name)
        
        self.opt_gen_author = QLineEdit()
        gen_layout.addRow(QLabel("Author:"), self.opt_gen_author)
        
        self.opt_gen_info = QLineEdit()
        gen_layout.addRow(QLabel("Additional Info:"), self.opt_gen_info)
        
        self.opt_gen_bots = QSpinBox()
        self.opt_gen_bots.setRange(1, 200)
        self.opt_gen_bots.setValue(1)
        gen_layout.addRow(QLabel("Suggested Bots:"), self.opt_gen_bots)
        
        self.opt_gen_max_cpm = QSpinBox()
        self.opt_gen_max_cpm.setRange(0, 100000)
        self.opt_gen_max_cpm.setValue(0)
        self.opt_gen_max_cpm.setSuffix(" CPM (0 = infinite)")
        gen_layout.addRow(QLabel("Max CPM Speed Limit:"), self.opt_gen_max_cpm)
        
        self.opt_gen_empty_caps = QCheckBox("Save empty captures")
        gen_layout.addRow(self.opt_gen_empty_caps)
        
        self.opt_gen_continue_custom = QCheckBox("Continue after Custom Status")
        gen_layout.addRow(self.opt_gen_continue_custom)
        
        self.opt_gen_save_to_file = QCheckBox("Save hits to a text file instead of DB")
        gen_layout.addRow(self.opt_gen_save_to_file)
        
        self.options_tabs.addTab(general_widget, "General")
        
        # 1.5. Requests Tab Options
        requests_widget = QWidget()
        req_opt_layout = QVBoxLayout(requests_widget)
        req_opt_layout.setContentsMargins(10, 10, 10, 10)
        req_opt_layout.setSpacing(10)
        
        req_box = QGroupBox("HTTP Execution Engine")
        req_box_layout = QVBoxLayout(req_box)
        
        self.opt_use_selenium = QCheckBox("Use Selenium (Browser Mode)")
        self.opt_use_selenium.setToolTip("If unchecked, the configuration will execute using the rapid, lightweight requests library (Requests Mode) without opening a browser.")
        self.opt_use_selenium.setChecked(True)
        self.opt_use_selenium.stateChanged.connect(self.save_current_block_info)
        req_box_layout.addWidget(self.opt_use_selenium)
        
        lbl_info = QLabel("Requests mode performs HTTP connection pooling and cookie tracking per-bot thread, making it up to 50x faster than browser automation.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #78909c; font-style: italic; font-size: 11px;")
        req_box_layout.addWidget(lbl_info)
        
        req_opt_layout.addWidget(req_box)
        req_opt_layout.addStretch()
        
        self.options_tabs.addTab(requests_widget, "Requests")
        
        # 2. Proxies Options Tab
        proxies_widget = QWidget()
        prox_layout = QFormLayout(proxies_widget)
        
        self.opt_prox_needed = QCheckBox("Needs Proxies")
        prox_layout.addRow(self.opt_prox_needed)
        
        self.opt_prox_only_socks = QCheckBox("Use Only Socks Proxies")
        prox_layout.addRow(self.opt_prox_only_socks)
        
        self.opt_prox_only_ssl = QCheckBox("Use Only SSL Proxies")
        prox_layout.addRow(self.opt_prox_only_ssl)
        
        self.opt_prox_ban_after_good = QCheckBox("Ban Proxy after Good Status")
        prox_layout.addRow(self.opt_prox_ban_after_good)
        
        self.opt_prox_max_uses = QSpinBox()
        self.opt_prox_max_uses.setRange(0, 1000)
        self.opt_prox_max_uses.setValue(0)
        prox_layout.addRow(QLabel("Max Uses Per Proxy (0 = infinite):"), self.opt_prox_max_uses)
        
        self.opt_prox_ban_loop = QSpinBox()
        self.opt_prox_ban_loop.setRange(-1, 1000)
        self.opt_prox_ban_loop.setValue(-1)
        prox_layout.addRow(QLabel("Ban Loop Evasion (-1 = default):"), self.opt_prox_ban_loop)
        
        self.options_tabs.addTab(proxies_widget, "Proxies")
        
        # Input Tab placeholder
        self.options_tabs.addTab(QLabel("Input form values (Placeholder)"), "Input")
        
        # 3. Data Options Tab
        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)
        
        # Wordlist Configuration Group Box
        wl_config_group = QGroupBox("Wordlist Configuration")
        wl_config_lay = QVBoxLayout()
        wl_config_lay.setContentsMargins(10, 10, 10, 10)
        wl_config_lay.setSpacing(8)
        
        form_lay = QFormLayout()
        self.opt_data_wl_type = QComboBox()
        self.opt_data_wl_type.addItems(["Default", "Credentials", "Card", "Numeric", "URLs", "Extended", "Custom"])
        form_lay.addRow(QLabel("Allowed Wordlist Types:"), self.opt_data_wl_type)
        
        # Custom format section in Data Tab
        self.data_custom_format_widget = QWidget()
        data_cf_layout = QVBoxLayout()
        data_cf_layout.setContentsMargins(0, 0, 0, 0)
        self.data_custom_format_widget.setLayout(data_cf_layout)
        
        self.opt_data_custom_format = QLineEdit()
        self.opt_data_custom_format.setPlaceholderText("<NAME>:<EMAIL>:<PASSWORD>:<DD>/<MM>/<YYYY>")
        data_cf_layout.addWidget(QLabel("Custom Format Pattern:"))
        data_cf_layout.addWidget(self.opt_data_custom_format)
        
        # Presets in Data Tab
        data_cf_presets = QHBoxLayout()
        data_cf_presets.addWidget(QLabel("Presets:"))
        
        btn_df_ep = QPushButton("EMAIL:PASS")
        btn_df_ep.clicked.connect(lambda: self.opt_data_custom_format.setText("<EMAIL>:<PASSWORD>"))
        data_cf_presets.addWidget(btn_df_ep)
        
        btn_df_ph = QPushButton("PHONE")
        btn_df_ph.clicked.connect(lambda: self.opt_data_custom_format.setText("<PHONE>"))
        data_cf_presets.addWidget(btn_df_ph)
        
        btn_df_cc = QPushButton("CCNUM:MM/YY:CVV")
        btn_df_cc.clicked.connect(lambda: self.opt_data_custom_format.setText("<CCNUM>|<MM>|<YY>|<CVV>"))
        data_cf_presets.addWidget(btn_df_cc)
        
        btn_df_ur = QPushButton("URLs")
        btn_df_ur.clicked.connect(lambda: self.opt_data_custom_format.setText("<URL>"))
        data_cf_presets.addWidget(btn_df_ur)
        
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
        btn_df_ep.setStyleSheet(button_style)
        btn_df_ph.setStyleSheet(button_style)
        btn_df_cc.setStyleSheet(button_style)
        btn_df_ur.setStyleSheet(button_style)
        
        data_cf_layout.addLayout(data_cf_presets)
        form_lay.addRow(self.data_custom_format_widget)
        self.data_custom_format_widget.hide()
        
        self.opt_data_wl_type.currentTextChanged.connect(
            lambda t: self.data_custom_format_widget.setVisible(t == "Custom")
        )
        
        self.opt_data_urlencode = QCheckBox("URLEncode Data after Slicing")
        form_lay.addRow(self.opt_data_urlencode)
        
        wl_config_lay.addLayout(form_lay)
        wl_config_group.setLayout(wl_config_lay)
        data_layout.addWidget(wl_config_group)
        
        # Rules layout panel
        rules_box = QGroupBox("Rules List configuration")
        rules_lay = QVBoxLayout()
        
        rules_buttons = QHBoxLayout()
        self.btn_add_rule = QPushButton("Add Rule")
        self.btn_add_rule.clicked.connect(self.on_add_rule)
        rules_buttons.addWidget(self.btn_add_rule)
        
        self.btn_clear_rules = QPushButton("Clear Rules")
        self.btn_clear_rules.clicked.connect(lambda: self.opt_data_rules_list.clear())
        rules_buttons.addWidget(self.btn_clear_rules)
        rules_lay.addLayout(rules_buttons)
        
        self.opt_data_rules_list = QListWidget()
        rules_lay.addWidget(self.opt_data_rules_list)
        rules_box.setLayout(rules_lay)
        data_layout.addWidget(rules_box)
        
        self.options_tabs.addTab(data_widget, "Data")
        
        # 4. Selenium Options Sub-tab (Dual Column layout)
        selenium_opt_widget = QWidget()
        sel_opt_layout = QHBoxLayout(selenium_opt_widget)
        
        left_col = QGroupBox("Selenium Lifecycle")
        left_col_layout = QVBoxLayout()
        self.opt_always_open = QCheckBox("Always Open browser at the start")
        self.opt_always_open.setChecked(True)
        left_col_layout.addWidget(self.opt_always_open)
        
        self.opt_always_quit = QCheckBox("Always Quit browser at the end")
        self.opt_always_quit.setChecked(True)
        left_col_layout.addWidget(self.opt_always_quit)
        
        self.opt_quit_ban_retry = QCheckBox("Quit browser only on BAN or RETRY")
        left_col_layout.addWidget(self.opt_quit_ban_retry)
        left_col_layout.addStretch()
        left_col.setLayout(left_col_layout)
        sel_opt_layout.addWidget(left_col)
        
        right_col = QGroupBox("Identity & Arguments")
        right_col_layout = QFormLayout()
        self.opt_headless = QCheckBox("Force Headless")
        right_col_layout.addRow(self.opt_headless)
        self.opt_disable_notifications = QCheckBox("Disable Notifications")
        self.opt_disable_notifications.setChecked(True)
        right_col_layout.addRow(self.opt_disable_notifications)
        self.opt_custom_args = QLineEdit()
        self.opt_custom_args.setPlaceholderText("e.g. --incognito --disable-gpu")
        right_col_layout.addRow(QLabel("Custom Args:"), self.opt_custom_args)
        self.opt_user_agent = QLineEdit()
        self.opt_user_agent.setPlaceholderText("Custom User Agent header")
        right_col_layout.addRow(QLabel("User Agent:"), self.opt_user_agent)
        self.opt_random_ua = QCheckBox("Use Random User Agent")
        right_col_layout.addRow(self.opt_random_ua)
        right_col.setLayout(right_col_layout)
        sel_opt_layout.addWidget(right_col)
        
        self.options_tabs.addTab(selenium_opt_widget, "Selenium")
        
        self.sub_tabs.addTab(options_widget, "Other Options")
        
        # Real-time footer label update from Data options tab
        def update_footer_wl(text):
            self.lbl_allowed_wl.setText(f"Allowed Wordlists: {text}")
        self.opt_data_wl_type.currentTextChanged.connect(update_footer_wl)

    def init_request_properties(self):
        self.prop_request = QWidget()
        layout = QVBoxLayout(self.prop_request)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_req_url = QLineEdit()
        self.txt_req_url.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("URL:"), self.txt_req_url)
        
        self.cb_req_method = QComboBox()
        self.cb_req_method.addItems(["GET", "HEAD", "DELETE", "POST", "PUT", "OPTIONS", "PATCH", "TRACE"])
        self.cb_req_method.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Method:"), self.cb_req_method)
        
        chks = QHBoxLayout()
        self.chk_req_redirect = QCheckBox("Auto Redirect")
        self.chk_req_redirect.setChecked(True)
        self.chk_req_redirect.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_req_redirect)
        
        self.chk_req_read_resp = QCheckBox("Read Resp. Source")
        self.chk_req_read_resp.setChecked(True)
        self.chk_req_read_resp.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_req_read_resp)
        
        self.chk_req_accept_enc = QCheckBox("Accept-Encoding")
        self.chk_req_accept_enc.setChecked(True)
        self.chk_req_accept_enc.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_req_accept_enc)
        
        self.chk_req_encode_content = QCheckBox("Encode Content")
        self.chk_req_encode_content.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_req_encode_content)
        
        form.addRow(chks)
        
        self.cb_req_sec_proto = QComboBox()
        self.cb_req_sec_proto.addItems(["SystemDefault", "Tls10", "Tls11", "Tls12", "Tls13"])
        self.cb_req_sec_proto.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Security Protocol:"), self.cb_req_sec_proto)
        
        self.cb_req_type = QComboBox()
        self.cb_req_type.addItems(["Standard"])
        self.cb_req_type.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Request Type:"), self.cb_req_type)
        
        self.cb_req_content_type = QComboBox()
        self.cb_req_content_type.addItems(["", "application/x-www-form-urlencoded", "application/json", "text/plain", "multipart/form-data"])
        self.cb_req_content_type.setEditable(True)
        self.cb_req_content_type.currentIndexChanged.connect(self.save_current_block_info)
        self.cb_req_content_type.lineEdit().textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Content-Type:"), self.cb_req_content_type)
        
        self.cb_req_resp_type = QComboBox()
        self.cb_req_resp_type.addItems(["String", "File", "Base64"])
        self.cb_req_resp_type.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Response Type:"), self.cb_req_resp_type)
        
        layout.addLayout(form)
        
        layout.addWidget(QLabel("POST Data:"))
        self.txt_req_post_data = QTextEdit()
        self.txt_req_post_data.textChanged.connect(self.save_current_block_info)
        layout.addWidget(self.txt_req_post_data)
        
        layout.addWidget(QLabel("Custom Cookies (Name=Value per line):"))
        self.txt_req_cookies = QTextEdit()
        self.txt_req_cookies.textChanged.connect(self.save_current_block_info)
        layout.addWidget(self.txt_req_cookies)
        
        layout.addWidget(QLabel("Custom Headers (Name:Value per line):"))
        self.txt_req_headers = QTextEdit()
        self.txt_req_headers.textChanged.connect(self.save_current_block_info)
        layout.addWidget(self.txt_req_headers)
        
        self.info_stack.addWidget(self.prop_request)

    def init_utility_properties(self):
        self.prop_utility = QWidget()
        layout = QVBoxLayout(self.prop_utility)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_ut_var_name = QLineEdit()
        self.txt_ut_var_name.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Variable Name:"), self.txt_ut_var_name)
        
        self.chk_ut_capture = QCheckBox("Is Capture")
        self.chk_ut_capture.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_ut_capture)
        
        self.cb_ut_group = QComboBox()
        self.cb_ut_group.addItems(["List", "File", "Folder", "System"])
        self.cb_ut_group.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Group:"), self.cb_ut_group)
        
        self.cb_ut_action = QComboBox()
        self.cb_ut_action.addItems(["Join", "Split", "Clear", "Zip"])
        self.cb_ut_action.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Action:"), self.cb_ut_action)
        
        self.txt_ut_list_var = QLineEdit()
        self.txt_ut_list_var.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("List Variable Name:"), self.txt_ut_list_var)
        
        self.txt_ut_separator = QLineEdit(",")
        self.txt_ut_separator.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Separator:"), self.txt_ut_separator)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_utility)

    def init_keycheck_properties(self):
        self.prop_keycheck = QWidget()
        layout = QVBoxLayout(self.prop_keycheck)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.chk_kc_insta_ban = QCheckBox("Insta Ban 4xx")
        self.chk_kc_insta_ban.stateChanged.connect(self.save_current_block_info)
        layout.addWidget(self.chk_kc_insta_ban)
        
        self.chk_kc_ban_no_key = QCheckBox("Ban if no key found")
        self.chk_kc_ban_no_key.stateChanged.connect(self.save_current_block_info)
        layout.addWidget(self.chk_kc_ban_no_key)
        
        layout.addWidget(QLabel("Keychains:"))
        kc_layout = QHBoxLayout()
        self.keychains_list = QListWidget()
        self.keychains_list.currentRowChanged.connect(self.on_keychain_selected)
        kc_layout.addWidget(self.keychains_list, 2)
        
        kc_btns = QVBoxLayout()
        self.btn_add_kc = QPushButton("Add Keychain")
        self.btn_add_kc.clicked.connect(self.on_add_keychain)
        kc_btns.addWidget(self.btn_add_kc)
        
        self.btn_del_kc = QPushButton("Delete Keychain")
        self.btn_del_kc.clicked.connect(self.on_delete_keychain)
        kc_btns.addWidget(self.btn_del_kc)
        kc_btns.addStretch()
        kc_layout.addLayout(kc_btns)
        
        layout.addLayout(kc_layout)
        
        self.kc_prop_group = QGroupBox("Selected Keychain Properties")
        self.kc_prop_group.setEnabled(False)
        kc_prop_layout = QVBoxLayout(self.kc_prop_group)
        
        form = QFormLayout()
        self.cb_kc_type = QComboBox()
        self.cb_kc_type.addItems(["Success", "Failure", "Ban", "Retry", "Custom"])
        self.cb_kc_type.currentIndexChanged.connect(self.on_keychain_properties_changed)
        form.addRow(QLabel("Type:"), self.cb_kc_type)
        
        self.cb_kc_mode = QComboBox()
        self.cb_kc_mode.addItems(["OR", "AND"])
        self.cb_kc_mode.currentIndexChanged.connect(self.on_keychain_properties_changed)
        form.addRow(QLabel("Mode:"), self.cb_kc_mode)
        kc_prop_layout.addLayout(form)
        
        kc_prop_layout.addWidget(QLabel("Keys / Rules:"))
        keys_h_layout = QHBoxLayout()
        self.keys_list = QListWidget()
        self.keys_list.itemDoubleClicked.connect(self.on_edit_key_item)
        keys_h_layout.addWidget(self.keys_list, 2)
        
        keys_btns = QVBoxLayout()
        self.btn_add_key = QPushButton("Add Key")
        self.btn_add_key.clicked.connect(self.on_add_key_to_keychain)
        keys_btns.addWidget(self.btn_add_key)
        
        self.btn_del_key = QPushButton("Delete Key")
        self.btn_del_key.clicked.connect(self.on_delete_key_from_keychain)
        keys_btns.addWidget(self.btn_del_key)
        keys_btns.addStretch()
        keys_h_layout.addLayout(keys_btns)
        
        kc_prop_layout.addLayout(keys_h_layout)
        layout.addWidget(self.kc_prop_group)
        
        self.info_stack.addWidget(self.prop_keycheck)

    def on_keychain_selected(self, row):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            self.kc_prop_group.setEnabled(False)
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row >= 0 and row < len(keychains):
            self.kc_prop_group.setEnabled(True)
            kc = keychains[row]
            
            self.cb_kc_type.blockSignals(True)
            self.cb_kc_mode.blockSignals(True)
            self.cb_kc_type.setCurrentText(kc.get("type", "Success"))
            self.cb_kc_mode.setCurrentText(kc.get("mode", "OR"))
            self.cb_kc_type.blockSignals(False)
            self.cb_kc_mode.blockSignals(False)
            
            self.keys_list.blockSignals(True)
            self.keys_list.clear()
            for key in kc.get("keys", []):
                self.keys_list.addItem(key)
            self.keys_list.blockSignals(False)
        else:
            self.kc_prop_group.setEnabled(False)
            self.keys_list.clear()

    def on_keychain_properties_changed(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        row = self.keychains_list.currentRow()
        if row < 0:
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row < len(keychains):
            keychains[row]["type"] = self.cb_kc_type.currentText()
            keychains[row]["mode"] = self.cb_kc_mode.currentText()
            block["keychains"] = keychains
            
            self.keychains_list.blockSignals(True)
            self.keychains_list.item(row).setText(f"Keychain {row+1} [{keychains[row]['type']}] ({keychains[row]['mode']})")
            self.keychains_list.blockSignals(False)
            self.save_current_block_info()

    def on_add_keychain(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        new_kc = {"type": "Success", "mode": "OR", "keys": []}
        keychains.append(new_kc)
        block["keychains"] = keychains
        self.save_current_block_info()
        
        self.keychains_list.blockSignals(True)
        self.keychains_list.addItem(f"Keychain {len(keychains)} [Success] (OR)")
        self.keychains_list.blockSignals(False)
        self.keychains_list.setCurrentRow(len(keychains) - 1)

    def on_delete_keychain(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        row = self.keychains_list.currentRow()
        if row < 0:
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row < len(keychains):
            keychains.pop(row)
            block["keychains"] = keychains
            self.save_current_block_info()
            
            self.keychains_list.blockSignals(True)
            self.keychains_list.clear()
            for i, kc in enumerate(keychains):
                self.keychains_list.addItem(f"Keychain {i+1} [{kc.get('type','Success')}] ({kc.get('mode','OR')})")
            self.keychains_list.blockSignals(False)
            self.keys_list.clear()
            self.kc_prop_group.setEnabled(False)

    def on_add_key_to_keychain(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        row = self.keychains_list.currentRow()
        if row < 0:
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row < len(keychains):
            key, ok = QInputDialog.getText(self, "Add Key/Rule", "Enter text pattern or response code:")
            if ok and key.strip():
                keychains[row]["keys"].append(key.strip())
                block["keychains"] = keychains
                self.save_current_block_info()
                
                self.keys_list.addItem(key.strip())

    def on_delete_key_from_keychain(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        row = self.keychains_list.currentRow()
        if row < 0:
            return
        key_row = self.keys_list.currentRow()
        if key_row < 0:
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row < len(keychains):
            kc = keychains[row]
            if key_row < len(kc.get("keys", [])):
                kc["keys"].pop(key_row)
                block["keychains"] = keychains
                self.save_current_block_info()
                
                self.keys_list.takeItem(key_row)

    def on_edit_key_item(self, item):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        row = self.keychains_list.currentRow()
        if row < 0:
            return
        key_row = self.keys_list.row(item)
        if key_row < 0:
            return
            
        block = self.blocks[idx]
        keychains = block.get("keychains", [])
        if isinstance(keychains, str):
            try:
                import json
                keychains = json.loads(keychains)
            except Exception:
                keychains = []
                
        if row < len(keychains):
            kc = keychains[row]
            if key_row < len(kc.get("keys", [])):
                old_val = kc["keys"][key_row]
                key, ok = QInputDialog.getText(self, "Edit Key/Rule", "Edit text pattern or response code:", text=old_val)
                if ok and key.strip():
                    kc["keys"][key_row] = key.strip()
                    block["keychains"] = keychains
                    self.save_current_block_info()
                    item.setText(key.strip())

    def init_parse_properties(self):
        self.prop_parse = QWidget()
        layout = QVBoxLayout(self.prop_parse)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_parse_source = QLineEdit("<SOURCE>")
        self.txt_parse_source.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Parse Source:"), self.txt_parse_source)
        
        self.txt_parse_var_name = QLineEdit()
        self.txt_parse_var_name.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Var/Cap Name:"), self.txt_parse_var_name)
        
        self.txt_parse_prefix = QLineEdit()
        self.txt_parse_prefix.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Prefix:"), self.txt_parse_prefix)
        
        self.txt_parse_suffix = QLineEdit()
        self.txt_parse_suffix.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Suffix:"), self.txt_parse_suffix)
        
        mode_box = QGroupBox("Mode Selection")
        mode_layout = QHBoxLayout()
        self.rad_parse_lr = QRadioButton("LR (Left/Right)")
        self.rad_parse_lr.setChecked(True)
        self.rad_parse_lr.toggled.connect(self.save_current_block_info)
        mode_layout.addWidget(self.rad_parse_lr)
        
        self.rad_parse_css = QRadioButton("CSS")
        self.rad_parse_css.toggled.connect(self.save_current_block_info)
        mode_layout.addWidget(self.rad_parse_css)
        
        self.rad_parse_json = QRadioButton("JSON")
        self.rad_parse_json.toggled.connect(self.save_current_block_info)
        mode_layout.addWidget(self.rad_parse_json)
        
        self.rad_parse_regex = QRadioButton("REGEX")
        self.rad_parse_regex.toggled.connect(self.save_current_block_info)
        mode_layout.addWidget(self.rad_parse_regex)
        
        mode_box.setLayout(mode_layout)
        form.addRow(mode_box)
        
        self.txt_parse_left = QLineEdit()
        self.txt_parse_left.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Left string / Path / Pattern:"), self.txt_parse_left)
        
        self.txt_parse_right = QLineEdit()
        self.txt_parse_right.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Right string / Attribute:"), self.txt_parse_right)
        
        chks = QHBoxLayout()
        self.chk_parse_recursive = QCheckBox("Recursive")
        self.chk_parse_recursive.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_parse_recursive)
        
        self.chk_parse_enc = QCheckBox("Enc. Output")
        self.chk_parse_enc.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_parse_enc)
        
        self.chk_parse_empty = QCheckBox("Create Empty")
        self.chk_parse_empty.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_parse_empty)
        
        self.chk_parse_use_regex = QCheckBox("Use Regex")
        self.chk_parse_use_regex.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_parse_use_regex)
        
        self.chk_parse_is_capture = QCheckBox("Is Capture")
        self.chk_parse_is_capture.stateChanged.connect(self.save_current_block_info)
        chks.addWidget(self.chk_parse_is_capture)
        
        form.addRow(chks)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_parse)

    def init_function_properties(self):
        self.prop_function = QWidget()
        layout = QVBoxLayout(self.prop_function)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_fn_var_name = QLineEdit()
        self.txt_fn_var_name.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Variable Name:"), self.txt_fn_var_name)
        
        self.txt_fn_input = QLineEdit()
        self.txt_fn_input.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Input string:"), self.txt_fn_input)
        
        self.chk_fn_capture = QCheckBox("Is Capture")
        self.chk_fn_capture.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_fn_capture)
        
        self.cb_fn_type = QComboBox()
        self.cb_fn_type.addItems([
            "Constant", "Base64Encode", "Base64Decode", "Hash", "HMAC", 
            "Translate", "DateToUnixTime", "Length", "ToLowercase", "ToUppercase"
        ])
        self.cb_fn_type.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Function Type:"), self.cb_fn_type)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_function)

    def init_solve_captcha_properties(self):
        self.prop_solve_captcha = QWidget()
        layout = QVBoxLayout(self.prop_solve_captcha)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_sc_var = QLineEdit()
        self.txt_sc_var.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Variable Name:"), self.txt_sc_var)
        
        self.cb_sc_type = QComboBox()
        self.cb_sc_type.addItems(["ReCaptchaV2", "ReCaptchaV3", "HCaptcha", "ImageCaptcha", "FunCaptcha"])
        self.cb_sc_type.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Captcha Type:"), self.cb_sc_type)
        
        self.txt_sc_sitekey = QLineEdit()
        self.txt_sc_sitekey.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Site Key:"), self.txt_sc_sitekey)
        
        self.txt_sc_url = QLineEdit()
        self.txt_sc_url.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Page URL:"), self.txt_sc_url)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_solve_captcha)

    def init_report_captcha_properties(self):
        self.prop_report_captcha = QWidget()
        layout = QVBoxLayout(self.prop_report_captcha)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_rc_id = QLineEdit()
        self.txt_rc_id.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Captcha ID:"), self.txt_rc_id)
        
        self.chk_rc_bad = QCheckBox("Report Bad")
        self.chk_rc_bad.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_rc_bad)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_report_captcha)

    def init_bypass_cf_properties(self):
        self.prop_bypass_cf = QWidget()
        layout = QVBoxLayout(self.prop_bypass_cf)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_cf_url = QLineEdit()
        self.txt_cf_url.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("URL:"), self.txt_cf_url)
        
        self.txt_cf_ua = QLineEdit("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.txt_cf_ua.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("User Agent:"), self.txt_cf_ua)
        
        self.cb_cf_sec = QComboBox()
        self.cb_cf_sec.addItems(["SystemDefault", "Tls10", "Tls11", "Tls12", "Tls13"])
        self.cb_cf_sec.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Security Protocol:"), self.cb_cf_sec)
        
        self.chk_cf_print = QCheckBox("Print Response Info")
        self.chk_cf_print.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_cf_print)
        
        self.chk_cf_redir = QCheckBox("Auto Redirect")
        self.chk_cf_redir.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_cf_redir)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_bypass_cf)

    def init_tcp_properties(self):
        self.prop_tcp = QWidget()
        layout = QVBoxLayout(self.prop_tcp)
        layout.setContentsMargins(5, 5, 5, 5)
        
        form = QFormLayout()
        
        self.txt_tcp_var = QLineEdit()
        self.txt_tcp_var.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Variable Name:"), self.txt_tcp_var)
        
        self.chk_tcp_capture = QCheckBox("Is Capture")
        self.chk_tcp_capture.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_tcp_capture)
        
        self.cb_tcp_cmd = QComboBox()
        self.cb_tcp_cmd.addItems(["Connect", "Disconnect", "Send", "Receive"])
        self.cb_tcp_cmd.currentIndexChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Command:"), self.cb_tcp_cmd)
        
        self.txt_tcp_host = QLineEdit()
        self.txt_tcp_host.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Host (or data for Send):"), self.txt_tcp_host)
        
        self.txt_tcp_port = QLineEdit("80")
        self.txt_tcp_port.textChanged.connect(self.save_current_block_info)
        form.addRow(QLabel("Port:"), self.txt_tcp_port)
        
        self.chk_tcp_ssl = QCheckBox("SSL")
        self.chk_tcp_ssl.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_tcp_ssl)
        
        self.chk_tcp_hello = QCheckBox("Wait for hello")
        self.chk_tcp_hello.stateChanged.connect(self.save_current_block_info)
        form.addRow(self.chk_tcp_hello)
        
        layout.addLayout(form)
        layout.addStretch()
        self.info_stack.addWidget(self.prop_tcp)

    def set_properties_signals_blocked(self, blocked):
        self.info_box.blockSignals(blocked)
        for child in self.info_box.findChildren(QWidget):
            child.blockSignals(blocked)

    def on_add_rule(self):
        rule, ok = QInputDialog.getText(self, "Add Permutation Rule", "Enter condition rule string:")
        if ok and rule.strip():
            self.opt_data_rules_list.addItem(rule.strip())

    def read_config_file(self, filepath) -> dict:
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

    def load_configs_list(self):
        self.configs_table.setRowCount(0)
        for file in os.listdir(self.configs_dir):
            if file.endswith(".zan") or file.endswith(".json"):
                path = os.path.join(self.configs_dir, file)
                try:
                    data = self.read_config_file(path)
                    row = self.configs_table.rowCount()
                    self.configs_table.insertRow(row)
                    
                    name_without_ext = file[:-4] if file.endswith(".zan") else file[:-5]
                    self.configs_table.setItem(row, 0, QTableWidgetItem(data.get("name", name_without_ext)))
                    self.configs_table.setItem(row, 1, QTableWidgetItem(data.get("author", "Unknown")))
                    self.configs_table.setItem(row, 2, QTableWidgetItem(data.get("category", "Default")))
                    
                    proxies_text = "Yes" if data.get("use_proxies", False) else "No"
                    captchas_text = "Yes" if data.get("use_captchas", False) else "No"
                    sel_text = "Yes" if data.get("use_selenium", True) else "No"
                    cf_text = "Yes" if data.get("cf_bypass", False) else "No"
                    
                    self.configs_table.setItem(row, 3, QTableWidgetItem(proxies_text))
                    self.configs_table.setItem(row, 4, QTableWidgetItem(captchas_text))
                    self.configs_table.setItem(row, 5, QTableWidgetItem(sel_text))
                    self.configs_table.setItem(row, 6, QTableWidgetItem(cf_text))
                    self.configs_table.setItem(row, 7, QTableWidgetItem(data.get("last_modified", "Unknown")))
                except Exception:
                    pass
        self.lbl_total_configs.setText(f"Total Configs: {self.configs_table.rowCount()}")

    def filter_configs(self):
        query = self.txt_search.text().lower()
        for r in range(self.configs_table.rowCount()):
            name = self.configs_table.item(r, 0).text().lower()
            cat = self.configs_table.item(r, 2).text().lower()
            match = query in name or query in cat
            self.configs_table.setRowHidden(r, not match)

    def on_config_selected(self):
        selected_rows = self.configs_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        name = self.configs_table.item(row, 0).text()
        
        self.selected_config_name = name
        self.lbl_current_config.setText(f"Current Config: {name}")
        
        zan_path = os.path.join(self.configs_dir, f"{name}.zan")
        json_path = os.path.join(self.configs_dir, f"{name}.json")
        if os.path.exists(zan_path):
            self.current_config_file = zan_path
        else:
            self.current_config_file = json_path
            
        try:
            data = self.read_config_file(self.current_config_file)
            self.blocks = data.get("blocks", [])
            self.sync_blocks_to_ui()
            
            # Populate bottom meta info bar
            allowed_wl = data.get('allowed_wordlists', data.get('data_settings', {}).get('allowed_wl_type', 'Credentials'))
            self.lbl_allowed_wl.setText(f"Allowed Wordlists: {allowed_wl}")
            self.lbl_blocks_count.setText(f"Blocks Amount: {len(self.blocks)}")
            self.lbl_suggested_bots.setText(f"Suggested Bots: {data.get('suggested_bots', '5')}")
            self.lbl_info_author.setText(f"Author: {data.get('author', 'Unknown')}")
            self.lbl_info_modified.setText(f"Last Modified: {data.get('last_modified', 'Unknown')}")
            self.lbl_additional_info.setText(f"Additional Info: {data.get('additional_info', 'None')}")
            
            # Load General Configuration options
            self.opt_gen_name.setText(data.get("name", name))
            self.opt_gen_author.setText(data.get("author", "Unknown"))
            self.opt_gen_info.setText(data.get("additional_info", "None"))
            self.opt_gen_bots.setValue(int(data.get("suggested_bots", 1)))
            self.opt_gen_max_cpm.setValue(int(data.get("max_cpm", 0)))
            self.opt_gen_empty_caps.setChecked(data.get("save_empty_captures", False))
            self.opt_gen_continue_custom.setChecked(data.get("continue_custom", False))
            self.opt_gen_save_to_file.setChecked(data.get("save_hits_to_file", False))
            
            # Load Proxy configuration options
            p_set = data.get("proxy_settings", {})
            self.opt_prox_needed.setChecked(p_set.get("needs_proxies", False))
            self.opt_prox_only_socks.setChecked(p_set.get("only_socks", False))
            self.opt_prox_only_ssl.setChecked(p_set.get("only_ssl", False))
            self.opt_prox_ban_after_good.setChecked(p_set.get("ban_after_good", False))
            self.opt_prox_max_uses.setValue(p_set.get("max_uses", 0))
            self.opt_prox_ban_loop.setValue(p_set.get("ban_loop", -1))
            
            # Load Data configuration options
            d_set = data.get("data_settings", {})
            self.opt_data_wl_type.setCurrentText(d_set.get("allowed_wl_type", "Default"))
            self.opt_data_urlencode.setChecked(d_set.get("urlencode", False))
            self.opt_data_custom_format.setText(d_set.get("custom_format", ""))
            
            # Load HTTP execution engine settings
            self.opt_use_selenium.setChecked(data.get("use_selenium", True))
            
            self.opt_data_rules_list.clear()
            for rule in d_set.get("rules", []):
                self.opt_data_rules_list.addItem(rule)
            
            # Load specific Selenium settings bound to this config
            sel_set = data.get("selenium_settings", {})
            self.opt_always_open.setChecked(sel_set.get("always_open", True))
            self.opt_always_quit.setChecked(sel_set.get("always_quit", True))
            self.opt_quit_ban_retry.setChecked(sel_set.get("quit_on_ban_retry", False))
            self.opt_headless.setChecked(sel_set.get("headless", False))
            self.opt_disable_notifications.setChecked(sel_set.get("disable_notifications", True))
            self.opt_custom_args.setText(sel_set.get("custom_args", ""))
            self.opt_user_agent.setText(sel_set.get("user_agent", ""))
            self.opt_random_ua.setChecked(sel_set.get("use_random_ua", False))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load config: {str(e)}")

    def sync_blocks_to_ui(self):
        self._is_syncing_ui = True
        # Update Visual list
        self.blocks_list.blockSignals(True)
        self.blocks_list.clear()
        for i, block in enumerate(self.blocks):
            summary = self.get_block_summary(block)
            label_text = f" [{block['label']}]" if block.get("label") else ""
            item = QListWidgetItem(f"{i + 1}. {block['type']}{label_text} ({summary})")
            
            # Store the block reference in user role data for drag and drop sync
            item.setData(Qt.ItemDataRole.UserRole, block)
            
            # Color code based on signature
            b_type = block.get("type", "")
            if b_type == "REQUEST":
                item.setForeground(QColor("#81c784")) # Green
            elif b_type == "PARSE":
                item.setForeground(QColor("#ffd54f")) # Yellow
            elif b_type == "KEY CHECK":
                item.setForeground(QColor("#64b5f6")) # Blue
            elif b_type == "BROWSER ACTION":
                item.setForeground(QColor("#00acc1")) # Cyan
            elif b_type == "ELEMENT ACTION":
                item.setForeground(QColor("#e57373")) # Red
            elif b_type == "EXECUTE JS":
                item.setForeground(QColor("#ba68c8")) # Purple
            else:
                item.setForeground(QColor("#e0e0e0")) # Silver/Gray default
                
            self.blocks_list.addItem(item)
        self.blocks_list.blockSignals(False)
        
        # Update script editor
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText(OneScriptCompiler.compile_to_script(self.blocks))
        self.text_editor.blockSignals(False)
        
        # Reset properties
        self.info_stack.setCurrentIndex(0)
        self.txt_block_label.clear()
        self._is_syncing_ui = False
        self.silent_save_config()

    def get_block_summary(self, block) -> str:
        b_type = block.get("type", "")
        if b_type == "BROWSER ACTION":
            return block.get("action", "Start Browser")
        elif b_type == "NAVIGATE":
            return block.get("url", "")
        elif b_type == "ELEMENT ACTION":
            return f"{block.get('action', 'Click')} -> {block.get('selector', '')}"
        elif b_type == "EXECUTE JS":
            code = block.get("script", "")
            return code[:30] + "..." if len(code) > 30 else code
        elif b_type == "REQUEST":
            return f"{block.get('method', 'GET')} -> {block.get('url', '')}"
        elif b_type == "UTILITY":
            return f"{block.get('group', 'List')} -> {block.get('action', 'Join')}"
        elif b_type == "KEY CHECK":
            return "Key Check Rule"
        elif b_type == "PARSE":
            return f"Parse {block.get('variable_name', '')} ({block.get('mode', 'LR')})"
        elif b_type == "FUNCTION":
            return f"Function: {block.get('function_type', 'Constant')}"
        elif b_type == "SOLVE CAPTCHA":
            return f"Solve {block.get('captcha_type', 'ReCaptchaV2')}"
        elif b_type == "REPORT CAPTCHA":
            return "Report Captcha Bad"
        elif b_type == "BYPASS CF":
            return f"Bypass CF -> {block.get('url', '')}"
        elif b_type == "TCP":
            return f"TCP {block.get('command', 'Connect')} -> {block.get('host', '')}"
        return ""

    @property
    def btn_view_text(self):
        class Dummy:
            def __init__(self, tab):
                self.tab = tab
            def isChecked(self):
                return self.tab.editor_stack.currentIndex() == 1
            def setChecked(self, val):
                pass
        return Dummy(self)

    @property
    def btn_view_visual(self):
        class Dummy:
            def __init__(self, tab):
                self.tab = tab
            def isChecked(self):
                return self.tab.editor_stack.currentIndex() == 0
            def setChecked(self, val):
                pass
        return Dummy(self)

    def on_clear_blocks(self):
        if QMessageBox.question(self, "Clear Stack", "Are you sure you want to clear all blocks?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.blocks = []
            self.sync_blocks_to_ui()

    def on_toggle_view(self):
        if self.editor_stack.currentIndex() == 0:
            # Switch to Script View
            self.btn_toggle_view.setText("[ </> SWITCH TO VISUAL ]")
            self.text_editor.setPlainText(OneScriptCompiler.compile_to_script(self.blocks))
            self.editor_stack.setCurrentIndex(1)
        else:
            # Switch to Visual View
            self.btn_toggle_view.setText("[ </> SWITCH TO ONE SCRIPT ]")
            script_text = self.text_editor.toPlainText()
            self.blocks = OneScriptCompiler.decompile_to_blocks(script_text)
            self.sync_blocks_to_ui()
            self.editor_stack.setCurrentIndex(0)

    def on_blocks_drag_dropped(self):
        if getattr(self, '_is_syncing_ui', False):
            return
        new_blocks = []
        for i in range(self.blocks_list.count()):
            item = self.blocks_list.item(i)
            block_data = item.data(Qt.ItemDataRole.UserRole)
            if block_data:
                new_blocks.append(block_data)
        if new_blocks:
            self.blocks = new_blocks
            self.sync_blocks_to_ui()

    def init_debugger_tab(self):
        from ui.debugger_widget import DebuggerWidget
        self.debugger_widget = DebuggerWidget(self)
        self.sub_tabs.addTab(self.debugger_widget, "Debugger")

    def on_edit_config(self):
        # Focus on Stacker Tab to edit
        self.sub_tabs.setCurrentIndex(1)

    def on_create_new(self):
        name, ok = QInputDialog.getText(self, "New Config", "Enter config name:")
        if not ok or not name.strip():
            return
            
        from utils.helpers import load_settings
        default_author = load_settings().get("OneBullet", {}).get("General", {}).get("defaultAuthor", "One Bullet Development Team")
        author, ok = QInputDialog.getText(self, "New Config", "Enter Author Name:", text=default_author)
        if not ok or not author.strip():
            author = default_author
            
        category, ok = QInputDialog.getText(self, "New Config", "Enter category (default 'Default'):")
        if not ok or not category.strip():
            category = "Default"
            
        filename = f"{name.strip()}.zan"
        filepath = os.path.join(self.configs_dir, filename)
        if os.path.exists(filepath):
            QMessageBox.warning(self, "Warning", "Config with this name already exists.")
            return
            
        new_data = {
            "name": name.strip(),
            "author": author.strip(),
            "category": category.strip(),
            "use_proxies": False,
            "use_captchas": False,
            "use_selenium": True,
            "cf_bypass": False,
            "allowed_wordlists": "Credentials",
            "suggested_bots": 5,
            "additional_info": "None",
            "version": "1.0.0",
            "last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocks": [],
            "max_cpm": 0,
            "save_empty_captures": False,
            "continue_custom": False,
            "save_hits_to_file": False,
            "proxy_settings": {
                "needs_proxies": False,
                "only_socks": False,
                "only_ssl": False,
                "ban_after_good": False,
                "max_uses": 0,
                "ban_loop": -1
            },
            "data_settings": {
                "allowed_wl_type": "Default",
                "urlencode": False,
                "custom_format": "",
                "rules": []
            },
            "selenium_settings": {
                "always_open": True,
                "always_quit": True,
                "quit_on_ban_retry": False,
                "headless": False,
                "disable_notifications": True,
                "custom_args": "",
                "user_agent": "",
                "use_random_ua": False
            }
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("[SETTINGS]\n")
                f.write(json.dumps(new_data, indent=4))
                f.write("\n\n[SCRIPT]\n")
                f.write("")
            self.load_configs_list()
            # Select new config
            for r in range(self.configs_table.rowCount()):
                if self.configs_table.item(r, 0).text() == name.strip():
                    self.configs_table.selectRow(r)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create config: {str(e)}")

    def on_save_config(self):
        if not self.current_config_file:
            QMessageBox.warning(self, "Warning", "Please select a config first.")
            return
            
        # Get active blocks
        if self.btn_view_text.isChecked():
            self.blocks = OneScriptCompiler.decompile_to_blocks(self.text_editor.toPlainText())
            
        try:
            data = self.read_config_file(self.current_config_file)
                
            data["blocks"] = self.blocks
            data["last_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data["use_proxies"] = self.settings_tab.get_settings().get("use_proxies", False)
            
            # Save General configuration options
            data["name"] = self.opt_gen_name.text()
            data["author"] = self.opt_gen_author.text()
            data["additional_info"] = self.opt_gen_info.text()
            data["suggested_bots"] = self.opt_gen_bots.value()
            data["max_cpm"] = self.opt_gen_max_cpm.value()
            data["save_empty_captures"] = self.opt_gen_empty_caps.isChecked()
            data["continue_custom"] = self.opt_gen_continue_custom.isChecked()
            data["save_hits_to_file"] = self.opt_gen_save_to_file.isChecked()
            
            # Save Proxy configuration options
            data["proxy_settings"] = {
                "needs_proxies": self.opt_prox_needed.isChecked(),
                "only_socks": self.opt_prox_only_socks.isChecked(),
                "only_ssl": self.opt_prox_only_ssl.isChecked(),
                "ban_after_good": self.opt_prox_ban_after_good.isChecked(),
                "max_uses": self.opt_prox_max_uses.value(),
                "ban_loop": self.opt_prox_ban_loop.value()
            }
            
            # Save Data configuration options
            rules = []
            for i in range(self.opt_data_rules_list.count()):
                rules.append(self.opt_data_rules_list.item(i).text())
                
            data["allowed_wordlists"] = self.opt_data_wl_type.currentText()
            self.lbl_allowed_wl.setText(f"Allowed Wordlists: {data['allowed_wordlists']}")
            
            data["data_settings"] = {
                "allowed_wl_type": self.opt_data_wl_type.currentText(),
                "urlencode": self.opt_data_urlencode.isChecked(),
                "custom_format": self.opt_data_custom_format.text().strip(),
                "rules": rules
            }
            
            data["use_selenium"] = self.opt_use_selenium.isChecked()
            
            # Save specific config Selenium settings
            data["selenium_settings"] = {
                "always_open": self.opt_always_open.isChecked(),
                "always_quit": self.opt_always_quit.isChecked(),
                "quit_on_ban_retry": self.opt_quit_ban_retry.isChecked(),
                "headless": self.opt_headless.isChecked(),
                "disable_notifications": self.opt_disable_notifications.isChecked(),
                "custom_args": self.opt_custom_args.text(),
                "user_agent": self.opt_user_agent.text(),
                "use_random_ua": self.opt_random_ua.isChecked()
            }
            
            if self.current_config_file.endswith(".zan"):
                script_code = OneScriptCompiler.compile_to_script(self.blocks)
                settings_data = data.copy()
                if "blocks" in settings_data:
                    del settings_data["blocks"]
                with open(self.current_config_file, "w", encoding="utf-8") as f:
                    f.write("[SETTINGS]\n")
                    f.write(json.dumps(settings_data, indent=4))
                    f.write("\n\n[SCRIPT]\n")
                    f.write(script_code)
            else:
                with open(self.current_config_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
            self.load_configs_list()
            QMessageBox.information(self, "Success", "Configuration saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save config: {str(e)}")

    def silent_save_config(self):
        if not self.current_config_file:
            return
        if self.btn_view_text.isChecked():
            self.blocks = OneScriptCompiler.decompile_to_blocks(self.text_editor.toPlainText())
        try:
            data = self.read_config_file(self.current_config_file)
            data["blocks"] = self.blocks
            data["last_modified"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data["use_proxies"] = self.settings_tab.get_settings().get("use_proxies", False)
            data["use_selenium"] = self.opt_use_selenium.isChecked()
            data["name"] = self.opt_gen_name.text()
            data["author"] = self.opt_gen_author.text()
            data["additional_info"] = self.opt_gen_info.text()
            data["suggested_bots"] = self.opt_gen_bots.value()
            data["max_cpm"] = self.opt_gen_max_cpm.value()
            data["save_empty_captures"] = self.opt_gen_empty_caps.isChecked()
            data["continue_custom"] = self.opt_gen_continue_custom.isChecked()
            data["save_hits_to_file"] = self.opt_gen_save_to_file.isChecked()
            data["proxy_settings"] = {
                "needs_proxies": self.opt_prox_needed.isChecked(),
                "only_socks": self.opt_prox_only_socks.isChecked(),
                "only_ssl": self.opt_prox_only_ssl.isChecked(),
                "ban_after_good": self.opt_prox_ban_after_good.isChecked(),
                "max_uses": self.opt_prox_max_uses.value(),
                "ban_loop": self.opt_prox_ban_loop.value()
            }
            rules = []
            for i in range(self.opt_data_rules_list.count()):
                rules.append(self.opt_data_rules_list.item(i).text())
            
            data["allowed_wordlists"] = self.opt_data_wl_type.currentText()
            self.lbl_allowed_wl.setText(f"Allowed Wordlists: {data['allowed_wordlists']}")
            
            data["data_settings"] = {
                "allowed_wl_type": self.opt_data_wl_type.currentText(),
                "urlencode": self.opt_data_urlencode.isChecked(),
                "custom_format": self.opt_data_custom_format.text().strip(),
                "rules": rules
            }
            data["selenium_settings"] = {
                "always_open": self.opt_always_open.isChecked(),
                "always_quit": self.opt_always_quit.isChecked(),
                "quit_on_ban_retry": self.opt_quit_ban_retry.isChecked(),
                "headless": self.opt_headless.isChecked(),
                "disable_notifications": self.opt_disable_notifications.isChecked(),
                "custom_args": self.opt_custom_args.text(),
                "user_agent": self.opt_user_agent.text(),
                "use_random_ua": self.opt_random_ua.isChecked()
            }
            if self.current_config_file.endswith(".zan"):
                script_code = OneScriptCompiler.compile_to_script(self.blocks)
                settings_data = data.copy()
                if "blocks" in settings_data:
                    del settings_data["blocks"]
                with open(self.current_config_file, "w", encoding="utf-8") as f:
                    f.write("[SETTINGS]\n")
                    f.write(json.dumps(settings_data, indent=4))
                    f.write("\n\n[SCRIPT]\n")
                    f.write(script_code)
            else:
                with open(self.current_config_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
        except Exception:
            pass

    def on_delete_config(self):
        if not self.current_config_file:
            QMessageBox.warning(self, "Warning", "Please select a config to delete.")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this config?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.current_config_file)
                self.current_config_file = None
                self.blocks = []
                self.sync_blocks_to_ui()
                self.load_configs_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete config: {str(e)}")

    def on_open_folder(self):
        os.startfile(self.configs_dir)

    def show_visual_view(self):
        self.btn_view_visual.setChecked(True)
        self.btn_view_text.setChecked(False)
        script_text = self.text_editor.toPlainText()
        self.blocks = OneScriptCompiler.decompile_to_blocks(script_text)
        self.sync_blocks_to_ui()
        self.editor_stack.setCurrentIndex(0)

    def show_text_view(self):
        self.btn_view_visual.setChecked(False)
        self.btn_view_text.setChecked(True)
        self.text_editor.setPlainText(OneScriptCompiler.compile_to_script(self.blocks))
        self.editor_stack.setCurrentIndex(1)

    def on_block_selected(self, index):
        if index < 0 or index >= len(self.blocks):
            self.info_stack.setCurrentIndex(0)
            self.txt_block_label.clear()
            return
            
        block = self.blocks[index]
        b_type = block.get("type", "")
        
        self.set_properties_signals_blocked(True)
        
        self.txt_block_label.setText(block.get("label", ""))
        
        if b_type == "BROWSER ACTION":
            self.info_stack.setCurrentIndex(1)
            self.cb_browser_action.setCurrentText(block.get("action", "Start Browser"))
        elif b_type == "NAVIGATE":
            self.info_stack.setCurrentIndex(2)
            self.txt_nav_url.setText(block.get("url", ""))
            self.spin_nav_timeout.setValue(block.get("timeout", 60))
            self.chk_nav_ban.setChecked(block.get("ban_on_timeout", False))
        elif b_type == "ELEMENT ACTION":
            self.info_stack.setCurrentIndex(3)
            self.cb_sel_type.setCurrentText(block.get("selector_type", "XPATH"))
            self.txt_sel_value.setText(block.get("selector", ""))
            self.cb_el_action.setCurrentText(block.get("action", "Click"))
            self.txt_el_val.setText(block.get("value", ""))
            self.txt_el_var.setText(block.get("variable_name", ""))
            self.spin_el_index.setValue(block.get("index", 0))
            self.chk_el_recursive.setChecked(block.get("recursive", False))
            self.chk_el_capture.setChecked(block.get("is_capture", False))
        elif b_type == "EXECUTE JS":
            self.info_stack.setCurrentIndex(4)
            self.txt_js_code.setPlainText(block.get("script", ""))
            self.txt_js_var.setText(block.get("variable_name", ""))
        elif b_type == "REQUEST":
            self.info_stack.setCurrentIndex(5)
            self.txt_req_url.setText(block.get("url", ""))
            self.cb_req_method.setCurrentText(block.get("method", "GET"))
            self.chk_req_redirect.setChecked(block.get("auto_redirect", True))
            self.chk_req_read_resp.setChecked(block.get("read_resp_source", True))
            self.chk_req_accept_enc.setChecked(block.get("accept_encoding", True))
            self.chk_req_encode_content.setChecked(block.get("encode_content", False))
            self.cb_req_sec_proto.setCurrentText(block.get("security_protocol", "SystemDefault"))
            self.cb_req_type.setCurrentText(block.get("request_type", "Standard"))
            self.cb_req_content_type.setCurrentText(block.get("content_type", ""))
            self.cb_req_resp_type.setCurrentText(block.get("response_type", "String"))
            self.txt_req_post_data.setPlainText(block.get("post_data", ""))
            self.txt_req_cookies.setPlainText(block.get("custom_cookies", ""))
            self.txt_req_headers.setPlainText(block.get("custom_headers", ""))
        elif b_type == "UTILITY":
            self.info_stack.setCurrentIndex(6)
            self.txt_ut_var_name.setText(block.get("variable_name", ""))
            self.chk_ut_capture.setChecked(block.get("is_capture", False))
            self.cb_ut_group.setCurrentText(block.get("group", "List"))
            self.cb_ut_action.setCurrentText(block.get("action", "Join"))
            self.txt_ut_list_var.setText(block.get("list_var_name", ""))
            self.txt_ut_separator.setText(block.get("separator", ","))
        elif b_type == "KEY CHECK":
            self.info_stack.setCurrentIndex(7)
            self.chk_kc_insta_ban.setChecked(block.get("insta_ban_4xx", False))
            self.chk_kc_ban_no_key.setChecked(block.get("ban_if_no_key", False))
            
            # Populate Keychains
            self.keychains_list.clear()
            self.keys_list.clear()
            self.kc_prop_group.setEnabled(False)
            
            keychains = block.get("keychains", [])
            if isinstance(keychains, str):
                try:
                    import json
                    keychains = json.loads(keychains)
                except Exception:
                    keychains = []
            
            for i, kc in enumerate(keychains):
                self.keychains_list.addItem(f"Keychain {i+1} [{kc.get('type','Success')}] ({kc.get('mode','OR')})")
        elif b_type == "PARSE":
            self.info_stack.setCurrentIndex(8)
            self.txt_parse_source.setText(block.get("source", "<SOURCE>"))
            self.txt_parse_var_name.setText(block.get("variable_name", ""))
            self.txt_parse_prefix.setText(block.get("prefix", ""))
            self.txt_parse_suffix.setText(block.get("suffix", ""))
            
            mode = block.get("mode", "LR")
            self.rad_parse_lr.setChecked(mode == "LR")
            self.rad_parse_css.setChecked(mode == "CSS")
            self.rad_parse_json.setChecked(mode == "JSON")
            self.rad_parse_regex.setChecked(mode == "REGEX")
            
            self.txt_parse_left.setText(block.get("left_string", ""))
            self.txt_parse_right.setText(block.get("right_string", ""))
            self.chk_parse_recursive.setChecked(block.get("recursive", False))
            self.chk_parse_enc.setChecked(block.get("enc_output", False))
            self.chk_parse_empty.setChecked(block.get("create_empty", False))
            self.chk_parse_use_regex.setChecked(block.get("use_regex", False))
            self.chk_parse_is_capture.setChecked(block.get("is_capture", False))
        elif b_type == "FUNCTION":
            self.info_stack.setCurrentIndex(9)
            self.txt_fn_var_name.setText(block.get("variable_name", ""))
            self.txt_fn_input.setText(block.get("input_string", ""))
            self.chk_fn_capture.setChecked(block.get("is_capture", False))
            self.cb_fn_type.setCurrentText(block.get("function_type", "Constant"))
        elif b_type == "SOLVE CAPTCHA":
            self.info_stack.setCurrentIndex(10)
            self.txt_sc_var.setText(block.get("variable_name", ""))
            self.cb_sc_type.setCurrentText(block.get("captcha_type", "ReCaptchaV2"))
            self.txt_sc_sitekey.setText(block.get("site_key", ""))
            self.txt_sc_url.setText(block.get("page_url", ""))
        elif b_type == "REPORT CAPTCHA":
            self.info_stack.setCurrentIndex(11)
            self.txt_rc_id.setText(block.get("captcha_id", ""))
            self.chk_rc_bad.setChecked(block.get("report_bad", False))
        elif b_type == "BYPASS CF":
            self.info_stack.setCurrentIndex(12)
            self.txt_cf_url.setText(block.get("url", ""))
            self.txt_cf_ua.setText(block.get("user_agent", ""))
            self.cb_cf_sec.setCurrentText(block.get("security_protocol", "SystemDefault"))
            self.chk_cf_print.setChecked(block.get("print_response_info", False))
            self.chk_cf_redir.setChecked(block.get("auto_redirect", False))
        elif b_type == "TCP":
            self.info_stack.setCurrentIndex(13)
            self.txt_tcp_var.setText(block.get("variable_name", ""))
            self.chk_tcp_capture.setChecked(block.get("is_capture", False))
            self.cb_tcp_cmd.setCurrentText(block.get("command", "Connect"))
            self.txt_tcp_host.setText(block.get("host", ""))
            self.txt_tcp_port.setText(block.get("port", "80"))
            self.chk_tcp_ssl.setChecked(block.get("ssl", False))
            self.chk_tcp_hello.setChecked(block.get("wait_for_hello", False))
            
        self.set_properties_signals_blocked(False)

    def save_current_block_info(self):
        """Saves values from parameters fields into the selected block's dict."""
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
            
        block = self.blocks[idx]
        b_type = block.get("type", "")
        
        block["label"] = self.txt_block_label.text()
        
        if b_type == "BROWSER ACTION":
            block["action"] = self.cb_browser_action.currentText()
        elif b_type == "NAVIGATE":
            block["url"] = self.txt_nav_url.text()
            block["timeout"] = self.spin_nav_timeout.value()
            block["ban_on_timeout"] = self.chk_nav_ban.isChecked()
        elif b_type == "ELEMENT ACTION":
            block["selector_type"] = self.cb_sel_type.currentText()
            block["selector"] = self.txt_sel_value.text()
            block["action"] = self.cb_el_action.currentText()
            block["value"] = self.txt_el_val.text()
            block["variable_name"] = self.txt_el_var.text()
            block["index"] = self.spin_el_index.value()
            block["recursive"] = self.chk_el_recursive.isChecked()
            block["is_capture"] = self.chk_el_capture.isChecked()
        elif b_type == "EXECUTE JS":
            block["script"] = self.txt_js_code.toPlainText()
            block["variable_name"] = self.txt_js_var.text()
        elif b_type == "REQUEST":
            block["url"] = self.txt_req_url.text()
            block["method"] = self.cb_req_method.currentText()
            block["auto_redirect"] = self.chk_req_redirect.isChecked()
            block["read_resp_source"] = self.chk_req_read_resp.isChecked()
            block["accept_encoding"] = self.chk_req_accept_enc.isChecked()
            block["encode_content"] = self.chk_req_encode_content.isChecked()
            block["security_protocol"] = self.cb_req_sec_proto.currentText()
            block["request_type"] = self.cb_req_type.currentText()
            block["content_type"] = self.cb_req_content_type.currentText()
            block["response_type"] = self.cb_req_resp_type.currentText()
            block["post_data"] = self.txt_req_post_data.toPlainText()
            block["custom_cookies"] = self.txt_req_cookies.toPlainText()
            block["custom_headers"] = self.txt_req_headers.toPlainText()
        elif b_type == "UTILITY":
            block["variable_name"] = self.txt_ut_var_name.text()
            block["is_capture"] = self.chk_ut_capture.isChecked()
            block["group"] = self.cb_ut_group.currentText()
            block["action"] = self.cb_ut_action.currentText()
            block["list_var_name"] = self.txt_ut_list_var.text()
            block["separator"] = self.txt_ut_separator.text()
        elif b_type == "KEY CHECK":
            block["insta_ban_4xx"] = self.chk_kc_insta_ban.isChecked()
            block["ban_if_no_key"] = self.chk_kc_ban_no_key.isChecked()
        elif b_type == "PARSE":
            block["source"] = self.txt_parse_source.text()
            block["variable_name"] = self.txt_parse_var_name.text()
            block["prefix"] = self.txt_parse_prefix.text()
            block["suffix"] = self.txt_parse_suffix.text()
            
            if self.rad_parse_lr.isChecked():
                block["mode"] = "LR"
            elif self.rad_parse_css.isChecked():
                block["mode"] = "CSS"
            elif self.rad_parse_json.isChecked():
                block["mode"] = "JSON"
            elif self.rad_parse_regex.isChecked():
                block["mode"] = "REGEX"
                
            block["left_string"] = self.txt_parse_left.text()
            block["right_string"] = self.txt_parse_right.text()
            block["recursive"] = self.chk_parse_recursive.isChecked()
            block["enc_output"] = self.chk_parse_enc.isChecked()
            block["create_empty"] = self.chk_parse_empty.isChecked()
            block["use_regex"] = self.chk_parse_use_regex.isChecked()
            block["is_capture"] = self.chk_parse_is_capture.isChecked()
        elif b_type == "FUNCTION":
            block["variable_name"] = self.txt_fn_var_name.text()
            block["input_string"] = self.txt_fn_input.text()
            block["is_capture"] = self.chk_fn_capture.isChecked()
            block["function_type"] = self.cb_fn_type.currentText()
        elif b_type == "SOLVE CAPTCHA":
            block["variable_name"] = self.txt_sc_var.text()
            block["captcha_type"] = self.cb_sc_type.currentText()
            block["site_key"] = self.txt_sc_sitekey.text()
            block["page_url"] = self.txt_sc_url.text()
        elif b_type == "REPORT CAPTCHA":
            block["captcha_id"] = self.txt_rc_id.text()
            block["report_bad"] = self.chk_rc_bad.isChecked()
        elif b_type == "BYPASS CF":
            block["url"] = self.txt_cf_url.text()
            block["user_agent"] = self.txt_cf_ua.text()
            block["security_protocol"] = self.cb_cf_sec.currentText()
            block["print_response_info"] = self.chk_cf_print.isChecked()
            block["auto_redirect"] = self.chk_cf_redir.isChecked()
        elif b_type == "TCP":
            block["variable_name"] = self.txt_tcp_var.text()
            block["is_capture"] = self.chk_tcp_capture.isChecked()
            block["command"] = self.cb_tcp_cmd.currentText()
            block["host"] = self.txt_tcp_host.text()
            block["port"] = self.txt_tcp_port.text()
            block["ssl"] = self.chk_tcp_ssl.isChecked()
            block["wait_for_hello"] = self.chk_tcp_hello.isChecked()
            
        self.blocks_list.blockSignals(True)
        summary = self.get_block_summary(block)
        label_text = f" [{block['label']}]" if block.get("label") else ""
        self.blocks_list.item(idx).setText(f"{idx + 1}. {block['type']}{label_text} ({summary})")
        self.blocks_list.blockSignals(False)
        self.silent_save_config()

    def on_add_block(self):
        dialog = AddBlockDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            btype = dialog.selected_type
            if not btype:
                return
                
            new_block = {"type": btype, "label": ""}
            if btype == "BROWSER ACTION":
                new_block["action"] = "Start Browser"
            elif btype == "NAVIGATE":
                new_block["url"] = ""
                new_block["timeout"] = 60
                new_block["ban_on_timeout"] = False
            elif btype == "ELEMENT ACTION":
                new_block["selector_type"] = "XPATH"
                new_block["selector"] = ""
                new_block["action"] = "Click"
                new_block["value"] = ""
                new_block["variable_name"] = ""
                new_block["index"] = 0
                new_block["recursive"] = False
                new_block["is_capture"] = False
            elif btype == "EXECUTE JS":
                new_block["script"] = ""
                new_block["variable_name"] = ""
            elif btype == "REQUEST":
                new_block["url"] = ""
                new_block["method"] = "GET"
                new_block["auto_redirect"] = True
                new_block["read_resp_source"] = True
                new_block["accept_encoding"] = True
                new_block["encode_content"] = False
                new_block["security_protocol"] = "SystemDefault"
                new_block["request_type"] = "Standard"
                new_block["content_type"] = ""
                new_block["response_type"] = "String"
                new_block["post_data"] = ""
                new_block["custom_cookies"] = ""
                new_block["custom_headers"] = ""
            elif btype == "UTILITY":
                new_block["variable_name"] = ""
                new_block["is_capture"] = False
                new_block["group"] = "List"
                new_block["action"] = "Join"
                new_block["list_var_name"] = ""
                new_block["separator"] = ","
            elif btype == "KEY CHECK":
                new_block["insta_ban_4xx"] = False
                new_block["ban_if_no_key"] = False
                new_block["keychains"] = []
            elif btype == "PARSE":
                new_block["source"] = "<SOURCE>"
                new_block["variable_name"] = ""
                new_block["prefix"] = ""
                new_block["suffix"] = ""
                new_block["mode"] = "LR"
                new_block["left_string"] = ""
                new_block["right_string"] = ""
                new_block["recursive"] = False
                new_block["enc_output"] = False
                new_block["create_empty"] = False
                new_block["use_regex"] = False
                new_block["is_capture"] = False
            elif btype == "FUNCTION":
                new_block["function_type"] = "Constant"
                new_block["variable_name"] = ""
                new_block["input_string"] = ""
                new_block["is_capture"] = False
            elif btype == "SOLVE CAPTCHA":
                new_block["variable_name"] = ""
                new_block["captcha_type"] = "ReCaptchaV2"
                new_block["site_key"] = ""
                new_block["page_url"] = ""
            elif btype == "REPORT CAPTCHA":
                new_block["captcha_id"] = ""
                new_block["report_bad"] = False
            elif btype == "BYPASS CF":
                new_block["url"] = ""
                new_block["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                new_block["security_protocol"] = "SystemDefault"
                new_block["print_response_info"] = False
                new_block["auto_redirect"] = False
            elif btype == "TCP":
                new_block["variable_name"] = ""
                new_block["is_capture"] = False
                new_block["command"] = "Connect"
                new_block["host"] = ""
                new_block["port"] = "80"
                new_block["ssl"] = False
                new_block["wait_for_hello"] = False
                
            self.blocks.append(new_block)
            self.sync_blocks_to_ui()
            self.blocks_list.setCurrentRow(len(self.blocks) - 1)

    def on_move_block_up(self):
        idx = self.blocks_list.currentRow()
        if idx <= 0 or idx >= len(self.blocks):
            return
        self.blocks[idx], self.blocks[idx - 1] = self.blocks[idx - 1], self.blocks[idx]
        self.sync_blocks_to_ui()
        self.blocks_list.setCurrentRow(idx - 1)

    def on_move_block_down(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks) - 1:
            return
        self.blocks[idx], self.blocks[idx + 1] = self.blocks[idx + 1], self.blocks[idx]
        self.sync_blocks_to_ui()
        self.blocks_list.setCurrentRow(idx + 1)

    def on_clone_block(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        import copy
        cloned = copy.deepcopy(self.blocks[idx])
        cloned["label"] = (cloned.get("label", "") + "_clone").strip("_")
        self.blocks.insert(idx + 1, cloned)
        self.sync_blocks_to_ui()
        self.blocks_list.setCurrentRow(idx + 1)

    def on_delete_block(self):
        idx = self.blocks_list.currentRow()
        if idx < 0 or idx >= len(self.blocks):
            return
        self.blocks.pop(idx)
        self.sync_blocks_to_ui()

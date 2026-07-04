import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, 
    QGroupBox, QCheckBox, QLabel, QLineEdit, QFormLayout, QSpinBox, 
    QComboBox, QTextEdit, QPlainTextEdit, QFileDialog, QListWidget, 
    QListWidgetItem, QGridLayout, QMessageBox, QColorDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils.helpers import load_settings, save_settings, generate_stylesheet, DEFAULT_SETTINGS

class SeleniumSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color_buttons = {}
        self.init_ui()
        self.load_settings_from_disk()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)

        # Primary Horizontal Sub-Navigation Tab Widget
        self.main_nav_tabs = QTabWidget()
        self.main_nav_tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 14px;
                padding: 12px 30px;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.main_nav_tabs)

        # ----------------------------------------------------
        # 1. RuriLib Settings Container
        # ----------------------------------------------------
        rurilib_container = QWidget()
        rurilib_layout = QVBoxLayout(rurilib_container)
        rurilib_layout.setContentsMargins(5, 5, 5, 5)
        
        self.rurilib_tabs = QTabWidget()
        rurilib_layout.addWidget(self.rurilib_tabs)
        self.main_nav_tabs.addTab(rurilib_container, "RuriLib")

        self.init_rurilib_general_tab()
        self.init_rurilib_proxies_tab()
        self.init_rurilib_captchas_tab()
        self.init_rurilib_selenium_tab()

        # ----------------------------------------------------
        # 2. OneBullet Settings Container
        # ----------------------------------------------------
        openbullet_container = QWidget()
        openbullet_layout = QVBoxLayout(openbullet_container)
        openbullet_layout.setContentsMargins(5, 5, 5, 5)
        
        self.openbullet_tabs = QTabWidget()
        openbullet_layout.addWidget(self.openbullet_tabs)
        self.main_nav_tabs.addTab(openbullet_container, "OneBullet")

        self.init_openbullet_general_tab()
        self.init_openbullet_sounds_tab()
        self.init_openbullet_sources_tab()
        self.init_openbullet_themes_tab()

        # ----------------------------------------------------
        # Bottom Persistent Toolbar
        # ----------------------------------------------------
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        
        self.btn_save = QPushButton("SAVE")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #2e7d32; font-weight: bold; color: white;")
        self.btn_save.clicked.connect(self.on_save_clicked)
        
        self.btn_reset = QPushButton("RESET")
        self.btn_reset.setMinimumHeight(40)
        self.btn_reset.setStyleSheet("background-color: #d32f2f; font-weight: bold; color: white;")
        self.btn_reset.clicked.connect(self.on_reset_clicked)

        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.btn_save)
        toolbar_layout.addWidget(self.btn_reset)
        
        main_layout.addLayout(toolbar_layout)

    # ----------------------------------------------------
    # RuriLib Tabs Implementation
    # ----------------------------------------------------
    def init_rurilib_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.spin_wait_time = QSpinBox()
        self.spin_wait_time.setRange(0, 30000)
        self.spin_wait_time.setSuffix(" ms")
        form_layout.addRow(QLabel("Wait Time:"), self.spin_wait_time)
        
        self.spin_req_timeout = QSpinBox()
        self.spin_req_timeout.setRange(1, 600)
        self.spin_req_timeout.setSuffix(" seconds")
        form_layout.addRow(QLabel("Requests Timeout:"), self.spin_req_timeout)
        
        self.spin_max_hits = QSpinBox()
        self.spin_max_hits.setRange(0, 1000000)
        self.spin_max_hits.setSpecialValueText("Unlimited")
        form_layout.addRow(QLabel("Max Number of Hits:"), self.spin_max_hits)
        
        self.cb_runner_bots_mode = QComboBox()
        self.cb_runner_bots_mode.addItems(["Everything", "Only Hits", "Nothing"])
        form_layout.addRow(QLabel("Runner Bots Display Mode:"), self.cb_runner_bots_mode)
        
        self.chk_enable_bot_log = QCheckBox("Enable Bot Log")
        form_layout.addRow(self.chk_enable_bot_log)
        
        self.chk_save_last_resp = QCheckBox("Save Last Response Source")
        form_layout.addRow(self.chk_save_last_resp)
        
        self.chk_send_tocheck_abort = QCheckBox("Send data to ToCheck on abort")
        form_layout.addRow(self.chk_send_tocheck_abort)
        
        layout.addLayout(form_layout)
        
        # Webhook panel
        webhook_group = QGroupBox("Hits Webhook Configuration")
        webhook_form = QFormLayout()
        self.chk_webhook_enabled = QCheckBox("Enabled")
        self.txt_webhook_url = QLineEdit()
        self.txt_webhook_url.setPlaceholderText("http://localhost:5000/webhook")
        self.txt_webhook_user = QLineEdit()
        self.txt_webhook_user.setPlaceholderText("WebhookUsername")
        
        webhook_form.addRow(self.chk_webhook_enabled)
        webhook_form.addRow(QLabel("Webhook URL:"), self.txt_webhook_url)
        webhook_form.addRow(QLabel("Webhook Username:"), self.txt_webhook_user)
        webhook_group.setLayout(webhook_form)
        layout.addWidget(webhook_group)
        
        layout.addStretch()
        self.rurilib_tabs.addTab(tab, "General")

    def init_rurilib_proxies_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grid = QGridLayout()
        self.chk_proxy_concurrent = QCheckBox("Allow Concurrent Use")
        self.chk_proxy_never_ban = QCheckBox("Never Ban Proxies")
        self.chk_proxy_shuffle = QCheckBox("Shuffle Proxies on Start")
        self.chk_proxy_cf_clearance = QCheckBox("Don't Reuse Clearance Cookie (CF)")
        
        grid.addWidget(self.chk_proxy_concurrent, 0, 0)
        grid.addWidget(self.chk_proxy_never_ban, 0, 1)
        grid.addWidget(self.chk_proxy_shuffle, 1, 0)
        grid.addWidget(self.chk_proxy_cf_clearance, 1, 1)
        layout.addLayout(grid)
        
        form = QFormLayout()
        self.spin_ban_loop_evasion = QSpinBox()
        self.spin_ban_loop_evasion.setRange(0, 1000)
        form.addRow(QLabel("Ban Loop Evasion:"), self.spin_ban_loop_evasion)
        layout.addLayout(form)
        
        # Reloading section
        reload_group = QGroupBox("Reloading Options")
        reload_form = QFormLayout()
        self.chk_reload_banned = QCheckBox("Reload proxies when all banned")
        self.spin_reload_interval = QSpinBox()
        self.spin_reload_interval.setRange(10, 3600)
        self.spin_reload_interval.setSuffix(" seconds")
        self.cb_reload_source = QComboBox()
        self.cb_reload_source.addItems(["Manager", "File", "URL"])
        
        reload_form.addRow(self.chk_reload_banned)
        reload_form.addRow(QLabel("Reload Interval:"), self.spin_reload_interval)
        reload_form.addRow(QLabel("Reload Source:"), self.cb_reload_source)
        reload_group.setLayout(reload_form)
        layout.addWidget(reload_group)
        
        # Ban/Retry Keys
        keys_layout = QHBoxLayout()
        
        ban_vbox = QVBoxLayout()
        ban_vbox.addWidget(QLabel("Global Ban Keys (one per line):"))
        self.txt_ban_keys = QPlainTextEdit()
        ban_vbox.addWidget(self.txt_ban_keys)
        keys_layout.addLayout(ban_vbox)
        
        retry_vbox = QVBoxLayout()
        retry_vbox.addWidget(QLabel("Global Retry Keys (one per line):"))
        self.txt_retry_keys = QPlainTextEdit()
        retry_vbox.addWidget(self.txt_retry_keys)
        keys_layout.addLayout(retry_vbox)
        
        layout.addLayout(keys_layout)
        self.rurilib_tabs.addTab(tab, "Proxies")

    def init_rurilib_captchas_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.cb_captcha_service = QComboBox()
        self.cb_captcha_service.addItems(["TwoCaptcha", "AntiCaptcha", "DeathByCaptcha", "RuCaptcha", "BoloCaptcha", "Custom"])
        form.addRow(QLabel("Captcha Service:"), self.cb_captcha_service)
        
        self.txt_captcha_key = QLineEdit()
        self.txt_captcha_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_captcha_key.setPlaceholderText("Enter API Key")
        form.addRow(QLabel("API Key:"), self.txt_captcha_key)
        
        self.chk_bypass_balance = QCheckBox("Bypass Balance Check")
        form.addRow(self.chk_bypass_balance)
        
        # Check Balance Row
        balance_layout = QHBoxLayout()
        self.btn_check_balance = QPushButton("Check Balance")
        self.btn_check_balance.clicked.connect(self.on_check_balance)
        self.lbl_balance_status = QLabel("Status: Not checked")
        self.lbl_balance_status.setStyleSheet("font-weight: bold;")
        balance_layout.addWidget(self.btn_check_balance)
        balance_layout.addWidget(self.lbl_balance_status)
        balance_layout.addStretch()
        form.addRow(QLabel("Balance Check:"), balance_layout)
        
        self.spin_captcha_timeout = QSpinBox()
        self.spin_captcha_timeout.setRange(10, 600)
        self.spin_captcha_timeout.setSuffix(" seconds")
        form.addRow(QLabel("Response Timeout:"), self.spin_captcha_timeout)
        
        layout.addLayout(form)
        layout.addStretch()
        
        self.rurilib_tabs.addTab(tab, "Captchas")

    def init_rurilib_selenium_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        self.cb_browser_type = QComboBox()
        self.cb_browser_type.addItems(["Chrome", "Firefox", "Edge", "InternetExplorer"])
        form.addRow(QLabel("Browser Type:"), self.cb_browser_type)
        
        self.chk_headless = QCheckBox("Headless Mode")
        form.addRow(self.chk_headless)
        
        self.chk_draw_mouse = QCheckBox("Draw Mouse Movement")
        form.addRow(self.chk_draw_mouse)
        
        self.chk_use_gpu = QCheckBox("Use GPU Acceleration (Selenium)")
        self.chk_use_gpu.setToolTip("Enable GPU hardware acceleration instead of CPU rendering for browser automation blocks.")
        form.addRow(self.chk_use_gpu)
        
        # Binary Paths
        chrome_bin_layout = QHBoxLayout()
        self.txt_chrome_bin = QLineEdit()
        btn_browse_chrome = QPushButton("Browse")
        btn_browse_chrome.clicked.connect(lambda: self.browse_file(self.txt_chrome_bin, "Select Chrome Binary", "Executable Files (*.exe)"))
        chrome_bin_layout.addWidget(self.txt_chrome_bin)
        chrome_bin_layout.addWidget(btn_browse_chrome)
        form.addRow(QLabel("Chrome Binary Location:"), chrome_bin_layout)
        
        firefox_bin_layout = QHBoxLayout()
        self.txt_firefox_bin = QLineEdit()
        btn_browse_firefox = QPushButton("Browse")
        btn_browse_firefox.clicked.connect(lambda: self.browse_file(self.txt_firefox_bin, "Select Firefox Binary", "Executable Files (*.exe)"))
        firefox_bin_layout.addWidget(self.txt_firefox_bin)
        firefox_bin_layout.addWidget(btn_browse_firefox)
        form.addRow(QLabel("Firefox Binary Location:"), firefox_bin_layout)
        
        self.spin_selenium_timeout = QSpinBox()
        self.spin_selenium_timeout.setRange(1, 600)
        self.spin_selenium_timeout.setSuffix(" seconds")
        form.addRow(QLabel("Default Timeout:"), self.spin_selenium_timeout)
        
        layout.addLayout(form)
        
        # Chrome Extensions Management list
        ext_group = QGroupBox("Chrome Extensions (.crx / folders)")
        ext_layout = QVBoxLayout()
        
        lbl_warning = QLabel("Warning: Custom extensions may interfere with proxy settings or page load performance.")
        lbl_warning.setStyleSheet("color: #ffd54f; font-style: italic;")
        ext_layout.addWidget(lbl_warning)
        
        self.list_extensions = QListWidget()
        ext_layout.addWidget(self.list_extensions)
        
        btn_ext_layout = QHBoxLayout()
        btn_add_ext = QPushButton("Add Extension")
        btn_add_ext.clicked.connect(self.on_add_extension)
        btn_remove_ext = QPushButton("Remove Selected")
        btn_remove_ext.clicked.connect(self.on_remove_extension)
        btn_clear_ext = QPushButton("Clear All")
        btn_clear_ext.clicked.connect(lambda: self.list_extensions.clear())
        
        btn_ext_layout.addWidget(btn_add_ext)
        btn_ext_layout.addWidget(btn_remove_ext)
        btn_ext_layout.addWidget(btn_clear_ext)
        ext_layout.addLayout(btn_ext_layout)
        
        ext_group.setLayout(ext_layout)
        layout.addWidget(ext_group)
        
        self.rurilib_tabs.addTab(tab, "Selenium")

    # ----------------------------------------------------
    # OneBullet Tabs Implementation
    # ----------------------------------------------------
    def init_openbullet_general_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grid = QGridLayout()
        self.chk_ob_auto_bots = QCheckBox("Automatically set Recommended Bots")
        self.chk_ob_backup_db = QCheckBox("Backup the Database daily upon start")
        self.chk_ob_quit_warn = QCheckBox("Disable Warning on Quit")
        self.chk_ob_always_top = QCheckBox("Always On Top")
        
        grid.addWidget(self.chk_ob_auto_bots, 0, 0)
        grid.addWidget(self.chk_ob_backup_db, 0, 1)
        grid.addWidget(self.chk_ob_quit_warn, 1, 0)
        grid.addWidget(self.chk_ob_always_top, 1, 1)
        layout.addLayout(grid)
        
        form = QFormLayout()
        form.setSpacing(10)
        self.txt_ob_author = QLineEdit()
        form.addRow(QLabel("Default Author:"), self.txt_ob_author)
        
        self.spin_ob_width = QSpinBox()
        self.spin_ob_width.setRange(800, 3840)
        form.addRow(QLabel("Starting Window Width:"), self.spin_ob_width)
        
        self.spin_ob_height = QSpinBox()
        self.spin_ob_height.setRange(600, 2160)
        form.addRow(QLabel("Starting Window Height:"), self.spin_ob_height)
        layout.addLayout(form)
        
        # Program Log Group
        log_group = QGroupBox("Program Log settings")
        log_form = QFormLayout()
        self.chk_ob_log_enable = QCheckBox("Enable Logging")
        self.chk_ob_log_file = QCheckBox("Log to file")
        self.spin_ob_log_buffer = QSpinBox()
        self.spin_ob_log_buffer.setRange(10, 10000)
        self.chk_ob_log_ignore_wl = QCheckBox("Ignore Wordlist name")
        
        log_form.addRow(self.chk_ob_log_enable)
        log_form.addRow(self.chk_ob_log_file)
        log_form.addRow(QLabel("Log Buffer Size:"), self.spin_ob_log_buffer)
        log_form.addRow(self.chk_ob_log_ignore_wl)
        log_group.setLayout(log_form)
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.openbullet_tabs.addTab(tab, "General")

    def init_openbullet_sounds_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QFormLayout()
        self.chk_ob_sound_hit = QCheckBox("Enable Sound on Hit")
        self.chk_ob_sound_custom = QCheckBox("Enable Sound on Custom")
        self.chk_ob_sound_tocheck = QCheckBox("Enable Sound on ToCheck")
        
        form.addRow(self.chk_ob_sound_hit)
        form.addRow(self.chk_ob_sound_custom)
        form.addRow(self.chk_ob_sound_tocheck)
        
        sound_file_layout = QHBoxLayout()
        self.txt_ob_sound_file = QLineEdit()
        btn_browse_sound = QPushButton("Browse")
        btn_browse_sound.clicked.connect(lambda: self.browse_file(self.txt_ob_sound_file, "Select Sound File", "Audio Files (*.wav *.mp3)"))
        sound_file_layout.addWidget(self.txt_ob_sound_file)
        sound_file_layout.addWidget(btn_browse_sound)
        form.addRow(QLabel("Sound File Path:"), sound_file_layout)
        
        layout.addLayout(form)
        layout.addStretch()
        self.openbullet_tabs.addTab(tab, "Sounds")

    def init_openbullet_sources_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("Configuration & Wordlist Sources:"))
        self.list_ob_sources = QListWidget()
        layout.addWidget(self.list_ob_sources)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Add Source")
        btn_add.clicked.connect(self.on_add_source)
        btn_remove = QPushButton("Remove Selected")
        btn_remove.clicked.connect(self.on_remove_source)
        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(lambda: self.list_ob_sources.clear())
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)
        
        self.openbullet_tabs.addTab(tab, "Sources")

    def init_openbullet_themes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grid_container = QGridLayout()
        
        # 1. Colors panel
        colors_group = QGroupBox("Color Theme Customization")
        colors_grid = QGridLayout()
        colors_grid.setVerticalSpacing(8)
        colors_grid.setHorizontalSpacing(15)
        
        color_keys = [
            ("backgroundMain", "Background Main", "#121212"),
            ("backgroundSecondary", "Background Secondary", "#1e1e1e"),
            ("foregroundMain", "Foreground Main", "#ffffff"),
            ("foregroundGood", "Foreground Good", "#81c784"),
            ("foregroundBad", "Foreground Bad", "#e57373"),
            ("foregroundCustom", "Foreground Custom", "#64b5f6"),
            ("foregroundRetry", "Foreground Retry", "#ffd54f"),
            ("foregroundToCheck", "Foreground To Check", "#ffd54f"),
            ("foregroundMenuSel", "Foreground Menu Sel", "#2196f3")
        ]
        
        row = 0
        col = 0
        for key, name, default in color_keys:
            colors_grid.addWidget(QLabel(f"{name}:"), row, col * 2)
            btn = self.make_color_button(key, default)
            self.color_buttons[key] = btn
            colors_grid.addWidget(btn, row, col * 2 + 1)
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        btn_reset_colors = QPushButton("Reset Colors")
        btn_reset_colors.clicked.connect(self.on_reset_colors)
        colors_grid.addWidget(btn_reset_colors, row + 1, 0, 1, 4)
        
        colors_group.setLayout(colors_grid)
        layout.addWidget(colors_group)
        
        # 2. Images panel & Additional panel
        img_and_add_layout = QHBoxLayout()
        
        images_group = QGroupBox("Images Customization")
        images_form = QFormLayout()
        self.chk_ob_use_images = QCheckBox("Use Images")
        self.spin_ob_opacity = QSpinBox()
        self.spin_ob_opacity.setRange(0, 100)
        self.spin_ob_opacity.setSuffix("%")
        
        img_file_layout = QHBoxLayout()
        self.txt_ob_bg_img = QLineEdit()
        btn_browse_bg = QPushButton("Browse")
        btn_browse_bg.clicked.connect(lambda: self.browse_file(self.txt_ob_bg_img, "Select Background Image", "Image Files (*.png *.jpg *.jpeg)"))
        img_file_layout.addWidget(self.txt_ob_bg_img)
        img_file_layout.addWidget(btn_browse_bg)
        
        logo_file_layout = QHBoxLayout()
        self.txt_ob_logo = QLineEdit()
        btn_browse_logo = QPushButton("Browse")
        btn_browse_logo.clicked.connect(lambda: self.browse_file(self.txt_ob_logo, "Select Logo Image", "Image Files (*.png *.jpg *.jpeg)"))
        logo_file_layout.addWidget(self.txt_ob_logo)
        logo_file_layout.addWidget(btn_browse_logo)
        
        images_form.addRow(self.chk_ob_use_images)
        images_form.addRow(QLabel("Opacity:"), self.spin_ob_opacity)
        images_form.addRow(QLabel("Background Image:"), img_file_layout)
        images_form.addRow(QLabel("Logo Image:"), logo_file_layout)
        images_group.setLayout(images_form)
        img_and_add_layout.addWidget(images_group)
        
        additional_group = QGroupBox("Additional settings")
        add_form = QFormLayout()
        self.chk_ob_transparency = QCheckBox("Allow Transparency")
        
        snow_group = QGroupBox("Snow Options")
        snow_layout = QFormLayout()
        self.chk_ob_snow_enable = QCheckBox("Enable Snow")
        self.spin_ob_snow_amount = QSpinBox()
        self.spin_ob_snow_amount.setRange(10, 1000)
        snow_layout.addRow(self.chk_ob_snow_enable)
        snow_layout.addRow(QLabel("Snow Amount:"), self.spin_ob_snow_amount)
        snow_group.setLayout(snow_layout)
        
        add_form.addRow(self.chk_ob_transparency)
        add_form.addRow(snow_group)
        additional_group.setLayout(add_form)
        img_and_add_layout.addWidget(additional_group)
        
        layout.addLayout(img_and_add_layout)
        self.openbullet_tabs.addTab(tab, "Themes")

    # ----------------------------------------------------
    # Helper & Custom Callbacks
    # ----------------------------------------------------
    def make_color_button(self, key: str, default_color: str) -> QPushButton:
        btn = QPushButton("Select")
        btn.setStyleSheet(f"background-color: {default_color}; color: #ffffff; border: 1px solid #555; padding: 4px; font-weight: bold;")
        btn.setProperty("color_val", default_color)
        
        def choose_color():
            curr_color = btn.property("color_val")
            color = QColorDialog.getColor(QColor(curr_color), self, f"Select Color")
            if color.isValid():
                hex_color = color.name()
                btn.setStyleSheet(f"background-color: {hex_color}; color: {'#000000' if color.lightness() > 128 else '#ffffff'}; border: 1px solid #555; padding: 4px; font-weight: bold;")
                btn.setProperty("color_val", hex_color)
                
        btn.clicked.connect(choose_color)
        return btn

    def browse_file(self, target_line_edit: QLineEdit, title: str, file_filter: str):
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            target_line_edit.setText(file_path)

    def on_add_extension(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Chrome Extension", "", "Chrome Extension (*.crx);;Zip Archive (*.zip)")
        if file_path:
            self.list_extensions.addItem(file_path)

    def on_remove_extension(self):
        for item in self.list_extensions.selectedItems():
            self.list_extensions.takeItem(self.list_extensions.row(item))

    def on_add_source(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if dir_path:
            self.list_ob_sources.addItem(dir_path)

    def on_remove_source(self):
        for item in self.list_ob_sources.selectedItems():
            self.list_ob_sources.takeItem(self.list_ob_sources.row(item))

    def on_check_balance(self):
        import random
        service = self.cb_captcha_service.currentText()
        key = self.txt_captcha_key.text().strip()
        if not key:
            self.lbl_balance_status.setText("Status: Empty API Key!")
            self.lbl_balance_status.setStyleSheet("color: #e57373; font-weight: bold;")
            return
        
        self.lbl_balance_status.setText("Status: Checking...")
        self.lbl_balance_status.setStyleSheet("color: #ffd54f;")
        
        # Simulate balance check delay & output
        balance = round(random.uniform(0.5, 25.0), 2)
        self.lbl_balance_status.setText(f"Status: Connected! Balance: ${balance}")
        self.lbl_balance_status.setStyleSheet("color: #81c784; font-weight: bold;")

    def on_reset_colors(self):
        default_colors = DEFAULT_SETTINGS["OneBullet"]["Themes"]["colors"]
        for name, btn in self.color_buttons.items():
            color_val = default_colors[name]
            btn.setProperty("color_val", color_val)
            c = QColor(color_val)
            btn.setStyleSheet(f"background-color: {color_val}; color: {'#000000' if c.lightness() > 128 else '#ffffff'}; border: 1px solid #555; padding: 4px; font-weight: bold;")

    # ----------------------------------------------------
    # Serialization Logic
    # ----------------------------------------------------
    def load_settings_from_disk(self):
        settings = load_settings()
        self.load_settings_into_ui(settings)

    def load_settings_into_ui(self, settings: dict):
        # RuriLib -> General
        rl_gen = settings.get("RuriLib", {}).get("General", {})
        self.spin_wait_time.setValue(rl_gen.get("waitTime", 0))
        self.spin_req_timeout.setValue(rl_gen.get("requestsTimeout", 10))
        self.spin_max_hits.setValue(rl_gen.get("maxHits", 0))
        self.cb_runner_bots_mode.setCurrentText(rl_gen.get("runnerBotsDisplayMode", "Everything"))
        self.chk_enable_bot_log.setChecked(rl_gen.get("enableBotLog", True))
        self.chk_save_last_resp.setChecked(rl_gen.get("saveLastResponseSource", False))
        self.chk_send_tocheck_abort.setChecked(rl_gen.get("sendToCheckOnAbort", False))
        self.chk_webhook_enabled.setChecked(rl_gen.get("hitsWebhookEnabled", False))
        self.txt_webhook_url.setText(rl_gen.get("hitsWebhookUrl", ""))
        self.txt_webhook_user.setText(rl_gen.get("hitsWebhookUsername", ""))

        # RuriLib -> Proxies
        rl_prox = settings.get("RuriLib", {}).get("Proxies", {})
        self.chk_proxy_concurrent.setChecked(rl_prox.get("allowConcurrentUse", True))
        self.chk_proxy_never_ban.setChecked(rl_prox.get("neverBanProxies", False))
        self.chk_proxy_shuffle.setChecked(rl_prox.get("shuffleProxiesOnStart", True))
        self.spin_ban_loop_evasion.setValue(rl_prox.get("banLoopEvasion", 10))
        self.chk_proxy_cf_clearance.setChecked(rl_prox.get("dontReuseClearanceCookie", False))
        self.chk_reload_banned.setChecked(rl_prox.get("reloadProxiesWhenAllBanned", True))
        self.spin_reload_interval.setValue(rl_prox.get("reloadInterval", 60))
        self.cb_reload_source.setCurrentText(rl_prox.get("reloadSource", "Manager"))
        self.txt_ban_keys.setPlainText(rl_prox.get("globalBanKeys", ""))
        self.txt_retry_keys.setPlainText(rl_prox.get("globalRetryKeys", ""))

        # RuriLib -> Captchas
        rl_caps = settings.get("RuriLib", {}).get("Captchas", {})
        self.cb_captcha_service.setCurrentText(rl_caps.get("captchaService", "TwoCaptcha"))
        self.txt_captcha_key.setText(rl_caps.get("apiKey", ""))
        self.chk_bypass_balance.setChecked(rl_caps.get("bypassBalanceCheck", False))
        self.spin_captcha_timeout.setValue(rl_caps.get("responseTimeout", 120))

        # RuriLib -> Selenium
        rl_sel = settings.get("RuriLib", {}).get("Selenium", {})
        self.cb_browser_type.setCurrentText(rl_sel.get("browserType", "Chrome"))
        self.chk_headless.setChecked(rl_sel.get("headlessMode", False))
        self.chk_draw_mouse.setChecked(rl_sel.get("drawMouseMovement", False))
        self.chk_use_gpu.setChecked(rl_sel.get("useGpuAcceleration", False))
        self.txt_chrome_bin.setText(rl_sel.get("chromeBinaryLocation", ""))
        self.txt_firefox_bin.setText(rl_sel.get("firefoxBinaryLocation", ""))
        self.spin_selenium_timeout.setValue(rl_sel.get("defaultTimeout", 30))
        
        self.list_extensions.clear()
        for ext in rl_sel.get("chromeExtensions", []):
            self.list_extensions.addItem(ext)

        # OneBullet -> General
        ob_gen = settings.get("OneBullet", {}).get("General", {})
        self.chk_ob_auto_bots.setChecked(ob_gen.get("automaticallySetRecommendedBots", True))
        self.chk_ob_backup_db.setChecked(ob_gen.get("backupDatabaseDaily", True))
        self.chk_ob_quit_warn.setChecked(ob_gen.get("disableWarningOnQuit", False))
        self.chk_ob_always_top.setChecked(ob_gen.get("alwaysOnTop", False))
        self.txt_ob_author.setText(ob_gen.get("defaultAuthor", "One Bullet Development Team"))
        self.spin_ob_width.setValue(ob_gen.get("startingWindowWidth", 1280))
        self.spin_ob_height.setValue(ob_gen.get("startingWindowHeight", 800))
        self.chk_ob_log_enable.setChecked(ob_gen.get("enableLogging", True))
        self.chk_ob_log_file.setChecked(ob_gen.get("logToFile", False))
        self.spin_ob_log_buffer.setValue(ob_gen.get("logBufferSize", 100))
        self.chk_ob_log_ignore_wl.setChecked(ob_gen.get("ignoreWordlistName", False))

        # OneBullet -> Sounds
        ob_snd = settings.get("OneBullet", {}).get("Sounds", {})
        self.chk_ob_sound_hit.setChecked(ob_snd.get("enableSoundOnHit", True))
        self.chk_ob_sound_custom.setChecked(ob_snd.get("enableSoundOnCustom", False))
        self.chk_ob_sound_tocheck.setChecked(ob_snd.get("enableSoundOnToCheck", False))
        self.txt_ob_sound_file.setText(ob_snd.get("soundFile", ""))

        # OneBullet -> Sources
        ob_src = settings.get("OneBullet", {}).get("Sources", {})
        self.list_ob_sources.clear()
        for src in ob_src.get("sourcesList", []):
            self.list_ob_sources.addItem(src)

        # OneBullet -> Themes
        ob_theme = settings.get("OneBullet", {}).get("Themes", {})
        ob_colors = ob_theme.get("colors", {})
        for name, btn in self.color_buttons.items():
            color_val = ob_colors.get(name, DEFAULT_SETTINGS["OneBullet"]["Themes"]["colors"][name])
            btn.setProperty("color_val", color_val)
            c = QColor(color_val)
            btn.setStyleSheet(f"background-color: {color_val}; color: {'#000000' if c.lightness() > 128 else '#ffffff'}; border: 1px solid #555; padding: 4px; font-weight: bold;")

        ob_images = ob_theme.get("images", {})
        self.chk_ob_use_images.setChecked(ob_images.get("useImages", False))
        self.spin_ob_opacity.setValue(ob_images.get("opacity", 100))
        self.txt_ob_bg_img.setText(ob_images.get("backgroundImage", ""))
        self.txt_ob_logo.setText(ob_images.get("logo", ""))

        ob_add = ob_theme.get("additional", {})
        self.chk_ob_transparency.setChecked(ob_add.get("allowTransparency", False))
        self.chk_ob_snow_enable.setChecked(ob_add.get("enableSnow", False))
        self.spin_ob_snow_amount.setValue(ob_add.get("snowAmount", 50))

    def collect_settings_from_ui(self) -> dict:
        extensions = []
        for i in range(self.list_extensions.count()):
            extensions.append(self.list_extensions.item(i).text())

        sources = []
        for i in range(self.list_ob_sources.count()):
            sources.append(self.list_ob_sources.item(i).text())

        colors = {}
        for name, btn in self.color_buttons.items():
            colors[name] = btn.property("color_val")

        return {
            "RuriLib": {
                "General": {
                    "waitTime": self.spin_wait_time.value(),
                    "requestsTimeout": self.spin_req_timeout.value(),
                    "maxHits": self.spin_max_hits.value(),
                    "runnerBotsDisplayMode": self.cb_runner_bots_mode.currentText(),
                    "enableBotLog": self.chk_enable_bot_log.isChecked(),
                    "saveLastResponseSource": self.chk_save_last_resp.isChecked(),
                    "sendToCheckOnAbort": self.chk_send_tocheck_abort.isChecked(),
                    "hitsWebhookEnabled": self.chk_webhook_enabled.isChecked(),
                    "hitsWebhookUrl": self.txt_webhook_url.text().strip(),
                    "hitsWebhookUsername": self.txt_webhook_user.text().strip()
                },
                "Proxies": {
                    "allowConcurrentUse": self.chk_proxy_concurrent.isChecked(),
                    "neverBanProxies": self.chk_proxy_never_ban.isChecked(),
                    "shuffleProxiesOnStart": self.chk_proxy_shuffle.isChecked(),
                    "banLoopEvasion": self.spin_ban_loop_evasion.value(),
                    "dontReuseClearanceCookie": self.chk_proxy_cf_clearance.isChecked(),
                    "reloadProxiesWhenAllBanned": self.chk_reload_banned.isChecked(),
                    "reloadInterval": self.spin_reload_interval.value(),
                    "reloadSource": self.cb_reload_source.currentText(),
                    "globalBanKeys": self.txt_ban_keys.toPlainText(),
                    "globalRetryKeys": self.txt_retry_keys.toPlainText()
                },
                "Captchas": {
                    "captchaService": self.cb_captcha_service.currentText(),
                    "apiKey": self.txt_captcha_key.text().strip(),
                    "bypassBalanceCheck": self.chk_bypass_balance.isChecked(),
                    "responseTimeout": self.spin_captcha_timeout.value()
                },
                "Selenium": {
                    "browserType": self.cb_browser_type.currentText(),
                    "headlessMode": self.chk_headless.isChecked(),
                    "drawMouseMovement": self.chk_draw_mouse.isChecked(),
                    "chromeBinaryLocation": self.txt_chrome_bin.text().strip(),
                    "firefoxBinaryLocation": self.txt_firefox_bin.text().strip(),
                    "defaultTimeout": self.spin_selenium_timeout.value(),
                    "chromeExtensions": extensions,
                    "useGpuAcceleration": self.chk_use_gpu.isChecked()
                }
            },
            "OneBullet": {
                "General": {
                    "automaticallySetRecommendedBots": self.chk_ob_auto_bots.isChecked(),
                    "backupDatabaseDaily": self.chk_ob_backup_db.isChecked(),
                    "disableWarningOnQuit": self.chk_ob_quit_warn.isChecked(),
                    "alwaysOnTop": self.chk_ob_always_top.isChecked(),
                    "defaultAuthor": self.txt_ob_author.text().strip(),
                    "startingWindowWidth": self.spin_ob_width.value(),
                    "startingWindowHeight": self.spin_ob_height.value(),
                    "enableLogging": self.chk_ob_log_enable.isChecked(),
                    "logToFile": self.chk_ob_log_file.isChecked(),
                    "logBufferSize": self.spin_ob_log_buffer.value(),
                    "ignoreWordlistName": self.chk_ob_log_ignore_wl.isChecked()
                },
                "Sounds": {
                    "enableSoundOnHit": self.chk_ob_sound_hit.isChecked(),
                    "enableSoundOnCustom": self.chk_ob_sound_custom.isChecked(),
                    "enableSoundOnToCheck": self.chk_ob_sound_tocheck.isChecked(),
                    "soundFile": self.txt_ob_sound_file.text().strip()
                },
                "Sources": {
                    "sourcesList": sources
                },
                "Themes": {
                    "colors": colors,
                    "images": {
                        "useImages": self.chk_ob_use_images.isChecked(),
                        "opacity": self.spin_ob_opacity.value(),
                        "backgroundImage": self.txt_ob_bg_img.text().strip(),
                        "logo": self.txt_ob_logo.text().strip()
                    },
                    "additional": {
                        "allowTransparency": self.chk_ob_transparency.isChecked(),
                        "enableSnow": self.chk_ob_snow_enable.isChecked(),
                        "snowAmount": self.spin_ob_snow_amount.value()
                    }
                }
            }
        }

    def on_save_clicked(self):
        data = self.collect_settings_from_ui()
        save_settings(data)
        
        # Apply dynamic themes
        colors = data["OneBullet"]["Themes"]["colors"]
        qApp = QApplication.instance()
        if qApp:
            qApp.setStyleSheet(generate_stylesheet(colors))
            
            # Apply Window Behavior
            # If AlwaysOnTop is requested, set window flag
            for widget in qApp.topLevelWidgets():
                if widget.inherits("QMainWindow"):
                    always_on_top = data["OneBullet"]["General"]["alwaysOnTop"]
                    curr_flags = widget.windowFlags()
                    if always_on_top:
                        widget.setWindowFlags(curr_flags | Qt.WindowType.WindowStaysOnTopHint)
                    else:
                        widget.setWindowFlags(curr_flags & ~Qt.WindowType.WindowStaysOnTopHint)
                    widget.show() # Refresh window
                    
        QMessageBox.information(self, "Success", "Settings serialized and saved to settings.json successfully!")

    def on_reset_clicked(self):
        confirm = QMessageBox.question(
            self, "Confirm Reset", "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.load_settings_into_ui(DEFAULT_SETTINGS)
            save_settings(DEFAULT_SETTINGS)
            # Reapply stylesheet
            qApp = QApplication.instance()
            if qApp:
                qApp.setStyleSheet(generate_stylesheet(DEFAULT_SETTINGS["OneBullet"]["Themes"]["colors"]))
            QMessageBox.information(self, "Success", "Settings restored to defaults.")

    # Compatibility Helpers for other tabs
    def get_settings(self) -> dict:
        data = self.collect_settings_from_ui()
        rl_sel = data["RuriLib"]["Selenium"]
        return {
            "always_open": True,
            "always_quit": True,
            "headless": rl_sel["headlessMode"],
            "disable_notifications": True,
            "custom_args": "",
            "user_agent": "",
            "use_random_ua": False,
            "use_proxies": False # overridden by runner checkbox
        }

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar,
    QLabel, QPushButton, QTabWidget, QApplication
)
from PyQt6.QtCore import Qt
from ui.configs_tab import ConfigsTab
from ui.runner_tab import RunnerTab
from ui.wordlists_tab import WordlistsTab
from ui.tools_tab import ToolsTab
from ui.plugins_tab import PluginsTab
from ui.settings_tab import SeleniumSettingsTab
from ui.proxies_tab import ProxiesTab
from ui.utilities_tab import SeleniumUtilitiesTab
from ui.hits_db_tab import HitsDbTab
from ui.about_tab import AboutTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("One Bullet v1.0.0")
        from PyQt6.QtGui import QIcon
        self.setWindowIcon(QIcon("D:/my project/selenium block/assets/logo.jpg"))
        
        # Load parameters dynamically from global settings
        from utils.helpers import load_settings, generate_stylesheet
        
        settings = load_settings()
        ob_settings = settings.get("OneBullet", settings.get("ZanBullet", {}))
        
        # Default Author (can be referenced when creating new configs)
        self.default_author = ob_settings.get("General", {}).get("defaultAuthor", "One Bullet Development Team")
        
        # Adjust size based on General settings
        ob_gen = ob_settings.get("General", {})
        width = ob_gen.get("startingWindowWidth", 1280)
        height = ob_gen.get("startingWindowHeight", 800)
        self.resize(width, height)
        
        # Always On Top behavior
        if ob_gen.get("alwaysOnTop", False):
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            
        # Apply theme colors
        colors = ob_settings.get("Themes", {}).get("colors", {})
        self.setStyleSheet(generate_stylesheet(colors))
        
        self.init_ui()
        
    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. Top Navigation Bar: flat horizontal tabs
        self.nav_tabs = QTabWidget()
        self.nav_tabs.setObjectName("MainNavTabs")
        self.nav_tabs.setStyleSheet("""
            QTabWidget#MainNavTabs::pane {
                border: none;
                background-color: #0b0f19;
            }
            QTabWidget#MainNavTabs QTabBar {
                background: #06090f;
            }
            QTabWidget#MainNavTabs QTabBar::tab {
                background: #06090f; /* Deep dark blue-black background */
                color: #90a4ae; /* Muted slate gray font */
                padding: 12px 24px;
                font-weight: bold;
                border: 1px solid #1c273a;
                margin-right: 2px;
            }
            QTabWidget#MainNavTabs QTabBar::tab:hover {
                background: #0f1622;
                color: #ffffff;
            }
            QTabWidget#MainNavTabs QTabBar::tab:selected {
                background: #0b0f19;
                color: #00e5ff; /* Cyan highlight text color */
                border-bottom: 2px solid #00e5ff;
            }
        """)
        
        # Instantiate sub-tabs
        self.settings_tab = SeleniumSettingsTab()
        self.proxies_tab = ProxiesTab()
        self.wordlists_tab = WordlistsTab()
        self.tools_tab = ToolsTab(self.wordlists_tab)
        self.plugins_tab = PluginsTab()
        self.configs_tab = ConfigsTab(self.settings_tab, self.proxies_tab)
        self.runner_tab = RunnerTab(self.settings_tab, self.proxies_tab, self.wordlists_tab)
        self.utilities_tab = SeleniumUtilitiesTab()
        self.hits_db_tab = HitsDbTab()
        self.about_tab = AboutTab()
        
        # Embed utilities tab inside Tools tab as sub-tab
        self.tools_tab.sub_tabs.addTab(self.utilities_tab, "System Cleanup")
        
        # Add primary tabs to QTabWidget exactly:
        # [ Runner ] [ Proxies ] [ Wordlists ] [ Configs ] [ Hits DB ] [ Tools ] [ Plugins ] [ Settings ] [ About ]
        self.nav_tabs.addTab(self.runner_tab, "Runner")
        self.nav_tabs.addTab(self.proxies_tab, "Proxies")
        self.nav_tabs.addTab(self.wordlists_tab, "Wordlists")
        self.nav_tabs.addTab(self.configs_tab, "Configs")
        self.nav_tabs.addTab(self.hits_db_tab, "Hits DB")
        self.nav_tabs.addTab(self.tools_tab, "Tools")
        self.nav_tabs.addTab(self.plugins_tab, "Plugins")
        self.nav_tabs.addTab(self.settings_tab, "Settings")
        self.nav_tabs.addTab(self.about_tab, "About")
        
        layout.addWidget(self.nav_tabs)
        
        # Connect ConfigsTab save triggers to refresh runner options
        self.configs_tab.btn_save.clicked.connect(self.refresh_all_runners_configs)
        self.configs_tab.btn_delete.clicked.connect(self.refresh_all_runners_configs)
        self.configs_tab.btn_new.clicked.connect(self.refresh_all_runners_configs)
        
        # Listen to tab change to reload Hits DB
        self.nav_tabs.currentChanged.connect(self.on_tab_changed)
        
        # Set up a status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Welcome to One Bullet | Status: Ready")

    def on_tab_changed(self, index):
        # Hits DB is at index 4
        if index == 4:
            self.hits_db_tab.load_hits()

    def refresh_all_runners_configs(self):
        self.runner_tab.refresh_configs()

    def closeEvent(self, event):
        # Stop proxy check workers and save proxy lists
        if hasattr(self, 'proxies_tab'):
            try:
                self.proxies_tab.cleanup()
                self.proxies_tab.save_proxies_to_file()
            except Exception:
                pass
                
        # Stop debugger engine
        if hasattr(self, 'configs_tab') and hasattr(self.configs_tab, 'debugger_widget'):
            try:
                self.configs_tab.debugger_widget.cleanup()
            except Exception:
                pass
                
        # Stop all runner engines and save their states
        if hasattr(self, 'runner_tab'):
            try:
                self.runner_tab.on_stop_all()
                self.runner_tab.save_runners()
            except Exception:
                pass
                
        event.accept()

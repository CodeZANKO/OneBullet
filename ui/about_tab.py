from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)
        
        # Logo or Title Card
        title_card = QFrame()
        title_card.setObjectName("AboutCard")
        title_card.setStyleSheet("QFrame#AboutCard { background-color: #151b27; border: 2px solid #00e5ff; border-radius: 12px; padding: 20px; }")
        title_card.setFixedWidth(500)
        card_layout = QVBoxLayout(title_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PyQt6.QtGui import QPixmap
        lbl_logo_img = QLabel()
        logo_pixmap = QPixmap("D:/my project/selenium block/assets/logo.jpg")
        if not logo_pixmap.isNull():
            lbl_logo_img.setPixmap(logo_pixmap.scaledToWidth(120, Qt.TransformationMode.SmoothTransformation))
            card_layout.addWidget(lbl_logo_img)
        
        lbl_logo = QLabel("ONE BULLET")
        lbl_logo.setStyleSheet("font-size: 32px; font-weight: 800; color: #00e5ff; letter-spacing: 2px;")
        card_layout.addWidget(lbl_logo)
        
        lbl_version = QLabel("Version 1.0.0 (Release Build)")
        lbl_version.setStyleSheet("font-size: 14px; color: #9e9e9e; font-weight: 500;")
        card_layout.addWidget(lbl_version)
        
        layout.addWidget(title_card)
        
        # Details Card
        details_card = QFrame()
        details_card.setObjectName("DetailsCard")
        details_card.setStyleSheet("QFrame#DetailsCard { background-color: #151b27; border: 1px solid #1c273a; border-radius: 12px; padding: 25px; }")
        details_card.setFixedWidth(500)
        details_layout = QVBoxLayout(details_card)
        details_layout.setSpacing(12)
        
        def add_detail_row(label, val):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #b0bec5; font-size: 13px;")
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet("color: white; font-size: 13px;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(v_lbl)
            details_layout.addLayout(row)
            
        add_detail_row("Developer Team:", "One Bullet Development Team")
        add_detail_row("Developer:", "Zanko Legend | zankodev.xyz")
        add_detail_row("Framework Platform:", "PyQt6 / Python 3.x")
        add_detail_row("Theme Aesthetics:", "Midnight Dark Palette with Neon Accents")
        add_detail_row("Automation Core:", "Selenium WebDriver API")
        add_detail_row("Database Backend:", "Local JSON Datastore")
        add_detail_row("System Status:", "Online & Secure")
        
        layout.addWidget(details_card)
        
        # Copyright Text
        lbl_copyright = QLabel("© 2026 One Bullet Development Team. All Rights Reserved.")
        lbl_copyright.setStyleSheet("font-size: 11px; color: #757575;")
        layout.addWidget(lbl_copyright)

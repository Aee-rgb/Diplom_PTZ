# styles/theme.py

LIGHT_BLUE_THEME = """
QMainWindow {
    background-color: #ffffff;
    color: #0f172a;
}

QWidget {
    background-color: #ffffff;
    color: #0f172a;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 500;
    font-size: 11px;
    min-height: 24px;
    text-align: center;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #e2e8f0;
    color: #94a3b8;
}

QPushButton[type="success"] {
    background-color: #16a34a;
}

QPushButton[type="success"]:hover {
    background-color: #15803d;
}

QPushButton[type="success"]:pressed {
    background-color: #14532d;
}

QPushButton[type="danger"] {
    background-color: #dc2626;
}

QPushButton[type="danger"]:hover {
    background-color: #ef4444;
}

QPushButton[type="danger"]:pressed {
    background-color: #b91c1c;
}

QPushButton[type="warning"] {
    background-color: #d97706;
}

QPushButton[type="warning"]:hover {
    background-color: #f59e0b;
}

QPushButton[type="warning"]:pressed {
    background-color: #b45309;
}

QComboBox {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 32px;
    font-size: 12px;
}

QComboBox:hover {
    background-color: #f1f5f9;
    border: 1px solid #94a3b8;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    width: 0px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    selection-background-color: #2563eb;
    border: 1px solid #cbd5e1;
}

QLabel {
    color: #0f172a;
    font-size: 12px;
}

QLabel[type="title"] {
    font-size: 16px;
    font-weight: bold;
    color: #1e40af;
}

QLabel[type="subtitle"] {
    font-size: 13px;
    font-weight: 600;
    color: #475569;
}

QLabel[type="status"] {
    font-size: 11px;
    color: #64748b;
    padding: 2px 0px;
}

QTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 11px;
}

QTextEdit:focus {
    border: 1px solid #2563eb;
}

QTextEdit:hover {
    border: 1px solid #94a3b8;
}

QScrollBar:vertical {
    background-color: #f8fafc;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #f8fafc;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94a3b8;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

QSpinBox {
    background-color: #f8fafc;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 32px;
    font-size: 12px;
}

QSpinBox:focus {
    border: 1px solid #2563eb;
}

QSpinBox::up-button,
QSpinBox::down-button {
    background-color: #2563eb;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover {
    background-color: #3b82f6;
}

QGroupBox {
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    padding-left: 12px;
    padding-right: 12px;
    padding-bottom: 12px;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 4px;
}

QProgressBar {
    background-color: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    height: 20px;
    text-align: center;
    color: #0f172a;
    font-size: 11px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #2563eb, stop:1 #3b82f6);
    border-radius: 3px;
}

QCheckBox {
    color: #0f172a;
    spacing: 6px;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QCheckBox::indicator:unchecked {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
}

QCheckBox::indicator:unchecked:hover {
    background-color: #f1f5f9;
    border: 1px solid #94a3b8;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border: 1px solid #2563eb;
    border-radius: 4px;
    image: url(:/check.png);
}

QDialog {
    background-color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #cbd5e1;
}

QTabBar::tab {
    background-color: #f8fafc;
    color: #64748b;
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    background-color: #f1f5f9;
    color: #0f172a;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563eb;
    border-bottom: 2px solid #2563eb;
}

QFrame[frameShape="4"] {
    color: #cbd5e1;
}

QWidget[class="dark-panel"] {
    background-color: #f8fafc;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    padding: 12px;
}

QWidget[class="highlight-panel"] {
    background-color: #eff6ff;
    border-radius: 8px;
    border: 1px solid #3b82f6;
    padding: 12px;
}
"""


def apply_dark_theme(app):
    """Применяет бело-синюю светлую тему.
    Имя функции сохранено для совместимости с существующим импортом в app.py"""
    app.setStyle('Fusion')
    app.setStyleSheet(LIGHT_BLUE_THEME)


# Алиас для логичного вызова (опционально)
apply_light_blue_theme = apply_dark_theme


def get_colors():
    return {
        'bg_primary': '#ffffff',
        'bg_secondary': '#f8fafc',
        'bg_tertiary': '#f1f5f9',
        'border': '#cbd5e1',
        'border_hover': '#94a3b8',
        'text': '#0f172a',
        'text_secondary': '#475569',
        'text_muted': '#64748b',
        'accent': '#2563eb',
        'accent_hover': '#3b82f6',
        'accent_active': '#1d4ed8',
        'success': '#16a34a',
        'success_hover': '#15803d',
        'danger': '#dc2626',
        'danger_hover': '#ef4444',
        'warning': '#d97706',
        'warning_hover': '#f59e0b',
    }
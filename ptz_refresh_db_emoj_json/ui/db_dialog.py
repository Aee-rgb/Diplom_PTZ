# ui/db_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QMessageBox, QLabel, QComboBox
)
from PyQt5.QtCore import Qt


class DBDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("База данных: Мониторинг")
        self.setGeometry(150, 150, 900, 600)
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Статус подключения
        status_layout = QHBoxLayout()
        status_lbl = QLabel("MySQL подключен")
        status_lbl.setProperty("type", "status")
        status_layout.addWidget(status_lbl)

        self.table_combo = QComboBox()
        self.table_combo.addItems(["tracking_events", "script_logs", "cameras", "scripts"])
        self.table_combo.currentTextChanged.connect(self.refresh_data)
        status_layout.addStretch()
        status_layout.addWidget(QLabel("Таблица:"))
        status_layout.addWidget(self.table_combo)

        layout.addLayout(status_layout)

        # Таблица данных
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh_data)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_data(self):
        table_name = self.table_combo.currentText()
        try:
            if table_name == "tracking_events":
                data = self.db._execute(
                    "SELECT event_time, camera_id, action_taken, confidence, ptz_position FROM tracking_events ORDER BY event_time DESC LIMIT 100",
                    fetch_all=True
                ) or []
                headers = ["Время", "Камера", "Действие", "Уверенность", "PTZ"]
            elif table_name == "script_logs":
                data = self.db._execute(
                    "SELECT start_time, script_id, camera_id, status, error_message FROM script_logs ORDER BY start_time DESC LIMIT 100",
                    fetch_all=True
                ) or []
                headers = ["Старт", "Скрипт", "Камера", "Статус", "Ошибка"]
            elif table_name == "cameras":
                data = self.db._execute("SELECT id, name, connection_type, is_active, created_at FROM cameras",
                                        fetch_all=True) or []
                headers = ["ID", "Имя", "Тип", "Активна", "Создана"]
            else:  # scripts
                data = self.db._execute("SELECT id, name, description, is_system, created_at FROM scripts",
                                        fetch_all=True) or []
                headers = ["ID", "Имя", "Описание", "Системный", "Создан"]

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(data))

            for i, row in enumerate(data):
                for j, (key, val) in enumerate(row.items()):
                    text = str(val).split('.')[0] if isinstance(val, str) and '.' in val else str(val)
                    self.table.setItem(i, j, QTableWidgetItem(text[:50] + "..." if len(str(val)) > 50 else text))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")
# ui/script_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
    QLabel, QFormLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QTextEdit, QGroupBox, QScrollArea, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import datetime


class ScriptDialog(QDialog):
    # Сигнал для потокобезопасного обновления логов из фонового потока
    log_signal = pyqtSignal(str)

    script_started = pyqtSignal(str)
    script_stopped = pyqtSignal()

    def __init__(self, script_engine, camera_manager, parent=None):
        super().__init__(parent)
        self.script_engine = script_engine
        self.camera_manager = camera_manager
        self.setWindowTitle("Управление скриптами")
        self.setGeometry(100, 100, 540, 700)
        self.setModal(True)

        self.param_widgets = {}
        self.current_script_key = None

        self.setup_ui()
        self.setup_connections()

        # Подключаем сигнал к методу обновления логов
        self.log_signal.connect(self._append_log)

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # === Заголовок ===
        title = QLabel("Автоматизация камеры")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 4px;")
        main_layout.addWidget(title)

        # === Выбор скрипта ===
        script_group = QGroupBox("Выберите скрипт")
        script_layout = QVBoxLayout()

        self.script_combo = QComboBox()
        self.script_combo.setMinimumHeight(32)
        self.script_combo.currentIndexChanged.connect(self.on_script_selected)
        script_layout.addWidget(self.script_combo)

        self.script_desc = QLabel()
        self.script_desc.setWordWrap(True)
        self.script_desc.setStyleSheet("""
            QLabel { color: #8b949e; padding: 8px; background: #161b22; border-radius: 4px; border: 1px solid #30363d; }
        """)
        script_layout.addWidget(self.script_desc)
        script_group.setLayout(script_layout)
        main_layout.addWidget(script_group)

        # === Параметры скрипта ===
        self.params_group = QGroupBox("Параметры")
        params_main_layout = QVBoxLayout()

        self.params_scroll = QScrollArea()
        self.params_scroll.setWidgetResizable(True)
        self.params_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.params_scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #30363d; border-radius: 4px; background: #0d1117; }")

        params_widget = QWidget()
        self.params_layout = QFormLayout()
        self.params_layout.setSpacing(8)
        self.params_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        params_widget.setLayout(self.params_layout)

        self.params_scroll.setWidget(params_widget)
        params_main_layout.addWidget(self.params_scroll)
        self.params_group.setLayout(params_main_layout)
        main_layout.addWidget(self.params_group)

        # === ЖУРНАЛ КОМАНД И ОТВЕТОВ КАМЕРЫ ===
        log_group = QGroupBox("Журнал команд и ответов камеры")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 4px;
            }
        """)
        log_layout.addWidget(self.log_text)

        # Кнопки управления журналом
        log_btn_layout = QHBoxLayout()

        self.clear_log_btn = QPushButton("Очистить журнал")
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.clear_log_btn.setMaximumWidth(140)
        log_btn_layout.addWidget(self.clear_log_btn)

        self.auto_scroll_check = QLabel("Автоскролл: Вкл")
        self.auto_scroll_check.setStyleSheet("color: #3fb950; font-size: 10px;")
        log_btn_layout.addWidget(self.auto_scroll_check)

        log_btn_layout.addStretch()
        log_layout.addLayout(log_btn_layout)

        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # === Статус выполнения ===
        self.status_label = QLabel("Готов к запуску")
        self.status_label.setStyleSheet("QLabel { color: #3fb950; font-weight: bold; padding: 4px 0; }")
        main_layout.addWidget(self.status_label)

        # === Кнопки управления ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.run_btn = QPushButton("Запустить")
        self.run_btn.setProperty("type", "success")
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_script)
        btn_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setProperty("type", "danger")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_script)
        btn_layout.addWidget(self.stop_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.populate_scripts()

    def setup_connections(self):
        """Подключение колбэков от ScriptEngine"""
        self.script_engine.set_callbacks(
            on_status_change=self.on_script_status,
            on_progress=self.on_script_progress,
            on_log=self.log_signal.emit  # Прямая отправка логов в сигнал (потокобезопасно)
        )

    def populate_scripts(self):
        scripts = self.script_engine.get_scripts()
        self.script_combo.clear()
        for key, info in scripts.items():
            self.script_combo.addItem(info["name"], key)
        if scripts:
            self.script_combo.setCurrentIndex(0)
            self.on_script_selected()

    def on_script_selected(self, index=None):
        key = self.script_combo.currentData()
        if not key: return

        self.current_script_key = key
        info = self.script_engine.get_scripts()[key]
        self.script_desc.setText(f"{info['description']}")

        self._clear_params()
        for param in info["params"]:
            self._create_param_widget(param)

        self.params_group.setVisible(bool(info["params"]))
        self.status_label.setText("Готов к запуску")
        self.status_label.setStyleSheet("QLabel { color: #3fb950; font-weight: bold; padding: 4px 0; }")

    def _clear_params(self):
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.param_widgets.clear()

    def _create_param_widget(self, param: dict):
        ptype = param.get("type", "text")
        name, label = param["name"], param["label"]

        if ptype == "int":
            widget = QSpinBox()
            widget.setRange(param.get("min", 0), param.get("max", 100))
            widget.setValue(param.get("default", 0))
        elif ptype == "float":
            widget = QDoubleSpinBox()
            widget.setRange(param.get("min", 0.0), param.get("max", 100.0))
            widget.setValue(param.get("default", 0.0))
            widget.setDecimals(2)
        else:
            if param.get("multiline"):
                widget = QTextEdit()
                widget.setPlainText(param.get("default", ""))
                widget.setMaximumHeight(80)
            else:
                widget = QLineEdit()
                widget.setText(param.get("default", ""))

        self.params_layout.addRow(label, widget)
        self.param_widgets[name] = widget

    def _get_params(self) -> dict:
        params = {}
        for name, widget in self.param_widgets.items():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                params[name] = widget.value()
            elif isinstance(widget, QTextEdit):
                params[name] = widget.toPlainText().strip()
            else:
                params[name] = widget.text().strip()
        return params

    def run_script(self):
        key = self.script_combo.currentData()
        if not key:
            QMessageBox.warning(self, "Ошибка", "Не выбран скрипт")
            return

        params = self._get_params()
        self.log_text.clear()
        self._append_log("Инициализация скрипта...")

        if self.script_engine.run_script(key, params):
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.script_combo.setEnabled(False)
            self.status_label.setText("Выполняется...")
            self.status_label.setStyleSheet("QLabel { color: #f0b429; font-weight: bold; padding: 4px 0; }")
            self.script_started.emit(key)

    def stop_script(self):
        self.script_engine.stop_script()
        self._on_script_finished()

    def _on_script_finished(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.script_combo.setEnabled(True)
        self.status_label.setText("Готово")
        self.status_label.setStyleSheet("QLabel { color: #3fb950; font-weight: bold; padding: 4px 0; }")
        self.script_stopped.emit()

    # ==================== КОЛБЭКИ ====================

    def on_script_status(self, message: str):
        self.status_label.setText(message)
        if "[OK]" in message or "завершено" in message.lower() or "готов" in message.lower():
            color = "#3fb950"
        elif "[ERR]" in message or "ошибка" in message.lower():
            color = "#f85149"
        elif "[WARN]" in message or "предупреждение" in message.lower():
            color = "#d29922"
        elif "выполняется" in message.lower() or "запуск" in message.lower():
            color = "#f0b429"
        else:
            color = "#8b949e"
        self.status_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; padding: 4px 0; }}")

    def on_script_progress(self, value: float):
        pass

    # Метод безопасного обновления логов из фонового потока
    def _append_log(self, message: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Цветовая схема по типу сообщения
        if "В очередь" in message:
            color = "#58a6ff"  # Отправка в очередь — синий
        elif "Выполнено" in message:
            color = "#3fb950"  # Успех — зелёный
        elif "Ошибка" in message:
            color = "#f85149"  # Ошибка — красный
        elif "Патруль" in message or "Запуск" in message or "Инициализация" in message:
            color = "#d29922"  # Процесс — оранжевый
        elif "Позиция" in message or "Переход" in message:
            color = "#a371f7"  # Позиции — фиолетовый
        else:
            color = "#8b949e"  # По умолчанию — серый

        html = f'<span style="color:#6e7681">[{ts}]</span> <span style="color:{color}">{message}</span>'
        self.log_text.append(html)

        # Автоскролл вниз
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    # ==================== СОБЫТИЯ ====================

    def closeEvent(self, event):
        if self.script_engine.is_running:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Скрипт выполняется. Остановить и закрыть?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.script_engine.stop_script()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and not self.script_engine.is_running:
            self.accept()
        else:
            super().keyPressEvent(event)

    # ==================== ПУБЛИЧНЫЕ МЕТОДЫ ====================

    def refresh_scripts(self):
        self.populate_scripts()

    def set_script_enabled(self, enabled: bool):
        self.run_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)
        self.script_combo.setEnabled(enabled)
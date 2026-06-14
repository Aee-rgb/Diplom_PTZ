from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
                             QLabel, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont
from datetime import datetime


class CalibrationWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, camera_manager):
        super().__init__()
        self.camera_manager = camera_manager

    def run(self):
        results = {}

        for direction in ['tilt', 'pan', 'zoom']:
            self.progress.emit(f'Калибровка {direction}...')
            min_val, max_val = self.camera_manager.calibrate_range(direction)
            results[direction] = {'min': min_val, 'max': max_val}
            self.progress.emit(f'{direction}: [{min_val}, {max_val}]')

        self.finished.emit(results)


class CalibrationWidget(QWidget):
    calibration_started = pyqtSignal()
    calibration_finished = pyqtSignal(dict)

    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.calibration_results = None
        self.calibration_thread = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Автоматическая калибровка камеры")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setProperty("type", "title")
        layout.addWidget(title)

        description = QLabel(
            "Система автоматически найдёт диапазон движения камеры.\n"
            "Не трогайте камеру во время процесса."
        )
        description.setProperty("type", "status")
        description.setStyleSheet("color: #8b949e; font-style: italic; margin: 8px 0px;")
        layout.addWidget(description)

        controls_group = QGroupBox("Управление")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        controls_layout.setContentsMargins(12, 12, 12, 12)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.start_button = QPushButton("Начать калибровку")
        self.start_button.setProperty("type", "success")
        self.start_button.clicked.connect(self.start_calibration)
        self.start_button.setMinimumHeight(40)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Остановить")
        self.stop_button.setProperty("type", "danger")
        self.stop_button.clicked.connect(self.stop_calibration)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        controls_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(3)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(24)
        controls_layout.addWidget(self.progress_bar)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        log_group = QGroupBox("Процесс калибровки")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(12, 12, 12, 12)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #00ff00;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        results_group = QGroupBox("Результаты калибровки")
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(12, 12, 12, 12)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(120)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        results_layout.addWidget(self.results_text)

        apply_layout = QHBoxLayout()
        apply_layout.setSpacing(8)

        self.apply_button = QPushButton("Применить результаты")
        self.apply_button.setProperty("type", "success")
        self.apply_button.clicked.connect(self.apply_calibration)
        self.apply_button.setMinimumHeight(36)
        self.apply_button.setEnabled(False)
        apply_layout.addWidget(self.apply_button)

        self.save_button = QPushButton("Сохранить в конфиг")
        self.save_button.clicked.connect(self.save_calibration)
        self.save_button.setMinimumHeight(36)
        self.save_button.setEnabled(False)
        apply_layout.addWidget(self.save_button)

        results_layout.addLayout(apply_layout)

        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        self.status_label = QLabel("Готов к калибровке")
        self.status_label.setProperty("type", "status")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

    def add_log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if level == "INFO":
            prefix = "[INFO]"
            color = "#00ff00"
        elif level == "WARNING":
            prefix = "[WARN]"
            color = "#ffff00"
        elif level == "ERROR":
            prefix = "[ERR]"
            color = "#ff0000"
        else:
            prefix = "[MSG]"
            color = "#00ffff"

        log_message = f'<span style="color: #888">{timestamp}</span> <span style="color: {color}">{prefix}</span> {message}'
        self.log_text.append(log_message)

        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def start_calibration(self):
        if not self.camera_manager.is_opened():
            self.add_log("Ошибка: Камера не подключена!", "ERROR")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.apply_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.results_text.clear()

        self.status_label.setText("Статус: Калибровка в процессе...")
        self.status_label.setStyleSheet("font-weight: bold; color: red;")

        self.add_log('<span style="color: #4CAF50">Начало калибровки...</span>')
        self.add_log('Калибровка TILT (наклон)...')

        self.calibration_thread = CalibrationWorker(self.camera_manager)
        self.calibration_thread.progress.connect(self.on_progress)
        self.calibration_thread.finished.connect(self.on_calibration_finished)
        self.calibration_thread.start()

        self.calibration_started.emit()

    def stop_calibration(self):
        if self.calibration_thread and self.calibration_thread.isRunning():
            self.calibration_thread.terminate()
            self.calibration_thread.wait()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Статус: Калибровка прервана")
        self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        self.add_log('<span style="color: #f44336">Калибровка остановлена пользователем</span>')

    @pyqtSlot(str)
    def on_progress(self, message):
        self.add_log(message)

        if 'tilt' in message.lower() and 'tilt' in message:
            self.progress_bar.setValue(1)
        elif 'pan' in message.lower() and 'pan' in message:
            self.progress_bar.setValue(2)
        elif 'zoom' in message.lower() and 'zoom' in message:
            self.progress_bar.setValue(3)

    @pyqtSlot(dict)
    def on_calibration_finished(self, results):
        self.calibration_results = results

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.apply_button.setEnabled(True)
        self.save_button.setEnabled(True)

        self.status_label.setText("Статус: Калибровка завершена")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        self.add_log('<span style="color: #4CAF50">Калибровка успешно завершена!</span>')

        results_text = "=== РЕЗУЛЬТАТЫ КАЛИБРОВКИ ===\n\n"
        results_text += f"TILT (Наклон):\n  Минимум: {results['tilt']['min']}\n  Максимум: {results['tilt']['max']}\n\n"
        results_text += f"PAN (Поворот):\n  Минимум: {results['pan']['min']}\n  Максимум: {results['pan']['max']}\n\n"
        results_text += f"ZOOM (Зум):\n  Минимум: {results['zoom']['min']}\n  Максимум: {results['zoom']['max']}\n"

        self.results_text.setText(results_text)

        self.calibration_finished.emit(results)

    def apply_calibration(self):
        if not self.calibration_results:
            return

        tilt_range = self.calibration_results['tilt']['max'] - self.calibration_results['tilt']['min']
        pan_range = self.calibration_results['pan']['max'] - self.calibration_results['pan']['min']
        zoom_range = self.calibration_results['zoom']['max'] - self.calibration_results['zoom']['min']

        new_tilt_step = max(1, tilt_range // 10)
        new_pan_step = max(1, pan_range // 10)
        new_zoom_step = max(1, zoom_range // 10)

        self.camera_manager.set_tilt_step(new_tilt_step)
        self.camera_manager.set_pan_step(new_pan_step)
        self.camera_manager.set_zoom_step(new_zoom_step)

        self.add_log(f'<span style="color: #2196F3">Новые шаги:</span>')
        self.add_log(f'  TILT: {new_tilt_step}')
        self.add_log(f'  PAN: {new_pan_step}')
        self.add_log(f'  ZOOM: {new_zoom_step}')

    def save_calibration(self):
        if not self.calibration_results:
            return

        if 'calibration' not in self.camera_manager.config:
            self.camera_manager.config['calibration'] = {}

        self.camera_manager.config['calibration'] = {
            'tilt': self.calibration_results['tilt'],
            'pan': self.calibration_results['pan'],
            'zoom': self.calibration_results['zoom']
        }

        self.camera_manager.save_config()
        self.add_log('<span style="color: #4CAF50">Результаты сохранены в конфиг</span>')
# ui/main.py
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGridLayout, QDialog, QGroupBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeyEvent
from queue import Queue
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.camera import CameraManager
from ui.video import VideoWidget
from ui.settings import SettingsDialog
from ui.calibration import CalibrationWidget
from ui.watch import HumanTracker
from ui.skript import ScriptEngine


class MainWindow(QMainWindow):
    def __init__(self, db_manager=None, config=None):
        super().__init__()
        self.setWindowTitle("Трекер Камеры")
        self.setGeometry(100, 100, 1400, 900)

        self.db = db_manager
        self.app_config = config or {}

        self.camera_manager = CameraManager()
        self.command_queue = Queue()
        self.running = True

        self.command_thread = threading.Thread(target=self.process_commands, daemon=True)
        self.command_thread.start()

        # Инициализация модулей с передачей БД
        self.tracker = HumanTracker(self.camera_manager, self.db)
        self.script_engine = ScriptEngine(self.camera_manager, self.db)

        self.setup_ui()

        # Колбэки ставим ПОСЛЕ создания self.video_widget
        self.script_engine.set_callbacks(
            on_status_change=lambda msg: self.video_widget.show_message(msg),
            on_progress=lambda val: None
        )
        if self.db:
            self.script_engine.load_custom_scripts()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        central_widget.setLayout(main_layout)

        # === ГРУППА УПРАВЛЕНИЯ КАМЕРОЙ ===
        control_group = QGroupBox("Выбор камеры")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        control_layout.setContentsMargins(12, 12, 12, 12)

        camera_label = QLabel("Камера:")
        camera_label.setProperty("type", "subtitle")
        control_layout.addWidget(camera_label)

        self.camera_combo = QComboBox()
        self.camera_combo.currentIndexChanged.connect(self.on_camera_selected)
        self.camera_combo.setMinimumWidth(150)
        control_layout.addWidget(self.camera_combo)

        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh_cameras)
        refresh_button.setMaximumWidth(120)
        control_layout.addWidget(refresh_button)

        self.start_button = QPushButton("Включить")
        self.start_button.clicked.connect(self.start_camera)
        self.start_button.setProperty("type", "success")
        self.start_button.setMaximumWidth(120)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Выключить")
        self.stop_button.clicked.connect(self.stop_camera)
        self.stop_button.setProperty("type", "danger")
        self.stop_button.setMaximumWidth(120)
        control_layout.addWidget(self.stop_button)

        # Кнопка слежения
        #self.track_button = QPushButton("Слежение")
        #self.track_button.clicked.connect(self.toggle_tracking)
        #self.track_button.setProperty("type", "warning")
        #self.track_button.setMaximumWidth(130)
        #control_layout.addWidget(self.track_button)

        # Кнопка скриптов
        self.script_button = QPushButton("Скрипты")
        self.script_button.clicked.connect(self.open_script_panel)
        self.script_button.setMaximumWidth(120)
        control_layout.addWidget(self.script_button)

        # КНОПКА БАЗЫ ДАННЫХ
        self.db_button = QPushButton("База данных")
        self.db_button.clicked.connect(self.open_db_panel)
        self.db_button.setMaximumWidth(130)
        control_layout.addWidget(self.db_button)

        settings_button = QPushButton("Настройки")
        settings_button.clicked.connect(self.open_settings)
        settings_button.setMaximumWidth(120)
        control_layout.addWidget(settings_button)

        calibration_button = QPushButton("Калибр.")
        calibration_button.clicked.connect(self.open_calibration)
        calibration_button.setMaximumWidth(120)
        control_layout.addWidget(calibration_button)

        control_layout.addStretch()
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # === ВИДЕО ===
        self.video_widget = VideoWidget()
        main_layout.addWidget(self.video_widget, 1)

        # === PTZ УПРАВЛЕНИЕ ===
        ptz_group = QGroupBox("Управление камерой (Стрелки / WASD / Q-E)")
        ptz_layout = QVBoxLayout()
        ptz_layout.setSpacing(12)
        ptz_layout.setContentsMargins(12, 12, 12, 12)

        ptz_controls = QGridLayout()
        ptz_controls.setSpacing(8)

        self.tilt_up_btn = QPushButton("Вверх")
        self.tilt_up_btn.clicked.connect(lambda: (self.camera_manager.tilt_up(), self.centralWidget().setFocus()))
        self.tilt_up_btn.setMinimumHeight(32)
        ptz_controls.addWidget(self.tilt_up_btn, 0, 1)

        self.pan_left_btn = QPushButton("Влево")
        self.pan_left_btn.clicked.connect(lambda: (self.camera_manager.pan_left(), self.centralWidget().setFocus()))
        self.pan_left_btn.setMinimumHeight(32)
        ptz_controls.addWidget(self.pan_left_btn, 1, 0)

        reset_btn = QPushButton("Центр")
        reset_btn.clicked.connect(lambda: (self.reset_ptz(), self.centralWidget().setFocus()))
        reset_btn.setMinimumHeight(32)
        reset_btn.setProperty("type", "warning")
        ptz_controls.addWidget(reset_btn, 1, 1)

        self.pan_right_btn = QPushButton("Вправо")
        self.pan_right_btn.clicked.connect(lambda: (self.camera_manager.pan_right(), self.centralWidget().setFocus()))
        self.pan_right_btn.setMinimumHeight(32)
        ptz_controls.addWidget(self.pan_right_btn, 1, 2)

        self.tilt_down_btn = QPushButton("Вниз")
        self.tilt_down_btn.clicked.connect(lambda: (self.camera_manager.tilt_down(), self.centralWidget().setFocus()))
        self.tilt_down_btn.setMinimumHeight(32)
        ptz_controls.addWidget(self.tilt_down_btn, 2, 1)

        ptz_layout.addLayout(ptz_controls)

        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(8)
        zoom_layout.setContentsMargins(0, 12, 0, 0)

        zoom_label = QLabel("Зум:")
        zoom_label.setProperty("type", "subtitle")
        zoom_layout.addWidget(zoom_label)

        self.zoom_out_btn = QPushButton("Уменьшить")
        self.zoom_out_btn.clicked.connect(lambda: (self.camera_manager.zoom_out(), self.centralWidget().setFocus()))
        self.zoom_out_btn.setMinimumHeight(28)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_in_btn = QPushButton("Увеличить")
        self.zoom_in_btn.clicked.connect(lambda: (self.camera_manager.zoom_in(), self.centralWidget().setFocus()))
        self.zoom_in_btn.setMinimumHeight(28)
        zoom_layout.addWidget(self.zoom_in_btn)

        zoom_layout.addStretch()
        ptz_layout.addLayout(zoom_layout)

        ptz_group.setLayout(ptz_layout)
        main_layout.addWidget(ptz_group)

    def toggle_tracking(self):
        if self.tracker.is_tracking:
            self.tracker.stop()
            self.track_button.setText("Включить слежение")
            self.track_button.setProperty("type", "warning")
            self.video_widget.show_message("Слежение остановлено")
        else:
            if not self.camera_manager.is_opened():
                self.video_widget.show_message("Сначала включите камеру")
                return
            self.tracker.start()
            self.track_button.setText("Остановить слежение")
            self.track_button.setProperty("type", "danger")
            self.video_widget.show_message("Слежение запущено")
        self.track_button.style().polish(self.track_button)

    def open_script_panel(self):
        from ui.script_dialog import ScriptDialog
        dialog = ScriptDialog(self.script_engine, self.camera_manager, self)
        dialog.exec_()

    def open_db_panel(self):
        if not self.db:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "База данных", "Подключение к MySQL не установлено.\nПроверьте config.json.")
            return
        from ui.db_dialog import DBDialog
        dialog = DBDialog(self.db, self)
        dialog.exec_()

    def refresh_cameras(self):
        self.camera_combo.clear()
        available_cameras = self.camera_manager.find_available_cameras()
        if not available_cameras:
            self.video_widget.show_message("Камеры не найдены")
            self.camera_combo.addItem("Нет доступных камер")
            return
        for idx in available_cameras:
            self.camera_combo.addItem(f"Камера {idx}", idx)
        if available_cameras:
            self.camera_combo.setCurrentIndex(0)

    def on_camera_selected(self, index):
        pass

    def start_camera(self):
        index = self.camera_combo.currentIndex()
        if index < 0: return
        camera_id = self.camera_combo.itemData(index)
        if camera_id is None: return
        if self.camera_manager.open_camera(camera_id):
            self.video_widget.show_message("Подключение...")
            if not self.timer.isActive(): self.timer.start(30)
            # Логируем камеру в БД при старте
            if self.db:
                self.db.upsert_camera(f"Camera_{camera_id}", 'usb', '')
        else:
            self.video_widget.show_message(f"Ошибка: не удалось открыть камеру {camera_id}")
            self.timer.stop()

    def update_frame(self):
        if not self.camera_manager.is_opened(): return
        frame = self.camera_manager.read_frame()
        if frame is not None:
            self.video_widget.display_frame(frame)
        else:
            self.video_widget.show_message("Ошибка чтения кадра")

    def stop_camera(self):
        self.timer.stop()
        self.camera_manager.release()
        self.video_widget.show_message("Камера не подключена")
        if self.tracker.is_tracking: self.toggle_tracking()
        if self.script_engine.is_running: self.script_engine.stop_script()

    def reset_ptz(self):
        self.camera_manager.reset_ptz()

    def open_settings(self):
        dialog = SettingsDialog(self.camera_manager, self)
        dialog.exec_()

    def open_calibration(self):
        if not self.camera_manager.is_opened():
            self.video_widget.show_message("Сначала подключите камеру")
            return
        self.timer.stop()
        calibration_dialog = QDialog(self)
        calibration_dialog.setWindowTitle("Автокалибровка камеры")
        calibration_dialog.setGeometry(100, 100, 600, 700)
        dialog_layout = QVBoxLayout()
        calibration_widget = CalibrationWidget(self.camera_manager)
        dialog_layout.addWidget(calibration_widget)
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(calibration_dialog.accept)
        dialog_layout.addWidget(close_button)
        calibration_dialog.setLayout(dialog_layout)
        calibration_dialog.exec_()
        if self.camera_manager.is_opened(): self.timer.start(30)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = event.text().upper()
        cmd_map = {
            Qt.Key_Left: 'pan_left', Qt.Key_Right: 'pan_right',
            Qt.Key_Up: 'tilt_up', Qt.Key_Down: 'tilt_down',
            Qt.Key_Plus: 'zoom_in', Qt.Key_Equal: 'zoom_in', Qt.Key_Minus: 'zoom_out'
        }
        if key in cmd_map:
            self.add_command(cmd_map[key])
            event.accept()
            return
        ru_map = {'W': 'Ц', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'Q': 'Й', 'E': 'У'}
        if text in ru_map:
            text = ru_map[text]
        action_map = {'W': 'tilt_up', 'A': 'pan_left', 'S': 'tilt_down', 'D': 'pan_right', 'Q': 'zoom_in',
                      'E': 'zoom_out'}
        if text in action_map:
            self.add_command(action_map[text])
            event.accept()
            return
        super().keyPressEvent(event)

    def add_command(self, command):
        self.command_queue.put(command)

    def process_commands(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.01)
                if command == 'pan_left':
                    self.camera_manager.pan_left()
                elif command == 'pan_right':
                    self.camera_manager.pan_right()
                elif command == 'tilt_up':
                    self.camera_manager.tilt_up()
                elif command == 'tilt_down':
                    self.camera_manager.tilt_down()
                elif command == 'zoom_in':
                    self.camera_manager.zoom_in()
                elif command == 'zoom_out':
                    self.camera_manager.zoom_out()
            except:
                pass

    def closeEvent(self, event):
        self.running = False
        self.tracker.stop()
        self.script_engine.stop_script()
        self.timer.stop()
        self.camera_manager.release()
        self.command_thread.join(timeout=1)
        event.accept()
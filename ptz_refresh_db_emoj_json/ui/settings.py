from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
                             QPushButton, QGroupBox)
from PyQt5.QtGui import QFont


class SettingsDialog(QDialog):
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки управления")
        self.setGeometry(200, 200, 450, 350)
        self.camera_manager = camera_manager

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Параметры управления камерой")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setProperty("type", "title")
        layout.addWidget(title)

        controls_group = QGroupBox("Шаги управления")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(12)
        controls_layout.setContentsMargins(12, 12, 12, 12)

        pan_layout = QHBoxLayout()
        pan_label = QLabel("Шаг поворота:")
        self.pan_spinbox = QSpinBox()
        self.pan_spinbox.setMinimum(1)
        self.pan_spinbox.setMaximum(180)
        self.pan_spinbox.setValue(self.camera_manager.get_pan_step())
        self.pan_spinbox.setMinimumWidth(80)
        self.pan_spinbox.setSuffix("°")
        pan_layout.addWidget(pan_label)
        pan_layout.addWidget(self.pan_spinbox)
        pan_layout.addStretch()
        controls_layout.addLayout(pan_layout)

        tilt_layout = QHBoxLayout()
        tilt_label = QLabel("Шаг наклона:")
        self.tilt_spinbox = QSpinBox()
        self.tilt_spinbox.setMinimum(1)
        self.tilt_spinbox.setMaximum(180)
        self.tilt_spinbox.setValue(self.camera_manager.get_tilt_step())
        self.tilt_spinbox.setMinimumWidth(80)
        self.tilt_spinbox.setSuffix("°")
        tilt_layout.addWidget(tilt_label)
        tilt_layout.addWidget(self.tilt_spinbox)
        tilt_layout.addStretch()
        controls_layout.addLayout(tilt_layout)

        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Шаг зума:")
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setMinimum(1)
        self.zoom_spinbox.setMaximum(1000)
        self.zoom_spinbox.setValue(self.camera_manager.get_zoom_step())
        self.zoom_spinbox.setMinimumWidth(80)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_spinbox)
        zoom_layout.addStretch()
        controls_layout.addLayout(zoom_layout)

        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        ok_button = QPushButton("ОК")
        ok_button.setProperty("type", "success")
        ok_button.clicked.connect(self.accept)
        ok_button.setMinimumHeight(36)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("Отмена")
        cancel_button.setProperty("type", "danger")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumHeight(36)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def accept(self):
        self.camera_manager.set_pan_step(self.pan_spinbox.value())
        self.camera_manager.set_tilt_step(self.tilt_spinbox.value())
        self.camera_manager.set_zoom_step(self.zoom_spinbox.value())
        super().accept()
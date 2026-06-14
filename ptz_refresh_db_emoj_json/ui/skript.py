# ui/skript.py
import threading
import time
import json
import os
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime


class ScriptEngine:
    def __init__(self, camera_manager, db_manager=None):
        # Прямая ссылка на CameraManager — как в main.py
        self.camera_manager = camera_manager
        self.db = db_manager

        # Флаги управления
        self.is_running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._current_script_key = None

        # Колбэки для UI
        self._on_status_change: Optional[Callable] = None
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None  # Новый колбэк для логов

        # Реестр скриптов
        self._scripts: Dict[str, dict] = {}

        # ОЧЕРЕДЬ КОМАНД — как в main.py для клавиатуры
        self._command_queue: List[str] = []
        self._queue_lock = threading.Lock()

        # Запускаем обработчик команд (аналог process_commands в main.py)
        self._command_thread = threading.Thread(target=self._process_commands, daemon=True)
        self._command_thread.start()

        # Скрипты загружаются через load_custom_scripts() из main.py

    # ==================== КОЛБЭКИ ДЛЯ UI ====================

    def set_callbacks(self, on_status_change: Callable = None, on_progress: Callable = None, on_log: Callable = None):
        self._on_status_change = on_status_change
        self._on_progress = on_progress
        self._on_log = on_log  # Сохраняем колбэк логов

    def _notify_status(self, message: str):
        if self._on_status_change:
            self._on_status_change(message)

    def _notify_progress(self, value: float):
        if self._on_progress:
            self._on_progress(min(1.0, max(0.0, value)))

    def _notify_log(self, message: str):
        """Безопасный вызов колбэка логов"""
        if self._on_log:
            try:
                self._on_log(message)
            except:
                pass  # Не блокируем работу при ошибке UI

    # ==================== ОЧЕРЕДЬ КОМАНД (как в main.py) ====================

    def _add_command(self, command: str):
        with self._queue_lock:
            self._command_queue.append(command)
        # Логируем отправку команды
        self._notify_log(f"В очередь: {command}")

    def _process_commands(self):
        while True:
            command = None
            with self._queue_lock:
                if self._command_queue:
                    command = self._command_queue.pop(0)

            if command:
                try:
                    # ТЕ ЖЕ ВЫЗОВЫ, ЧТО В main.py process_commands:
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
                    elif command == 'reset_ptz':
                        self.camera_manager.reset_ptz()

                    # Логируем успешное выполнение + текущие координаты камеры
                    p = getattr(self.camera_manager, 'pan_position', 0)
                    t = getattr(self.camera_manager, 'tilt_position', 0)
                    z = getattr(self.camera_manager, 'zoom_position', 0)
                    self._notify_log(f"Выполнено: {command} | PTZ: P={p} T={t} Z={z}")

                except Exception as e:
                    # Логируем ошибку выполнения
                    self._notify_log(f"Ошибка: {command} -> {str(e)}")
            else:
                time.sleep(0.01)  # Не грузим CPU

    # ==================== РАБОТА С JSON СКРИПТАМИ ====================

    def _get_scripts_path(self):
        """Получить путь к файлу scripts.json"""
        return os.path.join(os.path.dirname(__file__), "scripts.json")

    def _create_default_scripts_json(self):
        """Создать JSON файл со стандартными скриптами"""
        default_scripts = {
            "pan_patrol": {
                "name": "Патруль: влево-вправо",
                "description": "Автоматический поворот камеры по горизонтали",
                "params": [
                    {"name": "pan_range", "label": "Диапазон (°)", "type": "int", "default": 30, "min": 5, "max": 90},
                    {"name": "step_delay", "label": "Задержка (сек)", "type": "float", "default": 0.3, "min": 0.1, "max": 2.0},
                    {"name": "cycles", "label": "Циклы (0=∞)", "type": "int", "default": 0, "min": 0, "max": 100}
                ],
                "custom": False
            },
            "tilt_patrol": {
                "name": "Патруль: вверх-вниз",
                "description": "Автоматический наклон камеры по вертикали",
                "params": [
                    {"name": "tilt_range", "label": "Диапазон (°)", "type": "int", "default": 20, "min": 5, "max": 60},
                    {"name": "step_delay", "label": "Задержка (сек)", "type": "float", "default": 0.3, "min": 0.1, "max": 2.0},
                    {"name": "cycles", "label": "Циклы (0=∞)", "type": "int", "default": 0, "min": 0, "max": 100}
                ],
                "custom": False
            },
            "zoom_cycle": {
                "name": "Зум-цикл",
                "description": "Плавное увеличение и уменьшение зума",
                "params": [
                    {"name": "zoom_steps", "label": "Шагов зума", "type": "int", "default": 10, "min": 3, "max": 50},
                    {"name": "step_delay", "label": "Задержка (сек)", "type": "float", "default": 0.2, "min": 0.05, "max": 1.0}
                ],
                "custom": False
            },
            "preset_tour": {
                "name": "Тур по позициям",
                "description": "Переход между заданными позициями",
                "params": [
                    {"name": "positions", "label": "Позиции (pan,tilt,zoom;...)", "type": "text", "default": "0,0,0;30,10,200;-30,-10,150", "multiline": True},
                    {"name": "hold_time", "label": "Удержание (сек)", "type": "float", "default": 3.0, "min": 1.0, "max": 30.0}
                ],
                "custom": False
            },
            "reset_center": {
                "name": "Возврат в центр",
                "description": "Сброс камеры в исходное положение",
                "params": [],
                "custom": False
            },
            "scan_360": {
                "name": "Круговое сканирование",
                "description": "Полный поворот на 360° с паузами",
                "params": [
                    {"name": "step_angle", "label": "Шаг (°)", "type": "int", "default": 15, "min": 5, "max": 45},
                    {"name": "pause_time", "label": "Пауза (сек)", "type": "float", "default": 1.0, "min": 0.5, "max": 5.0}
                ],
                "custom": False
            }
        }

        scripts_path = self._get_scripts_path()
        try:
            with open(scripts_path, "w", encoding="utf-8") as f:
                json.dump(default_scripts, f, indent=2, ensure_ascii=False)
            self._notify_log(f"Создан файл scripts.json со стандартными скриптами")
        except Exception as e:
            print(f"Ошибка создания scripts.json: {e}")

    def load_custom_scripts(self):
        """Загрузить все скрипты из JSON файла (вызывается из main.py)"""
        # Очищаем реестр перед загрузкой (чтобы не было дублей при повторном вызове)
        self._scripts.clear()

        scripts_path = self._get_scripts_path()

        # Если файла нет - создаём с стандартными скриптами
        if not os.path.exists(scripts_path):
            self._create_default_scripts_json()

        try:
            with open(scripts_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            standard_count = 0
            custom_count = 0

            for key, info in data.items():
                is_custom = info.get("custom", False)

                if is_custom:
                    # Пользовательский скрипт - создаём wrapper с exec()
                    def make_wrapper(code_str):
                        def wrapper(user_params):
                            safe_globals = {
                                "add_cmd": self._add_command,
                                "camera": self.camera_manager,
                                "db": self.db,
                                "time": time,
                                "params": user_params,
                                "stop": self._stop_event,
                                "status": self._notify_status,
                                "progress": self._notify_progress,
                                "log": self._notify_log
                            }
                            exec(code_str, safe_globals)
                        return wrapper

                    setattr(self, f"_script_{key}", make_wrapper(info.get("code", "")))
                    custom_count += 1
                else:
                    # Стандартный скрипт - метод уже есть в классе
                    standard_count += 1

                # Регистрируем скрипт в реестре
                self._register_script(
                    key=key,
                    name=info.get("name", key),
                    description=info.get("description", ""),
                    params=info.get("params", [])
                )

            self._notify_log(f"Загружено скриптов: {standard_count} стандартных, {custom_count} пользовательских")

        except Exception as e:
            print(f"Ошибка загрузки scripts.json: {e}")
            self._notify_log(f"Ошибка загрузки скриптов: {e}")

    def _register_script(self, key: str, name: str, description: str, params: List[dict]):
        """Регистрация скрипта с привязкой метода по имени"""
        self._scripts[key] = {
            "name": name,
            "description": description,
            "params": params,
            "method_name": f"_script_{key}"
        }

    def get_scripts(self) -> dict:
        """Получить список скриптов для UI"""
        return {
            k: {"name": v["name"], "description": v["description"], "params": v["params"]}
            for k, v in self._scripts.items()
        }

    # ==================== ЗАПУСК/ОСТАНОВКА ====================

    def run_script(self, key: str, params: dict = None) -> bool:
        if key not in self._scripts:
            self._notify_status(f"Скрипт '{key}' не найден")
            return False

        if self.is_running:
            self._notify_status("Сначала остановите текущий скрипт")
            return False

        script_info = self._scripts[key]
        self.is_running = True
        self._current_script_key = key
        self._stop_event.clear()

        self._notify_status(f"Запуск: {script_info['name']}")
        self._notify_log(f"Скрипт '{key}' запущен с параметрами: {params}")

        # Лог в БД
        if self.db:
            self.db.log_script_execution(
                script_id=key,
                camera_id=getattr(self.camera_manager, 'current_index', 1) or 1,
                status='started'
            )

        # Запуск в потоке
        self._thread = threading.Thread(
            target=self._execute_script,
            args=(script_info["method_name"], params or {}),
            daemon=True
        )
        self._thread.start()
        return True

    def _execute_script(self, method_name: str, params: dict):
        """Выполнение скрипта через вызов метода по имени"""
        try:
            method = getattr(self, method_name, None)
            if method and callable(method):
                method(params)  # Прямой вызов метода
            else:
                raise AttributeError(f"Метод {method_name} не найден")
        except Exception as e:
            self._notify_status(f"Ошибка: {str(e)}")
            self._notify_log(f"Исключение в скрипте: {str(e)}")
            if self.db:
                self.db.log_script_execution(
                    script_id=self._current_script_key,
                    camera_id=getattr(self.camera_manager, 'current_index', 1) or 1,
                    status='error',
                    error=str(e),
                    end_time=datetime.now()
                )
        finally:
            self.is_running = False
            self._current_script_key = None
            self._notify_status("Скрипт завершён")
            self._notify_log("Скрипт завершил выполнение")

    def stop_script(self):
        """Остановка скрипта"""
        if not self.is_running:
            return
        self._notify_status("Остановка...")
        self._notify_log("Пользователь запросил остановку скрипта")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.is_running = False

    # ==================== СКРИПТЫ — "НАЖИМАЮТ КНОПКИ" ====================

    def _script_pan_patrol(self, params: dict):
        pan_range = params.get("pan_range", 30)
        step_delay = params.get("step_delay", 0.3)
        max_cycles = params.get("cycles", 0)

        direction = 1
        cycle_count = 0
        steps_per_side = max(1, pan_range // self.camera_manager.get_pan_step())

        self._notify_status("Патрулирование: старт")
        self._notify_log(f"Патруль: диапазон={pan_range}°, задержка={step_delay}с, шаги={steps_per_side}")

        while not self._stop_event.is_set():
            if max_cycles > 0 and cycle_count >= max_cycles:
                break

            for _ in range(steps_per_side):
                if self._stop_event.is_set(): break
                cmd = 'pan_right' if direction > 0 else 'pan_left'
                self._add_command(cmd)
                time.sleep(step_delay)
                self._notify_progress(0.5 if direction > 0 else 0.0)

            if self._stop_event.is_set(): break
            time.sleep(0.3)

            for _ in range(steps_per_side):
                if self._stop_event.is_set(): break
                cmd = 'pan_left' if direction > 0 else 'pan_right'
                self._add_command(cmd)
                time.sleep(step_delay)
                self._notify_progress(1.0 if direction > 0 else 0.5)

            if self._stop_event.is_set(): break
            direction *= -1
            cycle_count += 1
            self._notify_status(f"Цикл {cycle_count}" if max_cycles else "Патрулирование...")

        self._notify_status("Патрулирование завершено")

    def _script_tilt_patrol(self, params: dict):
        tilt_range = params.get("tilt_range", 20)
        step_delay = params.get("step_delay", 0.3)
        max_cycles = params.get("cycles", 0)

        direction = 1
        cycle_count = 0
        steps_per_side = max(1, tilt_range // self.camera_manager.get_tilt_step())

        self._notify_status("Вертикальный патруль: старт")
        self._notify_log(f"Патруль: диапазон={tilt_range}°, задержка={step_delay}с")

        while not self._stop_event.is_set():
            if max_cycles > 0 and cycle_count >= max_cycles: break
            for _ in range(steps_per_side):
                if self._stop_event.is_set(): break
                cmd = 'tilt_up' if direction > 0 else 'tilt_down'
                self._add_command(cmd)
                time.sleep(step_delay)
            if self._stop_event.is_set(): break
            time.sleep(0.3)
            for _ in range(steps_per_side):
                if self._stop_event.is_set(): break
                cmd = 'tilt_down' if direction > 0 else 'tilt_up'
                self._add_command(cmd)
                time.sleep(step_delay)
            if self._stop_event.is_set(): break
            direction *= -1
            cycle_count += 1
        self._notify_status("Вертикальный патруль завершён")

    def _script_zoom_cycle(self, params: dict):
        zoom_steps = params.get("zoom_steps", 10)
        step_delay = params.get("step_delay", 0.2)

        self._notify_status("Зум-цикл: старт")
        self._notify_log(f"Зум-цикл: шаги={zoom_steps}, задержка={step_delay}с")

        while not self._stop_event.is_set():
            for i in range(zoom_steps):
                if self._stop_event.is_set(): break
                self._add_command('zoom_in')
                time.sleep(step_delay)
                self._notify_progress(i / zoom_steps)
            if self._stop_event.is_set(): break
            time.sleep(0.3)
            for i in range(zoom_steps):
                if self._stop_event.is_set(): break
                self._add_command('zoom_out')
                time.sleep(step_delay)
                self._notify_progress(1.0 - i / zoom_steps)
            if self._stop_event.is_set(): break
            time.sleep(0.3)
        self._notify_status("Зум-цикл завершён")

    def _script_preset_tour(self, params: dict):
        positions_str = params.get("positions", "0,0,0;30,10,200;-30,-10,150")
        hold_time = params.get("hold_time", 3.0)

        positions = []
        for pos in positions_str.strip().split(";"):
            parts = pos.strip().split(",")
            if len(parts) >= 3:
                try:
                    positions.append({'pan': int(parts[0]), 'tilt': int(parts[1]), 'zoom': int(parts[2])})
                except ValueError:
                    continue

        if not positions:
            self._notify_status("Нет валидных позиций")
            self._notify_log("Не удалось распарсить позиции")
            return

        self._notify_status(f"Тур: {len(positions)} позиций")
        self._notify_log(f"Загружено позиций: {len(positions)}")

        current_idx = 0
        while not self._stop_event.is_set():
            target = positions[current_idx]
            self._notify_status(f"Позиция {current_idx + 1}/{len(positions)}")
            self._notify_log(f"Переход к: P={target['pan']} T={target['tilt']} Z={target['zoom']}")

            steps = 20
            for step in range(steps):
                if self._stop_event.is_set(): break
                curr_pan = getattr(self.camera_manager, 'pan_position', 0)
                curr_tilt = getattr(self.camera_manager, 'tilt_position', 0)
                curr_zoom = getattr(self.camera_manager, 'zoom_position', 0)

                new_pan = curr_pan + (target['pan'] - curr_pan) // max(1, steps - step)
                new_tilt = curr_tilt + (target['tilt'] - curr_tilt) // max(1, steps - step)
                new_zoom = curr_zoom + (target['zoom'] - curr_zoom) // max(1, steps - step)

                self.camera_manager.set_pan(new_pan)
                self.camera_manager.set_tilt(new_tilt)
                self.camera_manager.set_zoom(new_zoom)

                time.sleep(0.05)
                self._notify_progress(step / steps)

            if self._stop_event.is_set(): break
            time.sleep(hold_time)
            current_idx = (current_idx + 1) % len(positions)
        self._notify_status("Тур завершён")

    def _script_reset_center(self, params: dict):
        self._notify_status("Возврат в центр...")
        self._notify_log("Отправка команды сброса PTZ")
        self._add_command('reset_ptz')
        time.sleep(0.3)
        self._notify_progress(1.0)
        self._notify_status("Камера в центре")

    def _script_scan_360(self, params: dict):
        step_angle = params.get("step_angle", 15)
        pause_time = params.get("pause_time", 1.0)

        self._notify_status("Сканирование 360°: старт")
        self._notify_log(f"Сканирование: шаг={step_angle}°, пауза={pause_time}с")

        pan_step = self.camera_manager.get_pan_step()
        total_steps = max(1, 360 // step_angle)

        for step in range(total_steps):
            if self._stop_event.is_set(): break
            self._add_command('pan_right')
            time.sleep(0.1)
            self._notify_progress((step + 1) / total_steps)
            time.sleep(pause_time)
        self._notify_status("Сканирование завершено")

    # ==================== ПОЛЬЗОВАТЕЛЬСКИЕ СКРИПТЫ ====================

    def save_custom_script(self, key: str, name: str, description: str, code: str, params: List[dict]) -> bool:
        try:
            scripts_path = self._get_scripts_path()
            data = {}

            # Загружаем существующие скрипты
            if os.path.exists(scripts_path):
                with open(scripts_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            # Добавляем/обновляем пользовательский скрипт
            data[key] = {
                "name": name,
                "description": description,
                "code": code,
                "params": params,
                "custom": True
            }

            # Сохраняем обратно в JSON
            with open(scripts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Создаём wrapper для выполнения
            def wrapper(user_params):
                safe_globals = {
                    "add_cmd": self._add_command,
                    "camera": self.camera_manager,
                    "db": self.db,
                    "time": time,
                    "params": user_params,
                    "stop": self._stop_event,
                    "status": self._notify_status,
                    "progress": self._notify_progress,
                    "log": self._notify_log,
                }
                exec(code, safe_globals)

            setattr(self, f"_script_{key}", wrapper)
            self._register_script(key, name, description, params)
            self._notify_log(f"Пользовательский скрипт '{key}' сохранён и зарегистрирован")
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            self._notify_log(f"Ошибка сохранения скрипта: {e}")
            return False

    def delete_script(self, key: str) -> bool:
        """Удалить скрипт из JSON файла"""
        try:
            scripts_path = self._get_scripts_path()
            if not os.path.exists(scripts_path):
                return False

            with open(scripts_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if key not in data:
                self._notify_log(f"Скрипт '{key}' не найден")
                return False

            # Нельзя удалять стандартные скрипты
            if not data[key].get("custom", False):
                self._notify_log(f"Нельзя удалить стандартный скрипт '{key}'")
                return False

            # Удаляем из JSON
            del data[key]

            with open(scripts_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Удаляем из реестра
            if key in self._scripts:
                del self._scripts[key]

            # Удаляем метод
            method_name = f"_script_{key}"
            if hasattr(self, method_name):
                delattr(self, method_name)

            self._notify_log(f"Скрипт '{key}' удалён")
            return True

        except Exception as e:
            print(f"Ошибка удаления скрипта: {e}")
            self._notify_log(f"Ошибка удаления скрипта: {e}")
            return False

    def reload_scripts(self):
        """Перезагрузить все скрипты из JSON"""
        self.load_custom_scripts()
        self._notify_log("Скрипты перезагружены")
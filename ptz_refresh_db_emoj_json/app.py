# app.py
import sys
import os
import json
from PyQt5.QtWidgets import QApplication
from styles.theme import apply_dark_theme
from ui.main import MainWindow
from core.database import DBManager

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    config_path = os.path.join(ROOT_DIR, 'config.json')
    if not os.path.exists(config_path):
        default = {
            "database": {"host": "MySQL-8.4", "user": "root", "password": "", "database": "camera_tracker_db"},
            "controls": {"pan_step": 5, "tilt_step": 5, "zoom_step": 100},
            "camera": {"default_camera": 0}
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    
    config = load_config()
    db_cfg = config.get('database', {})
    db = None
    try:
        db = DBManager(
            host=db_cfg.get('host', 'MySQL-8.4'),
            user=db_cfg.get('user', 'root'),
            password=db_cfg.get('password', ''),
            database=db_cfg.get('database', 'camera_tracker_db')
        )
        print("База данных подключена")
    except Exception as e:
        print(f"БД не подключена: {e}")
    
    window = MainWindow(db_manager=db, config=config)
    window.show()
    sys.exit(app.exec_())
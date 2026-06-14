# core/database.py
import mysql.connector
from mysql.connector import Error, pooling
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBManager:
    """Менеджер пула соединений с MySQL 8.4"""
    
    def __init__(self, host: str, user: str, password: str, database: str):
        self.pool = None
        self._init_pool(host, user, password, database)
    
    def _init_pool(self, host: str, user: str, password: str, database: str):
        try:
            config = {
                'host': host,
                'user': user,
                'password': password,
                'database': database,
                'charset': 'utf8mb4',
                'autocommit': True,
                'pool_name': 'ptz_tracker_pool',
                'pool_size': 5,
                'pool_reset_session': True,
                'use_pure': True
            }
            self.pool = pooling.MySQLConnectionPool(**config)
            logger.info("Подключение к MySQL пулу установлено")
        except Error as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            self.pool = None

    def _execute(self, query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False):
        if not self.pool:
            logger.error("Пул соединений не инициализирован")
            return None
            
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return cursor.lastrowid if query.strip().upper().startswith("INSERT") else cursor.rowcount
        except Error as e:
            logger.error(f"Ошибка БД: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    # === КАМЕРЫ ===
    def upsert_camera(self, name: str, conn_type: str = 'usb', conn_str: str = '') -> Optional[int]:
        query = """INSERT INTO cameras (name, connection_type, connection_string) 
                   VALUES (%s, %s, %s) 
                   ON DUPLICATE KEY UPDATE updated_at=NOW()"""
        return self._execute(query, (name, conn_type, conn_str))

    def get_active_cameras(self) -> List[Dict]:
        return self._execute("SELECT * FROM cameras WHERE is_active=1", fetch_all=True) or []

    # === СКРИПТЫ ===
    def upsert_script(self, name: str, desc: str, code: dict, params: list, is_system: bool = False) -> Optional[int]:
        query = """INSERT INTO scripts (name, description, code, parameters, is_system) 
                   VALUES (%s, %s, %s, %s, %s) 
                   ON DUPLICATE KEY UPDATE description=%s, code=%s, parameters=%s, updated_at=NOW()"""
        code_json = json.dumps(code, ensure_ascii=False)
        params_json = json.dumps(params, ensure_ascii=False)
        return self._execute(query, (name, desc, code_json, params_json, is_system, desc, code_json, params_json))

    def get_all_scripts(self) -> List[Dict]:
        return self._execute("SELECT id, name, description, is_system, created_at FROM scripts ORDER BY created_at DESC", fetch_all=True) or []

    # === ЛОГИ ===
    def log_script_execution(self, script_id: int, camera_id: int, status: str, error: str = None, end_time: datetime = None) -> Optional[int]:
        query = """INSERT INTO script_logs (script_id, camera_id, status, error_message, end_time) 
                   VALUES (%s, %s, %s, %s, %s)"""
        return self._execute(query, (script_id, camera_id, status, error, end_time))

    def log_tracking_event(self, camera_id: int, bbox: dict, confidence: float, action: str, ptz_pos: dict) -> Optional[int]:
        query = """INSERT INTO tracking_events (camera_id, bbox, confidence, action_taken, ptz_position) 
                   VALUES (%s, %s, %s, %s, %s)"""
        return self._execute(query, (camera_id, json.dumps(bbox), confidence, action, json.dumps(ptz_pos)))

    # === НАСТРОЙКИ ===
    def save_setting(self, key: str, value: Any, desc: str = '') -> Optional[int]:
        val_json = json.dumps(value) if not isinstance(value, str) else value
        query = """INSERT INTO app_settings (setting_key, setting_value, description) 
                   VALUES (%s, %s, %s) 
                   ON DUPLICATE KEY UPDATE setting_value=%s, updated_at=NOW()"""
        return self._execute(query, (key, val_json, desc, val_json))

    def get_setting(self, key: str, default=None) -> Any:
        res = self._execute("SELECT setting_value FROM app_settings WHERE setting_key=%s", (key,), fetch_one=True)
        if res and res.get('setting_value'):
            try:
                return json.loads(res['setting_value'])
            except json.JSONDecodeError:
                return res['setting_value']
        return default
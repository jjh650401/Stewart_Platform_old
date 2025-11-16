# D:\Python_Programs\Stewart_Platform\src\core\database_manager.py

import sqlite3
import pandas as pd
from typing import Tuple, List, Dict, Any
import os
from src.core import config

class DatabaseManager:
    def __init__(self, db_path: str = "stewart_platform.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS motors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL, -- 型號
                brand TEXT, -- 品牌
                rated_power_kw REAL, -- 額定功率 (kW)
                rated_speed_rpm REAL, -- 額定轉速 (rpm)
                rated_torque_nm REAL, -- 額定扭矩 (N·m)
                max_torque_nm REAL, -- 最大扭矩 (N·m)
                rated_current_a REAL, -- 額定電流 (A)
                max_current_a REAL, -- 最大電流 (A)
                weight_kg REAL, -- 重量 (kg)
                servo_driver_model TEXT, -- 伺服驅動器型號
                max_allowed_speed_rpm REAL, -- 最大允許轉速 (rpm)
                shaft_diameter_mm REAL, -- 軸徑 (mm)
                shaft_length_mm REAL -- 軸長 (mm)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL, -- 型號
                brand TEXT, -- 品牌
                dia_mm REAL, -- 直徑 (mm)
                lead_mm REAL, -- 導程 (mm)
                ca_n REAL, -- 動態負荷額定值 (N)
                coa_n REAL, -- 靜態負荷額定值 (N)
                pearl_dia_mm REAL, -- 滾珠直徑 (mm)
                rigidity_kg_um REAL, -- 剛性 (kg/μm)
                nut_length_mm REAL -- 螺母長度 (mm)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pulleys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL, -- 型號
                brand TEXT, -- 品牌
                teeth INTEGER, -- 齒數
                diameter_mm REAL, -- 直徑 (mm)
                belt_width_mm REAL -- 皮帶寬度 (mm)
            )
        """)
        self.conn.commit()

    def import_from_excel(self, file_path: str, table_name: str, column_mapping: Dict[str, str], sheet_name: str = 'Sheet1') -> Tuple[bool, str, int, int, List[Dict[str, Any]]]:
        """
        從指定的 Excel 檔案匯入資料到資料庫，支援指定工作表名稱。
        
        Args:
            file_path (str): Excel 檔案的路徑。
            table_name (str): 目標資料表名稱（motors, screws, pulleys）。
            column_mapping (Dict[str, str]): Excel 欄位與資料庫欄位的映射。
            sheet_name (str): 要載入的 Excel 工作表名稱，預設為 'Sheet1'。
        
        Returns:
            Tuple[bool, str, int, int, List[Dict[str, Any]]]: 
                - 是否成功
                - 訊息
                - 成功匯入的筆數
                - 失敗的筆數
                - 重複型號的清單（包含差異資料）
        
        Raises:
            ValueError: 若工作表名稱無效，則拋出錯誤並列出可用工作表。
        """
        try:
            # 檢查檔案是否存在
            if not os.path.exists(file_path):
                return False, f"檔案 {file_path} 不存在", 0, 0, []
            
            # 檢查並載入指定工作表
            excel_file = pd.ExcelFile(file_path)
            if sheet_name not in excel_file.sheet_names:
                return False, f"工作表 '{sheet_name}' 不存在。可用工作表：{', '.join(excel_file.sheet_names)}", 0, 0, []
            
            # 載入指定工作表的資料
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 診斷：打印實際欄位和映射
            print(f"實際 Excel 欄位: {df.columns.tolist()}")
            print(f"映射欄位: {list(column_mapping.keys())}")
            
            # 檢查必要欄位與映射
            required_field = 'model'
            model_mapping = {k: v for k, v in column_mapping.items() if v == required_field}
            if not model_mapping:
                return False, f"映射中缺少必要欄位: {required_field}", 0, 0, []
            model_col = list(model_mapping.keys())[0]
            if model_col not in df.columns:
                print(f"檢查: {model_col} 不存在於 Excel 欄位中")
                return False, f"Excel 中缺少必要欄位: {model_col} (映射到 {required_field})", 0, 0, []
            
            # 檢查 mapping 鍵是否在 Excel 欄位中，記錄缺失的欄位
            missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
            if missing_columns:
                print(f"警告: 以下 mapping 鍵在 Excel 中缺失: {missing_columns}")
            
            cursor = self.conn.cursor()
            success_count, error_count = 0, 0
            duplicates = []

            table_columns = {
                'motors': [
                    'model', 'brand', 'rated_power_kw', 'rated_speed_rpm', 'rated_torque_nm',
                    'max_torque_nm', 'rated_current_a', 'max_current_a', 'weight_kg',
                    'servo_driver_model', 'max_allowed_speed_rpm', 'shaft_diameter_mm', 'shaft_length_mm'
                ],
                'screws': [
                    'model', 'brand', 'dia_mm', 'lead_mm', 'ca_n', 'coa_n',
                    'pearl_dia_mm', 'rigidity_kg_um', 'nut_length_mm'
                ],
                'pulleys': [
                    'model', 'brand', 'teeth', 'diameter_mm', 'belt_width_mm'
                ]
            }
            default_values = {
                'motors': {
                    'model': '', 'brand': '', 'rated_power_kw': 0, 'rated_speed_rpm': 0,
                    'rated_torque_nm': 0, 'max_torque_nm': 0, 'rated_current_a': 0,
                    'max_current_a': 0, 'weight_kg': 0, 'servo_driver_model': '',
                    'max_allowed_speed_rpm': 0, 'shaft_diameter_mm': 0, 'shaft_length_mm': 0
                },
                'screws': {
                    'model': '', 'brand': '', 'dia_mm': 0, 'lead_mm': 0,
                    'ca_n': 0, 'coa_n': 0, 'pearl_dia_mm': 0, 'rigidity_kg_um': 0, 'nut_length_mm': 0
                },
                'pulleys': {
                    'model': '', 'brand': '', 'teeth': 0, 'diameter_mm': 0, 'belt_width_mm': 0
                }
            }

            for index, row in df.iterrows():
                data = {col: default_values[table_name][col] for col in table_columns[table_name]}
                for excel_col, db_col in column_mapping.items():
                    if excel_col in row and pd.notna(row[excel_col]):
                        try:
                            cleaned_value = str(row[excel_col]).strip()
                            # 針對 screws 表的 ca_n 和 coa_n 進行單位轉換 (kgf to N)
                            if table_name == 'screws' and db_col in ['ca_n', 'coa_n']:
                                cleaned_value = float(cleaned_value) * config.G_ACCELERATION
                            data[db_col] = cleaned_value if db_col != 'model' else cleaned_value or 'Unknown'
                        except (ValueError, TypeError) as e:
                            print(f"行 {index + 2} 欄位 {excel_col} 轉換失敗: {str(e)}, 使用預設值")
                            data[db_col] = default_values[table_name][db_col]

                if not data.get('model') or pd.isna(data.get('model')):
                    print(f"行 {index + 2} 型號 (model) 無效或空值，已設為 'Unknown'")
                    data['model'] = 'Unknown'
                    error_count += 1
                    continue

                cursor.execute(f"SELECT * FROM {table_name} WHERE model = ?", (data['model'],))
                existing = cursor.fetchone()
                if existing:
                    existing_data = dict(zip([desc[0] for desc in cursor.description], existing))
                    differences = {k: (existing_data.get(k), data.get(k)) for k in data if k in existing_data and existing_data[k] != data[k]}
                    if differences:
                        duplicates.append({
                            'model': data['model'],
                            'differences': differences,
                            'new_data': data,
                            'existing_data': existing_data
                        })
                    error_count += 1
                    continue

                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' * len(data))
                try:
                    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
                    success_count += 1
                except Exception as e:
                    print(f"行 {index + 2} 插入失敗: {str(e)}")
                    error_count += 1

            self.conn.commit()
            msg = f"匯入完成: 成功 {success_count} 筆，失敗 {error_count} 筆"
            if duplicates:
                msg += f"，發現 {len(duplicates)} 筆重複型號"
            return True, msg, success_count, error_count, duplicates

        except Exception as e:
            return False, f"匯入失敗: {str(e)}", 0, 0, []

    def get_all_motors(self) -> Tuple[List[Dict[str, Any]], str]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM motors")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()], ""
        except Exception as e:
            return [], f"查詢失敗: {str(e)}"

    def get_all_screws(self) -> Tuple[List[Dict[str, Any]], str]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM screws")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()], ""
        except Exception as e:
            return [], f"查詢失敗: {str(e)}"

    def get_all_pulleys(self) -> Tuple[List[Dict[str, Any]], str]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM pulleys")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()], ""
        except Exception as e:
            return [], f"查詢失敗: {str(e)}"

    def add_item(self, table_name: str, item_data: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            cursor = self.conn.cursor()
            columns = ', '.join(item_data.keys())
            placeholders = ', '.join('?' * len(item_data))
            cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(item_data.values()))
            self.conn.commit()
            return True, "新增成功"
        except Exception as e:
            return False, f"新增失敗: {str(e)}"

    def update_item(self, table_name: str, item_id: int, item_data: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            cursor = self.conn.cursor()
            columns = ', '.join(f"{k} = ?" for k in item_data.keys())
            values = list(item_data.values()) + [item_id]
            cursor.execute(f"UPDATE {table_name} SET {columns} WHERE id = ?", values)
            self.conn.commit()
            return True, "更新成功"
        except Exception as e:
            return False, f"更新失敗: {str(e)}"

    def delete_item(self, table_name: str, item_id: int) -> Tuple[bool, str]:
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
            self.conn.commit()
            return True, "刪除成功"
        except Exception as e:
            return False, f"刪除失敗: {str(e)}"

    def close(self):
        """手動關閉資料庫連線"""
        self.conn.close()

    def __del__(self):
        self.conn.close()
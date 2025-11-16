# D:\Python_Programs\Stewart_Platform\excel_test.py

import pandas as pd
import sqlite3
import os

# 定義映射（與 database_management_widget.py 一致）
column_mappings = {
    "motors": {
        "伺服馬達型號": "model",
        "廠牌": "brand",
        "額定出力容量_kW": "rated_power_kw",
        "額定回轉數_rpm": "rated_speed_rpm",
        "額定轉矩_Nm": "rated_torque_nm",
        "最大轉矩_Nm": "max_torque_nm",
        "額定電流_A": "rated_current_a",
        "最大電流_A": "max_current_a",
        "伺服驅動器型號": "servo_driver_model",
        "瞬間容許轉速_rpm": "max_allowed_speed_rpm",
        "重量_kg": "weight_kg",
        "軸心直徑_mm": "shaft_diameter_mm",
        "軸心長度_mm": "shaft_length_mm"
    },
    "screws": {
        "螺桿型號": "model",
        "廠牌": "brand",
        "螺桿軸外徑_mm": "dia_mm",
        "螺桿螺距_mm": "lead_mm",
        "動額定負荷_Ca_kgf": "ca_n",
        "靜額定負荷_Coa_kgf": "coa_n",
        "最大長度_mm": "max_length_mm",
        "效率_pct": "efficiency_pct",
        "珠徑_Da_mm": "pearl_dia_mm",
        "剛性_K_kg/μm": "rigidity_kg_um",
        "螺帽長度_L": "nut_length_mm"
    },
    "pulleys": {
        "皮帶輪型號": "model",
        "廠牌": "brand",
        "齒數": "teeth",
        "齒輪直徑_PD_mm": "diameter_mm",
        "皮帶寬度_mm": "belt_width_mm"
    }
}

# 定義資料庫表結構
table_definitions = {
    "motors": """
        CREATE TABLE IF NOT EXISTS motors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            brand TEXT,
            rated_power_kw REAL,
            rated_speed_rpm REAL,
            rated_torque_nm REAL,
            max_torque_nm REAL,
            rated_current_a REAL,
            max_current_a REAL,
            weight_kg REAL,
            servo_driver_model TEXT,
            max_allowed_speed_rpm REAL,
            shaft_diameter_mm REAL,
            shaft_length_mm REAL
        )
    """,
    "screws": """
        CREATE TABLE IF NOT EXISTS screws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            brand TEXT,
            dia_mm REAL,
            lead_mm REAL,
            ca_n REAL,
            coa_n REAL,
            max_length_mm REAL,
            efficiency_pct REAL,
            pearl_dia_mm REAL,
            rigidity_kg_um REAL,
            nut_length_mm REAL
        )
    """,
    "pulleys": """
        CREATE TABLE IF NOT EXISTS pulleys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            brand TEXT,
            teeth INTEGER,
            diameter_mm REAL,
            belt_width_mm REAL
        )
    """
}

# 定義 Excel 檔案路徑
excel_files = {
    "motors": "D:/Python_Programs/Stewart_Platform/伺服馬達資料.xlsx",
    "screws": "D:/Python_Programs/Stewart_Platform/螺桿資料.xlsx",  # 假設檔案名稱，請替換實際路徑
    "pulleys": "D:/Python_Programs/Stewart_Platform/皮帶輪資料.xlsx"  # 假設檔案名稱，請替換實際路徑
}

# 預設值
default_values = {
    "motors": {"model": "Unknown", "brand": "", "rated_power_kw": 0, "rated_speed_rpm": 0,
               "rated_torque_nm": 0, "max_torque_nm": 0, "rated_current_a": 0,
               "max_current_a": 0, "weight_kg": 0, "servo_driver_model": "",
               "max_allowed_speed_rpm": 0, "shaft_diameter_mm": 0, "shaft_length_mm": 0},
    "screws": {"model": "Unknown", "brand": "", "dia_mm": 0, "lead_mm": 0,
               "ca_n": 0, "coa_n": 0, "max_length_mm": 2000, "efficiency_pct": 0,
               "pearl_dia_mm": 0, "rigidity_kg_um": 0, "nut_length_mm": 0},
    "pulleys": {"model": "Unknown", "brand": "", "teeth": 0, "diameter_mm": 0, "belt_width_mm": 0}
}

def test_excel_import():
    # 連線到 SQLite 資料庫
    db_path = "test_database.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 創建表
    for table_name, definition in table_definitions.items():
        cursor.execute(definition)

    # 處理每個 Excel 檔案
    for table_name, file_path in excel_files.items():
        if not os.path.exists(file_path):
            print(f"警告: 檔案 {file_path} 不存在，跳過")
            continue

        # 讀取 Excel 檔案（假設第一個工作表）
        try:
            df = pd.read_excel(file_path, sheet_name=0)
            print(f"成功讀取 {file_path}")
            print(f"欄位名稱: {df.columns.tolist()}")
            print(f"前 5 行數據:\n{df.head().to_string()}\n")

            # 驗證映射鍵
            mapping = column_mappings[table_name]
            missing_cols = [col for col in mapping.keys() if col not in df.columns]
            if missing_cols:
                print(f"警告: 以下欄位在 {file_path} 中缺失: {missing_cols}")
            else:
                print(f"{file_path} 的欄位與映射完全匹配")

            # 準備數據
            for index, row in df.iterrows():
                data = {col: default_values[table_name][col] for col in default_values[table_name]}
                for excel_col, db_col in mapping.items():
                    if excel_col in row and pd.notna(row[excel_col]):
                        try:
                            cleaned_value = str(row[excel_col]).strip()
                            data[db_col] = cleaned_value if db_col != 'model' else cleaned_value or 'Unknown'
                        except (ValueError, TypeError) as e:
                            print(f"行 {index + 2} 欄位 {excel_col} 轉換失敗: {str(e)}, 使用預設值")
                            data[db_col] = default_values[table_name][db_col]

                # 插入數據
                columns = ', '.join(data.keys())
                placeholders = ', '.join('?' * len(data))
                try:
                    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
                    print(f"成功插入行 {index + 2} 到 {table_name}")
                except Exception as e:
                    print(f"行 {index + 2} 插入失敗: {str(e)}")

        except Exception as e:
            print(f"讀取 {file_path} 失敗: {str(e)}")

    # 提交並關閉
    conn.commit()
    conn.close()
    print("測試完成，資料庫已生成: test_database.db")

if __name__ == "__main__":
    test_excel_import()
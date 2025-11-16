# D:\Python_Programs\Stewart_Platform\debug_drive_system.py - 調試腳本

import sys
import os

# 確保在專案根目錄運行
project_root = r"D:\Python_Programs\Stewart_Platform"
os.chdir(project_root)
sys.path.insert(0, project_root)

from src.core.database_manager import DatabaseManager
from src.core.drive_system_engine import DriveSystemEngine
from src.core import config

print("=== 調試腳本開始 ===")

# 1. DatabaseManager.get_all_motors() 返回數據
print("\n=== 1. DatabaseManager.get_all_motors() 返回數據 ===")
db_manager = DatabaseManager()
motors, error = db_manager.get_all_motors()
if error:
    print(f"Error: {error}")
else:
    print(f"Number of motors: {len(motors)}")
    for motor in motors:
        print(f"Model: {motor.get('model', 'N/A')}, rated_torque_nm: {motor.get('rated_torque_nm', 'N/A')}, max_torque_nm: {motor.get('max_torque_nm', 'N/A')}, rated_speed_rpm: {motor.get('rated_speed_rpm', 'N/A')}, id: {motor.get('id', 'N/A')}")

    sme_motor = next((m for m in motors if m.get('model') == 'SME-L20020SDBU'), None)
    if sme_motor:
        print(f"\nSME-L20020SDBU full data: {sme_motor}")

# 2. DatabaseManager.get_all_screws() 返回數據
print("\n=== 2. DatabaseManager.get_all_screws() 返回數據 ===")
screws, screw_error = db_manager.get_all_screws()
if screw_error:
    print(f"Error: {screw_error}")
else:
    print(f"Number of screws: {len(screws)}")
    for screw in screws:
        print(f"Model: {screw.get('model', 'N/A')}, lead_mm: {screw.get('lead_mm', 'N/A')}, ca_n: {screw.get('ca_n', 'N/A')}, dia_mm: {screw.get('dia_mm', 'N/A')}, id: {screw.get('id', 'N/A')}")

    fsdc_screw = next((s for s in screws if s.get('model') == 'FSDC-025x10_6.35-5'), None)
    if fsdc_screw:
        print(f"\nFSDC-025x10_6.35-5 full data: {fsdc_screw}")

# 3. DatabaseManager.get_all_pulleys() 返回數據
print("\n=== 3. DatabaseManager.get_all_pulleys() 返回數據 ===")
pulleys, pulley_error = db_manager.get_all_pulleys()
if pulley_error:
    print(f"Error: {pulley_error}")
else:
    print(f"Number of pulleys: {len(pulleys)}")
    for pulley in pulleys:
        print(f"Model: {pulley.get('model', 'N/A')}, teeth: {pulley.get('teeth', 'N/A')}, belt_width_mm: {pulley.get('belt_width_mm', 'N/A')}, id: {pulley.get('id', 'N/A')}")

# 4. 模擬 params 輸入值檢查
print("\n=== 4. 模擬 params 輸入值檢查 ===")
engine = DriveSystemEngine()

# 模擬 params 並包含 t_profile 和 mode
params = {
    'mode': 'manual',  # 添加 mode
    'moving_part_mass': 500.0,
    'max_acceleration': 0.2,
    'friction_coeff': 0.01,
    'install_angle': 90.0,
    'max_velocity': 0.22,
    'screw_efficiency': 90.0,
    'transmission_efficiency': 95.0,
    'ratio': 1.5,
    'required_lead_mm': 10.0,
    'hours_per_day': 10.0,
    'days_per_year': 250.0,
    'expected_years': 2.0,
    'duty_cycle': 70.0,
    'selected_motor_id': 132,
    'selected_screw_id': 90,  # 假設的螺桿 ID，需與 get_all_screws() 結果匹配
    # 模擬 t_profile 值（請根據實際情況調整）
    't_up_accel': 6.0,
    't_up_const': 60.0,
    't_up_decel': 30.0,
    't_down_accel': 6.0,
    't_down_const': 60.0,
    't_down_decel': 30.0,
    't_stop': 168.0
}
print(f"Simulated params: {params}")

# 呼叫 calculate() 並打印結果
result = engine.calculate(params)
print("\n=== DriveSystemEngine.calculate() 結果 ===")
print(result)

# 打印關鍵調試值
print("\n=== 關鍵調試值 ===")
print(f"max_axial_force: {result.get('torque_analysis', {}).get('max_axial_force', 'N/A')}")
print(f"avg_axial_force: {result.get('life_analysis', {}).get('avg_axial_force', 'N/A')}")
print(f"avg_screw_speed_rpm: {result.get('life_analysis', {}).get('avg_screw_speed_rpm', 'N/A')}")
print(f"required_ca: {result.get('life_analysis', {}).get('required_ca', 'N/A')}")
print(f"required_hours: {result.get('life_analysis', {}).get('required_life_hours', 'N/A')}")
print(f"estimated_l10h_life: {result.get('life_analysis', {}).get('estimated_l10h_life', 'N/A')}")
print(f"Debug: Extracted params - ratio: {params.get('ratio')}, screw_efficiency: {params.get('screw_efficiency')}, transmission_efficiency: {params.get('transmission_efficiency')}")

print("=== 調試腳本結束 ===")
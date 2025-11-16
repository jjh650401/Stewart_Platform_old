# debug_drive_system.py - 調試腳本
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
    # 打印所有馬達的相關字段
    for motor in motors:
        print(f"Model: {motor.get('model', 'N/A')}, rated_torque_nm: {motor.get('rated_torque_nm', 'N/A')}, max_torque_nm: {motor.get('max_torque_nm', 'N/A')}, rated_speed_rpm: {motor.get('rated_speed_rpm', 'N/A')}, rated_rpm: {motor.get('rated_rpm', 'N/A')}, id: {motor.get('id', 'N/A')}")

    # 特別打印 SME-L20020SDBU
    sme_motor = next((m for m in motors if m.get('model') == 'SME-L20020SDBU'), None)
    if sme_motor:
        print(f"\nSME-L20020SDBU full data: {sme_motor}")
    else:
        print("\nSME-L20020SDBU not found in motors!")

# 2. 模擬 params 和 DriveSystemEngine.calculate() 輸入值檢查
print("\n=== 2. 模擬 params 輸入值檢查 ===")
engine = DriveSystemEngine()

# 基於您的截圖模擬 params
params = {
    'mode': 'manual',
    'moving_part_mass': 500.0,
    'max_acceleration': 0.2,
    'friction_coeff': 0.01,  # 假設值
    'install_angle': 90.0,
    'max_velocity': 0.220,
    'screw_efficiency': 90.0,
    'transmission_efficiency': 95.0,
    'ratio': 2.0,
    'required_lead_mm': 10.0,
    'hours_per_day': 8.0,
    'days_per_year': 250.0,
    'expected_years': 5.0,
    'duty_cycle': 80.0,
    'selected_motor_id': 132  # 從錯誤訊息
}

print(f"Simulated params: {params}")
print(f"模擬 params (請補充 t_profile): {params}")

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

print("=== 調試腳本結束 ===")
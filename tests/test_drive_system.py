# D:\Python_Programs\Stewart_Platform\tests\test_drive_system.py

import unittest
import sqlite3
import pandas as pd
import os
import sys
from unittest.mock import patch

# 動態添加專案根目錄到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.database_manager import DatabaseManager

class TestDriveSystem(unittest.TestCase):
    def setUp(self):
        # 使用記憶體資料庫進行測試
        self.db_manager = DatabaseManager()
        self.db_manager.conn = sqlite3.connect(':memory:')
        self.db_manager._create_tables()

        # 模擬 Excel 檔案資料（缺少部分欄位以測試預設值）
        self.motor_data = pd.DataFrame({
            '伺服馬達型號': ['MTR001', 'MTR002'],
            '廠牌': ['BrandA', 'BrandB'],
            '額定出力容量_kW': [1.5, 2.0],
            '額定回轉數_rpm': [3000, 3500],
            '額定轉矩_Nm': [4.77, 6.37],
            '最大轉矩_Nm': [14.31, 19.11],
            '額定電流_A': [5.0, 6.0],
            '最大電流_A': [15.0, 18.0],
            '重量_kg': [10.0, 12.0],
            '伺服驅動器型號': ['DRV001', 'DRV002'],
            '瞬間容許轉速_rpm': [4500, 5000],
            '軸心直徑_mm': [20.0, 22.0],
            '軸心長度_mm': [50.0, 55.0]
            # 未提供 rotor_inertia_kgm2, rated_voltage_v
        })
        self.ball_screw_data = pd.DataFrame({
            '螺桿型號': ['SCR001', 'SCR002'],
            '廠牌': ['BrandA', 'BrandB'],
            '螺桿軸外徑_mm': [25.0, 32.0],
            '螺桿螺距_mm': [5.0, 10.0],
            '動額定負荷_Ca_kgf': [1000, 1500],
            '靜額定負荷_Coa_kgf': [2000, 3000],
            '珠徑_Da_mm': [4.0, 5.0],
            '剛性_K_kg/um': [50.0, 60.0]
            # 未提供 max_length_mm, efficiency_pct
        })
        self.pulley_data = pd.DataFrame({
            '皮帶輪型號': ['PUL001', 'PUL002'],
            '廠牌': ['BrandA', 'BrandB'],
            '齒數_teeth': [20, 30],
            '齒輪直徑_PD_mm': [50.0, 75.0],
            '皮帶寬度_mm': [15.0, 20.0],
            '齒輪厚度_W_mm': [10.0, 12.0]
        })

    def tearDown(self):
        self.db_manager.conn.close()

    def test_import_motors(self):
        with patch('pandas.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.motor_data
            column_mapping = {
                '伺服馬達型號': 'model',
                '廠牌': 'manufacturer',
                '額定出力容量_kW': 'rated_power_kw',
                '額定回轉數_rpm': 'rated_speed_rpm',
                '額定轉矩_Nm': 'rated_torque_nm',
                '最大轉矩_Nm': 'max_torque_nm',
                '額定電流_A': 'rated_current_a',
                '最大電流_A': 'max_current_a',
                '重量_kg': 'weight_kg',
                '伺服驅動器型號': 'servo_driver_model',
                '瞬間容許轉速_rpm': 'max_allowed_speed_rpm',
                '軸心直徑_mm': 'shaft_diameter_mm',
                '軸心長度_mm': 'shaft_length_mm'
            }
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_motors.xlsx', 'motors', column_mapping)
            
            self.assertTrue(success, msg)
            self.assertEqual(success_count, 2, "應成功匯入 2 筆馬達資料")
            self.assertEqual(error_count, 0, "不應有匯入失敗的資料")
            self.assertEqual(len(duplicates), 0, "不應有重複型號")

            motors, _ = self.db_manager.get_all_motors()
            self.assertEqual(len(motors), 2)
            self.assertEqual(motors[0]['model'], 'MTR001')
            self.assertEqual(motors[0]['servo_driver_model'], 'DRV001')
            self.assertEqual(motors[0]['max_allowed_speed_rpm'], 4500)
            self.assertEqual(motors[0]['shaft_diameter_mm'], 20.0)
            self.assertEqual(motors[0]['shaft_length_mm'], 50.0)
            self.assertEqual(motors[0]['rotor_inertia_kgm2'], 0, "rotor_inertia_kgm2 應為預設值 0")
            self.assertEqual(motors[0]['rated_voltage_v'], 0, "rated_voltage_v 應為預設值 0")

    def test_import_ball_screws(self):
        with patch('pandas.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.ball_screw_data
            column_mapping = {
                '螺桿型號': 'model',
                '廠牌': 'manufacturer',
                '螺桿軸外徑_mm': 'dia_mm',
                '螺桿螺距_mm': 'lead_mm',
                '動額定負荷_Ca_kgf': 'ca_n',
                '靜額定負荷_Coa_kgf': 'coa_n',
                '珠徑_Da_mm': 'pearl_dia_mm',
                '剛性_K_kg/um': 'rigidity_kg_um'
            }
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_screws.xlsx', 'ball_screws', column_mapping)
            
            self.assertTrue(success, msg)
            self.assertEqual(success_count, 2, "應成功匯入 2 筆螺桿資料")
            self.assertEqual(error_count, 0, "不應有匯入失敗的資料")
            self.assertEqual(len(duplicates), 0, "不應有重複型號")

            screws, _ = self.db_manager.get_all_ball_screws()
            self.assertEqual(len(screws), 2)
            self.assertEqual(screws[0]['model'], 'SCR001')
            self.assertAlmostEqual(screws[0]['ca_n'], 1000 * 9.81, places=2)
            self.assertAlmostEqual(screws[0]['coa_n'], 2000 * 9.81, places=2)
            self.assertEqual(screws[0]['pearl_dia_mm'], 4.0)
            self.assertEqual(screws[0]['rigidity_kg_um'], 50.0)
            self.assertEqual(screws[0]['max_length_mm'], 2000, "max_length_mm 應為預設值 2000")
            self.assertEqual(screws[0]['efficiency_pct'], 0, "efficiency_pct 應為預設值 0")

    def test_import_pulleys(self):
        with patch('pandas.read_excel') as mock_read_excel:
            mock_read_excel.return_value = self.pulley_data
            column_mapping = {
                '皮帶輪型號': 'model',
                '廠牌': 'manufacturer',
                '齒數_teeth': 'teeth',
                '齒輪直徑_PD_mm': 'diameter_mm',
                '皮帶寬度_mm': 'width_mm',
                '齒輪厚度_W_mm': 'thickness_mm'
            }
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_pulleys.xlsx', 'pulleys', column_mapping)
            
            self.assertTrue(success, msg)
            self.assertEqual(success_count, 2, "應成功匯入 2 筆皮帶輪資料")
            self.assertEqual(error_count, 0, "不應有匯入失敗的資料")
            self.assertEqual(len(duplicates), 0, "不應有重複型號")

            pulleys, _ = self.db_manager.get_all_pulleys()
            self.assertEqual(len(pulleys), 2)
            self.assertEqual(pulleys[0]['model'], 'PUL001')
            self.assertEqual(pulleys[0]['teeth'], 20)
            self.assertEqual(pulleys[0]['diameter_mm'], 50.0)
            self.assertEqual(pulleys[0]['thickness_mm'], 10.0)

    def test_duplicate_model(self):
        with patch('pandas.read_excel') as mock_read_excel:
            duplicate_data = pd.DataFrame({
                '伺服馬達型號': ['MTR001', 'MTR001'],
                '廠牌': ['BrandA', 'BrandA'],
                '額定出力容量_kW': [1.5, 1.8],
                '額定回轉數_rpm': [3000, 3200],
                '額定轉矩_Nm': [4.77, 5.0],
                '最大轉矩_Nm': [14.31, 15.0],
                '額定電流_A': [5.0, 5.5],
                '最大電流_A': [15.0, 16.0],
                '重量_kg': [10.0, 11.0],
                '伺服驅動器型號': ['DRV001', 'DRV002'],
                '瞬間容許轉速_rpm': [4500, 4600],
                '軸心直徑_mm': [20.0, 21.0],
                '軸心長度_mm': [50.0, 51.0]
            })
            mock_read_excel.return_value = duplicate_data
            column_mapping = {
                '伺服馬達型號': 'model',
                '廠牌': 'manufacturer',
                '額定出力容量_kW': 'rated_power_kw',
                '額定回轉數_rpm': 'rated_speed_rpm',
                '額定轉矩_Nm': 'rated_torque_nm',
                '最大轉矩_Nm': 'max_torque_nm',
                '額定電流_A': 'rated_current_a',
                '最大電流_A': 'max_current_a',
                '重量_kg': 'weight_kg',
                '伺服驅動器型號': 'servo_driver_model',
                '瞬間容許轉速_rpm': 'max_allowed_speed_rpm',
                '軸心直徑_mm': 'shaft_diameter_mm',
                '軸心長度_mm': 'shaft_length_mm'
            }
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_motors.xlsx', 'motors', column_mapping)
            
            self.assertTrue(success, msg)
            self.assertEqual(success_count, 1, "應只匯入 1 筆非重複資料")
            self.assertEqual(error_count, 1, "應有 1 筆重複型號被跳過")
            self.assertEqual(len(duplicates), 1, "應檢測到 1 筆重複型號")
            self.assertEqual(duplicates[0]['model'], 'MTR001')
            self.assertIn('rated_power_kw', duplicates[0]['differences'])

            motors, _ = self.db_manager.get_all_motors()
            self.assertEqual(len(motors), 1)
            self.assertEqual(motors[0]['model'], 'MTR001')
            self.assertEqual(motors[0]['rated_power_kw'], 1.5)

    def test_duplicate_model_differences(self):
        with patch('pandas.read_excel') as mock_read_excel:
            initial_data = pd.DataFrame({
                '螺桿型號': ['SCR001'],
                '廠牌': ['BrandA'],
                '螺桿軸外徑_mm': [25.0],
                '螺桿螺距_mm': [5.0],
                '動額定負荷_Ca_kgf': [1000],
                '靜額定負荷_Coa_kgf': [2000],
                '珠徑_Da_mm': [4.0],
                '剛性_K_kg/um': [50.0]
            })
            mock_read_excel.return_value = initial_data
            column_mapping = {
                '螺桿型號': 'model',
                '廠牌': 'manufacturer',
                '螺桿軸外徑_mm': 'dia_mm',
                '螺桿螺距_mm': 'lead_mm',
                '動額定負荷_Ca_kgf': 'ca_n',
                '靜額定負荷_Coa_kgf': 'coa_n',
                '珠徑_Da_mm': 'pearl_dia_mm',
                '剛性_K_kg/um': 'rigidity_kg_um'
            }
            self.db_manager.import_from_excel('mock_screws.xlsx', 'ball_screws', column_mapping)

        with patch('pandas.read_excel') as mock_read_excel:
            duplicate_data = pd.DataFrame({
                '螺桿型號': ['SCR001'],
                '廠牌': ['BrandA'],
                '螺桿軸外徑_mm': [26.0],
                '螺桿螺距_mm': [5.0],
                '動額定負荷_Ca_kgf': [1000],
                '靜額定負荷_Coa_kgf': [2000],
                '珠徑_Da_mm': [4.0],
                '剛性_K_kg/um': [60.0]
            })
            mock_read_excel.return_value = duplicate_data
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_screws.xlsx', 'ball_screws', column_mapping)
            
            self.assertTrue(success, msg)
            self.assertEqual(success_count, 0, "不應插入重複資料")
            self.assertEqual(error_count, 1, "應有 1 筆重複型號")
            self.assertEqual(len(duplicates), 1, "應檢測到 1 筆重複型號")
            self.assertEqual(duplicates[0]['model'], 'SCR001')
            self.assertEqual(duplicates[0]['differences']['dia_mm'], (25.0, 26.0))
            self.assertEqual(duplicates[0]['differences']['rigidity_kg_um'], (50.0, 60.0))

            screws, _ = self.db_manager.get_all_ball_screws()
            self.assertEqual(len(screws), 1)
            self.assertEqual(screws[0]['dia_mm'], 25.0)

    def test_missing_required_field(self):
        with patch('pandas.read_excel') as mock_read_excel:
            invalid_data = pd.DataFrame({
                '廠牌': ['BrandA'],
                '額定出力容量_kW': [1.5]
            })
            mock_read_excel.return_value = invalid_data
            column_mapping = {
                '伺服馬達型號': 'model',
                '廠牌': 'manufacturer',
                '額定出力容量_kW': 'rated_power_kw'
            }
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                'mock_motors.xlsx', 'motors', column_mapping)
            
            self.assertFalse(success, "缺少必要欄位應失敗")
            self.assertIn("缺少必要欄位", msg)
            self.assertEqual(success_count, 0)
            self.assertEqual(error_count, 0)
            self.assertEqual(len(duplicates), 0)

if __name__ == '__main__':
    unittest.main()
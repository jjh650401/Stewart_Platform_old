# D:\Python_Programs\Stewart_Platform\src\core\drive_system_engine.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# 本檔案中的所有長度數值，無論是與使用者互動，還是與核心引擎交換，皆使用 mm 單位。
# 檔案內不應存在任何 m 與 mm 之間的轉換（除了極少數與外部定義比較所需之局部轉換）。
# 詳情請參閱《基礎背景與規則.v5.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

import numpy as np
from src.core import config
from src.core.database_manager import DatabaseManager
from typing import List, Dict, Any, Tuple

class DriveSystemEngine:
    """
    執行所有與驅動系統相關的後端計算，包含零件篩選與負荷係數計算。
    回傳詳細的 profile 數據供前端使用。
    """
    def __init__(self):
        # --- MODIFIED: v2.0 ALIGNED ---
        print("驅動系統計算引擎 (DriveSystemEngine) v4.0 (v2.0 Guide Aligned) 已初始化。")
        self.g_m_s2 = 9.81  # 標準重力加速度 (m/s²)，用於將 kg 轉換為 N
        self.db_manager = DatabaseManager()

    def calculate(self, params: dict) -> Dict[str, Any]:
        try:
            mode = params.get('mode', 'manual')
            if mode == 'manual':
                return self._calculate_manual_mode(params)
            elif mode == 'auto':
                return self._calculate_auto_mode(params)
            else:
                return {'success': False, 'warnings': [{'message': '未知的計算模式。', 'details': {}}]}
        except KeyError as e:
            return {'success': False, 'warnings': [{'message': f"輸入參數缺失: {e}", 'details': {}}]}
        except Exception as e:
            return {'success': False, 'warnings': [{'message': f"計算時發生未知錯誤: {e}", 'details': {}}]}

    def _get_sanitized_params(self, params: dict) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """ 從輸入字典中提取並驗證計算所需參數，返回標準化字典及警告訊息 """
        warnings = []
        sanitized = {}

        # --- v2.0 Variable Mapping ---
        param_map = {
            'moving_part_mass': 'm', 'max_acceleration_g': 'a_max_g', 'friction_coeff': 'mu',
            'install_angle': 'theta', 'max_velocity_mm_s': 'v_max',
            'hours_per_day': 'R_h', 'days_per_year': 'R_d', 'expected_years': 'R_y',
            'duty_cycle': 'Aval', 'ratio': 'i', 'screw_efficiency': 'eta_screw',
            'transmission_efficiency': 'eta_pulley', 'load_factor': 'f_w',
            't_up_accel': 't_ua', 't_up_const': 't_uc', 't_up_decel': 't_ud',
            't_down_accel': 't_da', 't_down_const': 't_dc', 't_down_decel': 't_dd',
            't_stop': 't_s'
        }

        for old_key, new_key in param_map.items():
            if old_key in params:
                sanitized[new_key] = params[old_key]

        # 單位與型別轉換
        sanitized['theta_rad'] = np.deg2rad(sanitized.get('theta', 90.0))
        sanitized['a_max'] = sanitized.get('a_max_g', 0.0) * self.g_m_s2  # m/s²
        sanitized['eta_screw'] /= 100.0
        sanitized['eta_pulley'] /= 100.0
        sanitized['Aval'] /= 100.0
        
        # 填充必要但可能缺失的參數
        # --- MODIFIED: Use new config variable name ---
        sanitized.setdefault('i', config.DRIVE_DEFAULT_REDUCTION_RATIO_I)
        
        return sanitized, warnings

    def _calculate_manual_mode(self, params: dict) -> Dict[str, Any]:
        p, warnings = self._get_sanitized_params(params)

        load_profile = self._calculate_load_profile(p['m'], p['a_max'], p['theta_rad'], p['mu'])
        F_eq = self._calculate_average_axial_force(load_profile, p)
        n_eq = self._calculate_average_screw_speed(p, params.get('selected_screw_id'))
        
        # 從 v_max 直接計算 f_w
        p['f_w'] = self.get_load_factor(p['v_max'])

        return self._perform_common_calculations(p, params, load_profile, F_eq, n_eq, warnings)

    def _calculate_auto_mode(self, params: dict) -> Dict[str, Any]:
        p, warnings = self._get_sanitized_params(params)
        
        max_axial_force = params.get('max_axial_force_from_sim', 0)
        
        # 簡化負載模型
        load_profile = {
            'F_ua': max_axial_force, 'F_uc': max_axial_force, 'F_ud': max_axial_force * 0.8,
            'F_da': -max_axial_force * 0.2, 'F_dc': -max_axial_force * 0.2, 'F_dd': max_axial_force * 0.5,
            'F_s': max(0, p['m'] * self.g_m_s2 * np.sin(p['theta_rad']) - p['mu'] * p['m'] * self.g_m_s2 * np.cos(p['theta_rad']))
        }
        F_eq = self._calculate_average_axial_force(load_profile, p)
        n_eq = self._calculate_average_screw_speed(p, params.get('selected_screw_id'))
        
        p['f_w'] = self.get_load_factor(p['v_max'])
        
        return self._perform_common_calculations(p, params, load_profile, F_eq, n_eq, warnings)

    def _perform_common_calculations(self, p: dict, original_params: dict, load_profile: dict, F_eq: float, n_eq: float, warnings: list) -> Dict[str, Any]:
        L_T = self._calculate_required_life_hours(p)
        C_ac = self._calculate_required_ca(F_eq, n_eq, L_T, p['f_w'])
        
        F_max = max(abs(val) for val in load_profile.values()) if load_profile else 0

        # 零件篩選
        motors, motor_error = self.filter_motors(p, original_params, F_max)
        if motor_error: warnings.append({'message': motor_error, 'details': {}})
        
        screws, screw_error = self.filter_screws(p, original_params, F_eq, n_eq, L_T, C_ac)
        if screw_error: warnings.append({'message': screw_error, 'details': {}})
        
        # 獲取選定零件
        selected_motor = next((m for m in motors if m['id'] == original_params.get('selected_motor_id')), motors[0] if motors else None)
        selected_screw = next((s for s in screws if s['id'] == original_params.get('selected_screw_id')), screws[0] if screws else None)
        
        P_h = selected_screw['P_h'] if selected_screw else 10.0 # 使用選定螺桿導程或預設值
        T_motor_req = self._calculate_required_motor_torque(F_max, P_h, p['eta_screw'], p['i'], p['eta_pulley'])
        
        L_t = 0
        if selected_screw:
            L_t = self._calculate_l10_life_hours(selected_screw['C_a'], F_eq, n_eq, p['f_w'])
        
        # 執行檢查
        warnings.extend(self._perform_checks(p, T_motor_req, n_eq, C_ac, selected_motor, selected_screw))

        return {
            'success': True,
            'warnings': warnings,
            'results': {
                'F_max': F_max, 'F_eq': F_eq, 'n_eq': n_eq, 'L_T': L_T, 'L_t': L_t,
                'C_ac': C_ac, 'T_motor_req': T_motor_req, 'f_w': p['f_w']
            },
            'profiles': {'load_profile': load_profile},
            'components': {'motors': motors, 'screws': screws}
        }
    
    def _perform_checks(self, p, T_motor_req, n_eq, C_ac, motor, screw) -> list:
        """根據選定零件執行一系列工程檢查"""
        warnings = []
        if not motor or not screw:
            warnings.append({'message': '缺少選定零件，無法進行校核。', 'details': {}})
            return warnings

        # 扭力檢查
        if T_motor_req > motor['T_motor_peak']:
            warnings.append({'message': '馬達峰值扭力不足', 'details': {'required': T_motor_req, 'available': motor['T_motor_peak']}})
        elif T_motor_req > motor['T_motor_rated']:
            warnings.append({'message': '需求扭力超過額定扭力，請注意運轉條件。', 'details': {'required': T_motor_req, 'available': motor['T_motor_rated']}})
        
        # 轉速檢查
        required_rpm_at_vmax = (p['v_max'] * 60) / screw['P_h'] if screw['P_h'] > 0 else 0
        motor_rpm_at_vmax = required_rpm_at_vmax * p['i']
        if motor_rpm_at_vmax > motor['n_motor_max']:
             warnings.append({'message': '馬達最高轉速不足', 'details': {'required': motor_rpm_at_vmax, 'available': motor['n_motor_max']}})
        elif motor_rpm_at_vmax > motor['n_motor_rated']:
             warnings.append({'message': '需求轉速超過額定轉速', 'details': {'required': motor_rpm_at_vmax, 'available': motor['n_motor_rated']}})

        # 螺桿動負荷檢查
        if C_ac > screw['C_a']:
            warnings.append({'message': '螺桿動額定負荷不足', 'details': {'required': C_ac, 'available': screw['C_a']}})
            
        return warnings

    def _calculate_load_profile(self, m, a_max, theta_rad, mu) -> Dict[str, float]:
        """ 根據指南 2.0 的七段式運動負載模型計算 """
        mg = m * self.g_m_s2
        ma = m * a_max
        
        sin_theta = np.sin(theta_rad)
        cos_theta = np.cos(theta_rad)

        return {
            'F_ua': mg * (sin_theta + mu * cos_theta) + ma,
            'F_uc': mg * (sin_theta + mu * cos_theta),
            'F_ud': mg * (sin_theta + mu * cos_theta) - ma,
            'F_da': mu * mg * cos_theta - mg * sin_theta - ma,
            'F_dc': mu * mg * cos_theta - mg * sin_theta,
            'F_dd': ma + mu * mg * cos_theta - mg * sin_theta,
            'F_s': max(0, mg * sin_theta - mu * mg * cos_theta)
        }

    def _calculate_average_axial_force(self, load_profile, p) -> float:
        """ 根據指南 2.0 公式計算平均(等效)軸向負載 F_eq """
        times = {'ua': p.get('t_ua',0), 'uc': p.get('t_uc',0), 'ud': p.get('t_ud',0),
                 'da': p.get('t_da',0), 'dc': p.get('t_dc',0), 'dd': p.get('t_dd',0),
                 's':  p.get('t_s',0)}
        
        total_time = sum(times.values())
        if total_time <= 0: return 0.0

        sum_f3_t = sum(abs(load_profile.get(f'F_{key}', 0))**3 * t for key, t in times.items())
        
        return (sum_f3_t / total_time) ** (1/3)

    def _calculate_average_screw_speed(self, p, selected_screw_id) -> float:
        """ 根據指南 2.0 公式計算平均(等效)轉速 n_eq """
        screws, _ = self.db_manager.get_all_screws()
        selected_screw = next((s for s in screws if s['id'] == selected_screw_id), screws[0] if screws else None)
        P_h = selected_screw['P_h'] if selected_screw else 10.0

        n_max = (p['v_max'] / P_h) * 60 if P_h > 0 else 0
        
        speeds = {'ua': n_max / 2, 'uc': n_max, 'ud': n_max / 2,
                  'da': n_max / 2, 'dc': n_max, 'dd': n_max / 2,
                  's': 0}
        
        times = {'ua': p.get('t_ua',0), 'uc': p.get('t_uc',0), 'ud': p.get('t_ud',0),
                 'da': p.get('t_da',0), 'dc': p.get('t_dc',0), 'dd': p.get('t_dd',0),
                 's':  p.get('t_s',0)}

        total_time = sum(times.values())
        if total_time <= 0: return 0.0

        weighted_speed_sum = sum(speeds[key] * t for key, t in times.items())
        
        return weighted_speed_sum / total_time

    def _calculate_required_motor_torque(self, F_i, P_h, eta_screw, i, eta_pulley) -> float:
        """ 根據指南 2.0 公式計算需求馬達扭矩 T_motor_req """
        if any(v <= 0 for v in [eta_screw, i, eta_pulley]): return 0.0
        # P_h (導程) 單位為 mm，需轉換為 m 以計算 Nm
        return (F_i * P_h) / (2 * np.pi * eta_screw * i * eta_pulley * 1000)

    def _calculate_required_life_hours(self, p) -> float:
        """ 根據指南 2.0 公式計算需求壽命 L_T """
        return p.get('R_h', 0) * p.get('R_d', 0) * p.get('R_y', 0) * p.get('Aval', 1.0)

    def _calculate_required_ca(self, F_eq, n_eq, L_T, f_w) -> float:
        """ 根據指南 2.0 公式計算需求動額定負荷 C_ac """
        if F_eq <= 0 or n_eq <= 0 or L_T <= 0: return 0.0
        return F_eq * f_w * ((60 * n_eq * L_T) / 1e6) ** (1/3)

    def _calculate_l10_life_hours(self, C_a, F_eq, n_eq, f_w) -> float:
        """ 根據指南 2.0 公式計算預估疲勞壽命 L_t """
        if C_a <= 0 or F_eq <= 0 or n_eq <= 0 or f_w <= 0: return float('inf')
        try:
            life_revs = (C_a / (F_eq * f_w))**3 * 1e6
            return life_revs / (60 * n_eq)
        except (ValueError, ZeroDivisionError, OverflowError):
            return float('inf')

    def filter_motors(self, p: dict, original_params: dict, F_max: float) -> Tuple[List[Dict[str, Any]], str]:
        selected_screw_id = original_params.get('selected_screw_id')
        screws, _ = self.db_manager.get_all_screws()
        selected_screw = next((s for s in screws if s['id'] == selected_screw_id), screws[0] if screws else None)
        P_h = selected_screw['P_h'] if selected_screw else 10.0

        T_motor_req = self._calculate_required_motor_torque(F_max, P_h, p['eta_screw'], p['i'], p['eta_pulley'])
        required_rpm_at_vmax = (p['v_max'] * 60) / P_h if P_h > 0 else 0
        motor_rpm_at_vmax = required_rpm_at_vmax * p['i']

        all_motors, error = self.db_manager.get_all_motors()
        if error: return [], f"無法取得馬達資料: {error}"

        filtered_motors = [
            motor for motor in all_motors
            if motor.get('T_motor_rated', 0) > 0 and
               motor.get('T_motor_peak', 0) >= T_motor_req and
               motor.get('n_motor_max', 0) >= motor_rpm_at_vmax
        ]
        
        if not filtered_motors:
            return [], "無符合條件的馬達。"
        
        return filtered_motors, ""

    def filter_screws(self, p: dict, original_params: dict, F_eq: float, n_eq: float, L_T: float, C_ac: float) -> Tuple[List[Dict[str, Any]], str]:
        all_screws, error = self.db_manager.get_all_screws()
        if error: return [], f"無法取得螺桿資料: {error}"

        filtered_screws = [
            screw for screw in all_screws
            if screw.get('C_a', 0) >= C_ac
        ]

        if not filtered_screws:
            return [], "無符合條件的螺桿。"
            
        return filtered_screws, ""

    def get_load_factor(self, v_max_mm_s: float) -> float:
        """ 根據指南 2.0 表格自動判斷負荷係數 f_w """
        v_max_m_min = v_max_mm_s * 0.06 # mm/s to m/min
        
        if v_max_m_min < 15:
            return config.LOAD_FACTOR_RANGES['v_max < 15']['default']
        elif 15 <= v_max_m_min < 60:
            return config.LOAD_FACTOR_RANGES['15 <= v_max < 60']['default']
        else: # v_max >= 60
            return config.LOAD_FACTOR_RANGES['v_max >= 60']['default']
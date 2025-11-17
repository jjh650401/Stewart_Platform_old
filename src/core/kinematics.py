# D:\Python_Programs\Stewart_Platform\src\core\kinematics.py

# ==============================================================================
# [修改註記 - v2.3-kinematics-fix (3-DOF 座標修正)]
# 日期: 2025-11-17
# 修改者: AI 協作
# ------------------------------------------------------------------------------
# 修改重點:
# 1. [Bug修復] _analyze_workspace_3dof: 移除了 Heave (Z) 軸結果減去 H0 的操作。
#    - 原因: UI 層 (analysis_widget.py) 已經包含了將絕對座標轉為相對座標的邏輯。
#    - 解決: 防止「雙重扣減」導致 Heave 數值錯誤及 3D 預覽錯位，確保與 6-DOF 架構一致。
# ==============================================================================

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# UI層、核心層的所有長度參數的儲存、傳遞與計算皆以 mm 為準。

import numpy as np
import json
from scipy.optimize import least_squares, fsolve, minimize, Bounds
from scipy.spatial.transform import Rotation

from . import config
from .dynamics_engine import DynamicsEngine

class CoreEngine:
    def __init__(self):
        super().__init__()
        self.params = {}
        self.formulas = []
        self.dynamics_engine = DynamicsEngine()
        self._register_formulas()
        print("核心計算引擎 (CoreEngine) v2.3 (3-DOF 修正版) 已初始化。")
        self.reset()

    def reset(self):
        self.platform_type = '6-DOF'
        self.zero_pose_offset = {'x': 0.0, 'y': 0.0}
        self.zero_pose_base_angle = None
        self.zero_pose_platform_angle = None
        self._initialize_parameters()
        print("[除錯] 核心引擎的完整狀態已重置。")

    def reset_calculated_parameters(self):
        self.params['Ra'] = 0.0
        self.params['Rb'] = 0.0
        self.params['s_mech'] = 0.0
        self.params['H'] = 0.0
        self.zero_pose_offset = {'x': 0.0, 'y': 0.0}
        self.zero_pose_base_angle = None
        self.zero_pose_platform_angle = None
        print("[除錯] 核心引擎的衍生計算參數已重置。")

    def _initialize_parameters(self):
        self.params.clear()
        geom_keys_6dof = ['Df', 'df', 'Dm', 'dm']
        geom_keys_3dof = ['D1', 'D2', 'd1', 'd2']
        geom_keys_common = [
            'Ra', 'Rb', 'H', 'L', 's_mech', 's_buffer', 's',
            'base_joint_limit', 'platform_joint_limit',
            'm_p', 'm_l', 'com_l_x', 'com_l_y', 'com_l_z', 'a_lin', 'a_ang'
        ]
        for key in geom_keys_6dof + geom_keys_3dof + geom_keys_common:
            self.params[key] = 0.0
        
        self.params['enable_joint_limits'] = False
        self.params['platform_joint_style'] = 'bottom'
        
        # [新增 - v2.3] 新增 6-DOF 輸入相位角參數
        self.params['phase_angle_deg'] = 0.0

        self.params['base_joint_limit'] = np.deg2rad(25.0)
        self.params['platform_joint_limit'] = np.deg2rad(25.0)

        self.params['view_params'] = None
        
        dyn_keys = {
            'm_p': 200.0, 
            'm_l': 500.0, 
            'com_l_x': 0.0, 
            'com_l_y': 0.0, 
            'com_l_z': 700.0,
            'a_lin': [0.0, 0.0, config.G_ACCELERATION],
            'a_ang': [0.0, 0.0, 0.0]
        }
        self.params.update(dyn_keys)
        
        self.params['drive_system_data'] = {}

    def _register_formulas(self):
        self.formulas.clear()
        self.formulas.append({'output': 'Ra', 'inputs': ['Df', 'df'], 'func': self._calculate_radius_from_chords, 'type': '6-DOF'})
        self.formulas.append({'output': 'Rb', 'inputs': ['Dm', 'dm'], 'func': self._calculate_radius_from_chords, 'type': '6-DOF'})
        self.formulas.append({'output': 's_mech', 'inputs': ['s', 's_buffer'], 'func': lambda p: p.get('s', 0) + p.get('s_buffer', 0), 'type': 'common'})

    def update_parameter(self, name, value):
        self.params[name] = value

    def update_drive_system_data(self, data: dict):
        self.params['drive_system_data'] = data

    def get_parameter(self, name):
        return self.params.get(name)

    def get_all_parameters(self):
        all_params = self.params.copy()
        all_params['zero_pose_offset_x'] = self.zero_pose_offset.get('x', 0.0)
        all_params['zero_pose_offset_y'] = self.zero_pose_offset.get('y', 0.0)
        return all_params

    def load_parameters(self, data: dict) -> str:
        status = 'mm_native'
        if data.get('unit_system') != 'mm':
            if data.get('L', 100.0) < 10.0:
                print("[提示] 偵測到舊版 (m) 單位專案檔，正在自動轉換為 mm 單位。")
                status = 'conversion_done'
                length_keys = [
                    'Df', 'df', 'Dm', 'dm', 'D1', 'D2', 'd1', 'd2', 'Ra', 'Rb', 
                    'H', 'L', 's_mech', 's_buffer', 's', 'h',
                    'load_com_x', 'load_com_y', 'load_com_z', 'com_l_x', 'com_l_y', 'com_l_z',
                    'zero_pose_offset_x', 'zero_pose_offset_y'
                ]
                for key in length_keys:
                    if key in data and data[key] is not None:
                        data[key] *= 1000.0
        
        self.platform_type = data.get('platform_type', '6-DOF')
        
        name_map = {
            'platform_mass': 'm_p', 'load_mass': 'm_l', 'load_com_x': 'com_l_x',
            'load_com_y': 'com_l_y', 'load_com_z': 'com_l_z', 'lin_accel': 'a_lin',
            'ang_accel': 'a_ang'
        }

        for old_key, value in data.items():
            new_key = name_map.get(old_key, old_key)
            if new_key in self.params:
                self.params[new_key] = value

        self.zero_pose_offset['x'] = data.get('zero_pose_offset_x', 0.0)
        self.zero_pose_offset['y'] = data.get('zero_pose_offset_y', 0.0)

        return status

    def save_to_file(self, filepath: str):
        try:
            data_to_save = self.get_all_parameters()
            data_to_save['platform_type'] = self.platform_type
            data_to_save['unit_system'] = 'mm'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"存檔失敗: {e}"); return False

    def load_from_file(self, filepath: str) -> dict | None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"讀檔失敗: {e}"); return None
            
    def save_drive_design_to_file(self, filepath: str, data: dict) -> bool:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"儲存驅動系統設計失敗: {e}")
            return False

    def load_drive_design_from_file(self, filepath: str) -> dict | None:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"讀取驅動系統設計失敗: {e}")
            return None
    
    def calculate_target(self, target_name):
        for formula in self.formulas:
            is_common = formula['type'] == 'common'
            type_match = formula['type'] == self.platform_type
            if formula['output'] == target_name and (is_common or type_match):
                required_inputs = formula['inputs']
                if not all(self.params.get(key) is not None and (self.params.get(key) != 0.0 or key in ['s_buffer']) for key in required_inputs):
                    continue
                input_params = {k: self.params[k] for k in required_inputs}
                result = formula['func'](input_params)
                if result is not None and result >= 0:
                    self.update_parameter(target_name, result)
                    return result
        return None

    def calculate_platform_geometry(self):
        self.zero_pose_base_angle = None
        self.zero_pose_platform_angle = None
        
        if self.platform_type == '6-DOF':
            return self._calculate_geometry_6dof()
        elif self.platform_type == '3-DOF':
            success = self._calculate_geometry_3dof()
            return success, "3-DOF 幾何計算失敗" if not success else ""
        return False, "未知的平台類型"

    def _calculate_joint_angles(self, r_matrix, base_nodes, mobile_nodes_world) -> tuple[np.ndarray, np.ndarray]:
        leg_vectors = mobile_nodes_world - np.array(base_nodes)
        leg_norms = np.linalg.norm(leg_vectors, axis=1)
        leg_unit_vectors = np.divide(leg_vectors, leg_norms[:, np.newaxis], where=leg_norms[:, np.newaxis] != 0)
        base_normal = np.array([0, 0, 1])
        base_cos_angles = np.clip(np.dot(leg_unit_vectors, base_normal), -1.0, 1.0)
        joint_style = self.get_parameter('platform_joint_style')
        normal_direction = -1.0 if joint_style == 'bottom' else 1.0
        platform_normal = (r_matrix @ base_normal) * normal_direction
        platform_cos_angles = np.clip(np.sum(-leg_unit_vectors * platform_normal, axis=1), -1.0, 1.0)
        return base_cos_angles, platform_cos_angles

    def is_pose_valid(self, pose_ui: dict, space_type: str) -> bool:
        L, s, s_buffer, s_mech = [self.get_parameter(key) for key in ['L', 's', 's_buffer', 's_mech']]
        if any(p is None for p in [L, s, s_buffer, s_mech]): return False
        leg_min, leg_max = (L + s_buffer / 2.0, L + s_buffer / 2.0 + s) if space_type == 'operational' else (L, L + s_mech)
        
        pose_data = self._get_pose_data_from_ui(pose_ui)
        if not pose_data: return False
        r_matrix, mobile_nodes_world, leg_lengths, base_nodes = pose_data
        
        tolerance = 1e-6
        if not np.all((leg_lengths >= leg_min - tolerance) & (leg_lengths <= leg_max + tolerance)):
            return False
        if not self.get_parameter('enable_joint_limits'):
            return True
        base_limit, platform_limit = self.get_parameter('base_joint_limit'), self.get_parameter('platform_joint_limit')
        if base_limit is None or platform_limit is None or base_limit <= 1e-9 or platform_limit <= 1e-9:
            return True
        
        base_cos_angles, platform_cos_angles = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
        if not np.all(base_cos_angles >= np.cos(base_limit) - tolerance): return False
        if not np.all(platform_cos_angles >= np.cos(platform_limit) - tolerance): return False
        return True
    
    def _get_pose_data_from_ui(self, pose_ui: dict) -> tuple | None:
        h_val = self.get_parameter('H')
        if not h_val or h_val <= 0: return None
        if self.platform_type == '6-DOF':
            offset = self.zero_pose_offset
            # [v2.3 註記] 零位 Yaw 來自 'phase_angle_deg'
            zero_yaw_rad = np.deg2rad(self.params.get('phase_angle_deg', 0.0))
            pose_mm_rad = np.array([offset['x'] + pose_ui.get('x', 0), 
                                  offset['y'] + pose_ui.get('y', 0), 
                                  h_val + pose_ui.get('z', 0), 
                                  np.deg2rad(pose_ui.get('pitch', 0)), 
                                  np.deg2rad(pose_ui.get('roll', 0)), 
                                  zero_yaw_rad + np.deg2rad(pose_ui.get('yaw', 0))]) # Yaw 是相對於零位 Yaw 的偏移
        else:
            pose_mm_rad = np.array([h_val + pose_ui.get('z', 0), 
                                  np.deg2rad(pose_ui.get('pitch', 0)), 
                                  np.deg2rad(pose_ui.get('roll', 0))])
        
        r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(pose_mm_rad)
        if not base_nodes: return None
        leg_lengths = np.linalg.norm(mobile_nodes_world - np.array(base_nodes), axis=1)
        return r_matrix, mobile_nodes_world, leg_lengths, base_nodes

    def _get_world_geometry_from_pose_vec(self, pose_mm_rad: np.ndarray) -> tuple[np.ndarray, np.ndarray, list]:
        base_nodes, mobile_nodes_local = self._get_canonical_nodes()
        if not base_nodes or not mobile_nodes_local:
            return np.identity(3), [], []
        
        if self.platform_type == '6-DOF':
            pos = pose_mm_rad[:3]
            r = Rotation.from_euler('ZXY', [pose_mm_rad[5], pose_mm_rad[3], -pose_mm_rad[4]], degrees=False)
        else:
            pos = np.array([0, 0, pose_mm_rad[0]])
            if len(pose_mm_rad) >= 3:
                r = Rotation.from_euler('ZXY', [0, pose_mm_rad[1], -pose_mm_rad[2]], degrees=False)
            else:
                r = Rotation.from_euler('ZXY', [0, 0, 0], degrees=False)
        r_matrix = r.as_matrix()
        mobile_nodes_world = r.apply(mobile_nodes_local) + pos
        
        return r_matrix, mobile_nodes_world, base_nodes
            
    def calculate_force_for_ui_pose(self, pose_ui: dict) -> list[float] | None:
        pose_data = self._get_pose_data_from_ui(pose_ui)
        if not pose_data: return None
        
        dynamics_params = {
            'm_p': self.get_parameter('m_p'), 'm_l': self.get_parameter('m_l'),
            'com_l_x': self.get_parameter('com_l_x'), 'com_l_y': self.get_parameter('com_l_y'),
            'com_l_z': self.get_parameter('com_l_z'), 'a_lin': self.get_parameter('a_lin'),
            'a_ang': self.get_parameter('a_ang')
        }
        
        r_matrix, mobile_nodes_world, _, base_nodes = pose_data
        pos = np.mean(mobile_nodes_world, axis=0) - r_matrix @ np.mean(self._get_canonical_nodes()[1], axis=0)
        
        platform_params = { 'nodes_3d_base': base_nodes, 'nodes_3d_mobile_world': mobile_nodes_world, 'position': pos, 'orientation_quat': Rotation.from_matrix(r_matrix).as_quat() }
        return self.dynamics_engine.calculate_actuator_forces(platform_params, dynamics_params)

    def get_current_joint_angles_and_vectors(self, pose_ui: dict) -> dict | None:
        pose_data = self._get_pose_data_from_ui(pose_ui)
        if not pose_data: return None
        
        r_matrix, mobile_nodes_world, _, base_nodes = pose_data
        
        base_cos, platform_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
        base_angles_deg = np.rad2deg(np.arccos(base_cos)); platform_angles_deg = np.rad2deg(np.arccos(platform_cos))
        base_normal = np.array([0, 0, 1])
        joint_style = self.get_parameter('platform_joint_style')
        normal_direction = -1.0 if joint_style == 'bottom' else 1.0
        platform_normal_world = (r_matrix @ base_normal) * normal_direction
        return { "base_angles_deg": base_angles_deg, "platform_angles_deg": platform_angles_deg, "base_normal": base_normal, "platform_normal_world": platform_normal_world, "base_nodes": base_nodes, "mobile_nodes_world": mobile_nodes_world }

    def _calculate_radius_from_chords(self, p):
        D_chord, d_chord = (p.get('Df'), p.get('df')) if 'Df' in p else (p.get('Dm'), p.get('dm'))
        if not D_chord or not d_chord or D_chord <= 0 or d_chord <= 0: return None
        
        if D_chord < d_chord: D_chord, d_chord = d_chord, D_chord 

        try:
            def objective_func(R_var):
                R = R_var[0]
                
                ratio_D = D_chord / (2.0 * R)
                ratio_d = d_chord / (2.0 * R)
                
                if ratio_D > 1.0 and ratio_D < 1.000001: ratio_D = 1.0
                if ratio_d > 1.0 and ratio_d < 1.000001: ratio_d = 1.0
                
                if ratio_D > 1.0 or ratio_d > 1.0:
                    return 1e6 

                error = np.arcsin(ratio_D) + np.arcsin(ratio_d) - (np.pi / 3.0)
                return np.abs(error)

            initial_guess = max(D_chord, d_chord * 2.0) 
            
            epsilon = 1e-9
            bounds = [(D_chord / 2.0 + epsilon, D_chord * 10)]

            result = minimize(objective_func, [initial_guess], method='SLSQP', bounds=bounds, tol=1e-10)
            
            if result.success and result.fun < 1e-6:
                return float(result.x[0])
            else:
                print(f"警告: _calculate_radius_from_chords 求解失敗。Success={result.success}, Fun={result.fun}, D={D_chord}, d={d_chord}")
                return None 
        except (ValueError, TypeError, ZeroDivisionError) as e:
            print(f"錯誤: _calculate_radius_from_chords 發生例外: {e}")
            return None

    def _get_canonical_nodes(self):
        if self.platform_type == '6-DOF': return self._get_6dof_nodes()
        elif self.platform_type == '3-DOF': return self._get_3dof_nodes()
        return [], []

    def calculate_initial_height(self) -> float | None:
        required_params_6dof = ['L', 'Ra', 'Rb']
        required_params_3dof = ['L', 'D1', 'D2', 'd1', 'd2']
        
        if self.platform_type == '6-DOF':
            if not all(self.get_parameter(key) and self.get_parameter(key) > 0 for key in required_params_6dof): return None
        else: # 3-DOF
             if not all(self.get_parameter(key) and self.get_parameter(key) > 0 for key in required_params_3dof): return None

        base_nodes, mobile_nodes = self._get_canonical_nodes()
        if not base_nodes or not mobile_nodes: return None
        target_leg_length = self.get_parameter('L')
        
        if self.platform_type == '6-DOF':
            # [v2.3 註記] 零位 Yaw 來自 'phase_angle_deg'
            zero_yaw_rad = np.deg2rad(self.params.get('phase_angle_deg', 0.0))
            def error_func(pose_vars):
                Tx, Ty, Tz, pitch, roll, yaw = pose_vars
                r = Rotation.from_euler('ZXY', [yaw, pitch, roll], degrees=False)
                errors = []
                for i in range(len(base_nodes)):
                    Ai, Bi = np.array(base_nodes[i]), np.array(mobile_nodes[i])
                    li_vec = (np.array([Tx, Ty, Tz]) + r.apply(Bi)) - Ai
                    errors.append(np.linalg.norm(li_vec)**2 - target_leg_length**2)
                return errors
            # [v2.3 註記] 初始猜測的 Yaw 也使用 phase_angle_deg
            result = least_squares(error_func, [0, 0, target_leg_length, 0, 0, zero_yaw_rad], method='lm', ftol=config.GEOMETRY_SOLVER_TOLERANCE)
            return result.x[2] if result.success else None
        else:
            def error_func_3dof(H_var):
                errors = []
                for i in range(len(base_nodes)):
                    li_vec = (np.array([0, 0, H_var[0]]) + np.array(mobile_nodes[i])) - np.array(base_nodes[i])
                    errors.append(np.linalg.norm(li_vec)**2 - target_leg_length**2)
                return np.sum(np.array(errors)**2)
            result = minimize(error_func_3dof, [target_leg_length], method='SLSQP', bounds=[(0, None)])
            return result.x[0] if result.success else None

    # [重要修正] 補回缺失的 _calculate_geometry_6dof 函式
    def _calculate_geometry_6dof(self):
        required = ['L', 's', 's_buffer', 's_mech', 'Ra', 'Rb']
        if not all(self.get_parameter(key) is not None and self.get_parameter(key) > 0 for key in required):
            return False, "缺少必要的幾何參數"
            
        base_nodes, mobile_nodes = self._get_6dof_nodes()
        if not base_nodes or not mobile_nodes:
            return False, "無法計算平台節點"
            
        l, s, s_buf = [self.get_parameter(key) for key in ['L', 's', 's_buffer']]
        target_leg_length = l + s_buf/2.0 + s/2.0
        
        def error_func_vec(pose_vars):
            _, mobile_nodes_world, base_nodes_internal = self._get_world_geometry_from_pose_vec(pose_vars)
            if not base_nodes_internal: return [1e6] * 6
            return [np.linalg.norm(mobile_nodes_world[i] - np.array(base_nodes_internal[i]))**2 - target_leg_length**2 for i in range(len(base_nodes_internal))]

        # [修改 - v2.3 共識 #9] 初始猜測的 Yaw (索引 5) 應使用輸入的 phase_angle
        zero_yaw_rad = np.deg2rad(self.params.get('phase_angle_deg', 0.0))
        initial_guess = np.array([0, 0, l + s/2.0, 0, 0, zero_yaw_rad]) 
        status_message = ""

        scale_factor = self.get_parameter('Ra')
        if not scale_factor or scale_factor <= 0: scale_factor = 100.0

        def scale_pose(pose, factor, down=True):
            scaled = pose.copy()
            if down: scaled[:3] /= factor
            else: scaled[:3] *= factor
            return scaled
        
        # [緊急修正 - v2.3] 計算 H (零位) 是一個幾何定義問題，不應受物理約束 (如腿長、角度) 限制。
        result = least_squares(error_func_vec, initial_guess, method='lm', ftol=config.GEOMETRY_SOLVER_TOLERANCE)
        
        if not result.success:
            # 嘗試使用 minimize 作為後備方案 (無約束)
            error_func_sq = lambda pose_vars: np.sum(np.square(error_func_vec(pose_vars)))
            # 使用與 least_squares 相同的縮放邏輯
            scaled_error_func = lambda scaled_vars: error_func_sq(scale_pose(scaled_vars, scale_factor, down=False))
            scaled_initial = scale_pose(initial_guess, scale_factor, down=True)
            
            res_min = minimize(scaled_error_func, scaled_initial, method='SLSQP', tol=config.GEOMETRY_SOLVER_TOLERANCE)
            
            if res_min.success and res_min.fun < 1e-6:
                solved_pose = scale_pose(res_min.x, scale_factor, down=False)
                status_message = "計算成功 (使用後備優化器)"
            else:
                return False, "求解器無法收斂以找到幾何零位 (H)。請檢查幾何參數是否合理。"
        else:
            solved_pose = result.x
            status_message = "計算成功"

        self.update_parameter('H', solved_pose[2])
        self.zero_pose_offset = {'x': solved_pose[0], 'y': solved_pose[1]}
        
        r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(solved_pose)
        base_cos, plat_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
        self.zero_pose_base_angle = np.rad2deg(np.max(np.arccos(base_cos)))
        self.zero_pose_platform_angle = np.rad2deg(np.max(np.arccos(plat_cos)))
        return True, status_message

    def _get_6dof_nodes(self):
        base_nodes, mobile_nodes = [], []
        Ra, Df, df = self.get_parameter('Ra'), self.get_parameter('Df'), self.get_parameter('df')
        Rb, Dm, dm = self.get_parameter('Rb'), self.get_parameter('Dm'), self.get_parameter('dm')

        if not all([Ra, Df, df, Rb, Dm, dm]) or Ra <= 0 or Rb <= 0:
            return [], []

        if Df < df: Df, df = df, Df
        if Dm < dm: Dm, dm = dm, Dm
        
        try:
            if Df/(2*Ra) > 1.0 or df/(2*Ra) > 1.0 or Dm/(2*Rb) > 1.0 or dm/(2*Rb) > 1.0:
                if any(v > 1.000001 for v in [Df/(2*Ra), df/(2*Ra), Dm/(2*Rb), dm/(2*Rb)]):
                    print("警告: 弦長大於 2*R，無法計算節點。")
                    return [], []
            
            ratio_f_d = min(1.0, Df / (2.0 * Ra))
            ratio_f_s = min(1.0, df / (2.0 * Ra))
            ratio_m_d = min(1.0, Dm / (2.0 * Rb))
            ratio_m_s = min(1.0, dm / (2.0 * Rb))

            alpha_f = 2.0 * np.arcsin(ratio_f_d)
            beta_f = 2.0 * np.arcsin(ratio_f_s)
            
            angles_base_raw = [
                0.0,
                beta_f,
                beta_f + alpha_f,
                beta_f + alpha_f + beta_f,
                beta_f + alpha_f + beta_f + alpha_f,
                beta_f + alpha_f + beta_f + alpha_f + beta_f
            ]
            rot_offset_base = - (angles_base_raw[5] - np.pi) / 2.0
            angles_base = [a + rot_offset_base for a in angles_base_raw]
            base_nodes = [[Ra*np.cos(a), Ra*np.sin(a), 0] for a in angles_base]

            alpha_m = 2.0 * np.arcsin(ratio_m_d)
            beta_m = 2.0 * np.arcsin(ratio_m_s)
            
            angles_mobile_raw = [
                0.0,
                alpha_m,
                alpha_m + beta_m,
                alpha_m + beta_m + alpha_m,
                alpha_m + beta_m + alpha_m + beta_m,
                alpha_m + beta_m + alpha_m + beta_m + alpha_m
            ]
            
            rot_offset_mobile = - (angles_mobile_raw[5] - np.pi) / 2.0
            
            # [v2.3] 使用者輸入的 'phase_angle_deg' (θ) 將在 _get_world_geometry_from_pose_vec 中被應用
            # 此處僅計算幾何形狀，不包含 Yaw 旋轉
            angles_mobile = [a + rot_offset_mobile for a in angles_mobile_raw]
            mobile_nodes = [[Rb*np.cos(a), Rb*np.sin(a), 0] for a in angles_mobile]
            
        except (ValueError, TypeError, ZeroDivisionError) as e: 
            print(f"計算 6-DOF 節點時發生錯誤: {e}")
            return [], []
            
        return base_nodes, mobile_nodes
        
    def _find_limit(self, dof_index: int, direction: int, neutral_pose: np.ndarray, space_type: str):
        
        # 1. 建立縮放向量 (Scale Vector)
        scale_factor_pos = float(self.get_parameter('Ra')) if self.get_parameter('Ra') else 100.0
        # [強制修正] 強制角度縮放因子為 1.0
        scale_factor_ang = 1.0 
        
        if self.platform_type == '6-DOF':
            scale_vector = np.array([
                scale_factor_pos, scale_factor_pos, scale_factor_pos, 
                scale_factor_ang, scale_factor_ang, scale_factor_ang  
            ], dtype=float)
        else: 
            scale_vector = np.array([
                scale_factor_pos, 
                scale_factor_ang, 
                scale_factor_ang 
            ], dtype=float)

        # 2. 建立正規化/還原函數
        def scale_pose(pose, s_vec, down=True):
            if down:
                return np.divide(pose, s_vec)
            else:
                return np.multiply(pose, s_vec)

        # 3. 目標函數
        scaled_objective = lambda scaled_pose_vars: -direction * scaled_pose_vars[dof_index]

        # 4. 約束函數
        def make_scaled_constraint_func(original_func, s_vec):
            return lambda scaled_vars: original_func(scale_pose(scaled_vars, s_vec, down=False))

        constraints = self._create_workspace_constraints(space_type)
        scaled_constraints = [{'type': c['type'], 'fun': make_scaled_constraint_func(c['fun'], scale_vector)} for c in constraints]
        
        # 5. 邊界和起始點
        var_bounds = self._get_workspace_variable_bounds(neutral_pose)
        scaled_bounds = Bounds(
            lb=scale_pose(var_bounds.lb, scale_vector, down=True),
            ub=scale_pose(var_bounds.ub, scale_vector, down=True)
        )
        scaled_x0 = scale_pose(neutral_pose, scale_vector, down=True)

        # [診斷] 輸出關鍵除錯資訊
        if dof_index >= 3: 
             print(f"[DIAGNOSTIC _find_limit] DOF Index: {dof_index}, Direction: {direction}")
             print(f"[DIAGNOSTIC _find_limit] Scale Vector: {scale_vector}")
             print(f"[DIAGNOSTIC _find_limit] Scaled Bounds LB: {scaled_bounds.lb}")
             print(f"[DIAGNOSTIC _find_limit] Scaled Bounds UB: {scaled_bounds.ub}")
             print(f"[DIAGNOSTIC _find_limit] Scaled X0: {scaled_x0}")

        # 6. 執行求解器
        result = minimize(scaled_objective, x0=scaled_x0, method='SLSQP', constraints=scaled_constraints, bounds=scaled_bounds, 
                          options={'ftol': config.WORKSPACE_SOLVER_TOLERANCE, 'disp': False})

        print(f"[DIAGNOSTIC] Solver Success: {result.success}, Msg: {result.message}")
        print(f"[DIAGNOSTIC] Raw Solver Output (Scaled): {result.x}")

        if result.success:
            print(f"[DIAGNOSTIC] Scale Vector used for unscaling: {scale_vector}")
            
            final_pose = scale_pose(result.x, scale_vector, down=False)
            print(f"[DIAGNOSTIC] Final Pose (Unscaled): {final_pose}")
            
            val = final_pose[dof_index]
            print(f"[DIAGNOSTIC] Returning Value: {val}")
            return val
        else:
            return neutral_pose[dof_index]

    def _create_workspace_constraints(self, space_type: str):
        L, s, s_buf, s_mech = [self.get_parameter(key) for key in ['L', 's', 's_buffer', 's_mech']]
        leg_min, leg_max = (L + s_buf/2.0, L + s_buf/2.0 + s) if space_type == 'operational' else (L, L + s_mech)
        base_limit, plat_limit = self.get_parameter('base_joint_limit'), self.get_parameter('platform_joint_limit')
        enable_angle_limits = self.get_parameter('enable_joint_limits')
        
        constraints = []
        
        num_legs = len(self._get_canonical_nodes()[0])
        if num_legs == 0: return []

        def make_len_func(leg_idx, is_min):
            def len_constraint(pose):
                _r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(pose)
                if not base_nodes: return -1.0
                length = np.linalg.norm(mobile_nodes_world[leg_idx] - base_nodes[leg_idx])
                return (length - leg_min) if is_min else (leg_max - length)
            return len_constraint

        for i in range(num_legs):
            constraints.append({'type': 'ineq', 'fun': make_len_func(i, True)})
            constraints.append({'type': 'ineq', 'fun': make_len_func(i, False)})

        if enable_angle_limits:
            def make_angle_func(leg_idx, is_base):
                def constraint_func(pose):
                    r_matrix, mobile_nodes_world, base_nodes_internal = self._get_world_geometry_from_pose_vec(pose)
                    if not base_nodes_internal: return -1.0

                    cos_angles = self._calculate_joint_angles(r_matrix, np.array(base_nodes_internal), mobile_nodes_world)
                    angle_cos = cos_angles[0 if is_base else 1][leg_idx]
                    limit_cos = np.cos(base_limit if is_base else plat_limit)
                    return angle_cos - limit_cos
                return constraint_func

            if base_limit > 1e-9:
                for i in range(num_legs):
                    constraints.append({'type': 'ineq', 'fun': make_angle_func(i, True)})
            if plat_limit > 1e-9:
                for i in range(num_legs):
                    constraints.append({'type': 'ineq', 'fun': make_angle_func(i, False)})          
        return constraints

    def _get_workspace_variable_bounds(self, neutral_pose):
        s_mech, Ra, L_val = self.get_parameter('s_mech') or 0, self.get_parameter('Ra') or 0, self.get_parameter('L') or 0
        
        # [修正 - v2.3] 將角度邊界從 +/- pi 收緊至 +/- 85 度 (約 1.48 rad)
        LIMIT_ANG_RAD = np.deg2rad(85.0) 
        
        if self.platform_type == '6-DOF':
            H, x0, y0 = neutral_pose[2], neutral_pose[0], neutral_pose[1]
            max_travel = Ra + L_val + s_mech
            
            lb = [x0-max_travel, y0-max_travel, 0, -LIMIT_ANG_RAD, -LIMIT_ANG_RAD, -LIMIT_ANG_RAD]
            ub = [x0+max_travel, y0+max_travel, max_travel, LIMIT_ANG_RAD, LIMIT_ANG_RAD, LIMIT_ANG_RAD]
            return Bounds(lb, ub)
        else:
            H = neutral_pose[0]; max_travel = H + s_mech
            return Bounds([0, -LIMIT_ANG_RAD, -LIMIT_ANG_RAD], [max_travel, LIMIT_ANG_RAD, LIMIT_ANG_RAD])

    def _analyze_workspace_6dof(self, space_type):
        H, offset = self.get_parameter('H'), self.zero_pose_offset
        if not H or H <= 0: return (False, None)
        
        # [修改 - v2.3] 'neutral_pose' 的 Yaw 使用輸入的 'phase_angle_deg'
        zero_yaw_rad = np.deg2rad(self.params.get('phase_angle_deg', 0.0))
        neutral_pose = np.array([offset['x'], offset['y'], H, 0, 0, zero_yaw_rad])
        
        if self.get_parameter('enable_joint_limits'):
            feasible_pose = self._find_feasible_initial_pose(neutral_pose, space_type)
            if feasible_pose is None: return (False, "NO_FEASIBLE_START")
            neutral_pose = feasible_pose
        
        print("\n" + "="*20 + " DIAGNOSTIC: STARTING WORKSPACE ANALYSIS " + "="*20)
        print(f"DIAGNOSTIC: Analyzing '{space_type}' workspace.")
        print(f"DIAGNOSTIC: Neutral pose for analysis (X,Y,Z,P,R,Y_rad): {neutral_pose}")
        print("="*70 + "\n")
        
        dof_names = ['x', 'y', 'z', 'pitch', 'roll', 'yaw']; limits = {}
        for i, name in enumerate(dof_names):
            min_val = self._find_limit(i, -1, neutral_pose, space_type)
            max_val = self._find_limit(i, 1, neutral_pose, space_type)
            
            limits[f"{name}_min"] = min_val
            limits[f"{name}_max"] = max_val
            
        return (True, limits)

    def _analyze_workspace_3dof(self, space_type):
        if not self.get_parameter('H'): return (False, None)
        H0 = self.get_parameter('H'); neutral_pose = np.array([H0, 0, 0])
        if self.get_parameter('enable_joint_limits'):
            feasible_pose = self._find_feasible_initial_pose(neutral_pose, space_type)
            if feasible_pose is None: return (False, "NO_FEASIBLE_START")
            neutral_pose = feasible_pose
        dof_names = ['z', 'pitch', 'roll']; limits = {}
        for i, name in enumerate(dof_names):
            min_val_abs = self._find_limit(i, -1, neutral_pose, space_type)
            max_val_abs = self._find_limit(i, 1, neutral_pose, space_type)
            
            # [修正 - v2.3] 這裡直接回傳絕對座標，不再減去 H0。
            # 因為 analysis_widget.py 已經會執行 (min_abs - h_val) 的運算。
            if i==0: 
                limits[f"{name}_min"],limits[f"{name}_max"] = min_val_abs, max_val_abs
            else: 
                limits[f"{name}_min"],limits[f"{name}_max"] = min_val_abs, max_val_abs
        return (True, limits)

    def _find_feasible_initial_pose(self, neutral_pose, space_type):
        constraints = self._create_workspace_constraints(space_type)
        if not constraints: return neutral_pose
        def violation_func(pose_m_rad):
            violations = [min(0, const['fun'](pose_m_rad)) for const in constraints]
            return np.sum(np.square(violations))
        var_bounds = self._get_workspace_variable_bounds(neutral_pose)
        result = minimize(violation_func, neutral_pose, method='SLSQP', bounds=var_bounds, tol=1e-8)
        if result.success and result.fun < 1e-6: return result.x
        else: return None

    def analyze_operational_workspace(self):
        return self._analyze_workspace_6dof('operational') if self.platform_type == '6-DOF' else self._analyze_workspace_3dof('operational')

    def analyze_mechanical_workspace(self):
        return self._analyze_workspace_6dof('mechanical') if self.platform_type == '6-DOF' else self._analyze_workspace_3dof('mechanical')

    def _calculate_geometry_3dof(self):
        required = ['L', 's', 's_buffer', 'D1', 'D2', 'd1', 'd2']
        if not all(self.get_parameter(key) is not None for key in required): return False
        
        l, s, s_buf = [self.get_parameter(key) for key in ['L', 's', 's_buffer']]
        target_leg_length = l + s_buf/2.0 + s/2.0
        def objective_func(H_var):
            pose_vec = np.array([H_var[0], 0, 0])
            _, mobile_nodes_world, base_nodes_internal = self._get_world_geometry_from_pose_vec(pose_vec)
            if not base_nodes_internal: return 1e12
            errors = [np.linalg.norm(mobile_nodes_world[i] - np.array(base_nodes_internal[i]))**2 - target_leg_length**2 for i in range(len(base_nodes_internal))]
            return np.sum(np.array(errors)**2)
        
        # [修正 - v2.3] 3-DOF 同樣移除約束，僅求解幾何零位
        result = minimize(objective_func, [l + s/2.0], method='SLSQP', bounds=[(0, None)], tol=config.GEOMETRY_SOLVER_TOLERANCE)
        if result.success and result.fun < 1e-6:
            solved_h = result.x[0]
            self.update_parameter('H', solved_h); self.zero_pose_offset = {'x': 0.0, 'y': 0.0}
            r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(np.array([solved_h, 0, 0]))
            base_cos, plat_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
            self.zero_pose_base_angle = np.rad2deg(np.max(np.arccos(base_cos)))
            self.zero_pose_platform_angle = np.rad2deg(np.max(np.arccos(plat_cos)))
            return True
        return False

    def _get_3dof_nodes(self):
        base_nodes, mobile_nodes = [], []
        D1, D2 = self.get_parameter('D1'), self.get_parameter('D2')
        if D1 and D2 and D1 > 0 and D2 > 0:
            base_nodes = [
                [-D1/2.0, -D2/3.0, 0.0], # A1
                [0.0, 2.0*D2/3.0, 0.0],      # A3
                [D1/2.0, -D2/3.0, 0.0]  # A5
            ]
        d1, d2 = self.get_parameter('d1'), self.get_parameter('d2')
        if d1 and d2 and d1 > 0 and d2 > 0:
            mobile_nodes = [
                [-d1/2.0, -d2/3.0, 0.0], # B1
                [0.0, 2.0*d2/3.0, 0.0],      # B3
                [d1/2.0, -d2/3.0, 0.0]  # B5
            ]
        return base_nodes, mobile_nodes
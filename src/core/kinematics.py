# D:\Python_Programs\Stewart_Platform\src\core\kinematics.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# UI層、核心層的所有長度參數的儲存、傳遞與計算皆以 mm 為準。
# 詳情請參閱《基礎背景與規則 v5 優化版.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

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
        # [v2.3 註記] 移除 v13.5 等易混淆的內部版本號
        print("核心計算引擎 (CoreEngine) 已初始化。")
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
        
        # [新增 - v2.3 共識 #8] 新增 6-DOF 輸入相位角參數
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
        # [刪除 - v2.3 共識 #11] 移除 3-DOF 對 'Ra' 和 'Rb' 的過時註冊
        # self.formulas.append({'output': 'Ra', 'inputs': ['D1', 'D2'], 'func': self._calculate_radius_from_3dof_triangle, 'type': '3-DOF'})
        # self.formulas.append({'output': 'Rb', 'inputs': ['d1', 'd2'], 'func': self._calculate_radius_from_3dof_triangle, 'type': '3-DOF'})
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

    # [刪除 - v2.3 共識 #3, #11] 移除 3-DOF 過時的半徑計算函式
    # def _calculate_radius_from_3dof_triangle(self, p):
    #     ...

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

    # [刪除 - v2.3 共識 #8, #11] 移除錯誤的 'stagger' 計算函式
    # def get_phase_angle_deg(self) -> float | None:
    #     ...
    
    def _get_3dof_nodes(self):
        base_nodes, mobile_nodes = [], []
        D1, D2 = self.get_parameter('D1'), self.get_parameter('D2')
        if D1 and D2 and D1 > 0 and D2 > 0:
            base_nodes = [
                [-D1/2.0, -D2/3.0, 0.0], # A1 (Index 0)
                [0.0, 2.0*D2/3.0, 0.0],      # A3 (Index 1)
                [D1/2.0, -D2/3.0, 0.0]  # A5 (Index 2)
            ]
        d1, d2 = self.get_parameter('d1'), self.get_parameter('d2')
        if d1 and d2 and d1 > 0 and d2 > 0:
            mobile_nodes = [
                [-d1/2.0, -d2/3.0, 0.0], # B1 (Index 0)
                [0.0, 2.0*d2/3.0, 0.0],      # B3 (Index 1)
                [d1/2.0, -d2/3.0, 0.0]  # B5 (Index 2)
            ]
        return base_nodes, mobile_nodes

    def _calculate_geometry_3dof(self):
        # [修改 - v2.3 共識 #10] 移除 'Ra', 'Rb' 的依賴，改為依賴 v4.6 的質心參數
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
        constraints = self._create_workspace_constraints('operational') if self.get_parameter('enable_joint_limits') else []
        result = minimize(objective_func, [l + s/2.0], method='SLSQP', bounds=[(0, None)], constraints=constraints, tol=config.GEOMETRY_SOLVER_TOLERANCE)
        if result.success and result.fun < 1e-6:
            solved_h = result.x[0]
            self.update_parameter('H', solved_h); self.zero_pose_offset = {'x': 0.0, 'y': 0.0}
            r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(np.array([solved_h, 0, 0]))
            base_cos, plat_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
            self.zero_pose_base_angle = np.rad2deg(np.max(np.arccos(base_cos)))
            self.zero_pose_platform_angle = np.rad2deg(np.max(np.arccos(plat_cos)))
            return True
        return False

    def _find_feasible_pose_by_height_adjustment(self, initial_pose_vec, base_nodes, mobile_nodes_local):
        step = config.SOLVER_FEASIBILITY_SEARCH_STEP
        max_iterations = config.SOLVER_FEASIBILITY_MAX_ITERATIONS
        
        base_limit = self.get_parameter('base_joint_limit')
        platform_limit = self.get_parameter('platform_joint_limit')

        def is_current_pose_valid(pose_vec):
            r_matrix, mobile_nodes_world = self._get_world_geometry_from_pose_vec(pose_vec)[:2]
            base_cos, platform_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
            if np.any(base_cos < np.cos(base_limit)): return False
            if np.any(platform_cos < np.cos(platform_limit)): return False
            return True

        if is_current_pose_valid(initial_pose_vec):
            return initial_pose_vec, "初始姿態有效，無需調整"

        original_z = initial_pose_vec[2]
        current_pose_vec = initial_pose_vec.copy()
        for i in range(1, (max_iterations // 2) + 1):
            current_pose_vec[2] = original_z + i * step
            if is_current_pose_valid(current_pose_vec):
                adjustment_mm = i * step
                msg = (f"警告：初始姿態與關節角度限制衝突。\n\n"
                       f"系統已自動將平台高度向上微調 {adjustment_mm:.2f} mm 以完成計算。\n\n"
                       f"改善建議：若要永久消除此警告，您可以考慮：\n"
                       f"1. 微調『通用參數』中的『自然平衡零位高度 (H)』。\n"
                       f"2. 適度放寬『關節角度限制』的設定值。")
                return current_pose_vec, msg

            current_pose_vec[2] = original_z - i * step
            if is_current_pose_valid(current_pose_vec):
                adjustment_mm = i * -step
                msg = (f"警告：初始姿態與關節角度限制衝突。\n\n"
                       f"系統已自動將平台高度向下微調 {adjustment_mm:.2f} mm 以完成計算。\n\n"
                       f"改善建議：若要永久消除此警告，您可以考慮：\n"
                       f"1. 微調『通用參數』中的『自然平衡零位高度 (H)』。\n"
                       f"2. 適度放寬『關節角度限制』的設定值。")
                return current_pose_vec, msg
        
        return None, "錯誤：在調整範圍內找不到滿足角度限制的可行姿態。"

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

        def make_scaled_func(original_func, factor):
            return lambda scaled_vars: original_func(scale_pose(scaled_vars, factor, down=False))
        
        if not self.get_parameter('enable_joint_limits'):
            result = least_squares(error_func_vec, initial_guess, method='lm', ftol=config.GEOMETRY_SOLVER_TOLERANCE)
            if not result.success:
                return False, "求解器無法在無角度限制下收斂"
            solved_pose = result.x
            status_message = "計算成功 (未啟用角度限制)"
        else:
            feasible_start_point, status_message = self._find_feasible_pose_by_height_adjustment(
                initial_guess, np.array(base_nodes), np.array(mobile_nodes)
            )
            
            if feasible_start_point is None:
                return False, status_message 

            error_func_sq = lambda pose_vars: np.sum(np.square(error_func_vec(pose_vars)))
            
            scaled_error_func = make_scaled_func(error_func_sq, scale_factor)
            
            constraints = self._create_workspace_constraints('operational')
            scaled_constraints = []
            for const in constraints:
                scaled_constraints.append({
                    'type': const['type'],
                    'fun': make_scaled_func(const['fun'], scale_factor)
                })

            bounds_obj = self._get_workspace_variable_bounds(feasible_start_point)
            scaled_bounds_obj = Bounds(
                lb=scale_pose(bounds_obj.lb, scale_factor, down=True),
                ub=scale_pose(bounds_obj.ub, scale_factor, down=True)
            )
            scaled_start_point = scale_pose(feasible_start_point, scale_factor, down=True)
            
            # --- DIAGNOSTIC MODIFICATION START ---
            # [註記] 依使用者要求，加入診斷訊息以追蹤求解器失敗原因。
            print("\n" + "="*20 + " [診斷] 啟動 'minimize' 求解器 (零位計算) " + "="*20)
            print(f"[診斷] 初始猜測點 (Scaled): {scaled_start_point}")
            print(f"[診斷] 總約束條件數量: {len(scaled_constraints)}")

            # 驗證約束條件在初始點的值
            print("[診斷] 驗證初始點的約束條件 (應全部 >= 0):")
            try:
                for i, const in enumerate(constraints): # 使用未縮放的約束和點
                    const_val = const['fun'](feasible_start_point)
                    if const_val < -1e-6: # 容忍極小的負值
                        print(f"  [!! 警告 !!] 約束 {i} 在初始點為負: {const_val:.2e}")
                    # else:
                    #     print(f"  [通過] 約束 {i} 在初始點為正: {const_val:.2e}")
            except Exception as e:
                print(f"  [!! 錯誤 !!] 驗證約束條件時出錯: {e}")
            
            print("[診斷] 呼叫 'scipy.optimize.minimize' (disp=True)...")
            
            result = minimize(scaled_error_func, scaled_start_point, method='SLSQP', 
                            bounds=scaled_bounds_obj, constraints=scaled_constraints, 
                            tol=config.GEOMETRY_SOLVER_TOLERANCE, 
                            options={'disp': True}) # 啟用求解器的詳細日誌

            print(f"[診斷] 'minimize' 執行完畢。")
            print(f"[診斷] 求解器成功: {result.success}")
            print(f"[診斷] 求解器訊息: {result.message}")
            print(f"[診斷] 最終函數值 (應趨近0): {result.fun}")
            print("="*60 + "\n")
            # --- DIAGNOSTIC MODIFICATION END ---

            if not (result.success and result.fun < 1e-6):
                return False, f"求解器在有角度限制下無法收斂。\n({status_message})"
            
            solved_pose = scale_pose(result.x, scale_factor, down=False)

        self.update_parameter('H', solved_pose[2])
        self.zero_pose_offset = {'x': solved_pose[0], 'y': solved_pose[1]}
        
        r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(solved_pose)
        base_cos, plat_cos = self._calculate_joint_angles(r_matrix, base_nodes, mobile_nodes_world)
        self.zero_pose_base_angle = np.rad2deg(np.max(np.arccos(base_cos)))
        self.zero_pose_platform_angle = np.rad2deg(np.max(np.arccos(plat_cos)))
        return True, status_message

    # --- MODIFICATION START ---
    # [註記] 根據 v4.3 拓樸修正版 (6-DOF 史都華平台完整幾何參數定義 v4.3 拓樸修正版)
    # 重寫 6-DOF 節點定義，使用「角度累加法」並匹配交錯拓樸。
    def _get_6dof_nodes(self):
        base_nodes, mobile_nodes = [], []
        Ra, Df, df = self.get_parameter('Ra'), self.get_parameter('Df'), self.get_parameter('df')
        Rb, Dm, dm = self.get_parameter('Rb'), self.get_parameter('Dm'), self.get_parameter('dm')

        if not all([Ra, Df, df, Rb, Dm, dm]) or Ra <= 0 or Rb <= 0:
            return [], []

        # 確保 Df 是長弦, df 是短弦
        if Df < df: Df, df = df, Df
        # 確保 Dm 是長弦, dm 是短弦
        if Dm < dm: Dm, dm = dm, Dm
        
        try:
            # 檢查 asin 的定義域
            if Df/(2*Ra) > 1.0 or df/(2*Ra) > 1.0 or Dm/(2*Rb) > 1.0 or dm/(2*Rb) > 1.0:
                # 容忍極小的浮點數誤差
                if any(v > 1.000001 for v in [Df/(2*Ra), df/(2*Ra), Dm/(2*Rb), dm/(2*Rb)]):
                    print("警告: 弦長大於 2*R，無法計算節點。")
                    return [], []
            
            ratio_f_d = min(1.0, Df / (2.0 * Ra)) # 長
            ratio_f_s = min(1.0, df / (2.0 * Ra)) # 短
            ratio_m_d = min(1.0, Dm / (2.0 * Rb)) # 長
            ratio_m_s = min(1.0, dm / (2.0 * Rb)) # 短

            # A 平台 (固定平台) (Short-Long 拓樸)
            alpha_f = 2.0 * np.arcsin(ratio_f_d) # 長弦角
            beta_f = 2.0 * np.arcsin(ratio_f_s)  # 短弦角
            
            # 節點角度累加: [0, B, B+a, B+a+B, B+a+B+a, B+a+B+a+B]
            angles_base_raw = [
                0.0,
                beta_f,
                beta_f + alpha_f,
                beta_f + alpha_f + beta_f,
                beta_f + alpha_f + beta_f + alpha_f,
                beta_f + alpha_f + beta_f + alpha_f + beta_f
            ]
            # 旋轉偏移以匹配標準方位 (A1/A6 圍繞 X 軸對稱)
            rot_offset_base = - (angles_base_raw[5] - np.pi) / 2.0
            angles_base = [a + rot_offset_base for a in angles_base_raw]
            base_nodes = [[Ra*np.cos(a), Ra*np.sin(a), 0] for a in angles_base]

            # B 平台 (活動平台) (Long-Short 拓樸)
            alpha_m = 2.0 * np.arcsin(ratio_m_d) # 長弦角
            beta_m = 2.0 * np.arcsin(ratio_m_s)  # 短弦角
            
            # 節點角度累加: [0, a, a+B, a+B+a, a+B+a+B, a+B+a+B+a]
            angles_mobile_raw = [
                0.0,
                alpha_m,
                alpha_m + beta_m,
                alpha_m + beta_m + alpha_m,
                alpha_m + beta_m + alpha_m + beta_m,
                alpha_m + beta_m + alpha_m + beta_m + alpha_m
            ]
            
            # [刪除 - v2.3 共識 #7] 移除錯誤的、計算出來的 'stagger'
            # stagger = (beta_f - alpha_m) / 2.0
            
            # 旋轉偏移以匹配標準方位 (B1/B6 圍繞 X 軸對稱)
            rot_offset_mobile = - (angles_mobile_raw[5] - np.pi) / 2.0
            
            # [修改 - v2.3 共識 #7] 移除 stagger 的應用
            # 註：使用者輸入的 'phase_angle_deg' (θ) 將在 _get_world_geometry_from_pose_vec 中被應用
            angles_mobile = [a + rot_offset_mobile for a in angles_mobile_raw]
            mobile_nodes = [[Rb*np.cos(a), Rb*np.sin(a), 0] for a in angles_mobile]
            
        except (ValueError, TypeError, ZeroDivisionError) as e: 
            print(f"計算 6-DOF 節點時發生錯誤: {e}")
            return [], []
            
        return base_nodes, mobile_nodes
    # --- MODIFICATION END ---
        
    # --- MODIFICATION START ---
    # [註記] 徹底重寫此方法以修正「變數正規化(Scaling)」的根本性缺陷。
    # 舊版僅縮放 pose[:3]，導致求解器在混合尺度 (mm vs rad) 下運算，
    # 從而產生 Surge 單邊範圍和角度範圍巨大的錯誤。
    # 新版使用 scale_vector 確保所有自由度都被一致地正規化。
    def _find_limit(self, dof_index: int, direction: int, neutral_pose: np.ndarray, space_type: str):
        
        # 1. 建立縮放向量 (Scale Vector)
        scale_factor_pos = self.get_parameter('Ra')
        if not scale_factor_pos or scale_factor_pos <= 0: scale_factor_pos = 100.0
        # 角度已經在 [-pi, pi] 範圍，無需縮放，故因子為 1.0
        scale_factor_ang = 1.0 
        
        if self.platform_type == '6-DOF':
            scale_vector = np.array([
                scale_factor_pos, scale_factor_pos, scale_factor_pos, # X, Y, Z
                scale_factor_ang, scale_factor_ang, scale_factor_ang  # Pitch, Roll, Yaw
            ])
        else: # 3-DOF
            scale_vector = np.array([
                scale_factor_pos, # Z
                scale_factor_ang, # Pitch
                scale_factor_ang  # Roll
            ])

        # 2. 建立正規化/還原函數
        def scale_pose(pose, s_vec, down=True):
            """使用 scale_vector 進行元素對應縮放。"""
            if down:
                return np.divide(pose, s_vec) # 元素對應相除 (正規化)
            else:
                return np.multiply(pose, s_vec) # 元素對應相乘 (還原)

        # 3. 目標函數必須在「縮放後」的空間中運作
        scaled_objective = lambda scaled_pose_vars: -direction * scaled_pose_vars[dof_index]

        # 4. 約束函數的封裝器，必須「還原」縮放，在真實物理空間中計算
        def make_scaled_constraint_func(original_func, s_vec):
            return lambda scaled_vars: original_func(scale_pose(scaled_vars, s_vec, down=False)) # 還原

        constraints = self._create_workspace_constraints(space_type)
        scaled_constraints = [{'type': c['type'], 'fun': make_scaled_constraint_func(c['fun'], scale_vector)} for c in constraints]
        
        # 5. 邊界和起始點也必須被縮放
        var_bounds = self._get_workspace_variable_bounds(neutral_pose)
        scaled_bounds = Bounds(
            lb=scale_pose(var_bounds.lb, scale_vector, down=True),
            ub=scale_pose(var_bounds.ub, scale_vector, down=True)
        )
        scaled_x0 = scale_pose(neutral_pose, scale_vector, down=True)

        # 6. 執行求解器
        result = minimize(scaled_objective, x0=scaled_x0, method='SLSQP', constraints=scaled_constraints, bounds=scaled_bounds, 
                          options={'ftol': config.WORKSPACE_SOLVER_TOLERANCE, 'disp': False})

        if result.success:
            # 7. 將結果「還原」回真實的物理單位 (mm / rad)
            final_pose = scale_pose(result.x, scale_vector, down=False)
            return final_pose[dof_index]
        else:
            # 若求解失敗，返回中立點的值作為後備
            return neutral_pose[dof_index]
    # --- MODIFICATION END ---

    # --- MODIFICATION START ---
    # [註記] 徹底重構此方法，使其內部所有約束函數都變得獨立、自給自足，
    # 透過統一呼叫 _get_world_geometry_from_pose_vec 來獲取所有同步的幾何數據，
    # 以根除「預檢」和「正式求解」之間的邏輯不一致問題。
    def _create_workspace_constraints(self, space_type: str):
        L, s, s_buf, s_mech = [self.get_parameter(key) for key in ['L', 's', 's_buffer', 's_mech']]
        leg_min, leg_max = (L + s_buf/2.0, L + s_buf/2.0 + s) if space_type == 'operational' else (L, L + s_mech)
        base_limit, plat_limit = self.get_parameter('base_joint_limit'), self.get_parameter('platform_joint_limit')
        enable_angle_limits = self.get_parameter('enable_joint_limits')
        
        constraints = []
        
        # 由於約束函數在內部會重新計算節點，我們只需要在這裡確定腿的數量
        num_legs = len(self._get_canonical_nodes()[0])
        if num_legs == 0: 
            return [] # 如果還沒有幾何參數，直接返回空列表

        # --- 腿長限制條件 (重構為更穩定、清晰的輔助函數) ---
        def make_len_func(leg_idx, is_min):
            def len_constraint(pose):
                # 每次都從 pose 重新計算所有幾何資訊
                _r_matrix, mobile_nodes_world, base_nodes = self._get_world_geometry_from_pose_vec(pose)
                if not base_nodes: return -1.0 # 幾何無效時返回一個負值 (違反約束)
                length = np.linalg.norm(mobile_nodes_world[leg_idx] - base_nodes[leg_idx])
                return (length - leg_min) if is_min else (leg_max - length)
            return len_constraint

        for i in range(num_legs):
            constraints.append({'type': 'ineq', 'fun': make_len_func(i, True)})
            constraints.append({'type': 'ineq', 'fun': make_len_func(i, False)})

        # --- 角度限制條件 (重構) ---
        if enable_angle_limits:
            def make_angle_func(leg_idx, is_base):
                def constraint_func(pose):
                    # 1. 每次計算時，都從 pose 重新取得完整的幾何資訊
                    r_matrix, mobile_nodes_world, base_nodes_internal = self._get_world_geometry_from_pose_vec(pose)
                    if not base_nodes_internal: return -1.0 # 幾何無效時返回一個負值 (違反約束)

                    # 2. 以正確順序呼叫角度計算函數
                    cos_angles = self._calculate_joint_angles(r_matrix, np.array(base_nodes_internal), mobile_nodes_world)
                    
                    # 3. 選取正確的關節角度並計算限制
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
    # --- MODIFICATION END ---


    def _get_workspace_variable_bounds(self, neutral_pose):
        s_mech, Ra, L_val = self.get_parameter('s_mech') or 0, self.get_parameter('Ra') or 0, self.get_parameter('L') or 0
        if self.platform_type == '6-DOF':
            H, x0, y0 = neutral_pose[2], neutral_pose[0], neutral_pose[1]
            max_travel = Ra + L_val + s_mech
            lb = [x0-max_travel, y0-max_travel, 0, -np.pi, -np.pi, -np.pi]
            ub = [x0+max_travel, y0+max_travel, max_travel, np.pi, np.pi, np.pi]
            return Bounds(lb, ub)
        else:
            H = neutral_pose[0]; max_travel = H + s_mech
            return Bounds([0, -np.pi, -np.pi], [max_travel, np.pi, np.pi])

    def _analyze_workspace_6dof(self, space_type):
        H, offset = self.get_parameter('H'), self.zero_pose_offset
        if not H or H <= 0: return (False, None)
        
        # --- MODIFICATION START ---
        # [修改 - v2.3 共識 #9] 
        # 'neutral_pose' (分析起始點) 的 Yaw (索引 5) 應使用輸入的 'phase_angle_deg'
        zero_yaw_rad = np.deg2rad(self.params.get('phase_angle_deg', 0.0))
        neutral_pose = np.array([offset['x'], offset['y'], H, 0, 0, zero_yaw_rad])
        # --- MODIFICATION END ---
        
        if self.get_parameter('enable_joint_limits'):
            feasible_pose = self._find_feasible_initial_pose(neutral_pose, space_type)
            if feasible_pose is None: return (False, "NO_FEASIBLE_START")
            neutral_pose = feasible_pose
        
        # --- START DIAGNOSTIC PRINTS ---
        print("\n" + "="*20 + " DIAGNOSTIC: STARTING WORKSPACE ANALYSIS " + "="*20)
        print(f"DIAGNOSTIC: Analyzing '{space_type}' workspace.")
        print(f"DIAGNOSTIC: Neutral pose for analysis (X,Y,Z,P,R,Y_rad): {neutral_pose}")
        print("="*70 + "\n")
        # --- END DIAGNOSTIC PRINTS ---
        
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
            if i==0: # Z-Position, relative to H0
                # [v2.3 註記] 3-DOF 的 Z 軸是絕對位置，需減去 H0 得到相對值
                limits[f"{name}_min"],limits[f"{name}_max"] = (min_val_abs-H0), (max_val_abs-H0)
            else: # Orientation
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

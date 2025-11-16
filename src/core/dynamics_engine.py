# D:\Python_Programs\Stewart_Platform\src\core\dynamics_engine.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 本檔案遵循「核心層 (mm)」的單位原則，但為了計算標準物理單位 (N, Nm)，
# 內部會進行局部的 mm -> m 轉換。
# 詳情請參閱《基礎背景與規則.v5.md》。
#「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

import numpy as np
from scipy.spatial.transform import Rotation
from src.core import config

class DynamicsEngine:
    """
    負責處理史都華平台的逆動力學計算。
    輸入：平台几何、負載參數、期望運動狀態（加速度）。
    輸出：各電動缸所需的瞬時推力/拉力。
    """
    def __init__(self):
        # --- MODIFIED: Update comment to reflect new unit in config ---
        self.g = np.array([0, 0, -config.G_ACCELERATION]) # 重力加速度向量 (mm/s^2)
        print("動力學計算引擎 (DynamicsEngine) v1.1 (通用版) 已初始化。")

    def calculate_actuator_forces(self, platform_params: dict, dynamics_params: dict) -> list[float] | None:
        """
        逆動力學求解器的主要入口。

        Args:
            platform_params: 包含平台幾何資訊的字典 (由 CoreEngine 提供, 單位: mm)。
            dynamics_params: 包含負載和運動資訊的字典 (單位: mm/s^2)。

        Returns:
            一個包含各電動缸所需力的列表 (牛頓)，正值為推力，負值為拉力。
            如果計算失敗則返回 None。
        """
        
        base_nodes = platform_params.get('nodes_3d_base')
        mobile_nodes_world = platform_params.get('nodes_3d_mobile_world')
        
        if base_nodes is None or mobile_nodes_world is None or len(base_nodes) == 0:
            return None
        
        num_actuators = len(base_nodes)

        # --- MODIFIED: Renamed variables to align with v2.0 ---
        m_p = dynamics_params.get('m_p', 200.0)
        m_l = dynamics_params.get('m_l', 0.0)
        
        load_com_local = np.array([
            dynamics_params.get('com_l_x', 0.0),
            dynamics_params.get('com_l_y', 0.0),
            dynamics_params.get('com_l_z', 700.0)
        ])
        
        a_lin = np.array(dynamics_params.get('a_lin', [0,0,0]))
        a_ang = np.array(dynamics_params.get('a_ang', [0,0,0]))
        
        R = Rotation.from_quat(platform_params.get('orientation_quat', [0,0,0,1])).as_matrix()
        T = np.array(platform_params.get('position', [0,0,0]))

        m_total = m_p + m_l
        
        platform_com_world = T
        load_com_world = T + R @ load_com_local
        
        total_com_world = (m_p * platform_com_world + m_l * load_com_world) / m_total if m_total > 0 else T

        leg_vectors = mobile_nodes_world - np.array(base_nodes)
        leg_unit_vectors = leg_vectors / np.linalg.norm(leg_vectors, axis=1)[:, np.newaxis]
        
        r_vectors = mobile_nodes_world - total_com_world
        
        # --- MODIFIED: Convert r_vectors to meters for wrench matrix calculation ---
        r_vectors_m = r_vectors / 1000.0
        
        wrench_matrix = np.zeros((6, num_actuators))
        for i in range(num_actuators):
            wrench_matrix[:3, i] = leg_unit_vectors[i]
            # Use meter-based vector for cross product to get torque arm in meters
            wrench_matrix[3:, i] = np.cross(r_vectors_m[i], leg_unit_vectors[i])

        try:
            if num_actuators == 6:
                J_inv_T = np.linalg.inv(wrench_matrix.T)
                actuator_forces_callable = lambda wrench: J_inv_T @ (-wrench)
            else:
                J_pseudo_inv = np.linalg.pinv(wrench_matrix)
                actuator_forces_callable = lambda wrench: J_pseudo_inv @ (-wrench)

        except np.linalg.LinAlgError:
            print("錯誤：雅可比矩陣奇異，無法求解。")
            return None

        # --- MODIFIED: Local conversions to get Force in N and Torque in Nm ---
        # Convert gravitational force from kg*mm/s^2 to N (kg*m/s^2)
        force_g = (m_total * self.g) / 1000.0
        
        # Convert CoM to meters before calculating torque
        total_com_world_m = total_com_world / 1000.0
        torque_g = np.cross(total_com_world_m, force_g)
        
        # Inertia tensor is approximated based on a meter scale
        I_total_approx = np.eye(3) * config.DYN_INERTIA_APPROX_SCALAR
        
        # --- MODIFIED: Use new v2.0 variable names ---
        # Convert inertial force from kg*mm/s^2 to N (kg*m/s^2)
        force_inertia = (-m_total * a_lin) / 1000.0
        
        # Inertial torque calculation remains the same as a_ang is in rad/s^2 and I is in kg*m^2
        torque_inertia = -(I_total_approx @ a_ang)
        
        total_wrench = np.concatenate([
            force_g + force_inertia,
            torque_g + torque_inertia
        ])

        actuator_forces = actuator_forces_callable(total_wrench)

        return actuator_forces.tolist()
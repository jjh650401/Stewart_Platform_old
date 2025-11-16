# D:\Python_Programs\Stewart_Platform\src\core\analysis_engine.py

import numpy as np
import itertools
from scipy.optimize import minimize, Bounds
from scipy.stats.qmc import LatinHypercube
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import time

from src.core.kinematics import CoreEngine 
from src.core import config

class AnalysisEngine(QObject):
    """
    一個完全獨立的分析工作者，設計為在自己的執行緒中執行。
    它不持有任何屬於主執行緒的物件引用。
    """
    progress_updated = pyqtSignal(int, int, str)
    analysis_finished = pyqtSignal(dict)
    angle_analysis_completed = pyqtSignal(dict)
    # [新增] 為工作空間分析新增專用的完成信號
    workspace_analysis_finished = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._is_running = False
        print("分析引擎 (AnalysisEngine) v4.0 (整合工作空間分析) 已初始化。")

    @pyqtSlot(dict)
    def run_workspace_analysis(self, task_data: dict):
        """
        [新增] 接收任務包並在背景執行緒中執行工作空間分析。
        """
        if self._is_running:
            return

        self._is_running = True
        start_time = time.time()
        print("\n" + "="*50)
        print("[偵錯] AnalysisEngine: run_workspace_analysis 已被呼叫，分析開始。")

        try:
            core_params = task_data.get('core_params')
            platform_type = task_data.get('platform_type')
            space_type = task_data.get('space_type')

            if not all([core_params, platform_type, space_type]):
                raise ValueError("任務資料不完整，缺少 core_params, platform_type 或 space_type。")

            local_core_engine = CoreEngine()
            local_core_engine.platform_type = platform_type
            # 核心引擎現在持有自己的參數字典副本，因此可以直接載入
            local_core_engine.params = core_params

            def progress_callback(value, total, msg):
                # 檢查停止旗標，如果被設定，則透過拋出例外來中斷冗長的迴圈
                if not self._is_running:
                    raise InterruptedError("分析已由使用者取消。")
                self.progress_updated.emit(value, total, msg)
            
            # --- MODIFICATION START ---
            # [註記] 修正 AttributeError
            # CoreEngine (kinematics.py) 中沒有 'analyze_workspace' 方法。
            # 必須根據 space_type 呼叫正確的特定方法。
            # 同時移除 progress_callback，因為目標方法不接受此參數。
            
            print(f"[偵錯] AnalysisEngine: 正在呼叫 {space_type} 分析...")
            if space_type == 'operational':
                success, result = local_core_engine.analyze_operational_workspace()
            elif space_type == 'mechanical':
                success, result = local_core_engine.analyze_mechanical_workspace()
            else:
                raise ValueError(f"未知的 space_type: {space_type}")
            # --- MODIFICATION END ---
            
            final_result = {'success': success, 'result': result}

        except InterruptedError as e:
            final_result = {'success': False, 'result': str(e)}
        except Exception as e:
            final_result = {'success': False, 'result': f"分析時發生未預期錯誤: {e}"}

        if self._is_running: # 只有在沒有被取消的情況下才發送信號
            self.workspace_analysis_finished.emit(final_result)
        
        self._is_running = False
        print(f"工作空間分析執行緒完成，耗時 {time.time() - start_time:.2f} 秒。")
        print("="*50 + "\n")

    @pyqtSlot(dict)
    def run_global_analysis(self, task_data: dict):
        """
        接收一個包含所有必要資料的「任務包」並開始全域出力分析。
        """
        if self._is_running:
            return

        self._is_running = True
        start_time = time.time()
        print("\n" + "="*50)
        print("[偵錯] AnalysisEngine: run_global_analysis 已被呼叫，分析開始。")
        
        local_core_engine, bounds, dof_keys = self._setup_analysis(task_data)
        if not local_core_engine:
            self._is_running = False
            return

        is_static_only = task_data.get('is_static_only', True)
        total_samples = config.ALGO_LHS_SAMPLES
        K = config.ALGO_SQP_CANDIDATES
        
        analysis_type_str = "靜態負載" if is_static_only else "動態出力"
        self.progress_updated.emit(0, total_samples + K, f"階段 1/2: 執行拉丁超立方採樣 ({analysis_type_str})...")
        
        scaled_samples = self._perform_lhs_sampling(bounds, total_samples, len(dof_keys))

        thrusts = []
        for i, pose_vec in enumerate(scaled_samples):
            if not self._is_running: break
            pose_ui_units = self._convert_pose_to_ui_units(pose_vec, dof_keys)

            if local_core_engine.is_pose_valid(pose_ui_units, 'operational'):
                dynamics_params = self._get_dynamics_params_for_analysis(local_core_engine, task_data.get('core_params'), is_static_only)
                forces = local_core_engine.calculate_force_for_ui_pose(pose_ui_units)
                if forces:
                    thrust = np.max(np.abs(forces))
                    thrusts.append((pose_vec, thrust))
            
            if (i % 50) == 0:
                self.progress_updated.emit(i + 1, total_samples + K, f"階段 1/2: 掃描點 {i+1}/{total_samples}")
        
        if not self._is_running:
            self.analysis_finished.emit({'success': False, 'message': '分析已由使用者取消。'})
            return

        if not thrusts:
            self.analysis_finished.emit({'success': False, 'message': '在拉丁超立方採樣中未能找到任何有效姿態點。'})
            self._is_running = False
            return
            
        thrusts.sort(key=lambda t: t[1], reverse=True)
        init_guesses = [t[0] for t in thrusts[:K]]
        
        def objective(x_vec):
            pose_ui_units = self._convert_pose_to_ui_units(x_vec, dof_keys)
            if not local_core_engine.is_pose_valid(pose_ui_units, 'operational'):
                return np.inf 
            dynamics_params = self._get_dynamics_params_for_analysis(local_core_engine, task_data.get('core_params'), is_static_only)
            forces = local_core_engine.calculate_force_for_ui_pose(pose_ui_units)
            if not forces:
                return np.inf
            return -np.max(np.abs(forces))

        global_max_force = thrusts[0][1]
        worst_pose_vec = thrusts[0][0]

        for i, x0 in enumerate(init_guesses):
            if not self._is_running: break
            self.progress_updated.emit(total_samples + i + 1, total_samples + K, f"階段 2/2: 精煉最佳化點 {i+1}/{K}...")
            res = minimize(objective, x0, bounds=bounds, method='SLSQP', tol=1e-7)
            
            if res.success and -res.fun > global_max_force:
                global_max_force = -res.fun
                worst_pose_vec = res.x
        
        if not self._is_running:
            self.analysis_finished.emit({'success': False, 'message': '分析已由使用者取消。'})
            return

        worst_pose_ui_units = self._convert_pose_to_ui_units(worst_pose_vec, dof_keys)
        final_dynamics_params = self._get_dynamics_params_for_analysis(local_core_engine, task_data.get('core_params'), is_static_only)
        final_forces = local_core_engine.calculate_force_for_ui_pose(worst_pose_ui_units)

        result = {
            'success': True,
            'forces': final_forces,
            'pose_ui': worst_pose_ui_units,
            'message': f"LHS+SQP ({analysis_type_str}) 分析完成。"
        }
        self.analysis_finished.emit(result)
        self._is_running = False
        print(f"全域出力分析完成，耗時 {time.time() - start_time:.2f} 秒。")
        print("="*50 + "\n")

    @pyqtSlot(dict)
    def run_angle_range_analysis(self, task_data: dict):
        if self._is_running:
            return

        self._is_running = True
        start_time = time.time()
        print("\n" + "="*50)
        print("[偵錯] AnalysisEngine: run_angle_range_analysis 已被呼叫，分析開始。")

        local_core_engine, bounds, dof_keys = self._setup_analysis(task_data)
        if not local_core_engine:
            self._is_running = False
            return

        total_samples = config.ALGO_LHS_SAMPLES
        
        self.progress_updated.emit(0, total_samples, "執行拉丁超立方採樣 (LHS) 掃描擺角...")
        
        scaled_samples = self._perform_lhs_sampling(bounds, total_samples, len(dof_keys))

        if local_core_engine.platform_type == '6-DOF':
            joint_names = [f"{p}{i+1}" for p in "AB" for i in range(6)]
        else: # 3-DOF
            joint_names = [f"{p}{i}" for p in "AB" for i in [1, 3, 5]]
        max_angles = {name: 0.0 for name in joint_names}
        
        for i, pose_vec in enumerate(scaled_samples):
            if not self._is_running: break
            pose_ui_units = self._convert_pose_to_ui_units(pose_vec, dof_keys)

            if local_core_engine.is_pose_valid(pose_ui_units, 'operational'):
                angle_data = local_core_engine.get_current_joint_angles_and_vectors(pose_ui_units)
                if angle_data:
                    base_angles = angle_data["base_angles_deg"]
                    platform_angles = angle_data["platform_angles_deg"]
                    
                    for j, angle in enumerate(base_angles):
                        joint_name = joint_names[j]
                        if angle > max_angles[joint_name]:
                            max_angles[joint_name] = angle
                            
                    for j, angle in enumerate(platform_angles):
                        joint_name = joint_names[j + len(base_angles)]
                        if angle > max_angles[joint_name]:
                            max_angles[joint_name] = angle

            if (i % 50) == 0:
                self.progress_updated.emit(i + 1, total_samples, f"掃描點 {i+1}/{total_samples}")

        if not self._is_running:
            self.angle_analysis_completed.emit({'success': False, 'message': '分析已由使用者取消。'})
            return

        result = {
            'success': True,
            'max_angles': max_angles,
            'message': "節點擺角範圍分析完成。"
        }
        self.angle_analysis_completed.emit(result)
        self._is_running = False
        print(f"節點擺角範圍分析完成，耗時 {time.time() - start_time:.2f} 秒。")
        print("="*50 + "\n")

    @pyqtSlot()
    def stop_analysis(self):
        self._is_running = False

    def _setup_analysis(self, task_data):
        workspace_limits = task_data.get('workspace_limits')
        platform_type = task_data.get('platform_type')
        core_params = task_data.get('core_params')

        if not workspace_limits or not platform_type or not core_params:
            self.analysis_finished.emit({'success': False, 'message': '收到的分析任務資料不完整。'})
            return None, None, None
            
        local_core_engine = CoreEngine()
        local_core_engine.platform_type = platform_type
        for key, value in core_params.items():
            local_core_engine.update_parameter(key, value)

        if platform_type == '6-DOF':
            dof_keys = ['x', 'y', 'z', 'pitch', 'roll', 'yaw']
        else:
            dof_keys = ['z', 'pitch', 'roll']
        
        relative_limits = self._get_relative_limits(workspace_limits, dof_keys, local_core_engine)
        bounds_min = [relative_limits[f'{key}_min'] for key in dof_keys]
        bounds_max = [relative_limits[f'{key}_max'] for key in dof_keys]
        bounds = Bounds(bounds_min, bounds_max)

        return local_core_engine, bounds, dof_keys

    def _perform_lhs_sampling(self, bounds, n_samples, dimensions):
        seed = config.ALGO_DETERMINISTIC_SEED
        sampler = LatinHypercube(d=dimensions, seed=seed)
        samples = sampler.random(n=n_samples)
        scaled_samples = np.array(bounds.lb) + samples * (np.array(bounds.ub) - np.array(bounds.lb))
        return scaled_samples

    def _get_relative_limits(self, absolute_limits, dof_keys, local_core_engine):
        relative = {}
        h_val = local_core_engine.get_parameter('H')

        for key in dof_keys:
            min_val_abs = absolute_limits.get(f'{key}_min', 0)
            max_val_abs = absolute_limits.get(f'{key}_max', 0)
            
            if key in ['pitch', 'roll', 'yaw']:
                min_val_ui = min_val_abs
                max_val_ui = max_val_abs
            else:
                min_val_ui = min_val_abs
                max_val_ui = max_val_abs

            if local_core_engine.platform_type == '6-DOF' and h_val and h_val > 0:
                zero_val = 0
                if key == 'x': zero_val = local_core_engine.zero_pose_offset.get('x', 0.0)
                elif key == 'y': zero_val = local_core_engine.zero_pose_offset.get('y', 0.0)
                elif key == 'z': zero_val = h_val
                min_val_ui -= zero_val
                max_val_ui -= zero_val

            relative[f'{key}_min'] = min_val_ui
            relative[f'{key}_max'] = max_val_ui
        return relative

    def _get_dynamics_params_for_analysis(self, local_core_engine, core_params: dict, is_static_only: bool) -> dict:
        if is_static_only:
            lin_accel, ang_accel = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        else:
            lin_accel = core_params.get('lin_accel', [0.0, 0.0, 0.0])
            ang_accel = core_params.get('ang_accel', [0.0, 0.0, 0.0])

        return {
            'a_lin': lin_accel, 
            'a_ang': ang_accel,
            'm_p': local_core_engine.get_parameter('m_p'),
            'm_l': local_core_engine.get_parameter('m_l'),
            'com_l_x': local_core_engine.get_parameter('com_l_x'),
            'com_l_y': local_core_engine.get_parameter('com_l_y'),
            'com_l_z': local_core_engine.get_parameter('com_l_z')
        }

    def _convert_pose_to_ui_units(self, pose_vec, dof_keys):
        return {key: pose_vec[i] for i, key in enumerate(dof_keys)}

# [新增] 輔助類別，用於在執行緒中傳遞停止信號
class InterruptedError(Exception):
    pass
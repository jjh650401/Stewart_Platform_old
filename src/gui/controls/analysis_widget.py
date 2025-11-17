# D:\Python_Programs\Stewart_Platform\src\gui\controls\analysis_widget.py

# ==============================================================================
# [修改註記 - feature-auto-demo (Bug 修復)]
# 日期: 2025-11-17
# 修改者: AI 協作
# ------------------------------------------------------------------------------
# 修改重點:
# 1. [Bug修復] _apply_slider_value: 修正了負半週期的方向計算錯誤。
#    - 原因: 原程式碼在處理 norm_val < 0 時多乘了一個 -1，導致負值變成正值。
#    - 解決: 移除 * -1，讓負的 norm_val 正確驅動滑塊至負座標。
# ==============================================================================

# [架構性註記] 
# 1. 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# 2. 本檔案 (UI 層) 負責將從核心引擎 (kinematics.py) 接收到的
#    標準單位 (mm, rad) 轉換為使用者易讀的單位 (mm, deg)。

import time
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, 
                             QLabel, QPushButton, QCheckBox, QInputDialog, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QEvent, pyqtSignal
from src.core import config
from src.utils.custom_widgets import CustomDoubleSpinBox, CustomSlider, CustomComboBox

class AnalysisWidget(QWidget):
    pose_changed = pyqtSignal(dict)
    workspace_analysis_requested = pyqtSignal(str)
    toggle_angle_visualization = pyqtSignal(bool)
    toggle_node_coordinate_visualization = pyqtSignal(bool)

    def __init__(self, parent=None, dof_list=['x', 'y', 'z', 'pitch', 'roll', 'yaw']):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.dof_list = dof_list
        self.sliders = {}
        self.workspace_labels = {}
        
        self.animation_timer = QTimer(self)
        self.animation_start_time = 0
        self.animation_duration = config.DEFAULT_ANIMATION_DURATION_S
        self.is_looping_animation = False
        self.selected_dofs_for_animation = []
        self.current_demo_mode_index = 0 # 0: Custom, 1: Sequential, 2: Circular
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.workspace_display_group = self._create_workspace_display()
        self.controls_group = self._create_dof_controls()
        
        main_layout.addWidget(self.workspace_display_group)
        main_layout.addWidget(self.controls_group)
        
        self.demo_group = self._create_demo_controls()
        main_layout.addWidget(self.demo_group)

        main_layout.addStretch()

    def _connect_signals(self):
        self.animation_timer.timeout.connect(self._update_animation_frame)
        if hasattr(self, 'demo_start_btn'):
            self.demo_start_btn.clicked.connect(self.on_start_demo_clicked)
            self.demo_stop_btn.clicked.connect(self.on_stop_demo_clicked)
            self.demo_loop_checkbox.stateChanged.connect(lambda state: setattr(self, 'is_looping_animation', state == Qt.CheckState.Checked.value))
            self.demo_duration_spinbox.valueChanged.connect(lambda value: setattr(self, 'animation_duration', value))
        
        if hasattr(self, 'show_angles_checkbox'):
            self.show_angles_checkbox.stateChanged.connect(
                lambda state: self.toggle_angle_visualization.emit(state == Qt.CheckState.Checked.value)
            )
            
        if hasattr(self, 'show_coords_checkbox'):
            self.show_coords_checkbox.stateChanged.connect(
                lambda state: self.toggle_node_coordinate_visualization.emit(state == Qt.CheckState.Checked.value)
            )

    def _create_workspace_display(self):
        group = QGroupBox("平台空間範圍")
        form = QFormLayout(group)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        dof_map = {
            'x': 'Surge (X, mm)', 'y': 'Sway (Y, mm)', 'z': 'Heave (Z, mm)',
            'pitch': 'Pitch (X, °)', 'roll': 'Roll (Y, °)', 'yaw': 'Yaw (Z, °)'
        }

        for name in self.dof_list:
            label_text = dof_map.get(name, name.capitalize())
            result_label = QLabel("[ 0.000 ~ 0.000 ]")
            result_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            form.addRow(label_text, result_label)
            self.workspace_labels[name] = result_label
            
        return group

    def _create_dof_controls(self):
        main_group = QGroupBox("平台姿態控制")
        form = QFormLayout(main_group)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        dof_map_labels = {
            'x': 'Surge (X)', 'y': 'Sway (Y)', 'z': 'Heave (Z)',
            'pitch': 'Pitch (X)', 'roll': 'Roll (Y)', 'yaw': 'Yaw (Z)'
        }
        
        for name in self.dof_list:
            is_translation = name in ['x', 'y', 'z']
            s_min, s_max, s_init = config.DEFAULT_SLIDER_RANGES.get(name, (-30, 30, 0))
            unit = "mm" if is_translation else "°"
            
            label_text = dof_map_labels.get(name, name.capitalize())
            label = f"{label_text} ({unit})"
            
            self._add_slider_to_form(name, label, s_min, s_max, s_init, form)
        
        return main_group

    def _add_slider_to_form(self, name, label, s_min, s_max, s_init, form_layout):
        slider = CustomSlider(Qt.Orientation.Horizontal, self)
        prec = config.SLIDER_PRECISION_FACTOR
        slider.setRange(int(s_min * prec), int(s_max * prec))
        slider.setValue(int(s_init * prec))
        slider.installEventFilter(self)

        min_label, max_label, value_label = QLabel(f"{s_min:.1f}"), QLabel(f"{s_max:.1f}"), QLabel(f"{s_init:.1f}")
        checkbox = QCheckBox(self)
        checkbox.setToolTip(f"勾選以將 {label} 加入自動展演")
        
        slider_container = QWidget(self)
        hbox = QHBoxLayout(slider_container); hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(checkbox); hbox.addWidget(min_label); hbox.addWidget(slider, 1); hbox.addWidget(max_label); hbox.addWidget(value_label)
        
        slider.valueChanged.connect(self._on_any_slider_moved)
        self.sliders[name] = {'slider': slider, 'label': value_label, 'min_label': min_label, 'max_label': max_label, 'checkbox': checkbox}
        form_layout.addRow(label, slider_container)
        
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonDblClick and isinstance(source, CustomSlider):
            for name, ctrl in self.sliders.items():
                if ctrl['slider'] is source:
                    self._prompt_for_slider_value(name, ctrl)
                    return True
        return super().eventFilter(source, event)

    def _prompt_for_slider_value(self, name, ctrl):
        slider = ctrl['slider']; prec = config.SLIDER_PRECISION_FACTOR
        is_deg = name in ['pitch', 'roll', 'yaw']
        unit = "°" if is_deg else "mm"
        min_val, max_val = slider.minimum() / prec, slider.maximum() / prec
        
        new_value, ok = QInputDialog.getDouble(self, f"精確輸入 - {name}", f"請輸入數值 ({unit}):", slider.value() / prec, min_val, max_val, 2)
        if ok: slider.setValue(int(new_value * prec))

    def _on_any_slider_moved(self):
        pose_ui = {}
        prec = config.SLIDER_PRECISION_FACTOR
        for name, ctrl in self.sliders.items():
            val = ctrl['slider'].value() / prec
            ctrl['label'].setText(f"{val:.1f}")
            pose_ui[name] = val
        self.pose_changed.emit(pose_ui)

    def _create_demo_controls(self):
        group = QGroupBox("姿態展演與視覺化")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # [新增] 展演模式選擇與選項
        options_layout = QHBoxLayout()
        
        self.demo_mode_combo = CustomComboBox(self)
        self.demo_mode_combo.addItems([
            "自訂勾選 (手動選擇)",
            "單軸極限順序 (自動)", 
            "畫圓/畫球繞行 (自動)"
        ])
        self.demo_mode_combo.setToolTip("選擇自動展演的模式")
        
        self.demo_loop_checkbox = QCheckBox("循環展演", self)
        self.demo_loop_checkbox.setChecked(config.VIZ_DEFAULT_LOOP_ANIMATION)

        self.show_angles_checkbox = QCheckBox("顯示關節角度")
        self.show_angles_checkbox.setChecked(config.VIZ_DEFAULT_SHOW_ANGLES)

        self.show_coords_checkbox = QCheckBox("顯示節點座標")
        self.show_coords_checkbox.setChecked(config.VIZ_DEFAULT_SHOW_COORDS)
        
        options_layout.addWidget(QLabel("模式:"))
        options_layout.addWidget(self.demo_mode_combo, 1) # Stretch combo
        options_layout.addWidget(self.demo_loop_checkbox)
        options_layout.addWidget(self.show_angles_checkbox)
        options_layout.addWidget(self.show_coords_checkbox)
        
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 5, 0, 5)

        self.demo_duration_spinbox = CustomDoubleSpinBox(self)
        self.demo_duration_spinbox.setRange(*config.ANIMATION_DURATION_RANGE_S)
        self.demo_duration_spinbox.setValue(self.animation_duration)
        self.demo_duration_spinbox.setSuffix(" s")
        # [修改] 標籤改為 "週期時間 (Cycle Time)" 以符合新邏輯
        form_layout.addRow("週期時間 (Cycle Time, s):", self.demo_duration_spinbox)
        
        buttons_layout = QHBoxLayout()
        self.demo_start_btn = QPushButton("開始展演"); self.demo_stop_btn = QPushButton("停止展演")
        self.demo_stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.demo_start_btn); buttons_layout.addWidget(self.demo_stop_btn)
        
        layout.addLayout(options_layout)
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        
        return group
    
    def on_start_demo_clicked(self):
        if self.animation_timer.isActive(): return
        
        # [新增] 根據模式選擇目標軸
        mode_idx = self.demo_mode_combo.currentIndex()
        self.current_demo_mode_index = mode_idx
        
        if mode_idx == 0: # 自訂
            self.selected_dofs_for_animation = [name for name, ctrl in self.sliders.items() if ctrl['checkbox'].isChecked()]
            if not self.selected_dofs_for_animation:
                QMessageBox.information(self, "提示", "請至少勾選一個要展演的姿態。")
                return
        
        elif mode_idx == 1: # 單軸順序
            # 自動選取所有可用軸
            self.selected_dofs_for_animation = list(self.dof_list)
            
        elif mode_idx == 2: # 畫圓
            # 檢查是否有 pitch 和 roll
            if 'pitch' not in self.sliders or 'roll' not in self.sliders:
                 QMessageBox.warning(self, "無法執行", "此平台類型不支援 Pitch/Roll 畫圓展演。")
                 return
            self.selected_dofs_for_animation = ['pitch', 'roll']
        
        self._set_demo_ui_enabled(is_running=True)
        self.animation_start_time = time.time()
        self.animation_timer.start(config.ANIMATION_FRAME_INTERVAL_MS)

    def on_global_analysis_pose_update(self, pose_ui: dict):
        for ctrl in self.sliders.values():
            ctrl['slider'].blockSignals(True)
        
        for name, value in pose_ui.items():
            if name in self.sliders:
                prec = config.SLIDER_PRECISION_FACTOR
                self.sliders[name]['slider'].setValue(int(value * prec))
        
        for ctrl in self.sliders.values():
            ctrl['slider'].blockSignals(False)
            
        self._on_any_slider_moved()

    def update_workspace_display(self, limits: dict, analysis_type: str, h_val: float, offset: dict = None):
        if not limits:
            self.reset_workspace_display()
            return

        self.workspace_display_group.setVisible(True)
        is_6dof = 'x' in self.dof_list

        relative_limits = {}

        # --- MODIFICATION START ---
        # [註記] 修正：恢復 6-DOF 平台下將絕對座標轉換為相對座標的邏輯。
        # 核心引擎 (kinematics.py) 傳來的 limits 包含 'x', 'y', 'z' 的絕對座標 (mm)
        # 和 'pitch', 'roll', 'yaw' 的絕對範圍 (rad)。
        
        for name in ['x', 'y', 'z']:
            if name in self.dof_list:
                min_abs = limits.get(f'{name}_min', 0.0)
                max_abs = limits.get(f'{name}_max', 0.0)
                
                if is_6dof and offset:
                    # 6-DOF: 計算相對於零位姿態的偏移量
                    if name == 'x': zero_val = offset.get('x', 0.0)
                    elif name == 'y': zero_val = offset.get('y', 0.0)
                    else: zero_val = h_val # name == 'z'
                    relative_limits[f'{name}_min'] = (min_abs - zero_val)
                    relative_limits[f'{name}_max'] = (max_abs - zero_val)
                else:
                    # 3-DOF: 只有 Z 軸需要轉換為相對值
                    if name == 'z':
                        relative_limits[f'{name}_min'] = min_abs - h_val
                        relative_limits[f'{name}_max'] = max_abs - h_val
                    else:
                        relative_limits[f'{name}_min'] = min_abs
                        relative_limits[f'{name}_max'] = max_abs

        for name in ['pitch', 'roll', 'yaw']:
            if name in self.dof_list:
                # 角度值從 kinematics.py 傳來時是弧度 (rad)
                # 並且它們是相對於零位姿態的角度（零位姿態的 pitch/roll=0, yaw=相位角）
                # 因此我們可以直接轉換為度 (deg) 來顯示
                relative_limits[f'{name}_min'] = np.rad2deg(limits.get(f'{name}_min', 0.0))
                relative_limits[f'{name}_max'] = np.rad2deg(limits.get(f'{name}_max', 0.0))
        # --- MODIFICATION END ---

        for name in self.dof_list:
            min_val = relative_limits.get(f'{name}_min', 0.0)
            max_val = relative_limits.get(f'{name}_max', 0.0)
            
            # [註記] 移除此處的 rad2deg 轉換，因為已在上面處理完畢。
            self.workspace_labels[name].setText(f"[{min_val:.3f} ~ {max_val:.3f}]")
            
            ctrl = self.sliders[name]
            prec = config.SLIDER_PRECISION_FACTOR
            ctrl['slider'].setRange(int(min_val * prec), int(max_val * prec))
            ctrl['min_label'].setText(f"{min_val:.1f}")
            ctrl['max_label'].setText(f"{max_val:.1f}")
            ctrl['slider'].setValue(0)

        title_suffix = "可用行程範圍" if analysis_type == 'operational' else "機械極限範圍"
        
        title_controls = f"平台姿態控制 ({title_suffix})"
        self.controls_group.setTitle(title_controls)

        title_workspace = f"平台空間範圍 ({title_suffix})"
        self.workspace_display_group.setTitle(title_workspace)
            
        self._on_any_slider_moved()

    def reset_workspace_display(self):
        if hasattr(self, 'workspace_display_group'):
            self.workspace_display_group.setVisible(True)
            self.workspace_display_group.setTitle("平台空間範圍")

        if hasattr(self, 'controls_group'):
            self.controls_group.setTitle("平台姿態控制")
        
        for name in self.dof_list:
            if name in self.workspace_labels:
                self.workspace_labels[name].setText("[ 0.000 ~ 0.000 ]")
            if name in self.sliders:
                s_min, s_max, s_init = config.DEFAULT_SLIDER_RANGES.get(name, (-30, 30, 0))
                ctrl = self.sliders[name]
                prec = config.SLIDER_PRECISION_FACTOR
                ctrl['slider'].setRange(int(s_min * prec), int(s_max * prec))
                ctrl['min_label'].setText(f"{s_min:.1f}")
                ctrl['max_label'].setText(f"{s_max:.1f}")
                ctrl['slider'].setValue(int(s_init * prec))

    def on_stop_demo_clicked(self):
        if not self.animation_timer.isActive(): return
        self.animation_timer.stop()
        
        # 停止時將所有參與動畫的軸歸零
        targets = self.selected_dofs_for_animation if self.current_demo_mode_index != 1 else self.dof_list
        for name in targets: 
            if name in self.sliders:
                self.sliders[name]['slider'].setValue(0)
        
        self._on_any_slider_moved()
        self._set_demo_ui_enabled(is_running=False)

    def _update_animation_frame(self):
        elapsed_time = time.time() - self.animation_start_time
        cycle_duration = self.animation_duration
        
        # 模式 1: 自訂勾選 (原邏輯)
        if self.current_demo_mode_index == 0:
            progress = elapsed_time / cycle_duration
            if progress >= 1.0:
                if self.is_looping_animation:
                    progress %= 1.0; self.animation_start_time = time.time()
                else:
                    self.on_stop_demo_clicked(); return
            
            # 標準化波形: 0 -> 1 -> 0 -> -1 -> 0 (sin波形)
            # sin(2*pi*t) 在 t=0~1 剛好完成一個週期
            norm_val = np.sin(2 * np.pi * progress)
            
            for name in self.selected_dofs_for_animation:
                self._apply_slider_value(name, norm_val)

        # 模式 2: 單軸極限順序
        elif self.current_demo_mode_index == 1:
            num_axes = len(self.selected_dofs_for_animation)
            if num_axes == 0: return
            
            total_sequence_time = cycle_duration * num_axes
            
            if elapsed_time >= total_sequence_time and not self.is_looping_animation:
                self.on_stop_demo_clicked(); return
                
            current_axis_idx = int(elapsed_time / cycle_duration) % num_axes
            local_progress = (elapsed_time % cycle_duration) / cycle_duration
            
            # 標準化波形: 0 -> Max -> Min -> 0
            norm_val = np.sin(2 * np.pi * local_progress)
            
            for i, name in enumerate(self.selected_dofs_for_animation):
                if i == current_axis_idx:
                    self._apply_slider_value(name, norm_val)
                else:
                    self.sliders[name]['slider'].setValue(0)

        # 模式 3: 畫圓/畫球繞行
        elif self.current_demo_mode_index == 2:
            # 無限循環直到停止，或是單次
            if elapsed_time >= cycle_duration and not self.is_looping_animation:
                 self.on_stop_demo_clicked(); return
                 
            phase = 2 * np.pi * (elapsed_time / cycle_duration)
            
            # 設定振幅為滑塊最大範圍的 50% (安全範圍)
            # Pitch 使用 sin
            if 'pitch' in self.sliders:
                self._apply_slider_value('pitch', np.sin(phase), amplitude_ratio=0.5)
                
            # Roll 使用 cos (相差 90 度)
            if 'roll' in self.sliders:
                self._apply_slider_value('roll', np.cos(phase), amplitude_ratio=0.5)
            
            # 其他軸歸零
            for name in self.dof_list:
                if name not in ['pitch', 'roll']:
                     self.sliders[name]['slider'].setValue(0)
        
        self._on_any_slider_moved()
    
    def _apply_slider_value(self, name, norm_val, amplitude_ratio=1.0):
        """輔助函式：將標準化數值 (-1~1) 套用到滑塊"""
        slider = self.sliders[name]['slider']
        slider.blockSignals(True)
        
        # 根據正負值決定使用 max 或 min 的範圍
        if norm_val >= 0:
            target = slider.maximum() * amplitude_ratio
            slider.setValue(int(norm_val * target))
        else:
            target = abs(slider.minimum()) * amplitude_ratio
            # [修正] 移除多餘的 * -1，因為 norm_val 本身已是負值
            slider.setValue(int(norm_val * target)) 
            
        slider.blockSignals(False)

    def _set_demo_ui_enabled(self, is_running: bool):
        if not hasattr(self, 'demo_start_btn'): return
        self.demo_start_btn.setEnabled(not is_running)
        self.demo_stop_btn.setEnabled(is_running)
        self.demo_duration_spinbox.setEnabled(not is_running)
        self.demo_loop_checkbox.setEnabled(not is_running)
        self.demo_mode_combo.setEnabled(not is_running) # [新增] 鎖定模式選擇
        
        for ctrl in self.sliders.values():
            ctrl['slider'].setEnabled(not is_running)
            ctrl['checkbox'].setEnabled(not is_running)
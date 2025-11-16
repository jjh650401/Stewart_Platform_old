# D:\Python_Programs\Stewart_Platform\src\gui\controls\dynamics_widget.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 本檔案遵循「核心層 (mm)」的單位原則，但為了計算標準物理單位 (N, Nm)，
# 內部會進行局部的 mm -> m 轉換。
# 詳情請參閱《基礎背景與規則.v5.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, 
                             QPushButton, QLabel, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt
from src.core import config
from src.utils.custom_widgets import CustomDoubleSpinBox, CustomComboBox  # 導入自訂類別

# 用於將牛頓(N)轉換為公斤力(kgf)以供顯示的標準重力近似值
G_STANDARD_FOR_KGF = 9.81

class DynamicsWidget(QWidget):
    """
    一個獨立的 UI 元件，用於輸入動力學分析參數和顯示結果。
    """
    analysis_requested = pyqtSignal()
    global_analysis_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inputs = {}
        self.labels = {}
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        input_group = QGroupBox("動力學輸入參數")
        form_layout = QFormLayout(input_group)

        self.inputs['load_condition'] = CustomComboBox()
        self.inputs['load_condition'].addItems(config.UI_LOAD_CONDITIONS)
        self.inputs['load_condition'].currentIndexChanged.connect(self._on_condition_change)
        form_layout.addRow("負載工況:", self.inputs['load_condition'])

        # --- MODIFIED: Renamed variables and labels to align with v2.0 ---
        self._add_spinbox(form_layout, 'm_p', "平台質量 (m_p) (kg):", 1.0, 10000.0, 200.0)
        self._add_spinbox(form_layout, 'm_l', "負載質量 (m_l) (kg):", 0.0, 10000.0, 500.0)
        self._add_spinbox(form_layout, 'com_l_x', "負載質心 X (com_l_x) (mm):", -5000.0, 5000.0, 0.0)
        self._add_spinbox(form_layout, 'com_l_y', "負載質心 Y (com_l_y) (mm):", -5000.0, 5000.0, 0.0)
        self._add_spinbox(form_layout, 'com_l_z', "負載質心 Z (com_l_z) (mm):", -5000.0, 5000.0, 700.0)
        
        self._add_spinbox(form_layout, 'a_lin_z', "Z軸平移加速度 (a_lin_z) (g):", -5.0, 5.0, 0.5)
        self._add_spinbox(form_layout, 'a_ang_x', "X軸角加速度 (a_ang_x) (rad/s²):", -50.0, 50.0, 0.0)
        self._add_spinbox(form_layout, 'a_ang_y', "Y軸角加速度 (a_ang_y) (rad/s²):", -50.0, 50.0, 0.0)
        
        self.inputs['com_l_x'].setEnabled(False)
        self.inputs['com_l_y'].setEnabled(False)

        main_layout.addWidget(input_group)

        current_pose_group = QGroupBox("當前姿態出力分析")
        current_pose_layout = QFormLayout(current_pose_group)
        self.labels['current_force'] = QLabel("N/A")
        self.labels['current_force'].setStyleSheet("font-weight: bold; color: blue; font-size: 14px;")
        self.labels['current_pose'] = QLabel("N/A")
        self.labels['current_pose'].setAlignment(Qt.AlignmentFlag.AlignTop)
        self.labels['current_pose'].setStyleSheet("color: #333; line-height: 1.5;")
        
        self.analyze_button = QPushButton("計算當前姿態出力")
        self.analyze_button.clicked.connect(self.analysis_requested.emit)
        current_pose_layout.addRow(self.analyze_button)
        current_pose_layout.addRow("最大推/拉力:", self.labels['current_force'])
        current_pose_layout.addRow("發生姿態:", self.labels['current_pose'])
        main_layout.addWidget(current_pose_group)

        global_max_group = QGroupBox("全域最大出力分析")
        global_max_layout = QVBoxLayout(global_max_group)

        results_form_layout = QFormLayout()
        self.labels['global_force'] = QLabel("N/A")
        self.labels['global_force'].setStyleSheet("font-weight: bold; color: red; font-size: 14px;")
        self.labels['global_pose'] = QLabel("N/A")
        self.labels['global_pose'].setAlignment(Qt.AlignmentFlag.AlignTop)
        self.labels['global_pose'].setStyleSheet("color: #333; line-height: 1.5;")
        results_form_layout.addRow("最大推/拉力:", self.labels['global_force'])
        results_form_layout.addRow("發生姿態:", self.labels['global_pose'])
        
        self.static_only_checkbox = QCheckBox("僅考慮靜態負載 (忽略加速度)")
        self.static_only_checkbox.setChecked(True)
        
        self.analyze_global_button = QPushButton("分析全域最大出力")
        self.analyze_global_button.setToolTip("在可用工作空間內執行LHS+SQP智慧搜尋，找出最大出力點。\n可取消勾選上方選項以納入加速度進行動態分析。")
        self.analyze_global_button.clicked.connect(self.global_analysis_requested.emit)
        
        global_max_layout.addLayout(results_form_layout)
        global_max_layout.addWidget(self.static_only_checkbox)
        global_max_layout.addWidget(self.analyze_global_button)
        
        main_layout.addWidget(global_max_group)

        main_layout.addStretch()

    def _add_spinbox(self, layout, name, label, min_val, max_val, default_val):
        spinbox = CustomDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        spinbox.setDecimals(2)
        self.inputs[name] = spinbox
        layout.addRow(label, spinbox)

    def _on_condition_change(self, index):
        is_offset = (index == 1)
        # --- MODIFIED: Use new variable names ---
        self.inputs['com_l_x'].setEnabled(is_offset)
        self.inputs['com_l_y'].setEnabled(is_offset)
        if not is_offset:
            self.inputs['com_l_x'].setValue(0.0)
            self.inputs['com_l_y'].setValue(0.0)
            
    def get_values(self) -> dict:
        # --- MODIFIED: Update keys and unit conversion logic to match v2.0 ---
        params = {}
        # Length values are now sent directly in mm
        params['com_l_x'] = self.inputs['com_l_x'].value()
        params['com_l_y'] = self.inputs['com_l_y'].value()
        params['com_l_z'] = self.inputs['com_l_z'].value()
        params['m_p'] = self.inputs['m_p'].value()
        params['m_l'] = self.inputs['m_l'].value()
        
        # Acceleration is converted from g to mm/s^2 using the global config value
        a_lin_z_g = self.inputs['a_lin_z'].value()
        params['a_lin'] = [0.0, 0.0, a_lin_z_g * config.G_ACCELERATION]
        
        params['a_ang'] = [self.inputs['a_ang_x'].value(), self.inputs['a_ang_y'].value(), 0.0]
        return params

    def is_static_analysis_only(self) -> bool:
        return self.static_only_checkbox.isChecked()

    def set_values(self, params: dict):
        # --- MODIFIED: Expect new keys and mm units from backend ---
        if 'com_l_x' in params: self.inputs['com_l_x'].setValue(params['com_l_x'])
        if 'com_l_y' in params: self.inputs['com_l_y'].setValue(params['com_l_y'])
        if 'com_l_z' in params: self.inputs['com_l_z'].setValue(params['com_l_z'])
        
        if 'm_p' in params: self.inputs['m_p'].setValue(params['m_p'])
        if 'm_l' in params: self.inputs['m_l'].setValue(params['m_l'])

        if 'a_lin' in params and params['a_lin']:
            a_lin_z_mms2 = params['a_lin'][2]
            self.inputs['a_lin_z'].setValue(a_lin_z_mms2 / config.G_ACCELERATION)

        if 'a_ang' in params and params['a_ang']:
            self.inputs['a_ang_x'].setValue(params['a_ang'][0])
            self.inputs['a_ang_y'].setValue(params['a_ang'][1])
        
        is_offset = (params.get('com_l_x', 0.0) != 0.0 or params.get('com_l_y', 0.0) != 0.0)
        self.inputs['load_condition'].setCurrentIndex(1 if is_offset else 0)

    def _format_pose_to_string(self, pose_ui: dict | None) -> str:
        if not pose_ui:
            return "N/A"
        
        parts = []
        dof_map = {
            'x': 'Surge (X)', 'y': 'Sway (Y)', 'z': 'Heave (Z)',
            'pitch': 'Pitch (X)', 'roll': 'Roll (Y)', 'yaw': 'Yaw (Z)'
        }
        
        for key, unit in [('x', 'mm'), ('y', 'mm'), ('z', 'mm'), ('pitch', '°'), ('roll', '°'), ('yaw', '°')]:
            if key in pose_ui:
                display_name = dof_map.get(key, key.capitalize())
                parts.append(f"{display_name}: {pose_ui[key]:.1f} {unit}")
        
        return "<br>".join(parts)

    def set_current_result(self, forces: list[float] | None, pose_ui: dict | None, is_valid: bool):
        force_text = ""
        if forces:
            max_abs_force = max(abs(f) for f in forces)
            force_kgf = max_abs_force / G_STANDARD_FOR_KGF
            force_text = f"{max_abs_force:,.2f} N  ({force_kgf:,.2f} kgf)"

        warning_text = "<font color='orange'>超出可用工作範圍</font>"
        
        if not is_valid:
            display_html = f"{warning_text}<br>{force_text}" if force_text else warning_text
            self.labels['current_force'].setText(display_html)
        else:
            self.labels['current_force'].setText(force_text if force_text else "N/A")
        
        self.labels['current_pose'].setText(self._format_pose_to_string(pose_ui))


    def set_global_result(self, forces: list[float] | None, pose_ui: dict | None):
        if forces:
            max_abs_force = max(abs(f) for f in forces)
            force_kgf = max_abs_force / G_STANDARD_FOR_KGF
            self.labels['global_force'].setText(f"{max_abs_force:,.2f} N  ({force_kgf:,.2f} kgf)")
        else:
            self.labels['global_force'].setText("N/A")
            
        self.labels['global_pose'].setText(self._format_pose_to_string(pose_ui))
        
    def reset_results(self):
        self.labels['current_force'].setText("N/A")
        self.labels['current_pose'].setText("N/A")
        self.labels['global_force'].setText("N/A")
        self.labels['global_pose'].setText("N/A")
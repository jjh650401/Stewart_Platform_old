# D:\Python_Programs\Stewart_Platform\src\gui\controls\six_dof_widget.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# 本檔案中的所有長度數值，無論是與使用者互動，還是與核心引擎交換，皆使用 mm 單位。
# 檔案內不應存在任何 m 與 mm 之間的轉換。
# 詳情請參閱《基礎背景與規則.v5.md》。

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from src.core import config

class SixDofWidget(QWidget):
    """
    專門用於六自由度平台幾何參數輸入與結果顯示的 Widget。
    """
    parameters_confirmed = pyqtSignal(dict)
    op_workspace_analysis_requested = pyqtSignal()
    mech_workspace_analysis_requested = pyqtSignal()
    parameter_changed = pyqtSignal()
    angle_range_analysis_requested = pyqtSignal()
    calculation_finished = pyqtSignal(bool, str)

    def __init__(self, ui_builder, core_engine, parent=None):
        super().__init__(parent)
        self.ui_builder = ui_builder
        self.core_engine = core_engine
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        self.inputs = {}
        self.labels = {}
        self.buttons = {}
        self.combos = {}
        self.radios = {}
        self.angle_limit_widgets = []
        self.displays = {}

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        base_group, base_inputs, base_labels = self.ui_builder.create_6dof_base_group(self)
        self.inputs.update(base_inputs)
        self.labels.update(base_labels)

        mobile_group, mobile_inputs, mobile_labels = self.ui_builder.create_6dof_mobile_group(self)
        self.inputs.update(mobile_inputs)
        self.labels.update(mobile_labels)

        actuator_payload = self.ui_builder.create_actuator_group(self)
        actuator_group = actuator_payload["group"]
        self.inputs.update(actuator_payload["inputs"])
        self.labels.update(actuator_payload["labels"])
        self.combos.update(actuator_payload["combos"])
        self.radios.update(actuator_payload["radios"])
        self.angle_limit_widgets = actuator_payload["angle_limit_widgets"]
        self.enable_angle_limits_checkbox = actuator_payload["enable_angle_limits_checkbox"]
        
        button_group, results_group, calc_buttons, calc_labels, calc_displays = self.ui_builder.create_calculation_group(self, is_3dof=False)
        self.buttons.update(calc_buttons)
        self.labels.update(calc_labels)
        self.displays.update(calc_displays)
        
        main_layout.addWidget(base_group)
        main_layout.addWidget(mobile_group)
        main_layout.addWidget(actuator_group)
        main_layout.addWidget(button_group)
        main_layout.addWidget(results_group)

    def _connect_signals(self):
        self.buttons['confirm_all'].clicked.connect(self._on_confirm_clicked)
        self.buttons['H'].clicked.connect(self._handle_geometry_calculation_request)
        self.buttons['analyze_op'].clicked.connect(self.op_workspace_analysis_requested.emit)
        self.buttons['analyze_mech'].clicked.connect(self.mech_workspace_analysis_requested.emit)
        self.buttons['analyze_angles'].clicked.connect(self.angle_range_analysis_requested.emit)
        
        for spinbox in self.inputs.values():
            spinbox.valueChanged.connect(self.parameter_changed.emit)

        for combo in self.combos.values():
            combo.currentIndexChanged.connect(self._on_preset_selected_proxy)

        self.enable_angle_limits_checkbox.stateChanged.connect(self._on_toggle_angle_limits)
        
        self._on_toggle_angle_limits(self.enable_angle_limits_checkbox.checkState().value)
        for name, combo in self.combos.items():
            self._on_preset_selected(self.inputs[name], combo, is_init=True)
            
    def _handle_geometry_calculation_request(self):
        """
        處理計算平台幾何的請求，調用核心引擎，並根據結果顯示對應的訊息。
        """
        success, message = self.core_engine.calculate_platform_geometry()

        self.calculation_finished.emit(success, message)

        if success:
            if "警告" in message:
                QMessageBox.warning(self, "計算提示", message)
        else:
            if message:
                QMessageBox.critical(self, "計算失敗", message)
    
    def display_angle_range_results(self, results: dict):
        display_widget = self.displays.get('angle_results_display')
        if not display_widget:
            return

        if not results.get('success'):
            display_widget.setText(results.get('message', '分析失敗。'))
            return
            
        max_angles = results.get('max_angles', {})
        if not max_angles:
            display_widget.setText("在工作空間內未找到有效的姿態點進行分析。")
            return
            
        base_angles = sorted([(k, v) for k, v in max_angles.items() if k.startswith('A')])
        mobile_angles = sorted([(k, v) for k, v in max_angles.items() if k.startswith('B')])

        html_output = "<style> table { border-collapse: collapse; } td { padding: 2px; } </style>"
        html_output += "<table><tr>"
        html_output += "<td style='padding-left: 5px;'><b>固定平台 (Base)</b></td>"
        html_output += "<td style='padding-left: 5px;'><b>活動平台 (Mobile)</b></td>"
        html_output += "</tr>"
        
        num_rows = max(len(base_angles), len(mobile_angles))
        for i in range(num_rows):
            html_output += "<tr>"
            if i < len(base_angles):
                name, angle = base_angles[i]
                html_output += f"<td style='padding-left: 5px;'>{name}: {angle:.2f}°</td>"
            else:
                html_output += "<td></td>"

            if i < len(mobile_angles):
                name, angle = mobile_angles[i]
                html_output += f"<td style='padding-left: 5px;'>{name}: {angle:.2f}°</td>"
            else:
                html_output += "<td></td>"
            html_output += "</tr>"

        html_output += "</table>"
        display_widget.setHtml(html_output)

    def _on_toggle_angle_limits(self, state):
        is_checked = (state == Qt.CheckState.Checked.value)
        for widget in self.angle_limit_widgets:
            widget.setVisible(is_checked)

    def _on_preset_selected_proxy(self):
        sender = self.sender()
        for name, combo in self.combos.items():
            if combo == sender:
                self._on_preset_selected(self.inputs[name], combo)
                break

    def _on_preset_selected(self, spinbox, combo, is_init=False):
        current_index = combo.currentIndex()
        _, preset_value = config.ANGLE_LIMIT_PRESETS[current_index]

        if preset_value is None:
            if not is_init:
                spinbox.setEnabled(True)
        else:
            spinbox.setValue(preset_value)
            spinbox.setEnabled(False)

    def _on_confirm_clicked(self):
        params = self.get_all_inputs()
        self.parameters_confirmed.emit(params)
        
    def get_all_inputs(self):
        params = {}
        params['enable_joint_limits'] = self.enable_angle_limits_checkbox.isChecked()

        for name, spinbox in self.inputs.items():
            if name in ['base_joint_limit', 'platform_joint_limit']:
                params[name] = np.deg2rad(spinbox.value())
            else:
                # --- MODIFIED: REMOVED unit conversion. Pass mm value directly to the core engine. ---
                params[name] = spinbox.value()
        
        params['platform_joint_style'] = 'bottom' if self.radios['bottom_mount'].isChecked() else 'top'
        return params
        
    def set_input_values(self, params: dict):
        enable_limits = params.get('enable_joint_limits', False) 
        self.enable_angle_limits_checkbox.setChecked(enable_limits)

        for name, value in params.items():
            if name in self.inputs and value is not None:
                self.inputs[name].blockSignals(True)
                if name in ['base_joint_limit', 'platform_joint_limit']:
                    self.inputs[name].setValue(np.rad2deg(value))
                    if name in self.combos:
                        combo = self.combos[name]
                        found_preset = False
                        for i, (_, val) in enumerate(config.ANGLE_LIMIT_PRESETS):
                            if val is not None and np.isclose(np.rad2deg(value), val):
                                combo.setCurrentIndex(i)
                                self.inputs[name].setEnabled(False)
                                found_preset = True
                                break
                        if not found_preset:
                            combo.setCurrentIndex(0)
                            self.inputs[name].setEnabled(True)
                else:
                    # --- MODIFIED: REMOVED unit conversion. Expect mm from core and display directly. ---
                    self.inputs[name].setValue(value)
                self.inputs[name].blockSignals(False)
        
        joint_style = params.get('platform_joint_style', 'bottom')
        if joint_style == 'top':
            self.radios['top_mount'].setChecked(True)
        else:
            self.radios['bottom_mount'].setChecked(True)

    def update_display_value(self, name: str, value: float | None, unit: str = ''):
        if name in self.labels:
            if value is None or value < -1e9:
                display_text = "N/A"
            else:
                # --- MODFIED: REMOVED unit conversion. Value from core is now already in mm. ---
                display_text = f"{value:.2f}"
            self.labels[name].setText(display_text)
            
    def reset_all_calculated_values(self):
        self.update_display_value('Ra', None)
        self.update_display_value('Rb', None)
        self.update_display_value('s_mech', None)
        self.update_display_value('H', None)
        self.update_display_value('h_initial', None)
        # [刪除 - v2.3 共識 #11] 移除對已刪除的 'phase_angle' 標籤的引用
        # self.update_display_value('phase_angle', None)
        self.update_display_value('zero_pose_base_angle', None)
        self.update_display_value('zero_pose_platform_angle', None)
        
        self.buttons['H'].setEnabled(False)
        self.buttons['analyze_op'].setEnabled(False)
        self.buttons['analyze_mech'].setEnabled(False)
        self.buttons['analyze_angles'].setEnabled(False)

        if 'angle_results_display' in self.displays:
            self.displays['angle_results_display'].setText("請先執行分析...")

    def get_buttons(self):
        return self.buttons
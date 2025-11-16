# D:\Python_Programs\Stewart_Platform\src\gui\controls\drive_system_widget.py

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# 本檔案中的所有長度數值，無論是與使用者互動，還是與核心引擎交換，皆使用 mm 單位。
# 檔案內不應存在任何 m 與 mm 之間的轉換（除了極少數與外部定義比較所需之局部轉換）。
# 詳情請參閱《基礎背景與規則.v5.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, 
                             QLabel, QPushButton, QRadioButton, QScrollArea,
                             QMessageBox, QTextEdit, QGridLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from src.utils.custom_widgets import CustomDoubleSpinBox, CustomComboBox

from src.core.database_manager import DatabaseManager
from src.core.drive_system_engine import DriveSystemEngine
from src.core import config

class DriveSystemWidget(QWidget):
    """
    驅動系統計算頁籤的 UI 介面，支援負荷係數、減速比選擇、壽命需求計算及詳細參數顯示。
    """
    mode_changed = pyqtSignal(str)

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.drive_engine = DriveSystemEngine()
        
        self.auto_required_axial_force = None
        self.last_calc_results = {}
        self.motor_data = []
        self.screw_data = []
        self.pulley_data = []
        
        # --- MODIFIED: Renamed input dictionaries for clarity ---
        self.manual_inputs = {}
        self.eng_param_inputs = {}
        self.motion_profile_inputs = {}
        self.life_req_inputs = {}

        self.result_labels = {}
        self.part_spec_display = QTextEdit()
        self.motion_profile_table = QTableWidget()
        self.ratio_input = QWidget() # Placeholder
        self.ratio_label = QLabel()
        self.fw_label = QLabel()
        self.auto_force_display = QLabel()
        self._is_loading_data = False
        
        self._init_ui()
        self._connect_signals()
        self.load_initial_data()
        self._on_mode_changed(True)
        self._update_load_factor_display()
        self._update_life_hours_display()

    def set_required_axial_force(self, force_n: float | None):
        self.auto_required_axial_force = force_n
        if self.auto_mode_radio.isChecked():
            self._update_force_input_display()

    def get_current_mode(self):
        return 'auto' if self.auto_mode_radio.isChecked() else 'manual'

    def get_parameters(self) -> dict:
        """蒐集所有UI輸入，轉換為v2.0標準變數名，並打包成字典。"""
        params = {'mode': self.get_current_mode()}
        
        all_inputs = {
            **self.manual_inputs, **self.eng_param_inputs, 
            **self.motion_profile_inputs, **self.life_req_inputs
        }
        for key, widget in all_inputs.items():
            params[key] = widget.value()

        params['selected_motor_id'] = self.motor_combo.currentData().get('id') if self.motor_combo.currentData() else None
        params['selected_screw_id'] = self.screw_combo.currentData().get('id') if self.screw_combo.currentData() else None
        
        params['use_pulley_selection'] = self.pulley_ratio_radio.isChecked()
        if params['use_pulley_selection']:
            driving_teeth = self.driving_pulley_combo.currentData().get('teeth', 1) if self.driving_pulley_combo.currentData() else 1
            driven_teeth = self.driven_pulley_combo.currentData().get('teeth', 1) if self.driven_pulley_combo.currentData() else 1
            params['i'] = driven_teeth / driving_teeth if driving_teeth > 0 else 1.0
        else:
            params['i'] = self.ratio_input.value()
            
        return params

    def set_parameters(self, data: dict):
        """根據傳入的v2.0標準變數名字典，設定UI介面。"""
        self._is_loading_data = True
        
        mode = data.get('mode', 'auto')
        if mode == 'manual': self.manual_mode_radio.setChecked(True)
        else: self.auto_mode_radio.setChecked(True)

        all_inputs = {
            **self.manual_inputs, **self.eng_param_inputs, 
            **self.motion_profile_inputs, **self.life_req_inputs
        }
        for key, widget in all_inputs.items():
            if key in data:
                widget.setValue(data[key])
        
        if data.get('selected_motor_id'): self.motor_combo.setCurrentIndex(self._find_combo_index_by_id(self.motor_combo, data['selected_motor_id']))
        if data.get('selected_screw_id'): self.screw_combo.setCurrentIndex(self._find_combo_index_by_id(self.screw_combo, data['selected_screw_id']))
        
        if data.get('use_pulley_selection', False):
            self.pulley_ratio_radio.setChecked(True)
            if data.get('driving_pulley_id'): self.driving_pulley_combo.setCurrentIndex(self._find_combo_index_by_id(self.driving_pulley_combo, data['driving_pulley_id']))
            if data.get('driven_pulley_id'): self.driven_pulley_combo.setCurrentIndex(self._find_combo_index_by_id(self.driven_pulley_combo, data['driven_pulley_id']))
        elif 'i' in data:
            self.direct_ratio_radio.setChecked(True)
            self.ratio_input.setValue(data['i'])

        self._is_loading_data = False
        self.mode_changed.emit(self.get_current_mode())
        self._update_all_displays()

    def _find_combo_index_by_id(self, combo, item_id):
        for i in range(combo.count()):
            item_data = combo.itemData(i)
            if item_data and item_data.get('id') == item_id:
                return i
        return 0

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        left_scroll = QScrollArea(); left_scroll.setWidgetResizable(True)
        left_container = QWidget(); left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._create_load_input_group())
        left_layout.addWidget(self._create_general_params_group())
        left_layout.addWidget(self._create_motion_profile_group())
        left_layout.addWidget(self._create_part_selection_group())
        left_layout.addWidget(self._create_life_requirements_box())
        left_layout.addWidget(self._create_calculation_control_group())
        left_layout.addStretch()
        left_scroll.setWidget(left_container)
        
        right_scroll = QScrollArea(); right_scroll.setWidgetResizable(True)
        right_container = QWidget(); right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(10)
        right_layout.addWidget(self._create_results_display_group())
        right_layout.addWidget(self._create_part_spec_display_group())
        right_layout.addWidget(self._create_motion_profile_display_group())
        right_layout.addStretch()
        right_scroll.setWidget(right_container)

        main_layout.addWidget(left_scroll, config.DRIVE_DASHBOARD_STRETCH_LEFT)
        main_layout.addWidget(right_scroll, config.DRIVE_DASHBOARD_STRETCH_RIGHT)

    def _create_load_input_group(self):
        group = QGroupBox("1. 負載與模式選擇")
        layout = QVBoxLayout(group)
        radio_layout = QHBoxLayout()
        self.auto_mode_radio = QRadioButton("自動模式 (基於模擬分析的校核)")
        self.manual_mode_radio = QRadioButton("手動模式 (基於基礎參數的設計)")
        radio_layout.addWidget(self.auto_mode_radio); radio_layout.addWidget(self.manual_mode_radio); radio_layout.addStretch()
        
        self.params_container = QWidget(); form_layout = QFormLayout(self.params_container)
        form_layout.setContentsMargins(0, 10, 0, 0)
        form_layout.addRow("最大軸向負載 (來自模擬):", self.auto_force_display)

        self.manual_inputs['m'] = CustomDoubleSpinBox(decimals=2, value=200.0, suffix=" kg", minimum=0, maximum=10000)
        self.manual_inputs['a_max_g'] = CustomDoubleSpinBox(decimals=3, value=0.2, suffix=" g", minimum=0, maximum=10)
        form_layout.addRow("移動件重量 (m):", self.manual_inputs['m'])
        form_layout.addRow("最高加速度 (a_max):", self.manual_inputs['a_max_g'])
        
        layout.addLayout(radio_layout); layout.addWidget(self.params_container)
        self.auto_mode_radio.setChecked(True)
        return group

    def _create_general_params_group(self):
        group = QGroupBox("2. 通用運動與工程參數")
        layout = QFormLayout(group)
        self.eng_param_inputs['v_max'] = CustomDoubleSpinBox(decimals=1, value=100.0, suffix=" mm/s", minimum=0, maximum=10000)
        self.eng_param_inputs['theta'] = CustomDoubleSpinBox(decimals=1, value=90.0, suffix=" °", minimum=0, maximum=90)
        self.eng_param_inputs['mu'] = CustomDoubleSpinBox(decimals=3, value=config.DRIVE_DEFAULT_FRICTION_COEFF, minimum=0, maximum=1)
        self.eng_param_inputs['f_w'] = CustomDoubleSpinBox(decimals=2, value=1.1, minimum=1.0, maximum=5.0)
        self.eng_param_inputs['eta_screw'] = CustomDoubleSpinBox(decimals=1, value=90.0, minimum=0, maximum=100, suffix=" %")
        self.eng_param_inputs['eta_pulley'] = CustomDoubleSpinBox(decimals=1, value=95.0, minimum=0, maximum=100, suffix=" %")
        self.fw_label = QLabel()
        
        layout.addRow("最高線速度 (v_max):", self.eng_param_inputs['v_max'])
        layout.addRow("安裝角度 (θ):", self.eng_param_inputs['theta'])
        layout.addRow("摩擦係數 (μ):", self.eng_param_inputs['mu'])
        layout.addRow("負荷係數 (f_w):", self.eng_param_inputs['f_w'])
        layout.addRow("", self.fw_label)
        layout.addRow("螺桿效率 (η_screw):", self.eng_param_inputs['eta_screw'])
        layout.addRow("傳動效率 (η_pulley):", self.eng_param_inputs['eta_pulley'])
        return group

    def _create_motion_profile_group(self):
        group = QGroupBox("3. 運動剖面 (Motion Profile)")
        form = QFormLayout(group)
        profile_map = {
            't_ua': ("加速上昇 (t_ua) (s):", 6.0), 't_uc': ("等速上昇 (t_uc) (s):", 60.0), 't_ud': ("減速上昇 (t_ud) (s):", 30.0),
            't_da': ("加速下降 (t_da) (s):", 6.0), 't_dc': ("等速下降 (t_dc) (s):", 60.0), 't_dd': ("減速下降 (t_dd) (s):", 30.0),
            't_s':  ("靜止 (t_s) (s):", 108.0)
        }
        for key, (label, default) in profile_map.items():
            spinbox = CustomDoubleSpinBox(decimals=3, value=default, minimum=0, maximum=10000)
            self.motion_profile_inputs[key] = spinbox
            form.addRow(label, spinbox)
        return group

    def _create_part_selection_group(self):
        group = QGroupBox("4. 零件選型與減速比")
        self.part_selection_group = group
        form = QFormLayout(group)
        self.motor_combo = CustomComboBox(); self.screw_combo = CustomComboBox()
        self.driving_pulley_combo = CustomComboBox(); self.driven_pulley_combo = CustomComboBox()
        self.direct_ratio_radio = QRadioButton("直接輸入減速比"); self.pulley_ratio_radio = QRadioButton("透過皮帶輪選擇")
        self.ratio_input = CustomDoubleSpinBox(decimals=2, value=config.DRIVE_DEFAULT_REDUCTION_RATIO_I, minimum=0.1, maximum=10.0)
        self.ratio_label = QLabel()
        
        form.addRow("馬達型號:", self.motor_combo)
        form.addRow("螺桿型號:", self.screw_combo)
        form.addRow(self.direct_ratio_radio); form.addRow("減速比 (i):", self.ratio_input)
        form.addRow(self.pulley_ratio_radio)
        form.addRow("主動輪 (馬達端):", self.driving_pulley_combo); form.addRow("從動輪 (螺桿端):", self.driven_pulley_combo)
        form.addRow("", self.ratio_label)
        self.direct_ratio_radio.setChecked(True)
        return group

    def _create_life_requirements_box(self):
        box = QGroupBox("5. 壽命需求 (選填)")
        grid = QGridLayout(box)
        self.life_req_inputs['R_h'] = CustomDoubleSpinBox(decimals=1, value=8.0, minimum=0, maximum=24)
        self.life_req_inputs['R_d'] = CustomDoubleSpinBox(decimals=0, value=250.0, minimum=0, maximum=365)
        self.life_req_inputs['R_y'] = CustomDoubleSpinBox(decimals=1, value=5.0, minimum=0)
        self.life_req_inputs['Aval'] = CustomDoubleSpinBox(decimals=1, value=80.0, minimum=0, maximum=100, suffix=" %")
        self.life_hours_label = QLabel()
        
        grid.addWidget(QLabel("每日運轉 (R_h) (hr):"), 0, 0); grid.addWidget(self.life_req_inputs['R_h'], 0, 1)
        grid.addWidget(QLabel("每年運轉 (R_d) (day):"), 0, 2); grid.addWidget(self.life_req_inputs['R_d'], 0, 3)
        grid.addWidget(QLabel("運轉年數 (R_y) (yr):"), 1, 0); grid.addWidget(self.life_req_inputs['R_y'], 1, 1)
        grid.addWidget(QLabel("稼動率 (Aval) (%):"), 1, 2); grid.addWidget(self.life_req_inputs['Aval'], 1, 3)
        grid.addWidget(self.life_hours_label, 2, 0, 1, 4)
        return box

    def _create_calculation_control_group(self):
        group = QGroupBox("6. 執行計算"); layout = QVBoxLayout(group)
        self.calculate_btn = QPushButton("開始計算與校核"); layout.addWidget(self.calculate_btn)
        return group

    def _create_results_display_group(self):
        group = QGroupBox("計算結果預覽"); form = QFormLayout(group)
        self.result_labels['F_max'] = QLabel("N/A"); self.result_labels['T_motor_req'] = QLabel("N/A")
        self.result_labels['F_eq'] = QLabel("N/A"); self.result_labels['L_t'] = QLabel("N/A")
        self.result_labels['L_T'] = QLabel("N/A"); self.result_labels['C_ac'] = QLabel("N/A")
        
        form.addRow("最大軸向負載 (F_max):", self.result_labels['F_max'])
        form.addRow("需求馬達扭矩 (T_motor_req):", self.result_labels['T_motor_req'])
        form.addRow("平均軸向負載 (F_eq):", self.result_labels['F_eq'])
        form.addRow("需求動額定負荷 (C_ac):", self.result_labels['C_ac'])
        form.addRow("估算壽命 (L_t):", self.result_labels['L_t'])
        form.addRow("需求壽命 (L_T):", self.result_labels['L_T'])
        return group

    def _create_part_spec_display_group(self):
        group = QGroupBox("選定零件規格"); layout = QVBoxLayout(group)
        self.part_spec_display = QTextEdit(); self.part_spec_display.setReadOnly(True)
        self.part_spec_display.setText("請從左側選擇零件..."); layout.addWidget(self.part_spec_display)
        return group

    def _create_motion_profile_display_group(self):
        group = QGroupBox("運動剖面總覽"); layout = QVBoxLayout(group)
        self.motion_profile_table = QTableWidget(7, 4)
        self.motion_profile_table.setHorizontalHeaderLabels(["階段", "軸向負荷 (N)", "時間 (%)", "時間 (s)"])
        self.motion_profile_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.motion_profile_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.motion_profile_table)
        return group

    def _connect_signals(self):
        self.auto_mode_radio.toggled.connect(self._on_mode_changed)
        self.calculate_btn.clicked.connect(self._on_calculate_clicked)
        self.motor_combo.currentIndexChanged.connect(self._update_part_spec_display)
        self.screw_combo.currentIndexChanged.connect(self._update_part_spec_display)
        self.driving_pulley_combo.currentIndexChanged.connect(self._update_ratio_input_display)
        self.driven_pulley_combo.currentIndexChanged.connect(self._update_ratio_input_display)
        self.direct_ratio_radio.toggled.connect(self._update_ratio_input_display)
        self.eng_param_inputs['v_max'].valueChanged.connect(self._update_load_factor_display)
        for widget in self.life_req_inputs.values(): widget.valueChanged.connect(self._update_life_hours_display)

    def _on_mode_changed(self, is_auto_mode):
        form = self.params_container.layout()
        auto_label_widget = form.labelForField(self.auto_force_display)
        self.auto_force_display.setVisible(is_auto_mode)
        if auto_label_widget: auto_label_widget.setVisible(is_auto_mode)
        
        for widget in self.manual_inputs.values():
            label_widget = form.labelForField(widget)
            widget.setVisible(not is_auto_mode)
            if label_widget: label_widget.setVisible(not is_auto_mode)
            
        self._update_force_input_display()
        if not self._is_loading_data: self.mode_changed.emit(self.get_current_mode())

    def _update_force_input_display(self):
        if self.auto_mode_radio.isChecked():
            text = f"<strong>{self.auto_required_axial_force:,.2f} N</strong>" if self.auto_required_axial_force is not None else "<font color='red'>N/A</font>"
            self.auto_force_display.setText(text)

    def _update_all_displays(self):
        self._update_ratio_input_display()
        self._update_load_factor_display()
        self._update_life_hours_display()
        self._update_part_spec_display()

    def _update_load_factor_display(self):
        v_max_mm_s = self.eng_param_inputs['v_max'].value()
        f_w = self.drive_engine.get_load_factor(v_max_mm_s)
        self.eng_param_inputs['f_w'].setValue(f_w)
        v_max_m_min = v_max_mm_s * 0.06
        suggestion = "低速" if v_max_m_min < 15 else "中速" if v_max_m_min < 60 else "高速"
        self.fw_label.setText(f"建議值: {f_w:.2f} ({suggestion}應用)")

    def _update_life_hours_display(self):
        params = {key: w.value() for key, w in self.life_req_inputs.items()}
        l_t = self.drive_engine._calculate_required_life_hours(params)
        self.life_hours_label.setText(f"計算需求壽命 (L_T): {l_t:,.0f} 小時")

    def _update_ratio_input_display(self, _=None):
        is_direct_ratio = self.direct_ratio_radio.isChecked()
        self.ratio_input.setVisible(is_direct_ratio)
        self.driving_pulley_combo.setVisible(not is_direct_ratio)
        self.driven_pulley_combo.setVisible(not is_direct_ratio)
        self.ratio_label.setVisible(not is_direct_ratio)

        form_layout = self.part_selection_group.layout()
        for i in range(form_layout.rowCount()):
            label_widget = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
            field_widget = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
            if label_widget and field_widget:
                widget = field_widget.widget()
                if widget == self.ratio_input:
                    label_widget.widget().setVisible(is_direct_ratio)
                elif widget in [self.driving_pulley_combo, self.driven_pulley_combo]:
                    label_widget.widget().setVisible(not is_direct_ratio)
        
        if not is_direct_ratio and self.driving_pulley_combo.currentData() and self.driven_pulley_combo.currentData():
            driving_teeth = self.driving_pulley_combo.currentData().get('teeth', 1)
            driven_teeth = self.driven_pulley_combo.currentData().get('teeth', 1)
            ratio = driven_teeth / driving_teeth if driving_teeth > 0 else 1.0
            self.ratio_label.setText(f"匹配減速比: {ratio:.2f}")
        else:
            self.ratio_label.setText("匹配減速比: N/A")

    def load_initial_data(self):
        # --- MODIFIED: Added data normalization step to align db keys with v2.0 ---
        motors_raw, _ = self.db_manager.get_all_motors()
        if motors_raw:
            self.motor_data = []
            for m in motors_raw:
                self.motor_data.append({
                    **m,
                    'T_motor_rated': m.get('rated_torque_nm', 0),
                    'T_motor_peak': m.get('max_torque_nm', 0),
                    'n_motor_rated': m.get('rated_speed_rpm', 0),
                    'n_motor_max': m.get('max_speed_rpm', 0),
                })
        self.motor_combo.clear(); self.motor_combo.addItem("--- 請選擇馬達 ---", None)
        if self.motor_data: [self.motor_combo.addItem(f"{m['brand']} - {m['model']}", m) for m in self.motor_data]
        
        screws_raw, _ = self.db_manager.get_all_screws()
        if screws_raw:
            self.screw_data = []
            for s in screws_raw:
                self.screw_data.append({
                    **s,
                    'P_h': s.get('lead_mm', 0),
                    'C_a': s.get('ca_n', 0),
                })
        self.screw_combo.clear(); self.screw_combo.addItem("--- 請選擇螺桿 ---", None)
        if self.screw_data: [self.screw_combo.addItem(f"{s['brand']} - {s['model']} (Lead: {s['P_h']}mm)", s) for s in self.screw_data]

        self.pulley_data, _ = self.db_manager.get_all_pulleys()
        self.driving_pulley_combo.clear(); self.driving_pulley_combo.addItem("--- 請選擇 ---", None)
        self.driven_pulley_combo.clear(); self.driven_pulley_combo.addItem("--- 請選擇 ---", None)
        if self.pulley_data:
            [self.driving_pulley_combo.addItem(f"{p['brand']} - {p['model']} ({p['teeth']}T)", p) for p in self.pulley_data]
            [self.driven_pulley_combo.addItem(f"{p['brand']} - {p['model']} ({p['teeth']}T)", p) for p in self.pulley_data]

    def _update_part_spec_display(self, _=None):
        html = "<style>td { padding: 2px 5px; }</style><table>"
        motor = self.motor_combo.currentData(); screw = self.screw_combo.currentData()
        
        if motor:
            html += f"<tr><td colspan='3'><b>馬達: {motor['brand']} - {motor['model']}</b></td></tr>"
            html += f"<tr><td>額定扭矩</td><td>T_motor_rated</td><td>{motor.get('T_motor_rated', 'N/A')} Nm</td></tr>"
            html += f"<tr><td>峰值扭矩</td><td>T_motor_peak</td><td>{motor.get('T_motor_peak', 'N/A')} Nm</td></tr>"
            html += f"<tr><td>額定轉速</td><td>n_motor_rated</td><td>{motor.get('n_motor_rated', 'N/A')} rpm</td></tr>"
            html += f"<tr><td>最高轉速</td><td>n_motor_max</td><td>{motor.get('n_motor_max', 'N/A')} rpm</td></tr>"
        if screw:
            html += f"<tr><td colspan='3'><b>螺桿: {screw['brand']} - {screw['model']}</b></td></tr>"
            html += f"<tr><td>導程</td><td>P_h</td><td>{screw.get('P_h', 'N/A')} mm</td></tr>"
            html += f"<tr><td>動額定負荷</td><td>C_a</td><td>{screw.get('C_a', 'N/A'):,} N</td></tr>"
        
        html += "</table>"
        self.part_spec_display.setHtml(html if any([motor, screw]) else "請從左側選擇零件...")
        self._adjust_widget_height_to_content(self.part_spec_display)

    def _update_motion_profile_table(self, result):
        profiles = result.get('profiles', {}); load_profile = profiles.get('load_profile', {})
        total_time = sum(self.motion_profile_inputs[key].value() for key in self.motion_profile_inputs)
        if total_time <= 0: return

        stages_map = {'ua': "加速上昇", 'uc': "等速上昇", 'ud': "減速上昇",
                      'da': "加速下降", 'dc': "等速下降", 'dd': "減速下降", 's': "靜止"}

        for i, (stage_key, stage_name) in enumerate(stages_map.items()):
            load = load_profile.get(f"F_{stage_key}", 0)
            time_s = self.motion_profile_inputs[f"t_{stage_key}"].value()
            time_percent = (time_s / total_time) * 100 if total_time > 0 else 0
            
            self.motion_profile_table.setItem(i, 0, QTableWidgetItem(stage_name))
            self.motion_profile_table.setItem(i, 1, QTableWidgetItem(f"{load:,.2f}"))
            self.motion_profile_table.setItem(i, 2, QTableWidgetItem(f"{time_percent:.1f}"))
            self.motion_profile_table.setItem(i, 3, QTableWidgetItem(f"{time_s:.2f}"))

        self._adjust_widget_height_to_content(self.motion_profile_table)

    def _adjust_widget_height_to_content(self, widget):
        if isinstance(widget, QTextEdit):
            doc_height = widget.document().size().height(); widget.setFixedHeight(int(doc_height) + 15)
        elif isinstance(widget, QTableWidget):
            header_height = widget.horizontalHeader().height(); content_height = sum([widget.rowHeight(i) for i in range(widget.rowCount())])
            widget.setFixedHeight(header_height + content_height + 15)

    def _on_calculate_clicked(self):
        params = self.get_parameters()
        if self.get_current_mode() == 'auto':
            if self.auto_required_axial_force is None:
                QMessageBox.warning(self, "缺少參數", "自動模式下缺少有效的軸向力輸入。"); return
            params['max_axial_force_from_sim'] = self.auto_required_axial_force
        
        result = self.drive_engine.calculate(params)
        self._update_results_display(result)

    def _update_results_display(self, result):
        self.last_calc_results = result
        
        # Display Warnings
        warnings = result.get('warnings', [])
        if warnings:
            msg = "計算完成，但存在以下警告：\n\n" + "\n".join([f"- {w['message']}" for w in warnings])
            QMessageBox.warning(self, "計算警告", msg)
        
        # Update result labels
        results_data = result.get('results', {})
        self.result_labels['F_max'].setText(f"<b>{results_data.get('F_max', 0):,.2f} N</b>")
        self.result_labels['T_motor_req'].setText(f"<b>{results_data.get('T_motor_req', 0):.3f} Nm</b>")
        self.result_labels['F_eq'].setText(f"{results_data.get('F_eq', 0):,.2f} N")
        self.result_labels['C_ac'].setText(f"<b>{results_data.get('C_ac', 0):,.0f} N</b>")

        L_t = results_data.get('L_t', 0); L_T = results_data.get('L_T', 0)
        life_color = "green" if L_t >= L_T and L_T > 0 else "black" if L_T == 0 else "red"
        self.result_labels['L_t'].setText(f"<b style='color:{life_color};'>{L_t:,.0f} 小時</b>")
        self.result_labels['L_T'].setText(f"{L_T:,.0f} 小時")

        self._update_motion_profile_table(result)
        self._update_part_spec_display()
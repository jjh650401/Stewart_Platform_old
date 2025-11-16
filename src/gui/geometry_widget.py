# D:\Python_Programs\Stewart_Platform\src\gui\geometry_widget.py

import numpy as np
from PyQt6.QtWidgets import (QWidget, QFormLayout, QGroupBox, QPushButton, 
                             QLabel, QDoubleSpinBox, QComboBox, QHBoxLayout, QCheckBox,
                             QRadioButton, QSizePolicy, QTextEdit, QVBoxLayout, QGridLayout)
from PyQt6.QtCore import Qt
from src.core import config
from src.utils.custom_widgets import CustomDoubleSpinBox, CustomComboBox  # 導入自訂類別

class GeometryWidget:
    """
    [v1.20 最終佈局修正版]
    為輸入框設定固定寬度，並為按鈕佈局加入彈性空間。
    重構 calculation_group 的佈局以解決寬度問題。
    """
    def create_input_row(self, parent_widget, name, label_text, form_layout):
        spinbox = CustomDoubleSpinBox(parent_widget)
        spinbox.setDecimals(2)
        spinbox.setSingleStep(config.DEFAULT_INPUT_STEP)
        spinbox.setRange(*config.DEFAULT_INPUT_RANGE)
        spinbox.setObjectName(name)
        spinbox.setFixedWidth(config.UI_INPUT_FIELD_WIDTH)
        form_layout.addRow(label_text, spinbox)
        return spinbox

    def create_angle_input_row(self, parent_widget, name, label_text, form_layout):
        row_label = QLabel(label_text, parent_widget)
        
        spinbox = CustomDoubleSpinBox(parent_widget)
        spinbox.setDecimals(1)
        spinbox.setSingleStep(5.0)
        spinbox.setRange(0.0, 90.0)
        spinbox.setSuffix(" °")
        spinbox.setFixedWidth(config.UI_INPUT_FIELD_WIDTH)

        combo = CustomComboBox(parent_widget)
        presets = [text for text, value in config.ANGLE_LIMIT_PRESETS]
        combo.addItems(presets)

        container = QWidget(parent_widget)
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(spinbox)
        hbox.addWidget(combo, 1)
        form_layout.addRow(row_label, container)

        return spinbox, combo, row_label, container

    def create_6dof_base_group(self, parent_widget):
        group = QGroupBox("固定平台", parent_widget)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        inputs = {}
        labels = {}
        
        inputs['Df'] = self.create_input_row(parent_widget, "Df", "較大弦長 (Df, mm):", form)
        inputs['df'] = self.create_input_row(parent_widget, "df", "較小弦長 (df, mm):", form)
        
        labels['Ra'] = QLabel("N/A", parent_widget)
        labels['Ra'].setStyleSheet("font-weight: bold;")
        form.addRow("固定平台半徑 (Ra, mm):", labels['Ra'])
        
        return group, inputs, labels

    def create_6dof_mobile_group(self, parent_widget):
        group = QGroupBox("活動平台", parent_widget)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        inputs = {}
        labels = {}
        
        inputs['Dm'] = self.create_input_row(parent_widget, "Dm", "較大弦長 (Dm, mm):", form)
        inputs['dm'] = self.create_input_row(parent_widget, "dm", "較小弦長 (dm, mm):", form)
        
        labels['Rb'] = QLabel("N/A", parent_widget)
        labels['Rb'].setStyleSheet("font-weight: bold;")
        form.addRow("活動平台半徑 (Rb, mm):", labels['Rb'])
        
        return group, inputs, labels

    def create_3dof_base_group(self, parent_widget):
        group = QGroupBox("固定平台 (等腰三角形)", parent_widget)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        inputs = {}
        labels = {}
        
        inputs['D1'] = self.create_input_row(parent_widget, "D1", "底邊長度 (D1, mm):", form)
        inputs['D2'] = self.create_input_row(parent_widget, "D2", "三角形高 (D2, mm):", form)
        
        labels['Ra'] = QLabel("N/A", parent_widget)
        labels['Ra'].setStyleSheet("font-weight: bold;")
        form.addRow("外接圓半徑 (Ra, mm):", labels['Ra'])
        
        return group, inputs, labels

    def create_3dof_mobile_group(self, parent_widget):
        group = QGroupBox("活動平台 (等腰三角形)", parent_widget)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        inputs = {}
        labels = {}

        inputs['d1'] = self.create_input_row(parent_widget, "d1", "底邊長度 (d1, mm):", form)
        inputs['d2'] = self.create_input_row(parent_widget, "d2", "三角形高 (d2, mm):", form)
        
        labels['Rb'] = QLabel("N/A", parent_widget)
        labels['Rb'].setStyleSheet("font-weight: bold;")
        form.addRow("外接圓半徑 (Rb, mm):", labels['Rb'])
        
        return group, inputs, labels

    def create_actuator_group(self, parent_widget):
        group = QGroupBox("通用與電動缸參數", parent_widget)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(10, 10, 10, 10)
        form.setVerticalSpacing(10)
        
        inputs = {}; labels = {}; combos = {}; radios = {}; angle_limit_widgets = []

        inputs['L'] = self.create_input_row(parent_widget, "L", "最小長度 (L, mm):", form)
        inputs['s'] = self.create_input_row(parent_widget, "s", "可用行程 (s, mm):", form)
        inputs['s_buffer'] = self.create_input_row(parent_widget, "s_buffer", "安全裕量 (s_buffer, mm):", form)
        
        labels['s_mech'] = QLabel("N/A", parent_widget); labels['s_mech'].setStyleSheet("font-weight: bold;")
        form.addRow("總機械行程 (s_mech, mm):", labels['s_mech'])
        
        form.addRow(QLabel("--- 關節物理限制 ---", parent_widget))
        
        enable_angle_limits_checkbox = QCheckBox("啟用關節角度限制", parent_widget)
        form.addRow(enable_angle_limits_checkbox)

        inputs['base_joint_limit'], combos['base_joint_limit'], r, c = self.create_angle_input_row(parent_widget, "base_joint_limit", "固定平台關節最大擺角:", form)
        angle_limit_widgets.extend([r, c])

        inputs['platform_joint_limit'], combos['platform_joint_limit'], r, c = self.create_angle_input_row(parent_widget, "platform_joint_limit", "活動平台關節最大擺角:", form)
        angle_limit_widgets.extend([r, c])
        
        joint_style_label = QLabel("活動平台關節安裝方式:", parent_widget)
        radios['top_mount'] = QRadioButton("上置式 (法線朝上)", parent_widget)
        radios['bottom_mount'] = QRadioButton("下置式 (法線朝下)", parent_widget)
        radios['bottom_mount'].setChecked(True)
        
        style_container = QWidget(parent_widget); hbox = QHBoxLayout(style_container)
        hbox.setContentsMargins(0,0,0,0); hbox.addWidget(radios['top_mount']); hbox.addWidget(radios['bottom_mount']); hbox.addStretch()
        form.addRow(joint_style_label, style_container)
        angle_limit_widgets.extend([joint_style_label, style_container])
        
        return { "group": group, "inputs": inputs, "labels": labels, "combos": combos, "radios": radios, "angle_limit_widgets": angle_limit_widgets, "enable_angle_limits_checkbox": enable_angle_limits_checkbox }

    def create_calculation_group(self, parent_widget, is_3dof=False):
        # --- 第一個區塊：按鈕區 ---
        button_group = QGroupBox("平台計算與分析", parent_widget)
        button_v_layout = QVBoxLayout(button_group)
        button_v_layout.setContentsMargins(10, 10, 10, 10)
        button_v_layout.setSpacing(8)

        confirm_btn = QPushButton("確認所有幾何參數", parent_widget)
        calc_h_btn = QPushButton("計算零位", parent_widget)
        calc_h_btn.setEnabled(False)
        # [修改] 移除按鈕前的 addStretch() 以實現靠左對齊
        btn_layout1 = QHBoxLayout(); btn_layout1.addWidget(confirm_btn); btn_layout1.addWidget(calc_h_btn); btn_layout1.addStretch()
        button_v_layout.addLayout(btn_layout1)
        buttons = {'confirm_all': confirm_btn, 'H': calc_h_btn}

        analyze_op_btn = QPushButton("分析可用工作空間", parent_widget); analyze_op_btn.setEnabled(False)
        analyze_mech_btn = QPushButton("分析機械極限空間", parent_widget); analyze_mech_btn.setEnabled(False)
        # [修改] 移除按鈕前的 addStretch() 以實現靠左對齊
        btn_layout2 = QHBoxLayout(); btn_layout2.addWidget(analyze_op_btn); btn_layout2.addWidget(analyze_mech_btn); btn_layout2.addStretch()
        button_v_layout.addLayout(btn_layout2)
        buttons['analyze_op'] = analyze_op_btn; buttons['analyze_mech'] = analyze_mech_btn

        analyze_angles_btn = QPushButton("分析節點擺角範圍", parent_widget); analyze_angles_btn.setEnabled(False)
        # [修改] 移除按鈕前的 addStretch() 以實現靠左對齊
        btn_layout3 = QHBoxLayout(); btn_layout3.addWidget(analyze_angles_btn); btn_layout3.addStretch()
        button_v_layout.addLayout(btn_layout3)
        buttons['analyze_angles'] = analyze_angles_btn

        # --- 第二個區塊：結果顯示區 ---
        results_group = QGroupBox("計算結果", parent_widget)
        grid_layout = QGridLayout(results_group)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        labels = {}
        labels['H'] = QLabel("N/A", parent_widget); labels['H'].setStyleSheet("font-weight: bold;"); labels['H'].setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(QLabel("零位高度 (H, mm):"), 0, 0); grid_layout.addWidget(labels['H'], 0, 1)
        
        labels['h_initial'] = QLabel("N/A", parent_widget); labels['h_initial'].setStyleSheet("font-weight: bold; color: #555;"); labels['h_initial'].setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(QLabel("初始高度 (h, mm):"), 1, 0); grid_layout.addWidget(labels['h_initial'], 1, 1)

        if not is_3dof:
            labels['phase_angle'] = QLabel("N/A", parent_widget); labels['phase_angle'].setStyleSheet("font-weight: bold; color: #555;"); labels['phase_angle'].setAlignment(Qt.AlignmentFlag.AlignLeft)
            grid_layout.addWidget(QLabel("幾何相位角 (Δθ, °):"), 2, 0); grid_layout.addWidget(labels['phase_angle'], 2, 1)

        base_angle_label = QLabel("零位姿態所需固定平台擺角 (°):", parent_widget)
        platform_angle_label = QLabel("零位姿態所需活動平台擺角 (°):", parent_widget)
        labels['zero_pose_base_angle'] = QLabel("N/A", parent_widget); labels['zero_pose_base_angle'].setStyleSheet("font-weight: bold; color: #0055A4;"); labels['zero_pose_base_angle'].setAlignment(Qt.AlignmentFlag.AlignLeft)
        labels['zero_pose_platform_angle'] = QLabel("N/A", parent_widget); labels['zero_pose_platform_angle'].setStyleSheet("font-weight: bold; color: #0055A4;"); labels['zero_pose_platform_angle'].setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(base_angle_label, 3, 0); grid_layout.addWidget(labels['zero_pose_base_angle'], 3, 1)
        grid_layout.addWidget(platform_angle_label, 4, 0); grid_layout.addWidget(labels['zero_pose_platform_angle'], 4, 1)

        results_display_group = QGroupBox("節點擺角範圍分析結果 (°)", parent_widget)
        results_layout = QVBoxLayout(results_display_group)
        displays = {}
        displays['angle_results_display'] = QTextEdit(parent_widget); displays['angle_results_display'].setReadOnly(True)
        displays['angle_results_display'].setText("請先執行分析...")
        displays['angle_results_display'].setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        displays['angle_results_display'].textChanged.connect(lambda: displays['angle_results_display'].setFixedHeight(int(displays['angle_results_display'].document().size().height() + 10)))
        results_layout.addWidget(displays['angle_results_display'])
        
        grid_layout.addWidget(results_display_group, 5, 0, 1, 2)
        grid_layout.setColumnStretch(1, 1)

        # 最終返回兩個獨立的 GroupBox 以及相關資料
        return button_group, results_group, buttons, labels, displays
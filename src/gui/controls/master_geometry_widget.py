# D:\Python_Programs\Stewart_Platform\src\gui\controls\master_geometry_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QStackedWidget, 
                             QGroupBox, QHBoxLayout, QRadioButton, QSizePolicy)
from PyQt6.QtCore import pyqtSignal

from src.gui.controls.six_dof_widget import SixDofWidget
from src.gui.controls.three_dof_widget import ThreeDofWidget
from src.gui.geometry_widget import GeometryWidget

class MasterGeometryWidget(QWidget):
    """
    幾何參數設計的主控制元件。
    [重構後] 職責為建立並管理特定平台的 UI 元件。
    """
    platform_type_changed = pyqtSignal(str)
    parameters_confirmed = pyqtSignal(dict)
    # --- MODIFIED: calculation_requested is no longer used for 6-DOF, but kept for 3-DOF forwarding ---
    calculation_requested = pyqtSignal()
    op_workspace_analysis_requested = pyqtSignal()
    mech_workspace_analysis_requested = pyqtSignal()
    parameter_changed = pyqtSignal()
    angle_range_analysis_requested = pyqtSignal()
    # --- ADDED: New signal to forward the result from the refactored SixDofWidget ---
    calculation_finished = pyqtSignal(bool, str)

    # --- MODIFIED: Update constructor to accept core_engine from MainWindow ---
    def __init__(self, core_engine, parent=None):
        super().__init__(parent)
        
        self.setMinimumWidth(500)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        # --- MODIFIED: Pass core_engine to the child widgets that need it ---
        # We create a ui_builder instance here as per the original design pattern
        ui_builder = GeometryWidget()
        self.six_dof_widget = SixDofWidget(ui_builder, core_engine, self)
        # Assuming ThreeDofWidget will also be refactored to accept core_engine eventually
        self.three_dof_widget = ThreeDofWidget(ui_builder, self) # Kept original for now

        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        selector_group = QGroupBox("平台類型選擇")
        selector_layout = QHBoxLayout(selector_group)
        
        self.radio_6dof = QRadioButton("六自由度平台 (6-DOF)")
        self.radio_3dof = QRadioButton("三自由度平台 (3-DOF)")
        self.radio_6dof.setChecked(True)

        selector_layout.addWidget(self.radio_6dof)
        selector_layout.addWidget(self.radio_3dof)
        selector_layout.addStretch()
        
        main_layout.addWidget(selector_group)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.six_dof_widget)
        self.stacked_widget.addWidget(self.three_dof_widget)
        
        main_layout.addWidget(self.stacked_widget)

    def _connect_signals(self):
        self.radio_6dof.toggled.connect(self._on_platform_changed)

        # --- 將 6-DOF Widget 的訊號轉發出去 ---
        self.six_dof_widget.parameters_confirmed.connect(self.parameters_confirmed.emit)
        
        # --- REMOVED: This is the line that caused the AttributeError crash ---
        # self.six_dof_widget.calculation_requested.connect(self.calculation_requested.emit)
        # --- ADDED: Forward the new signal from the child to the parent (MainWindow) ---
        self.six_dof_widget.calculation_finished.connect(self.calculation_finished.emit)

        self.six_dof_widget.op_workspace_analysis_requested.connect(self.op_workspace_analysis_requested.emit)
        self.six_dof_widget.mech_workspace_analysis_requested.connect(self.mech_workspace_analysis_requested.emit)
        self.six_dof_widget.parameter_changed.connect(self.parameter_changed.emit)
        self.six_dof_widget.angle_range_analysis_requested.connect(self.angle_range_analysis_requested.emit)

        # --- 將 3-DOF Widget 的訊號轉發出去 (保持不變) ---
        self.three_dof_widget.parameters_confirmed.connect(self.parameters_confirmed.emit)
        self.three_dof_widget.calculation_requested.connect(self.calculation_requested.emit)
        self.three_dof_widget.op_workspace_analysis_requested.connect(self.op_workspace_analysis_requested.emit)
        self.three_dof_widget.mech_workspace_analysis_requested.connect(self.mech_workspace_analysis_requested.emit)
        self.three_dof_widget.parameter_changed.connect(self.parameter_changed.emit)
        self.three_dof_widget.angle_range_analysis_requested.connect(self.angle_range_analysis_requested.emit)

    def _on_platform_changed(self, checked):
        if checked:
            self.stacked_widget.setCurrentIndex(0)
            self.platform_type_changed.emit("6-DOF")
        else:
            self.stacked_widget.setCurrentIndex(1)
            self.platform_type_changed.emit("3-DOF")
            
    def get_current_platform_widget(self):
        return self.stacked_widget.currentWidget()

    def set_platform_type(self, platform_type: str):
        if platform_type == "6-DOF":
            self.radio_6dof.setChecked(True)
        elif platform_type == "3-DOF":
            self.radio_3dof.setChecked(True)
# D:\Python_Programs\Stewart_Platform\src\gui\main_window.py

# ==============================================================================
# [修改註記 - v2.3-kinematics-fix (UI 單位修正)]
# 日期: 2025-11-17
# 修改者: AI 協作
# ------------------------------------------------------------------------------
# 修改重點:
# 1. [Bug修復] on_workspace_analysis_finished: 移除了多餘的 np.rad2deg 角度轉換。
#    - 原因: analysis_widget.py 已包含顯示層的單位轉換邏輯。
#    - 解決: 防止「雙重轉換」導致角度數值膨脹至非物理範圍 (如 +/- 1000度)。
# ==============================================================================

# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# UI層、核心層的所有長度參數的儲存、傳遞與計算皆以 mm 為準。
# 詳情請參閱《基礎背景與規則 v5 優化版.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

import sys
import json
import itertools
import numpy as np
from scipy.spatial.transform import Rotation
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar,
                             QLabel, QPushButton, QMessageBox, QFileDialog, QTabWidget,
                             QApplication, QGroupBox, QStyle, QStackedWidget, QProgressDialog,
                             QSizePolicy, QScrollArea, QSplitter)
from PyQt6.QtGui import QAction, QIcon, QFont, QActionGroup
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSlot

from src.gui.controls.master_geometry_widget import MasterGeometryWidget
from src.gui.controls.analysis_widget import AnalysisWidget
from src.gui.controls.dynamics_widget import DynamicsWidget
from src.gui.controls.drive_system_widget import DriveSystemWidget
from src.gui.pyvista_widget import PyVistaWidget
from src.core.kinematics import CoreEngine
from src.core.state_manager import StateManager
from src.core.analysis_engine import AnalysisEngine
from src.core.report_generator import ReportGenerator
from src.core.database_manager import DatabaseManager
from src.gui.controls.database_management_widget import DatabaseManagementWidget
from src.core import config

class MainWindow(QMainWindow):
    BASE_TITLE = "史都華平台設計與模擬工具"

    def __init__(self):
        super().__init__()
        
        font = QFont(config.FONT_UI_NAME, config.FONT_UI_SIZE)
        self.setFont(font)

        self.state_manager = StateManager()
        self.core_engine = CoreEngine()
        self.db_manager = DatabaseManager()
        
        self.analysis_thread = None
        self.analysis_worker = None
        
        self.master_geometry_widget = MasterGeometryWidget(self.core_engine, self)
        
        self.dynamics_widget = DynamicsWidget(self)
        self.drive_system_widget = DriveSystemWidget(self.db_manager, self)
        self.pv_window = PyVistaWidget()

        self.six_dof_controls = AnalysisWidget(self, dof_list=['x', 'y', 'z', 'pitch', 'roll', 'yaw'])
        self.three_dof_controls = AnalysisWidget(self, dof_list=['z', 'pitch', 'roll'])
        
        self._is_loading = False
        self.standard_mode_geometry = None

        self.init_ui()
        self.connect_signals()
        self.on_new_project()
        
    def showEvent(self, event):
        super().showEvent(event)
        pass

    def screenChanged(self, screen):
        super().screenChanged(screen)
        if self.main_stack.currentIndex() == 0:
            self._center_and_adjust_to_content()
            
    def _center_and_adjust_to_content(self):
        screen_geometry = self.screen().availableGeometry()
        center_point = screen_geometry.center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def init_ui(self):
        self.setWindowTitle(self.BASE_TITLE)
        self._create_menu_bar()
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)
        standard_mode_page = self._create_standard_mode_page()
        drive_system_page = self.drive_system_widget
        self.main_stack.addWidget(standard_mode_page)
        self.main_stack.addWidget(drive_system_page)
        self.status_label = QLabel("準備就緒"); self.setStatusBar(QStatusBar(self)); self.statusBar().addWidget(self.status_label)

    def _create_standard_mode_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        margin = config.UI_WINDOW_CONTENT_MARGIN
        layout.setContentsMargins(margin, margin, margin, margin)
        
        self.standard_mode_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.standard_mode_splitter.setHandleWidth(1)
        self.standard_mode_splitter.setStyleSheet("QSplitter::handle { background-color: lightgray; } QSplitter::handle:hover { background-color: darkgray; }")
        self.left_panel_stack = QStackedWidget()
        scroll_area_geo = QScrollArea(); scroll_area_geo.setWidgetResizable(True); scroll_area_geo.setWidget(self.master_geometry_widget)
        scroll_area_dyn = QScrollArea(); scroll_area_dyn.setWidgetResizable(True); scroll_area_dyn.setWidget(self.dynamics_widget)
        self.left_panel_stack.addWidget(scroll_area_geo)
        self.left_panel_stack.addWidget(scroll_area_dyn)
        self.controls_stack = QStackedWidget()
        self.controls_stack.addWidget(self.six_dof_controls)
        self.controls_stack.addWidget(self.three_dof_controls)
        self.standard_mode_splitter.addWidget(self.left_panel_stack)
        self.standard_mode_splitter.addWidget(self.controls_stack)
        
        self.standard_mode_splitter.setSizes([config.UI_SPLITTER_LEFT_WIDTH, config.UI_SPLITTER_RIGHT_WIDTH])
        
        layout.addWidget(self.standard_mode_splitter)
        return page

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("檔案(&F)")
        self.new_action = QAction("新建專案(&N)", self); self.new_action.triggered.connect(self.on_new_project); file_menu.addAction(self.new_action)
        self.load_action = QAction("讀取專案(&O)...", self); self.load_action.triggered.connect(self.on_load_project); file_menu.addAction(self.load_action)
        self.save_action = QAction("儲存專案(&S)", self); self.save_action.triggered.connect(self.on_save_project); file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        self.load_drive_design_action = QAction("讀取驅動系統設計...", self); self.load_drive_design_action.triggered.connect(self.on_load_drive_design); file_menu.addAction(self.load_drive_design_action)
        self.save_drive_design_action = QAction("儲存驅動系統設計...", self); self.save_drive_design_action.triggered.connect(self.on_save_drive_design); file_menu.addAction(self.save_drive_design_action)
        file_menu.addSeparator()
        self.report_action = QAction("生成設計報告(&R)...", self); self.report_action.triggered.connect(self.on_generate_report_requested); file_menu.addAction(self.report_action)
        file_menu.addSeparator()
        self.exit_action = QAction("結束程式(&X)", self); self.exit_action.triggered.connect(self.close); file_menu.addAction(self.exit_action)
        self.mode_action_group = QActionGroup(self); self.mode_action_group.setExclusive(True)
        self.action_geo = QAction("幾何參數設計", self, checkable=True); self.mode_action_group.addAction(self.action_geo)
        self.action_dyn = QAction("動力學分析", self, checkable=True); self.mode_action_group.addAction(self.action_dyn)
        self.action_drive = QAction("驅動系統計算", self, checkable=True); self.mode_action_group.addAction(self.action_drive)
        menu_bar.addAction(self.action_geo); menu_bar.addAction(self.action_dyn); menu_bar.addAction(self.action_drive)
        self.action_geo.setChecked(True)
        db_menu = menu_bar.addMenu("資料庫維護")
        db_manage_action = QAction("零件資料庫管理...", self); db_manage_action.triggered.connect(self._open_database_manager); db_menu.addAction(db_manage_action)
        window_menu = menu_bar.addMenu("視窗(&W)")
        self.toggle_3d_preview_action = QAction("3D 預覽視窗(&V)", self, checkable=True); self.toggle_3d_preview_action.setChecked(config.STARTUP_SHOW_3D_PREVIEW); self.toggle_3d_preview_action.toggled.connect(self._on_toggle_3d_preview_action); window_menu.addAction(self.toggle_3d_preview_action)
        window_menu.addSeparator()
        view_control_menu = window_menu.addMenu("視角控制(&C)")
        actions_info = [("iso", "等角視角"), ("xy", "俯視角"), ("xz", "正視角"), ("yz", "側視角"),("separator", ""), ("undo", "撤銷"),("previous", "返回"), ("restore_saved", "恢復"),("refresh", "刷新"),]
        for name, text in actions_info:
            if name == "separator": view_control_menu.addSeparator(); continue
            action = QAction(text, self); action.triggered.connect(lambda _, n=name: self._on_toolbar_action_triggered(n)); view_control_menu.addAction(action)

    def _open_database_manager(self):
        dialog = DatabaseManagementWidget(self.db_manager, self)
        dialog.exec()
        self.drive_system_widget.load_initial_data()

    def connect_signals(self):
        self.action_geo.triggered.connect(lambda: self._switch_mode('geo'))
        self.action_dyn.triggered.connect(lambda: self._switch_mode('dyn'))
        self.action_drive.triggered.connect(lambda: self._switch_mode('drive'))
        self.drive_system_widget.mode_changed.connect(self._update_file_menu_state)
        self.master_geometry_widget.platform_type_changed.connect(self.on_platform_type_changed)
        self.master_geometry_widget.parameters_confirmed.connect(self.on_parameters_confirmed)
        
        self.master_geometry_widget.calculation_requested.connect(self.on_calculation_requested)
        self.master_geometry_widget.calculation_finished.connect(self._on_geometry_calculation_finished)

        self.master_geometry_widget.parameter_changed.connect(self._on_parameter_changed)
        self.master_geometry_widget.op_workspace_analysis_requested.connect(lambda: self.on_workspace_analysis_requested('operational'))
        self.master_geometry_widget.mech_workspace_analysis_requested.connect(lambda: self.on_workspace_analysis_requested('mechanical'))
        self.master_geometry_widget.angle_range_analysis_requested.connect(self.on_angle_range_analysis_requested)
        self.six_dof_controls.pose_changed.connect(self.on_pose_changed)
        self.three_dof_controls.pose_changed.connect(self.on_pose_changed)
        self.dynamics_widget.analysis_requested.connect(self._on_current_force_analysis_requested)
        self.dynamics_widget.global_analysis_requested.connect(self.on_global_force_analysis_requested)
        self.pv_window.view_changed.connect(self._mark_as_dirty)
        self.pv_window.visibilityChanged.connect(self._on_3d_window_visibility_changed)
        
        if hasattr(self, 'analysis_widget'):
            self.analysis_widget.toggle_angle_visualization.connect(self.pv_window.update_angle_visualization)
            self.analysis_widget.toggle_node_coordinate_visualization.connect(self._on_toggle_node_coordinate_visualization)
            self.analysis_widget.workspace_analysis_requested.connect(self.on_workspace_analysis_requested)
            self.analysis_widget.pose_changed.connect(self.on_pose_changed)
    
    @pyqtSlot(bool, str)
    def _on_geometry_calculation_finished(self, success, message):
        if success:
            self._update_ui_after_successful_calculation(from_load=False)
        else:
            self.status_label.setText(f"幾何計算失敗: {message}")

    def _switch_mode(self, mode_key):
        if mode_key in ['geo', 'dyn']:
            total_width = config.UI_SPLITTER_LEFT_WIDTH + config.UI_SPLITTER_RIGHT_WIDTH + 30
            self.resize(total_width, self.sizeHint().height())
            self._center_and_adjust_to_content()
            
            self.main_stack.setCurrentIndex(0)
            self.left_panel_stack.setCurrentIndex(0 if mode_key == 'geo' else 1)
            self.pv_window.setVisible(self.toggle_3d_preview_action.isChecked())
            self._update_file_menu_state('auto')

        elif mode_key == 'drive':
            if self.main_stack.currentIndex() == 0:
                self.standard_mode_geometry = self.geometry()
            self.main_stack.setCurrentIndex(1)
            self.pv_window.setVisible(False)
            self.resize(config.DRIVE_DASHBOARD_WIDTH, config.DRIVE_DASHBOARD_HEIGHT)
            self._center_and_adjust_to_content()
            current_drive_mode = self.drive_system_widget.get_current_mode()
            self._update_file_menu_state(current_drive_mode)
            if self.state_manager.get_global_force_result():
                forces = self.state_manager.get_global_force_result().get('forces')
                if forces: self.drive_system_widget.set_required_axial_force(max(abs(f) for f in forces))
            else: self.drive_system_widget.set_required_axial_force(None)

    @pyqtSlot(str)
    def _update_file_menu_state(self, drive_mode: str):
        is_in_drive_tab = self.action_drive.isChecked()
        is_manual_drive_mode = is_in_drive_tab and drive_mode == 'manual'
        is_auto_drive_mode = is_in_drive_tab and drive_mode == 'auto'
        is_standard_mode = not is_in_drive_tab
        
        self.load_action.setEnabled(is_standard_mode or is_auto_drive_mode)
        self.save_action.setEnabled(is_standard_mode or is_auto_drive_mode)
        self.load_drive_design_action.setEnabled(is_manual_drive_mode)
        self.save_drive_design_action.setEnabled(is_manual_drive_mode)

    @pyqtSlot(bool)
    def _on_toggle_3d_preview_action(self, checked):
        if self.action_drive.isChecked(): self.pv_window.setVisible(False); return
        # [修改] 新增邏輯：如果視窗是首次從隱藏變為顯示，強制進行一次重建
        is_first_show = checked and not self.pv_window.isVisible()
        if checked != self.pv_window.isVisible(): self.pv_window.setVisible(checked)
        if is_first_show:
            self.update_3d_view(rebuild=True, reset_view=False)
        if checked: self.pv_window.activateWindow()

    @pyqtSlot(bool)
    def _on_3d_window_visibility_changed(self, visible):
        if hasattr(self, 'toggle_3d_preview_action') and self.toggle_3d_preview_action.isChecked() != visible:
            self.toggle_3d_preview_action.blockSignals(True); self.toggle_3d_preview_action.setChecked(visible); self.toggle_3d_preview_action.blockSignals(False)
    
    def on_save_drive_design(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "儲存驅動系統設計", "", "Drive System Designs (*.dsd)")
        if not filepath: return
        params = self.drive_system_widget.get_parameters()
        success = self.core_engine.save_drive_design_to_file(filepath, params)
        if success: self.status_label.setText(f"驅動系統設計已儲存至 {filepath}")
        else: QMessageBox.critical(self, "錯誤", "驅動系統設計存檔失敗。")

    def on_load_drive_design(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "讀取驅動系統設計", "", "Drive System Designs (*.dsd)")
        if not filepath: return
        data = self.core_engine.load_drive_design_from_file(filepath)
        if data:
            self.drive_system_widget.set_parameters(data)
            self.status_label.setText(f"已從 {filepath} 讀取驅動系統設計。")
        else: QMessageBox.critical(self, "錯誤", "讀取驅動系統設計失敗。")

    def closeEvent(self, event):
        if self.analysis_thread and self.analysis_thread.isRunning():
            if self.analysis_worker: self.analysis_worker.stop_analysis()
            self.analysis_thread.quit(); self.analysis_thread.wait(1000)
        if self.state_manager.is_dirty():
            reply = QMessageBox.question(self, '關閉程式', "您有未儲存的變更，是否要儲存？", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                if not self.on_save_project(): event.ignore(); return
            elif reply == QMessageBox.StandardButton.Cancel: event.ignore(); return
        self.pv_window.close(); self.db_manager.close(); QApplication.instance().quit(); event.accept()

    def _on_toolbar_action_triggered(self, name: str):
        if not self.pv_window.isVisible(): self.pv_window.setVisible(True)
        self.pv_window.activateWindow()
        if name == 'iso': self.update_3d_view(rebuild=True, reset_view=True)
        elif name == 'restore_saved': self.pv_window.restore_saved_camera_view()
        elif name == 'refresh': self._on_refresh_view_requested()
        else: self.pv_window.handle_view_change(name)

    def get_current_geo_widget(self):
        return self.master_geometry_widget.get_current_platform_widget()

    @pyqtSlot()
    def _on_refresh_view_requested(self):
        self.update_3d_view(rebuild=True, reset_view=False)
        self.status_label.setText("3D 視圖已刷新。")

    @pyqtSlot(str)
    def on_platform_type_changed(self, platform_type: str):
        if not self._is_loading: self.on_new_project(platform_type=platform_type)
        
    @pyqtSlot()
    @pyqtSlot(str)
    def on_new_project(self, platform_type: str = "6-DOF"):
        self.standard_mode_geometry = None
        self._is_loading = True
        self.state_manager.reset(); self.state_manager.set_platform_type(platform_type)
        self.master_geometry_widget.set_platform_type(platform_type)
        self.controls_stack.setCurrentIndex(0 if platform_type == "6-DOF" else 1)
        current_geo_widget = self.get_current_geo_widget()
        self.core_engine.reset(); self.core_engine.platform_type = platform_type
        all_params = self.core_engine.get_all_parameters()
        current_geo_widget.set_input_values(all_params); current_geo_widget.reset_all_calculated_values()
        self.dynamics_widget.set_values(all_params); self.dynamics_widget.reset_results()
        self.six_dof_controls.reset_workspace_display(); self.three_dof_controls.reset_workspace_display()
        self.pv_window.clear_and_init_scene(); self._set_clean()
        self.status_label.setText(f"已建立新專案 ({platform_type})。")
        self._initial_split_set = False
        self._switch_mode('geo'); self.action_geo.setChecked(True)
        self._is_loading = False
        
    def on_parameters_confirmed(self, params: dict):
        self.core_engine.reset_calculated_parameters(); self.state_manager.set_workspace_limits(None); self.state_manager.set_mechanical_workspace_limits(None)
        for name, value in params.items(): self.core_engine.update_parameter(name, value)
        self.core_engine.calculate_target('Ra'); self.core_engine.calculate_target('Rb'); self.core_engine.calculate_target('s_mech')
        current_widget = self.get_current_geo_widget()
        current_widget.update_display_value('Ra', self.core_engine.get_parameter('Ra')); current_widget.update_display_value('Rb', self.core_engine.get_parameter('Rb')); current_widget.update_display_value('s_mech', self.core_engine.get_parameter('s_mech'))
        can_calc_h = all(self.core_engine.get_parameter(p) for p in ['Ra', 'Rb', 's_mech', 'L'])
        buttons = current_widget.get_buttons()
        if 'H' in buttons: buttons['H'].setEnabled(can_calc_h)
        if can_calc_h: self.status_label.setText("參數已確認，可計算零位。")

    def on_calculation_requested(self, from_load: bool = False):
        if self.core_engine.platform_type == "6-DOF" and not from_load:
            print("DEBUG: on_calculation_requested called for 6-DOF, but handled by child widget. Ignoring.")
            return
        
        success, message = self.core_engine.calculate_platform_geometry()
        if not success:
            if not from_load:
                QMessageBox.warning(self, "求解失敗", f"無法計算出一個有效的零位姿態。\n{message}");
            return
        
        self._update_ui_after_successful_calculation(from_load)

    def _update_ui_after_successful_calculation(self, from_load: bool = False):
        h_val = self.core_engine.get_parameter('H')
        current_widget = self.get_current_geo_widget()
        if h_val and h_val > 0:
            current_widget.update_display_value('H', h_val, 'mm')
            current_widget.update_display_value('h_initial', self.core_engine.calculate_initial_height(), 'mm')
            
            # [修正] 刪除了錯誤呼叫已廢棄函式 get_phase_angle_deg 的程式碼
            
            current_widget.update_display_value('zero_pose_base_angle', self.core_engine.zero_pose_base_angle, 'deg')
            current_widget.update_display_value('zero_pose_platform_angle', self.core_engine.zero_pose_platform_angle, 'deg')
            
            buttons = current_widget.get_buttons()
            buttons['analyze_op'].setEnabled(True)
            buttons['analyze_mech'].setEnabled(True)
            
            self.dynamics_widget.reset_results()
            
            if not from_load:
                self.status_label.setText(f"零位求解完成! H = {h_val:.2f} mm")
                self.update_3d_view(rebuild=True, reset_view=not any(self.pv_window.platform_actors.values()))
                self._mark_as_dirty()
        elif not from_load:
            QMessageBox.warning(self, "求解失敗", "無法計算出一個有效的零位姿態。")

    def on_workspace_analysis_requested(self, analysis_type: str):
        # [重構] 使用 QThread 執行工作空間分析
        if self.analysis_thread and self.analysis_thread.isRunning():
            QMessageBox.warning(self, "提示", "另一個分析正在進行中，請稍候。")
            return

        text = '可用' if analysis_type == 'operational' else '機械極限'
        self.progress_dialog = QProgressDialog(f"正在分析 {text} 空間...", "取消", 0, config.ALGO_LHS_SAMPLES * 10, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.setMinimumDuration(500)

        # 準備任務包
        task_data = {
            'core_params': self.core_engine.params.copy(),
            'platform_type': self.state_manager.get_platform_type(),
            'space_type': analysis_type
        }

        self.analysis_thread = QThread()
        self.analysis_worker = AnalysisEngine()
        self.analysis_worker.moveToThread(self.analysis_thread)

        # 連接信號
        self.progress_dialog.canceled.connect(self.analysis_worker.stop_analysis)
        self.analysis_worker.progress_updated.connect(self.on_analysis_progress)
        self.analysis_worker.workspace_analysis_finished.connect(lambda result, at=analysis_type: self.on_workspace_analysis_finished(result, at))
        
        self.analysis_thread.started.connect(lambda: self.analysis_worker.run_workspace_analysis(task_data))
        self.analysis_thread.finished.connect(self._cleanup_analysis_thread)
        
        self.progress_dialog.show()
        self.analysis_thread.start()
        
    @pyqtSlot(dict, str)
    def on_workspace_analysis_finished(self, result_package, analysis_type):
        # [新增] 處理來自背景執行緒的工作空間分析結果
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

        success = result_package.get('success', False)
        result = result_package.get('result', '未知錯誤')

        if success:
            limits = result
            if analysis_type == 'operational': 
                self.state_manager.set_workspace_limits(limits)
                self.get_current_geo_widget().get_buttons()['analyze_angles'].setEnabled(True)
            else: 
                self.state_manager.set_mechanical_workspace_limits(limits)
            
            # [修正] 移除此處的單位轉換。analysis_widget.py 會負責將弧度轉換為度數進行顯示。
            # 避免發生雙重轉換導致數值異常 (e.g. +/- 1000度)。
            self.controls_stack.currentWidget().update_workspace_display(limits, analysis_type, self.core_engine.get_parameter('H'))
            
            text = '可用' if analysis_type == 'operational' else '機械極限'
            self.status_label.setText(f"{text} 空間分析完成.")
            self.update_3d_view(rebuild=False)
            self._mark_as_dirty()
        else:
            if analysis_type == 'operational': self.state_manager.set_workspace_limits(None)
            else: self.state_manager.set_mechanical_workspace_limits(None)
            
            if '取消' not in result:
                 QMessageBox.warning(self, "分析失敗", f"無法執行分析。\n原因: {result}")
            self.status_label.setText(f"分析失敗: {result}")

        if self.analysis_thread:
            self.analysis_thread.quit()

    def update_3d_view(self, rebuild: bool = False, reset_view: bool = False, override_pose: dict = None):
        current_controls = self.controls_stack.currentWidget()
        show_angles = hasattr(current_controls, 'show_angles_checkbox') and current_controls.show_angles_checkbox.isChecked(); show_coords = hasattr(current_controls, 'show_coords_checkbox') and current_controls.show_coords_checkbox.isChecked()
        pose_data, platform_params, labels = self._get_full_pose_and_geometry_data(override_pose=override_pose, show_coords=show_coords)
        if not self.pv_window.isVisible() and not rebuild: return
        QApplication.processEvents()
        if not pose_data:
            if rebuild: self.pv_window.rebuild_scene({}, {}, {}, reset_view); return
        if rebuild: self.pv_window.rebuild_scene(platform_params, pose_data, labels, reset_view)
        else: self.pv_window.update_platform_pose(platform_params, pose_data, labels)
        if show_angles:
            current_pose = override_pose or {name: ctrl['slider'].value()/config.SLIDER_PRECISION_FACTOR for name, ctrl in current_controls.sliders.items()}
            viz_data = self.core_engine.get_current_joint_angles_and_vectors(current_pose); self.pv_window.update_angle_visualization(viz_data, True)
        else: self.pv_window.update_angle_visualization(None, False)

    def _get_full_pose_and_geometry_data(self, override_pose: dict = None, show_coords: bool = False):
        base_nodes, mobile_nodes_local = self.core_engine._get_canonical_nodes()
        if not base_nodes or not mobile_nodes_local: return None, None, None
        
        platform_params = {'nodes_3d_base': base_nodes, 'nodes_3d_mobile': mobile_nodes_local}
        
        h_val = self.core_engine.get_parameter('H')
        if not h_val or h_val <= 0: return None, platform_params, {}
        
        pose_ui = override_pose or {name: ctrl['slider'].value()/config.SLIDER_PRECISION_FACTOR for name, ctrl in self.controls_stack.currentWidget().sliders.items()}
        
        offset_mm = self.core_engine.zero_pose_offset
        if self.core_engine.platform_type == '6-DOF':
            position = [offset_mm['x'] + pose_ui.get('x', 0), offset_mm['y'] + pose_ui.get('y', 0), h_val + pose_ui.get('z', 0)]
            r = Rotation.from_euler('ZXY', [pose_ui.get('yaw', 0), pose_ui.get('pitch', 0), -pose_ui.get('roll', 0)], degrees=True)
        else: 
            position = [0, 0, h_val + pose_ui.get('z', 0)]
            r = Rotation.from_euler('ZXY', [0, pose_ui.get('pitch', 0), -pose_ui.get('roll', 0)], degrees=True)
            
        pose_data = {'position': position, 'orientation': r.as_quat()}
        
        mobile_nodes_world = r.apply(mobile_nodes_local) + position
        labels = self._generate_node_labels(base_nodes, mobile_nodes_world, show_coords)
        return pose_data, platform_params, labels
    
    def _generate_node_labels(self, base_nodes, mobile_nodes_world, show_coords):
        labels = {}
        base_names, mobile_names = [], []
        if self.core_engine.platform_type == '6-DOF':
            base_names = [f"A{i+1}" for i in range(len(base_nodes))]
            mobile_names = [f"B{i+1}" for i in range(len(mobile_nodes_world))]
        elif self.core_engine.platform_type == '3-DOF':
            base_names = ['A1', 'A3', 'A5']
            mobile_names = ['B1', 'B3', 'B5']

        if show_coords:
            labels['base'] = [f"{n}\nX:{p[0]:.1f} Y:{p[1]:.1f} Z:{p[2]:.1f}" for n, p in zip(base_names, base_nodes)]
            labels['mobile'] = [f"{n}\nX:{p[0]:.1f} Y:{p[1]:.1f} Z:{p[2]:.1f}" for n, p in zip(mobile_names, mobile_nodes_world)]
        else:
            labels['base'] = base_names
            labels['mobile'] = mobile_names
        return labels
        
    def on_save_project(self):
        project_path = self.state_manager.get_project_path()
        if not project_path:
            filepath, _ = QFileDialog.getSaveFileName(self, "儲存專案", "", "JSON Files (*.json)");
            if not filepath: return False
            project_path = filepath
        
        drive_params = self.drive_system_widget.get_parameters()
        self.core_engine.update_drive_system_data(drive_params)
        
        dynamics_params = self.dynamics_widget.get_values();
        for name, value in dynamics_params.items(): self.core_engine.update_parameter(name, value)
        self.core_engine.update_parameter('view_params', self.pv_window.get_camera_params())
        if self.core_engine.save_to_file(project_path):
            self.state_manager.set_project_path(project_path)
            self.status_label.setText(f"專案已儲存至 {project_path}")
            self._set_clean()
            return True
        else:
            QMessageBox.critical(self, "錯誤", "專案存檔失敗.")
            return False

    def on_load_project(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "讀取專案", "", "JSON Files (*.json)");
        if not filepath: return
        try:
            self._is_loading = True
            data = self.core_engine.load_from_file(filepath)
            if data is None: raise IOError("無法從檔案讀取數據。")
            loaded_type = data.get('platform_type', '6-DOF')
            self.on_new_project(platform_type=loaded_type)
            self._is_loading = True
            
            status = self.core_engine.load_parameters(data)
            
            drive_data = data.get('drive_system_data', {})
            if drive_data: self.drive_system_widget.set_parameters(drive_data)
            self.state_manager.set_project_path(filepath)
            all_params = self.core_engine.get_all_parameters()
            self.get_current_geo_widget().set_input_values(all_params)
            self.dynamics_widget.set_values(all_params)
            self.on_parameters_confirmed(all_params)
            
            if self.core_engine.get_parameter('H') and self.core_engine.get_parameter('H') > 0:
                self.on_calculation_requested(from_load=True)
            
            self._set_clean()
            self.status_label.setText(f"已從 {filepath} 讀取專案。")
            self.update_3d_view(rebuild=True, reset_view=False)
            view_params_to_set = self.core_engine.get_parameter('view_params')
            if view_params_to_set: self.pv_window.set_camera_params(view_params_to_set)

            if status == 'conversion_done':
                QMessageBox.information(self, "提示", "已成功載入舊版(公尺單位)專案檔，並自動轉換為毫米(mm)單位。\n建議您立即重新儲存，以升級此專案檔。")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"專案讀檔失敗: {e}")
            self.on_new_project()
        finally:
            self._is_loading = False
            total_width = config.UI_SPLITTER_LEFT_WIDTH + config.UI_SPLITTER_RIGHT_WIDTH + 30
            self.resize(total_width, self.sizeHint().height())
            self._center_and_adjust_to_content()
            
    @pyqtSlot()
    def on_generate_report_requested(self):
        if self.core_engine.get_parameter('H') is None or self.core_engine.get_parameter('H') <= 0:
            QMessageBox.warning(self, "無法生成報告", "請先載入或計算出一個有效的專案。"); return
        default_filename = "Stewart_Platform_Report.pdf"; project_path = self.state_manager.get_project_path()
        if project_path: default_filename = f"{project_path.split('/')[-1].split('\\')[-1].split('.')[0]}_Report.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "儲存報告", default_filename, "PDF Files (*.pdf)")
        if not filepath: self.status_label.setText("報告生成已取消。"); return
        project_data = {'project_path': self.state_manager.get_project_path() or "N/A", 'platform_type': self.state_manager.get_platform_type(), 'core_params': self.core_engine.get_all_parameters(), 'phase_angle': self.core_engine.get_parameter('phase_angle_deg') if self.state_manager.get_platform_type() == '6-DOF' else None, 'workspace_limits': self.state_manager.get_workspace_limits(), 'mechanical_workspace_limits': self.state_manager.get_mechanical_workspace_limits(), 'global_force_result': self.state_manager.get_global_force_result(), 'angle_range_result': self.state_manager.get_angle_range_result()}
        self.status_label.setText("正在生成 PDF 報告..."); QApplication.processEvents()
        generator = ReportGenerator(project_data, filepath); success, message = generator.generate_report()
        if success: self.status_label.setText(f"報告已成功儲存至 {filepath}"); QMessageBox.information(self, "成功", f"設計報告已成功儲存！")
        else: self.status_label.setText("報告生成失敗。"); QMessageBox.critical(self, "錯誤", f"生成報告時發生錯誤:\n{message}")

    def on_global_force_analysis_requested(self):
        if self.analysis_thread and self.analysis_thread.isRunning(): QMessageBox.warning(self, "提示", "另一個分析正在進行中，請稍候。"); return
        workspace_limits = self.state_manager.get_workspace_limits()
        if not workspace_limits: QMessageBox.warning(self, "無法分析", "請先成功分析可用工作空間。"); return
        self.progress_dialog = QProgressDialog("準備開始全域出力智慧搜尋...", "取消", 0, 100, self); self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal); self.progress_dialog.setAutoClose(True); self.progress_dialog.setMinimumDuration(0)
        task_data = {'workspace_limits': workspace_limits, 'platform_type': self.state_manager.get_platform_type(), 'core_params': self.core_engine.get_all_parameters(), 'is_static_only': self.dynamics_widget.is_static_analysis_only()}
        self.analysis_thread = QThread(); self.analysis_worker = AnalysisEngine(); self.analysis_worker.moveToThread(self.analysis_thread)
        self.progress_dialog.canceled.connect(self.analysis_worker.stop_analysis); self.analysis_worker.progress_updated.connect(self.on_analysis_progress); self.analysis_worker.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_thread.started.connect(lambda: self.analysis_worker.run_global_analysis(task_data)); self.analysis_thread.finished.connect(self._cleanup_analysis_thread); self.progress_dialog.show(); self.analysis_thread.start()

    @pyqtSlot(int, int, str)
    def on_analysis_progress(self, value, total, message):
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            if self.progress_dialog.maximum() != total: self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(value); self.progress_dialog.setLabelText(message)

    @pyqtSlot(dict)
    def on_analysis_finished(self, result):
        if hasattr(self, 'progress_dialog') and self.progress_dialog: self.progress_dialog.setValue(self.progress_dialog.maximum()); self.progress_dialog = None
        if result.get('success'):
            self.state_manager.set_global_force_result(result); self.dynamics_widget.set_global_result(result.get('forces'), result.get('pose_ui')); self.status_label.setText(result.get('message', '分析完成。'))
            forces = result.get('forces');
            if forces: self.drive_system_widget.set_required_axial_force(max(abs(f) for f in forces))
            worst_pose_ui = result.get('pose_ui');
            if worst_pose_ui: self.controls_stack.currentWidget().on_global_analysis_pose_update(worst_pose_ui); self.dynamics_widget.set_current_result(result.get('forces'), worst_pose_ui, is_valid=True)
        else:
            self.state_manager.set_global_force_result(None); self.drive_system_widget.set_required_axial_force(None); self.dynamics_widget.set_global_result(None, None)
            if '取消' not in result.get('message', ''): QMessageBox.warning(self, "分析失敗", result.get('message', '未知錯誤。'))
            self.status_label.setText(result.get('message', '分析失敗。'))
        if self.analysis_thread: self.analysis_thread.quit()
        
    @pyqtSlot(dict)
    def on_angle_analysis_finished(self, result):
        if hasattr(self, 'progress_dialog') and self.progress_dialog: self.progress_dialog.setValue(self.progress_dialog.maximum()); self.progress_dialog = None
        self.state_manager.set_angle_range_result(result)
        self.get_current_geo_widget().display_angle_range_results(result)
        self.status_label.setText(result.get('message', '分析完成。'))
        if self.analysis_thread: self.analysis_thread.quit()

    @pyqtSlot()
    def _cleanup_analysis_thread(self):
        if self.analysis_thread: self.analysis_thread.quit(); self.analysis_thread.wait()
        self.analysis_thread = None; self.analysis_worker = None

    @pyqtSlot()
    def on_pose_changed(self):
        if not self._is_loading: self.update_3d_view()
        
    @pyqtSlot()
    def _on_current_force_analysis_requested(self):
        if self._is_loading: return
        if not (self.core_engine.get_parameter('H') and self.core_engine.get_parameter('H') > 0): QMessageBox.warning(self, "無法計算", "請先成功計算零位高度 H。"); return
        pose_ui = {name: ctrl['slider'].value()/config.SLIDER_PRECISION_FACTOR for name, ctrl in self.controls_stack.currentWidget().sliders.items()}
        forces = self.core_engine.calculate_force_for_ui_pose(pose_ui)
        is_display_valid = self.core_engine.is_pose_valid(pose_ui, 'operational'); self.dynamics_widget.set_current_result(forces, pose_ui, is_display_valid)
        if self.sender() == self.dynamics_widget.analyze_button: self.status_label.setText("當前姿態出力計算完成。"); self._mark_as_dirty()
    
    @pyqtSlot()
    def on_angle_range_analysis_requested(self):
        if self.analysis_thread and self.analysis_thread.isRunning(): QMessageBox.warning(self, "提示", "另一個分析正在進行中，請稍候。"); return
        workspace_limits = self.state_manager.get_workspace_limits();
        if not workspace_limits: QMessageBox.warning(self, "無法分析", "請先成功分析可用工作空間。"); return
        self.progress_dialog = QProgressDialog("準備開始節點擺角範圍分析...", "取消", 0, 100, self); self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal); self.progress_dialog.setAutoClose(True); self.progress_dialog.setMinimumDuration(0)
        task_data = {'workspace_limits': workspace_limits, 'platform_type': self.state_manager.get_platform_type(), 'core_params': self.core_engine.get_all_parameters()}
        self.analysis_thread = QThread(); self.analysis_worker = AnalysisEngine(); self.analysis_worker.moveToThread(self.analysis_thread)
        self.progress_dialog.canceled.connect(self.analysis_worker.stop_analysis); self.analysis_worker.progress_updated.connect(self.on_analysis_progress); self.analysis_worker.angle_analysis_completed.connect(self.on_angle_analysis_finished)
        self.analysis_thread.started.connect(lambda: self.analysis_worker.run_angle_range_analysis(task_data)); self.analysis_thread.finished.connect(self._cleanup_analysis_thread); self.progress_dialog.show(); self.analysis_thread.start()
        
    def _mark_as_dirty(self):
        if self._is_loading: return
        if not self.state_manager.is_dirty(): self.state_manager.set_dirty(True); self._update_window_title()
    
    def _on_parameter_changed(self):
        if self._is_loading: return
        self._mark_as_dirty(); current_widget = self.get_current_geo_widget(); current_widget.reset_all_calculated_values()
        self.state_manager.set_workspace_limits(None); self.state_manager.set_mechanical_workspace_limits(None)
        self.six_dof_controls.reset_workspace_display(); self.three_dof_controls.reset_workspace_display(); self.dynamics_widget.reset_results()

    def _set_clean(self):
        self.state_manager.set_dirty(False); self._update_window_title()

    def _update_window_title(self):
        title = self.BASE_TITLE
        project_path = self.state_manager.get_project_path()
        if project_path: title += f" - [{project_path}]"
        if self.state_manager.is_dirty(): title += " (*)"
        self.setWindowTitle(title)
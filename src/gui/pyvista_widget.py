# D:\Python_Programs\Stewart_Platform\src\gui\pyvista_widget.py

import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np
from scipy.spatial.transform import Rotation
from PyQt6.QtCore import pyqtSignal

from src.core import config

# --- MODIFIED: Added scaling factor for unit conversion ---
# 3D繪圖的內部單位統一為公尺(m)，此常數用於將傳入的毫米(mm)數據轉換為公尺。
MM_TO_M = 0.001

class PyVistaWidget(QtInteractor):
    view_changed = pyqtSignal()
    visibilityChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotter = self
        
        self.platform_actors = { 
            'base': None, 'mobile': None, 'legs': None, 
            'base_labels': None, 'mobile_labels': None, 
            'base_center': None, 'mobile_center': None,
            'angle_vectors': [], 'angle_labels': []
        }
        self.platform_meshes = { 'base': None, 'mobile': None, 'legs': None }
        
        self.view_history_stack = []
        self.origin_camera_params = None
        self.is_in_preset_view_sequence = False
        self.saved_camera_params = None

        self.iren.add_observer("EndInteractionEvent", self._on_view_interaction_end)
        self.clear_and_init_scene()

    def showEvent(self, event):
        super().showEvent(event)
        self.visibilityChanged.emit(True)

    def closeEvent(self, event):
        self.visibilityChanged.emit(False)
        self.hide()
        event.accept()

    def clear_and_init_scene(self):
        self.plotter.clear()
        self.platform_actors = {key: [] if isinstance(self.platform_actors.get(key), list) else None for key in self.platform_actors}
        self.platform_meshes = {key: None for key in self.platform_meshes}
        self.view_history_stack.clear()
        self.origin_camera_params = None
        
        self.plotter.add_axes(interactive=True)
        self.plotter.set_background(config.STYLE_BACKGROUND_COLOR)
        
    def rebuild_scene(self, params: dict, pose: dict, labels: dict, reset_view: bool):
        self.clear_and_init_scene()

        # --- MODIFIED: Scale incoming mm data to meters for rendering ---
        base_nodes_mm = np.array(params.get('nodes_3d_base', []))
        mobile_nodes_local_mm = np.array(params.get('nodes_3d_mobile', []))
        
        if base_nodes_mm.size == 0 or mobile_nodes_local_mm.size == 0:
            self.plotter.camera_position = 'iso'
            return

        base_nodes = base_nodes_mm * MM_TO_M
        mobile_nodes_local = mobile_nodes_local_mm * MM_TO_M
        position = np.array(pose.get('position', [0,0,0])) * MM_TO_M
        # --- END MODIFICATION ---

        r = Rotation.from_quat(pose.get('orientation', [0,0,0,1]))
        mobile_nodes_world = r.apply(mobile_nodes_local) + position
        
        self.platform_meshes['base'] = self._create_lines_from_nodes(base_nodes)
        self.platform_meshes['mobile'] = self._create_lines_from_nodes(mobile_nodes_world)
        self.platform_meshes['legs'] = self._create_leg_lines(base_nodes, mobile_nodes_world)
        
        self.platform_actors['base'] = self.plotter.add_mesh(self.platform_meshes['base'], color=config.STYLE_BASE_FRAME_COLOR, line_width=config.STYLE_BASE_FRAME_LINE_WIDTH)
        self.platform_actors['mobile'] = self.plotter.add_mesh(self.platform_meshes['mobile'], color=config.STYLE_MOBILE_FRAME_COLOR, line_width=config.STYLE_MOBILE_FRAME_LINE_WIDTH)
        self.platform_actors['legs'] = self.plotter.add_mesh(self.platform_meshes['legs'], color=config.STYLE_LEG_COLOR, line_width=config.STYLE_LEG_LINE_WIDTH)
        
        label_style = {'point_size': config.STYLE_NODE_POINT_SIZE, 'font_size': config.STYLE_NODE_LABEL_FONT_SIZE, 'text_color': config.STYLE_NODE_LABEL_FONT_COLOR, 'shape_opacity': 0.5, 'render_points_as_spheres': True, 'always_visible': True}
        self.platform_actors['base_labels'] = self.plotter.add_point_labels(np.array(base_nodes), labels.get('base', []), name='base_labels', shape_color=config.STYLE_NODE_LABEL_BASE_BG, **label_style)
        self.platform_actors['mobile_labels'] = self.plotter.add_point_labels(np.array(mobile_nodes_world), labels.get('mobile', []), name='mobile_labels', shape_color=config.STYLE_NODE_LABEL_MOBILE_BG, **label_style)
        
        base_center_pos = np.mean(np.array(base_nodes), axis=0)
        # The label text logic is now correct: base_center_pos is in meters, *1000 converts it to mm for display.
        base_center_label_text = f"Base Center\nX: {base_center_pos[0]*1000:.1f} Y: {base_center_pos[1]*1000:.1f} Z: {base_center_pos[2]*1000:.1f}"
        self.platform_actors['base_center'] = self.plotter.add_point_labels(base_center_pos, [base_center_label_text], name='base_center_label', point_size=config.STYLE_CENTER_POINT_SIZE, font_size=config.STYLE_CENTER_LABEL_FONT_SIZE, text_color=config.STYLE_CENTER_LABEL_COLOR_BASE, point_color=config.STYLE_CENTER_LABEL_COLOR_BASE, shape_opacity=0.0, always_visible=True, render_points_as_spheres=True)

        mobile_center_pos = np.mean(np.array(mobile_nodes_world), axis=0)
        mobile_center_label_text = f"Motion Center\nX: {mobile_center_pos[0]*1000:.1f} Y: {mobile_center_pos[1]*1000:.1f} Z: {mobile_center_pos[2]*1000:.1f}"
        self.platform_actors['mobile_center'] = self.plotter.add_point_labels(mobile_center_pos, [mobile_center_label_text], name='mobile_center_label', point_size=config.STYLE_CENTER_POINT_SIZE, font_size=config.STYLE_CENTER_LABEL_FONT_SIZE, text_color=config.STYLE_CENTER_LABEL_COLOR_MOBILE, point_color=config.STYLE_CENTER_LABEL_COLOR_MOBILE, shape_opacity=0.0, always_visible=True, render_points_as_spheres=True)

        if reset_view:
            bounds = self.plotter.bounds
            center = np.array(self.plotter.center)
            diag_length = np.sqrt((bounds[1]-bounds[0])**2 + (bounds[3]-bounds[2])**2 + (bounds[5]-bounds[4])**2)
            distance = diag_length * 2.0
            camera_pos = center + np.array([-distance, -distance, distance]) / np.sqrt(3)
            focal_point = center
            view_up = [0.0, 0.0, 1.0]
            
            self.plotter.camera_position = [camera_pos, focal_point, view_up]
            self.plotter.camera.zoom(config.CAMERA_ZOOM_FACTOR)
    
    def update_platform_pose(self, params: dict, pose: dict, labels: dict):
        if not all(actor for name, actor in self.platform_actors.items() if name in ['mobile', 'legs']): return
        
        # --- MODIFIED: Scale incoming mm data to meters for rendering ---
        base_nodes_mm = np.array(params.get('nodes_3d_base', []))
        mobile_nodes_local_mm = np.array(params.get('nodes_3d_mobile', []))
        if base_nodes_mm.size == 0 or mobile_nodes_local_mm.size == 0: return

        base_nodes = base_nodes_mm * MM_TO_M
        mobile_nodes_local = mobile_nodes_local_mm * MM_TO_M
        position = np.array(pose.get('position', [0,0,0])) * MM_TO_M
        # --- END MODIFICATION ---
        
        r = Rotation.from_quat(pose.get('orientation', [0,0,0,1]))
        mobile_nodes_world = r.apply(mobile_nodes_local) + position
        
        self.platform_meshes['mobile'].points = mobile_nodes_world
        self.platform_meshes['legs'].points = np.vstack([base_nodes, mobile_nodes_world])
        
        # This part of removing/re-adding labels remains largely the same
        if self.platform_actors.get('base_labels'):
            try: self.plotter.remove_actor(self.platform_actors['base_labels'], reset_camera=False)
            except (KeyError, ValueError): pass
        if self.platform_actors.get('mobile_labels'):
            try: self.plotter.remove_actor(self.platform_actors['mobile_labels'], reset_camera=False)
            except (KeyError, ValueError): pass
        if self.platform_actors.get('mobile_center'):
            try: self.plotter.remove_actor(self.platform_actors['mobile_center'], reset_camera=False)
            except (KeyError, ValueError): pass
                
        label_style = {'point_size': config.STYLE_NODE_POINT_SIZE, 'font_size': config.STYLE_NODE_LABEL_FONT_SIZE, 'text_color': config.STYLE_NODE_LABEL_FONT_COLOR, 'shape_opacity': 0.5, 'render_points_as_spheres': True, 'always_visible': True}
        self.platform_actors['base_labels'] = self.plotter.add_point_labels(np.array(base_nodes), labels.get('base', []), name='base_labels', shape_color=config.STYLE_NODE_LABEL_BASE_BG, **label_style)
        self.platform_actors['mobile_labels'] = self.plotter.add_point_labels(np.array(mobile_nodes_world), labels.get('mobile', []), name='mobile_labels', shape_color=config.STYLE_NODE_LABEL_MOBILE_BG, **label_style)

        mobile_center_pos = np.mean(np.array(mobile_nodes_world), axis=0)
        mobile_center_label_text = f"Motion Center\nX: {mobile_center_pos[0]*1000:.1f} Y: {mobile_center_pos[1]*1000:.1f} Z: {mobile_center_pos[2]*1000:.1f}"
        self.platform_actors['mobile_center'] = self.plotter.add_point_labels(mobile_center_pos, [mobile_center_label_text], name='mobile_center_label', point_size=config.STYLE_CENTER_POINT_SIZE, font_size=config.STYLE_CENTER_LABEL_FONT_SIZE, text_color=config.STYLE_CENTER_LABEL_COLOR_MOBILE, point_color=config.STYLE_CENTER_LABEL_COLOR_MOBILE, shape_opacity=0.0, always_visible=True, render_points_as_spheres=True)
        
        self.plotter.render()
    
    def update_angle_visualization(self, data: dict | None, show: bool):
        for actor in self.platform_actors['angle_vectors']: self.plotter.remove_actor(actor, reset_camera=False)
        for actor in self.platform_actors['angle_labels']: self.plotter.remove_actor(actor, reset_camera=False)
        self.platform_actors['angle_vectors'].clear()
        self.platform_actors['angle_labels'].clear()

        if not show or not data:
            self.plotter.render()
            return
            
        # --- MODIFIED: Scale incoming mm data to meters for rendering ---
        base_nodes_mm = data.get("base_nodes")
        mobile_nodes_world_mm = data.get("mobile_nodes_world")
        base_normal = data.get("base_normal")
        platform_normal_world = data.get("platform_normal_world")
        base_angles_deg = data.get("base_angles_deg")
        platform_angles_deg = data.get("platform_angles_deg")

        if any(d is None for d in [base_nodes_mm, mobile_nodes_world_mm, base_normal, platform_normal_world, base_angles_deg, platform_angles_deg]):
            return
        
        base_nodes = np.array(base_nodes_mm) * MM_TO_M
        mobile_nodes_world = np.array(mobile_nodes_world_mm) * MM_TO_M
        # --- END MODIFICATION ---

        vector_length = np.mean(np.linalg.norm(mobile_nodes_world - base_nodes, axis=1)) * 0.3
        # --- MODIFIED: Scale radius from config (which is in mm) ---
        shaft_radius = config.STYLE_NORMAL_VECTOR_RADIUS * MM_TO_M
        
        for i, pos in enumerate(base_nodes):
            arrow = pv.Tube(pointa=pos, pointb=pos + base_normal * vector_length, radius=shaft_radius)
            actor = self.plotter.add_mesh(arrow, color=config.STYLE_NORMAL_VECTOR_BASE_COLOR)
            self.platform_actors['angle_vectors'].append(actor)
        
        for i, pos in enumerate(mobile_nodes_world):
            arrow = pv.Tube(pointa=pos, pointb=pos + platform_normal_world * vector_length, radius=shaft_radius)
            actor = self.plotter.add_mesh(arrow, color=config.STYLE_NORMAL_VECTOR_MOBILE_COLOR)
            self.platform_actors['angle_vectors'].append(actor)
            
        labels = [f"B:{b:.1f}°\nP:{p:.1f}°" for b, p in zip(base_angles_deg, platform_angles_deg)]
        leg_midpoints = (base_nodes + mobile_nodes_world) / 2.0
        
        label_actor = self.plotter.add_point_labels(
            leg_midpoints, labels, 
            font_size=10, text_color='black',
            shape_opacity=0.0, always_visible=True
        )
        self.platform_actors['angle_labels'].append(label_actor)
        
        self.plotter.render()
    
    # ... (The rest of the file from _create_lines_from_nodes to the end remains unchanged) ...
    def _create_lines_from_nodes(self, nodes):
        if not isinstance(nodes, (np.ndarray, list)) or len(nodes) < 2: return pv.PolyData()
        points = np.array(nodes)
        lines = np.array([[2, i, (i + 1) % len(points)] for i in range(len(points))]).flatten()
        return pv.PolyData(points, lines=lines)
    
    def _create_leg_lines(self, base_nodes, mobile_nodes):
        if not isinstance(base_nodes, np.ndarray) or not isinstance(mobile_nodes, np.ndarray) or base_nodes.size == 0 or mobile_nodes.size == 0 or len(base_nodes) != len(mobile_nodes): return pv.PolyData()
        points = np.vstack([base_nodes, mobile_nodes])
        lines = np.array([[2, i, i + len(base_nodes)] for i in range(len(base_nodes))]).flatten()
        return pv.PolyData(points, lines=lines)
        
    def _on_view_interaction_end(self, *args):
        self.is_in_preset_view_sequence = False
        self.view_changed.emit()

    def handle_view_change(self, view_name: str):
        current_params = self.get_camera_params()
        if current_params:
            self.view_history_stack.append(current_params)
            if len(self.view_history_stack) > config.VIZ_VIEW_HISTORY_SIZE: 
                self.view_history_stack.pop(0)
        if not self.is_in_preset_view_sequence:
            self.origin_camera_params = current_params
        
        if view_name == 'undo': self._restore_from_history()
        elif view_name == 'previous': self._restore_from_origin()
        elif view_name == 'iso':
            self.plotter.clear()
            print("重置標準等角视图... (需要主視窗協調)")
        else: self._set_preset_view(view_name); self.is_in_preset_view_sequence = True
        self.view_changed.emit()

    def _set_preset_view(self, view_name: str):
        view_methods = {'xy': self.plotter.view_xy, 'xz': self.plotter.view_xz, 'yz': self.plotter.view_yz}
        if view_name in view_methods:
            view_methods[view_name](); self.plotter.camera.zoom(1.2)

    def _restore_from_history(self):
        if self.view_history_stack:
            self.set_camera_params(self.view_history_stack.pop())
        else: print("無更多歷史視角可供撤銷。")

    def _restore_from_origin(self):
        if self.origin_camera_params:
            self.set_camera_params(self.origin_camera_params)
            self.is_in_preset_view_sequence = False
        else: print("沒有記錄探索前視角。")
            
    def get_camera_params(self) -> dict | None:
        if not self.plotter: return None
        cpos = self.plotter.camera_position
        return {'cpos': [list(cpos[0]), list(cpos[1]), list(cpos[2])], 'parallel_scale': self.plotter.camera.parallel_scale}

    def set_camera_params(self, params: dict | None):
        if not params or not self.plotter: return
        if 'cpos' in params and params['cpos']: self.plotter.camera_position = params['cpos']
        if 'parallel_scale' in params: self.plotter.camera.parallel_scale = params['parallel_scale']
        self.saved_camera_params = self.get_camera_params()
        self.plotter.render()
    
    def restore_saved_camera_view(self):
        self.handle_view_change('previous')
        if self.saved_camera_params:
            self.set_camera_params(self.saved_camera_params)
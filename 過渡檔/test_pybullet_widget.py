# D:\Python_Programs\Stewart_Platform\test_pybullet_widget.py

import sys
import pybullet as p
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPainter

# 這是從您之前的版本中簡化而來的 PyBulletWidget
# 它的唯一職責就是在一個乾淨的環境中繪圖
class PyBulletTestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.physics_client_id = -1
        self.camera_yaw = 90.0
        self.camera_pitch = -45.0
        self.camera_distance = 2.5
        self.camera_target_pos = [0.0, 0.0, 0.5]
        self.setMinimumSize(800, 600)
        
        # 使用 QTimer 來確保 PyQt 的事件循環和 PyBullet 的渲染有機會協調
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update) # 持續觸發 paintEvent
        self.timer.start(1000 // 60) # 60 FPS
        
        self._init_pybullet()
        self._draw_test_model()

    def _init_pybullet(self):
        if self.physics_client_id < 0:
            # 我們使用 p.GUI 來創建一個獨立的調試窗口，以便對比
            # self.physics_client_id = p.connect(p.GUI) 
            # 如果上面的 p.GUI 能顯示，但下面的 p.DIRECT 不行，就說明問題出在渲染到Qt的環節
            self.physics_client_id = p.connect(p.DIRECT)
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0, physicsClientId=self.physics_client_id)
            self._draw_world_frame()

    def _draw_world_frame(self):
        p.addUserDebugLine([0,0,0], [1,0,0], [1,0,0], 2, physicsClientId=self.physics_client_id)
        p.addUserDebugLine([0,0,0], [0,1,0], [0,1,0], 2, physicsClientId=self.physics_client_id)
        p.addUserDebugLine([0,0,0], [0,0,1], [0,0,1], 2, physicsClientId=self.physics_client_id)

    def _draw_test_model(self):
        """使用您截圖中的硬編碼數據來繪製模型"""
        # 這些是從您成功的終端日誌中提取的、未經旋轉的純粹數學座標
        base_nodes = [[1.152, 0.0, 0], [1.13, 0.228, 0], [0.88, 0.74, 0], [0.0, 1.152, 0], [-0.228, 1.13, 0], [-0.74, 0.88, 0]]
        mobile_nodes_local = [[0.939, 0.0, 0], [0.92, 0.186, 0], [0.72, 0.60, 0], [0.0, 0.939, 0], [-0.186, 0.92, 0], [-0.60, 0.72, 0]]
        
        # 繪製下平台
        for i in range(6):
            p1, p2 = base_nodes[i], base_nodes[(i + 1) % 6]
            p.addUserDebugLine(p1, p2, [0.2, 0.6, 1], 3, self.physics_client_id)

        # 假設平台處於零位姿態
        position = [0, 0, 1.363] # H
        orientation_quat = [0, 0, 0, 1]
        rot_matrix = np.array(p.getMatrixFromQuaternion(orientation_quat)).reshape(3, 3)
        mobile_nodes_world = [np.array(position) + rot_matrix @ np.array(node) for node in mobile_nodes_local]
        
        # 繪製上平台
        for i in range(6):
            p1, p2 = mobile_nodes_world[i], mobile_nodes_world[(i + 1) % 6]
            p.addUserDebugLine(p1, p2, [0.2, 0.9, 0.4], 3, self.physics_client_id)
        
        # 繪製連桿
        for i in range(6):
            p_base, p_mobile = base_nodes[i], mobile_nodes_world[i]
            p.addUserDebugLine(p_base, p_mobile, [0.8, 0.8, 0.2], 2, self.physics_client_id)

    def paintEvent(self, event):
        if self.physics_client_id < 0: return

        w, h = self.width(), self.height()
        if h == 0: return

        view_matrix = p.computeViewMatrixFromYawPitchRoll(
            cameraTargetPosition=self.camera_target_pos,
            distance=self.camera_distance,
            yaw=self.camera_yaw,
            pitch=self.camera_pitch,
            roll=0,
            upAxisIndex=2,
            physicsClientId=self.physics_client_id
        )
        proj_matrix = p.computeProjectionMatrixFOV(60, w/h, 0.01, 100.0, self.physics_client_id)
        
        # 這是最關鍵的一步：從PyBullet的渲染緩衝區獲取圖像
        (_, _, rgba, _, _) = p.getCameraImage(w, h, view_matrix, proj_matrix, renderer=p.ER_BULLET_HARDWARE_OPENGL, physicsClientId=self.physics_client_id)
        
        image = QImage(bytes(rgba), w, h, QImage.Format.Format_RGBA8888)
        painter = QPainter(self)
        painter.drawImage(0, 0, image)

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    test_widget = PyBulletTestWidget()
    window.setCentralWidget(test_widget)
    window.setWindowTitle("PyBullet 獨立渲染測試")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
# test_layout.py

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QSplitter, QScrollArea, QLabel, QGroupBox, QFormLayout, 
                             QSlider, QHBoxLayout)
from PyQt6.QtCore import Qt

# --- 模擬我們專案中的 config.py ---
UI_LAYOUT_STRETCH_FACTOR_LEFT = 45
UI_LAYOUT_STRETCH_FACTOR_RIGHT = 55

class ComplexWidget(QWidget):
    """一個用來模擬我們專案中複雜元件（如 MasterGeometryWidget）的類別"""
    def __init__(self, num_groups, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        for i in range(num_groups):
            group = QGroupBox(f"參數群組 {i+1}")
            form = QFormLayout(group)
            for j in range(5):
                form.addRow(f"參數 {j+1}:", QLabel("N/A"))
            main_layout.addWidget(group)
        main_layout.addStretch()

class AnotherComplexWidget(QWidget):
    """一個用來模擬我們專案中 AnalysisWidget 的類別"""
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        group = QGroupBox("平台姿態控制")
        form = QFormLayout(group)
        for name in ["Surge", "Sway", "Heave", "Pitch", "Roll", "Yaw"]:
            slider_container = QWidget()
            hbox = QHBoxLayout(slider_container)
            hbox.setContentsMargins(0, 0, 0, 0)
            hbox.addWidget(QLabel(f"-200.0"))
            hbox.addWidget(QSlider(Qt.Orientation.Horizontal))
            hbox.addWidget(QLabel(f"200.0"))
            form.addRow(f"{name} (mm):", slider_container)
        main_layout.addWidget(group)
        main_layout.addStretch()

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("佈局壓力測試")
        self.setGeometry(100, 100, 1200, 800)
        
        self._initial_split_set = False
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # --- 模擬左側面板 ---
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        # 建立一個包含 4 個群組的複雜元件，模擬 MasterGeometryWidget
        left_content = ComplexWidget(num_groups=4) 
        left_scroll_area.setWidget(left_content)

        # --- 模擬右側面板 ---
        # 建立一個模擬 AnalysisWidget 的複雜元件
        right_content = AnotherComplexWidget()
        
        self.splitter.addWidget(left_scroll_area)
        self.splitter.addWidget(right_content)
        
        main_layout.addWidget(self.splitter)

    def showEvent(self, event):
        """在視窗首次顯示時，執行一次性的初始佈局設定"""
        super().showEvent(event)
        if not self._initial_split_set:
            total_width = self.splitter.width()
            left_width = int(total_width * (UI_LAYOUT_STRETCH_FACTOR_LEFT / (UI_LAYOUT_STRETCH_FACTOR_LEFT + UI_LAYOUT_STRETCH_FACTOR_RIGHT)))
            right_width = total_width - left_width
            self.splitter.setSizes([left_width, right_width])
            self._initial_split_set = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
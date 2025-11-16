# D:\Python_Programs\Stewart_Platform\src\utils\custom_widgets.py

from PyQt6.QtWidgets import QDoubleSpinBox, QComboBox, QSlider
from PyQt6.QtCore import Qt

class CustomDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activated = False  # 標記是否激活滾輪調整

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated = not self.activated  # 雙擊切換激活狀態
            event.accept()

    def wheelEvent(self, event):
        if self.activated and self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()  # 忽略未激活的滾輪事件

    def focusOutEvent(self, event):
        self.activated = False  # 失去焦點時重設
        super().focusOutEvent(event)

class CustomComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activated = False  # 標記是否激活滾輪調整

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated = not self.activated  # 雙擊切換激活狀態
            event.accept()

    def wheelEvent(self, event):
        if self.activated and self.hasFocus():
            super().wheelEvent(event)  # 允許滾輪改變選項
        else:
            event.ignore()  # 忽略未激活的滾輪事件

    def focusOutEvent(self, event):
        self.activated = False  # 失去焦點時重設
        super().focusOutEvent(event)

class CustomSlider(QSlider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activated = False  # 標記是否激活滾輪調整

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated = not self.activated  # 雙擊切換激活狀態
            event.accept()

    def wheelEvent(self, event):
        if self.activated and self.hasFocus():
            super().wheelEvent(event)  # 允許滾輪調整滑桿
        else:
            event.ignore()  # 忽略未激活的滾輪事件

    def focusOutEvent(self, event):
        self.activated = False  # 失去焦點時重設
        super().focusOutEvent(event)
# D:\Python_Programs\Stewart_Platform\main.py

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QScreen
from src.gui.main_window import MainWindow 
from src.core import config  # 引入設定檔

def main():
    """應用程式主函數"""
    app = QApplication(sys.argv)
    
    # 設定應用程式全局字體
    app.setFont(QFont(config.FONT_UI_NAME, config.FONT_UI_SIZE))
    
    main_window = MainWindow()
    
    # 設定主視窗尺寸並置中
    main_window.setGeometry(0, 0, config.DRIVE_DASHBOARD_WIDTH, config.DRIVE_DASHBOARD_HEIGHT)
    screen = app.primaryScreen().geometry()
    main_window.move(
        (screen.width() - config.DRIVE_DASHBOARD_WIDTH) // 2,
        (screen.height() - config.DRIVE_DASHBOARD_HEIGHT) // 2
    )
    main_window.show()

    # 根據 config 決定是否顯示 3D 預覽視窗
    if config.STARTUP_SHOW_3D_PREVIEW:
        pv_window = main_window.pv_window
        pv_window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
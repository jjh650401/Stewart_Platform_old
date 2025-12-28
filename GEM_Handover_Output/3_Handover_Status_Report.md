# 專案交接狀態報告
日期: 2025-12-28
版本: v2.4.1 (動力學與 3D 預覽修復版)

## 1. 專案現況概述
本專案為「史都華平台設計與模擬工具」，使用 Python (PyQt6 + PyVista) 開發。
目前剛完成 v2.4.1 版本的關鍵 Bug 修復，準備進入下一階段開發。

## 2. Git 與版本狀態
- **目前分支**: main (已合併 fix-dynamics-algo 開發分支)
- **最新變更**:
    1. [Core] 修正動力學矩陣逆運算錯誤 (Inv(J^T))，靜態受力回歸物理合理值。
    2. [Core] 修正 6-DOF 幾何求解器在非零相位角下的 Yaw 軸鎖定邏輯。
    3. [GUI] 修正 main_window.py 中的 3D 預覽邏輯，解決平台主體與法線分離問題。

## 3. 檔案結構說明
- `src/core/`: 包含 kinematics, dynamics, config 等核心邏輯。
- `src/gui/`: 包含 main_window 及各個 widget (controls/)。
- `data/`: 存放專案設定檔。

## 4. 待辦事項 (Next Steps)
- 請讀取 `Project_Code_Snapshot.txt` 以理解完整程式碼邏輯。
- 請使用 `o-Ride E_平台數據.json` 進行回歸測試，驗證推力數值 (預期: 60度相位角/200kg負載下約 4781N)。

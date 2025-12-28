import os
import shutil
from datetime import datetime

# ================= 設定區 =================
OUTPUT_DIR = "GEM_Handover_Output"
TARGET_EXTENSIONS = {".py", ".json", ".xml", ".md"} # 要抓取的檔案類型
IGNORE_DIRS = {".venv", "__pycache__", ".git", ".vscode", "GEM_Handover_Output"}
# 指定要特別抓取的測試數據檔名 (請確認您的檔名是否正確)
TEST_DATA_FILENAME = "o-Ride E_平台數據.json" 

# 交接報告內容 (自動生成)
HANDOVER_REPORT_CONTENT = f"""# 專案交接狀態報告
日期: {datetime.now().strftime('%Y-%m-%d')}
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
"""

def generate_tree(startpath):
    """生成目錄結構樹"""
    tree_str = "Project Directory Structure:\n"
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith(tuple(TARGET_EXTENSIONS)) or f == "requirements.txt":
                tree_str += '{}{}\n'.format(subindent, f)
    return tree_str

def generate_code_snapshot(startpath):
    """將所有程式碼合併為一個檔案"""
    snapshot_content = ""
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith(".py") or file == "requirements.txt":
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, startpath)
                
                snapshot_content += f"\n{'='*60}\n"
                snapshot_content += f"FILE PATH: {rel_path}\n"
                snapshot_content += f"{'='*60}\n"
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        snapshot_content += f.read() + "\n"
                except Exception as e:
                    snapshot_content += f"[Error reading file: {e}]\n"
    return snapshot_content

def main():
    # 1. 建立輸出資料夾
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"正在準備轉移文件至 {OUTPUT_DIR}...")

    # 2. 生成目錄結構樹 (1_Directory_Tree.txt)
    tree_content = generate_tree(".")
    with open(os.path.join(OUTPUT_DIR, "1_Directory_Tree.txt"), "w", encoding="utf-8") as f:
        f.write(tree_content)
    print("-> 已生成目錄結構樹。")

    # 3. 生成程式碼快照 (2_Project_Code_Snapshot.txt)
    code_content = generate_code_snapshot(".")
    with open(os.path.join(OUTPUT_DIR, "2_Project_Code_Snapshot.txt"), "w", encoding="utf-8") as f:
        f.write(code_content)
    print("-> 已生成程式碼快照 (包含所有 .py 檔)。")

    # 4. 生成交接報告 (3_Handover_Status_Report.md)
    with open(os.path.join(OUTPUT_DIR, "3_Handover_Status_Report.md"), "w", encoding="utf-8") as f:
        f.write(HANDOVER_REPORT_CONTENT)
    print("-> 已生成交接狀態報告。")

    # 5. 複製測試數據 (4_Test_Data.json)
    # 嘗試在專案根目錄或 data/projects 尋找
    found_data = False
    possible_paths = [TEST_DATA_FILENAME, os.path.join("data", "projects", TEST_DATA_FILENAME)]
    
    for path in possible_paths:
        if os.path.exists(path):
            shutil.copy(path, os.path.join(OUTPUT_DIR, "4_Test_Data.json"))
            print(f"-> 已複製測試數據: {path}")
            found_data = True
            break
    
    if not found_data:
        print(f"⚠️ 警告: 找不到 '{TEST_DATA_FILENAME}'。請手動將該測試數據複製到輸出資料夾。")

    print(f"\n✅ 轉移文件準備完成！請將 '{OUTPUT_DIR}' 資料夾內的檔案上傳至新 GEM。")

if __name__ == "__main__":
    main()
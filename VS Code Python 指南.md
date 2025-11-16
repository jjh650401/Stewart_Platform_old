您好！很高興能協助您建立一套 VS Code 和 Python 學習與操作指南。考量您在家用和公司電腦間協作的獨特環境，本指南將會系統性地整合來源文件中的資訊，幫助您快速上手並高效管理專案。

以下是為您整理的 VS Code 和 Python 學習及操作指南，將重點放在專案建置、虛擬環境管理、Git 版本控制、GitHub 同步，以及您家用與公司電腦的特殊環境考量。

---

### **VS Code 與 Python 專案開發指南：從入門到跨電腦同步**

**適用對象**：自控工程師（機械背景）、具備基礎程式設計概念者
**專案目錄**：`D:\Python_Programs`
**GitHub 帳號**：jjh650401

---

#### **第一部分：環境準備**

在開始任何專案之前，請確保您的家用和公司電腦已安裝必要的軟體並完成基本配置。

1.  **安裝必要軟體**
    *   **Visual Studio Code (VS Code)**：這將是您的主要程式開發環境。
        *   下載並安裝：[VS Code 官方網站](https://code.visualstudio.com/)。
    *   **Git**：版本控制工具，用於追蹤程式碼變更與多電腦同步。
        *   下載並安裝：[Git 官方網站](https://git-scm.com/download/win)。
        *   **安裝時請務必勾選「Add Git to PATH」**，這樣您才能在終端機中直接使用 Git 指令。
        *   安裝完成後，開啟終端機（Cmd 或 PowerShell），輸入 `git --version` 檢查是否安裝成功。
    *   **Python**：您的主要開發語言。
        *   下載並安裝：[Python 官方網站](https://www.python.org/)。
        *   **安裝時請務必勾選「Add Python to PATH」**，這樣您才能在終端機中直接使用 Python 指令。
        *   安裝完成後，輸入 `python --version` 檢查是否安裝成功。
        *   **如果您有多個 Python 版本（如 Python 3.10 和 3.12）**，可以在 VS Code 中靈活切換。預設情況下，VS Code 會嘗試使用 PATH 中的 Python 版本，您也可以在 `settings.json` 中指定路徑，或透過 VS Code GUI (`Ctrl + Shift + P` -> `Python: Select Interpreter`) 選擇。

2.  **配置 GitHub 帳戶與 SSH 金鑰**
    *   **GitHub 帳戶資訊**：您的 GitHub 使用者名稱是 **jjh650401**，電子郵件是 **jjh0401@gmail.com**。
    *   **SSH 金鑰的目的**：使用 SSH 連接到 GitHub 可以確保連線安全，並免除每次推送/拉取時輸入帳號密碼的麻煩。
    *   **為每個專案生成專屬的 SSH 金鑰 (推薦做法)**：
        *   建議為每個專案生成一組獨立的 SSH 金鑰。這樣可以提高安全性，並在管理多個專案時更清晰。
        *   **生成指令（使用 RSA 4096 位元金鑰，並指定輸出路徑和註解）**：
            ```bash
            ssh-keygen -t rsa -b 4096 -C "jjh0401@gmail.com" -f C:\Users\jason\.ssh\id_rsa_專案名稱
            ```
            *   **舉例**：為 `VideoDownloader` 專案生成金鑰：
                ```bash
                ssh-keygen -t rsa -b 4096 -C "jjh0401@gmail.com" -f C:\Users\jason\.ssh\id_rsa_VideoDownloader
                ```
            *   當系統提示輸入密碼時，可以直接按 Enter 跳過，或設定密碼以增加安全性（每次使用金鑰時需輸入）。
        *   **確認生成檔案**：執行指令後，您會在 `C:\Users\jason\.ssh\` 目錄下看到兩個檔案：`id_rsa_VideoDownloader` (私鑰) 和 `id_rsa_VideoDownloader.pub` (公鑰)。
    *   **將公鑰添加到 GitHub**：
        1.  登入 GitHub (jjh650401)。
        2.  點擊右上角個人頭像，選擇 **Settings** > **SSH and GPG keys** > **New SSH key**。
        3.  **Title (標題)**：為金鑰設定一個易於識別的名稱，例如「**公司電腦 - VideoDownloader**」或「**家裡電腦 - VideoDownloader**」。這有助於您在 GitHub 介面區分不同電腦的金鑰。
        4.  **Key (公鑰內容)**：複製您剛生成的 `.pub` 檔案內容（從 `ssh-rsa` 或 `ssh-ed25519` 開始到您的電子郵件結束）並貼上。
        5.  點擊「Add SSH key」。
    *   **配置 SSH 設定檔案 (`~/.ssh/config`)**：
        *   這是管理多個 SSH 金鑰的關鍵。您需要在 `C:\Users\jason\.ssh\` 目錄下創建或編輯 `config` 檔案。
        *   **範例內容**：
            ```
            # 公司電腦 - VideoDownloader 專案
            Host github-videodownloader-company
                HostName github.com
                User git
                IdentityFile C:/Users/jason/.ssh/id_rsa_VideoDownloader
                IdentitiesOnly yes

            # 家用電腦 - VideoDownloader 專案
            Host github-videodownloader-home
                HostName github.com
                User git
                IdentityFile C:/Users/jason/.ssh/id_rsa_VideoDownloader_home # 如果您在家裡電腦的金鑰名稱不同
                IdentitiesOnly yes
            ```
            *   **`Host`**：這是一個自訂別名，用於在 Git 指令中指定使用哪組 SSH 金鑰設定。
            *   **`HostName`**：實際連接的伺服器名稱（GitHub 的主機名為 `github.com`）。
            *   **`User`**：GitHub SSH 連線的固定使用者名稱為 `git`。
            *   **`IdentityFile`**：指定該 `Host` 使用的私鑰檔案路徑。
            *   **`IdentitiesOnly yes`**：確保 SSH 只使用 `IdentityFile` 中指定的金鑰，避免嘗試其他金鑰導致認證失敗。
    *   **測試 SSH 連線**：
        *   在 Git Bash 或 PowerShell 中執行（使用您在 `config` 中設定的 `Host` 別名）：
            ```bash
            ssh -T github-videodownloader-company
            ```
            或
            ```bash
            ssh -T github-videodownloader-home
            ```
        *   如果成功，您會看到類似「Hi jjh650401! You've successfully authenticated...」的訊息。提示「GitHub does not provide shell access」是正常的預期行為。
        *   **首次連接時，可能會要求確認主機指紋**，輸入 `yes` 即可。

---

#### **第二部分：VS Code 基本設定與專案管理**

高效使用 VS Code 可以大大提升您的開發體驗。

1.  **VS Code 擴充功能**
    *   開啟 VS Code，按 `Ctrl+Shift+X` 進入「擴充功能」面板，搜尋並安裝以下推薦擴充功能：
        *   **Python**：提供 Python 語法高亮、程式碼執行、除錯等功能。
        *   **GitLens**：增強 Git 功能，例如查看程式碼的 Git 提交歷史。
        *   **GitHub Pull Requests and Issues**：方便與 GitHub 專案整合。
        *   **Project Manager** (選用)：如果您需要管理多個專案並快速切換，這個擴充功能非常有用。

2.  **VS Code UI 設定**
    *   您可以透過修改 VS Code 的設定來調整使用者介面 (UI) 的外觀。
    *   開啟設定：按 `Ctrl + Shift + P`，輸入 `settings.json`，選擇「Preferences: Open Settings (JSON)」。
    *   **整體 UI 縮放**：調整 `window.zoomLevel` 可以放大或縮小整個 UI（包括側邊欄、選單、按鈕等）。
        ```json
        "window.zoomLevel": 0.5 // 0 為預設，正數放大，負數縮小
        ```
        *   您也可以使用快捷鍵 `Ctrl + +` 放大、`Ctrl + -` 縮小、`Ctrl + 0` 還原。
    *   **終端機字體大小**：可以獨立調整終端機的字體大小。
        ```json
        "terminal.integrated.fontSize": 14
        ```
    *   **側邊欄字體大小**：VS Code 不提供直接設定選項，但可以透過安裝 `Custom CSS and JS Loader` 擴充功能來修改 CSS 實現。這是較進階的做法，如果沒有特殊需求，建議使用整體 UI 縮放即可。

3.  **多專案管理**
    *   您的所有程式專案資料夾都將放在 `D:\Python_Programs` 下。VS Code 提供了幾種管理多個專案的方法：
        *   **方法一：分別載入專案**：每次只打開一個專案資料夾 (例如 `D:\Python_Programs\VideoDownloader`)。這適合您專注於單一專案時。
        *   **方法二：同時載入多個專案 (多根工作區)**：在一個 VS Code 視窗中同時載入多個專案資料夾。這對於需要同時查看或編輯多個專案的情況非常有用。您可以透過「檔案」>「將資料夾新增到工作區...」來實現。
        *   **方法三：使用「Project Manager」擴充功能**：安裝 `Project Manager` 擴充功能後，您可以將所有專案添加到其列表中，然後透過命令面板 (`Ctrl + Shift + P` -> `Project Manager: List Projects to Open`) 快速切換專案。

---

#### **第三部分：Python 開發環境**

為每個專案建立獨立的虛擬環境是 Python 開發的最佳實踐。

1.  **虛擬環境的建立與管理**
    *   **作用**：虛擬環境 (`venv`) 能夠隔離每個 Python 專案的依賴包，避免不同專案間的套件版本衝突，並確保部署環境的一致性。**切記不要將 `.venv` 資料夾上傳到 Git 儲存庫**，因為它包含系統相關的檔案，無法跨系統使用。
    *   **建立虛擬環境**：
        1.  在 VS Code 中開啟終端機（快捷鍵 `Ctrl + ` ` `）。
        2.  導航到您的專案根目錄 (例如 `D:\Python_Programs\MyProject`)。
        3.  執行指令建立虛擬環境：
            ```bash
            python -m venv .venv
            ```
            *   這會在當前專案目錄下建立一個名為 `.venv` 的資料夾。
    *   **啟動虛擬環境**：
        *   **在 PowerShell 中**：
            ```bash
            .\.venv\Scripts\Activate.ps1
            ```
            *   **PowerShell 執行策略問題**：Windows 預設會阻止執行未簽名的腳本。如果遇到執行失敗，您可以**暫時更改執行策略**：
                ```bash
                Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
                ```
                *   這個指令只對當前 PowerShell 進程有效，關閉 PowerShell 後會恢復。如果您不想每次都設定，可以考慮永久更改（請謹慎評估安全性）。
        *   **在 CMD 中**：
            ```bash
            .venv\Scripts\activate
            ```
        *   成功啟動後，您的命令提示字元前會顯示 `(venv)`，表示已進入虛擬環境。
    *   **停用虛擬環境**：
        ```bash
        deactivate
        ```
    *   **刪除並重建虛擬環境**：當虛擬環境損壞、需要升級 Python 版本，或在不同電腦間確保一致性時，可以重建。
        1.  如果虛擬環境已啟動，請先停用。
        2.  刪除現有虛擬環境（Windows 指令）：
            ```bash
            rmdir .venv /s /q
            # 或使用 PowerShell: Remove-Item -Recurse -Force .venv
            ```
            *   **注意**：`rm -rf .git` 是 Linux/Unix 指令，Windows 應使用 `rmdir` 或 `Remove-Item`。
        3.  重新建立並啟動新的虛擬環境 (如上述步驟)。
    *   **設定 VS Code 使用虛擬環境**：
        1.  在 VS Code 中，按 `Ctrl+Shift+P`，輸入「Python: Select Interpreter」。
        2.  選擇您專案虛擬環境的路徑（例如 `.\.venv\Scripts\python.exe`）。

2.  **依賴套件管理**
    *   **升級 pip**
        ```bash
        python -m pip install --upgrade pip
        ```
    *   **安裝套件**：在虛擬環境啟動後，使用 `pip` 安裝所需的 Python 套件。
        ```bash
        pip install requests numpy # 範例
        ```
    *   **生成依賴套件清單 (`requirements.txt`)**：
        *   **最推薦：使用 `pipreqs .` 產生最小化清單**：這個工具會掃描您的 Python 程式碼，只列出直接 `import` 的套件，這有助於保持 `requirements.txt` 的精簡和避免不必要的依賴。
            ```bash
            pip install pipreqs # 如果尚未安裝
            pipreqs . # 在專案根目錄執行
            ```
            *   **注意**：`pipreqs` 可能會遺漏間接依賴或動態載入的套件。
            *   **`UnicodeDecodeError` 問題**：如果 `pipreqs` 報錯，可能是您的 Python 檔案編碼不是 UTF-8。建議使用 VS Code 或記事本將問題檔案轉換為 UTF-8 編碼。
        *   **完整備份：使用 `pip freeze > requirements.txt`**：這個指令會列出當前虛擬環境中所有已安裝的套件及其版本（包括間接依賴），並匯出到 `requirements.txt`。
            ```bash
            pip freeze > requirements.txt
            ```
            *   **優點**：確保可以還原**完全相同**的環境。
            *   **缺點**：可能包含開發時安裝但程式實際不需的套件（例如 `jupyter`, `pytest` 等）。
        *   **比較兩種方式**：您可以用 `pipreqs .` 產生一份，再用 `pip freeze > requirements_full.txt` 產生一份，然後比較兩者的差異，找出 `pipreqs` 可能遺漏的必要套件並手動加入 `requirements.txt`。
    *   **從 `requirements.txt` 安裝套件**：
        *   在新環境或重建虛擬環境後，使用以下指令安裝所有依賴：
            ```bash
            pip install -r requirements.txt
            ```

---

#### **第四部分：Git 版本控制與 GitHub 同步**

本部分涵蓋從初始化 Git 專案到在家用和公司電腦間同步程式碼的完整工作流程。

1.  **Git 初始化與遠端設定**
    *   **初始化 Git 儲存庫**：
        1.  在 VS Code 終端機中，導航到您的專案根目錄 (例如 `D:\Python_Programs\MyProject`)。
        2.  執行指令初始化 Git：
            ```bash
            git init
            ```
            *   這會在專案目錄中建立一個 `.git` 資料夾，將此目錄設為 Git 專案。
            *   如果終端機顯示「not a git repository」，表示當前目錄沒有初始化 Git。
        3.  **建立 `.gitignore` 檔案**：在專案根目錄下新建一個 `.gitignore` 檔案，並添加以下內容以忽略不必要的檔案和虛擬環境。
            ```
            .venv/
            downloads/ # 排除下載資料夾
            __pycache__/
            *.pyc
            .vscode/ # 如果 VS Code 設定是專案層級的，可以考慮不排除
            ```
            *   **注意**：`downloads/` 是您專案可能存放下載內容的資料夾。
        4.  **提交初始檔案**：
            ```bash
            git add . # 將所有檔案添加到暫存區
            git commit -m "Initial commit - project setup" # 提交到本地儲存庫
            ```
            *   **提交訊息很重要**，應清晰描述本次變更的內容和目的。
    *   **在 GitHub 上建立遠端儲存庫**：
        1.  登入 GitHub (jjh650401)，點擊右上角的 `+` 號，選擇 **New repository**。
        2.  輸入 **Repository name** (例如 `VideoDownloader`)，選擇 **Public** 或 **Private**。
        3.  點擊 **Create repository**。
        4.  複製 GitHub 提供的 SSH URL，格式為 `git@github.com:jjh650401/VideoDownloader.git`。
    *   **連結本地儲存庫到 GitHub**：
        1.  在 VS Code 終端機中，執行指令添加遠端儲存庫。**請使用您在 `~/.ssh/config` 中為該專案設定的 `Host` 別名**。
            *   **公司電腦** (假設 `config` 中 Host 為 `github-videodownloader-company`)：
                ```bash
                git remote add origin git@github-videodownloader-company:jjh650401/VideoDownloader.git
                ```
            *   **家用電腦** (假設 `config` 中 Host 為 `github-videodownloader-home`)：
                ```bash
                git remote add origin git@github-videodownloader-home:jjh650401/VideoDownloader.git
                ```
            *   **`origin`** 是遠端儲存庫的預設名稱。
        2.  **驗證遠端 URL**：執行 `git remote -v`。應該會顯示您剛才設定的 SSH URL。
    *   **推送本地分支到遠端**：
        ```bash
        git push -u origin main
        ```
        *   這會將您本地的 `main` 分支推送到 GitHub 上的 `main` 分支。`-u` 參數會設定 `origin main` 為預設上游分支，之後只需使用 `git push` 即可。

2.  **跨電腦專案同步工作流程**
    *   **首次在另一台電腦 (例如公司電腦) 克隆專案**：
        1.  在公司電腦上安裝 VS Code、Python、Git 並設定擴充功能。
        2.  **確保您已在公司電腦上完成了 SSH 金鑰的生成、添加到 GitHub 及 `~/.ssh/config` 的配置**。
        3.  開啟 VS Code，在檔案總管中導航到您的專案根目錄 (`D:\Python_Programs`)。
        4.  在 VS Code 終端機中，執行指令克隆專案。**請使用您在公司電腦 `~/.ssh/config` 中設定的 `Host` 別名**。
            ```bash
            git clone git@github-videodownloader-company:jjh650401/VideoDownloader.git
            ```
        5.  進入新克隆的專案目錄 (`cd VideoDownloader`)。
        6.  **建立並啟動虛擬環境**：
            ```bash
            python -m venv .venv
            .\.venv\Scripts\Activate.ps1 # 或 .venv\Scripts\activate for CMD
            ```
        7.  **安裝依賴套件**：
            *   **如果您在家中電腦已生成 `requirements.txt` 並推送到 GitHub**，在公司電腦拉取後，執行：
                ```bash
                pip install -r requirements.txt
                ```
            *   如果沒有 `requirements.txt`，則手動安裝必要套件並生成。
    *   **日常同步操作 (在家或公司)**：
        1.  **開始工作前**：進入專案目錄，**啟動虛擬環境**，然後拉取遠端最新程式碼。
            ```bash
            cd D:\Python_Programs\VideoDownloader
            .\.venv\Scripts\Activate.ps1
            git pull origin main
            ```
        2.  **完成修改後**：提交本地變更並推送到 GitHub。
            ```bash
            git add .
            git commit -m "描述本次更新內容"
            git push origin main
            ```

3.  **解決常見同步問題**
    *   **合併衝突 (Merge Conflict)**：如果您在家裡和公司同時修改了同一個檔案的相同部分，Git 會提示衝突。
        *   **解決方法**：VS Code 通常會顯示衝突標記 (`<<<<<<<`, `=======`, `>>>>>>>`)，您可以手動編輯檔案，保留需要的內容並移除標記。
        *   解決後，執行 `git add .` 標記衝突已解決，然後 `git commit` 提交合併結果，最後 `git push` 推送。
    *   **Git 無法推送 (rejected, non-fast-forward)**：這通常表示遠端儲存庫有新的變更，而您尚未拉取。
        *   **解決方法**：先執行 `git pull origin main` 拉取最新變更，解決任何衝突後再推送。
    *   **Git 無法推送 (大文件問題)**：GitHub 會拒絕超過一定大小（通常是 100MB）的大文件。
        *   **解決方法**：需要使用 `git filter-repo` 從 Git 歷史中移除大文件，然後強制推送修改後的歷史。
    *   **Git 無法推送 (找不到 `main` 分支)**：這表示您可能在 `master` 分支而非 `main`。
        *   **解決方法**：檢查當前分支 (`git branch`)，如果顯示 `master`，則執行 `git branch -M main` 將 `master` 改名為 `main`，然後再推送到遠端。
    *   **確認資料已推送到 GitHub**：
        1.  **檢查 GitHub 網站**：登入 GitHub，進入您的儲存庫，查看 `Commits` 頁籤，確認您的最新提交是否已顯示。
        2.  **使用 `git status`**：執行 `git status`，如果顯示「Your branch is up to date with 'origin/main'」，表示本地與遠端已同步。
        3.  **使用 `git log`**：執行 `git log --oneline` 和 `git log origin/main --oneline`，比較兩者提交記錄是否一致。

---

#### **第五部分：針對您的特殊環境設定與問題解決**

考量您家用與公司電腦的 GPU 和 CUDA/cuDNN 配置差異，以下提供特定建議。

1.  **CUDA/cuDNN 配置考量 (家用 vs. 公司)**
    *   **家用電腦 (有系統級 CUDA/cuDNN)**：由於您有系統管理員權限，且有系統級的 CUDA Toolkit 和 cuDNN，您可以自由安裝需要 GPU 加速的 Python 套件（如 PyTorch 的 CUDA 版本）。
        ```bash
        # 範例：安裝 PyTorch CUDA 11.8 版本
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        ```
    *   **公司電腦 (有系統級 CUDA，但沒有系統級 cuDNN，無管理員權限)**：
        *   **如果 PyTorch 或其他深度學習框架需要 cuDNN**，但您沒有管理員權限安裝系統級 cuDNN，**最直接且穩定的解決方案是在公司電腦上安裝這些套件的 CPU 版本**。
            ```bash
            # 範例：安裝 PyTorch CPU 版本
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
            ```
        *   這樣可以確保程式在沒有完整 GPU 環境的情況下也能正常運行，只是無法利用 GPU 加速。
        *   雖然程式碼沒有直接 `import numpy`，但像 PyTorch 這樣的庫在內部運作時可能會依賴 `numpy`。為避免潛在警告和提升效能，**建議始終在虛擬環境中安裝 `numpy`**：`pip install numpy`。

2.  **環境變數查詢 (無管理員權限)**
    *   在公司電腦上，如果您沒有系統管理員權限，**無法直接修改「系統環境變數」**。但您可以修改「使用者環境變數」，這些變更僅影響您的使用者帳戶。
    *   **查詢方法**：
        *   在 CMD 中：`set` (顯示所有變數) 或 `echo %PATH%` (顯示 PATH)。
        *   在 PowerShell 中：`Get-ChildItem Env:` (顯示所有變數) 或 `$env:PATH` (顯示 PATH)。
        *   透過 GUI：按 `Win + R` 輸入 `sysdm.cpl`，切換到「進階」標籤，點擊「環境變數」可查看使用者變數和系統變數。
        *   透過註冊表：`reg query HKCU\Environment` (查詢使用者環境變數)。

3.  **其他常見問題與建議**
    *   **Git 無法執行 `git gc` 報錯 `.pack` 檔案已存在**：手動刪除 `.git/objects/pack/*.pack` 檔案後再重新執行 `git gc --prune=now --aggressive`。
    *   **檢查是否安裝了所有所需資源**：使用 `python --version && pip --version && pip show requests` (`requests` 為範例套件) 來檢查 Python、pip 和特定套件是否已安裝。
    *   **檢查系統模組是否安裝過多**：過多的模組可能導致佔用空間、依賴衝突。您可以使用 `pip list` 列出所有安裝的模組，並與 `requirements.txt` 比較，以判斷是否有冗餘。
    *   **清理多餘模組**：
        *   您可以嘗試使用 `pip freeze | findstr /V /G:requirements.txt > extra_modules.txt` 來找出多餘的模組，然後手動卸載。
        *   最徹底的方式是**刪除並重建虛擬環境**，然後只從 `requirements.txt` 安裝必要依賴。

---

#### **常用命令速查表**

| 功能 | 命令 | 說明 |
| :----------------------- | :--------------------------------------------- | :--------------------------------------------------------------- |
| **Git 初始化** | `git init` | 在當前目錄初始化 Git 儲存庫 |
| **設定 `.gitignore`** | 創建 `.gitignore` 檔案 | 排除不需要版本控制的檔案/資料夾 (例如 `.venv/`, `downloads/`) |
| **添加所有變更** | `git add .` | 將所有修改添加到暫存區 |
| **提交變更** | `git commit -m "訊息"` | 提交暫存區的變更到本地儲存庫，附帶提交訊息 |
| **添加遠端儲存庫** | `git remote add origin <SSH URL>` | 連結本地儲存庫到 GitHub 遠端儲存庫 |
| **推送到 GitHub** | `git push -u origin main` | 將本地 `main` 分支推送到遠端 `main` 分支 |
| **拉取最新更新** | `git pull origin main` | 從遠端拉取最新變更並合併 |
| **克隆專案** | `git clone <SSH URL>` | 從 GitHub 克隆專案到本地 |
| **檢查 Git 狀態** | `git status` | 查看當前工作目錄的變更狀態 |
| **檢查本地分支** | `git branch` | 列出所有本地分支 |
| **檢查遠端分支** | `git branch -r` | 列出所有遠端分支 |
| **檢查所有分支** | `git branch -a` | 列出本地和遠端所有分支 |
| **重命名本地分支** | `git branch -M main` | 將當前分支從 `master` 改為 `main` |
| **刪除本地分支** | `git branch -d <branch_name>` | 安全刪除本地分支 |
| **清理本地過期遠端緩存** | `git remote prune origin` | 清理本地的遠端分支緩存資訊 |
| **建立虛擬環境** | `python -m venv .venv` | 在當前目錄建立名為 `.venv` 的虛擬環境 |
| **啟動虛擬環境 (PowerShell)** | `.\.venv\Scripts\Activate.ps1` | 啟動虛擬環境 (需解決執行策略問題) |
| **啟動虛擬環境 (CMD)** | `.\.venv\Scripts\activate` | 啟動虛擬環境 |
| **停用虛擬環境** | `deactivate` | 停用當前虛擬環境 |
| **刪除虛擬環境 (CMD)** | `rmdir .venv /s /q` | 刪除虛擬環境資料夾 |
| **刪除虛擬環境 (PowerShell)** | `Remove-Item -Recurse -Force .venv` | 刪除虛擬環境資料夾 |
| **安裝套件** | `pip install <套件名稱>` | 安裝 Python 套件到當前虛擬環境 |
| **從 `requirements.txt` 安裝** | `pip install -r requirements.txt` | 從檔案安裝所有依賴套件 |
| **生成精簡依賴清單** | `pipreqs .` | 根據程式碼自動生成 `requirements.txt` (推薦) |
| **生成完整依賴清單** | `pip freeze > requirements.txt` | 匯出當前虛擬環境所有已安裝套件 |
| **檢查 Python 版本** | `python --version` | 顯示 Python 版本 |
| **檢查 pip 版本** | `pip --version` | 顯示 pip 版本 |
| **檢查特定套件** | `pip show <套件名稱>` | 顯示特定套件的資訊 (例如 `pip show requests`) |
| **調整 VS Code UI 縮放** | `Ctrl + +` / `Ctrl + -` | 放大/縮小 VS Code 介面 |
| **手動轉換檔案編碼** | VS Code/記事本儲存為 UTF-8 | 解決 `UnicodeDecodeError` |

---

希望這份指南能幫助您在程式開發的道路上建立堅實的基礎，並在不同工作環境中無縫接軌您的專案！如果您在實踐過程中遇到任何問題，請隨時提供具體資訊，我會進一步協助您。
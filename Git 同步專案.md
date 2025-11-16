### 📈 執行計畫：同步 GitHub 並建立分支

**前提：** 此計畫假設您(你)已經在您的電腦上安裝了 Git。

1.  **開啟終端機：** 我(AI)會指導您(你)開啟一個命令提示字元 (CMD) 或 PowerShell，並切換到您(你)的專案根目錄（根據文件，路徑應為 `D:\PYTHON_PROGRAMS\STEWART_PLATFORM_OLD\`）。
2.  **初始化本地 Git 儲存庫：** 我(AI)會提供指令，在該資料夾中建立一個新的 Git 儲存庫。
3.  **新增 `.gitignore`：** 為了保持儲存庫的乾淨，我(AI)會建議您(你)建立一個 `.gitignore` 檔案，用來忽略 `/.venv/` 和 `__pycache__` 等不需要版本控制的檔案。
4.  **建立「穩定基線」 (Main Baseline)：**
    * 我(AI)會指導您(你)將**所有**專案檔案（包括您(你)剛剛上傳的 29 個檔案）添加到 Git 暫存區。
    * 然後，建立一個初始提交 (Initial Commit)。這將完全符合【開發工作流程 步驟一】，將這個版本定義為我們的 `main` 分支（穩定基線）。
5.  **連接到遠端 GitHub：** 我(AI)會提供指令，將您(你)的本地儲存庫連接到您(你)指定的 URL (`https://github.com/jjh650401/Stewart_Platform_old.git`)。
6.  **推送「穩定基線」：** 我(AI)會指導您(你)將 `main` 分支推送到 GitHub。完成後，您(你)將在 GitHub 網站上看到所有專案檔案。
7.  **建立「開發分支」 (Develop Branch)：**
    * 遵照【開發工作流程 步驟二】，在推送完成後，我(AI)會**立即**指導您(你)從 `main` 分支建立一個新的、隔離的「開發分支」。
    * 我們(我)將此分支命名為 `v2.3-kinematics-fix`，以反映我們即將進行的任務（修正 `kinematics.py`）。
8.  **切換分支：** 最後，我(AI)會指導您(你)切換到 `v2.3-kinematics-fix` 分支。

---

### 步驟 1-3：初始化本地儲存庫與 `.gitignore`

請您(你)開啟您的命令提示字元 (CMD) 或 PowerShell，然後**逐一**`執行以下指令。

**1. 切換到您的專案根目錄**
(根據指南，我(AI)假設路徑為 `D:\PYTHON_PROGRAMS\STEWART_PLATFORM\`)

```bash
D:
cd \PYTHON_PROGRAMS\STEWART_PLATFORM
```

*(請根據您的實際路徑調整)*

**2. 初始化 Git 儲存庫**
(此指令會在您的資料夾中建立一個隱藏的 `.git` 資料夾)

```bash
git init
```

**3. 建立 `.gitignore` 檔案**
(此指令將建立一個名為 `.gitignore` 的檔案，並自動寫入規則，以忽略虛擬環境 和 Python 快取檔案)

```powershell
# Windows CMD:
echo /.venv/ >> .gitignore
echo __pycache__/ >> .gitignore

# Windows PowerShell:
Add-Content .gitignore "/.venv/"
Add-Content .gitignore "__pycache__/"
```

*(請根據您(你)使用的終端機類型，選擇上述 CMD 或 PowerShell 指令的其中一組來執行)*

---

### 步驟 4：建立「穩定基線」 (Main Baseline)

請您(你)在同一個終端機視窗中，繼續執行以下指令。

**1. 將所有檔案添加到 Git 暫存區**
(此指令會將您(你)目錄中所有未被 `.gitignore` 忽略的檔案（包括所有 `.py`, `.md`, `.json`, `.txt` 檔案）全部加入)

```bash
git add .
```

**2. 建立您的首次提交 (Initial Commit)**
(這會將所有檔案的當前狀態儲存為 `main` 分支 的「穩定基線」。提交訊息 `v2.2-failed-debug baseline` 對應了 `v2.3 交接清單` 中的版本號。)

```bash
git commit -m "Initial commit: v2.2-failed-debug baseline"
```

---

### 步驟 5-6：連接 GitHub 並推送「穩定基線」

請您(你)在同一個終端機視窗中，繼續執行以下指令。

**1. 更改預設分支名稱為 `main`**
(GitHub 現在預設使用 `main` 作為分支名稱，此指令確保您的本地分支與 GitHub 一致)

```bash
git branch -M main
```

**2. 連接到您(你)的遠端 GitHub 儲存庫**
(此指令會將您(你)提供的 URL 設置為您(你)本地儲存庫的「遠端」目的地)

```bash
git remote add origin https://github.com/jjh650401/Stewart_Platform_old.git
```

**3. 推送您的「穩定基線」到 GitHub**
(此指令會將您(你)本地的 `main` 分支 內容，上傳到 GitHub 的 `origin` 儲存庫中)

```bash
git push -u origin main
```

*(**請注意：** 執行此指令時，您的終端機可能會彈出一個視窗或提示，要求您(你)登入 GitHub 帳號以進行身份驗證。)*

---

### 步驟 7-8：建立並切換到「開發分支」

請您(你)在同一個終端機視窗中，繼續執行以下指令。

**1. 建立新的「開發分支」**
(此指令會從您(你)當前的 `main`（穩定基線） 分支中，建立一個名為 `v2.3-kinematics-fix` 的新分支。這個新分支將用於我們(我)即將進行的 `kinematics.py` 修正工作。)

```bash
git branch v2.3-kinematics-fix
```

**2. 切換到新的「開發分支」**
(此指令會將您(你)的工作環境從 `main` 切換到 `v2.3-kinematics-fix` 分支。**我們(我)所有的程式碼修改都將在這個分支上進行**。)

```bash
git switch v2.3-kinematics-fix
```

---














---
**[規則 8] 尋求確認：**
以上是我(AI)的執行計畫。請問您是否同意我(AI)依照此計畫，開始提供第一組操作指令（步驟 1-3：初始化與 `.gitignore`）？

### 執行計畫：同步專案至 GitHub

遵照【規則 5】和【規則 6】，以下是操作的描述性邏輯：

#### A. 準備工作 (必要前提)

1.  **安裝 Git：** 請確保您(你)的電腦上已經安裝了 Git。
2.  **SSH 金鑰：** 由於您(你)提供了 SSH 格式的連結 (`git@github.com:...`)，請確保您(你)已經在 GitHub 帳戶中設定了 SSH 公開金鑰。
3.  **專案目錄：** 請開啟一個終端機 (Terminal) 或命令提示字元 (Command Prompt)，並切換到您(你)的專案根目錄（例如 `D:\PYTHON_PROGRAMS\STEWART_PLATFORM\`）。

#### B. 操作步驟 (描述性邏輯)

1.  **初始化本地倉庫 (`git init`)：**
    我們需要將您(你)的本地專案資料夾轉換為一個 Git 倉庫。
2.  **建立 `.gitignore` (強烈建議)：**
    我們需要建立一個 `.gitignore` 檔案，告訴 Git 忽略不需要追蹤的檔案，例如 `.venv` 虛擬環境資料夾 和 `__pycache__` 緩存。
3.  **加入所有檔案 (`git add .`)：**
    我們將把所有 29 個專案檔案（以及 `.gitignore`）加入到 Git 的「暫存區」。
4.  **建立「穩定基線」快照 (`git commit`)：**
    我們將建立第一個「提交」(commit)，這將是我們的「穩定基線」。我們將其標記為 `v2.2-failed-debug`，以反映當前的程式狀態。
5.  **連結遠端 GitHub 倉庫 (`git remote add`)：**
    我們需要告訴本地倉庫，您(你)在 GitHub 上建立的遠端倉庫位置。
6.  **重新命名主分支 (`git branch -M`)：**
    為符合現代 Git 慣例，我們將本地的主分支命名為 `main`。
7.  **推送「穩定基線」到 GitHub (`git push`)：**
    我們將把 `main` 分支（即我們的「穩定基線」）上傳到 GitHub。
8.  **建立「開發分支」 (`git checkout -b`)：**
    遵照【規則 3】 和【開發工作流程 步驟二】，我們將立即從 `main` 基線建立一個新的「開發分支」，所有的修改都將在這個新分支上進行。
9.  **推送「開發分支」到 GitHub (`git push`)：**
    我們也將這個新的「開發分支」 推送到 GitHub，以確保它已被遠端備份。

-----

### C. 操作指令

請在您(你)的專案根目錄下，依序執行以下指令：

```bash
# 步驟 1：初始化本地倉庫
git init

# 步驟 2：(建議) 建立 .gitignore 檔案
# (您可以手動建立 .gitignore 檔案，或使用以下指令 [Windows])
echo .venv/ > .gitignore
echo __pycache__/ >> .gitignore
echo *.db >> .gitignore
echo *.db-journal >> .gitignore

# 步驟 3：加入所有檔案到暫存区
git add .

# 步驟 4：建立「穩定基線」快照 (Commit)
# 我們使用 v2.3 交接清單 中的版本號作為提交訊息
git commit -m "Initial commit: v2.2-failed-debug baseline"

# 步驟 5：連結遠端 GitHub 倉庫
# (請使用您(你)提供的 SSH 連結)
git remote add origin git@github.com:jjh650401/Stewart_Platform_old.git

# 步驟 6：將目前的主分支重新命名為 'main'
git branch -M main

# 步驟 7：推送「穩定基線」 (main 分支) 到 GitHub
# -u 參數會將本地 main 分支設置為預設追蹤遠端 main 分支
git push -u origin main

# 步驟 8：建立並切換到新的「開發分支」 (符合【開發工作流程 步驟二】)
# 我們將其命名為 v2.3-kinematics-fix，以反映我們即將進行的任務
git checkout -b v2.3-kinematics-fix

# 步驟 9：將新的「開發分支」也推送到 GitHub
git push -u origin v2.3-kinematics-fix
```

-----

**[規則 11] 任務提醒：**
我(AI)已完成了「提供 Git 同步指令」 的任務。

在您(你)確認已在本地的 `v2.3-kinematics-fix` 分支上，並且 `main` 和 `v2.3-kinematics-fix` 兩個分支都已成功推送到 GitHub 之後，我(AI)的下一步計畫 將是（重新提出）修正 `kinematics.py` 的執行計畫。

**請問您(你)是否同意我(AI)的下一步行動（在您(你)完成 Git 操作後，提出 `kinematics.py` 的修正計畫）？**
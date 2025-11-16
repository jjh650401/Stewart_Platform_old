弆### **檔案：`Git 協作操作指南_v3_0.md` (v3.0.2 協作與除錯增補版)**

**版本：** 3.0.2
**日期：** 2025年10月26日
**目的：** 本指南定義了您 (總工程師) 與我 (AI 開發者) 之間，使用 `Git (版本控制)` 與 `GitHub (一個線上的 Git 儲存庫平台)` 進行協作的標準作業流程 (SOP)，並包含了初始設定的常見除錯指南。

---

**[AI 開發者註記]**：
我們目前在 `main (主分支)` 上。我將提供 `Git 協作操作指南_v3_0.md` 的**完整更新版**（v3.0.2）。這份文件將**無省略地**包含所有舊章節、增補的除錯章節、以及所有指令的參數說明。

---

### **第零部分：(可選) 清理舊的或混亂的 `Git` 紀錄**

**情境：** 當 `VS Code (視覺化程式碼編輯器)` 顯示「過多使用中的變更」或 `Git (版本控制)` 狀態混亂時，代表此處可能已存在一個舊的、設定不當的 `Git repository (儲存庫)`。

**目標：** 徹底刪除舊的 `Git (版本控制)` 歷史紀錄，以便建立一個全新的、乾淨的連結。

**操作步驟 (在您的 Windows 命令提示字元 (cmd) 執行)：**

1.  **進入專案目錄：**

    ```bash
    cd D:\Python_Programs\Stewart_Platform
    ```

      * **指令說明：**
          * `cd`: 指令 "Change Directory (變更目錄)"，用於切換目前所在的資料夾位置。

2.  **(關鍵) 強制刪除舊的 `Git` 紀錄：**

    ```bash
    rmdir /s /q .git
    ```

      * **指令說明：**
          * `rmdir`: Windows 指令 "Remove Directory (移除目錄)"。
          * `/s`: 參數 "Subdirectories (子目錄)"，代表刪除該目錄 (`.git`) 及其下的所有子目錄和檔案。
          * `/q`: 參數 "Quiet (安靜模式)"，代表刪除時不需要逐一確認，強制執行。
          * `.git`: `Git (版本控制)` 儲存庫 (repository) 的隱藏資料夾名稱。

3.  **(關鍵) 建立 `.gitignore` 檔案：**

      * 在執行「第一部分」的 `git init (初始化)` 之前，您**必須**在專案根目錄手動建立一個名為 `.gitignore` 的檔案。
      * **目的：** 此檔案會告訴 `Git (版本控制)` 哪些檔案或資料夾（例如 `.\.venv`）應該**永遠被忽略**，從而避免「過多變更」的錯誤。
      * **[AI 開發者註記]**：我已在之前的對話中提供此檔案的內容，請確保它已存在且內容正確。

---

### **第一部分：初始階段 (一次性設定)**

**目標：** 將您本地的專案資料夾與您的遠端 `GitHub repository (儲存庫)` 進行連結，並提交我們目前所有的程式碼作為 `v3.0` 的第一個「初始提交 (Initial Commit)」。

**操作步驟 (在您的 Windows 命令提示字元 (cmd) 執行)：**

1.  **進入專案目錄：**

    ```bash
    cd D:\Python_Programs\Stewart_Platform
    ```

2.  **確認 `.gitignore` 檔案已存在。** (參考第零部分)

3.  **初始化 `Git (版本控制)`：**

    ```bash
    git init
    ```

      * **指令說明：**
          * `git`: `Git (版本控制)` 系統的主程式。
          * `init`: 指令 "Initialize (初始化)"，在目前資料夾建立一個新的、隱藏的 `.git` 子目錄，使其成為一個 `Git repository (儲存庫)`。

4.  **連結遠端 `GitHub` 儲存庫 (repository)：**

    ```bash
    A add origin https://github.com/jjh650401/stewart_platform.git
    ```

      * **指令說明：**
          * `remote`: `Git (版本控制)` 的 "遠端 (remote)" 管理指令。
          * `add`: 新增一個遠端 (remote)。
          * `origin`: 遠端 (remote) 的「別名 (alias)」。`origin` 是標準預設名稱，代表您在 `GitHub` 上的主要 `repository (儲存庫)`。
          * `https://...`: 您的 `repository (儲存庫)` 網址 (我們已確認使用 `HTTPS (安全超文字傳輸協定)` 格式)。

5.  **將所有檔案加入 `Git (版本控制)` 追蹤：**

    ```bash
    git add .
    ```

      * **指令說明：**
          * `add`: `Git (版本控制)` 的 "添加 (add)" 指令，將檔案的「變更」從「工作目錄」加入到「暫存區 (Staging Area)」，準備 `commit (提交)`。
          * `.`: 代表「目前目錄下的所有變更」(`.gitignore` 中列出的檔案會被自動忽略)。

6.  **建立您的第一個「提交 (Commit)」：**

    ```bash
    git commit -m "v3.0.3: 建立基礎專案骨架與 UI 介面 (已清理)"
    ```

      * **指令說明：**
          * `commit`: `Git (版本控制)` 的 "提交 (commit)" 指令，將「暫存區 (Staging Area)」中的所有變更，建立一個永久的「快照 (snapshot)」並儲存到本地 `repository (儲存庫)`。
          * `-m`: 參數 "Message (訊息)"，允許您在指令列中直接附加一行「提交訊息 (commit message)」。

7.  **將本地分支 (branch) 重新命名為 `main`：**

      * (部分 `Git (版本控制)` 用戶端 (client) 預設會建立 `master` 分支 (branch))

    <!-- end list -->

    ```bash
    git branch -m master main
    ```

      * **指令說明：**
          * `branch`: `Git (版本控制)` 的 "分支 (branch)" 管理指令。
          * `-m`: 參數 "Move (移動/重新命名)"。
          * `master`: 舊的分支 (branch) 名稱。
          * `main`: 您想要使用的新分支 (branch) 名稱。

8.  **將 `main (主分支)` 推送 (Push) 至 `GitHub`：**

    ```bash
    git push -u origin main
    ```

      * **指令說明：**
          * `push`: `Git (版本控制)` 的 "推送 (push)" 指令，將您本地的 `commit (提交)` 上傳到遠端 `repository (儲存庫)`。
          * `-u`: 參數 "Set Upstream (設定上游)"，建立一個永久連結。未來您只需輸入 `git push`，`Git (版本控制)` 就會自動知道您要推送到 `origin` 的 `main` 分支 (branch)。(此為一次性設定)
          * `origin`: 遠端 (remote) 的別名。
          * `main`: 您要推送 (push) 的分支 (branch) 名稱。

---

### **第二部分：平時開發流程 (AI 協作與上傳)**

**目標：** 這是我們未來最常用的流程。我會在「開發分支 (feature branch)」上提供程式碼，您審核後，再將其「合併 (merge)」回「穩定基線 (main branch)」。

**情境模擬 (我們的互動模式)：**

1.  **我 (AI) 說：**
    「好的，我們來開始新功能。請建立一個 `feature/geometry-linking` 分支 (branch)。」

2.  **您 (總工程師) 執行：**

    ```bash
    git checkout main
    git checkout -b feature/geometry-linking
    ```

      * **指令說明：**
          * `checkout`: `Git (版本控制)` 的 "切換 (checkout)" 指令，用來切換分支 (branch)。
          * `-b`: 參數 "Branch (分支)"，代表「建立 (create) *並* 切換到 (checkout)」一個新的本地分支 (branch)。

3.  **(您與 AI 互動，修改程式碼並儲存...)**

4.  **我 (AI) 說：**
    「所有檔案都已提供完畢。請將這個新功能『提交 (commit)』到 `feature` 分支 (branch)。」

5.  **您 (總工程師) 執行：**

    ```bash
    git add .
    git commit -m "feat: 實作 6-DOF 即時計算與 UI 佈局"
    ```

      * **指令說明：**
          * `add .`: 將所有修改過的檔案加入「暫存區 (Staging Area)」。
          * `commit -m "..."`: 將暫存的變更建立一個「提交 (commit)」。

6.  **我 (AI) 說：**
    「功能已完成，您是否同意將此 `feature (功能)` 分支 (branch) 合併 (merge) 回 `main (主分支)`？」

7.  **您 (總工程師) 說：** 「同意。」

8.  **您 (總工程師) 執行：**

      * (1. 切換回 `main (主分支)`)
        ```bash
        git checkout main
        ```
      * (2. 將 `feature` 分支 (branch) 的變更合併 (merge) 進來)
        ```bash
        git merge feature/geometry-linking
        ```
          * **指令說明：**
              * `merge`: `Git (版本控制)` 的 "合併 (merge)" 指令，將另一個分支 (branch) (`feature/geometry-linking`) 的歷史紀錄，合併 (merge) 到您「目前所在」的分支 (branch) (即 `main`)。
      * (3. 將合併 (merge) 後的 `main (主分支)` 推送 (push) 到 `GitHub`)
        ```bash
        git push origin main
        ```
          * **指令說明：**
              * (由於 `main` 分支 (branch) 已經用 `-u` 連結過，未來推送 (push) `main` 分支 (branch) 時，技術上只需 `git push` 即可，但寫明 `origin main` 更為清晰。)
      * (4. (可選) 刪除已完成的本地 `feature (功能)` 分支 (branch))
        ```bash
        git branch -d feature/geometry-linking
        ```
          * **指令說明：**
              * `branch`: `Git (版本控制)` 的 "分支 (branch)" 管理指令。
              * `-d`: 參數 "Delete (刪除)"，安全地刪除一個「已經被合併 (merge)」的分支 (branch)。

---

### **第三部分：從 `GitHub` 下載 (同步)**

**目標：** 當您在另一台電腦，或 `GitHub` 上的版本比您本地還新時，用來同步。

**操作步驟：**

1.  **確保您在 `main (主分支)` 上：**
    ```bash
    git checkout main
    ```
2.  **拉取 (Pull) 遠端 `GitHub` 的最新變更：**
    ```bash
    git pull origin main
    ```
      * **指令說明：**
          * `pull`: `Git (版本控制)` 的 "拉取 (pull)" 指令，從遠端 `repository (儲存庫)` (`origin`) 下載 `main` 分支 (branch) 的最新 `commit (提交)`，並自動「合併 (merge)」到您本地的 `main` 分支 (branch)。

---

### **第四部分：如何回溯 (復原旧版)**

**目標：** 保障「可回溯性」。

#### **情境一：放棄「開發中」的錯誤 (最常用、最安全)**

如果我們在 `feature` 分支 (branch) 上把一切都改亂了，但**還沒有**合併 (merge) 回 `main (主分支)`：

1.  **切換回穩定的 `main (主分支)`：**
    ```bash
    git checkout main
    ```
2.  **強制刪除錯誤的 `feature (功能)` 分支 (branch)：**
    ```bash
    git branch -D feature/bad-feature
    ```
      * **指令說明：**
          * `-D`: (大寫 D) 參數 "Delete --force (強制刪除)"，強制刪除一個分支 (branch)，*即使它還沒有被合併 (merge)*。

#### **情境二：復原「已合併」的錯誤 (緊急情況)**

如果我們不小心將一個錯誤的 `commit (提交)` 合併 (merge) 到了 `main (主分支)`：

1.  **查看歷史紀錄：**
    ```bash
    git log --oneline
    ```
      * **指令說明：**
          * `log`: `Git (版本控制)` 的 "日誌 (log)" 指令，顯示 `commit (提交)` 歷史。
          * `--oneline`: 參數 "One Line (單行)"，將每一次 `commit (提交)` 壓縮成一行顯示，使其更易於閱讀。
2.  **安全地「復原 (Revert)」：**
      * (假設 `a1b2c3d` 是您想復原的那個錯誤 `commit (提交)` 的 `hash (雜湊值)`)
    <!-- end list -->
    ```bash
    git revert a1b2c3d
    ```
      * **指令說明：**
          * `revert`: `Git (版本控制)` 的 "復原 (revert)" 指令，建立一個「反向 (inverse)」的 `commit (提交)` 來「抵銷」掉某個舊的 `commit (提交)` (`a1b2c3d`)。這是最安全的回溯方式，因為它**不會**改寫歷史紀錄。
3.  **推送 (Push) 復原結果：**
    ```bash
    git push origin main
    ```

---

### **[新增] 第五部分：初始設定除錯指南**

**情境：** 當您在執行「第一部分：初始階段」時遇到錯誤，請參考以下解決方案。

#### **問題一：`fatal: ambiguous argument 'HEAD~1'`**

  * **觸發指令：** `git reset --soft HEAD~1`
  * **原因分析：** 這是因為 `commit (提交)` 是 `root-commit (根提交)`，它沒有「前一個」 `commit (提交)` (`HEAD~1`)，導致指令失敗。
  * **解決方案：** 使用 `update-ref` 指令來安全地撤銷 `root-commit (根提交)`。
    ```bash
    git update-ref -d HEAD
    ```
      * **指令說明：**

          * `update-ref`: `Git (版本控制)` 的底層指令 "Update Reference (更新參照)"。
          * `-d`: 參數 "Delete (刪除)"。
          * `HEAD`: `Git (版本控制)` 中指向「目前 `commit (提交)`」的指標 (pointer)。
          * **(組合意義)**：強制刪除 `HEAD (當前)` 指標，安全地撤銷 `root-commit (根提交)`，讓所有檔案回到「已 `add (添加)`」但未 `commit (提交)` 的狀態。

      * **後續步驟：** 撤銷後，您必須先建立 `.gitignore` 檔案，然後再執行 `git reset` (清空暫存區)、`git add .` (重新添加) 和 `git commit` (重新提交)。

#### **問題二：`git@github.com: Permission denied (publickey)`**

  * **觸發指令：** `git push -u origin main`
  * **原因分析：** 這是因為 `git remote add` 時使用了 `git@github.com:...` 的 `SSH (安全殼層協定)` 位址，但您的電腦尚未設定 `SSH Key (SSH 金鑰)` 供 `GitHub` 驗證。
  * **解決方案：** 移除 `SSH (安全殼層協定)` 的遠端 (remote)，改用 `HTTPS (安全超文字傳輸協定)` 網址，`HTTPS (安全超文字傳輸協定)` 會彈出視窗要求您輸入帳號密碼 (或 `Token (權杖)`)。
      * (1. 移除舊的 `origin (來源)`)
        ```bash
        git remote remove origin
        ```
      * (2. 添加新的 `HTTPS (安全超文字傳輸協定)` `origin (來源)`)
        ```bash
        git remote add origin https://github.com/jjh650401/stewart_platform.git
        ```
      * (3. 重新 `push (推送)`)
        ```bash
        git push -u origin main
        ```

#### **問題三：`! [rejected] main -> main (fetch first)`**

  * **觸發指令：** `git push -u origin main` (在使用 `HTTPS (安全超文字傳輸協定)` 之後)
  * **原因分析：** 您的本地 `repository (儲存庫)` 和遠端 `GitHub repository (儲存庫)` 的歷史紀錄**各自獨立 (diverged)**。通常是因為 `GitHub` 專案在建立時勾選了「`Add a README file` (添加 README 檔案)」，導致遠端 (remote) 已經有了一個 `GitHub` 自動產生的「`Initial commit` (初始提交)」。
  * **解決方案：** 使用「強制推送 (Force Push)」，用您本地「乾淨的」 `commit (提交)` 紀錄，覆蓋掉 `GitHub` 上舊的紀錄。
    ```bash
    git push --force origin main
    ```
      * **指令說明：**
          * `--force` (或 `-f`): 參數 "Force (強制)"，忽略遠端 (remote) 的歷史紀錄，強制使用您本地的 `commit (提交)` 紀錄覆蓋它。
          * **(安全警告)**：此操作在**專案初始化**且您是**唯一開發者**時是安全的。但在多人協作的專案中，**切勿**隨意使用 `force push (強制推送)`。

---

# 在 VS Code 和 GitHub 上建立 v4.7 開發分支

# 步驟 1: 切換到您的「穩定基線」(main) 分支
# (我們假設您的主分支叫做 'main')
git checkout main

# 步驟 2: 確保您的「穩定基線」是最新版本
git pull origin main

# 步驟 3: 從 'main' 建立我們的新開發分支
# (v4.7-kinematics-analysis)
git branch v4.7-kinematics-analysis

# 步驟 4: 切換到您剛剛建立的新分支
git checkout v4.7-kinematics-analysis

# 步驟 5: 將這個新分支推送到 GitHub (origin)
# (-u 會設定此本地分支追蹤遠端的同名分支)
git push -u origin v4.7-kinematics-analysis

---

刪除 feature/3d-drawing 分支

# 步驟 1: 刪除您電腦上的「本地」分支
# ( -d 會安全地刪除，如果它尚未合併，則會警告您)
git branch -d feature/3d-drawing

# 步驟 2: 刪除 GitHub (origin) 上的「遠端」分支
git push origin --delete feature/3d-drawing

---

### 關於合併 v4.7 分支的建議

**我的建議是：是的，現在是將 `v4.7` 合併回 `main`（主支）的最佳時機。**

**理由（根據我們的規則）：**

我們嚴格遵循了 `基礎背景與規則 v5 優化版.md` 中定義的「開發工作流程」。

1.  **[步驟 4：程式碼實作]** 我們(AI)已經完成了 v4.7 分支的所有開發工作。
2.  **[步驟 5：回歸測試]** 我們(AI)已經執行了回歸測試。
3.  **[步驟 5：結果]** 測試結果證實：
      * **v4.6 舊功能（幾何計算）** 仍然穩定運作。
      * **v4.7 新功能（節點擺角分析）** 現已成功運作。

`v4.7` 分支 現在是一個**已通過測試的穩定版本**。根據 [規則 v5.1 步驟 5]，我們(AI)應執行「合併」操作，將這個「開發分支」更新回我們的「穩定基線 (`main`)」。

---

### GitHub 操作指令建議

以下是將您的 v4.7 工作安全地合併到 `main` 並更新到 GitHub 的建議指令流程。

**(假設您目前位於 `v4.7-kinematics-analysis` 分支上)**

#### 步驟一：提交 v4.7 分支上的所有最終更改

首先，我們(AI)將所有 v4.7 的最終偵錯修正（v4.7.2 到 v4.7.6）提交到您的本地 `v4.7` 分支。

```bash
# 1. 將所有修改過的檔案加入暫存區
# (這包括 kinematics_engine.py, analysis_engine.py, state_manager.py, 
#  analysis_widget.py, main_window.py)
git add src/core/kinematics_engine.py src/core/analysis_engine.py src/core/state_manager.py src/gui/controls/analysis_widget.py src/gui/main_window.py

# 2. 提交一個清晰的訊息，總結 v4.7 的所有工作
git commit -m "v4.7: 完成運動學分析 (LHS) 並修復所有偵錯 (IK, einsum, 角度檢查)"
```

#### 步驟二：將 v4.7 開發分支推送到 GitHub

在合併前回傳開發分支是一個好習慣，可以備份您的工作。

```bash
# 3. 將 v4.7 分支推送到 GitHub (origin)
git push origin v4.7-kinematics-analysis
```

#### 步驟三：執行合併（v4.7 -\> main）

現在我們(AI)執行 `基礎背景與規則 v5 優化版.md` 中定義的合併步驟。

```bash
# 4. 切換回您的「穩定基線」 (main)
git checkout main

# 5. 確保您的 main 分支是最新版本（以防萬一）
git pull origin main

# 6. 將 v4.7 分支的成果合併進 main
git merge v4.7-kinematics-analysis
```

#### 步驟四：將合併後的 main 推送到 GitHub

最後，將已更新的「穩定基線」推送到 GitHub。

```bash
# 7. 將合併後的 main 推送到 GitHub
git push origin main
```

---

**v4.7 任務完成提示：**

`v4.7-kinematics-analysis` 分支 的任務已全部完成，並且**已合併回 `main`**。

我們(AI)現在已經準備好，可以從這個**新**的、**穩定**的 `main` 基線開始，建立我們的下一個開發分支。

---

# 建立 v4.8-workspace-analysis 開發分支 所需的操作指令：

# 1. 確保您在 main 分支上（如果上一步驟還沒切換的話）
git checkout main

# 2. 再次確保您的本地 main 分支與 GitHub (origin) 完全同步
git pull origin main

# 3. 從 main 建立我們的新 v4.8 開發分支
git branch v4.8-workspace-analysis

# 4. 切換到新建立的 v4.8 分支
git checkout v4.8-workspace-analysis
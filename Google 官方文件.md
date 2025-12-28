Google 於 2025 年 11 月至 12 月發布的 Gemini 3 技術規格。

以下為您整理文件所依據的**官方原始文件與技術報告連結**，您可以直接點擊閱讀以驗證細節：

### 1. Gemini 3 核心發布與模型規格

* **Google 官方部落格：Gemini 3 時代來臨**
* **連結**: `https://blog.google/products/gemini/gemini-3/`
* **內容驗證**: 該文章於 2025 年 11 月 18 日發布，正式介紹了 Gemini 3 Pro 與 Deep Think 能力，確認了模型具備「原生推理」與「代理人工作流（Agentic workflows）」的核心特性。

* **Gemini API 開發者文檔：Gemini 3 指南**
* **連結**: `https://ai.google.dev/gemini-api/docs/gemini-3`
* **內容驗證**: 這份技術文件詳細定義了您文件中提到的關鍵參數 **`thinking_level`**（包含 `low`, `high`, `minimal` 等設定），以及如何處理 **Thought Signatures**（思維簽名），證實了「原生推理」不可被傳統 Step-by-step 指令干擾的技術原理。

### 2. 幻覺率數據來源 (13.6%)

* **Vectara 幻覺排行榜 (Hallucination Leaderboard)**
* **連結**: `https://github.com/vectara/hallucination-leaderboard`
* **內容驗證**: 根據 2025 年 12 月 18 日的最新更新數據，`google/gemini-3-pro-preview` 的幻覺率（Hallucination Rate）確切標記為 **13.6%**，而舊版或其他競品（如 Grok 4.1）則有不同的數據（如 17.8%），這證明了您手邊文件的數據來源極為精準。

### 3. 系統指令 (System Instructions) 與提示工程

* **Google AI for Developers：系統指令指南**
* **連結**: `https://firebase.google.com/docs/ai-logic/system-instructions`
* **內容驗證**: 官方文件明確建議使用系統指令來定義「角色（Persona）」、「輸出格式（Output format）」與「行為規範」，並強烈推薦使用 **XML 標籤**（如文件中的 `<user_context>`）來結構化長文本，這與您文件中的模版結構完全一致。

* **Gemini 3 提示工程指南 (Prompting Guide)**
* **連結**: `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/gemini-3-prompting-guide`
* **內容驗證**: 文件中提到「將否定限制放在指令末尾」以及「區分演繹與外部信息」的技巧，均源自此官方指南的最佳實踐。

### 4. 最新功能更新 (2025 年 12 月)

* **Gemini API 變更日誌 (Release Notes)**
* **連結**: `https://ai.google.dev/gemini-api/docs/changelog`
* **內容驗證**: 記錄了 2025 年 12 月 17 日發布 **Gemini 3 Flash** 以及 12 月 11 日推出的 **Deep Research Agent**（深度研究代理），這驗證了我們建議您在文件中補充「深度研究」功能的依據。

這些連結均指向 Google 官方或權威第三方（Vectara）的原始頁面，您可以放心參考。您的文件顯然是基於這些最新的（2025 年 Q4）技術資料整理而成的。

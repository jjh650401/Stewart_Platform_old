# D:\Python_Programs\Stewart_Platform\src\core\config.py

# ==============================================================================
# Stewart Platform Simulator - 中央設定檔 (Central Configuration)
# ==============================================================================
#
# 說明：
# 這個檔案集中管理了整個應用程式的所有可調整參數與預設值。
# 當需要微調程式的視覺表現、預設行為或演算法精度時，
# 應優先修改此檔案中的數值，而非直接修改程式邏輯檔案。
#
# [架構性註記] 單位系統標準 (Architectural Note: Unit System Standard)
# 根據 v5 開發規則，本專案所有長度單位統一使用毫米 (mm)。
# UI層、核心層的所有長度參數的儲存、傳遞與計算皆以 mm 為準。
# 詳情請參閱《基礎背景與規則.v5.md》。
# 「單位正常化」、「變數名稱 v2.0 對齊」、並完整保留與更新了所有中文註記

# ==============================================================================
# 區域一：3D 視覺化設定 (用於 src/gui/pyvista_widget.py)
# ==============================================================================

# --- 攝影機與視角 ---
CAMERA_ZOOM_FACTOR = 1.2      # 自動視角重置後的放大倍率。大於 1.0 為放大，小於 1.0 為縮小。
AXIS_PADDING_FACTOR = 1.05      # 座標軸相對於模型尺寸的留白倍率。1.1 代表座標軸比模型長 5%。

# --- 繪圖樣式 ---
STYLE_BACKGROUND_COLOR = 'white'
STYLE_BASE_FRAME_COLOR = 'darkgray'      # 固定平台顏色
STYLE_MOBILE_FRAME_COLOR = '#B22222'     # 活動平台顏色
STYLE_LEG_COLOR = 'gold'                 # 連桿顏色
STYLE_AXIS_COLOR = 'gray'                # 座標軸線條顏色
STYLE_AXIS_FONT_COLOR = 'black'          # 座標軸刻度與標籤顏色
STYLE_NODE_LABEL_BASE_BG = 'lightgray'      # 固定平台節點標籤(A1,A2...)背景色
STYLE_NODE_LABEL_MOBILE_BG = 'lightgray'    # 活動平台節點標籤(B1,B2...)背景色
STYLE_NODE_LABEL_FONT_COLOR = 'black'       # 節點標籤字體顏色
STYLE_NORMAL_VECTOR_BASE_COLOR = 'cyan'     # 固定平台法線顏色
STYLE_NORMAL_VECTOR_MOBILE_COLOR = 'magenta' # 活動平台法線顏色
STYLE_CENTER_LABEL_COLOR_BASE = 'blue'    # 固定平台中心點標籤顏色
STYLE_CENTER_LABEL_COLOR_MOBILE = 'red'     # 活動平台中心點標籤顏色
STYLE_CENTER_LABEL_FONT_SIZE = 12           # 中心點標籤的字體大小
STYLE_CENTER_POINT_SIZE = 5                 # 中心點標記的大小

# 線寬與粗細
STYLE_BASE_FRAME_LINE_WIDTH = 5
STYLE_MOBILE_FRAME_LINE_WIDTH = 5
STYLE_LEG_LINE_WIDTH = 3
STYLE_NORMAL_VECTOR_RADIUS = 3 # 單位: mm (原 0.003m)

# 字體與點大小
STYLE_AXIS_FONT_SIZE = 10
STYLE_NODE_LABEL_FONT_SIZE = 10
STYLE_NODE_POINT_SIZE = 15

# ==============================================================================
# 區域二：GUI 互動與預設值 (用於 src/gui/controls/*)
# ==============================================================================

# --- 參數輸入框 (GeometryWidget) ---
DEFAULT_INPUT_RANGE = (0.0, 20000.0) # 單位: mm
DEFAULT_INPUT_STEP = 10.0 # 單位: mm

# --- 姿態控制滑塊 (AnalysisWidget) ---
SLIDER_PRECISION_FACTOR = 10.0
DEFAULT_SLIDER_RANGES = {
    'x': (-200, 200, 0), 'y': (-200, 200, 0), 'z': (-150, 150, 0), # 單位: mm
    'roll': (-30, 30, 0), 'pitch': (-30, 30, 0), 'yaw': (-45, 45, 0) # 單位: deg
}

# --- 動畫展演 (AnalysisWidget) ---
ANIMATION_FRAME_INTERVAL_MS = 33
DEFAULT_ANIMATION_DURATION_S = 10.0
ANIMATION_DURATION_RANGE_S = (1.0, 300.0)

# --- UI 預設選項 ---
UI_LOAD_CONDITIONS = ["理想負載 (中心)", "水平偏心負載"]
ANGLE_LIMIT_PRESETS = [
    ('自訂', None), ('標準工業級 (±45°)', 45.0),
    ('高機動性需求 (±60°)', 60.0), ('小型/桌上型 (±30°)', 30.0)
]

# --- UI 元件尺寸 ---
UI_INPUT_FIELD_WIDTH = 150

# ==============================================================================
# 區域三：GUI 佈局設定 (用於 main.py 和 src/gui/main_window.py)
# ==============================================================================
UI_WINDOW_CONTENT_MARGIN = 5
UI_SPLITTER_LEFT_WIDTH = 550
UI_SPLITTER_RIGHT_WIDTH = 450

# ==============================================================================
# 區域四：GUI 介面字體設定 (用於 main_window.py)
# ==============================================================================
FONT_UI_NAME = "Microsoft JhengHei"
FONT_UI_SIZE = 9

# ==============================================================================
# 區域五：PDF 報告字體設定 (用於 src/core/report_generator.py)
# ==============================================================================
FONT_PATH_CHINESE = 'C:/Windows/Fonts/kaiu.ttf'
FONT_PATH_CHINESE_FALLBACK = 'C:/Windows/Fonts/msjh.ttc'
FONT_PATH_LATIN = 'C:/Windows/Fonts/GOTHIC.TTF'

# ==============================================================================
# 區域六：核心計算與演算法 (用於 src/core/*)
# ==============================================================================
# --- MODIFIED: Changed to mm/s^2 to match the new mm-based unit system ---
G_ACCELERATION = 9806.65  # 標準重力加速度 (mm/s²)，用於力學計算

GEOMETRY_SOLVER_TOLERANCE = 1e-9 # 基於 mm 尺度的幾何求解器公差
WORKSPACE_SOLVER_TOLERANCE = 1e-7 # 基於 mm 尺度的空間分析求解器公差
ALGO_LHS_SAMPLES = 2000
ALGO_SQP_CANDIDATES = 10
ALGO_DETERMINISTIC_SEED = 42

# ==============================================================================
# 區域七：動力學模型參數 (用於 src/core/dynamics_engine.py)
# ==============================================================================
DYN_INERTIA_APPROX_SCALAR = 0.1

# ==============================================================================
# 區域八：視覺化微調 (用於 src/gui/pyvista_widget.py)
# ==============================================================================
VIZ_VIEW_HISTORY_SIZE = 20

# ==============================================================================
# 區域九：驅動系統計算模組 (用於 src/gui/controls/drive_system_widget.py)
# ==============================================================================
DRIVE_DEFAULT_FRICTION_COEFF = 0.01
LOAD_FACTOR_RANGES = {
    'v_max < 15': {'min': 1.0, 'max': 1.2, 'default': 1.1},
    '15 <= v_max < 60': {'min': 1.2, 'max': 1.5, 'default': 1.35},
    'v_max >= 60': {'min': 1.5, 'max': 3.0, 'default': 2.2}
}
SCREW_MIN_DIAMETER = 10.0        # 螺桿最小桿徑 (mm)
SCREW_LEAD_MM_MIN = 5.0          # 螺桿導程最小值 (mm)
SCREW_LEAD_MM_MAX = 50.0         # 螺桿導程最大值 (mm)
# --- MODIFIED: Renamed variable to align with v2.0 spec ---
DRIVE_DEFAULT_REDUCTION_RATIO_I = 2.0 # 預設減速比 (i)

# ==============================================================================
# 區域十：儀表板佈局設定 (用於 src/gui/controls/drive_system_widget.py)
# ==============================================================================
DRIVE_DASHBOARD_STRETCH_LEFT = 45
DRIVE_DASHBOARD_STRETCH_RIGHT = 55
DRIVE_DASHBOARD_WIDTH = 980
DRIVE_DASHBOARD_HEIGHT = 760

# ==============================================================================
# 區域十一：啟動行為設定 (用於 main.py)
# ==============================================================================
STARTUP_SHOW_3D_PREVIEW = False

# ==============================================================================
# 區域十二：分析與視覺化預設值 (用於 src/gui/controls/analysis_widget.py)
# ==============================================================================
VIZ_DEFAULT_LOOP_ANIMATION = False
VIZ_DEFAULT_SHOW_ANGLES = False
VIZ_DEFAULT_SHOW_COORDS = False

# ==============================================================================
# 區域十三：求解器穩定性參數 (用於 src/core/kinematics.py)
# ==============================================================================
# 用於在啟用關節角度限制時，尋找可行起始姿態的微調步長 (單位: mm)
SOLVER_FEASIBILITY_SEARCH_STEP = 0.1

# 用於尋找可行姿態時的最大迭代次數，以防止無限迴圈
# (例如 200 次代表允許向上和向下各嘗試 100 次)
SOLVER_FEASIBILITY_MAX_ITERATIONS = 200
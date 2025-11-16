# D:\Python_Programs\Stewart_Platform\src\core\state_manager.py

class StateManager:
    """
    一個集中管理應用程式所有狀態的類別。
    這是應用程式狀態的唯一真實來源 (Single Source of Truth)。
    """
    def __init__(self):
        print("狀態管理器 (StateManager) v1.0 已初始化。")
        self.reset()

    def reset(self):
        """將所有狀態重置為初始預設值，用於新建專案。"""
        self._platform_type = "6-DOF"
        self._is_dirty = False
        self._current_project_path = None
        self._workspace_limits = None
        self._mechanical_workspace_limits = None
        self._global_force_result = None # [新增]
        self._angle_range_result = None  # [新增]
        print("狀態管理器已重置為初始狀態。")

    # --- Getters ---
    def get_platform_type(self) -> str:
        return self._platform_type

    def is_dirty(self) -> bool:
        return self._is_dirty

    def get_project_path(self) -> str | None:
        return self._current_project_path

    def get_workspace_limits(self) -> dict | None:
        return self._workspace_limits

    def get_mechanical_workspace_limits(self) -> dict | None:
        return self._mechanical_workspace_limits

    def get_global_force_result(self) -> dict | None: # [新增]
        return self._global_force_result

    def get_angle_range_result(self) -> dict | None: # [新增]
        return self._angle_range_result

    # --- Setters ---
    def set_platform_type(self, p_type: str):
        self._platform_type = p_type

    def set_dirty(self, is_dirty: bool):
        self._is_dirty = is_dirty

    def set_project_path(self, path: str | None):
        self._current_project_path = path

    def set_workspace_limits(self, limits: dict | None):
        self._workspace_limits = limits

    def set_mechanical_workspace_limits(self, limits: dict | None):
        self._mechanical_workspace_limits = limits
        
    def set_global_force_result(self, result: dict | None): # [新增]
        self._global_force_result = result
        
    def set_angle_range_result(self, result: dict | None): # [新增]
        self._angle_range_result = result
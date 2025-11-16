# D:\Python_Programs\Stewart_Platform\src\gui\controls\database_management_widget.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, 
                             QLabel, QPushButton, QComboBox, QDoubleSpinBox, QLineEdit,
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QWidget)
from PyQt6.QtCore import Qt
import pandas as pd
import sqlite3
from src.core.database_manager import DatabaseManager
from src.utils.custom_widgets import CustomDoubleSpinBox, CustomComboBox  # 導入自訂類別

class DatabaseManagementWidget(QDialog):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.is_dirty = False
        self.import_mode = False
        self.setMinimumSize(800, 600)
        self.setWindowTitle("資料庫管理")
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.table_combo = CustomComboBox()
        self.table_combo.addItems(["馬達", "螺桿", "皮帶輪"])
        main_layout.addWidget(self.table_combo)
        
        self.input_group = QGroupBox("新增/編輯零件")
        input_layout = QFormLayout(self.input_group)
        
        self.model_input = QLineEdit()
        self.brand_input = QLineEdit()
        input_layout.addRow("型號:", self.model_input)
        input_layout.addRow("廠牌:", self.brand_input)
        
        self.fields_container = QWidget()
        self.fields_layout = QFormLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.addRow(self.fields_container)
        
        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("工作表:"))
        self.sheet_combo = CustomComboBox()
        self.sheet_combo.setEnabled(False)
        sheet_layout.addWidget(self.sheet_combo)
        main_layout.addLayout(sheet_layout)
        
        self.add_button = QPushButton("新增")
        self.update_button = QPushButton("更新")
        self.delete_button = QPushButton("刪除")
        self.import_button = QPushButton("匯入Excel")
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.import_button)
        main_layout.addWidget(self.input_group)
        main_layout.addLayout(button_layout)
        
        self.table_widget = QTableWidget()
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.horizontalHeader().setMinimumHeight(50)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        main_layout.addWidget(self.table_widget)
        
        self.ok_button = QPushButton("確定")
        self.cancel_button = QPushButton("取消")
        dialog_button_layout = QHBoxLayout()
        dialog_button_layout.addWidget(self.ok_button)
        dialog_button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(dialog_button_layout)
        
        self._update_fields("馬達")

    def _connect_signals(self):
        self.table_combo.currentTextChanged.connect(self._update_fields)
        self.add_button.clicked.connect(self._add_item)
        self.update_button.clicked.connect(self._update_item)
        self.delete_button.clicked.connect(self._delete_item)
        self.import_button.clicked.connect(self._import_excel)
        self.table_widget.itemSelectionChanged.connect(self._on_item_selected)
        self.model_input.textChanged.connect(self._set_dirty)
        self.brand_input.textChanged.connect(self._set_dirty)
        self.ok_button.clicked.connect(self._on_ok)
        self.cancel_button.clicked.connect(self._on_cancel)

    def _set_dirty(self):
        self.is_dirty = True

    def _on_ok(self):
        if self.import_mode:
            self.accept()
        else:
            if not self.model_input.text().strip():
                QMessageBox.warning(self, "警告", "型號為必要欄位，請填寫完整。")
                return
            if self.table_combo.currentText() == "馬達" and not any(
                isinstance(widget, CustomDoubleSpinBox) and widget.value() > 0 for widget in self.fields.values()
                if widget in [self.fields.get('rated_torque_nm'), self.fields.get('max_torque_nm')]
            ):
                QMessageBox.warning(self, "警告", "馬達的額定扭矩或最大扭矩必須大於 0。")
                return
            if self.table_combo.currentText() == "螺桿" and not self.fields.get('ca_n', CustomDoubleSpinBox()).value() > 0:
                QMessageBox.warning(self, "警告", "螺桿的動態負荷 (ca_n) 必須大於 0。")
                return
            self.accept()

    def _on_cancel(self):
        if self.is_dirty:
            reply = QMessageBox.question(
                self, "確認", "資料已變更，是否確定取消？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.reject()
        else:
            self.reject()

    def _import_excel(self):
        """
        從 Excel 檔案匯入資料，允許使用者選擇工作表。
        """
        column_mappings = {
            "motors": {
                "伺服馬達型號": "model",
                "廠牌": "brand",
                "額定出力容量_kW": "rated_power_kw",
                "額定回轉數_rpm": "rated_speed_rpm",
                "額定轉矩_Nm": "rated_torque_nm",
                "最大轉矩_Nm": "max_torque_nm",
                "額定電流_A": "rated_current_a",
                "最大電流_A": "max_current_a",
                "伺服驅動器型號": "servo_driver_model",
                "瞬間容許轉速_rpm": "max_allowed_speed_rpm",
                "重量_kg": "weight_kg",
                "軸心直徑_mm": "shaft_diameter_mm",
                "軸心長度_mm": "shaft_length_mm"
            },
            "screws": {
                "螺桿型號": "model",
                "廠牌": "brand",
                "螺桿軸外徑_mm": "dia_mm",
                "螺桿螺距_mm": "lead_mm",
                "動額定負荷_Ca_kgf": "ca_n",
                "靜額定負荷_Coa_kgf": "coa_n",
                "珠徑_Da_mm": "pearl_dia_mm",
                "剛性_K_kg/μm": "rigidity_kg_um",
                "螺帽長度_L": "nut_length_mm"
            },
            "pulleys": {
                "皮帶輪型號": "model",
                "廠牌": "brand",
                "齒數": "teeth",
                "齒輪直徑_PD_mm": "diameter_mm",
                "皮帶寬度_mm": "belt_width_mm"
            }
        }
        
        table_name_display = self.table_combo.currentText()
        table_map = {"馬達": "motors", "螺桿": "screws", "皮帶輪": "pulleys"}
        table_name = table_map.get(table_name_display, "motors")
        
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇Excel檔案", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            if not sheet_names:
                QMessageBox.critical(self, "錯誤", "無法讀取工作表，請檢查檔案格式。")
                return
            
            self.sheet_combo.clear()
            self.sheet_combo.addItems(sheet_names)
            self.sheet_combo.setEnabled(True)
            
            if len(sheet_names) == 1:
                self.sheet_combo.setCurrentIndex(0)
            
            sheet_name = self.sheet_combo.currentText()
            if not sheet_name:
                QMessageBox.warning(self, "警告", "請選擇一個工作表。")
                return
            
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"Excel 檔案: {file_path}")
            print(f"選擇的工作表: {sheet_name}")
            print(f"Excel 欄位名稱: {df.columns.tolist()}")
            print(f"程式 mapping 鍵: {list(column_mappings[table_name].keys())}")
            
            success, msg, success_count, error_count, duplicates = self.db_manager.import_from_excel(
                file_path, table_name, column_mappings[table_name], sheet_name)
            
            if not success:
                QMessageBox.critical(self, "錯誤", msg)
                return

            for duplicate in duplicates:
                model = duplicate['model']
                differences = duplicate['differences']
                new_data = duplicate['new_data']
                existing_data = duplicate['existing_data']

                diff_text = f"檢測到重複型號: {model}\n\n差異欄位:\n"
                for field, (old_val, new_val) in differences.items():
                    diff_text += f"{field}: {old_val} -> {new_val}\n"

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("重複型號檢測")
                msg_box.setText(f"{diff_text}\n請選擇處理方式：")
                skip_btn = msg_box.addButton("跳過", QMessageBox.ButtonRole.RejectRole)
                overwrite_btn = msg_box.addButton("覆蓋", QMessageBox.ButtonRole.AcceptRole)
                add_btn = msg_box.addButton("新增", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()

                if msg_box.clickedButton() == overwrite_btn:
                    columns = ', '.join(f"{k} = ?" for k in new_data.keys())
                    values = list(new_data.values()) + [model]
                    self.db_manager.conn.cursor().execute(
                        f"UPDATE {table_name} SET {columns} WHERE model = ?", values)
                    self.db_manager.conn.commit()
                elif msg_box.clickedButton() == add_btn:
                    try:
                        columns = ', '.join(new_data.keys())
                        placeholders = ', '.join('?' * len(new_data))
                        self.db_manager.conn.cursor().execute(
                            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(new_data.values()))
                        self.db_manager.conn.commit()
                    except sqlite3.IntegrityError:
                        QMessageBox.warning(self, "無法新增", "資料表要求 model 欄位唯一，請先修改資料庫結構或選擇其他處理方式。")
                self.is_dirty = True

            QMessageBox.information(self, "匯入結果", f"{msg}\n成功: {success_count} 筆\n失敗: {error_count} 筆")
            self._refresh_table(table_name)
            self.import_mode = True
            self.model_input.clear()
            self.brand_input.clear()
            self.is_dirty = False

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法載入檔案: {str(e)}")
            self.sheet_combo.setEnabled(False)
            return

    def _update_fields(self, table_name_display: str):
        table_map = {"馬達": "motors", "螺桿": "screws", "皮帶輪": "pulleys"}
        table_name = table_map.get(table_name_display, "motors")
        
        self.fields_layout.invalidate()
        for i in reversed(range(self.fields_layout.count())):
            widget = self.fields_layout.itemAt(i).widget()
            if widget: widget.deleteLater()
        
        self.fields = {}
        
        if table_name == "motors":
            self._add_field("額定功率 (kW):", "rated_power_kw")
            self._add_field("額定轉速 (rpm):", "rated_speed_rpm")
            self._add_field("額定扭矩 (Nm):", "rated_torque_nm")
            self._add_field("最大扭矩 (Nm):", "max_torque_nm")
            self._add_field("額定電流 (A):", "rated_current_a")
            self._add_field("最大電流 (A):", "max_current_a")
            self._add_field("重量 (kg):", "weight_kg")
            self._add_field("伺服驅動器型號:", "servo_driver_model", is_text=True)
            self._add_field("瞬間容許轉速 (rpm):", "max_allowed_speed_rpm")
            self._add_field("軸心直徑 (mm):", "shaft_diameter_mm")
            self._add_field("軸心長度 (mm):", "shaft_length_mm")
        elif table_name == "screws":
            self._add_field("螺桿直徑 (mm):", "dia_mm")
            self._add_field("導程 (mm):", "lead_mm")
            self._add_field("動態負荷 (N):", "ca_n")
            self._add_field("靜態負荷 (N):", "coa_n")
            self._add_field("珠徑 (mm):", "pearl_dia_mm")
            self._add_field("剛性 (kg/μm):", "rigidity_kg_um")
            self._add_field("螺帽長度 (mm):", "nut_length_mm")
        elif table_name == "pulleys":
            self._add_field("齒數:", "teeth")
            self._add_field("直徑 (mm):", "diameter_mm")
            self._add_field("皮帶寬度 (mm):", "belt_width_mm")
        
        self._refresh_table(table_name)

    def _add_field(self, label_text: str, field_name: str, is_text: bool = False):
        if is_text:
            widget = QLineEdit()
        else:
            widget = CustomDoubleSpinBox()  # 替換為自訂類別
            widget.setDecimals(3)
            widget.setRange(0, 1000000)
        widget.valueChanged.connect(self._set_dirty) if not is_text else widget.textChanged.connect(self._set_dirty)
        self.fields[field_name] = widget
        self.fields_layout.addRow(label_text, widget)

    def _refresh_table(self, table_name: str):
        get_func_map = {
            "motors": self.db_manager.get_all_motors,
            "screws": self.db_manager.get_all_screws,
            "pulleys": self.db_manager.get_all_pulleys
        }
        get_func = get_func_map.get(table_name)
        items, msg = get_func()
        
        if items is None:
            QMessageBox.critical(self, "錯誤", msg)
            return
        
        self.table_widget.clear()
        self.table_widget.setRowCount(len(items))
        
        if table_name == "motors":
            headers = ["ID", "型號", "廠牌", "額定功率 (kW)", "額定轉速 (rpm)", "額定扭矩 (Nm)", 
                       "最大扭矩 (Nm)", "額定電流 (A)", "最大電流 (A)", "重量 (kg)", 
                       "伺服驅動器型號", "瞬間容許轉速 (rpm)", "軸心直徑 (mm)", "軸心長度 (mm)"]
        elif table_name == "screws":
            headers = ["ID", "型號", "廠牌", "螺桿直徑 (mm)", "導程 (mm)", "動態負荷 (N)", 
                       "靜態負荷 (N)", "珠徑 (mm)", "剛性 (kg/μm)", "螺帽長度 (mm)"]
        elif table_name == "pulleys":
            headers = ["ID", "型號", "廠牌", "齒數", "直徑 (mm)", "皮帶寬度 (mm)"]
        
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_widget.horizontalHeader().setMinimumHeight(50)
        
        header_mapping = {
            "ID": "id",
            "型號": "model",
            "廠牌": "brand",
            "額定功率 (kW)": "rated_power_kw",
            "額定轉速 (rpm)": "rated_speed_rpm",
            "額定扭矩 (Nm)": "rated_torque_nm",
            "最大扭矩 (Nm)": "max_torque_nm",
            "額定電流 (A)": "rated_current_a",
            "最大電流 (A)": "max_current_a",
            "重量 (kg)": "weight_kg",
            "伺服驅動器型號": "servo_driver_model",
            "瞬間容許轉速 (rpm)": "max_allowed_speed_rpm",
            "軸心直徑 (mm)": "shaft_diameter_mm",
            "軸心長度 (mm)": "shaft_length_mm",
            "螺桿直徑 (mm)": "dia_mm",
            "導程 (mm)": "lead_mm",
            "動態負荷 (N)": "ca_n",
            "靜態負荷 (N)": "coa_n",
            "珠徑 (mm)": "pearl_dia_mm",
            "剛性 (kg/μm)": "rigidity_kg_um",
            "螺帽長度 (mm)": "nut_length_mm",
            "齒數": "teeth",
            "直徑 (mm)": "diameter_mm",
            "皮帶寬度 (mm)": "belt_width_mm"
        }

        for row, item in enumerate(items):
            for col, header in enumerate(headers):
                key = header_mapping.get(header)
                value = item.get(key, 'N/A')
                table_item = QTableWidgetItem(str(value))
                table_item.setData(Qt.ItemDataRole.UserRole, item['id'])
                self.table_widget.setItem(row, col, table_item)

    def _add_item(self):
        table_name = self._get_current_table_name()
        item_data = self._collect_item_data()
        if not item_data['model']:
            QMessageBox.warning(self, "警告", "型號為必要欄位，請填寫完整。")
            return
        if table_name == "motors" and not (item_data.get('rated_torque_nm', 0) > 0 or item_data.get('max_torque_nm', 0) > 0):
            QMessageBox.warning(self, "警告", "馬達的額定扭矩或最大扭矩必須大於 0。")
            return
        if table_name == "screws" and item_data.get('ca_n', 0) <= 0:
            QMessageBox.warning(self, "警告", "螺桿的動態負荷 (ca_n) 必須大於 0。")
            return
        success, msg = self.db_manager.add_item(table_name, item_data)
        if success:
            QMessageBox.information(self, "成功", "零件已新增。")
            self.is_dirty = True
            self._refresh_table(table_name)
        else:
            QMessageBox.critical(self, "錯誤", msg)

    def _update_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "請先選擇一筆資料。")
            return
        
        item_id = self.table_widget.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        table_name = self._get_current_table_name()
        item_data = self._collect_item_data()
        if not item_data['model']:
            QMessageBox.warning(self, "警告", "型號為必要欄位，請填寫完整。")
            return
        if table_name == "motors" and not (item_data.get('rated_torque_nm', 0) > 0 or item_data.get('max_torque_nm', 0) > 0):
            QMessageBox.warning(self, "警告", "馬達的額定扭矩或最大扭矩必須大於 0。")
            return
        if table_name == "screws" and item_data.get('ca_n', 0) <= 0:
            QMessageBox.warning(self, "警告", "螺桿的動態負荷 (ca_n) 必須大於 0。")
            return
        success, msg = self.db_manager.update_item(table_name, item_id, item_data)
        if success:
            QMessageBox.information(self, "成功", "零件已更新。")
            self.is_dirty = True
            self._refresh_table(table_name)
        else:
            QMessageBox.critical(self, "錯誤", msg)

    def _delete_item(self):
        selected_row = self.table_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "請先選擇一筆資料。")
            return
        
        item_id = self.table_widget.item(selected_row, 0).data(Qt.ItemDataRole.UserRole)
        table_name = self._get_current_table_name()
        success, msg = self.db_manager.delete_item(table_name, item_id)
        if success:
            QMessageBox.information(self, "成功", "零件已刪除。")
            self.is_dirty = True
            self._refresh_table(table_name)
        else:
            QMessageBox.critical(self, "錯誤", msg)

    def _on_item_selected(self):
        selected_row = self.table_widget.currentRow()
        if selected_row < 0: return
        
        self.model_input.setText(self.table_widget.item(selected_row, 1).text())
        self.brand_input.setText(self.table_widget.item(selected_row, 2).text())
        
        for col, field_name in enumerate(self.fields.keys(), start=3):
            value_str = self.table_widget.item(selected_row, col).text()
            if field_name in ["servo_driver_model"]:
                self.fields[field_name].setText(value_str)
            else:
                try:
                    value = float(value_str)
                except ValueError:
                    value = 0.0
                self.fields[field_name].setValue(value)

    def _collect_item_data(self):
        data = {
            'model': self.model_input.text().strip(),
            'brand': self.brand_input.text().strip()
        }
        for field_name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                data[field_name] = widget.text().strip()
            else:
                data[field_name] = widget.value()
        return data

    def _get_current_table_name(self):
        table_map = {"馬達": "motors", "螺桿": "screws", "皮帶輪": "pulleys"}
        return table_map.get(self.table_combo.currentText(), "motors")
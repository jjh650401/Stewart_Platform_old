# D:\Python_Programs\Stewart_Platform\src\core\report_generator.py

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import numpy as np
import re
from src.core import config

class ReportGenerator:
    """
    負責從專案數據生成 PDF 報告的類別。
    """
    def __init__(self, project_data: dict, filepath: str):
        self.project_data = project_data
        self.filepath = filepath
        self.story = []
        self._register_fonts()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _register_fonts(self):
        """註冊支援繁體中文和英數的字體"""
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', config.FONT_PATH_CHINESE))
            pdfmetrics.registerFont(TTFont('LatinFont', config.FONT_PATH_LATIN))
            self.font_name_ch = 'ChineseFont'
            self.font_name_latin = 'LatinFont'
            print("中、英文字體註冊成功。")
        except Exception as e:
            print(f"警告：註冊字體失敗，將退回使用預設字體。錯誤: {e}")
            self.font_name_ch = "Helvetica"
            self.font_name_latin = "Helvetica"
            
    def _setup_styles(self):
        """自訂報告中使用的樣式"""
        self.styles.add(ParagraphStyle(name='Title_ch', parent=self.styles['h1'], 
                                        fontName=self.font_name_ch, fontSize=18, alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='h2_ch', parent=self.styles['h2'], 
                                        fontName=self.font_name_ch, fontSize=14))
        self.styles.add(ParagraphStyle(name='Normal_ch', parent=self.styles['Normal'], 
                                        fontName=self.font_name_ch, fontSize=10, alignment=TA_LEFT, leading=14))

    def _mixed_font_paragraph(self, text, style):
        """建立一個支援中英混合字體的 Paragraph 物件"""
        # 使用正則表達式分割中文字和非中文字元
        parts = re.split(r'([a-zA-Z0-9\s.,;:°/()_-]+)', text)
        formatted_text = ""
        for part in parts:
            if not part:
                continue
            # 判斷是否為英數部分
            if re.match(r'^[a-zA-Z0-9\s.,;:°/()_-]+$', part):
                formatted_text += f'<font name="{self.font_name_latin}">{part}</font>'
            else:
                formatted_text += f'<font name="{self.font_name_ch}">{part}</font>'
        return Paragraph(formatted_text, style)

    def generate_report(self):
        """生成 PDF 報告的主方法"""
        try:
            doc = SimpleDocTemplate(self.filepath,
                                    pagesize=(210*mm, 297*mm),
                                    leftMargin=20*mm,
                                    rightMargin=20*mm,
                                    topMargin=20*mm,
                                    bottomMargin=20*mm)

            self._create_title_section()
            self._create_geometry_section()
            self._create_dynamics_section()
            self._create_analysis_section()
            
            doc.build(self.story)
            return True, "報告生成成功。"
        except Exception as e:
            print(f"PDF 生成失敗: {e}")
            return False, f"PDF 生成失敗: {e}"

    def _create_title_section(self):
        """建立文件標題和基本資訊"""
        self.story.append(self._mixed_font_paragraph("史都華平台設計與模擬分析報告", self.styles['Title_ch']))
        self.story.append(Spacer(1, 8*mm))
        
        project_path = self.project_data.get('project_path', '未命名專案')
        project_name = project_path.split('/')[-1].split('\\')[-1] if project_path != "N/A" else "未命名專案"
        
        info_data = [
            [self._mixed_font_paragraph('專案名稱:', self.styles['Normal_ch']), self._mixed_font_paragraph(project_name, self.styles['Normal_ch'])],
            [self._mixed_font_paragraph('報告生成日期:', self.styles['Normal_ch']), self._mixed_font_paragraph(datetime.date.today().strftime('%Y-%m-%d'), self.styles['Normal_ch'])],
            [self._mixed_font_paragraph('平台類型:', self.styles['Normal_ch']), self._mixed_font_paragraph(self.project_data.get('platform_type', 'N/A'), self.styles['Normal_ch'])]
        ]
        info_table = Table(info_data, colWidths=[40*mm, 110*mm])
        info_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        self.story.append(info_table)
        self.story.append(Spacer(1, 10*mm))

    def _create_geometry_section(self):
        """建立幾何與電動缸參數部分"""
        self.story.append(self._mixed_font_paragraph("1. 幾何與電動缸參數", self.styles['h2_ch']))
        self.story.append(Spacer(1, 4*mm))
        
        p = self.project_data['core_params']
        is_6dof = self.project_data.get('platform_type') == '6-DOF'
        
        data = []
        if is_6dof:
            data.extend([
                ['固定平台-較大弦長 (Df)', f"{p.get('Df', 0)*1000:.2f} mm"],
                ['固定平台-較小弦長 (df)', f"{p.get('df', 0)*1000:.2f} mm"],
                ['活動平台-較大弦長 (Dm)', f"{p.get('Dm', 0)*1000:.2f} mm"],
                ['活動平台-較小弦長 (dm)', f"{p.get('dm', 0)*1000:.2f} mm"],
            ])
        else:
            data.extend([
                ['固定平台-底邊長度 (D1)', f"{p.get('D1', 0)*1000:.2f} mm"],
                ['固定平台-三角形高 (D2)', f"{p.get('D2', 0)*1000:.2f} mm"],
                ['活動平台-底邊長度 (d1)', f"{p.get('d1', 0)*1000:.2f} mm"],
                ['活動平台-三角形高 (d2)', f"{p.get('d2', 0)*1000:.2f} mm"],
            ])

        data.extend([
            ['固定平台半徑 (Ra)', f"{p.get('Ra', 0)*1000:.2f} mm"],
            ['活動平台半徑 (Rb)', f"{p.get('Rb', 0)*1000:.2f} mm"],
            ['電動缸-最小長度 (L)', f"{p.get('L', 0)*1000:.2f} mm"],
            ['電動缸-可用行程 (s)', f"{p.get('s', 0)*1000:.2f} mm"],
            ['電動缸-安全裕量 (s_buffer)', f"{p.get('s_buffer', 0)*1000:.2f} mm"],
            ['零位高度 (H)', f"{p.get('H', 0)*1000:.2f} mm"],
        ])
        
        if is_6dof:
             data.append(['幾何相位角 (Δθ)', f"{self.project_data.get('phase_angle', 0):.3f} °"])

        # 將表格內容轉換為 Paragraph 物件以應用混合字體
        processed_data = [[self._mixed_font_paragraph(cell, self.styles['Normal_ch']) for cell in row] for row in data]
        table = Table(processed_data, colWidths=[80*mm, 70*mm])
        table.setStyle(self._get_default_table_style())
        self.story.append(table)
        self.story.append(Spacer(1, 10*mm))

    def _create_dynamics_section(self):
        """建立動力學參數部分"""
        self.story.append(self._mixed_font_paragraph("2. 動力學參數", self.styles['h2_ch']))
        self.story.append(Spacer(1, 4*mm))

        p = self.project_data['core_params']
        
        data = [
            ['上平台質量', f"{p.get('platform_mass', 0):.2f} kg"],
            ['負載質量', f"{p.get('load_mass', 0):.2f} kg"],
            ['負載質心 X 偏移', f"{p.get('load_com_x', 0)*1000:.2f} mm"],
            ['負載質心 Y 偏移', f"{p.get('load_com_y', 0)*1000:.2f} mm"],
            ['負載質心 Z 偏移', f"{p.get('load_com_z', 0)*1000:.2f} mm"],
            ['Z軸平移加速度', f"{p.get('lin_accel', [0,0,0])[2]:.3f} m/s²"],
            ['X軸角加速度', f"{p.get('ang_accel', [0,0,0])[0]:.3f} rad/s²"],
            ['Y軸角加速度', f"{p.get('ang_accel', [0,0,0])[1]:.3f} rad/s²"],
        ]
        
        processed_data = [[self._mixed_font_paragraph(cell, self.styles['Normal_ch']) for cell in row] for row in data]
        table = Table(processed_data, colWidths=[80*mm, 70*mm])
        table.setStyle(self._get_default_table_style())
        self.story.append(table)
        self.story.append(Spacer(1, 10*mm))

    def _create_analysis_section(self):
        """建立所有分析結果部分"""
        self.story.append(self._mixed_font_paragraph("3. 分析結果", self.styles['h2_ch']))
        self.story.append(Spacer(1, 4*mm))
        
        ws = self.project_data.get('workspace_limits')
        if ws:
            self.story.append(self._mixed_font_paragraph("3.1 可用工作空間範圍", self.styles['Normal_ch']))
            self.story.append(Spacer(1, 2*mm))
            data = [
                ['自由度', '最小值', '最大值'],
                ['Surge (X)', f"{ws.get('x_min', 0)*1000:.3f} mm", f"{ws.get('x_max', 0)*1000:.3f} mm"],
                ['Sway (Y)', f"{ws.get('y_min', 0)*1000:.3f} mm", f"{ws.get('y_max', 0)*1000:.3f} mm"],
                ['Heave (Z)', f"{ws.get('z_min', 0)*1000:.3f} mm", f"{ws.get('z_max', 0)*1000:.3f} mm"],
                ['Pitch (θx)', f"{np.rad2deg(ws.get('pitch_min', 0)):.3f} °", f"{np.rad2deg(ws.get('pitch_max', 0)):.3f} °"],
                ['Roll (θy)', f"{np.rad2deg(ws.get('roll_min', 0)):.3f} °", f"{np.rad2deg(ws.get('roll_max', 0)):.3f} °"],
                ['Yaw (θz)', f"{np.rad2deg(ws.get('yaw_min', 0)):.3f} °", f"{np.rad2deg(ws.get('yaw_max', 0)):.3f} °"],
            ]
            if self.project_data.get('platform_type') == '3-DOF':
                data = [data[0]] + data[3:6]
            
            processed_data = [[self._mixed_font_paragraph(cell, self.styles['Normal_ch']) for cell in row] for row in data]
            table = Table(processed_data, colWidths=[40*mm, 55*mm, 55*mm])
            table.setStyle(self._get_default_table_style(header=True))
            self.story.append(table)
            self.story.append(Spacer(1, 6*mm))

        gf = self.project_data.get('global_force_result')
        if gf:
            self.story.append(self._mixed_font_paragraph("3.2 全域最大出力分析", self.styles['Normal_ch']))
            self.story.append(Spacer(1, 2*mm))
            max_force = max(abs(f) for f in gf.get('forces', [0]))
            pose_str = ', '.join([f"{k.upper()}: {v:.1f}" for k,v in gf.get('pose_ui', {}).items()])
            data = [
                ['最大推/拉力', f"{max_force:.2f} N"],
                ['發生姿態', pose_str]
            ]
            processed_data = [[self._mixed_font_paragraph(cell, self.styles['Normal_ch']) for cell in row] for row in data]
            table = Table(processed_data, colWidths=[40*mm, 110*mm])
            table.setStyle(self._get_default_table_style())
            self.story.append(table)
            self.story.append(Spacer(1, 6*mm))

        ar = self.project_data.get('angle_range_result')
        if ar and ar.get('success'):
            self.story.append(self._mixed_font_paragraph("3.3 節點擺角範圍分析結果", self.styles['Normal_ch']))
            self.story.append(Spacer(1, 2*mm))
            
            max_angles = ar.get('max_angles', {})
            base = sorted([(k, v) for k, v in max_angles.items() if k.startswith('A')])
            mobile = sorted([(k, v) for k, v in max_angles.items() if k.startswith('B')])
            
            data = [['固定平台節點', '最大擺角', '活動平台節點', '最大擺角']]
            num_rows = max(len(base), len(mobile))
            for i in range(num_rows):
                row = []
                if i < len(base): row.extend([base[i][0], f"{base[i][1]:.2f}°"])
                else: row.extend(['', ''])
                if i < len(mobile): row.extend([mobile[i][0], f"{mobile[i][1]:.2f}°"])
                else: row.extend(['', ''])
                data.append(row)
            
            processed_data = [[self._mixed_font_paragraph(cell, self.styles['Normal_ch']) for cell in row] for row in data]
            table = Table(processed_data, colWidths=[35*mm, 40*mm, 35*mm, 40*mm])
            table.setStyle(self._get_default_table_style(header=True))
            self.story.append(table)

    def _get_default_table_style(self, header=False):
        style = [
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        if header:
            style.append(('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey))
        return TableStyle(style)
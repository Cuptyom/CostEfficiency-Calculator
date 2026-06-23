import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont, QGuiApplication

# =================== КАСТОМНЫЕ СПИНБОКСЫ БЕЗ КОЛЁСИКА ===================
class NoWheelSpinBox(QSpinBox):
    """Спинбокс, который игнорирует прокрутку колёсиком мыши."""
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """Double-спинбокс, который игнорирует прокрутку колёсиком мыши."""
    def wheelEvent(self, event):
        event.ignore()
# ======================================================================

class EconomicCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчёт экономической эффективности ПО")
        self.setMinimumSize(950, 750)

        self.apply_styles()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.input_tab = QWidget()
        self.tabs.addTab(self.input_tab, "📝 Ввод данных")
        self.setup_input_tab()

        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab, "📊 Результаты")
        self.setup_results_tab()

        # Панель кнопок (внизу)
        button_panel = QHBoxLayout()
        button_panel.setSpacing(15)

        style = self.style()

        self.calc_btn = QPushButton(" Рассчитать")
        self.calc_btn.setIcon(style.standardIcon(QStyle.SP_DialogApplyButton))
        self.calc_btn.setMinimumHeight(40)
        self.calc_btn.clicked.connect(self.calculate)
        button_panel.addWidget(self.calc_btn)

        self.example_btn = QPushButton(" Загрузить пример")
        self.example_btn.setIcon(style.standardIcon(QStyle.SP_DialogOpenButton))
        self.example_btn.setMinimumHeight(40)
        self.example_btn.clicked.connect(self.load_example)
        button_panel.addWidget(self.example_btn)

        self.clear_btn = QPushButton(" Очистить поля")
        self.clear_btn.setIcon(style.standardIcon(QStyle.SP_DialogResetButton))
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_fields)
        button_panel.addWidget(self.clear_btn)

        button_panel.addStretch()
        main_layout.addLayout(button_panel)

        # Для копирования результатов
        self.results_text = ""

    def apply_styles(self):
        style = """
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 #e8edf5, stop:1 #d5dce6);
        }
        QGroupBox {
            background-color: rgba(255,255,255,0.85);
            border: 1px solid #c8d0db;
            border-radius: 12px;
            margin-top: 1.5ex;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px 0 8px;
            color: #1f2a44;
        }
        QLabel {
            color: #1f2a44;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #5b7cfa, stop:1 #3b5de7);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            font-weight: bold;
            font-size: 11pt;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #7a95ff, stop:1 #4b6df5);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2b4fc7, stop:1 #1e3a9e);
        }
        NoWheelDoubleSpinBox, NoWheelSpinBox {
            background-color: white;
            border: 1px solid #ccd4e0;
            border-radius: 6px;
            padding: 5px 8px;
            min-height: 24px;
        }
        NoWheelDoubleSpinBox:focus, NoWheelSpinBox:focus {
            border: 2px solid #5b7cfa;
            background-color: #f4f7ff;
        }
        QTabWidget::pane {
            border: 1px solid #c8d0db;
            border-radius: 12px;
            background: rgba(255,255,255,0.7);
        }
        QTabBar::tab {
            background: #e2e8f0;
            border: 1px solid #c8d0db;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 10px 22px;
            margin-right: 3px;
            font-weight: 500;
        }
        QTabBar::tab:selected {
            background: white;
            border-bottom: 3px solid #5b7cfa;
        }
        QTabBar::tab:hover:!selected {
            background: #d0d8e6;
        }
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            background: #dde3ed;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #8fa4c9;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #6e87b5;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QMessageBox {
            background-color: white;
        }
        /* Стиль для полей с формулами (для выделения) */
        QTextEdit {
            background-color: #f8f9fc;
            border: 1px solid #d0d8e6;
            border-radius: 6px;
            padding: 6px 8px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            color: #1f2a44;
        }
        QTextEdit:focus {
            border: 2px solid #5b7cfa;
            background-color: #f4f7ff;
        }
        /* Стиль для поля результата */
        QTextEdit[cssClass="result"] {
            background-color: #eef3ff;
            border: 2px solid #5b7cfa;
            font-weight: bold;
            color: #1f2a44;
        }
        """
        self.setStyleSheet(style)

    def setup_input_tab(self):
        layout = QVBoxLayout(self.input_tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(15)

        # Группа 1: Трудозатраты
        group_tu = QGroupBox("Трудозатраты (чел-час)")
        group_tu_layout = QFormLayout(group_tu)
        group_tu_layout.setSpacing(8)

        self.tu = NoWheelDoubleSpinBox()
        self.tu.setRange(0, 10000)
        self.tu.setValue(194.4)
        self.tu.setToolTip("Затраты времени на исследование алгоритма")
        group_tu_layout.addRow("Исследование алгоритма (tu):", self.tu)

        self.ta = NoWheelDoubleSpinBox()
        self.ta.setRange(0, 10000)
        self.ta.setValue(185.14)
        self.ta.setToolTip("Затраты времени на разработку блок-схемы")
        group_tu_layout.addRow("Разработка блок-схемы (ta):", self.ta)

        self.tn = NoWheelDoubleSpinBox()
        self.tn.setRange(0, 10000)
        self.tn.setValue(204.69)
        self.tn.setToolTip("Затраты времени на программирование")
        group_tu_layout.addRow("Программирование (tn):", self.tn)

        self.toml = NoWheelDoubleSpinBox()
        self.toml.setRange(0, 10000)
        self.toml.setValue(288.0)
        self.toml.setToolTip("Затраты времени на отладку программы")
        group_tu_layout.addRow("Отладка программы (toml):", self.toml)

        self.td = NoWheelDoubleSpinBox()
        self.td.setRange(0, 10000)
        self.td.setValue(151.2)
        self.td.setToolTip("Затраты времени на подготовку документации")
        group_tu_layout.addRow("Подготовка документации (td):", self.td)

        form_layout.addWidget(group_tu)

        # Группа 2: Финансовые параметры
        group_fin = QGroupBox("Финансовые параметры")
        group_fin_layout = QFormLayout(group_fin)
        group_fin_layout.setSpacing(8)

        self.hourly_rate = NoWheelDoubleSpinBox()
        self.hourly_rate.setRange(0, 100000)
        self.hourly_rate.setValue(238.1)
        self.hourly_rate.setToolTip("Среднечасовая оплата труда разработчика")
        group_fin_layout.addRow("Среднечасовая оплата (руб/час):", self.hourly_rate)

        self.insurance = NoWheelDoubleSpinBox()
        self.insurance.setRange(0, 10)
        self.insurance.setValue(1.3)
        self.insurance.setSingleStep(0.05)
        self.insurance.setToolTip("Коэффициент, учитывающий страховые взносы")
        group_fin_layout.addRow("Коэф. страховых взносов:", self.insurance)

        self.machine_hour = NoWheelDoubleSpinBox()
        self.machine_hour.setRange(0, 10000)
        self.machine_hour.setValue(21.05)
        self.machine_hour.setToolTip("Стоимость одного машино-часа работы ПК")
        group_fin_layout.addRow("Стоимость машино-часа (руб):", self.machine_hour)

        self.electricity = NoWheelDoubleSpinBox()
        self.electricity.setRange(0, 100)
        self.electricity.setValue(7.28)
        self.electricity.setToolTip("Стоимость 1 кВт·ч электроэнергии")
        group_fin_layout.addRow("Стоимость электроэнергии (руб/кВт·ч):", self.electricity)

        self.power = NoWheelDoubleSpinBox()
        self.power.setRange(0, 10)
        self.power.setValue(0.5)
        self.power.setSingleStep(0.05)
        self.power.setToolTip("Мощность, потребляемая ПК (кВт)")
        group_fin_layout.addRow("Мощность ПК (кВт):", self.power)

        form_layout.addWidget(group_fin)

        # Группа 3: Базовый вариант
        group_base = QGroupBox("Базовый вариант")
        group_base_layout = QFormLayout(group_base)
        group_base_layout.setSpacing(8)

        self.work_hours = NoWheelDoubleSpinBox()
        self.work_hours.setRange(0, 8760)
        self.work_hours.setValue(2112)
        self.work_hours.setToolTip("Годовой фонд рабочего времени")
        group_base_layout.addRow("Фонд рабочего времени (час/год):", self.work_hours)

        self.labor_intensity = NoWheelDoubleSpinBox()
        self.labor_intensity.setRange(0, 100)
        self.labor_intensity.setValue(39)
        self.labor_intensity.setToolTip("Трудоёмкость решаемой задачи в % от общего времени")
        group_base_layout.addRow("Трудоёмкость задачи (%):", self.labor_intensity)

        self.salary_share = NoWheelDoubleSpinBox()
        self.salary_share.setRange(0, 1)
        self.salary_share.setValue(0.5)
        self.salary_share.setSingleStep(0.05)
        self.salary_share.setToolTip("Доля заработной платы в общей смете затрат")
        group_base_layout.addRow("Доля зарплаты в смете:", self.salary_share)

        form_layout.addWidget(group_base)

        # Группа 4: Амортизация
        group_amort = QGroupBox("Амортизация")
        group_amort_layout = QFormLayout(group_amort)
        group_amort_layout.setSpacing(8)

        self.useful_life = NoWheelSpinBox()
        self.useful_life.setRange(1, 20)
        self.useful_life.setValue(6)
        self.useful_life.setToolTip("Срок полезного использования ПО (лет)")
        group_amort_layout.addRow("Срок полезного использования (лет):", self.useful_life)

        self.depreciation_rate = NoWheelDoubleSpinBox()
        self.depreciation_rate.setRange(0, 100)
        self.depreciation_rate.setValue(16.67)
        self.depreciation_rate.setSingleStep(0.01)
        self.depreciation_rate.setToolTip("Годовая норма амортизации (%)")
        group_amort_layout.addRow("Норма амортизации (%):", self.depreciation_rate)

        self.pc_cost = NoWheelDoubleSpinBox()
        self.pc_cost.setRange(0, 10000000)
        self.pc_cost.setValue(129600)
        self.pc_cost.setToolTip("Стоимость компьютера (руб)")
        group_amort_layout.addRow("Стоимость ПК (руб):", self.pc_cost)

        form_layout.addWidget(group_amort)
        form_layout.addStretch()

    def setup_results_tab(self):
        layout = QVBoxLayout(self.results_tab)
        layout.setContentsMargins(10, 10, 10, 10)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        layout.addWidget(self.results_scroll)

        self.results_container = QWidget()
        self.results_scroll.setWidget(self.results_container)
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(12)

        # Кнопка копирования (будет добавлена позже)
        self.copy_btn = QPushButton("📋 Копировать все результаты")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.clicked.connect(self.copy_results)
        self.copy_btn.setVisible(False)
        layout.addWidget(self.copy_btn)

    def load_example(self):
        self.tu.setValue(194.4)
        self.ta.setValue(185.14)
        self.tn.setValue(204.69)
        self.toml.setValue(288.0)
        self.td.setValue(151.2)
        self.hourly_rate.setValue(238.1)
        self.insurance.setValue(1.3)
        self.machine_hour.setValue(21.05)
        self.electricity.setValue(7.28)
        self.power.setValue(0.5)
        self.work_hours.setValue(2112)
        self.labor_intensity.setValue(39)
        self.salary_share.setValue(0.5)
        self.useful_life.setValue(6)
        self.depreciation_rate.setValue(16.67)
        self.pc_cost.setValue(129600)

    def clear_fields(self):
        for widget in self.findChildren(NoWheelDoubleSpinBox):
            widget.clear()
        for widget in self.findChildren(NoWheelSpinBox):
            widget.clear()

    def copy_results(self):
        if not self.results_text:
            QMessageBox.information(self, "Нет данных", "Сначала выполните расчёт.")
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.results_text)
        QMessageBox.information(self, "Готово", "Результаты скопированы в буфер обмена.")

    def create_copyable_field(self, text, tooltip="", is_result=False):
        """Создаёт поле QTextEdit для выделения и копирования"""
        text_edit = QTextEdit()
        text_edit.setPlainText(text)
        text_edit.setReadOnly(True)
        
        if is_result:
            text_edit.setMaximumHeight(50)
            text_edit.setProperty("cssClass", "result")
            text_edit.setToolTip(tooltip if tooltip else "Выделите результат и скопируйте (Ctrl+C)")
        else:
            text_edit.setMaximumHeight(50)
            text_edit.setToolTip(tooltip if tooltip else "Выделите текст и скопируйте (Ctrl+C)")
        
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fc;
                border: 1px solid #d0d8e6;
                border-radius: 6px;
                padding: 6px 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                color: #1f2a44;
            }
            QTextEdit:focus {
                border: 2px solid #5b7cfa;
                background-color: #f4f7ff;
            }
            QTextEdit[cssClass="result"] {
                background-color: #eef3ff;
                border: 2px solid #5b7cfa;
                font-weight: bold;
                color: #1f2a44;
            }
        """)
        return text_edit

    def calculate(self):
        # Сбор данных
        tu = self.tu.value()
        ta = self.ta.value()
        tn = self.tn.value()
        toml = self.toml.value()
        td = self.td.value()

        hourly = self.hourly_rate.value()
        insurance = self.insurance.value()
        machine_hour = self.machine_hour.value()
        electricity = self.electricity.value()
        power = self.power.value()

        work_hours = self.work_hours.value()
        labor_intensity = self.labor_intensity.value()
        salary_share = self.salary_share.value()

        useful_life = self.useful_life.value()
        dep_rate = self.depreciation_rate.value()
        pc_cost = self.pc_cost.value()

        # Расчёты (по формулам из ПЗ)
        T = tu + ta + tn + toml + td
        Z_ot = T * hourly * insurance
        Z_mv = machine_hour * (tn + toml)
        Z_el = electricity * power * (tn + toml + td)
        Z_pr = 0.05 * (Z_ot + Z_mv + Z_el)
        Z_rp = Z_ot + Z_mv + Z_el + Z_pr
        A = (dep_rate / 100) * Z_rp
        total_expenses = Z_rp + A

        T_r = work_hours * (labor_intensity / 100)
        Z_b = hourly * T_r * (1 / salary_share)
        Z_pp = (work_hours * machine_hour + total_expenses) / useful_life
        E = Z_b - Z_pp
        R_total = pc_cost + total_expenses
        T_ok = R_total / E if E > 0 else float('inf')
        E_eff = E / R_total if R_total > 0 else 0

        # Формируем текст для копирования (весь отчёт)
        lines = []
        lines.append("="*60)
        lines.append("РЕЗУЛЬТАТЫ РАСЧЁТА ЭКОНОМИЧЕСКОЙ ЭФФЕКТИВНОСТИ")
        lines.append("="*60)

        def add_to_copy(name, general, subst, value, unit=""):
            lines.append(f"\n{name}")
            lines.append(f"  {general}")
            lines.append(f"  {subst}")
            lines.append(f"  Результат: {value:,.2f} {unit}".strip())
            lines.append("-"*40)

        add_to_copy("1. Общие трудозатраты",
                    "T = tu + ta + tn + toml + td",
                    f"T = {tu} + {ta} + {tn} + {toml} + {td} = {T:.2f}",
                    T, "чел-час")

        add_to_copy("2. Расходы на оплату труда и страховые взносы",
                    "Зот = T × Сч × кспр",
                    f"Зот = {T:.2f} × {hourly} × {insurance} = {Z_ot:.2f}",
                    Z_ot, "руб")

        add_to_copy("3. Затраты на машинное время",
                    "Змв = Смч × (tn + toml)",
                    f"Змв = {machine_hour} × ({tn} + {toml}) = {Z_mv:.2f}",
                    Z_mv, "руб")

        add_to_copy("4. Затраты на электроэнергию",
                    "Зэл = Цэл × Р × (tn + toml + td)",
                    f"Зэл = {electricity} × {power} × ({tn} + {toml} + {td}) = {Z_el:.2f}",
                    Z_el, "руб")

        add_to_copy("5. Прочие затраты",
                    "Зпр = 5% × (Зот + Змв + Зэл)",
                    f"Зпр = 0.05 × ({Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f}) = {Z_pr:.2f}",
                    Z_pr, "руб")

        add_to_copy("6. Затраты на разработку",
                    "Зрп = Зот + Змв + Зэл + Зпр",
                    f"Зрп = {Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f} + {Z_pr:.2f} = {Z_rp:.2f}",
                    Z_rp, "руб")

        add_to_copy("7. Амортизация",
                    "Ад = (На × Зрп) / 100",
                    f"Ад = ({dep_rate} × {Z_rp:.2f}) / 100 = {A:.2f}",
                    A, "руб/год")

        add_to_copy("8. Трудоёмкость задачи",
                    "Тр = Тп.к × Нтр / 100",
                    f"Тр = {work_hours} × {labor_intensity} / 100 = {T_r:.2f}",
                    T_r, "час/год")

        add_to_copy("9. Затраты по базовому варианту",
                    "Зб = Сч × Тр × (1 / Дз.п)",
                    f"Зб = {hourly} × {T_r:.2f} × (1 / {salary_share}) = {Z_b:.2f}",
                    Z_b, "руб/год")

        add_to_copy("10. Затраты при использовании ПО",
                    "Зп.п = (Тг × См + Зобщ) / Тс, где Зобщ = Зрп + Ад",
                    f"Зп.п = ({work_hours} × {machine_hour} + {total_expenses:.2f}) / {useful_life} = {Z_pp:.2f}",
                    Z_pp, "руб/год")

        add_to_copy("11. Экономическая эффективность",
                    "Э = Зб - Зп.п",
                    f"Э = {Z_b:.2f} - {Z_pp:.2f} = {E:.2f}",
                    E, "руб/год")

        if T_ok != float('inf'):
            add_to_copy("12. Срок окупаемости",
                        "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                        f"Ток = {R_total:.2f} / {E:.2f} = {T_ok:.2f}",
                        T_ok, "лет")
        else:
            add_to_copy("12. Срок окупаемости",
                        "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                        f"Ток = {R_total:.2f} / {E:.2f} (Э ≤ 0)",
                        0, "лет")

        add_to_copy("13. Экономический эффект",
                    "Е = Э / Робщ",
                    f"Е = {E:.2f} / {R_total:.2f} = {E_eff:.4f}",
                    E_eff, "руб/год")

        lines.append("\n" + "="*60)
        if E > 0 and T_ok < 3:
            lines.append("ВЫВОД: РАЗРАБОТКА ЭКОНОМИЧЕСКИ ЦЕЛЕСООБРАЗНА")
        elif E > 0:
            lines.append("ВЫВОД: РАЗРАБОТКА ЭКОНОМИЧЕСКИ ОПРАВДАНА, НО СРОК ОКУПАЕМОСТИ ВЫШЕ НОРМЫ")
        else:
            lines.append("ВЫВОД: РАЗРАБОТКА ЭКОНОМИЧЕСКИ НЕЦЕЛЕСООБРАЗНА")
        lines.append("="*60)

        self.results_text = "\n".join(lines)

        # === ВЫВОД В ИНТЕРФЕЙС ===
        self.clear_results()
        self.copy_btn.setVisible(True)

        title = QLabel("<b>📊 РЕЗУЛЬТАТЫ РАСЧЁТА</b>")
        title.setStyleSheet("font-size: 18px; color: #1f2a44; margin-bottom: 5px;")
        self.results_layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.results_layout.addWidget(line)

        def add_result(name, general_formula, formula_with_values, value, unit=""):
            group = QGroupBox(name)
            group.setStyleSheet("""
                QGroupBox {
                    background-color: rgba(255,255,255,0.9);
                    border: 1px solid #d0d8e6;
                    border-radius: 10px;
                    margin-top: 0.5ex;
                    padding: 5px;
                }
                QGroupBox::title {
                    color: #1f2a44;
                }
            """)
            layout = QVBoxLayout(group)
            layout.setSpacing(4)

            # Поле для формулы в общем виде
            general_field = self.create_copyable_field(
                general_formula, 
                "Нажмите Ctrl+A для выделения всей формулы, затем Ctrl+C для копирования"
            )
            layout.addWidget(general_field)

            # Поле для формулы с подстановкой и результатом
            values_field = self.create_copyable_field(
                formula_with_values,
                "Нажмите Ctrl+A для выделения всей формулы, затем Ctrl+C для копирования"
            )
            layout.addWidget(values_field)

            # Поле для результата (отдельно, с выделением)
            result_text = f"{value:,.2f} {unit}" if unit else f"{value:,.2f}"
            result_field = self.create_copyable_field(
                result_text,
                f"Результат: {result_text}",
                is_result=True
            )
            layout.addWidget(result_field)

            self.results_layout.addWidget(group)

        # Добавляем все блоки
        add_result(
            "1. Общие трудозатраты",
            "T = tu + ta + tn + toml + td",
            f"T = {tu} + {ta} + {tn} + {toml} + {td} = {T:.2f}",
            T, "чел-час"
        )
        add_result(
            "2. Расходы на оплату труда и страховые взносы",
            "Зот = T × Сч × кспр",
            f"Зот = {T:.2f} × {hourly} × {insurance} = {Z_ot:.2f}",
            Z_ot, "руб"
        )
        add_result(
            "3. Затраты на машинное время",
            "Змв = Смч × (tn + toml)",
            f"Змв = {machine_hour} × ({tn} + {toml}) = {Z_mv:.2f}",
            Z_mv, "руб"
        )
        add_result(
            "4. Затраты на электроэнергию",
            "Зэл = Цэл × Р × (tn + toml + td)",
            f"Зэл = {electricity} × {power} × ({tn} + {toml} + {td}) = {Z_el:.2f}",
            Z_el, "руб"
        )
        add_result(
            "5. Прочие затраты",
            "Зпр = 5% × (Зот + Змв + Зэл)",
            f"Зпр = 0.05 × ({Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f}) = {Z_pr:.2f}",
            Z_pr, "руб"
        )
        add_result(
            "6. Затраты на разработку",
            "Зрп = Зот + Змв + Зэл + Зпр",
            f"Зрп = {Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f} + {Z_pr:.2f} = {Z_rp:.2f}",
            Z_rp, "руб"
        )
        add_result(
            "7. Амортизация",
            "Ад = (На × Зрп) / 100",
            f"Ад = ({dep_rate} × {Z_rp:.2f}) / 100 = {A:.2f}",
            A, "руб/год"
        )
        add_result(
            "8. Трудоёмкость задачи",
            "Тр = Тп.к × Нтр / 100",
            f"Тр = {work_hours} × {labor_intensity} / 100 = {T_r:.2f}",
            T_r, "час/год"
        )
        add_result(
            "9. Затраты по базовому варианту",
            "Зб = Сч × Тр × (1 / Дз.п)",
            f"Зб = {hourly} × {T_r:.2f} × (1 / {salary_share}) = {Z_b:.2f}",
            Z_b, "руб/год"
        )
        add_result(
            "10. Затраты при использовании ПО",
            "Зп.п = (Тг × См + Зобщ) / Тс, где Зобщ = Зрп + Ад",
            f"Зп.п = ({work_hours} × {machine_hour} + {total_expenses:.2f}) / {useful_life} = {Z_pp:.2f}",
            Z_pp, "руб/год"
        )
        add_result(
            "11. Экономическая эффективность",
            "Э = Зб - Зп.п",
            f"Э = {Z_b:.2f} - {Z_pp:.2f} = {E:.2f}",
            E, "руб/год"
        )
        if T_ok != float('inf'):
            add_result(
                "12. Срок окупаемости",
                "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                f"Ток = {R_total:.2f} / {E:.2f} = {T_ok:.2f}",
                T_ok, "лет"
            )
        else:
            add_result(
                "12. Срок окупаемости",
                "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                f"Ток = {R_total:.2f} / {E:.2f} (Э ≤ 0)",
                0, "лет"
            )
        add_result(
            "13. Экономический эффект",
            "Е = Э / Робщ",
            f"Е = {E:.2f} / {R_total:.2f} = {E_eff:.4f}",
            E_eff, "руб/год"
        )

        # Итоговое заключение
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        self.results_layout.addWidget(line2)

        conclusion = QLabel()
        conclusion.setAlignment(Qt.AlignCenter)
        conclusion.setStyleSheet("font-size: 14px; padding: 12px; border-radius: 8px; font-weight: bold;")
        if E > 0 and T_ok < 3:
            conclusion.setText("✅ РАЗРАБОТКА ЭКОНОМИЧЕСКИ ЦЕЛЕСООБРАЗНА")
            conclusion.setStyleSheet("background: #e2f0d9; color: #1e6b2e; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
        elif E > 0:
            conclusion.setText("⚠ РАЗРАБОТКА ЭКОНОМИЧЕСКИ ОПРАВДАНА, НО СРОК ОКУПАЕМОСТИ ВЫШЕ НОРМЫ")
            conclusion.setStyleSheet("background: #fff3cd; color: #856404; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
        else:
            conclusion.setText("❌ РАЗРАБОТКА ЭКОНОМИЧЕСКИ НЕЦЕЛЕСООБРАЗНА")
            conclusion.setStyleSheet("background: #f8d7da; color: #721c24; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
        self.results_layout.addWidget(conclusion)

        # Информация о возможности копирования
        info_label = QLabel("💡 Для копирования отдельных формул выделите текст в поле выше и нажмите Ctrl+C")
        info_label.setStyleSheet("color: #6c757d; font-size: 10pt; font-style: italic; padding: 5px;")
        info_label.setAlignment(Qt.AlignCenter)
        self.results_layout.addWidget(info_label)

        self.results_layout.addStretch()
        self.tabs.setCurrentIndex(1)

    def clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


def main():
    app = QApplication(sys.argv)
    window = EconomicCalculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
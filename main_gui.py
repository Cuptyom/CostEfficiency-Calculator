import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

class EconomicCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчёт экономической эффективности ПО")
        self.setMinimumSize(900, 700)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Создаем вкладки
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Вкладка ввода данных
        self.input_tab = QWidget()
        self.tabs.addTab(self.input_tab, "Ввод данных")
        self.setup_input_tab()
        
        # Вкладка результатов
        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab, "Результаты")
        self.setup_results_tab()
        
        # Панель с кнопками (всегда внизу)
        button_panel = QHBoxLayout()
        button_panel.setSpacing(10)
        
        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.setMinimumHeight(40)
        self.calc_btn.clicked.connect(self.calculate)
        button_panel.addWidget(self.calc_btn)
        
        self.example_btn = QPushButton("Загрузить пример")
        self.example_btn.setMinimumHeight(40)
        self.example_btn.clicked.connect(self.load_example)
        button_panel.addWidget(self.example_btn)
        
        self.clear_btn = QPushButton("Очистить поля")
        self.clear_btn.setMinimumHeight(40)
        self.clear_btn.clicked.connect(self.clear_fields)
        button_panel.addWidget(self.clear_btn)
        
        button_panel.addStretch()
        main_layout.addLayout(button_panel)
    
    def setup_input_tab(self):
        """Настройка формы ввода"""
        layout = QVBoxLayout(self.input_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        form_layout = QFormLayout(container)
        form_layout.setSpacing(10)
        
        # Группа 1: Трудозатраты
        form_layout.addRow(QLabel("<b>Трудозатраты (чел-час):</b>"))
        
        self.tu = QDoubleSpinBox()
        self.tu.setRange(0, 10000)
        self.tu.setValue(194.4)
        form_layout.addRow("Исследование алгоритма (tu):", self.tu)
        
        self.ta = QDoubleSpinBox()
        self.ta.setRange(0, 10000)
        self.ta.setValue(185.14)
        form_layout.addRow("Разработка блок-схемы (ta):", self.ta)
        
        self.tn = QDoubleSpinBox()
        self.tn.setRange(0, 10000)
        self.tn.setValue(204.69)
        form_layout.addRow("Программирование (tn):", self.tn)
        
        self.toml = QDoubleSpinBox()
        self.toml.setRange(0, 10000)
        self.toml.setValue(288.0)
        form_layout.addRow("Отладка программы (toml):", self.toml)
        
        self.td = QDoubleSpinBox()
        self.td.setRange(0, 10000)
        self.td.setValue(151.2)
        form_layout.addRow("Подготовка документации (td):", self.td)
        
        # Группа 2: Финансовые параметры
        form_layout.addRow(QLabel("<b>Финансовые параметры:</b>"))
        
        self.hourly_rate = QDoubleSpinBox()
        self.hourly_rate.setRange(0, 100000)
        self.hourly_rate.setValue(238.1)
        form_layout.addRow("Среднечасовая оплата (руб/час):", self.hourly_rate)
        
        self.insurance = QDoubleSpinBox()
        self.insurance.setRange(0, 10)
        self.insurance.setValue(1.3)
        self.insurance.setSingleStep(0.05)
        form_layout.addRow("Коэф. страховых взносов:", self.insurance)
        
        self.machine_hour = QDoubleSpinBox()
        self.machine_hour.setRange(0, 10000)
        self.machine_hour.setValue(21.05)
        form_layout.addRow("Стоимость машино-часа (руб):", self.machine_hour)
        
        self.electricity = QDoubleSpinBox()
        self.electricity.setRange(0, 100)
        self.electricity.setValue(7.28)
        form_layout.addRow("Стоимость электроэнергии (руб/кВт·ч):", self.electricity)
        
        self.power = QDoubleSpinBox()
        self.power.setRange(0, 10)
        self.power.setValue(0.5)
        self.power.setSingleStep(0.05)
        form_layout.addRow("Мощность ПК (кВт):", self.power)
        
        # Группа 3: Базовый вариант
        form_layout.addRow(QLabel("<b>Базовый вариант:</b>"))
        
        self.work_hours = QDoubleSpinBox()
        self.work_hours.setRange(0, 8760)
        self.work_hours.setValue(2112)
        form_layout.addRow("Фонд рабочего времени (час/год):", self.work_hours)
        
        self.labor_intensity = QDoubleSpinBox()
        self.labor_intensity.setRange(0, 100)
        self.labor_intensity.setValue(39)
        form_layout.addRow("Трудоёмкость задачи (%):", self.labor_intensity)
        
        self.salary_share = QDoubleSpinBox()
        self.salary_share.setRange(0, 1)
        self.salary_share.setValue(0.5)
        self.salary_share.setSingleStep(0.05)
        form_layout.addRow("Доля зарплаты в смете:", self.salary_share)
        
        # Группа 4: Амортизация
        form_layout.addRow(QLabel("<b>Амортизация:</b>"))
        
        self.useful_life = QSpinBox()
        self.useful_life.setRange(1, 20)
        self.useful_life.setValue(6)
        form_layout.addRow("Срок полезного использования (лет):", self.useful_life)
        
        self.depreciation_rate = QDoubleSpinBox()
        self.depreciation_rate.setRange(0, 100)
        self.depreciation_rate.setValue(16.67)
        self.depreciation_rate.setSingleStep(0.01)
        form_layout.addRow("Норма амортизации (%):", self.depreciation_rate)
        
        self.pc_cost = QDoubleSpinBox()
        self.pc_cost.setRange(0, 10000000)
        self.pc_cost.setValue(129600)
        form_layout.addRow("Стоимость ПК (руб):", self.pc_cost)
        
        # Добавляем растяжку в конце формы
        form_layout.addRow(QLabel(""))
        form_layout.addRow(QLabel(""))
    
    def setup_results_tab(self):
        """Настройка вкладки результатов"""
        layout = QVBoxLayout(self.results_tab)
        
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        layout.addWidget(self.results_scroll)
        
        self.results_container = QWidget()
        self.results_scroll.setWidget(self.results_container)
        self.results_layout = QVBoxLayout(self.results_container)
    
    def load_example(self):
        """Загрузка значений из диплома"""
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
        """Очистка полей ввода"""
        for widget in self.findChildren(QDoubleSpinBox):
            widget.clear()
        for widget in self.findChildren(QSpinBox):
            widget.clear()
    
    def calculate(self):
        """Выполнение расчёта и вывод результатов"""
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
        
        # === РАСЧЁТЫ ===
        
        # 1. Общие трудозатраты
        T = tu + ta + tn + toml + td
        
        # 2. Расходы на оплату труда и страховые взносы
        Z_ot = T * hourly * insurance
        
        # 3. Затраты на машинное время
        Z_mv = machine_hour * (tn + toml)
        
        # 4. Затраты на электроэнергию
        Z_el = electricity * power * (tn + toml + td)
        
        # 5. Прочие затраты (5%)
        Z_pr = 0.05 * (Z_ot + Z_mv + Z_el)
        
        # 6. Затраты на разработку
        Z_rp = Z_ot + Z_mv + Z_el + Z_pr
        
        # 7. Амортизация
        A = (dep_rate / 100) * Z_rp
        
        # 8. Трудоёмкость задачи
        T_r = work_hours * (labor_intensity / 100)
        
        # 9. Затраты по базовому варианту
        Z_b = hourly * T_r * (1 / salary_share)
        
        # 10. Затраты при использовании программы
        Z_pp = (work_hours * machine_hour + Z_rp) / useful_life
        
        # 11. Экономическая эффективность
        E = Z_b - Z_pp
        
        # 12. Срок окупаемости
        R_total = pc_cost + Z_rp
        T_ok = R_total / E if E > 0 else float('inf')
        
        # 13. Экономический эффект
        E_eff = E / R_total if R_total > 0 else 0
        
        # === ВЫВОД РЕЗУЛЬТАТОВ ===
        self.clear_results()
        
        # Заголовок
        title = QLabel("<b>РЕЗУЛЬТАТЫ РАСЧЁТА</b>")
        title.setStyleSheet("font-size: 16px;")
        self.results_layout.addWidget(title)
        
        # Разделитель
        self.results_layout.addWidget(QLabel("="*90))
        
        # Функция для добавления результата
        def add_result(name, general_formula, formula_with_values, value, unit=""):
            group = QGroupBox(name)
            layout = QVBoxLayout(group)
            
            # Формула в общем виде
            general_label = QLabel(f"<b>Формула (общий вид):</b> {general_formula}")
            general_label.setStyleSheet("font-family: 'Courier New'; color: #2c3e50;")
            layout.addWidget(general_label)
            
            # Формула с подставленными значениями
            values_label = QLabel(f"<b>С подстановкой:</b> {formula_with_values}")
            values_label.setStyleSheet("font-family: 'Courier New'; color: #34495e;")
            layout.addWidget(values_label)
            
            # Результат
            if unit:
                result_label = QLabel(f"<b>Результат:</b> {value:,.2f} {unit}")
            else:
                result_label = QLabel(f"<b>Результат:</b> {value:,.2f}")
            result_label.setStyleSheet("color: #2980b9; font-weight: bold;")
            layout.addWidget(result_label)
            
            self.results_layout.addWidget(group)
        
        # Вывод всех результатов с тремя строками: общая формула, с подстановкой, результат
        
        # 1. Общие трудозатраты
        add_result(
            "1. Общие трудозатраты",
            "T = tu + ta + tn + toml + td",
            f"T = {tu} + {ta} + {tn} + {toml} + {td}",
            T, "чел-час"
        )
        
        # 2. Расходы на оплату труда и страховые взносы
        add_result(
            "2. Расходы на оплату труда и страховые взносы",
            "Зот = T × Сч × кспр",
            f"Зот = {T:.2f} × {hourly} × {insurance}",
            Z_ot, "руб"
        )
        
        # 3. Затраты на машинное время
        add_result(
            "3. Затраты на машинное время",
            "Змв = Смч × (tn + toml)",
            f"Змв = {machine_hour} × ({tn} + {toml})",
            Z_mv, "руб"
        )
        
        # 4. Затраты на электроэнергию
        add_result(
            "4. Затраты на электроэнергию",
            "Зэл = Цэл × Р × (tn + toml + td)",
            f"Зэл = {electricity} × {power} × ({tn} + {toml} + {td})",
            Z_el, "руб"
        )
        
        # 5. Прочие затраты
        add_result(
            "5. Прочие затраты",
            "Зпр = 5% × (Зот + Змв + Зэл)",
            f"Зпр = 0.05 × ({Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f})",
            Z_pr, "руб"
        )
        
        # 6. Затраты на разработку
        add_result(
            "6. Затраты на разработку",
            "Зрп = Зот + Змв + Зэл + Зпр",
            f"Зрп = {Z_ot:.2f} + {Z_mv:.2f} + {Z_el:.2f} + {Z_pr:.2f}",
            Z_rp, "руб"
        )
        
        # 7. Амортизация
        add_result(
            "7. Амортизация",
            "Ад = (На × К) / 100",
            f"Ад = ({dep_rate} × {Z_rp:.2f}) / 100",
            A, "руб/год"
        )
        
        # 8. Трудоёмкость задачи
        add_result(
            "8. Трудоёмкость задачи",
            "Тр = Тп.к × Нтр / 100",
            f"Тр = {work_hours} × {labor_intensity} / 100",
            T_r, "час/год"
        )
        
        # 9. Затраты по базовому варианту
        add_result(
            "9. Затраты по базовому варианту",
            "Зб = Сч × Тр × (1 / Дз.п)",
            f"Зб = {hourly} × {T_r:.2f} × (1 / {salary_share})",
            Z_b, "руб/год"
        )
        
        # 10. Затраты при использовании программы
        add_result(
            "10. Затраты при использовании ПО",
            "Зп.п = (Тг × См + Зобщ) / Тс",
            f"Зп.п = ({work_hours} × {machine_hour} + {Z_rp:.2f}) / {useful_life}",
            Z_pp, "руб/год"
        )
        
        # 11. Экономическая эффективность
        add_result(
            "11. Экономическая эффективность",
            "Э = Зб - Зп.п",
            f"Э = {Z_b:.2f} - {Z_pp:.2f}",
            E, "руб/год"
        )
        
        # 12. Срок окупаемости
        if T_ok != float('inf'):
            add_result(
                "12. Срок окупаемости",
                "Ток = Робщ / Э",
                f"Ток = {R_total:.2f} / {E:.2f}",
                T_ok, "лет"
            )
        else:
            add_result(
                "12. Срок окупаемости",
                "Ток = Робщ / Э",
                f"Ток = {R_total:.2f} / {E:.2f} (Э ≤ 0)",
                0, "лет"
            )
        
        # 13. Экономический эффект
        add_result(
            "13. Экономический эффект",
            "Е = Э / Робщ",
            f"Е = {E:.2f} / {R_total:.2f}",
            E_eff, "руб/год"
        )
        
        # Итоговое заключение
        self.results_layout.addWidget(QLabel("="*90))
        conclusion = QLabel()
        if E > 0 and T_ok < 3:
            conclusion.setText("<b>✅ РАЗРАБОТКА ЭКОНОМИЧЕСКИ ЦЕЛЕСООБРАЗНА</b>")
            conclusion.setStyleSheet("color: green; font-size: 14px;")
        elif E > 0:
            conclusion.setText("<b>⚠ РАЗРАБОТКА ЭКОНОМИЧЕСКИ ОПРАВДАНА, НО СРОК ОКУПАЕМОСТИ ВЫШЕ НОРМЫ</b>")
            conclusion.setStyleSheet("color: orange; font-size: 14px;")
        else:
            conclusion.setText("<b>❌ РАЗРАБОТКА ЭКОНОМИЧЕСКИ НЕЦЕЛЕСООБРАЗНА</b>")
            conclusion.setStyleSheet("color: red; font-size: 14px;")
        self.results_layout.addWidget(conclusion)
        
        # Растяжка
        self.results_layout.addStretch()
        
        # Переключаемся на вкладку результатов
        self.tabs.setCurrentIndex(1)
    
    def clear_results(self):
        """Очистка результатов"""
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
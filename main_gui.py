import sys
import re
import math
import csv
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QLocale, Signal
from PySide6.QtGui import QIcon, QFont, QGuiApplication

# Для графиков
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

# Подавляем предупреждения matplotlib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# =================== КАСТОМНЫЙ GROUPBOX С КЛИКОМ ===================
class ClickableGroupBox(QGroupBox):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
# ==================================================================

# =================== КАСТОМНЫЕ СПИНБОКСЫ БЕЗ КОЛЁСИКА ===================
class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()
# ======================================================================

class MplCanvas(FigureCanvas):
    """Канва для отображения графиков Matplotlib с фиксированным размером"""
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # Используем constrained_layout для стабильного позиционирования
        self.fig = Figure(figsize=(width, height), dpi=dpi,
                          facecolor='#f5f7fa',
                          constrained_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        # Фиксируем минимальный размер, чтобы холст не сжимался
        self.setMinimumSize(width * dpi, height * dpi)
        self.axes = self.fig.add_subplot(111)

class EconomicCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчёт экономической эффективности ПО")
        self.setMinimumSize(1000, 800)

        self.locale = QLocale("ru_RU")
        self.apply_styles()

        # Параметры для графика точки безубыточности (по умолчанию)
        self.sales_per_month = 5
        self.price_per_copy = 1000.0
        self.var_cost_per_unit = 300.0  # фиксировано

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.input_tab = QWidget()
        self.tabs.addTab(self.input_tab, "Ввод данных")
        self.setup_input_tab()

        self.results_tab = QWidget()
        self.tabs.addTab(self.results_tab, "Результаты")
        self.setup_results_tab()

        self.charts_tab = QWidget()
        self.tabs.addTab(self.charts_tab, "Графики")
        self.setup_charts_tab()

        # Панель кнопок
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

        self.results_text = ""
        self.calculation_data = None

        # Словарь для описания переменных
        self.var_descriptions = {
            'tu': 'Исследование алгоритма',
            'ta': 'Разработка блок-схемы',
            'tn': 'Программирование',
            'toml': 'Отладка программы',
            'td': 'Подготовка документации',
            'T': 'Общие трудозатраты',
            'Сч': 'Среднечасовая оплата',
            'кспр': 'Коэф. страховых взносов',
            'Смч': 'Стоимость машино-часа',
            'Цэл': 'Стоимость электроэнергии',
            'Р': 'Мощность ПК',
            'Тп.к': 'Фонд рабочего времени',
            'Нтр': 'Трудоёмкость задачи (%)',
            'Дз.п': 'Доля зарплаты в смете',
            'На': 'Норма амортизации',
            'Сбал': 'Стоимость ПК',
            'Тс': 'Срок полезного использования',
            'Тг': 'Время работы с программой',
            'См': 'Стоимость машинного часа',
            'Зобщ': 'Общие годовые эксплуатационные затраты',
            'Робщ': 'Общие расходы',
            'Зот': 'Расходы на оплату труда',
            'Змв': 'Затраты на машинное время',
            'Зэл': 'Затраты на электроэнергию',
            'Зпр': 'Прочие затраты',
            'Зрп': 'Затраты на разработку',
            'Ад': 'Амортизация',
            'Тр': 'Трудоёмкость задачи',
            'Зб': 'Затраты по базовому варианту',
            'Зп.п': 'Затраты при использовании ПО',
            'Э': 'Экономическая эффективность',
            'Ток': 'Срок окупаемости',
            'Е': 'Экономический эффект',
        }

    def format_number(self, value):
        """Форматирует число с 2 знаками после запятой"""
        if isinstance(value, int):
            value = float(value)
        return self.locale.toString(value, 'f', 2)

    def format_number_no_decimals(self, value):
        """Форматирует число без десятичных знаков"""
        value = float(value)
        return self.locale.toString(value, 'f', 0)

    def format_with_indices(self, text):
        replacements = {
            'tu': 't<sub>u</sub>',
            'ta': 't<sub>a</sub>',
            'tn': 't<sub>n</sub>',
            'toml': 't<sub>oml</sub>',
            'td': 't<sub>d</sub>',
            'T': 'T',
            'Зот': 'З<sub>от</sub>',
            'Змв': 'З<sub>мв</sub>',
            'Зэл': 'З<sub>эл</sub>',
            'Зпр': 'З<sub>пр</sub>',
            'Зрп': 'З<sub>рп</sub>',
            'Ад': 'А<sub>д</sub>',
            'Тр': 'Т<sub>р</sub>',
            'Зб': 'З<sub>б</sub>',
            'Зп.п': 'З<sub>п.п</sub>',
            'Ток': 'Т<sub>ок</sub>',
            'Робщ': 'Р<sub>общ</sub>',
            'Сч': 'С<sub>ч</sub>',
            'кспр': 'к<sub>спр</sub>',
            'Смч': 'С<sub>мч</sub>',
            'Цэл': 'Ц<sub>эл</sub>',
            'Тп.к': 'Т<sub>п.к</sub>',
            'Нтр': 'Н<sub>тр</sub>',
            'Дз.п': 'Д<sub>з.п</sub>',
            'Тг': 'Т<sub>г</sub>',
            'См': 'С<sub>м</sub>',
            'Зобщ': 'З<sub>общ</sub>',
            'Тс': 'Т<sub>с</sub>',
            'Сбал': 'С<sub>бал</sub>',
            'На': 'Н<sub>а</sub>',
            'Е': 'Е',
            'Э': 'Э',
            'Р': 'Р',
        }
        for key in sorted(replacements.keys(), key=len, reverse=True):
            pattern = r'(?<![A-Za-zА-Яа-я0-9])' + re.escape(key) + r'(?![A-Za-zА-Яа-я0-9\.])'
            text = re.sub(pattern, replacements[key], text)
        return text

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
        QLabel[cssClass="unit"] {
            color: #5b7cfa;
            font-weight: bold;
            font-size: 10pt;
            padding: 0 5px;
            min-width: 40px;
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
            padding: 5px 10px;
            min-height: 28px;
            min-width: 120px;
        }
        NoWheelDoubleSpinBox:focus, NoWheelSpinBox:focus {
            border: 2px solid #5b7cfa;
            background-color: #f4f7ff;
        }
        NoWheelDoubleSpinBox::up-button, NoWheelSpinBox::up-button,
        NoWheelDoubleSpinBox::down-button, NoWheelSpinBox::down-button {
            width: 0px;
            height: 0px;
            border: none;
        }
        NoWheelDoubleSpinBox::up-arrow, NoWheelSpinBox::up-arrow,
        NoWheelDoubleSpinBox::down-arrow, NoWheelSpinBox::down-arrow {
            width: 0px;
            height: 0px;
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
        QLabel.formula-label {
            background-color: #f8f9fc;
            border: 1px solid #d0d8e6;
            border-radius: 6px;
            padding: 6px 8px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
            color: #1f2a44;
        }
        QLabel.formula-label[cssClass="result"] {
            background-color: #eef3ff;
            border: 2px solid #5b7cfa;
            font-weight: bold;
            color: #1f2a44;
        }
        """
        self.setStyleSheet(style)

    def create_input_row(self, label_text, unit_text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        label.setMinimumWidth(250)
        layout.addWidget(label)
        spinbox = NoWheelDoubleSpinBox()
        spinbox.setRange(0, 1e9)
        layout.addWidget(spinbox)
        unit_label = QLabel(unit_text)
        unit_label.setProperty("cssClass", "unit")
        layout.addWidget(unit_label)
        layout.addStretch()
        return widget, spinbox

    def create_int_input_row(self, label_text, unit_text):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(label_text)
        label.setMinimumWidth(250)
        layout.addWidget(label)
        spinbox = NoWheelSpinBox()
        spinbox.setRange(0, 1e9)
        layout.addWidget(spinbox)
        unit_label = QLabel(unit_text)
        unit_label.setProperty("cssClass", "unit")
        layout.addWidget(unit_label)
        layout.addStretch()
        return widget, spinbox

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

        instruction_label = QLabel(
            "Инструкция: Введите исходные данные в поля ниже. "
            "Для быстрого заполнения нажмите «Загрузить пример». "
            "После ввода всех данных нажмите «Рассчитать» для получения отчёта."
        )
        instruction_label.setStyleSheet("""
            background-color: #eef3ff;
            border: 1px solid #5b7cfa;
            border-radius: 8px;
            padding: 10px;
            color: #1f2a44;
            font-size: 11pt;
        """)
        instruction_label.setWordWrap(True)
        form_layout.insertWidget(0, instruction_label)

        # Группа 1: Трудозатраты
        group_tu = QGroupBox("Трудозатраты (чел-час)")
        group_tu_layout = QVBoxLayout(group_tu)
        group_tu_layout.setSpacing(8)

        row1, self.tu = self.create_input_row("Исследование алгоритма (tu):", "(чел-час)")
        group_tu_layout.addWidget(row1)
        row2, self.ta = self.create_input_row("Разработка блок-схемы (ta):", "(чел-час)")
        group_tu_layout.addWidget(row2)
        row3, self.tn = self.create_input_row("Программирование (tn):", "(чел-час)")
        group_tu_layout.addWidget(row3)
        row4, self.toml = self.create_input_row("Отладка программы (toml):", "(чел-час)")
        group_tu_layout.addWidget(row4)
        row5, self.td = self.create_input_row("Подготовка документации (td):", "(чел-час)")
        group_tu_layout.addWidget(row5)

        form_layout.addWidget(group_tu)

        # Группа 2: Финансовые параметры
        group_fin = QGroupBox("Финансовые параметры")
        group_fin_layout = QVBoxLayout(group_fin)
        group_fin_layout.setSpacing(8)

        row6, self.hourly_rate = self.create_input_row("Среднечасовая оплата (руб/час):", "(руб/час)")
        group_fin_layout.addWidget(row6)
        row7, self.insurance = self.create_input_row("Коэф. страховых взносов:", "(коэф.)")
        group_fin_layout.addWidget(row7)
        row8, self.machine_hour = self.create_input_row("Стоимость машино-часа (руб):", "(руб/час)")
        group_fin_layout.addWidget(row8)
        row9, self.electricity = self.create_input_row("Стоимость электроэнергии (руб/кВт·ч):", "(руб/кВт·ч)")
        group_fin_layout.addWidget(row9)
        row10, self.power = self.create_input_row("Мощность ПК (кВт):", "(кВт)")
        group_fin_layout.addWidget(row10)

        form_layout.addWidget(group_fin)

        # Группа 3: Базовый вариант
        group_base = QGroupBox("Базовый вариант")
        group_base_layout = QVBoxLayout(group_base)
        group_base_layout.setSpacing(8)

        row11, self.work_hours = self.create_input_row("Фонд рабочего времени (час/год):", "(час/год)")
        group_base_layout.addWidget(row11)
        row12, self.labor_intensity = self.create_input_row("Трудоёмкость задачи (%):", "(%)")
        group_base_layout.addWidget(row12)
        row13, self.salary_share = self.create_input_row("Доля зарплаты в смете:", "(доля)")
        group_base_layout.addWidget(row13)

        form_layout.addWidget(group_base)

        # Группа 4: Амортизация
        group_amort = QGroupBox("Амортизация")
        group_amort_layout = QVBoxLayout(group_amort)
        group_amort_layout.setSpacing(8)

        row14, self.useful_life = self.create_int_input_row("Срок полезного использования (лет):", "(лет)")
        group_amort_layout.addWidget(row14)
        row15, self.depreciation_rate = self.create_input_row("Норма амортизации (%):", "(%)")
        group_amort_layout.addWidget(row15)
        row16, self.pc_cost = self.create_input_row("Стоимость ПК (руб):", "(руб)")
        group_amort_layout.addWidget(row16)

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

        # Кнопка копирования результатов
        self.copy_btn = QPushButton("Копировать все результаты")
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.clicked.connect(self.copy_results)
        self.copy_btn.setVisible(False)
        layout.addWidget(self.copy_btn)

        # Кнопка экспорта сводной таблицы в CSV
        self.export_btn = QPushButton("Экспортировать сводную таблицу (CSV)")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self.export_results_csv)
        self.export_btn.setVisible(False)
        layout.addWidget(self.export_btn)

    def setup_charts_tab(self):
        """Настройка вкладки с графиками (с прокруткой)"""
        # Основной скролл-контейнер
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Контейнер для всех элементов
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Информационная панель
        info_label = QLabel(
            "Графики финансового анализа — "
            "нажмите «Рассчитать» для построения графиков на основе введённых данных."
        )
        info_label.setStyleSheet("""
            background-color: #eef3ff;
            border: 1px solid #5b7cfa;
            border-radius: 8px;
            padding: 10px;
            color: #1f2a44;
            font-size: 11pt;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Панель параметров для графика "Точка безубыточности"
        param_group = QGroupBox("Параметры графика «Точка безубыточности»")
        param_layout = QHBoxLayout(param_group)
        param_layout.setSpacing(10)

        lbl_sales = QLabel("Продажи в месяц (шт.):")
        self.sales_spin = QSpinBox()
        self.sales_spin.setRange(1, 100000)
        self.sales_spin.setValue(self.sales_per_month)
        self.sales_spin.valueChanged.connect(self.on_sales_params_changed)

        lbl_price = QLabel("Цена за копию (руб.):")
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.01, 1e9)
        self.price_spin.setValue(self.price_per_copy)
        self.price_spin.valueChanged.connect(self.on_sales_params_changed)

        param_layout.addWidget(lbl_sales)
        param_layout.addWidget(self.sales_spin)
        param_layout.addWidget(lbl_price)
        param_layout.addWidget(self.price_spin)
        param_layout.addStretch()

        layout.addWidget(param_group)

        # Канва графика (размер 12x8 дюймов)
        self.chart_canvas = MplCanvas(self, width=12, height=8, dpi=100)
        # Разрешаем холсту растягиваться
        self.chart_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chart_canvas)

        # Панель навигации Matplotlib
        toolbar = NavigationToolbar(self.chart_canvas, self)
        layout.addWidget(toolbar)

        # Кнопки управления
        refresh_btn = QPushButton("Обновить графики")
        refresh_btn.setMinimumHeight(35)
        refresh_btn.clicked.connect(self.update_charts)
        layout.addWidget(refresh_btn)

        self.export_charts_btn = QPushButton("Экспортировать данные графиков (CSV)")
        self.export_charts_btn.setMinimumHeight(35)
        self.export_charts_btn.clicked.connect(self.export_charts_data_csv)
        self.export_charts_btn.setVisible(False)
        layout.addWidget(self.export_charts_btn)

        # Добавляем растяжку в конце
        layout.addStretch()

        # Устанавливаем контейнер в скролл-область
        scroll.setWidget(container)

        # Размещаем скролл-область на вкладке
        main_layout = QVBoxLayout(self.charts_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Рисуем заглушку (пустой график)
        self.draw_empty_chart()

    def on_sales_params_changed(self):
        """Слот для обновления параметров графика при изменении полей"""
        self.sales_per_month = self.sales_spin.value()
        self.price_per_copy = self.price_spin.value()
        self.update_charts()  # перерисовываем графики с новыми параметрами

    def draw_empty_chart(self):
        """Рисует заглушку на графике"""
        canvas = self.chart_canvas
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)
        ax.text(
            0.5, 0.5,
            "Нажмите «Рассчитать»\nдля построения графиков",
            horizontalalignment='center',
            verticalalignment='center',
            transform=ax.transAxes,
            fontsize=14,
            color='#666'
        )
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        canvas.draw()

    def update_charts(self):
        if not self.calculation_data:
            QMessageBox.information(
                self, "Нет данных",
                "Сначала выполните расчёт (нажмите «Рассчитать»)."
            )
            return
        self.draw_charts()

    def draw_charts(self):
        if not self.calculation_data:
            self.draw_empty_chart()
            return

        data = self.calculation_data
        canvas = self.chart_canvas
        canvas.fig.clear()

        # Получаем данные
        Z_ot = data['Z_ot']
        Z_mv = data['Z_mv']
        Z_el = data['Z_el']
        Z_pr = data['Z_pr']
        Z_rp = data['Z_rp']
        A = data['A']
        total_expenses = data['total_expenses']
        E = data['E']
        E_eff = data['E_eff']
        T_ok = data['T_ok']

        # Создаём четыре подграфика в сетке 2x2
        ax1 = canvas.fig.add_subplot(2, 2, 1)
        ax2 = canvas.fig.add_subplot(2, 2, 2)
        ax3 = canvas.fig.add_subplot(2, 2, 3)
        ax4 = canvas.fig.add_subplot(2, 2, 4)

        # 1. Структура затрат (круговая диаграмма с легендой)
        costs = [Z_ot, Z_mv, Z_el, Z_pr]
        labels = ['Заработная плата', 'Машинное время', 'Электроэнергия', 'Прочие затраты']
        colors = ['#3498db', '#2ecc71', '#e67e22', '#e74c3c']

        filtered = [(c, l, col) for c, l, col in zip(costs, labels, colors) if c > 0]

        if filtered:
            vals, lbls, cols = zip(*filtered)
            wedges, texts, autotexts = ax1.pie(
                vals,
                labels=None,
                colors=cols,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 9, 'color': '#2c3e50', 'fontweight': 'bold'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 1}
            )

            legend_labels = [f'{l} ({v:,.0f} руб.)' for l, v in zip(lbls, vals)]
            legend_handles = [plt.Rectangle((0,0), 1, 1, color=c) for c in cols]
            legend = ax1.legend(
                legend_handles,
                legend_labels,
                loc='center left',
                bbox_to_anchor=(-0.8, 0.5),
                fontsize=8,
                framealpha=0.95,
                edgecolor='#d0d8e6',
                title='Статьи затрат',
                title_fontsize=9,
                borderpad=0.5,
                handlelength=1.5,
                handletextpad=0.8
            )
            ax1.set_title('Структура затрат на разработку', fontsize=11, fontweight='bold', color='#2c3e50')
            ax1.set_position([0.2, 0.55, 0.2, 0.35])
        else:
            ax1.text(0.5, 0.5, 'Нет данных', ha='center', va='center', fontsize=12)
            ax1.set_title('Структура затрат', fontsize=11, fontweight='bold')

        # ========== 2. НОВЫЙ ГРАФИК ТОЧКИ БЕЗУБЫТОЧНОСТИ с параметрами продаж ==========
        sales_per_month = self.sales_per_month
        price_per_copy = self.price_per_copy
        var_cost_per_unit = 300.0

        fixed_costs = Z_rp

        if price_per_copy > var_cost_per_unit:
            break_even_units = fixed_costs / (price_per_copy - var_cost_per_unit)
        else:
            break_even_units = float('inf')

        max_units = max(break_even_units * 2.5 if break_even_units != float('inf') else 1000, 100)
        x = np.linspace(0, max_units, 200)
        revenue = price_per_copy * x
        total_cost = fixed_costs + var_cost_per_unit * x

        ax2.plot(x, revenue, 'g-', linewidth=2, label='Выручка')
        ax2.plot(x, total_cost, 'r-', linewidth=2, label='Общие затраты')
        ax2.axhline(y=fixed_costs, color='b', linestyle='--', linewidth=1.5, label='Постоянные затраты', alpha=0.7)

        if break_even_units != float('inf') and break_even_units <= max_units:
            ax2.axvline(x=break_even_units, color='k', linestyle=':', linewidth=1, alpha=0.7)
            ax2.plot(break_even_units, price_per_copy * break_even_units, 'ko', markersize=8)
            ax2.annotate(f'Точка безубыточности\n{break_even_units:.0f} ед.',
                         xy=(break_even_units, price_per_copy * break_even_units),
                         xytext=(break_even_units * 0.5, price_per_copy * break_even_units * 1.3),
                         fontsize=8, ha='center',
                         arrowprops=dict(arrowstyle='->', color='gray', lw=1))

            if sales_per_month > 0:
                payback_months = break_even_units / sales_per_month
                ax2.text(0.98, 0.05,
                         f'Точка безубыточности: {payback_months:.1f} мес.\n'
                         f'(при {sales_per_month} шт./мес.)',
                         transform=ax2.transAxes,
                         fontsize=8,
                         verticalalignment='bottom',
                         horizontalalignment='right',
                         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        else:
            ax2.text(0.5, 0.5, 'Точка безубыточности не достигается\n(цена ≤ переменные затраты)',
                     transform=ax2.transAxes, ha='center', va='center', fontsize=10, color='red')

        ax2.set_xlabel('Объём продаж (шт.)')
        ax2.set_ylabel('Затраты / Выручка (руб)')
        ax2.set_title(f'Точка безубыточности\n(цена = {price_per_copy:.0f} руб., переменные затраты = {var_cost_per_unit:.0f} руб.)',
                     fontsize=11, fontweight='bold')
        ax2.legend(loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, max_units)
        ax2.set_ylim(0, max(revenue.max(), total_cost.max()) * 1.1)

        # 3. Ежемесячные доходы и расходы
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        x_months = np.arange(len(months))
        width = 0.35

        monthly_saving = E / 12 if E > 0 else 0
        seasonal_factors = [0.7, 0.65, 0.8, 0.85, 0.9, 1.0,
                           1.0, 0.95, 0.9, 1.0, 1.05, 1.1]
        monthly_income = [E / 12 * f for f in seasonal_factors]
        monthly_expenses = monthly_saving * 0.7 * np.array(seasonal_factors)

        ax3.bar(x_months - width/2, monthly_income, width, label='Доходы', color='#2ecc71', alpha=0.8)
        ax3.bar(x_months + width/2, monthly_expenses, width, label='Расходы', color='#e74c3c', alpha=0.8)

        ax3.set_xlabel('Месяцы')
        ax3.set_ylabel('Сумма (руб)')
        ax3.set_title('Ежемесячные доходы и расходы', fontsize=11, fontweight='bold')
        ax3.set_xticks(x_months)
        ax3.set_xticklabels(months, rotation=45, ha='right')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. Накопленный денежный поток
        years = np.arange(0, 6, 1)
        yearly_income = E
        cumulative_cash = -Z_rp + yearly_income * years

        ax4.plot(years, cumulative_cash, 'b-o', linewidth=2, markersize=8, label='Накопленный поток')
        ax4.axhline(y=0, color='k', linestyle='-', linewidth=1, alpha=0.5)

        if T_ok != float('inf') and T_ok <= 6:
            ax4.axvline(x=T_ok, color='r', linestyle='--', linewidth=1.5, alpha=0.7)
            ax4.plot(T_ok, 0, 'ro', markersize=8)
            max_cash = max(cumulative_cash) if max(cumulative_cash) > 0 else 10000
            ax4.annotate(f'Окупаемость\n{T_ok:.1f} лет',
                        xy=(T_ok, 0),
                        xytext=(T_ok * 0.7, max_cash * 0.3),
                        fontsize=8, ha='center',
                        arrowprops=dict(arrowstyle='->', color='gray', lw=1))

        ax4.set_xlabel('Годы')
        ax4.set_ylabel('Накопленный денежный поток (руб)')
        ax4.set_title('Накопленный денежный поток и срок окупаемости',
                     fontsize=11, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)
        ax4.set_xlim(0, 5.5)
        ax4.set_xticks(years)

        # Принудительно обновляем холст – размер фигуры уже зафиксирован через constrained_layout
        canvas.draw()

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
        # Параметры продаж для графика точки безубыточности
        self.sales_spin.setValue(5)
        self.price_spin.setValue(1000.0)
        # Обновляем поля ввода (они уже есть на вкладке "Графики")
        self.sales_per_month = 5
        self.price_per_copy = 1000.0

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

    def create_formula_label(self, text, tooltip="", is_result=False):
        label = QLabel()
        label.setText(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        if is_result:
            label.setProperty("cssClass", "result")
        else:
            label.setProperty("cssClass", "formula-label")
        if tooltip:
            label.setToolTip(tooltip)
        return label

    def safe_divide(self, numerator, denominator):
        if denominator == 0:
            return float('inf')
        return numerator / denominator

    def show_formula_details(self, name, general, subst, value, unit, variables, description=""):
        dialog = QDialog(self)
        dialog.setWindowTitle("Подробности расчёта")
        dialog.setMinimumSize(600, 400)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        title = QLabel(f"<b>{name}</b>")
        title.setStyleSheet("font-size: 14pt; color: #1f2a44;")
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        lbl_general = QLabel(f"<b>Общая формула:</b> {general}")
        lbl_general.setWordWrap(True)
        lbl_general.setStyleSheet("font-size: 11pt;")
        layout.addWidget(lbl_general)

        lbl_subst = QLabel(f"<b>Подстановка значений:</b> {subst}")
        lbl_subst.setWordWrap(True)
        lbl_subst.setStyleSheet("font-size: 11pt;")
        layout.addWidget(lbl_subst)

        if variables:
            lbl_vars_title = QLabel("<b>Значения переменных:</b>")
            lbl_vars_title.setStyleSheet("font-size: 11pt; margin-top: 8px;")
            layout.addWidget(lbl_vars_title)

            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Обозначение", "Значение", "Описание"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)
            table.setRowCount(len(variables))

            for i, (var_name, var_value, var_desc) in enumerate(variables):
                item_name = QTableWidgetItem(var_name)
                item_name.setFont(QFont("Consolas", 10))
                table.setItem(i, 0, item_name)
                item_value = QTableWidgetItem(var_value)
                item_value.setFont(QFont("Consolas", 10))
                table.setItem(i, 1, item_value)
                item_desc = QTableWidgetItem(var_desc)
                table.setItem(i, 2, item_desc)

            table.resizeColumnsToContents()
            table.setMaximumHeight(200)
            layout.addWidget(table)

        if value == float('inf'):
            result_text = "∞ (деление на ноль)"
        else:
            if isinstance(value, float):
                result_text = self.format_number(value)
            else:
                result_text = str(value)
            if unit:
                result_text += f" {unit}"
        lbl_result = QLabel(f"<b>Результат:</b> {result_text}")
        lbl_result.setStyleSheet("font-size: 11pt; color: #5b7cfa; font-weight: bold;")
        layout.addWidget(lbl_result)

        if description:
            lbl_desc = QLabel(f"<i>{description}</i>")
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #555; font-size: 10pt; margin-top: 5px;")
            layout.addWidget(lbl_desc)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        btn_close.setMinimumHeight(35)
        layout.addWidget(btn_close)

        dialog.exec()

    def export_results_csv(self):
        """Экспорт сводной таблицы результатов в CSV"""
        if not self.calculation_data:
            QMessageBox.information(self, "Нет данных", "Сначала выполните расчёт.")
            return

        data = self.calculation_data
        rows = [
            ["Показатель", "Значение", "Ед. изм."],
            ["Общие трудозатраты (T)", self.format_number(data['T']), "чел-час"],
            ["Расходы на оплату труда (Зот)", self.format_number(data['Z_ot']), "руб"],
            ["Затраты на машинное время (Змв)", self.format_number(data['Z_mv']), "руб"],
            ["Затраты на электроэнергию (Зэл)", self.format_number(data['Z_el']), "руб"],
            ["Прочие затраты (Зпр)", self.format_number(data['Z_pr']), "руб"],
            ["Затраты на разработку (Зрп)", self.format_number(data['Z_rp']), "руб"],
            ["Амортизация (Ад)", self.format_number(data['A']), "руб/год"],
            ["Трудоёмкость задачи (Тр)", self.format_number(data['T_r']), "час/год"],
            ["Затраты по базовому варианту (Зб)", self.format_number(data['Z_b']), "руб/год"],
            ["Затраты при использовании ПО (Зп.п)", self.format_number(data['Z_pp']), "руб/год"],
            ["Экономическая эффективность (Э)", self.format_number(data['E']), "руб/год"],
            ["Срок окупаемости (Ток)", self.format_number(data['T_ok']) if data['T_ok'] != float('inf') else "∞", "лет"],
            ["Экономический эффект (Е)", self.format_number(data['E_eff']), "руб/год"],
        ]

        sales_per_month = self.sales_spin.value()
        price_per_copy = self.price_spin.value()
        monthly_revenue = sales_per_month * price_per_copy
        if monthly_revenue > 0:
            payback_months = data['Z_rp'] / monthly_revenue
            rows.append(["Окупаемость от продаж (мес.)", self.format_number(payback_months), "мес."])
            rows.append(["Продажи в месяц", str(sales_per_month), "шт."])
            rows.append(["Цена за копию", self.format_number(price_per_copy), "руб."])
        else:
            rows.append(["Окупаемость от продаж (мес.)", "∞", "мес."])

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV", "results.csv", "CSV файлы (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerows(rows)
            QMessageBox.information(self, "Готово", f"Сводная таблица сохранена в:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def export_charts_data_csv(self):
        """Экспорт данных, используемых для построения графиков, в CSV"""
        if not self.calculation_data:
            QMessageBox.information(self, "Нет данных", "Сначала выполните расчёт.")
            return

        data = self.calculation_data
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить данные графиков", "charts_data.csv", "CSV файлы (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                writer.writerow(["=== Структура затрат ==="])
                writer.writerow(["Статья затрат", "Сумма (руб.)", "Доля (%)"])
                Z_ot = data['Z_ot']
                Z_mv = data['Z_mv']
                Z_el = data['Z_el']
                Z_pr = data['Z_pr']
                total = Z_ot + Z_mv + Z_el + Z_pr
                if total > 0:
                    writer.writerow(["Заработная плата", self.format_number(Z_ot), f"{Z_ot/total*100:.1f}"])
                    writer.writerow(["Машинное время", self.format_number(Z_mv), f"{Z_mv/total*100:.1f}"])
                    writer.writerow(["Электроэнергия", self.format_number(Z_el), f"{Z_el/total*100:.1f}"])
                    writer.writerow(["Прочие затраты", self.format_number(Z_pr), f"{Z_pr/total*100:.1f}"])
                writer.writerow([])

                writer.writerow(["=== Точка безубыточности ==="])
                writer.writerow(["Параметр", "Значение"])
                writer.writerow(["Постоянные затраты (Зрп)", self.format_number(data['Z_rp'])])
                writer.writerow(["Цена за копию", self.format_number(self.price_spin.value())])
                writer.writerow(["Переменные затраты на единицу", "300.00"])
                price = self.price_spin.value()
                var_cost = 300.0
                if price > var_cost:
                    break_even = data['Z_rp'] / (price - var_cost)
                    writer.writerow(["Точка безубыточности (ед.)", self.format_number(break_even)])
                    sales = self.sales_spin.value()
                    if sales > 0:
                        writer.writerow(["Срок окупаемости (мес.)", self.format_number(break_even / sales)])
                else:
                    writer.writerow(["Точка безубыточности", "Не достигается"])
                writer.writerow([])

                writer.writerow(["=== Ежемесячные доходы и расходы ==="])
                writer.writerow(["Месяц", "Доход (руб.)", "Расход (руб.)"])
                months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                          'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
                E = data['E']
                monthly_saving = E / 12 if E > 0 else 0
                seasonal_factors = [0.7, 0.65, 0.8, 0.85, 0.9, 1.0,
                                    1.0, 0.95, 0.9, 1.0, 1.05, 1.1]
                monthly_income = [E / 12 * f for f in seasonal_factors]
                monthly_expenses = monthly_saving * 0.7 * np.array(seasonal_factors)
                for i, m in enumerate(months):
                    writer.writerow([m, self.format_number(monthly_income[i]), self.format_number(monthly_expenses[i])])
                writer.writerow([])

                writer.writerow(["=== Накопленный денежный поток ==="])
                writer.writerow(["Год", "Накопленный поток (руб.)"])
                years = range(0, 6)
                yearly_income = E
                cumulative = -data['Z_rp']
                for y in years:
                    cumulative += yearly_income
                    writer.writerow([str(y), self.format_number(cumulative)])

            QMessageBox.information(self, "Готово", f"Данные графиков сохранены в:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def calculate(self):
        try:
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

            if salary_share == 0:
                QMessageBox.warning(self, "Ошибка", "Доля зарплаты в смете не может быть равна нулю!")
                return
            if useful_life == 0:
                QMessageBox.warning(self, "Ошибка", "Срок полезного использования не может быть равен нулю!")
                return

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
            T_ok = self.safe_divide(R_total, E) if E > 0 else float('inf')
            E_eff = self.safe_divide(E, R_total) if R_total > 0 else 0

            self.calculation_data = {
                'Z_ot': Z_ot, 'Z_mv': Z_mv, 'Z_el': Z_el, 'Z_pr': Z_pr,
                'Z_rp': Z_rp, 'A': A, 'total_expenses': total_expenses,
                'E': E, 'E_eff': E_eff, 'T_ok': T_ok,
                'T_r': T_r, 'work_hours': work_hours,
                'T': T, 'Z_b': Z_b, 'Z_pp': Z_pp, 'R_total': R_total
            }

            def fmt(v):
                return self.format_number(v)

            def fmt_int(v):
                return self.format_number_no_decimals(v)

            def fmt_idx(text):
                return self.format_with_indices(text)

            # ----- текст для копирования -----
            lines = []
            lines.append("="*60)
            lines.append("РЕЗУЛЬТАТЫ РАСЧЁТА ЭКОНОМИЧЕСКОЙ ЭФФЕКТИВНОСТИ")
            lines.append("="*60)

            def add_to_copy(name, general, subst, value, unit=""):
                if value == float('inf'):
                    val_str = "∞ (деление на ноль)"
                else:
                    val_str = fmt(value)
                    if unit:
                        val_str += f" {unit}"
                lines.append(f"\n{name}")
                lines.append(f"  {general}")
                lines.append(f"  {subst}")
                lines.append(f"  Результат: {val_str}")
                lines.append("-"*40)

            add_to_copy("1. Общие трудозатраты",
                        "T = tu + ta + tn + toml + td",
                        f"T = {fmt(tu)} + {fmt(ta)} + {fmt(tn)} + {fmt(toml)} + {fmt(td)} = {fmt(T)}",
                        T, "чел-час")
            add_to_copy("2. Расходы на оплату труда и страховые взносы",
                        "Зот = T × Сч × кспр",
                        f"Зот = {fmt(T)} × {fmt(hourly)} × {fmt(insurance)} = {fmt(Z_ot)}",
                        Z_ot, "руб")
            add_to_copy("3. Затраты на машинное время",
                        "Змв = Смч × (tn + toml)",
                        f"Змв = {fmt(machine_hour)} × ({fmt(tn)} + {fmt(toml)}) = {fmt(Z_mv)}",
                        Z_mv, "руб")
            add_to_copy("4. Затраты на электроэнергию",
                        "Зэл = Цэл × Р × (tn + toml + td)",
                        f"Зэл = {fmt(electricity)} × {fmt(power)} × ({fmt(tn)} + {fmt(toml)} + {fmt(td)}) = {fmt(Z_el)}",
                        Z_el, "руб")
            add_to_copy("5. Прочие затраты",
                        "Зпр = 5% × (Зот + Змв + Зэл)",
                        f"Зпр = 0.05 × ({fmt(Z_ot)} + {fmt(Z_mv)} + {fmt(Z_el)}) = {fmt(Z_pr)}",
                        Z_pr, "руб")
            add_to_copy("6. Затраты на разработку",
                        "Зрп = Зот + Змв + Зэл + Зпр",
                        f"Зрп = {fmt(Z_ot)} + {fmt(Z_mv)} + {fmt(Z_el)} + {fmt(Z_pr)} = {fmt(Z_rp)}",
                        Z_rp, "руб")
            add_to_copy("7. Амортизация",
                        "Ад = (На × Зрп) / 100",
                        f"Ад = ({fmt(dep_rate)} × {fmt(Z_rp)}) / 100 = {fmt(A)}",
                        A, "руб/год")
            add_to_copy("8. Трудоёмкость задачи",
                        "Тр = Тп.к × Нтр / 100",
                        f"Тр = {fmt(work_hours)} × {fmt(labor_intensity)} / 100 = {fmt(T_r)}",
                        T_r, "час/год")
            add_to_copy("9. Затраты по базовому варианту",
                        "Зб = Сч × Тр × (1 / Дз.п)",
                        f"Зб = {fmt(hourly)} × {fmt(T_r)} × (1 / {fmt(salary_share)}) = {fmt(Z_b)}",
                        Z_b, "руб/год")
            add_to_copy("10. Затраты при использовании ПО",
                        "Зп.п = (Тг × См + Зобщ) / Тс, где Зобщ = Зрп + Ад",
                        f"Зп.п = ({fmt(work_hours)} × {fmt(machine_hour)} + {fmt(total_expenses)}) / {fmt_int(useful_life)} = {fmt(Z_pp)}",
                        Z_pp, "руб/год")
            add_to_copy("11. Экономическая эффективность",
                        "Э = Зб - Зп.п",
                        f"Э = {fmt(Z_b)} - {fmt(Z_pp)} = {fmt(E)}",
                        E, "руб/год")
            if T_ok != float('inf'):
                add_to_copy("12. Срок окупаемости",
                            "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                            f"Ток = {fmt(R_total)} / {fmt(E)} = {fmt(T_ok)}",
                            T_ok, "лет")
            else:
                add_to_copy("12. Срок окупаемости",
                            "Ток = Робщ / Э, где Робщ = Сбал + Зобщ",
                            f"Ток = {fmt(R_total)} / {fmt(E)} (Э ≤ 0)",
                            0, "лет")
            add_to_copy("13. Экономический эффект",
                        "Е = Э / Робщ",
                        f"Е = {fmt(E)} / {fmt(R_total)} = {fmt(E_eff)}",
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

            # ----- ВЫВОД В ИНТЕРФЕЙС -----
            self.clear_results()
            self.copy_btn.setVisible(True)
            self.export_btn.setVisible(True)
            self.export_charts_btn.setVisible(True)

            title = QLabel("<b>РЕЗУЛЬТАТЫ РАСЧЁТА</b>")
            title.setStyleSheet("font-size: 18px; color: #1f2a44; margin-bottom: 5px;")
            self.results_layout.addWidget(title)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            self.results_layout.addWidget(line)

            descriptions = {
                "1. Общие трудозатраты": "Суммарное время, затраченное на все этапы разработки.",
                "2. Расходы на оплату труда и страховые взносы": "Затраты на зарплату разработчика с учётом страховых взносов.",
                "3. Затраты на машинное время": "Стоимость работы ПК во время программирования и отладки.",
                "4. Затраты на электроэнергию": "Расходы на электроэнергию за время работы над программой.",
                "5. Прочие затраты": "Дополнительные расходы (5% от суммы основных затрат).",
                "6. Затраты на разработку": "Общая сумма всех затрат на создание ПО.",
                "7. Амортизация": "Годовые амортизационные отчисления от стоимости разработки.",
                "8. Трудоёмкость задачи": "Время, которое тратится на задачу в базовом варианте.",
                "9. Затраты по базовому варианту": "Годовые затраты при ручном (базовом) решении задачи.",
                "10. Затраты при использовании ПО": "Годовые затраты при использовании разработанного ПО.",
                "11. Экономическая эффективность": "Годовая экономия от внедрения ПО.",
                "12. Срок окупаемости": "Время, за которое окупаются затраты на разработку и внедрение.",
                "13. Экономический эффект": "Отношение годовой экономии к общим расходам (норматив > 0.33)."
            }

            def get_vars_list(var_names, values_map):
                result = []
                for name in var_names:
                    if name in values_map:
                        val = values_map[name]
                        if isinstance(val, float):
                            val_str = fmt(val)
                        else:
                            val_str = str(val)
                        desc = self.var_descriptions.get(name, "")
                        result.append((name, val_str, desc))
                return result

            all_vars = {
                'tu': tu, 'ta': ta, 'tn': tn, 'toml': toml, 'td': td,
                'T': T,
                'Сч': hourly,
                'кспр': insurance,
                'Смч': machine_hour,
                'Цэл': electricity,
                'Р': power,
                'Тп.к': work_hours,
                'Нтр': labor_intensity,
                'Дз.п': salary_share,
                'На': dep_rate,
                'Сбал': pc_cost,
                'Тс': useful_life,
                'Тг': work_hours,
                'См': machine_hour,
                'Зобщ': total_expenses,
                'Робщ': R_total,
                'Зот': Z_ot,
                'Змв': Z_mv,
                'Зэл': Z_el,
                'Зпр': Z_pr,
                'Зрп': Z_rp,
                'Ад': A,
                'Тр': T_r,
                'Зб': Z_b,
                'Зп.п': Z_pp,
                'Э': E,
                'Ток': T_ok if T_ok != float('inf') else None,
                'Е': E_eff,
            }

            def add_result(name, general_formula, formula_with_values, value, unit, var_names):
                group = ClickableGroupBox(name)
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

                general_label = self.create_formula_label(
                    general_formula,
                    "Нажмите Ctrl+A для выделения всей формулы, затем Ctrl+C для копирования"
                )
                layout.addWidget(general_label)

                values_label = self.create_formula_label(
                    formula_with_values,
                    "Нажмите Ctrl+A для выделения всей формулы, затем Ctrl+C для копирования"
                )
                layout.addWidget(values_label)

                if value == float('inf'):
                    result_text = "∞ (деление на ноль)"
                else:
                    result_text = f"{fmt(value)} {unit}" if unit else f"{fmt(value)}"

                result_label = self.create_formula_label(
                    result_text,
                    f"Результат: {result_text}",
                    is_result=True
                )
                layout.addWidget(result_label)

                group.clicked.connect(
                    lambda n=name, g=general_formula, s=formula_with_values, v=value, u=unit, vnames=var_names:
                    self.show_formula_details(
                        n, g, s, v, u,
                        get_vars_list(vnames, all_vars),
                        descriptions.get(n, "")
                    )
                )

                self.results_layout.addWidget(group)

            # Добавляем все блоки
            add_result(
                "1. Общие трудозатраты",
                fmt_idx("T = tu + ta + tn + toml + td"),
                fmt_idx(f"T = {fmt(tu)} + {fmt(ta)} + {fmt(tn)} + {fmt(toml)} + {fmt(td)} = {fmt(T)}"),
                T, "чел-час",
                ['tu', 'ta', 'tn', 'toml', 'td']
            )
            add_result(
                "2. Расходы на оплату труда и страховые взносы",
                fmt_idx("Зот = T × Сч × кспр"),
                fmt_idx(f"Зот = {fmt(T)} × {fmt(hourly)} × {fmt(insurance)} = {fmt(Z_ot)}"),
                Z_ot, "руб",
                ['T', 'Сч', 'кспр']
            )
            add_result(
                "3. Затраты на машинное время",
                fmt_idx("Змв = Смч × (tn + toml)"),
                fmt_idx(f"Змв = {fmt(machine_hour)} × ({fmt(tn)} + {fmt(toml)}) = {fmt(Z_mv)}"),
                Z_mv, "руб",
                ['Смч', 'tn', 'toml']
            )
            add_result(
                "4. Затраты на электроэнергию",
                fmt_idx("Зэл = Цэл × Р × (tn + toml + td)"),
                fmt_idx(f"Зэл = {fmt(electricity)} × {fmt(power)} × ({fmt(tn)} + {fmt(toml)} + {fmt(td)}) = {fmt(Z_el)}"),
                Z_el, "руб",
                ['Цэл', 'Р', 'tn', 'toml', 'td']
            )
            add_result(
                "5. Прочие затраты",
                fmt_idx("Зпр = 5% × (Зот + Змв + Зэл)"),
                fmt_idx(f"Зпр = 0.05 × ({fmt(Z_ot)} + {fmt(Z_mv)} + {fmt(Z_el)}) = {fmt(Z_pr)}"),
                Z_pr, "руб",
                ['Зот', 'Змв', 'Зэл']
            )
            add_result(
                "6. Затраты на разработку",
                fmt_idx("Зрп = Зот + Змв + Зэл + Зпр"),
                fmt_idx(f"Зрп = {fmt(Z_ot)} + {fmt(Z_mv)} + {fmt(Z_el)} + {fmt(Z_pr)} = {fmt(Z_rp)}"),
                Z_rp, "руб",
                ['Зот', 'Змв', 'Зэл', 'Зпр']
            )
            add_result(
                "7. Амортизация",
                fmt_idx("Ад = (На × Зрп) / 100"),
                fmt_idx(f"Ад = ({fmt(dep_rate)} × {fmt(Z_rp)}) / 100 = {fmt(A)}"),
                A, "руб/год",
                ['На', 'Зрп']
            )
            add_result(
                "8. Трудоёмкость задачи",
                fmt_idx("Тр = Тп.к × Нтр / 100"),
                fmt_idx(f"Тр = {fmt(work_hours)} × {fmt(labor_intensity)} / 100 = {fmt(T_r)}"),
                T_r, "час/год",
                ['Тп.к', 'Нтр']
            )
            add_result(
                "9. Затраты по базовому варианту",
                fmt_idx("Зб = Сч × Тр × (1 / Дз.п)"),
                fmt_idx(f"Зб = {fmt(hourly)} × {fmt(T_r)} × (1 / {fmt(salary_share)}) = {fmt(Z_b)}"),
                Z_b, "руб/год",
                ['Сч', 'Тр', 'Дз.п']
            )
            add_result(
                "10. Затраты при использовании ПО",
                fmt_idx("Зп.п = (Тг × См + Зобщ) / Тс, где Зобщ = Зрп + Ад"),
                fmt_idx(f"Зп.п = ({fmt(work_hours)} × {fmt(machine_hour)} + {fmt(total_expenses)}) / {fmt_int(useful_life)} = {fmt(Z_pp)}"),
                Z_pp, "руб/год",
                ['Тг', 'См', 'Зобщ', 'Тс', 'Зрп', 'Ад']
            )
            add_result(
                "11. Экономическая эффективность",
                fmt_idx("Э = Зб - Зп.п"),
                fmt_idx(f"Э = {fmt(Z_b)} - {fmt(Z_pp)} = {fmt(E)}"),
                E, "руб/год",
                ['Зб', 'Зп.п']
            )
            if T_ok != float('inf'):
                add_result(
                    "12. Срок окупаемости",
                    fmt_idx("Ток = Робщ / Э, где Робщ = Сбал + Зобщ"),
                    fmt_idx(f"Ток = {fmt(R_total)} / {fmt(E)} = {fmt(T_ok)}"),
                    T_ok, "лет",
                    ['Робщ', 'Э', 'Сбал', 'Зобщ']
                )
            else:
                add_result(
                    "12. Срок окупаемости",
                    fmt_idx("Ток = Робщ / Э, где Робщ = Сбал + Зобщ"),
                    fmt_idx(f"Ток = {fmt(R_total)} / {fmt(E)} (Э ≤ 0)"),
                    0, "лет",
                    ['Робщ', 'Э', 'Сбал', 'Зобщ']
                )
            add_result(
                "13. Экономический эффект",
                fmt_idx("Е = Э / Робщ"),
                fmt_idx(f"Е = {fmt(E)} / {fmt(R_total)} = {fmt(E_eff)}"),
                E_eff, "руб/год",
                ['Э', 'Робщ']
            )

            line2 = QFrame()
            line2.setFrameShape(QFrame.HLine)
            line2.setFrameShadow(QFrame.Sunken)
            self.results_layout.addWidget(line2)

            conclusion = QLabel()
            conclusion.setAlignment(Qt.AlignCenter)
            if E > 0 and T_ok < 3:
                conclusion.setText("РАЗРАБОТКА ЭКОНОМИЧЕСКИ ЦЕЛЕСООБРАЗНА")
                conclusion.setStyleSheet("background: #e2f0d9; color: #1e6b2e; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
            elif E > 0:
                conclusion.setText("РАЗРАБОТКА ЭКОНОМИЧЕСКИ ОПРАВДАНА, НО СРОК ОКУПАЕМОСТИ ВЫШЕ НОРМЫ")
                conclusion.setStyleSheet("background: #fff3cd; color: #856404; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
            else:
                conclusion.setText("РАЗРАБОТКА ЭКОНОМИЧЕСКИ НЕЦЕЛЕСООБРАЗНА")
                conclusion.setStyleSheet("background: #f8d7da; color: #721c24; font-size: 16px; font-weight: bold; border-radius: 10px; padding: 12px;")
            self.results_layout.addWidget(conclusion)

            info_label = QLabel("Для копирования отдельных формул выделите текст в поле выше и нажмите Ctrl+C")
            info_label.setStyleSheet("color: #6c757d; font-size: 10pt; font-style: italic; padding: 5px;")
            info_label.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(info_label)

            click_hint = QLabel("Кликните на любой блок с формулой для подробного просмотра")
            click_hint.setStyleSheet("color: #5b7cfa; font-size: 10pt; font-weight: bold; padding: 5px;")
            click_hint.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(click_hint)

            self.results_layout.addStretch()
            self.tabs.setCurrentIndex(1)

            self.draw_charts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при расчёте:\n{str(e)}")

    def clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


def main():
    app = QApplication(sys.argv)
    QLocale.setDefault(QLocale("ru_RU"))
    window = EconomicCalculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
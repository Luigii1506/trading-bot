from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QGroupBox, 
    QDateEdit, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QGridLayout, QSplitter
)
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from PyQt5.QtGui import QColor
import pandas as pd
import numpy as np
from datetime import datetime

class OptimizeTab(QWidget):
    """Pestaña para optimizar parámetros del bot"""
    run_optimization_signal = pyqtSignal(dict, str, str, float)
    apply_best_params_signal = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.optimization_results = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        main_layout = QVBoxLayout()
        
        # Configuración de la optimización
        config_group = QGroupBox("Configuración de la Optimización")
        config_layout = QVBoxLayout()
        
        # Período de tiempo para optimización
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Período de Optimización:"))
        
        date_form = QFormLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-6))
        date_form.addRow("Fecha Inicio:", self.start_date_edit)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_form.addRow("Fecha Fin:", self.end_date_edit)
        
        self.initial_capital_spin = QDoubleSpinBox()
        self.initial_capital_spin.setRange(100, 1000000)
        self.initial_capital_spin.setValue(1000)
        self.initial_capital_spin.setSingleStep(100)
        date_form.addRow("Capital Inicial ($):", self.initial_capital_spin)
        
        date_layout.addLayout(date_form)
        config_layout.addLayout(date_layout)
        
        # Grid de parámetros a optimizar
        params_group = QGroupBox("Parámetros a Optimizar")
        params_layout = QGridLayout()
        
        # Columna 1: Medias Móviles
        col1_layout = QFormLayout()
        
        # Checkbox para incluir parámetro en optimización
        self.fast_ma_check = QCheckBox("Fast MA")
        self.fast_ma_check.setChecked(True)
        col1_layout.addRow(self.fast_ma_check)
        
        # Valores a probar
        self.fast_ma_min = QSpinBox()
        self.fast_ma_min.setRange(5, 50)
        self.fast_ma_min.setValue(10)
        col1_layout.addRow("Min:", self.fast_ma_min)
        
        self.fast_ma_max = QSpinBox()
        self.fast_ma_max.setRange(10, 100)
        self.fast_ma_max.setValue(30)
        col1_layout.addRow("Max:", self.fast_ma_max)
        
        self.fast_ma_step = QSpinBox()
        self.fast_ma_step.setRange(1, 10)
        self.fast_ma_step.setValue(5)
        col1_layout.addRow("Step:", self.fast_ma_step)
        
        # Slow MA
        self.slow_ma_check = QCheckBox("Slow MA")
        self.slow_ma_check.setChecked(True)
        col1_layout.addRow(self.slow_ma_check)
        
        self.slow_ma_min = QSpinBox()
        self.slow_ma_min.setRange(20, 100)
        self.slow_ma_min.setValue(40)
        col1_layout.addRow("Min:", self.slow_ma_min)
        
        self.slow_ma_max = QSpinBox()
        self.slow_ma_max.setRange(50, 200)
        self.slow_ma_max.setValue(60)
        col1_layout.addRow("Max:", self.slow_ma_max)
        
        self.slow_ma_step = QSpinBox()
        self.slow_ma_step.setRange(1, 20)
        self.slow_ma_step.setValue(10)
        col1_layout.addRow("Step:", self.slow_ma_step)
        
        params_layout.addLayout(col1_layout, 0, 0)
        
        # Columna 2: RSI
        col2_layout = QFormLayout()
        
        # RSI Período
        self.rsi_period_check = QCheckBox("RSI Período")
        self.rsi_period_check.setChecked(True)
        col2_layout.addRow(self.rsi_period_check)
        
        self.rsi_period_min = QSpinBox()
        self.rsi_period_min.setRange(3, 20)
        self.rsi_period_min.setValue(7)
        col2_layout.addRow("Min:", self.rsi_period_min)
        
        self.rsi_period_max = QSpinBox()
        self.rsi_period_max.setRange(10, 30)
        self.rsi_period_max.setValue(21)
        col2_layout.addRow("Max:", self.rsi_period_max)
        
        self.rsi_period_step = QSpinBox()
        self.rsi_period_step.setRange(1, 5)
        self.rsi_period_step.setValue(7)
        col2_layout.addRow("Step:", self.rsi_period_step)
        
        # RSI Sobrecompra
        self.rsi_overbought_check = QCheckBox("RSI Sobrecompra")
        self.rsi_overbought_check.setChecked(True)
        col2_layout.addRow(self.rsi_overbought_check)
        
        self.rsi_overbought_min = QSpinBox()
        self.rsi_overbought_min.setRange(60, 80)
        self.rsi_overbought_min.setValue(70)
        col2_layout.addRow("Min:", self.rsi_overbought_min)
        
        self.rsi_overbought_max = QSpinBox()
        self.rsi_overbought_max.setRange(70, 90)
        self.rsi_overbought_max.setValue(80)
        col2_layout.addRow("Max:", self.rsi_overbought_max)
        
        self.rsi_overbought_step = QSpinBox()
        self.rsi_overbought_step.setRange(1, 5)
        self.rsi_overbought_step.setValue(5)
        col2_layout.addRow("Step:", self.rsi_overbought_step)
        
        params_layout.addLayout(col2_layout, 0, 1)
        
        # Columna 3: Más parámetros RSI y BB
        col3_layout = QFormLayout()
        
        # RSI Sobreventa
        self.rsi_oversold_check = QCheckBox("RSI Sobreventa")
        self.rsi_oversold_check.setChecked(True)
        col3_layout.addRow(self.rsi_oversold_check)
        
        self.rsi_oversold_min = QSpinBox()
        self.rsi_oversold_min.setRange(10, 30)
        self.rsi_oversold_min.setValue(20)
        col3_layout.addRow("Min:", self.rsi_oversold_min)
        
        self.rsi_oversold_max = QSpinBox()
        self.rsi_oversold_max.setRange(20, 40)
        self.rsi_oversold_max.setValue(30)
        col3_layout.addRow("Max:", self.rsi_oversold_max)
        
        self.rsi_oversold_step = QSpinBox()
        self.rsi_oversold_step.setRange(1, 5)
        self.rsi_oversold_step.setValue(5)
        col3_layout.addRow("Step:", self.rsi_oversold_step)
        
        # Bandas de Bollinger Período
        self.bb_period_check = QCheckBox("BB Período")
        self.bb_period_check.setChecked(False)
        col3_layout.addRow(self.bb_period_check)
        
        self.bb_period_min = QSpinBox()
        self.bb_period_min.setRange(5, 30)
        self.bb_period_min.setValue(15)
        col3_layout.addRow("Min:", self.bb_period_min)
        
        self.bb_period_max = QSpinBox()
        self.bb_period_max.setRange(15, 50)
        self.bb_period_max.setValue(25)
        col3_layout.addRow("Max:", self.bb_period_max)
        
        self.bb_period_step = QSpinBox()
        self.bb_period_step.setRange(1, 5)
        self.bb_period_step.setValue(5)
        col3_layout.addRow("Step:", self.bb_period_step)
        
        params_layout.addLayout(col3_layout, 0, 2)
        
        params_group.setLayout(params_layout)
        config_layout.addWidget(params_group)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Iniciar Optimización")
        self.run_button.clicked.connect(self.run_optimization)
        buttons_layout.addWidget(self.run_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        buttons_layout.addWidget(self.progress_bar)
        
        config_layout.addLayout(buttons_layout)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Tabla de resultados
        results_group = QGroupBox("Resultados de la Optimización")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)  # Parámetros + métricas
        self.results_table.setHorizontalHeaderLabels([
            "Fast MA", "Slow MA", "RSI Period", "RSI Overbought", 
            "RSI Oversold", "Retorno %", "Win Rate %", "Max Drawdown %"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        results_layout.addWidget(self.results_table)
        
        # Botón para aplicar los mejores parámetros
        apply_layout = QHBoxLayout()
        self.apply_button = QPushButton("Aplicar Mejores Parámetros")
        self.apply_button.clicked.connect(self.apply_best_params)
        self.apply_button.setEnabled(False)
        apply_layout.addWidget(self.apply_button)
        
        results_layout.addLayout(apply_layout)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        self.setLayout(main_layout)
    
    def run_optimization(self):
        """Inicia el proceso de optimización"""
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.apply_button.setEnabled(False)
        
        # Construir el grid de parámetros
        param_grid = {}
        
        # Fast MA
        if self.fast_ma_check.isChecked():
            param_grid['fast_ma'] = list(range(
                self.fast_ma_min.value(),
                self.fast_ma_max.value() + 1,
                self.fast_ma_step.value()
            ))
        
        # Slow MA
        if self.slow_ma_check.isChecked():
            param_grid['slow_ma'] = list(range(
                self.slow_ma_min.value(),
                self.slow_ma_max.value() + 1,
                self.slow_ma_step.value()
            ))
        
        # RSI Period
        if self.rsi_period_check.isChecked():
            param_grid['rsi_period'] = list(range(
                self.rsi_period_min.value(),
                self.rsi_period_max.value() + 1,
                self.rsi_period_step.value()
            ))
        
        # RSI Overbought
        if self.rsi_overbought_check.isChecked():
            param_grid['rsi_overbought'] = list(range(
                self.rsi_overbought_min.value(),
                self.rsi_overbought_max.value() + 1,
                self.rsi_overbought_step.value()
            ))
        
        # RSI Oversold
        if self.rsi_oversold_check.isChecked():
            param_grid['rsi_oversold'] = list(range(
                self.rsi_oversold_min.value(),
                self.rsi_oversold_max.value() + 1,
                self.rsi_oversold_step.value()
            ))
        
        # BB Period
        if self.bb_period_check.isChecked():
            param_grid['bb_period'] = list(range(
                self.bb_period_min.value(),
                self.bb_period_max.value() + 1,
                self.bb_period_step.value()
            ))
        
        # Verificar que haya al menos un parámetro seleccionado
        if not param_grid:
            self.run_button.setEnabled(True)
            return
        
        # Obtener fechas y capital inicial
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        initial_capital = self.initial_capital_spin.value()
        
        # Emitir señal para iniciar optimización
        self.run_optimization_signal.emit(param_grid, start_date, end_date, initial_capital)
    
    def update_progress(self, current, total):
        """Actualiza la barra de progreso"""
        progress = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
    
    def display_optimization_results(self, best_params, results_df):
        """Muestra los resultados de la optimización"""
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(100)
        
        self.optimization_results = results_df
        self.best_params = best_params
        
        if best_params:
            self.apply_button.setEnabled(True)
        
        # Mostrar resultados en la tabla
        if results_df is not None and not results_df.empty:
            # Llenar tabla de resultados
            self.results_table.setRowCount(len(results_df))
            
            for i, (_, row) in enumerate(results_df.iterrows()):
                params = row['params']
                
                # Columnas de parámetros
                col = 0
                for param_name in ['fast_ma', 'slow_ma', 'rsi_period', 'rsi_overbought', 'rsi_oversold']:
                    if param_name in params:
                        self.results_table.setItem(i, col, QTableWidgetItem(str(params[param_name])))
                    else:
                        self.results_table.setItem(i, col, QTableWidgetItem("-"))
                    col += 1
                
                # Columnas de métricas
                self.results_table.setItem(i, 5, QTableWidgetItem(f"{row['return']:.2f}"))
                self.results_table.setItem(i, 6, QTableWidgetItem(f"{row['win_rate']:.2f}"))
                self.results_table.setItem(i, 7, QTableWidgetItem(f"{row.get('max_drawdown', 0):.2f}"))
                
                # Resaltar la mejor combinación
                is_best = True
                for param_name, value in best_params.items():
                    if param_name in params and params[param_name] != value:
                        is_best = False
                        break
                
                if is_best:
                    for col in range(self.results_table.columnCount()):
                        item = self.results_table.item(i, col)
                        if item:
                            item.setBackground(QColor(200, 255, 200))  # Verde claro
            
            # Ordenar tabla por retorno (columna 5) en orden descendente
            self.results_table.sortItems(5, Qt.DescendingOrder)
    
    def apply_best_params(self):
        """Aplica los mejores parámetros encontrados"""
        if hasattr(self, 'best_params') and self.best_params:
            self.apply_best_params_signal.emit(self.best_params)
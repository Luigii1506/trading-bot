from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QDoubleSpinBox, QPushButton, QGroupBox, 
    QDateEdit, QComboBox, QProgressBar, QTextEdit,
    QSplitter, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from PyQt5.QtGui import QFont
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from trading_bot import generate_date_ranges, create_summary_stats, embed_matplotlib_plot

class BacktestTab(QWidget):
    """Pestaña para realizar y visualizar backtesting"""
    run_backtest_signal = pyqtSignal(str, str, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.backtest_results = None
        self.backtest_df = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        main_layout = QVBoxLayout()
        
        # Panel superior - Configuración de backtest
        config_group = QGroupBox("Configuración de Backtest")
        config_layout = QHBoxLayout()
        
        # Formulario de fechas
        date_form = QFormLayout()
        
        # Selector de rango predefinido
        self.range_combo = QComboBox()
        date_ranges = generate_date_ranges()
        self.range_combo.addItems(date_ranges.keys())
        self.range_combo.currentTextChanged.connect(self.update_date_range)
        date_form.addRow("Rango:", self.range_combo)
        
        # Fecha de inicio
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-3))
        date_form.addRow("Fecha Inicio:", self.start_date_edit)
        
        # Fecha de fin
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_form.addRow("Fecha Fin:", self.end_date_edit)
        
        config_layout.addLayout(date_form)
        
        # Formulario de capital inicial
        capital_form = QFormLayout()
        
        # Capital inicial
        self.initial_capital_spin = QDoubleSpinBox()
        self.initial_capital_spin.setRange(100, 1000000)
        self.initial_capital_spin.setValue(1000)
        self.initial_capital_spin.setSingleStep(100)
        capital_form.addRow("Capital Inicial ($):", self.initial_capital_spin)
        
        config_layout.addLayout(capital_form)
        
        # Botón de ejecución
        run_layout = QVBoxLayout()
        self.run_button = QPushButton("Ejecutar Backtest")
        self.run_button.clicked.connect(self.run_backtest)
        run_layout.addWidget(self.run_button)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        run_layout.addWidget(self.progress_bar)
        
        config_layout.addLayout(run_layout)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Panel de resultados - Dividido en pestañas
        results_tabs = QTabWidget()
        
        # Pestaña de resumen
        summary_tab = QWidget()
        summary_layout = QHBoxLayout()
        
        # Panel de estadísticas
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        font = QFont("Courier")
        self.stats_text.setFont(font)
        summary_layout.addWidget(self.stats_text, 1)
        
        # Panel de gráfico de equity
        self.equity_layout = QVBoxLayout()
        equity_widget = QWidget()
        equity_widget.setLayout(self.equity_layout)
        summary_layout.addWidget(equity_widget, 2)
        
        summary_tab.setLayout(summary_layout)
        results_tabs.addTab(summary_tab, "Resumen")
        
        # Pestaña de gráfico de precios
        price_tab = QWidget()
        self.price_layout = QVBoxLayout()
        price_tab.setLayout(self.price_layout)
        results_tabs.addTab(price_tab, "Gráfico de Precios")
        
        # Pestaña de operaciones
        trades_tab = QWidget()
        trades_layout = QVBoxLayout()
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            "Entrada", "Salida", "Precio Entrada", "Precio Salida", "Ganancia %", "Balance"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        trades_layout.addWidget(self.trades_table)
        
        trades_tab.setLayout(trades_layout)
        results_tabs.addTab(trades_tab, "Operaciones")
        
        # Pestaña de métricas
        metrics_tab = QWidget()
        metrics_layout = QVBoxLayout()
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setRowCount(7)
        self.metrics_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        metrics = [
            "Retorno Total (%)",
            "Retorno Anualizado (%)",
            "Volatilidad (%)",
            "Ratio de Sharpe",
            "Máximo Drawdown (%)",
            "Ratio de Calmar",
            "Días de Trading"
        ]
        
        for i, metric in enumerate(metrics):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem("-"))
        
        metrics_layout.addWidget(self.metrics_table)
        metrics_tab.setLayout(metrics_layout)
        results_tabs.addTab(metrics_tab, "Métricas")
        
        # Pestaña de drawdown
        drawdown_tab = QWidget()
        self.drawdown_layout = QVBoxLayout()
        drawdown_tab.setLayout(self.drawdown_layout)
        results_tabs.addTab(drawdown_tab, "Drawdown")
        
        main_layout.addWidget(results_tabs)
        
        self.setLayout(main_layout)
    
    def update_date_range(self, range_text):
        """Actualiza el rango de fechas según la selección predefinida"""
        date_ranges = generate_date_ranges()
        if range_text in date_ranges:
            start_date, end_date = date_ranges[range_text]
            
            if range_text != "Personalizado":
                # Convertir a QDate y establecer los campos
                if start_date:
                    qstart_date = QDate(start_date.year, start_date.month, start_date.day)
                    self.start_date_edit.setDate(qstart_date)
                
                if end_date:
                    qend_date = QDate(end_date.year, end_date.month, end_date.day)
                    self.end_date_edit.setDate(qend_date)
    
    def run_backtest(self):
        """Inicia el proceso de backtesting"""
        # Deshabilitar botón mientras se ejecuta
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Obtener parámetros
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        initial_capital = self.initial_capital_spin.value()
        
        # Emitir señal para ejecutar backtest
        self.run_backtest_signal.emit(start_date, end_date, initial_capital)
    
    def update_progress(self, current, total):
        """Actualiza la barra de progreso"""
        progress = int(current / total * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
    
    def display_backtest_results(self, results, df):
        """Muestra los resultados del backtest"""
        self.backtest_results = results
        self.backtest_df = df
        
        # Habilitar botón de nuevo
        self.run_button.setEnabled(True)
        self.progress_bar.setValue(100)
        
        if not results:
            self.stats_text.setText("No se encontraron resultados para el período seleccionado.")
            return
        
        # Actualizar estadísticas
        stats_text = create_summary_stats(results)
        self.stats_text.setText(stats_text)
        
        # Actualizar tablas de operaciones
        self.update_trades_table(results.get('trades'))
        
        # Actualizar métricas
        self.update_metrics_table(results)
        
        # Actualizar gráficos
        self.update_equity_chart(results)
        self.update_price_chart(df, results)
        self.update_drawdown_chart(results)
    
    def update_trades_table(self, trades_df):
        """Actualiza la tabla de operaciones"""
        if trades_df is None or trades_df.empty:
            self.trades_table.setRowCount(0)
            return
        
        self.trades_table.setRowCount(len(trades_df))
        
        for i, (_, trade) in enumerate(trades_df.iterrows()):
            # Formatear fechas
            entry_date = trade['entry_date']
            exit_date = trade['exit_date']
            
            if isinstance(entry_date, pd.Timestamp):
                entry_date = entry_date.strftime("%Y-%m-%d %H:%M")
            
            if isinstance(exit_date, pd.Timestamp):
                exit_date = exit_date.strftime("%Y-%m-%d %H:%M")
            
            # Agregar a la tabla
            self.trades_table.setItem(i, 0, QTableWidgetItem(str(entry_date)))
            self.trades_table.setItem(i, 1, QTableWidgetItem(str(exit_date)))
            self.trades_table.setItem(i, 2, QTableWidgetItem(f"{trade['entry_price']:.2f}"))
            self.trades_table.setItem(i, 3, QTableWidgetItem(f"{trade['exit_price']:.2f}"))
            self.trades_table.setItem(i, 4, QTableWidgetItem(f"{trade['profit_pct']:.2f}%"))
            self.trades_table.setItem(i, 5, QTableWidgetItem(f"{trade['balance']:.2f}"))
            
            # Colorear celdas según ganancia/pérdida
            profit_item = self.trades_table.item(i, 4)
            if trade['profit_pct'] > 0:
                profit_item.setBackground(Qt.green)
            else:
                profit_item.setBackground(Qt.red)
    
    def update_metrics_table(self, results):
        """Actualiza la tabla de métricas de rendimiento"""
        if 'equity_curve' in results and not results['equity_curve'].empty:
            from trading_bot import get_performance_metrics
            
            metrics = get_performance_metrics(results['equity_curve'], results['initial_balance'])
            
            # Actualizar tabla
            self.metrics_table.setItem(0, 1, QTableWidgetItem(f"{metrics['total_return']:.2f}%"))
            self.metrics_table.setItem(1, 1, QTableWidgetItem(f"{metrics['annual_return']:.2f}%"))
            self.metrics_table.setItem(2, 1, QTableWidgetItem(f"{metrics['volatility']:.2f}%"))
            self.metrics_table.setItem(3, 1, QTableWidgetItem(f"{metrics['sharpe_ratio']:.2f}"))
            self.metrics_table.setItem(4, 1, QTableWidgetItem(f"{metrics['max_drawdown']:.2f}%"))
            self.metrics_table.setItem(5, 1, QTableWidgetItem(f"{metrics['calmar_ratio']:.2f}"))
            self.metrics_table.setItem(6, 1, QTableWidgetItem(f"{metrics['trading_days']}"))
    
    def update_equity_chart(self, results):
        """Actualiza el gráfico de la curva de equity"""
        if 'equity_curve' not in results or results['equity_curve'].empty:
            return
        
        from trading_bot import plot_equity_curve
        
        # Crear figura
        fig = plot_equity_curve(
            results['equity_curve'], 
            f"Equity Curve (Retorno: {results['total_return_pct']:.2f}%)"
        )
        
        # Mostrar en el layout
        embed_matplotlib_plot(self.equity_layout, fig)
    
    def update_price_chart(self, df, results):
        """Actualiza el gráfico de precios"""
        if df is None or df.empty:
            return
        
        # Crear figura
        fig = Figure(figsize=(12, 8))
        ax1 = fig.add_subplot(311)  # Precios
        ax2 = fig.add_subplot(312)  # RSI
        ax3 = fig.add_subplot(313)  # Señales
        
        # Graficar precios
        ax1.plot(df.index, df['close'], label='Precio')
        ax1.plot(df.index, df['ma_fast'], label=f'MA Rápida')
        ax1.plot(df.index, df['ma_slow'], label=f'MA Lenta')
        ax1.fill_between(df.index, df['bb_upper'], df['bb_lower'], alpha=0.2, color='gray')
        
        # Marcar operaciones
        if 'trades' in results and not results['trades'].empty:
            for _, trade in results['trades'].iterrows():
                entry_date = trade['entry_date']
                exit_date = trade['exit_date']
                
                if isinstance(entry_date, pd.Timestamp) and entry_date in df.index:
                    ax1.scatter(entry_date, trade['entry_price'], color='green', marker='^', s=100)
                
                if isinstance(exit_date, pd.Timestamp) and exit_date in df.index:
                    ax1.scatter(exit_date, trade['exit_price'], color='red', marker='v', s=100)
        
        ax1.set_title('Precio y Señales')
        ax1.legend()
        ax1.grid(True)
        
        # Graficar RSI
        ax2.plot(df.index, df['rsi'], label='RSI')
        ax2.axhline(y=70, color='r', linestyle='--')
        ax2.axhline(y=30, color='g', linestyle='--')
        ax2.set_title('RSI')
        ax2.legend()
        ax2.grid(True)
        
        # Graficar señales
        ax3.plot(df.index, df['signal'], label='Señal')
        ax3.axhline(y=0, color='k', linestyle='--')
        ax3.set_title('Señales de Trading')
        ax3.legend()
        ax3.grid(True)
        
        fig.tight_layout()
        
        # Mostrar en el layout
        embed_matplotlib_plot(self.price_layout, fig)
    
    def update_drawdown_chart(self, results):
        """Actualiza el gráfico de drawdown"""
        if 'drawdown' not in results or results['drawdown'].empty:
            return
        
        from trading_bot import plot_drawdown_chart
        
        # Crear figura
        fig = plot_drawdown_chart(
            results['drawdown'], 
            f"Drawdown (Máximo: {results['max_drawdown']:.2f}%)"
        )
        
        # Mostrar en el layout
        embed_matplotlib_plot(self.drawdown_layout, fig)
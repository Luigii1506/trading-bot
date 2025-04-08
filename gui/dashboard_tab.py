from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QComboBox, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading_bot import embed_matplotlib_plot, format_price

class DashboardTab(QWidget):
    """Pestaña de panel de control para visualizar estadísticas generales"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trades_history = []  # Historial de operaciones
        self.equity_history = []  # Historial de equity
        self.dates = []           # Fechas para el historial
        self.init_ui()
        
        # Actualizar cada 5 segundos
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(5000)
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        main_layout = QVBoxLayout()
        
        # Panel superior con resumen
        summary_group = QGroupBox("Resumen de Trading")
        summary_layout = QHBoxLayout()
        
        # Métricas clave (izquierda)
        metrics_layout = QFormLayout()
        
        self.balance_label = QLabel("$1,000.00")
        self.balance_label.setFont(QFont("Arial", 14, QFont.Bold))
        metrics_layout.addRow("Balance:", self.balance_label)
        
        self.pl_day_label = QLabel("+$0.00 (0.00%)")
        metrics_layout.addRow("P&L del día:", self.pl_day_label)
        
        self.pl_total_label = QLabel("+$0.00 (0.00%)")
        metrics_layout.addRow("P&L total:", self.pl_total_label)
        
        self.win_rate_label = QLabel("0.00%")
        metrics_layout.addRow("Tasa de Victoria:", self.win_rate_label)
        
        summary_layout.addLayout(metrics_layout)
        
        # Estadísticas adicionales (centro)
        stats_layout = QFormLayout()
        
        self.trades_count_label = QLabel("0")
        stats_layout.addRow("Total Operaciones:", self.trades_count_label)
        
        self.win_trades_label = QLabel("0")
        stats_layout.addRow("Operaciones Ganadoras:", self.win_trades_label)
        
        self.lose_trades_label = QLabel("0")
        stats_layout.addRow("Operaciones Perdedoras:", self.lose_trades_label)
        
        self.avg_profit_label = QLabel("$0.00 (0.00%)")
        stats_layout.addRow("Ganancia Promedio:", self.avg_profit_label)
        
        summary_layout.addLayout(stats_layout)
        
        # Selector de períodos (derecha)
        period_layout = QVBoxLayout()
        
        period_label = QLabel("Período de Análisis:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Hoy", "Últimos 7 días", "Último mes", "Últimos 3 meses", "Todo"])
        self.period_combo.currentIndexChanged.connect(self.change_period)
        
        self.refresh_button = QPushButton("🔄 Actualizar")
        self.refresh_button.clicked.connect(self.update_dashboard)
        
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)
        period_layout.addWidget(self.refresh_button)
        period_layout.addStretch()
        
        summary_layout.addLayout(period_layout)
        
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        # Panel inferior dividido
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Gráfico de equity
        equity_widget = QWidget()
        equity_layout = QVBoxLayout(equity_widget)
        
        equity_group = QGroupBox("Curva de Equity")
        self.equity_chart_layout = QVBoxLayout()
        equity_group.setLayout(self.equity_chart_layout)
        equity_layout.addWidget(equity_group)
        
        main_splitter.addWidget(equity_widget)
        
        # Panel derecho: Tabla de operaciones
        trades_widget = QWidget()
        trades_layout = QVBoxLayout(trades_widget)
        
        trades_group = QGroupBox("Historial de Operaciones")
        trades_table_layout = QVBoxLayout()
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(7)
        self.trades_table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Precio Entrada", "Precio Salida", "Tamaño", "P&L", "P&L %"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        trades_table_layout.addWidget(self.trades_table)
        trades_group.setLayout(trades_table_layout)
        trades_layout.addWidget(trades_group)
        
        main_splitter.addWidget(trades_widget)
        
        # Establecer proporciones relativas de los paneles
        main_splitter.setSizes([600, 400])
        
        main_layout.addWidget(main_splitter)
        
        self.setLayout(main_layout)
        
        # Inicializar gráficos vacíos
        self.init_equity_chart()
    
    def init_equity_chart(self):
        """Inicializa el gráfico de equity"""
        fig = Figure(figsize=(10, 5))
        ax = fig.add_subplot(111)
        ax.set_title('Curva de Equity')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Balance ($)')
        ax.grid(True)
        
        # Crear línea vacía para actualizar después
        self.equity_line, = ax.plot([], [], 'b-', linewidth=2)
        
        fig.tight_layout()
        
        # Embeber el gráfico en la interfaz
        embed_matplotlib_plot(self.equity_chart_layout, fig)
        
        self.equity_fig = fig
        self.equity_ax = ax
    
    def update_dashboard(self):
        """Actualiza toda la información del dashboard"""
        # En una aplicación real, aquí se obtendría la información de la base de datos
        # Para este ejemplo, generaremos datos de muestra
        self.generate_sample_data()
        
        # Actualizar etiquetas de resumen
        current_balance = 1000
        if self.equity_history:
            current_balance = self.equity_history[-1]
        
        self.balance_label.setText(f"${current_balance:.2f}")
        
        # Calcular P&L del día
        if len(self.equity_history) > 1:
            day_start = current_balance - sum([t['pl_amount'] for t in self.trades_history if t['is_today']])
            day_pl = current_balance - day_start
            day_pl_pct = (day_pl / day_start) * 100 if day_start > 0 else 0
            
            pl_text = f"{'+' if day_pl >= 0 else ''}{day_pl:.2f} ({'+' if day_pl_pct >= 0 else ''}{day_pl_pct:.2f}%)"
            self.pl_day_label.setText(pl_text)
            
            if day_pl >= 0:
                self.pl_day_label.setStyleSheet("color: green;")
            else:
                self.pl_day_label.setStyleSheet("color: red;")
        
        # Calcular P&L total
        initial_balance = 1000  # Balance inicial supuesto
        total_pl = current_balance - initial_balance
        total_pl_pct = (total_pl / initial_balance) * 100
        
        pl_total_text = f"{'+' if total_pl >= 0 else ''}{total_pl:.2f} ({'+' if total_pl_pct >= 0 else ''}{total_pl_pct:.2f}%)"
        self.pl_total_label.setText(pl_total_text)
        
        if total_pl >= 0:
            self.pl_total_label.setStyleSheet("color: green;")
        else:
            self.pl_total_label.setStyleSheet("color: red;")
        
        # Estadísticas de operaciones
        total_trades = len(self.trades_history)
        win_trades = len([t for t in self.trades_history if t['pl_pct'] > 0])
        lose_trades = len([t for t in self.trades_history if t['pl_pct'] <= 0])
        
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
        
        self.trades_count_label.setText(str(total_trades))
        self.win_trades_label.setText(str(win_trades))
        self.lose_trades_label.setText(str(lose_trades))
        self.win_rate_label.setText(f"{win_rate:.2f}%")
        
        # Ganancia promedio
        if total_trades > 0:
            avg_profit_amount = sum([t['pl_amount'] for t in self.trades_history]) / total_trades
            avg_profit_pct = sum([t['pl_pct'] for t in self.trades_history]) / total_trades
            
            avg_profit_text = f"{'+' if avg_profit_amount >= 0 else ''}{avg_profit_amount:.2f} ({'+' if avg_profit_pct >= 0 else ''}{avg_profit_pct:.2f}%)"
            self.avg_profit_label.setText(avg_profit_text)
            
            if avg_profit_amount >= 0:
                self.avg_profit_label.setStyleSheet("color: green;")
            else:
                self.avg_profit_label.setStyleSheet("color: red;")
        
        # Actualizar tabla de operaciones
        self.update_trades_table()
        
        # Actualizar gráfico de equity
        self.update_equity_chart()
    
    def update_trades_table(self):
        """Actualiza la tabla de operaciones"""
        # Limpiar tabla
        self.trades_table.setRowCount(0)
        
        # Ordenar operaciones por fecha (más reciente primero)
        sorted_trades = sorted(self.trades_history, key=lambda x: x['date'], reverse=True)
        
        # Filtrar por período seleccionado
        period = self.period_combo.currentText()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == "Hoy":
            filtered_trades = [t for t in sorted_trades if t['date'] >= today]
        elif period == "Últimos 7 días":
            filtered_trades = [t for t in sorted_trades if t['date'] >= today - timedelta(days=7)]
        elif period == "Último mes":
            filtered_trades = [t for t in sorted_trades if t['date'] >= today - timedelta(days=30)]
        elif period == "Últimos 3 meses":
            filtered_trades = [t for t in sorted_trades if t['date'] >= today - timedelta(days=90)]
        else:  # "Todo"
            filtered_trades = sorted_trades
        
        # Llenar tabla
        for i, trade in enumerate(filtered_trades):
            self.trades_table.insertRow(i)
            
            # Fecha
            date_str = trade['date'].strftime("%Y-%m-%d %H:%M")
            self.trades_table.setItem(i, 0, QTableWidgetItem(date_str))
            
            # Tipo
            type_item = QTableWidgetItem(trade['type'].upper())
            if trade['type'] == 'buy':
                type_item.setBackground(QColor(200, 255, 200))  # Verde claro
            else:
                type_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            self.trades_table.setItem(i, 1, type_item)
            
            # Precio Entrada
            self.trades_table.setItem(i, 2, QTableWidgetItem(format_price(trade['entry_price'])))
            
            # Precio Salida
            self.trades_table.setItem(i, 3, QTableWidgetItem(format_price(trade['exit_price'])))
            
            # Tamaño
            self.trades_table.setItem(i, 4, QTableWidgetItem(f"{trade['size']:.6f}"))
            
            # P&L
            pl_item = QTableWidgetItem(f"{'+' if trade['pl_amount'] >= 0 else ''}{trade['pl_amount']:.2f}")
            if trade['pl_amount'] > 0:
                pl_item.setForeground(QColor("green"))
            elif trade['pl_amount'] < 0:
                pl_item.setForeground(QColor("red"))
            self.trades_table.setItem(i, 5, pl_item)
            
            # P&L %
            pl_pct_item = QTableWidgetItem(f"{'+' if trade['pl_pct'] >= 0 else ''}{trade['pl_pct']:.2f}%")
            if trade['pl_pct'] > 0:
                pl_pct_item.setForeground(QColor("green"))
            elif trade['pl_pct'] < 0:
                pl_pct_item.setForeground(QColor("red"))
            self.trades_table.setItem(i, 6, pl_pct_item)
    
    def update_equity_chart(self):
        """Actualiza el gráfico de la curva de equity"""
        if not self.dates or not self.equity_history:
            return
        
        # Filtrar por período seleccionado
        period = self.period_combo.currentText()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == "Hoy":
            start_date = today
        elif period == "Últimos 7 días":
            start_date = today - timedelta(days=7)
        elif period == "Último mes":
            start_date = today - timedelta(days=30)
        elif period == "Últimos 3 meses":
            start_date = today - timedelta(days=90)
        else:  # "Todo"
            start_date = min(self.dates)
        
        # Filtrar datos
        filtered_dates = []
        filtered_equity = []
        
        for i, date in enumerate(self.dates):
            if date >= start_date:
                filtered_dates.append(date)
                filtered_equity.append(self.equity_history[i])
        
        # Actualizar gráfico
        self.equity_line.set_data(filtered_dates, filtered_equity)
        
        # Ajustar límites
        self.equity_ax.relim()
        self.equity_ax.autoscale_view()
        
        # Asegurar que el eje Y comience desde un valor ligeramente inferior al mínimo
        y_min = min(filtered_equity) * 0.95 if filtered_equity else 0
        y_max = max(filtered_equity) * 1.05 if filtered_equity else 1000
        self.equity_ax.set_ylim(y_min, y_max)
        
        # Actualizar etiquetas en el eje X
        if len(filtered_dates) > 5:
            step = len(filtered_dates) // 5
            self.equity_ax.set_xticks(filtered_dates[::step])
            self.equity_ax.set_xticklabels([d.strftime("%Y-%m-%d") for d in filtered_dates[::step]], rotation=45)
        
        # Actualizar título
        self.equity_ax.set_title(f'Curva de Equity - {period}')
        
        # Redibujar
        self.equity_fig.canvas.draw_idle()
    
    def change_period(self):
        """Actualiza los datos cuando cambia el período seleccionado"""
        self.update_dashboard()
    
    def generate_sample_data(self):
        """Genera datos de muestra para demostración"""
        # Si ya hay datos, no generarlos de nuevo
        if self.trades_history:
            return
        
        # Generar historial de operaciones
        num_trades = 50
        current_balance = 1000
        
        for i in range(num_trades):
            # Fecha aleatoria en los últimos 3 meses
            days_ago = np.random.randint(0, 90)
            trade_date = datetime.now() - timedelta(days=days_ago)
            
            # Tipo de operación (más compras que ventas para este ejemplo)
            trade_type = "buy" if i % 3 != 0 else "sell"
            
            # Precios
            base_price = 50000  # Precio base para BTC/USDT
            random_variation = np.random.normal(0, 1000)
            entry_price = base_price + random_variation
            
            # Para las ventas, asegurar que hay ganancia la mayoría del tiempo
            is_profit = np.random.random() < 0.6  # 60% de operaciones ganadoras
            exit_price = entry_price * (1 + np.random.uniform(0.01, 0.05)) if is_profit else entry_price * (1 - np.random.uniform(0.01, 0.03))
            
            # Tamaño
            size = np.random.uniform(0.001, 0.01)
            
            # P&L
            pl_amount = (exit_price - entry_price) * size
            pl_pct = (exit_price - entry_price) / entry_price * 100
            
            # Actualizar balance
            current_balance += pl_amount
            
            # Añadir a historial
            is_today = days_ago == 0
            
            self.trades_history.append({
                'date': trade_date,
                'type': trade_type,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'size': size,
                'pl_amount': pl_amount,
                'pl_pct': pl_pct,
                'is_today': is_today
            })
        
        # Ordenar por fecha
        self.trades_history.sort(key=lambda x: x['date'])
        
        # Generar curva de equity
        self.dates = []
        self.equity_history = []
        
        # Crear una serie diaria para los últimos 90 días
        balance = 1000
        for days_ago in range(90, -1, -1):
            date = datetime.now() - timedelta(days=days_ago)
            
            # Ajustar balance con las operaciones de ese día
            days_trades = [t for t in self.trades_history if t['date'].date() == date.date()]
            for trade in days_trades:
                balance += trade['pl_amount']
            
            self.dates.append(date)
            self.equity_history.append(balance)
    
    def add_trade(self, trade_info):
        """Añade una nueva operación al historial"""
        # Implementar en una aplicación real para registrar operaciones
        pass
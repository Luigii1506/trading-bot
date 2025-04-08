from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QPushButton, QGroupBox, QTextEdit,
    QRadioButton, QButtonGroup, QSpinBox, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from datetime import datetime
import pandas as pd
import numpy as np
from trading_bot import format_price, embed_matplotlib_plot

class LiveTab(QWidget):
    """Pestaña para trading en vivo o simulación"""
    start_bot_signal = pyqtSignal(int, bool)
    stop_bot_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.price_history = []
        self.indicator_history = {
            'ma_fast': [],
            'ma_slow': [],
            'rsi': [],
            'bb_upper': [],
            'bb_middle': [],
            'bb_lower': [],
            'signal': []
        }
        self.time_labels = []
        self.position = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        main_layout = QVBoxLayout()
        
        # Panel de control
        control_group = QGroupBox("Control del Bot")
        control_layout = QHBoxLayout()
        
        # Modo de operación
        mode_group = QGroupBox("Modo de Operación")
        mode_layout = QVBoxLayout()
        
        self.simulation_radio = QRadioButton("Simulación")
        self.simulation_radio.setChecked(True)
        self.live_radio = QRadioButton("Trading en Vivo")
        
        mode_group_btn = QButtonGroup(self)
        mode_group_btn.addButton(self.simulation_radio)
        mode_group_btn.addButton(self.live_radio)
        
        # Añadir advertencia para modo en vivo
        warning_label = QLabel("⚠️ El modo en vivo realizará operaciones reales con tu dinero")
        warning_label.setStyleSheet("color: red;")
        
        mode_layout.addWidget(self.simulation_radio)
        mode_layout.addWidget(self.live_radio)
        mode_layout.addWidget(warning_label)
        mode_group.setLayout(mode_layout)
        
        control_layout.addWidget(mode_group)
        
        # Intervalo de actualización
        interval_group = QGroupBox("Intervalo de Actualización")
        interval_layout = QFormLayout()
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)  # 10 segundos a 1 hora
        self.interval_spin.setValue(60)  # 1 minuto por defecto
        self.interval_spin.setSuffix(" segundos")
        interval_layout.addRow("Intervalo:", self.interval_spin)
        
        interval_group.setLayout(interval_layout)
        control_layout.addWidget(interval_group)
        
        # Botones de inicio/parada
        button_group = QGroupBox("Control")
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("▶ Iniciar Bot")
        self.start_button.clicked.connect(self.start_bot)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.stop_button = QPushButton("⏹ Detener Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_group.setLayout(button_layout)
        
        control_layout.addWidget(button_group)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Panel principal dividido
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Logs y operaciones
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Registro de actividad
        log_group = QGroupBox("Registro de Actividad")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setStyleSheet("background-color: #f8f9fa;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        left_layout.addWidget(log_group)
        
        # Operaciones actuales
        trades_group = QGroupBox("Operaciones")
        trades_layout = QVBoxLayout()
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            "Tipo", "Precio", "Tamaño", "Stop Loss", "Take Profit", "Hora"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        trades_layout.addWidget(self.trades_table)
        
        trades_group.setLayout(trades_layout)
        left_layout.addWidget(trades_group)
        
        main_splitter.addWidget(left_widget)
        
        # Panel derecho: Gráficos y estado
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Estado actual
        status_group = QGroupBox("Estado Actual")
        status_layout = QHBoxLayout()
        
        # Información del precio
        price_form = QFormLayout()
        
        self.price_label = QLabel("N/A")
        self.price_label.setFont(QFont("Arial", 14, QFont.Bold))
        price_form.addRow("Precio:", self.price_label)
        
        self.signal_label = QLabel("N/A")
        price_form.addRow("Señal:", self.signal_label)
        
        self.ma_fast_label = QLabel("N/A")
        price_form.addRow("MA Rápida:", self.ma_fast_label)
        
        self.ma_slow_label = QLabel("N/A")
        price_form.addRow("MA Lenta:", self.ma_slow_label)
        
        self.rsi_label = QLabel("N/A")
        price_form.addRow("RSI:", self.rsi_label)
        
        status_layout.addLayout(price_form)
        
        # Información de posición
        position_form = QFormLayout()
        
        self.position_label = QLabel("Sin posición")
        self.position_label.setFont(QFont("Arial", 12))
        position_form.addRow("Posición:", self.position_label)
        
        self.entry_price_label = QLabel("N/A")
        position_form.addRow("Precio de Entrada:", self.entry_price_label)
        
        self.current_pl_label = QLabel("N/A")
        position_form.addRow("P&L Actual:", self.current_pl_label)
        
        self.stop_loss_label = QLabel("N/A")
        position_form.addRow("Stop Loss:", self.stop_loss_label)
        
        self.take_profit_label = QLabel("N/A")
        position_form.addRow("Take Profit:", self.take_profit_label)
        
        status_layout.addLayout(position_form)
        
        status_group.setLayout(status_layout)
        right_layout.addWidget(status_group)
        
        # Gráfico
        chart_group = QGroupBox("Gráfico de Precios en Tiempo Real")
        self.chart_layout = QVBoxLayout()
        chart_group.setLayout(self.chart_layout)
        right_layout.addWidget(chart_group)
        
        main_splitter.addWidget(right_widget)
        
        # Establecer proporciones relativas de los paneles
        main_splitter.setSizes([400, 600])
        
        main_layout.addWidget(main_splitter)
        
        self.setLayout(main_layout)
        
        # Inicializar gráfico vacío
        self.init_chart()
    
    def init_chart(self):
        """Inicializa el gráfico de precios"""
        fig = Figure(figsize=(8, 6))
        self.axes = fig.add_subplot(111)
        self.axes.set_title('Precio en Tiempo Real')
        self.axes.set_xlabel('Tiempo')
        self.axes.set_ylabel('Precio')
        self.axes.grid(True)
        
        # Crear líneas vacías para actualizar después
        self.price_line, = self.axes.plot([], [], label='Precio', linewidth=2)
        self.ma_fast_line, = self.axes.plot([], [], label='MA Rápida', linewidth=1.5)
        self.ma_slow_line, = self.axes.plot([], [], label='MA Lenta', linewidth=1.5)
        self.bb_upper_line, = self.axes.plot([], [], 'k--', label='BB Superior', alpha=0.5)
        self.bb_lower_line, = self.axes.plot([], [], 'k--', label='BB Inferior', alpha=0.5)
        
        self.axes.legend()
        fig.tight_layout()
        
        # Embeber el gráfico en la interfaz
        embed_matplotlib_plot(self.chart_layout, fig)
        
        self.chart_fig = fig
    
    def start_bot(self):
        """Inicia el bot de trading"""
        interval = self.interval_spin.value()
        simulation_mode = self.simulation_radio.isChecked()
        
        # Registrar información de inicio
        mode_str = "simulación" if simulation_mode else "tiempo real"
        self.log_message(f"Iniciando bot en modo {mode_str} con intervalo de {interval} segundos")
        
        # Cambiar estado de los botones
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.simulation_radio.setEnabled(False)
        self.live_radio.setEnabled(False)
        self.interval_spin.setEnabled(False)
        
        # Limpiar historial de precios
        self.price_history = []
        for key in self.indicator_history:
            self.indicator_history[key] = []
        self.time_labels = []
        
        # Limpiar tabla de operaciones
        self.trades_table.setRowCount(0)
        
        # Reiniciar estado de posición
        self.position = None
        self.update_position_display(None)
        
        # Emitir señal para iniciar bot
        self.start_bot_signal.emit(interval, simulation_mode)
    
    def stop_bot(self):
        """Detiene el bot de trading"""
        self.log_message("Deteniendo bot...")
        
        # Cambiar estado de los botones
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.simulation_radio.setEnabled(True)
        self.live_radio.setEnabled(True)
        self.interval_spin.setEnabled(True)
        
        # Emitir señal para detener bot
        self.stop_bot_signal.emit()
    
    def log_message(self, message):
        """Añade un mensaje al registro de actividad"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Desplazar automáticamente hacia abajo
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def update_price_display(self, price, indicators):
        """Actualiza la visualización del precio actual e indicadores"""
        if price is None:
            return
        
        # Actualizar etiquetas
        self.price_label.setText(format_price(price))
        
        # Actualizar etiquetas de indicadores si están disponibles
        if 'ma_fast' in indicators:
            self.ma_fast_label.setText(format_price(indicators['ma_fast']))
        
        if 'ma_slow' in indicators:
            self.ma_slow_label.setText(format_price(indicators['ma_slow']))
        
        if 'rsi' in indicators:
            self.rsi_label.setText(f"{indicators['rsi']:.1f}")
            if indicators['rsi'] > 70:
                self.rsi_label.setStyleSheet("color: red;")
            elif indicators['rsi'] < 30:
                self.rsi_label.setStyleSheet("color: green;")
            else:
                self.rsi_label.setStyleSheet("")
        
        if 'signal' in indicators:
            signal = indicators['signal']
            if signal > 0:
                self.signal_label.setText("COMPRA")
                self.signal_label.setStyleSheet("color: green; font-weight: bold;")
            elif signal < 0:
                self.signal_label.setText("VENTA")
                self.signal_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.signal_label.setText("NEUTRAL")
                self.signal_label.setStyleSheet("")
        
        # Actualizar historial de precios (mantener los últimos 100 puntos)
        self.price_history.append(price)
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        # Actualizar historial de indicadores
        for key, value in indicators.items():
            if key in self.indicator_history:
                self.indicator_history[key].append(value)
                if len(self.indicator_history[key]) > 100:
                    self.indicator_history[key] = self.indicator_history[key][-100:]
        
        # Actualizar etiquetas de tiempo
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_labels.append(current_time)
        if len(self.time_labels) > 100:
            self.time_labels = self.time_labels[-100:]
        
        # Actualizar gráfico
        self.update_chart()
        
        # Si hay una posición abierta, actualizar P&L
        if self.position == "long" and hasattr(self, 'entry_price'):
            pl_pct = (price - self.entry_price) / self.entry_price * 100
            self.current_pl_label.setText(f"{pl_pct:.2f}%")
            
            if pl_pct > 0:
                self.current_pl_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.current_pl_label.setStyleSheet("color: red; font-weight: bold;")
    
    def update_chart(self):
        """Actualiza el gráfico de precios en tiempo real"""
        if not self.price_history:
            return
        
        # Datos para el gráfico
        x = range(len(self.price_history))
        
        # Actualizar líneas
        self.price_line.set_data(x, self.price_history)
        
        if self.indicator_history['ma_fast']:
            self.ma_fast_line.set_data(x[-len(self.indicator_history['ma_fast']):], self.indicator_history['ma_fast'])
        
        if self.indicator_history['ma_slow']:
            self.ma_slow_line.set_data(x[-len(self.indicator_history['ma_slow']):], self.indicator_history['ma_slow'])
        
        if self.indicator_history['bb_upper']:
            self.bb_upper_line.set_data(x[-len(self.indicator_history['bb_upper']):], self.indicator_history['bb_upper'])
        
        if self.indicator_history['bb_lower']:
            self.bb_lower_line.set_data(x[-len(self.indicator_history['bb_lower']):], self.indicator_history['bb_lower'])
        
        # Ajustar límites del gráfico
        self.axes.relim()
        self.axes.autoscale_view()
        
        # Establecer etiquetas en el eje X cada 10 puntos
        if len(self.time_labels) >= 10:
            step = len(self.time_labels) // 10
            self.axes.set_xticks(range(0, len(self.time_labels), step))
            self.axes.set_xticklabels([self.time_labels[i] for i in range(0, len(self.time_labels), step)], rotation=45)
        
        # Actualizar gráfico
        self.chart_fig.canvas.draw_idle()
    
    def handle_trade_executed(self, trade_info):
        """Maneja la ejecución de una operación"""
        if 'type' not in trade_info:
            return
        
        if trade_info['type'] == 'buy':
            # Operación de compra
            self.log_message(f"COMPRA ejecutada a {trade_info['price']:.2f}")
            
            # Actualizar posición
            self.position = "long"
            self.entry_price = trade_info['price']
            self.stop_loss = trade_info['stop_loss']
            self.take_profit = trade_info['take_profit']
            
            # Actualizar visualización de posición
            self.update_position_display(trade_info)
            
            # Añadir a la tabla de operaciones
            self.add_trade_to_table(trade_info)
            
        elif trade_info['type'] == 'sell':
            # Operación de venta
            self.log_message(f"VENTA ejecutada a {trade_info['price']:.2f}, Ganancia/Pérdida: {trade_info['profit_pct']:.2f}%")
            
            # Actualizar posición
            self.position = None
            
            # Actualizar visualización de posición
            self.update_position_display(None)
            
            # Añadir a la tabla de operaciones
            self.add_trade_to_table(trade_info)
    
    def update_position_display(self, trade_info):
        """Actualiza la visualización de la posición actual"""
        if trade_info is None or self.position is None:
            self.position_label.setText("Sin posición")
            self.position_label.setStyleSheet("")
            self.entry_price_label.setText("N/A")
            self.current_pl_label.setText("N/A")
            self.stop_loss_label.setText("N/A")
            self.take_profit_label.setText("N/A")
        else:
            self.position_label.setText("LONG")
            self.position_label.setStyleSheet("color: green; font-weight: bold;")
            self.entry_price_label.setText(format_price(self.entry_price))
            self.stop_loss_label.setText(format_price(self.stop_loss))
            self.take_profit_label.setText(format_price(self.take_profit))
    
    def add_trade_to_table(self, trade_info):
        """Añade una operación a la tabla de operaciones"""
        row_position = self.trades_table.rowCount()
        self.trades_table.insertRow(row_position)
        
        # Tipo
        type_item = QTableWidgetItem(trade_info['type'].upper())
        type_item.setTextAlignment(Qt.AlignCenter)
        if trade_info['type'] == 'buy':
            type_item.setBackground(QColor(200, 255, 200))  # Verde claro
        else:
            type_item.setBackground(QColor(255, 200, 200))  # Rojo claro
        self.trades_table.setItem(row_position, 0, type_item)
        
        # Precio
        self.trades_table.setItem(row_position, 1, QTableWidgetItem(format_price(trade_info['price'])))
        
        # Tamaño
        if 'size' in trade_info:
            self.trades_table.setItem(row_position, 2, QTableWidgetItem(f"{trade_info['size']:.6f}"))
        else:
            self.trades_table.setItem(row_position, 2, QTableWidgetItem("N/A"))
        
        # Stop Loss
        if 'stop_loss' in trade_info:
            self.trades_table.setItem(row_position, 3, QTableWidgetItem(format_price(trade_info['stop_loss'])))
        else:
            self.trades_table.setItem(row_position, 3, QTableWidgetItem("N/A"))
        
        # Take Profit
        if 'take_profit' in trade_info:
            self.trades_table.setItem(row_position, 4, QTableWidgetItem(format_price(trade_info['take_profit'])))
        else:
            self.trades_table.setItem(row_position, 4, QTableWidgetItem("N/A"))
        
        # Hora
        self.trades_table.setItem(row_position, 5, QTableWidgetItem(trade_info['time']))
        
        # Hacer scroll hasta la última fila
        self.trades_table.scrollToBottom()
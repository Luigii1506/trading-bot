from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QDesktopWidget, QMessageBox, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon
import sys
import traceback
import time
import pandas as pd
from datetime import datetime
import os

from gui import (
    ConfigTab,
    BacktestTab,
    OptimizeTab,
    LiveTab,
    DashboardTab
)

from trading_bot import CryptoTradingBot

class BotWorker(QThread):
    """Clase para ejecutar el bot en un hilo separado"""
    update_log = pyqtSignal(str)
    trade_executed = pyqtSignal(dict)
    price_update = pyqtSignal(float, dict)
    
    def __init__(self, bot, interval, simulation_mode):
        super().__init__()
        self.bot = bot
        self.interval = interval
        self.simulation_mode = simulation_mode
        self.running = False
    
    def run(self):
        """Ejecuta el bucle principal del bot"""
        self.running = True
        while self.running:
            try:
                # Obtener datos actualizados
                df = self.bot.fetch_ohlcv_data(limit=100)
                if df is None or df.empty:
                    self.update_log.emit("No se pudieron obtener datos. Reintentando...")
                    time.sleep(self.interval)
                    continue
                
                # Añadir indicadores y obtener señal actual
                df = self.bot.add_indicators(df)
                current_price = df['close'].iloc[-1]
                current_signal = df['signal'].iloc[-1]
                
                # Crear diccionario de indicadores para la interfaz
                indicators = {
                    'ma_fast': df['ma_fast'].iloc[-1],
                    'ma_slow': df['ma_slow'].iloc[-1],
                    'rsi': df['rsi'].iloc[-1], 
                    'bb_upper': df['bb_upper'].iloc[-1],
                    'bb_middle': df['bb_middle'].iloc[-1],
                    'bb_lower': df['bb_lower'].iloc[-1],
                    'signal': df['signal'].iloc[-1]
                }
                
                # Emitir actualización de precio e indicadores
                self.price_update.emit(current_price, indicators)
                
                # Ejecutar operación si hay señal (en modo simulación o real)
                if self.bot.execute_trade(current_signal, current_price, df, is_backtest=self.simulation_mode):
                    self.update_log.emit("Operación ejecutada exitosamente")
                
                # Esperar hasta el próximo intervalo
                time.sleep(self.interval)
                
            except Exception as e:
                error_msg = f"Error en el bucle principal: {str(e)}\n{traceback.format_exc()}"
                self.update_log.emit(error_msg)
                time.sleep(self.interval)
    
    def stop(self):
        """Detiene el hilo"""
        self.running = False
        self.wait()

class BacktestWorker(QThread):
    """Clase para ejecutar backtesting en un hilo separado"""
    update_progress = pyqtSignal(int, int)
    backtest_completed = pyqtSignal(dict, pd.DataFrame)
    
    def __init__(self, bot, start_date, end_date, initial_capital):
        super().__init__()
        self.bot = bot
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
    
    def run(self):
        """Ejecuta el backtesting"""
        # Conectar señales temporalmente
        self.bot.signal_backtest_progress.connect(self.update_progress)
        
        # Ejecutar backtest
        results, df = self.bot.backtest(
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=self.initial_capital
        )
        
        # Emitir resultados
        self.backtest_completed.emit(results, df)
        
        # Desconectar señales
        self.bot.signal_backtest_progress.disconnect(self.update_progress)

class OptimizationWorker(QThread):
    """Clase para ejecutar optimización en un hilo separado"""
    update_progress = pyqtSignal(int, int)
    optimization_completed = pyqtSignal(dict, pd.DataFrame)
    
    def __init__(self, bot, param_grid, start_date, end_date, initial_capital):
        super().__init__()
        self.bot = bot
        self.param_grid = param_grid
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
    
    def run(self):
        """Ejecuta la optimización"""
        # Conectar señales temporalmente
        self.bot.signal_optimization_progress.connect(self.update_progress)
        
        # Ejecutar optimización
        best_params, results_df = self.bot.optimize_parameters(
            param_grid=self.param_grid,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=self.initial_capital
        )
        
        # Emitir resultados
        self.optimization_completed.emit(best_params, results_df)
        
        # Desconectar señales
        self.bot.signal_optimization_progress.disconnect(self.update_progress)

class CryptoBotGUI(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar el bot
        self.bot = CryptoTradingBot()
        
        # Conectar señales del bot
        self.bot.signal_log.connect(self.update_log)
        self.bot.signal_trade_executed.connect(self.handle_trade_executed)
        self.bot.signal_backtest_completed.connect(self.handle_backtest_completed)
        self.bot.signal_optimization_completed.connect(self.handle_optimization_completed)
        self.bot.signal_price_update.connect(self.handle_price_update)
        
        # Variables para los hilos de trabajo
        self.bot_worker = None
        self.backtest_worker = None
        self.optimization_worker = None
        
        # Inicializar interfaz
        self.init_ui()
        
        # Mostrar mensaje de bienvenida
        self.update_status("Bot iniciado. Listo para configurar.")
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Configurar ventana principal
        self.setWindowTitle("CryptoTrading Bot")
        self.setGeometry(100, 100, 1200, 800)
        self.center_window()
        
        # Crear widget principal y layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Crear pestañas
        self.tabs = QTabWidget()
        
        # Pestaña de Configuración
        self.config_tab = ConfigTab()
        self.config_tab.config_updated.connect(self.update_bot_config)
        self.tabs.addTab(self.config_tab, "Configuración")
        
        # Pestaña de Backtesting
        self.backtest_tab = BacktestTab()
        self.backtest_tab.run_backtest_signal.connect(self.run_backtest)
        self.tabs.addTab(self.backtest_tab, "Backtesting")
        
        # Pestaña de Optimización
        self.optimize_tab = OptimizeTab()
        self.optimize_tab.run_optimization_signal.connect(self.run_optimization)
        self.optimize_tab.apply_best_params_signal.connect(self.apply_best_params)
        self.tabs.addTab(self.optimize_tab, "Optimización")
        
        # Pestaña de Trading en Vivo
        self.live_tab = LiveTab()
        self.live_tab.start_bot_signal.connect(self.start_bot)
        self.live_tab.stop_bot_signal.connect(self.stop_bot)
        self.tabs.addTab(self.live_tab, "Trading en Vivo")
        
        # Pestaña de Dashboard
        self.dashboard_tab = DashboardTab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        # Añadir pestañas al layout principal
        main_layout.addWidget(self.tabs)
        
        # Configurar widget central
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Crear barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
    
    def update_status(self, message):
        """Actualiza la barra de estado"""
        self.status_bar.showMessage(message)
    
    def update_log(self, message):
        """Actualiza el registro de actividad en la pestaña de trading en vivo"""
        self.live_tab.log_message(message)
    
    @pyqtSlot(dict)
    def update_bot_config(self, config):
        """Actualiza la configuración del bot"""
        try:
            # Recrear bot con nueva configuración
            self.bot = CryptoTradingBot(**config)
            
            # Reconectar señales
            self.bot.signal_log.connect(self.update_log)
            self.bot.signal_trade_executed.connect(self.handle_trade_executed)
            self.bot.signal_backtest_completed.connect(self.handle_backtest_completed)
            self.bot.signal_optimization_completed.connect(self.handle_optimization_completed)
            self.bot.signal_price_update.connect(self.handle_price_update)
            
            self.update_status(f"Configuración actualizada: {config['symbol']} en {config['exchange_id']}")
        except Exception as e:
            error_msg = f"Error al actualizar configuración: {str(e)}"
            self.update_log(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    @pyqtSlot(int, bool)
    def start_bot(self, interval, simulation_mode):
        """Inicia el bot de trading"""
        # Si ya hay un hilo en ejecución, detenerlo
        if self.bot_worker is not None and self.bot_worker.isRunning():
            self.bot_worker.stop()
        
        # Crear y iniciar nuevo hilo
        self.bot_worker = BotWorker(self.bot, interval, simulation_mode)
        self.bot_worker.update_log.connect(self.update_log)
        self.bot_worker.trade_executed.connect(self.handle_trade_executed)
        self.bot_worker.price_update.connect(self.handle_price_update)
        self.bot_worker.start()
        
        mode_str = "simulación" if simulation_mode else "tiempo real"
        self.update_status(f"Bot iniciado en modo {mode_str}")
    
    @pyqtSlot()
    def stop_bot(self):
        """Detiene el bot de trading"""
        if self.bot_worker is not None and self.bot_worker.isRunning():
            self.bot_worker.stop()
            self.update_status("Bot detenido")
    
    @pyqtSlot(str, str, float)
    def run_backtest(self, start_date, end_date, initial_capital):
        """Ejecuta el backtest en un hilo separado"""
        # Si ya hay un hilo en ejecución, detenerlo
        if self.backtest_worker is not None and self.backtest_worker.isRunning():
            self.backtest_worker.wait()
        
        # Crear y iniciar nuevo hilo
        self.backtest_worker = BacktestWorker(
            self.bot, start_date, end_date, initial_capital
        )
        self.backtest_worker.update_progress.connect(self.backtest_tab.update_progress)
        self.backtest_worker.backtest_completed.connect(self.handle_backtest_completed)
        self.backtest_worker.start()
        
        self.update_status(f"Ejecutando backtest desde {start_date} hasta {end_date}...")
    
    @pyqtSlot(dict, pd.DataFrame)
    def handle_backtest_completed(self, results, df):
        """Maneja la finalización del backtest"""
        self.backtest_tab.display_backtest_results(results, df)
        
        if results:
            result_msg = f"Backtest completado. Retorno: {results['total_return_pct']:.2f}%, Win Rate: {results['win_rate']:.2f}%"
        else:
            result_msg = "Backtest completado sin resultados"
        
        self.update_status(result_msg)
    
    @pyqtSlot(dict, str, str, float)
    def run_optimization(self, param_grid, start_date, end_date, initial_capital):
        """Ejecuta la optimización en un hilo separado"""
        # Si ya hay un hilo en ejecución, detenerlo
        if self.optimization_worker is not None and self.optimization_worker.isRunning():
            self.optimization_worker.wait()
        
        # Crear y iniciar nuevo hilo
        self.optimization_worker = OptimizationWorker(
            self.bot, param_grid, start_date, end_date, initial_capital
        )
        self.optimization_worker.update_progress.connect(self.optimize_tab.update_progress)
        self.optimization_worker.optimization_completed.connect(self.handle_optimization_completed)
        self.optimization_worker.start()
        
        self.update_status("Ejecutando optimización...")
    
    @pyqtSlot(dict, pd.DataFrame)
    def handle_optimization_completed(self, best_params, results_df):
        """Maneja la finalización de la optimización"""
        self.optimize_tab.display_optimization_results(best_params, results_df)
        
        if best_params:
            param_str = ", ".join([f"{k}={v}" for k, v in best_params.items()])
            result_msg = f"Optimización completada. Mejores parámetros: {param_str}"
        else:
            result_msg = "Optimización completada sin resultados"
        
        self.update_status(result_msg)
    
    @pyqtSlot(dict)
    def apply_best_params(self, params):
        """Aplica los mejores parámetros encontrados"""
        try:
            # Obtener configuración actual
            current_config = self.bot.get_settings()
            
            # Actualizar con nuevos parámetros
            for param, value in params.items():
                current_config[param] = value
            
            # Actualizar bot y UI
            self.update_bot_config(current_config)
            self.config_tab.update_from_settings(current_config)
            
            self.update_status(f"Parámetros optimizados aplicados")
        except Exception as e:
            error_msg = f"Error al aplicar parámetros: {str(e)}"
            self.update_log(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    @pyqtSlot(float, dict)
    def handle_price_update(self, price, indicators):
        """Maneja la actualización de precio e indicadores"""
        self.live_tab.update_price_display(price, indicators)
    
    @pyqtSlot(dict)
    def handle_trade_executed(self, trade_info):
        """Maneja la ejecución de una operación"""
        self.live_tab.handle_trade_executed(trade_info)
        self.dashboard_tab.add_trade(trade_info)
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        # Detener todos los hilos antes de cerrar
        if self.bot_worker is not None and self.bot_worker.isRunning():
            self.bot_worker.stop()
        
        if self.backtest_worker is not None and self.backtest_worker.isRunning():
            self.backtest_worker.wait()
        
        if self.optimization_worker is not None and self.optimization_worker.isRunning():
            self.optimization_worker.wait()
        
        event.accept()
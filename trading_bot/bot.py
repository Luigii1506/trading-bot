import pandas as pd
import numpy as np
import ccxt
import time
from datetime import datetime
import matplotlib.pyplot as plt
import logging
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import os
from PyQt5.QtCore import QObject, pyqtSignal

# Configuración de logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradingBot")

class CryptoTradingBot(QObject):
    # Señales para comunicarse con la interfaz gráfica
    signal_log = pyqtSignal(str)
    signal_trade_executed = pyqtSignal(dict)
    signal_backtest_progress = pyqtSignal(int, int)  # (current, total)
    signal_backtest_completed = pyqtSignal(dict, pd.DataFrame)
    signal_optimization_progress = pyqtSignal(int, int)  # (current, total)
    signal_optimization_completed = pyqtSignal(dict, pd.DataFrame)
    signal_price_update = pyqtSignal(float, dict)  # (price, indicators)
    
    def __init__(self, exchange_id='binance', symbol='BTC/USDT', timeframe='1h', 
                 fast_ma=20, slow_ma=50, rsi_period=14, rsi_overbought=70, 
                 rsi_oversold=30, bb_period=20, bb_std=2, risk_per_trade=0.02,
                 use_ema=True, parent=None):
        """
        Inicializa el bot de trading
        
        Args:
            exchange_id (str): ID del exchange a utilizar (binance, coinbase, etc.)
            symbol (str): Par de trading (BTC/USDT, ETH/USDT, etc.)
            timeframe (str): Timeframe para el análisis (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            fast_ma (int): Período para la media móvil rápida
            slow_ma (int): Período para la media móvil lenta
            rsi_period (int): Período para el RSI
            rsi_overbought (int): Nivel de sobrecompra del RSI
            rsi_oversold (int): Nivel de sobreventa del RSI
            bb_period (int): Período para las Bandas de Bollinger
            bb_std (int): Desviación estándar para las Bandas de Bollinger
            risk_per_trade (float): Porcentaje de riesgo por operación (0.02 = 2%)
            use_ema (bool): Usar EMA en lugar de SMA
            parent: Objeto padre para las señales Qt
        """
        super().__init__(parent)
        
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Parámetros de la estrategia
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.use_ema = use_ema
        
        # Gestión de riesgos
        self.risk_per_trade = risk_per_trade
        
        # Estado del trading
        self.position = None
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
        # Control de ejecución
        self.running = False
        
        self.log_info(f"Bot inicializado para {symbol} en {exchange_id} con timeframe {timeframe}")
    
    def log_info(self, message):
        """Registra información y emite la señal para la interfaz gráfica"""
        logger.info(message)
        self.signal_log.emit(message)
    
    def log_error(self, message):
        """Registra errores y emite la señal para la interfaz gráfica"""
        logger.error(message)
        self.signal_log.emit(f"ERROR: {message}")
    
    def fetch_ohlcv_data(self, limit=500):
        """Obtiene datos históricos de velas OHLCV"""
        try:
            self.log_info(f"Obteniendo datos OHLCV para {self.symbol} ({self.timeframe})")
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            self.log_error(f"Error al obtener datos OHLCV: {e}")
            return None
    
    def add_indicators(self, df):
        """Añade indicadores técnicos al DataFrame"""
        # Medias Móviles
        if self.use_ema:
            df['ma_fast'] = EMAIndicator(close=df['close'], window=self.fast_ma).ema_indicator()
            df['ma_slow'] = EMAIndicator(close=df['close'], window=self.slow_ma).ema_indicator()
        else:
            df['ma_fast'] = SMAIndicator(close=df['close'], window=self.fast_ma).sma_indicator()
            df['ma_slow'] = SMAIndicator(close=df['close'], window=self.slow_ma).sma_indicator()
        
        # RSI
        rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
        df['rsi'] = rsi.rsi()
        
        # Bandas de Bollinger
        bb = BollingerBands(close=df['close'], window=self.bb_period, window_dev=self.bb_std)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        # Señales (1 = compra, -1 = venta, 0 = mantener)
        df['signal'] = 0
        
        # Señal de cruce de medias móviles
        df['ma_crossover'] = np.where(
            (df['ma_fast'] > df['ma_slow']) & (df['ma_fast'].shift(1) <= df['ma_slow'].shift(1)), 1,
            np.where((df['ma_fast'] < df['ma_slow']) & (df['ma_fast'].shift(1) >= df['ma_slow'].shift(1)), -1, 0)
        )
        
        # Señal de RSI
        df['rsi_signal'] = np.where(df['rsi'] < self.rsi_oversold, 1, 
                                   np.where(df['rsi'] > self.rsi_overbought, -1, 0))
        
        # Señal de Bandas de Bollinger
        df['bb_signal'] = np.where(df['close'] < df['bb_lower'], 1, 
                                  np.where(df['close'] > df['bb_upper'], -1, 0))
        
        # Señal combinada (con más peso en el cruce de medias móviles)
        df['signal'] = df['ma_crossover'] + 0.5 * df['rsi_signal'] + 0.5 * df['bb_signal']
        df['signal'] = np.where(df['signal'] >= 1, 1, np.where(df['signal'] <= -1, -1, 0))
        
        return df
    
    def calculate_position_size(self, price, stop_loss):
        """Calcula el tamaño de la posición basado en el riesgo por operación"""
        try:
            balance = self.exchange.fetch_balance()
            usdt_balance = balance['total']['USDT']
            risk_amount = usdt_balance * self.risk_per_trade
            stop_loss_pct = abs(price - stop_loss) / price
            position_size = risk_amount / stop_loss_pct
            return min(position_size, usdt_balance * 0.95)  # Máximo 95% del balance
        except Exception as e:
            self.log_error(f"Error al calcular tamaño de posición: {e}")
            return 0
    
    def execute_trade(self, signal, price, df, is_backtest=False):
        """Ejecuta una operación basada en la señal"""
        if self.position is None and signal == 1:  # Señal de compra y no hay posición abierta
            # Cálculo de Stop Loss y Take Profit
            atr = self._calculate_atr(df)
            stop_loss = price - 2 * atr
            take_profit = price + 3 * atr  # Relación riesgo/recompensa 1:1.5
            
            position_size = 1.0 if is_backtest else self.calculate_position_size(price, stop_loss)
            if position_size > 0:
                try:
                    # En modo backtest o cuando está en modo simulación, no ejecutamos órdenes reales
                    if not is_backtest:
                        # Comentado por seguridad, descomentarlo para operar en vivo
                        # self.exchange.create_market_buy_order(self.symbol, position_size)
                        pass
                    
                    self.position = "long"
                    self.entry_price = price
                    self.stop_loss = stop_loss
                    self.take_profit = take_profit
                    
                    trade_info = {
                        'type': 'buy',
                        'price': price,
                        'size': position_size,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    self.log_info(f"COMPRA en {price}: Tamaño={position_size:.6f}, SL={stop_loss:.2f}, TP={take_profit:.2f}")
                    self.signal_trade_executed.emit(trade_info)
                    return True
                except Exception as e:
                    self.log_error(f"Error al ejecutar orden de compra: {e}")
        
        elif self.position == "long":
            # Verificar Stop Loss o Take Profit
            if price <= self.stop_loss or price >= self.take_profit or signal == -1:
                try:
                    # En modo backtest o cuando está en modo simulación, no ejecutamos órdenes reales
                    if not is_backtest:
                        # Comentado por seguridad, descomentarlo para operar en vivo
                        # self.exchange.create_market_sell_order(self.symbol, position_size)
                        pass
                    
                    profit_pct = (price - self.entry_price) / self.entry_price * 100
                    
                    trade_info = {
                        'type': 'sell',
                        'price': price,
                        'entry_price': self.entry_price,
                        'profit_pct': profit_pct,
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    self.log_info(f"VENTA en {price}: Ganancia/Pérdida={profit_pct:.2f}%")
                    self.signal_trade_executed.emit(trade_info)
                    
                    self.position = None
                    return True
                except Exception as e:
                    self.log_error(f"Error al ejecutar orden de venta: {e}")
        
        return False
    
    def _calculate_atr(self, df, period=14):
        """Calcula el Average True Range para determinar stop loss"""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        return atr
    
    def backtest(self, start_date=None, end_date=None, initial_balance=1000):
        """Realiza un backtest de la estrategia"""
        self.log_info(f"Iniciando backtest desde {start_date} hasta {end_date} con balance inicial de {initial_balance}")
        
        df = self.fetch_ohlcv_data(limit=1000)
        if df is None or df.empty:
            self.log_error("No hay datos para hacer backtest")
            return None, None
        
        df = self.add_indicators(df)
        
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        # Preparar resultados
        balance = initial_balance
        position = None
        entry_price = 0
        trades = []
        
        total_rows = len(df)
        
        for i, (idx, row) in enumerate(df.iterrows()):
            # Informar progreso
            if i % 10 == 0:  # Cada 10 iteraciones
                self.signal_backtest_progress.emit(i, total_rows)
            
            price = row['close']
            signal = row['signal']
            
            # Lógica de compra
            if position is None and signal == 1:
                entry_price = price
                position_size = balance / price
                position = position_size
                self.log_info(f"Backtest - COMPRA: {idx}, Precio: {price:.2f}, Balance: {balance:.2f}")
            
            # Lógica de venta
            elif position is not None and signal == -1:
                exit_price = price
                profit = position * (exit_price - entry_price)
                balance += profit
                trades.append({
                    'entry_date': entry_price.index if hasattr(entry_price, 'index') else idx,
                    'exit_date': idx,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit_pct': (exit_price - entry_price) / entry_price * 100,
                    'balance': balance
                })
                position = None
                self.log_info(f"Backtest - VENTA: {idx}, Precio: {price:.2f}, Balance: {balance:.2f}")
        
        # Cerrar posición final si existe
        if position is not None:
            exit_price = df.iloc[-1]['close']
            profit = position * (exit_price - entry_price)
            balance += profit
            trades.append({
                'entry_date': entry_price.index if hasattr(entry_price, 'index') else df.index[-1],
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': exit_price,
                'profit_pct': (exit_price - entry_price) / entry_price * 100,
                'balance': balance
            })
        
        # Calcular métricas de rendimiento
        if trades:
            trades_df = pd.DataFrame(trades)
            total_return = (balance - initial_balance) / initial_balance * 100
            win_trades = trades_df[trades_df['profit_pct'] > 0]
            lose_trades = trades_df[trades_df['profit_pct'] <= 0]
            win_rate = len(win_trades) / len(trades_df) * 100 if len(trades_df) > 0 else 0
            
            # Calcular drawdown
            equity_curve = pd.Series(index=df.index)
            current_balance = initial_balance
            
            for i, row in df.iterrows():
                for trade in trades:
                    entry_date = trade['entry_date']
                    exit_date = trade['exit_date']
                    
                    if isinstance(entry_date, pd.Timestamp) and isinstance(exit_date, pd.Timestamp):
                        if entry_date <= i <= exit_date:
                            # Durante el trade
                            current_price = row['close']
                            profit = (current_price - trade['entry_price']) / trade['entry_price'] * 100
                            position_value = (1 + profit/100) * initial_balance
                            equity_curve[i] = position_value
                
                if pd.isna(equity_curve[i]):
                    equity_curve[i] = current_balance
            
            # Calcular maximum drawdown
            peak = equity_curve.cummax()
            drawdown = (equity_curve - peak) / peak * 100
            max_drawdown = drawdown.min()
            
            backtest_results = {
                'initial_balance': initial_balance,
                'final_balance': balance,
                'total_return_pct': total_return,
                'total_trades': len(trades_df),
                'win_trades': len(win_trades),
                'lose_trades': len(lose_trades),
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'trades': trades_df,
                'equity_curve': equity_curve,
                'drawdown': drawdown
            }
            
            self.log_info(f"Backtest completado: Retorno={total_return:.2f}%, Win Rate={win_rate:.2f}%, Max Drawdown={max_drawdown:.2f}%")
            
            # Emitir señal de backtest completado
            self.signal_backtest_completed.emit(backtest_results, df)
            
            return backtest_results, df
        
        self.log_info("No se realizaron operaciones durante el backtest")
        self.signal_backtest_completed.emit({}, df)
        
        return None, df
    
    def plot_backtest(self, df, backtest_results, save_path=None):
        """Grafica los resultados del backtest"""
        if not backtest_results or not df.any().any():
            self.log_error("No hay resultados para graficar")
            return
        
        trades_df = backtest_results.get('trades')
        if trades_df is None or trades_df.empty:
            self.log_error("No hay operaciones para graficar")
            return
        
        plt.figure(figsize=(15, 12))
        
        # Gráfico de precios
        plt.subplot(4, 1, 1)
        plt.plot(df.index, df['close'], label='Precio')
        plt.plot(df.index, df['ma_fast'], label=f'MA Rápida ({self.fast_ma})')
        plt.plot(df.index, df['ma_slow'], label=f'MA Lenta ({self.slow_ma})')
        plt.fill_between(df.index, df['bb_upper'], df['bb_lower'], alpha=0.2, color='gray')
        
        # Marcar entradas y salidas
        if not trades_df.empty:
            buy_points = []
            sell_points = []
            buy_prices = []
            sell_prices = []
            
            for _, trade in trades_df.iterrows():
                entry_date = trade['entry_date']
                exit_date = trade['exit_date']
                
                if isinstance(entry_date, pd.Timestamp) and entry_date in df.index:
                    buy_points.append(entry_date)
                    buy_prices.append(trade['entry_price'])
                
                if isinstance(exit_date, pd.Timestamp) and exit_date in df.index:
                    sell_points.append(exit_date)
                    sell_prices.append(trade['exit_price'])
            
            if buy_points:
                plt.scatter(buy_points, buy_prices, color='green', marker='^', s=100, label='Compra')
            if sell_points:
                plt.scatter(sell_points, sell_prices, color='red', marker='v', s=100, label='Venta')
        
        plt.title('Precio y Señales')
        plt.legend()
        
        # Gráfico de RSI
        plt.subplot(4, 1, 2)
        plt.plot(df.index, df['rsi'], label='RSI')
        plt.axhline(y=self.rsi_overbought, color='r', linestyle='--')
        plt.axhline(y=self.rsi_oversold, color='g', linestyle='--')
        plt.title('RSI')
        plt.legend()
        
        # Gráfico de señales
        plt.subplot(4, 1, 3)
        plt.plot(df.index, df['signal'], label='Señal')
        plt.axhline(y=0, color='k', linestyle='--')
        plt.title('Señales de Trading')
        plt.legend()
        
        # Gráfico de balance
        plt.subplot(4, 1, 4)
        if 'equity_curve' in backtest_results and not backtest_results['equity_curve'].empty:
            plt.plot(backtest_results['equity_curve'].index, backtest_results['equity_curve'], label='Balance')
            plt.title(f'Balance (Retorno: {backtest_results["total_return_pct"]:.2f}%, Win Rate: {backtest_results["win_rate"]:.2f}%)')
            plt.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        
        return plt.gcf()  # Devolver la figura para mostrarla en la GUI
    
    def optimize_parameters(self, param_grid, start_date=None, end_date=None, initial_balance=1000):
        """Optimiza los parámetros de la estrategia mediante grid search"""
        best_return = -float('inf')
        best_params = None
        results = []
        
        total_combinations = 1
        for param_values in param_grid.values():
            total_combinations *= len(param_values)
        
        self.log_info(f"Comenzando optimización con {total_combinations} combinaciones")
        
        # Guarda los parámetros originales para restaurarlos después
        original_params = {}
        for param in param_grid.keys():
            original_params[param] = getattr(self, param)
        
        current_combination = 0
        
        # Función recursiva para grid search
        def grid_search(params, param_names, current_idx, current_params):
            nonlocal best_return, best_params, current_combination
            
            if current_idx == len(param_names):
                current_combination += 1
                self.signal_optimization_progress.emit(current_combination, total_combinations)
                
                # Aplicar parámetros actuales
                for param, value in current_params.items():
                    setattr(self, param, value)
                
                # Ejecutar backtest
                backtest_results, _ = self.backtest(start_date, end_date, initial_balance)
                
                # Registrar resultados
                result_item = {
                    'params': current_params.copy(),
                }
                
                if backtest_results:
                    result_item.update({
                        'return': backtest_results['total_return_pct'],
                        'win_rate': backtest_results['win_rate'],
                        'trades': backtest_results['total_trades'],
                        'max_drawdown': backtest_results.get('max_drawdown', 0)
                    })
                    
                    if backtest_results['total_return_pct'] > best_return:
                        best_return = backtest_results['total_return_pct']
                        best_params = current_params.copy()
                else:
                    result_item.update({
                        'return': 0,
                        'win_rate': 0,
                        'trades': 0,
                        'max_drawdown': 0
                    })
                
                results.append(result_item)
                
                self.log_info(f"Probando {current_params}: Retorno={result_item['return']:.2f}%, Win Rate={result_item['win_rate']:.2f}%")
                return
            
            param_name = param_names[current_idx]
            for param_value in params[param_name]:
                current_params[param_name] = param_value
                grid_search(params, param_names, current_idx + 1, current_params)
        
        # Ejecutar grid search
        grid_search(param_grid, list(param_grid.keys()), 0, {})
        
        # Restaurar parámetros originales
        for param, value in original_params.items():
            setattr(self, param, value)
        
        # Ordenar resultados
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('return', ascending=False)
        
        self.log_info(f"Optimización completada. Mejores parámetros: {best_params} con retorno: {best_return:.2f}%")
        
        # Emitir señal de optimización completada
        self.signal_optimization_completed.emit(best_params, results_df)
        
        return best_params, results_df
    
    def run(self, interval_seconds=60, simulation_mode=True):
        """Ejecuta el bot en tiempo real"""
        self.log_info(f"Iniciando bot de trading en {'modo simulación' if simulation_mode else 'modo real'} con intervalo de {interval_seconds} segundos")
        self.running = True
        
        while self.running:
            try:
                # Obtener datos actualizados
                df = self.fetch_ohlcv_data(limit=100)
                if df is None or df.empty:
                    self.log_warning("No se pudieron obtener datos. Reintentando...")
                    time.sleep(interval_seconds)
                    continue
                
                # Añadir indicadores y obtener señal actual
                df = self.add_indicators(df)
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
                
                self.log_info(f"Precio actual: {current_price:.2f}, Señal: {current_signal}")
                
                # Emitir actualización de precio e indicadores
                self.signal_price_update.emit(current_price, indicators)
                
                # Ejecutar operación si hay señal (en modo simulación o real)
                if self.execute_trade(current_signal, current_price, df, is_backtest=simulation_mode):
                    self.log_info("Operación ejecutada exitosamente")
                
                # Esperar hasta el próximo intervalo
                time.sleep(interval_seconds)
                
            except Exception as e:
                self.log_error(f"Error en el ciclo principal: {e}")
                time.sleep(interval_seconds)
    
    def stop(self):
        """Detiene la ejecución del bot"""
        self.running = False
        self.log_info("Bot detenido")
    
    def apply_parameters(self, params):
        """Aplica un conjunto de parámetros al bot"""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
        
        self.log_info(f"Parámetros aplicados: {params}")
    
    def get_settings(self):
        """Devuelve configuración actual como diccionario"""
        return {
            'exchange_id': self.exchange_id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'fast_ma': self.fast_ma,
            'slow_ma': self.slow_ma,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'bb_period': self.bb_period,
            'bb_std': self.bb_std,
            'risk_per_trade': self.risk_per_trade,
            'use_ema': self.use_ema
        }
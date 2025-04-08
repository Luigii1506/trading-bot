import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from datetime import datetime, timedelta

def get_available_exchanges():
    """Devuelve una lista de exchanges disponibles en ccxt"""
    import ccxt
    return sorted([exchange for exchange in ccxt.exchanges])

def get_available_timeframes():
    """Devuelve una lista de timeframes comunes"""
    return ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']

def format_price(price, decimals=2):
    """Formatea un precio con el número de decimales especificado"""
    return f"{price:.{decimals}f}"

def calculate_portfolio_value(balance, positions, current_prices):
    """Calcula el valor total del portafolio"""
    portfolio_value = balance
    for symbol, amount in positions.items():
        if symbol in current_prices:
            portfolio_value += amount * current_prices[symbol]
    return portfolio_value

def plot_equity_curve(equity_data, title="Equity Curve"):
    """Genera un gráfico de la curva de equity"""
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    
    # Graficar la curva de equity
    ax.plot(equity_data.index, equity_data.values, label='Portfolio Value')
    ax.set_title(title)
    ax.set_ylabel('Value')
    ax.set_xlabel('Date')
    ax.grid(True)
    ax.legend()
    
    return fig

def plot_drawdown_chart(drawdown_data, title="Drawdown"):
    """Genera un gráfico de drawdown"""
    fig = Figure(figsize=(12, 6))
    ax = fig.add_subplot(111)
    
    # Graficar el drawdown como áreas
    ax.fill_between(drawdown_data.index, 0, drawdown_data.values, color='red', alpha=0.3)
    ax.plot(drawdown_data.index, drawdown_data.values, color='red', label='Drawdown %')
    
    ax.set_title(title)
    ax.set_ylabel('Drawdown %')
    ax.set_xlabel('Date')
    ax.grid(True)
    ax.legend()
    
    return fig

def create_summary_stats(backtest_results):
    """Crea un resumen de estadísticas del backtest"""
    if not backtest_results:
        return "No hay resultados disponibles"
    
    stats = [
        f"Balance inicial: ${backtest_results['initial_balance']:.2f}",
        f"Balance final: ${backtest_results['final_balance']:.2f}",
        f"Retorno total: {backtest_results['total_return_pct']:.2f}%",
        f"Operaciones totales: {backtest_results['total_trades']}",
        f"Operaciones ganadoras: {backtest_results['win_trades']}",
        f"Operaciones perdedoras: {backtest_results['lose_trades']}",
        f"Tasa de victoria: {backtest_results['win_rate']:.2f}%",
        f"Drawdown máximo: {backtest_results.get('max_drawdown', 0):.2f}%"
    ]
    
    return "\n".join(stats)

def get_performance_metrics(equity_curve, initial_balance):
    """Calcula métricas de rendimiento adicionales"""
    if equity_curve.empty:
        return {}
    
    # Cálculo de retornos diarios
    daily_returns = equity_curve.pct_change().dropna()
    
    # Cálculo de métricas
    total_return = (equity_curve.iloc[-1] - initial_balance) / initial_balance * 100
    
    # Volatilidad (desviación estándar anualizada)
    volatility = daily_returns.std() * np.sqrt(252) * 100  # Asumiendo 252 días de trading por año
    
    # Ratio de Sharpe (asumiendo tasa libre de riesgo = 0 para simplificar)
    sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else 0
    
    # Maximum Drawdown
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak * 100
    max_drawdown = drawdown.min()
    
    # Calmar Ratio
    calmar_ratio = (total_return / 100) / abs(max_drawdown / 100) if max_drawdown != 0 else 0
    
    # Retorno anualizado (asumiendo 252 días de trading)
    trading_days = len(daily_returns)
    annual_return = ((1 + total_return/100) ** (252/trading_days) - 1) * 100 if trading_days > 0 else 0
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'calmar_ratio': calmar_ratio,
        'trading_days': trading_days
    }

def generate_date_ranges():
    """Genera rangos de fechas predefinidos para backtesting"""
    today = datetime.now()
    
    ranges = {
        'Último mes': (today - timedelta(days=30), today),
        'Últimos 3 meses': (today - timedelta(days=90), today),
        'Últimos 6 meses': (today - timedelta(days=180), today),
        'Último año': (today - timedelta(days=365), today),
        'Últimos 2 años': (today - timedelta(days=730), today),
        'Personalizado': (None, None)
    }
    
    return ranges

class MatplotlibCanvas(FigureCanvasQTAgg):
    """Canvas para mostrar gráficos de Matplotlib en PyQt"""
    def __init__(self, fig=None, parent=None):
        if fig is None:
            fig = Figure()
        self.fig = fig
        super(MatplotlibCanvas, self).__init__(self.fig)
        self.setParent(parent)

def embed_matplotlib_plot(layout, figure):
    """Embebe un gráfico de matplotlib en un layout de PyQt"""
    # Limpiar el layout primero
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
    
    # Crear widget para contener el canvas
    canvas_widget = QWidget()
    canvas_layout = QVBoxLayout(canvas_widget)
    canvas = MatplotlibCanvas(figure)
    canvas_layout.addWidget(canvas)
    
    # Añadir al layout principal
    layout.addWidget(canvas_widget)
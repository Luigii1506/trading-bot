from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, 
    QPushButton, QCheckBox, QGroupBox, QLineEdit
)
from PyQt5.QtCore import pyqtSignal, Qt
from trading_bot import get_available_exchanges, get_available_timeframes

class ConfigTab(QWidget):
    """Pestaña para configurar los parámetros del bot de trading"""
    config_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        main_layout = QVBoxLayout()
        
        # Sección de Exchange/Mercado
        market_group = QGroupBox("Configuración del Mercado")
        market_layout = QFormLayout()
        
        # Exchange
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(get_available_exchanges())
        self.exchange_combo.setCurrentText("binance")
        market_layout.addRow("Exchange:", self.exchange_combo)
        
        # Símbolo
        self.symbol_edit = QLineEdit("BTC/USDT")
        market_layout.addRow("Par de Trading:", self.symbol_edit)
        
        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(get_available_timeframes())
        self.timeframe_combo.setCurrentText("1h")
        market_layout.addRow("Timeframe:", self.timeframe_combo)
        
        market_group.setLayout(market_layout)
        main_layout.addWidget(market_group)
        
        # Sección de Indicadores
        indicators_group = QGroupBox("Configuración de Indicadores")
        indicators_layout = QFormLayout()
        
        # Tipo de Media Móvil
        self.use_ema_checkbox = QCheckBox("Usar EMA (en lugar de SMA)")
        self.use_ema_checkbox.setChecked(True)
        indicators_layout.addRow("", self.use_ema_checkbox)
        
        # Media Móvil Rápida
        self.fast_ma_spin = QSpinBox()
        self.fast_ma_spin.setRange(5, 200)
        self.fast_ma_spin.setValue(20)
        indicators_layout.addRow("Período MA Rápida:", self.fast_ma_spin)
        
        # Media Móvil Lenta
        self.slow_ma_spin = QSpinBox()
        self.slow_ma_spin.setRange(10, 300)
        self.slow_ma_spin.setValue(50)
        indicators_layout.addRow("Período MA Lenta:", self.slow_ma_spin)
        
        # RSI Período
        self.rsi_period_spin = QSpinBox()
        self.rsi_period_spin.setRange(3, 50)
        self.rsi_period_spin.setValue(14)
        indicators_layout.addRow("Período RSI:", self.rsi_period_spin)
        
        # RSI Sobrecompra
        self.rsi_overbought_spin = QSpinBox()
        self.rsi_overbought_spin.setRange(60, 90)
        self.rsi_overbought_spin.setValue(70)
        indicators_layout.addRow("RSI Sobrecompra:", self.rsi_overbought_spin)
        
        # RSI Sobreventa
        self.rsi_oversold_spin = QSpinBox()
        self.rsi_oversold_spin.setRange(10, 40)
        self.rsi_oversold_spin.setValue(30)
        indicators_layout.addRow("RSI Sobreventa:", self.rsi_oversold_spin)
        
        # Bandas de Bollinger Período
        self.bb_period_spin = QSpinBox()
        self.bb_period_spin.setRange(5, 50)
        self.bb_period_spin.setValue(20)
        indicators_layout.addRow("Período Bollinger:", self.bb_period_spin)
        
        # Bandas de Bollinger Desviación Estándar
        self.bb_std_spin = QDoubleSpinBox()
        self.bb_std_spin.setRange(0.5, 5.0)
        self.bb_std_spin.setValue(2.0)
        self.bb_std_spin.setSingleStep(0.1)
        indicators_layout.addRow("Desviación Estándar BB:", self.bb_std_spin)
        
        indicators_group.setLayout(indicators_layout)
        main_layout.addWidget(indicators_group)
        
        # Sección de Gestión de Riesgos
        risk_group = QGroupBox("Gestión de Riesgos")
        risk_layout = QFormLayout()
        
        # Riesgo por Operación
        self.risk_per_trade_spin = QDoubleSpinBox()
        self.risk_per_trade_spin.setRange(0.001, 0.1)
        self.risk_per_trade_spin.setValue(0.02)
        self.risk_per_trade_spin.setSingleStep(0.001)
        self.risk_per_trade_spin.setDecimals(3)
        risk_layout.addRow("Riesgo por Operación (%):", self.risk_per_trade_spin)
        
        risk_group.setLayout(risk_layout)
        main_layout.addWidget(risk_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Aplicar Configuración")
        self.apply_button.clicked.connect(self.apply_config)
        buttons_layout.addWidget(self.apply_button)
        
        self.reset_button = QPushButton("Restablecer por Defecto")
        self.reset_button.clicked.connect(self.reset_config)
        buttons_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Espacio en blanco al final
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def apply_config(self):
        """Aplica la configuración actual y emite señal"""
        config = self.get_current_config()
        self.config_updated.emit(config)
    
    def reset_config(self):
        """Restablece la configuración a los valores por defecto"""
        self.exchange_combo.setCurrentText("binance")
        self.symbol_edit.setText("BTC/USDT")
        self.timeframe_combo.setCurrentText("1h")
        self.use_ema_checkbox.setChecked(True)
        self.fast_ma_spin.setValue(20)
        self.slow_ma_spin.setValue(50)
        self.rsi_period_spin.setValue(14)
        self.rsi_overbought_spin.setValue(70)
        self.rsi_oversold_spin.setValue(30)
        self.bb_period_spin.setValue(20)
        self.bb_std_spin.setValue(2.0)
        self.risk_per_trade_spin.setValue(0.02)
        
        self.apply_config()
    
    def get_current_config(self):
        """Obtiene la configuración actual como diccionario"""
        return {
            'exchange_id': self.exchange_combo.currentText(),
            'symbol': self.symbol_edit.text(),
            'timeframe': self.timeframe_combo.currentText(),
            'use_ema': self.use_ema_checkbox.isChecked(),
            'fast_ma': self.fast_ma_spin.value(),
            'slow_ma': self.slow_ma_spin.value(),
            'rsi_period': self.rsi_period_spin.value(),
            'rsi_overbought': self.rsi_overbought_spin.value(),
            'rsi_oversold': self.rsi_oversold_spin.value(),
            'bb_period': self.bb_period_spin.value(),
            'bb_std': self.bb_std_spin.value(),
            'risk_per_trade': self.risk_per_trade_spin.value()
        }
    
    def update_from_settings(self, settings):
        """Actualiza la interfaz con una configuración existente"""
        if 'exchange_id' in settings:
            index = self.exchange_combo.findText(settings['exchange_id'])
            if index >= 0:
                self.exchange_combo.setCurrentIndex(index)
        
        if 'symbol' in settings:
            self.symbol_edit.setText(settings['symbol'])
        
        if 'timeframe' in settings:
            index = self.timeframe_combo.findText(settings['timeframe'])
            if index >= 0:
                self.timeframe_combo.setCurrentIndex(index)
        
        if 'use_ema' in settings:
            self.use_ema_checkbox.setChecked(settings['use_ema'])
        
        if 'fast_ma' in settings:
            self.fast_ma_spin.setValue(settings['fast_ma'])
        
        if 'slow_ma' in settings:
            self.slow_ma_spin.setValue(settings['slow_ma'])
        
        if 'rsi_period' in settings:
            self.rsi_period_spin.setValue(settings['rsi_period'])
        
        if 'rsi_overbought' in settings:
            self.rsi_overbought_spin.setValue(settings['rsi_overbought'])
        
        if 'rsi_oversold' in settings:
            self.rsi_oversold_spin.setValue(settings['rsi_oversold'])
        
        if 'bb_period' in settings:
            self.bb_period_spin.setValue(settings['bb_period'])
        
        if 'bb_std' in settings:
            self.bb_std_spin.setValue(settings['bb_std'])
        
        if 'risk_per_trade' in settings:
            self.risk_per_trade_spin.setValue(settings['risk_per_trade'])
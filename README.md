# Bot de Trading de Criptomonedas con Interfaz Gráfica

Este proyecto implementa un bot de trading de criptomonedas con una interfaz gráfica completa que permite configurar parámetros, realizar backtesting, optimizar estrategias y ejecutar el bot en tiempo real o en modo simulación.

![Bot de Trading Screenshot](https://via.placeholder.com/800x450.png?text=Bot+de+Trading+Screenshot)

## Características

- **Interfaz gráfica intuitiva**: Fácil de usar, con múltiples pestañas para diferentes funcionalidades.
- **Configuración personalizable**: Permite configurar exchange, par de trading, timeframe y parámetros de la estrategia.
- **Backtesting**: Prueba tu estrategia con datos históricos para evaluar su rendimiento.
- **Optimización de parámetros**: Encuentra los mejores parámetros para tu estrategia mediante grid search.
- **Trading en vivo**: Opera en tiempo real o en modo simulación.
- **Dashboard**: Visualiza estadísticas y rendimiento de tus operaciones.
- **Gestión de riesgos**: Implementación de stop loss y take profit.
- **Gráficos interactivos**: Visualización de precios, indicadores y resultados.

## Estrategia de Trading

La estrategia implementada por defecto combina varios indicadores técnicos:

- **Cruce de Medias Móviles** (EMA o SMA)
- **RSI** (Índice de Fuerza Relativa)
- **Bandas de Bollinger**

Las señales de estos indicadores se combinan para generar decisiones de compra y venta.

## Instalación

### Requisitos

- Python 3.7 o superior
- Dependencias listadas en `requirements.txt`

### Pasos de instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/trading-bot.git
cd trading-bot
```

2. Crea un entorno virtual (opcional pero recomendado):

```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar la aplicación

```bash
python main.py
```

### Guía detallada de uso

#### Pestaña de Configuración

En esta pestaña puedes configurar los parámetros básicos del bot:

1. **Configuración del Mercado**:

   - Selecciona el exchange (por defecto: Binance)
   - Introduce el par de trading (por defecto: BTC/USDT)
   - Selecciona el timeframe (por defecto: 1h)

2. **Configuración de Indicadores**:

   - Selecciona el tipo de Media Móvil (EMA o SMA)
   - Configura períodos para las Medias Móviles rápida y lenta
   - Configura parámetros del RSI (período, niveles de sobrecompra/sobreventa)
   - Configura parámetros de las Bandas de Bollinger

3. **Gestión de Riesgos**:

   - Configura el porcentaje de riesgo por operación

4. **Aplicar Configuración**:
   - Haz clic en "Aplicar Configuración" para guardar los cambios
   - Puedes restablecer a valores por defecto con "Restablecer por Defecto"

#### Pestaña de Backtesting

Prueba tu estrategia con datos históricos:

1. **Configuración del Backtest**:

   - Selecciona un rango de fechas predefinido o personalizado
   - Establece el capital inicial para la simulación

2. **Ejecutar Backtest**:

   - Haz clic en "Ejecutar Backtest" y espera a que finalice

3. **Análisis de Resultados**:
   - Revisa el resumen con métricas clave (retorno total, win rate, etc.)
   - Examina el gráfico de precios con señales de compra/venta
   - Consulta la tabla de operaciones realizadas
   - Analiza métricas avanzadas como ratio de Sharpe, drawdown, etc.

#### Pestaña de Optimización

Encuentra los mejores parámetros para tu estrategia:

1. **Configuración de la Optimización**:

   - Selecciona el período de tiempo para optimizar
   - Marca los parámetros que deseas optimizar
   - Establece los rangos de valores a probar para cada parámetro

2. **Iniciar Optimización**:

   - Haz clic en "Iniciar Optimización" (puede tardar varios minutos)

3. **Resultados de la Optimización**:
   - Revisa la tabla con todas las combinaciones probadas
   - Los mejores parámetros aparecerán resaltados
   - Haz clic en "Aplicar Mejores Parámetros" para actualizar la configuración del bot

#### Pestaña de Trading en Vivo

Ejecuta el bot en tiempo real o simulación:

1. **Modo de Operación**:

   - Selecciona "Simulación" para operar sin realizar transacciones reales
   - Selecciona "Trading en Vivo" para operar con dinero real (¡precaución!)

2. **Intervalo de Actualización**:

   - Configura cada cuántos segundos el bot consultará nuevos datos

3. **Control del Bot**:

   - Haz clic en "Iniciar Bot" para comenzar
   - Haz clic en "Detener Bot" para finalizar

4. **Monitoreo**:
   - Observa el registro de actividad en tiempo real
   - Controla las operaciones ejecutadas
   - Visualiza el gráfico de precios actualizado
   - Monitorea los valores actuales de los indicadores

#### Pestaña de Dashboard

Visualiza estadísticas y rendimiento:

1. **Resumen de Trading**:

   - Balance actual y P&L (diario y total)
   - Tasa de victoria y estadísticas de operaciones

2. **Período de Análisis**:

   - Selecciona diferentes períodos para analizar el rendimiento

3. **Curva de Equity**:

   - Visualiza la evolución de tu capital en el tiempo

4. **Historial de Operaciones**:
   - Consulta todas tus operaciones realizadas con sus resultados

## Activación de Operaciones Reales

Por seguridad, las operaciones en tiempo real están desactivadas por defecto. Para activarlas:

1. Abre el archivo `trading_bot/bot.py`
2. Busca el método `execute_trade()`
3. Descomenta las líneas comentadas que contienen:

   ```python
   # self.exchange.create_market_buy_order(self.symbol, position_size)
   ```

   y

   ```python
   # self.exchange.create_market_sell_order(self.symbol, position_size)
   ```

4. Guarda los cambios

**ADVERTENCIA**: Al activar estas líneas, el bot realizará operaciones reales con tu dinero cuando se ejecute en modo de Trading en Vivo. Asegúrate de entender completamente cómo funciona el bot antes de activar esta función.

## Solución de problemas comunes

### Error al conectar con el exchange

Si tienes problemas para conectarte a un exchange:

1. Verifica tu conexión a internet
2. Comprueba que el exchange esté disponible y operativo
3. Si estás intentando operaciones reales, asegúrate de proporcionar credenciales válidas de API

### Error "No hay datos para hacer backtest"

Este error puede ocurrir por las siguientes razones:

1. El período seleccionado es demasiado reciente y no hay datos disponibles
2. El par de trading seleccionado no tiene datos históricos suficientes
3. Problema de conexión con el exchange

### El bot no genera señales de trading

Posibles soluciones:

1. Verifica los parámetros de la estrategia, es posible que sean demasiado restrictivos
2. Prueba con un timeframe diferente
3. Asegúrate de que el mercado elegido tenga suficiente volatilidad

## Estructura del Proyecto

```
trading-bot/
│
├── requirements.txt                # Dependencias del proyecto
├── main.py                         # Punto de entrada principal
├── crypto_bot_gui.py               # Clase principal de la interfaz gráfica
├── trading_bot/                    # Módulo del bot de trading
│   ├── __init__.py
│   ├── bot.py                      # La clase CryptoTradingBot
│   └── utils.py                    # Funciones de utilidad
│
├── gui/                            # Módulos específicos de la interfaz
│   ├── __init__.py
│   ├── config_tab.py               # Pestaña de configuración
│   ├── backtest_tab.py             # Pestaña de backtesting
│   ├── optimize_tab.py             # Pestaña de optimización
│   ├── live_tab.py                 # Pestaña de trading en vivo
│   └── dashboard_tab.py            # Panel de control y visualización
│
└── logs/                           # Directorio para archivos de registro
```

## Personalización

El sistema está diseñado para ser fácilmente extensible:

### Añadir nuevos indicadores

Para añadir un nuevo indicador técnico (ejemplo: MACD):

1. Abre `trading_bot/bot.py`
2. Importa el indicador: `from ta.momentum import MACD`
3. Añádelo en el método `add_indicators()`:

```python
# MACD
macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_diff'] = macd.macd_diff()
```

4. Implementa una nueva señal en el mismo método:

```python
# Señal de MACD
df['macd_signal'] = np.where(
    (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 1,
    np.where((df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), -1, 0)
)
```

5. Actualiza la señal combinada:

```python
# Señal combinada
df['signal'] = df['ma_crossover'] + 0.5 * df['rsi_signal'] + 0.5 * df['bb_signal'] + 0.5 * df['macd_signal']
```

### Implementar una estrategia completamente nueva

Para implementar una estrategia diferente:

1. Crea una nueva clase derivada de `CryptoTradingBot` en un nuevo archivo
2. Sobrescribe los métodos `add_indicators()` y `execute_trade()`
3. Implementa tu lógica personalizada

### Añadir soporte para nuevos exchanges

El sistema utiliza CCXT que soporta más de 100 exchanges. Para usar un exchange específico:

1. Asegúrate de que está en la lista de exchanges soportados por CCXT
2. Para exchanges que requieren autenticación, modifica el método `__init__` en `trading_bot/bot.py`:

```python
self.exchange = getattr(ccxt, exchange_id)({
    'enableRateLimit': True,
    'apiKey': 'TU_API_KEY',
    'secret': 'TU_API_SECRET',
})
```

## Contribuciones

Las contribuciones son bienvenidas. Si deseas contribuir:

1. Haz un fork del repositorio
2. Crea una nueva rama (`git checkout -b feature/amazing-feature`)
3. Haz tus cambios
4. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
5. Haz push a la rama (`git push origin feature/amazing-feature`)
6. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo `LICENSE` para más información.

## Agradecimientos

- [CCXT](https://github.com/ccxt/ccxt) por la API para interactuar con exchanges de criptomonedas.
- [TA-Lib](https://github.com/mrjbq7/ta-lib) y [pandas-ta](https://github.com/twopirllc/pandas-ta) por los indicadores técnicos.
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) por el framework de la interfaz gráfica.
- [Matplotlib](https://matplotlib.org/) por la visualización de datos.

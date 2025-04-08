#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crypto Trading Bot con Interfaz Gráfica
---------------------------------------
Punto de entrada principal para iniciar la aplicación.

Este archivo inicia la interfaz gráfica de usuario para
el bot de trading de criptomonedas. La aplicación permite
configurar parámetros, realizar backtesting, optimizar estrategias
y ejecutar el bot en tiempo real o simulación.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from crypto_bot_gui import CryptoBotGUI

# Configurar logging
def setup_logging():
    """Configura el sistema de logging"""
    # Crear carpeta de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configuración básica
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/application.log"),
            logging.StreamHandler()
        ]
    )
    
    # Suprimir mensajes de depuración de bibliotecas externas
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

def main():
    """Función principal"""
    # Configurar logging
    setup_logging()
    
    # Inicializar aplicación
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno y consistente
    
    # Establecer hoja de estilo
    style_sheet = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    QTabWidget::pane {
        border: 1px solid #cccccc;
        background-color: #ffffff;
    }
    QTabWidget::tab-bar {
        alignment: center;
    }
    QTabBar::tab {
        background-color: #e8e8e8;
        border: 1px solid #cccccc;
        border-bottom-color: #ffffff;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        min-width: 8ex;
        padding: 8px 16px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        border-bottom-color: #ffffff;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 16px;
        padding-top: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
    }
    QPushButton {
        padding: 6px 12px;
        border-radius: 4px;
        border: 1px solid #cccccc;
        background-color: #f8f8f8;
    }
    QPushButton:hover {
        background-color: #e8e8e8;
    }
    QPushButton:pressed {
        background-color: #d8d8d8;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
        padding: 4px;
        border: 1px solid #cccccc;
        border-radius: 3px;
    }
    QTableWidget {
        gridline-color: #e0e0e0;
        selection-background-color: #e0f0ff;
    }
    QHeaderView::section {
        background-color: #f0f0f0;
        padding: 4px;
        border: 1px solid #cccccc;
        font-weight: bold;
    }
    QStatusBar {
        background-color: #f0f0f0;
        color: #333333;
    }
    """
    app.setStyleSheet(style_sheet)
    
    # Crear y mostrar ventana principal
    main_window = CryptoBotGUI()
    main_window.show()
    
    # Iniciar bucle de eventos
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
"""
Módulo utilitario para la configuración de logs del chatbot.
- Permite logs en consola y archivo, con formato estándar.
"""

import logging
import os

def configurar_logger(nombre: str = "chatbot", nivel: str = "INFO", ruta_log: str = "data/api.log") -> logging.Logger:
    """
    Configura y retorna un logger para el chatbot.
    Parámetros:
        nombre (str): Nombre del logger.
        nivel (str): Nivel de log ("DEBUG", "INFO", "WARNING", "ERROR").
        ruta_log (str): Ruta del archivo de log.
    Retorna:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger(nombre)
    logger.setLevel(getattr(logging, nivel.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # Handler para consola
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Handler para archivo
    if ruta_log:
        os.makedirs(os.path.dirname(ruta_log), exist_ok=True)
        fh = logging.FileHandler(ruta_log, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger 

def get_logger(nombre: str = "chatbot") -> logging.Logger:
    """
    Obtiene o crea un logger con configuración básica.
    Alias para configurar_logger para compatibilidad.
    """
    return configurar_logger(nombre)
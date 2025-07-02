"""
Módulo utilitario para la gestión de configuración del chatbot.
- Carga variables desde .env y proporciona funciones de acceso seguro.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env al importar este módulo
load_dotenv()

# Función: obtener_configuracion
def obtener_configuracion(clave: str, valor_por_defecto=None):
    """
    Obtiene el valor de una variable de entorno o retorna un valor por defecto.
    Parámetros:
        clave (str): Nombre de la variable de entorno.
        valor_por_defecto: Valor a retornar si la variable no está definida.
    Retorna:
        str | None: Valor de la variable o el valor por defecto.
    """
    return os.getenv(clave, valor_por_defecto) 
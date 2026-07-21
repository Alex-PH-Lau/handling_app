"""
Persistencia sencilla en un archivo JSON local, para que los días
introducidos y el histórico de meses no se pierdan al cerrar la app.

Los datos se guardan separados POR USUARIO (nombre introducido en la app),
para que si varias personas comparten el mismo despliegue (por ejemplo en
Streamlit Community Cloud), sus datos no se mezclen entre sí.
"""

import json
from dataclasses import asdict
from pathlib import Path

from calculo import DesgloseMensual

DATA_FILE = Path(__file__).parent / "datos_guardados.json"


def _leer_archivo() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def cargar_datos(usuario: str):
    """Devuelve (dias_mes, historico) del usuario indicado, o vacíos si no hay nada."""
    data = _leer_archivo()
    datos_usuario = data.get("usuarios", {}).get(usuario, {})

    dias_mes = datos_usuario.get("dias_mes", {})
    for info in dias_mes.values():
        info["turnos"] = [tuple(t) for t in info.get("turnos", [])]

    historico_raw = datos_usuario.get("historico", {})
    historico = {mes: DesgloseMensual(**valores) for mes, valores in historico_raw.items()}

    return dias_mes, historico


def guardar_datos(usuario: str, dias_mes: dict, historico: dict):
    """Guarda el estado del usuario indicado, sin tocar los datos de otros usuarios."""
    data = _leer_archivo()
    if "usuarios" not in data:
        data["usuarios"] = {}
    data["usuarios"][usuario] = {
        "dias_mes": dias_mes,
        "historico": {mes: asdict(d) for mes, d in historico.items()},
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def listar_usuarios() -> list:
    """Devuelve los nombres de usuario que ya tienen datos guardados."""
    data = _leer_archivo()
    return sorted(data.get("usuarios", {}).keys())

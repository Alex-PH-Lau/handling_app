"""
Persistencia sencilla en un archivo JSON local, para que los días
introducidos y el histórico de meses no se pierdan al cerrar la app.

Los datos se guardan separados POR USUARIO (nombre introducido en la app),
para que si varias personas comparten el mismo despliegue (por ejemplo en
Streamlit Community Cloud), sus datos no se mezclen entre sí.

Cada usuario tiene una contraseña sencilla para dar algo de privacidad
frente a otros compañeros. NO se guarda en texto plano: se guarda un
hash (SHA-256) junto con una sal (salt) aleatoria por usuario.

Importante: esto da privacidad informal frente a compañeros, NO es un
sistema de seguridad robusto (no hay límite de intentos, ni cifrado del
archivo, etc.). No lo uses para nada sensible.

NOTA TÉCNICA: si la carpeta del proyecto está dentro de OneDrive (o
Dropbox/Google Drive), el archivo puede quedar brevemente bloqueado
mientras se sincroniza. Por eso las funciones de lectura/escritura
reintentan varias veces antes de rendirse, en vez de fallar en silencio.
"""

import hashlib
import json
import secrets
import time
from dataclasses import asdict
from pathlib import Path

from calculo import DesgloseMensual

DATA_FILE = Path(__file__).parent / "datos_guardados.json"

_INTENTOS = 5
_ESPERA_ENTRE_INTENTOS = 0.2  # segundos


def _leer_archivo() -> dict:
    if not DATA_FILE.exists():
        return {}
    ultimo_error = None
    for _ in range(_INTENTOS):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Archivo corrupto/vacío a medio escribir: no reintentar, devolver vacío
            return {}
        except OSError as e:
            ultimo_error = e
            time.sleep(_ESPERA_ENTRE_INTENTOS)
    # Si tras varios intentos seguimos sin poder leer, lo señalamos con una
    # excepción clara en vez de devolver silenciosamente un diccionario vacío
    # (eso podría hacer parecer, por ejemplo, que una contraseña es
    # incorrecta cuando en realidad no se pudo ni leer el archivo).
    raise RuntimeError(
        f"No se pudo leer '{DATA_FILE.name}' tras varios intentos "
        f"(¿está bloqueado por OneDrive, un antivirus, u otro programa?): {ultimo_error}"
    )


def _escribir_archivo(data: dict):
    ultimo_error = None
    for _ in range(_INTENTOS):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return
        except OSError as e:
            ultimo_error = e
            time.sleep(_ESPERA_ENTRE_INTENTOS)
    raise RuntimeError(
        f"No se pudo guardar en '{DATA_FILE.name}' tras varios intentos "
        f"(¿está bloqueado por OneDrive, un antivirus, u otro programa?): {ultimo_error}"
    )


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def listar_usuarios() -> list:
    """Devuelve los nombres de usuario que ya tienen datos guardados."""
    data = _leer_archivo()
    return sorted(data.get("usuarios", {}).keys())


def usuario_existe(usuario: str) -> bool:
    data = _leer_archivo()
    return usuario in data.get("usuarios", {})


def _normalizar_respuesta(respuesta: str) -> str:
    """Para que no importe mayúsculas/minúsculas ni espacios de más."""
    return respuesta.strip().lower()


def crear_usuario(usuario: str, password: str, pregunta: str, respuesta: str):
    """Crea un usuario nuevo con su contraseña y pregunta de seguridad.
    Sobrescribe si ya existiera.

    Lanza RuntimeError si no se puede leer o escribir el archivo (para que
    la app pueda avisar claramente en vez de fallar en silencio).
    """
    data = _leer_archivo()
    if "usuarios" not in data:
        data["usuarios"] = {}
    salt = secrets.token_hex(16)
    salt_respuesta = secrets.token_hex(16)
    data["usuarios"][usuario] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "pregunta": pregunta,
        "salt_respuesta": salt_respuesta,
        "respuesta_hash": _hash_password(_normalizar_respuesta(respuesta), salt_respuesta),
        "dias_mes": {},
        "historico": {},
    }
    _escribir_archivo(data)

    # Comprobación: releemos para confirmar que de verdad se guardó bien,
    # en vez de asumir que la escritura tuvo éxito.
    releido = _leer_archivo()
    if releido.get("usuarios", {}).get(usuario, {}).get("password_hash") != data["usuarios"][usuario]["password_hash"]:
        raise RuntimeError(
            "El usuario parecía crearse pero no se guardó correctamente al releerlo. "
            "Vuelve a intentarlo."
        )


def obtener_pregunta(usuario: str):
    """Devuelve la pregunta de seguridad del usuario, o None si no existe o no la tiene."""
    data = _leer_archivo()
    info = data.get("usuarios", {}).get(usuario)
    if not info:
        return None
    return info.get("pregunta")


def verificar_respuesta(usuario: str, respuesta: str) -> bool:
    data = _leer_archivo()
    info = data.get("usuarios", {}).get(usuario)
    if not info or not info.get("respuesta_hash"):
        return False
    salt_respuesta = info.get("salt_respuesta", "")
    return _hash_password(_normalizar_respuesta(respuesta), salt_respuesta) == info.get("respuesta_hash")


def restablecer_password(usuario: str, nueva_password: str):
    """Cambia la contraseña de un usuario (tras verificar la respuesta de
    seguridad), sin tocar sus datos ni su pregunta."""
    data = _leer_archivo()
    if usuario not in data.get("usuarios", {}):
        raise RuntimeError(f"El usuario '{usuario}' no existe.")
    salt = secrets.token_hex(16)
    data["usuarios"][usuario]["salt"] = salt
    data["usuarios"][usuario]["password_hash"] = _hash_password(nueva_password, salt)
    _escribir_archivo(data)


def verificar_password(usuario: str, password: str) -> bool:
    data = _leer_archivo()
    info = data.get("usuarios", {}).get(usuario)
    if not info:
        return False
    salt = info.get("salt", "")
    return _hash_password(password, salt) == info.get("password_hash")


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
    """Guarda el estado del usuario indicado, sin tocar los datos de otros usuarios
    ni su contraseña."""
    data = _leer_archivo()
    if "usuarios" not in data:
        data["usuarios"] = {}
    if usuario not in data["usuarios"]:
        # Por seguridad, si por lo que sea no existía (no debería pasar en
        # flujo normal), lo creamos sin contraseña utilizable (no debería
        # ocurrir porque siempre se pasa por crear_usuario primero).
        data["usuarios"][usuario] = {"salt": "", "password_hash": ""}

    data["usuarios"][usuario]["dias_mes"] = dias_mes
    data["usuarios"][usuario]["historico"] = {mes: asdict(d) for mes, d in historico.items()}
    _escribir_archivo(data)


def eliminar_usuario(usuario: str):
    """Elimina por completo a un usuario (cuenta, contraseña, días e histórico).
    Esta acción no se puede deshacer."""
    data = _leer_archivo()
    if usuario in data.get("usuarios", {}):
        del data["usuarios"][usuario]
        _escribir_archivo(data)

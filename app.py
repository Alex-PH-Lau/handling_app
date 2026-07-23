from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config import Convenio
from calculo import DiaTrabajo, calcular_mes
from calendario_turnos import html_calendario_mes
from persistencia import (
    cargar_datos,
    guardar_datos,
    crear_usuario,
    verificar_password,
    usuario_existe,
    obtener_pregunta,
    verificar_respuesta,
    restablecer_password,
    eliminar_usuario,
)

MESES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

st.set_page_config(page_title="Nómina Handling", page_icon="✈️", layout="wide")

# Si tienes un logo propio, guárdalo como "logo.png" en esta misma carpeta
# y se mostrará automáticamente arriba a la izquierda.
_LOGO_PATH = Path(__file__).parent / "logo.png"
if _LOGO_PATH.exists():
    st.logo(str(_LOGO_PATH))

st.title("🧮 Calculadora de salario - Handling aeroportuario")
st.caption(
    "Basada en el V Convenio Colectivo General de asistencia en tierra en "
    "aeropuertos (BOE-A-2022-16972). Cifras 2026 estimadas — revisa "
    "`config.py` si tienes datos oficiales de Azul Handling."
)

st.session_state.setdefault("usuario", "")
st.session_state.setdefault("autenticado", False)

if st.session_state.autenticado:
    col_bienvenida, col_salir = st.columns([4, 1])
    col_bienvenida.success(f"👤 Conectado como **{st.session_state.usuario}**")
    if col_salir.button("🔒 Cambiar de usuario"):
        st.session_state.usuario = ""
        st.session_state.autenticado = False
        st.rerun()

    with st.expander("🗑️ Eliminar mi cuenta"):
        st.warning(
            "Esto borra tu cuenta, tu contraseña, tus días guardados y tu "
            "histórico. **No se puede deshacer.**"
        )
        confirmar_pass = st.text_input(
            "Escribe tu contraseña para confirmar", type="password", key="confirmar_borrado_pass"
        )
        if st.button("Eliminar mi cuenta definitivamente", type="primary"):
            try:
                password_ok = verificar_password(st.session_state.usuario, confirmar_pass)
            except RuntimeError as e:
                st.error(f"⚠️ {e}")
                password_ok = None
            if password_ok:
                eliminar_usuario(st.session_state.usuario)
                st.session_state.usuario = ""
                st.session_state.autenticado = False
                st.success("Cuenta eliminada.")
                st.rerun()
            elif password_ok is False:
                st.error("Contraseña incorrecta. No se ha eliminado nada.")

else:
    st.session_state.setdefault("modo_login", None)  # None | "login" | "nuevo"

    if st.session_state.modo_login is None:
        st.write("¿Qué quieres hacer?")
        col_a, col_b, _ = st.columns([1, 1, 3])
        if col_a.button("🔑 Iniciar sesión", type="primary"):
            st.session_state.modo_login = "login"
            st.rerun()
        if col_b.button("🆕 Usuario nuevo"):
            st.session_state.modo_login = "nuevo"
            st.rerun()

    else:
        col_login, _ = st.columns([2, 3])
        with col_login:
            if st.button("⬅️ Volver"):
                st.session_state.modo_login = None
                st.rerun()

            PREGUNTAS_SEGURIDAD = [
                "¿Cuál era el nombre de tu primera mascota?",
                "¿En qué ciudad naciste?",
                "¿Cuál es tu comida favorita?",
                "¿Cómo se llamaba tu colegio?",
                "¿Cuál es tu película favorita?",
            ]

            if st.session_state.modo_login == "nuevo":
                st.subheader("🆕 Crear cuenta nueva")
                nombre_nuevo = st.text_input("Tu nombre", key="login_nombre_nuevo")
                pass1 = st.text_input("Elige una contraseña", type="password", key="login_pass1")
                pass2 = st.text_input("Repite la contraseña", type="password", key="login_pass2")
                pregunta_elegida = st.selectbox(
                    "Pregunta de seguridad (por si olvidas la contraseña)", PREGUNTAS_SEGURIDAD, key="login_pregunta"
                )
                respuesta_seguridad = st.text_input("Tu respuesta", key="login_respuesta")
                if st.button("Crear usuario y entrar", type="primary"):
                    nombre_nuevo = nombre_nuevo.strip()
                    if not nombre_nuevo:
                        st.error("Escribe tu nombre.")
                    elif usuario_existe(nombre_nuevo):
                        st.error("Ya existe alguien con ese nombre. Usa 'Iniciar sesión' en vez de crear una cuenta nueva.")
                    elif not pass1:
                        st.error("La contraseña no puede estar vacía.")
                    elif pass1 != pass2:
                        st.error("Las dos contraseñas no coinciden.")
                    elif not respuesta_seguridad.strip():
                        st.error("Escribe una respuesta a la pregunta de seguridad.")
                    else:
                        try:
                            crear_usuario(nombre_nuevo, pass1, pregunta_elegida, respuesta_seguridad)
                        except RuntimeError as e:
                            st.error(f"⚠️ {e}")
                        else:
                            st.session_state.usuario = nombre_nuevo
                            st.session_state.autenticado = True
                            st.session_state.modo_login = None
                            st.rerun()

            else:  # modo_login == "login"
                st.subheader("🔑 Iniciar sesión")
                nombre_login = st.text_input("Tu nombre", key="login_nombre_existente")
                password_intento = st.text_input(
                    "Contraseña", type="password", key="login_password_intento"
                )
                if st.button("Entrar", type="primary"):
                    nombre_login = nombre_login.strip()
                    if not nombre_login or not usuario_existe(nombre_login):
                        st.error("No existe ninguna cuenta con ese nombre. ¿Quizá quieres 'Usuario nuevo'?")
                    else:
                        try:
                            password_ok = verificar_password(nombre_login, password_intento)
                        except RuntimeError as e:
                            st.error(f"⚠️ {e}")
                            password_ok = None
                        if password_ok:
                            st.session_state.usuario = nombre_login
                            st.session_state.autenticado = True
                            st.session_state.modo_login = None
                            st.rerun()
                        elif password_ok is False:
                            st.error("Contraseña incorrecta.")

                with st.expander("¿Olvidaste tu contraseña?"):
                    nombre_recuperar = st.text_input("Tu nombre", key="recuperar_nombre")
                    if nombre_recuperar.strip():
                        pregunta_usuario = obtener_pregunta(nombre_recuperar.strip())
                        if not usuario_existe(nombre_recuperar.strip()):
                            st.error("No existe ninguna cuenta con ese nombre.")
                        elif not pregunta_usuario:
                            st.info("Esta cuenta no tiene una pregunta de seguridad configurada.")
                        else:
                            st.write(f"**{pregunta_usuario}**")
                            respuesta_intento = st.text_input("Tu respuesta", key="recuperar_respuesta")
                            nueva_pass1 = st.text_input("Nueva contraseña", type="password", key="recuperar_pass1")
                            nueva_pass2 = st.text_input(
                                "Repite la nueva contraseña", type="password", key="recuperar_pass2"
                            )
                            if st.button("Restablecer contraseña"):
                                if not verificar_respuesta(nombre_recuperar.strip(), respuesta_intento):
                                    st.error("Respuesta incorrecta.")
                                elif not nueva_pass1:
                                    st.error("La nueva contraseña no puede estar vacía.")
                                elif nueva_pass1 != nueva_pass2:
                                    st.error("Las dos contraseñas no coinciden.")
                                else:
                                    try:
                                        restablecer_password(nombre_recuperar.strip(), nueva_pass1)
                                    except RuntimeError as e:
                                        st.error(f"⚠️ {e}")
                                    else:
                                        st.success("Contraseña restablecida. Ya puedes entrar con la nueva contraseña arriba.")


if not st.session_state.autenticado:
    st.stop()

st.session_state["usuario"] = st.session_state.usuario

# --- Barra lateral: configuración del convenio -----------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    convenio = Convenio()

    modo_precio = st.radio(
        "¿Cómo quieres fijar el precio de la hora?",
        ["Precio de la hora directamente", "A partir del salario anual (jornada completa)"],
        help=(
            "Si tu contrato es a tiempo parcial con horas variables cada mes, "
            "lo más fiable es indicar directamente el precio de la hora."
        ),
    )
    if modo_precio == "Precio de la hora directamente":
        convenio.precio_hora_manual = st.number_input(
            "Precio hora ordinaria (€/h)", min_value=0.0, value=11.86, step=0.01, format="%.2f"
        )
    else:
        convenio.salario_anual_bruto = st.number_input(
            "Salario fijo bruto anual (€)", min_value=0.0, value=convenio.salario_anual_bruto, step=100.0,
        )
        convenio.precio_hora_manual = None

    st.metric("Precio hora ordinaria", f"{convenio.precio_hora_ordinaria:.2f} €/h")

    st.divider()
    st.subheader("Pluses por hora (€)")
    convenio.horas.nocturnidad = st.number_input("Nocturnidad (€/h)", value=convenio.horas.nocturnidad)
    convenio.horas.festivo = st.number_input("Festivo (€/h)", value=convenio.horas.festivo)
    convenio.horas.domingo = st.number_input("Domingo (€/h)", value=convenio.horas.domingo)

    st.subheader("Pluses por día (€)")
    convenio.dias.transporte = st.number_input("Transporte (€/día)", value=convenio.dias.transporte)
    convenio.dias.manutencion = st.number_input("Manutención (€/día)", value=convenio.dias.manutencion)
    convenio.dias.madrugue = st.number_input("Madrugue (€/día)", value=convenio.dias.madrugue)
    convenio.dias.jornada_fraccionada = st.number_input(
        "Jornada fraccionada (€/día)", value=convenio.dias.jornada_fraccionada
    )

tab_nomina, tab_calendario = st.tabs(["💶 Nómina del mes", "📅 Calendario de descansos"])

# ============================================================================
# TAB: NÓMINA DEL MES
# ============================================================================
with tab_nomina:

    def _guardar_datos_seguro():
        try:
            guardar_datos(st.session_state["usuario"], st.session_state.dias_mes, st.session_state.historico)
        except RuntimeError as e:
            st.error(f"⚠️ No se pudo guardar: {e}")

    if st.session_state.get("_usuario_cargado") != st.session_state["usuario"]:
        try:
            _dias_cargados, _historico_cargado = cargar_datos(st.session_state["usuario"])
        except RuntimeError as e:
            st.error(f"⚠️ No se pudieron cargar tus datos guardados: {e}")
            _dias_cargados, _historico_cargado = {}, {}
        st.session_state.dias_mes = _dias_cargados
        st.session_state.historico = _historico_cargado
        st.session_state["_usuario_cargado"] = st.session_state["usuario"]

    HOY = date.today()
    AÑOS_DISPONIBLES = list(range(HOY.year - 1, HOY.year + 3))
    MINUTOS_DISPONIBLES = list(range(0, 60, 1))

    def _reset_form_state():
        st.session_state.form_dia = HOY.day
        st.session_state.form_mes = HOY.month
        st.session_state.form_anio = HOY.year
        st.session_state.form_festivo = False
        st.session_state.form_perentoria = False
        st.session_state.form_extra = 0.0
        st.session_state.form_turno_ids = []
        st.session_state.next_turno_id = 0
        st.session_state.editando = None

    def _load_dia_state(fecha_key: str):
        dia = st.session_state.dias_mes[fecha_key]
        fecha_obj = datetime.strptime(fecha_key, "%d/%m/%Y").date()
        st.session_state.form_dia = fecha_obj.day
        st.session_state.form_mes = fecha_obj.month
        st.session_state.form_anio = fecha_obj.year
        st.session_state.form_festivo = dia["es_festivo"]
        st.session_state.form_perentoria = dia["es_perentoria"]
        st.session_state.form_extra = dia["horas_extra"]
        ids = list(range(len(dia["turnos"])))
        st.session_state.form_turno_ids = ids
        st.session_state.next_turno_id = len(ids)
        for i, (hi, hf) in zip(ids, dia["turnos"]):
            h_ini, m_ini = map(int, hi.split(":"))
            h_fin, m_fin = map(int, hf.split(":"))
            st.session_state[f"turno_ini_hora_{i}"] = h_ini
            st.session_state[f"turno_ini_min_{i}"] = m_ini
            st.session_state[f"turno_fin_hora_{i}"] = h_fin
            st.session_state[f"turno_fin_min_{i}"] = m_fin
        st.session_state.editando = fecha_key

    # IMPORTANTE: cualquier cambio a los valores de los widgets del formulario
    # (form_fecha, form_festivo, ...) solo puede hacerse ANTES de que esos
    # widgets se hayan creado en esta misma ejecución. Por eso, en vez de
    # modificarlos directamente desde un botón (que se pulsa después de que
    # los widgets ya se dibujaron), marcamos una "acción pendiente" y hacemos
    # rerun(); aquí, al principio del todo del siguiente repintado, es cuando
    # se aplica de forma segura.
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None

    if st.session_state.pending_action == "reset":
        _reset_form_state()
        st.session_state.pending_action = None
    elif (
        isinstance(st.session_state.pending_action, tuple)
        and st.session_state.pending_action[0] == "load"
    ):
        _load_dia_state(st.session_state.pending_action[1])
        st.session_state.pending_action = None

    MAX_TURNOS_POR_DIA = 20

    def _asegurar_claves_turno(tid: int):
        """Garantiza que las claves de un turno existan en session_state,
        aunque ese turno no esté actualmente visible en el formulario.
        Streamlit puede 'podar' del estado las claves de widgets que no se
        renderizan en un run, así que las inicializamos siempre que falten.
        """
        if f"turno_ini_hora_{tid}" not in st.session_state:
            st.session_state[f"turno_ini_hora_{tid}"] = 6
        if f"turno_ini_min_{tid}" not in st.session_state:
            st.session_state[f"turno_ini_min_{tid}"] = 0
        if f"turno_fin_hora_{tid}" not in st.session_state:
            st.session_state[f"turno_fin_hora_{tid}"] = 14
        if f"turno_fin_min_{tid}" not in st.session_state:
            st.session_state[f"turno_fin_min_{tid}"] = 0

    for _tid in range(MAX_TURNOS_POR_DIA):
        _asegurar_claves_turno(_tid)

    if "form_dia" not in st.session_state:
        _reset_form_state()

    st.subheader("➕ Añadir / editar día")
    if st.session_state.editando:
        st.info(f"Editando el día **{st.session_state.editando}**.")

    with st.container(border=True):
        st.write("**Fecha**")
        c_dia, c_mes, c_anio = st.columns(3)
        c_dia.selectbox(
            "Día", options=list(range(1, 32)), key="form_dia", format_func=lambda d: f"{d:02d}"
        )
        c_mes.selectbox(
            "Mes", options=list(range(1, 13)), key="form_mes", format_func=lambda m: MESES_ES[m - 1]
        )
        c_anio.selectbox("Año", options=AÑOS_DISPONIBLES, key="form_anio")

        col1, col2, col3 = st.columns(3)
        col1.checkbox("¿Festivo?", key="form_festivo")
        col2.checkbox("¿Perentoria?", key="form_perentoria")
        col3.number_input("Horas extra trabajadas", min_value=0.0, step=0.5, key="form_extra")

        st.write("**Turnos del día** (añade varios si hay turno partido)")
        if not st.session_state.form_turno_ids:
            st.caption("Sin turnos añadidos. Usa el botón de abajo si trabajaste algún tramo horario.")

        for tid in list(st.session_state.form_turno_ids):
            st.caption(f"Turno {tid + 1}")
            c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 0.6])
            c1.selectbox(
                "Hora inicio", options=list(range(24)), key=f"turno_ini_hora_{tid}",
                format_func=lambda h: f"{h:02d}",
            )
            c2.selectbox(
                "Min. inicio", options=MINUTOS_DISPONIBLES, key=f"turno_ini_min_{tid}",
                format_func=lambda m: f"{m:02d}",
            )
            c3.selectbox(
                "Hora fin", options=list(range(24)), key=f"turno_fin_hora_{tid}",
                format_func=lambda h: f"{h:02d}",
            )
            c4.selectbox(
                "Min. fin", options=MINUTOS_DISPONIBLES, key=f"turno_fin_min_{tid}",
                format_func=lambda m: f"{m:02d}",
            )
            with c5:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_turno_{tid}"):
                    st.session_state.form_turno_ids.remove(tid)
                    st.rerun()

        if st.button("➕ Añadir turno"):
            new_id = st.session_state.next_turno_id
            st.session_state.form_turno_ids.append(new_id)
            st.session_state[f"turno_ini_hora_{new_id}"] = 6
            st.session_state[f"turno_ini_min_{new_id}"] = 0
            st.session_state[f"turno_fin_hora_{new_id}"] = 14
            st.session_state[f"turno_fin_min_{new_id}"] = 0
            st.session_state.next_turno_id += 1
            st.rerun()

        st.write("")
        col_guardar, col_cancelar = st.columns([1, 1])
        guardar = col_guardar.button("💾 Guardar día", type="primary")
        cancelar = col_cancelar.button("✖️ Cancelar edición") if st.session_state.editando else False

        if cancelar:
            st.session_state.pending_action = "reset"
            st.rerun()

        if guardar:
            fecha_str = f"{st.session_state.form_dia:02d}/{st.session_state.form_mes:02d}/{st.session_state.form_anio}"
            error = False
            try:
                datetime.strptime(fecha_str, "%d/%m/%Y")
            except ValueError:
                st.error(
                    f"El {st.session_state.form_dia} de {MESES_ES[st.session_state.form_mes - 1]} "
                    "no es un día válido para ese mes."
                )
                error = True

            turnos_validos = []
            if not error:
                for tid in st.session_state.form_turno_ids:
                    h_ini = st.session_state[f"turno_ini_hora_{tid}"]
                    m_ini = st.session_state[f"turno_ini_min_{tid}"]
                    h_fin = st.session_state[f"turno_fin_hora_{tid}"]
                    m_fin = st.session_state[f"turno_fin_min_{tid}"]
                    turnos_validos.append((f"{h_ini:02d}:{m_ini:02d}", f"{h_fin:02d}:{m_fin:02d}"))

                if not turnos_validos and st.session_state.form_extra <= 0:
                    st.error("Añade al menos un turno, o indica horas extra si el día solo tiene horas extra.")
                    error = True

            if not error:
                if st.session_state.editando and st.session_state.editando != fecha_str:
                    st.session_state.dias_mes.pop(st.session_state.editando, None)
                st.session_state.dias_mes[fecha_str] = {
                    "turnos": turnos_validos,
                    "es_festivo": st.session_state.form_festivo,
                    "es_perentoria": st.session_state.form_perentoria,
                    "horas_extra": st.session_state.form_extra,
                }
                st.success(f"Día {fecha_str} guardado.")
                _guardar_datos_seguro()
                st.session_state.pending_action = "reset"
                st.rerun()

    st.divider()

    # --- Lista de solo lectura -------------------------------------------
    st.subheader("📋 Días del mes")
    if not st.session_state.dias_mes:
        st.info("Todavía no has añadido ningún día.")
    else:
        fechas_ordenadas = sorted(
            st.session_state.dias_mes.keys(),
            key=lambda s: datetime.strptime(s, "%d/%m/%Y"),
        )
        for fecha_str in fechas_ordenadas:
            dia = st.session_state.dias_mes[fecha_str]
            turnos_txt = ", ".join(f"{hi}-{hf}" for hi, hf in dia["turnos"]) or "(sin turnos)"
            etiquetas = []
            if dia["es_festivo"]:
                etiquetas.append("🔴 Festivo")
            if dia["es_perentoria"]:
                etiquetas.append("⚡ Perentoria")
            if dia["horas_extra"]:
                etiquetas.append(f"➕ {dia['horas_extra']}h extra")
            etiquetas_txt = " · ".join(etiquetas)

            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                texto = f"**{fecha_str}** — {turnos_txt}"
                if etiquetas_txt:
                    texto += f"  \n{etiquetas_txt}"
                st.markdown(texto)
            with col2:
                if st.button("✏️ Editar", key=f"editar_{fecha_str}"):
                    st.session_state.pending_action = ("load", fecha_str)
                    st.rerun()
            with col3:
                if st.button("🗑️ Eliminar", key=f"eliminar_{fecha_str}"):
                    st.session_state.dias_mes.pop(fecha_str)
                    _guardar_datos_seguro()
                    st.rerun()
            st.divider()

        if st.button("🧹 Vaciar todos los días de este mes"):
            st.session_state.dias_mes = {}
            _guardar_datos_seguro()
            st.rerun()

    st.divider()

    # --- Cálculo -----------------------------------------------------------
    if st.button("💰 Calcular salario del mes", type="primary"):
        if not st.session_state.dias_mes:
            st.warning("Añade al menos un día antes de calcular.")
        else:
            dias_trabajo = []
            for fecha_str, info in st.session_state.dias_mes.items():
                fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                turnos_time = [
                    (datetime.strptime(hi, "%H:%M").time(), datetime.strptime(hf, "%H:%M").time())
                    for hi, hf in info["turnos"]
                ]
                dias_trabajo.append(DiaTrabajo(
                    fecha=fecha_obj,
                    turnos=turnos_time,
                    es_festivo=info["es_festivo"],
                    es_perentoria=info["es_perentoria"],
                    horas_extra=info["horas_extra"],
                ))

            resultado = calcular_mes(dias_trabajo, convenio)
            st.session_state["ultimo_resultado"] = resultado

            meses_detectados = {f"{d.fecha.year}-{d.fecha.month:02d}" for d in dias_trabajo}
            if len(meses_detectados) > 1:
                st.warning(
                    "Los días introducidos pertenecen a más de un mes. "
                    "Para que el cálculo de mes vencido sea correcto, usa "
                    "'Vaciar todos los días' antes de empezar un mes nuevo."
                )
            st.session_state["ultimo_mes"] = sorted(meses_detectados)[0] if meses_detectados else None

    if "ultimo_resultado" in st.session_state:
        resultado = st.session_state["ultimo_resultado"]
        mes_clave = st.session_state.get("ultimo_mes")

        st.subheader(f"📆 Devengado en {mes_clave}" if mes_clave else "📆 Devengado")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total devengado", f"{resultado.total:.2f} €")
        col2.metric("Horas totales", f"{resultado.horas_totales:.1f} h")
        col3.metric("Días trabajados", resultado.dias_trabajados)

        st.caption(
            "⚠️ Esto es lo GENERADO este mes, no lo que vas a cobrar en la cuenta. "
            "Según el convenio (art. 29), el salario base se paga este mismo mes, "
            "pero los pluses se cobran el mes siguiente (mes vencido)."
        )

        desglose = {
            "Salario base (horas ordinarias)": resultado.salario_base,
            "Horas extraordinarias (+50%)": resultado.horas_extra,
            "Horas perentorias (+75%)": resultado.horas_perentorias,
            "Plus nocturnidad": resultado.plus_nocturnidad,
            "Plus festivo": resultado.plus_festivo,
            "Plus domingo": resultado.plus_domingo,
            "Plus transporte": resultado.plus_transporte,
            "Plus manutención": resultado.plus_manutencion,
            "Plus madrugue": resultado.plus_madrugue,
            "Plus jornada fraccionada": resultado.plus_jornada_fraccionada,
        }
        df_desglose = pd.DataFrame(
            [{"Concepto": k, "Importe (€)": v} for k, v in desglose.items() if v]
        )
        st.dataframe(df_desglose, width='stretch', hide_index=True)
        st.bar_chart(df_desglose.set_index("Concepto"))

        if mes_clave:
            if st.button(f"📌 Guardar {mes_clave} en el histórico"):
                st.session_state.historico[mes_clave] = resultado
                _guardar_datos_seguro()
                st.success(f"Guardado el mes {mes_clave} en el histórico.")

    st.divider()

    # --- Histórico y cálculo de "lo que cobras en la cuenta" -----------------
    if st.session_state.historico:
        st.subheader("📅 Histórico de meses guardados")
        st.caption(
            "El 'Cobro estimado en la cuenta' de cada mes = salario base de ESE mes "
            "+ pluses devengados el mes ANTERIOR (mes vencido)."
        )

        meses_ordenados = sorted(st.session_state.historico.keys())
        filas = []
        for i, mes in enumerate(meses_ordenados):
            d = st.session_state.historico[mes]
            pluses_mes_anterior = 0.0
            if i > 0:
                mes_anterior = meses_ordenados[i - 1]
                pluses_mes_anterior = st.session_state.historico[mes_anterior].total_pluses
            cobro_estimado = round(d.salario_base + pluses_mes_anterior, 2)
            filas.append({
                "Mes": mes,
                "Salario base devengado": d.salario_base,
                "Pluses devengados (se cobrarán el mes que viene)": d.total_pluses,
                "Pluses del mes anterior (cobrados este mes)": round(pluses_mes_anterior, 2),
                "💶 Cobro estimado en la cuenta": cobro_estimado,
            })

        df_historico = pd.DataFrame(filas)
        st.dataframe(df_historico, width='stretch', hide_index=True)

        if st.button("🗑️ Borrar histórico"):
            st.session_state.historico = {}
            _guardar_datos_seguro()
            st.rerun()

# ============================================================================
# TAB: CALENDARIO DE DESCANSOS
# ============================================================================
with tab_calendario:
    st.subheader("📅 Calendario de turnos y descansos")
    st.write(
        "Patrón fijo de Azul Handling: 3 días de mañana, 3 días de tarde y "
        "3 días de descanso, y se repite cada 9 días."
    )

    primer_descanso_str = st.text_input(
        "Primer día de descanso de un bloque de 3 (DD/MM/YYYY)",
        value=date.today().strftime("%d/%m/%Y"),
        help="Indica cualquier fecha que sepas que es el PRIMER día de un bloque de 3 días de descanso.",
    )
    n_meses = st.number_input("Meses a mostrar", min_value=1, max_value=12, value=2)

    try:
        primer_descanso = datetime.strptime(primer_descanso_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        st.error("Formato de fecha incorrecto, usa DD/MM/YYYY.")
    else:
        mes_inicio_idx = primer_descanso.month - 1
        año_inicio = primer_descanso.year

        for i in range(int(n_meses)):
            total = mes_inicio_idx + i
            año = año_inicio + total // 12
            mes = total % 12 + 1
            st.markdown(f"#### {MESES_ES[mes - 1]} {año}")
            html = html_calendario_mes(año, mes, primer_descanso)
            st.markdown(html, unsafe_allow_html=True)
            st.write("")

"""
Calendario de turnos/descansos para el patrón fijo de Azul Handling:

3 días de mañana -> 3 días de tarde -> 3 días de descanso -> se repite.

El usuario indica cuál es el PRIMER día de un bloque de descanso, y a
partir de ahí se puede calcular el tipo de cualquier otro día (pasado o
futuro), ya que el patrón es cíclico con periodo 9 días.
"""

import calendar as calendar_std
from dataclasses import dataclass
from datetime import date, timedelta

CICLO_DIAS = 9

MAÑANA = "Mañana"
TARDE = "Tarde"
DESCANSO = "Descanso"

EMOJI = {MAÑANA: "🌅", TARDE: "🌇", DESCANSO: "🛌"}
COLOR = {MAÑANA: "#fde68a", TARDE: "#fdba74", DESCANSO: "#cbd5e1"}


def tipo_de_dia(fecha: date, primer_dia_descanso: date) -> str:
    """Devuelve 'Mañana', 'Tarde' o 'Descanso' para una fecha dada.

    `primer_dia_descanso` es el primer día de un bloque de 3 días de
    descanso; a partir de él, los 3 días siguientes son de mañana, los
    3 siguientes de tarde, y vuelta a empezar (patrón cíclico de 9 días).
    """
    offset = (fecha - primer_dia_descanso).days % CICLO_DIAS
    if offset in (0, 1, 2):
        return DESCANSO
    elif offset in (3, 4, 5):
        return MAÑANA
    else:
        return TARDE


@dataclass
class DiaCalendario:
    fecha: date
    tipo: str


def generar_calendario(primer_dia_descanso: date, desde: date, hasta: date):
    """Lista de DiaCalendario para cada día entre `desde` y `hasta` (incluidos)."""
    dias = []
    cursor = desde
    while cursor <= hasta:
        dias.append(DiaCalendario(cursor, tipo_de_dia(cursor, primer_dia_descanso)))
        cursor += timedelta(days=1)
    return dias


def html_calendario_mes(año: int, mes: int, primer_dia_descanso: date) -> str:
    """Genera una tabla HTML tipo calendario para un mes concreto."""
    cal = calendar_std.Calendar(firstweekday=0)  # lunes primero
    semanas = cal.monthdatescalendar(año, mes)

    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    html = ['<table style="width:100%; border-collapse:collapse; text-align:center;">']
    html.append("<tr>" + "".join(f'<th style="padding:4px;">{d}</th>' for d in dias_semana) + "</tr>")

    for semana in semanas:
        html.append("<tr>")
        for dia in semana:
            if dia.month != mes:
                html.append('<td style="padding:6px; opacity:0.25;"></td>')
                continue
            tipo = tipo_de_dia(dia, primer_dia_descanso)
            color = COLOR[tipo]
            emoji = EMOJI[tipo]
            html.append(
                f'<td style="padding:6px; background:{color}; border-radius:6px; '
                f'color:#1f2937; font-weight:600;">'
                f'{dia.day}<br><span style="font-size:0.8em;">{emoji} {tipo}</span></td>'
            )
        html.append("</tr>")

    html.append("</table>")
    return "".join(html)

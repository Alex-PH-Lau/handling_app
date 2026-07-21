"""
Lógica de cálculo de salario a partir de una lista de DÍAS trabajados.

Cada día puede tener uno o varios tramos horarios (turno partido), y
tiene atributos a nivel de día: si es festivo, si es perentorio, y
cuántas horas extra se han trabajado ese día.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, Tuple

from config import Convenio


@dataclass
class TurnoHorario:
    """Un tramo horario concreto dentro de un día (hora inicio - hora fin)."""

    fecha: date
    hora_inicio: time
    hora_fin: time

    def duracion_horas(self) -> float:
        inicio_dt = datetime.combine(self.fecha, self.hora_inicio)
        fin_dt = datetime.combine(self.fecha, self.hora_fin)
        if self.hora_fin <= self.hora_inicio:
            fin_dt += timedelta(days=1)
        return (fin_dt - inicio_dt).total_seconds() / 3600

    def horas_nocturnas(self) -> float:
        """Horas efectivas entre las 22:00 y las 06:00."""
        inicio_dt = datetime.combine(self.fecha, self.hora_inicio)
        fin_dt = datetime.combine(self.fecha, self.hora_fin)
        if self.hora_fin <= self.hora_inicio:
            fin_dt += timedelta(days=1)

        total_nocturnas = 0.0
        cursor = inicio_dt
        while cursor < fin_dt:
            dia_actual = cursor.date()
            ventanas = [
                (datetime.combine(dia_actual, time(22, 0)),
                 datetime.combine(dia_actual + timedelta(days=1), time(6, 0))),
                (datetime.combine(dia_actual - timedelta(days=1), time(22, 0)),
                 datetime.combine(dia_actual, time(6, 0))),
            ]
            paso_fin = min(fin_dt, cursor + timedelta(hours=1))
            for v_inicio, v_fin in ventanas:
                solap_inicio = max(cursor, v_inicio)
                solap_fin = min(paso_fin, v_fin)
                if solap_fin > solap_inicio:
                    total_nocturnas += (solap_fin - solap_inicio).total_seconds() / 3600
            cursor = paso_fin
        return round(total_nocturnas, 4)

    def madrugue(self) -> bool:
        return time(4, 0) <= self.hora_inicio <= time(6, 55)

    def cubre_manutencion(self) -> bool:
        inicio_dt = datetime.combine(self.fecha, self.hora_inicio)
        fin_dt = datetime.combine(self.fecha, self.hora_fin)
        if self.hora_fin <= self.hora_inicio:
            fin_dt += timedelta(days=1)
        duracion = (fin_dt - inicio_dt).total_seconds() / 3600
        if duracion < 6:
            return False
        franjas = [(time(14, 0), time(16, 0)), (time(21, 0), time(23, 0))]
        for f_inicio, f_fin in franjas:
            franja_inicio = datetime.combine(self.fecha, f_inicio)
            franja_fin = datetime.combine(self.fecha, f_fin)
            if inicio_dt <= franja_inicio and fin_dt >= franja_fin:
                return True
        return False


@dataclass
class DiaTrabajo:
    fecha: date
    turnos: List[Tuple[time, time]] = field(default_factory=list)
    es_festivo: bool = False
    es_perentoria: bool = False
    horas_extra: float = 0.0

    def _turnos_horario(self) -> List[TurnoHorario]:
        return [TurnoHorario(self.fecha, hi, hf) for hi, hf in self.turnos]

    def es_domingo(self) -> bool:
        return self.fecha.weekday() == 6

    def horas_trabajadas(self) -> float:
        return sum(t.duracion_horas() for t in self._turnos_horario())

    def horas_nocturnas_totales(self) -> float:
        return sum(t.horas_nocturnas() for t in self._turnos_horario())

    def tiene_jornada_fraccionada(self) -> bool:
        return len(self.turnos) >= 2

    def tiene_madrugue(self) -> bool:
        return any(t.madrugue() for t in self._turnos_horario())

    def tiene_manutencion(self) -> bool:
        return any(t.cubre_manutencion() for t in self._turnos_horario())

    def horarios_distintos(self):
        return set(self.turnos)


@dataclass
class DesgloseMensual:
    salario_base: float = 0.0
    plus_nocturnidad: float = 0.0
    plus_festivo: float = 0.0
    plus_domingo: float = 0.0
    horas_extra: float = 0.0
    horas_perentorias: float = 0.0
    plus_transporte: float = 0.0
    plus_manutencion: float = 0.0
    plus_madrugue: float = 0.0
    plus_jornada_fraccionada: float = 0.0
    plus_turnicidad: float = 0.0
    horas_totales: float = 0.0
    dias_trabajados: int = 0

    @property
    def total_pluses(self) -> float:
        """Todo lo que NO es el salario base de horas ordinarias.

        Según el art. 29 del convenio, estos conceptos variables se
        devengan un mes pero se COBRAN el mes siguiente.
        """
        return round(
            self.plus_nocturnidad
            + self.plus_festivo
            + self.plus_domingo
            + self.horas_extra
            + self.horas_perentorias
            + self.plus_transporte
            + self.plus_manutencion
            + self.plus_madrugue
            + self.plus_jornada_fraccionada
            + self.plus_turnicidad,
            2,
        )

    @property
    def total(self) -> float:
        """Total DEVENGADO este mes (no necesariamente lo que se cobra)."""
        return round(self.salario_base + self.total_pluses, 2)


def calcular_mes(dias: List[DiaTrabajo], convenio: Convenio,
                  aplicar_turnicidad: bool = True) -> DesgloseMensual:
    d = DesgloseMensual()
    precio_hora = convenio.precio_hora_ordinaria

    dias_trabajados = 0
    horarios_distintos_mes = set()

    for dia in dias:
        horas = dia.horas_trabajadas()
        if horas <= 0 and dia.horas_extra <= 0:
            continue
        dias_trabajados += 1
        horarios_distintos_mes |= dia.horarios_distintos()

        d.horas_totales += horas + dia.horas_extra

        # Salario base / horas perentorias (a nivel de día: o todo el día
        # se paga como perentorio, o se paga como ordinario)
        if dia.es_perentoria:
            d.horas_perentorias += horas * precio_hora * (1 + convenio.horas.perentoria_pct)
        else:
            d.salario_base += horas * precio_hora

        # Horas extra manuales (siempre con recargo de hora extra, aparte
        # de las horas del turno)
        if dia.horas_extra:
            d.horas_extra += dia.horas_extra * precio_hora * (1 + convenio.horas.extra_pct)

        # Nocturnidad (compatible con festivo/domingo/perentoria, plus aparte)
        d.plus_nocturnidad += dia.horas_nocturnas_totales() * convenio.horas.nocturnidad

        # Festivo / domingo (no acumulables entre sí)
        if dia.es_festivo:
            d.plus_festivo += horas * convenio.horas.festivo
        elif dia.es_domingo():
            d.plus_domingo += horas * convenio.horas.domingo

        # Pluses por día
        if dia.turnos:
            d.plus_transporte += convenio.dias.transporte
        if dia.tiene_manutencion():
            d.plus_manutencion += convenio.dias.manutencion
        if dia.tiene_madrugue():
            d.plus_madrugue += convenio.dias.madrugue
        if dia.tiene_jornada_fraccionada():
            d.plus_jornada_fraccionada += convenio.dias.jornada_fraccionada

    d.dias_trabajados = dias_trabajados

    # Turnicidad: según nº de horarios (inicio, fin) DISTINTOS realizados en el mes
    if aplicar_turnicidad:
        n = len(horarios_distintos_mes)
        m = convenio.mensuales
        if n >= 5:
            d.plus_turnicidad = m.turnicidad_5_o_mas
        elif n == 4:
            d.plus_turnicidad = m.turnicidad_4_turnos
        elif n == 3:
            d.plus_turnicidad = m.turnicidad_3_turnos
        elif n == 2:
            d.plus_turnicidad = m.turnicidad_2_turnos

    for campo in ("salario_base", "plus_nocturnidad", "plus_festivo",
                  "plus_domingo", "horas_extra", "horas_perentorias",
                  "plus_transporte", "plus_manutencion", "plus_madrugue",
                  "plus_jornada_fraccionada", "plus_turnicidad"):
        setattr(d, campo, round(getattr(d, campo), 2))

    return d

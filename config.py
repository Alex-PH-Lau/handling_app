"""
Configuración de pluses y parámetros del convenio.

Fuente base: V Convenio Colectivo General del sector de servicios de
asistencia en tierra en aeropuertos (BOE-A-2022-16972), artículo 28.
Cifras originales referidas a 2022.

IMPORTANTE:
- Estas cifras son las MÍNIMAS del convenio SECTORIAL. Si Azul Handling
  tiene convenio de empresa propio, las cifras reales pueden (y suelen)
  ser distintas -normalmente iguales o superiores-.
- Los valores "2026" de aquí abajo son una ESTIMACIÓN, resultado de
  aplicar los incrementos pactados en el convenio sectorial
  (+2,5% en 2023, +3% en 2024, +3% en 2025, +1% en 2026) sobre las
  cifras de 2022. Contrastar con la nómina real y ajustar aquí si hace falta.
- Todo lo que hay en este archivo se puede modificar libremente sin tocar
  el resto del código.
"""

from dataclasses import dataclass, field

# --- Jornada -----------------------------------------------------------

JORNADA_ANUAL_HORAS = 1712  # Art. 32 del convenio

# --- Salario base --------------------------------------------------------
# Percepción mínima fija bruta anual (rellenar con la cifra real de tu
# grupo/nivel profesional, o la de tu nómina si a la empresa le aplica
# otra tabla salarial).
SALARIO_ANUAL_BRUTO_DEFAULT = 18000.0


# --- Pluses por hora -------------------------------------------------------

@dataclass
class PlusesPorHora:
    nocturnidad: float = 1.59      # €/hora entre 22:00 y 06:00
    festivo: float = 2.82          # €/hora en festivo (no domingo)
    domingo: float = 2.77          # €/hora en domingo (no acumulable con festivo)
    extra_pct: float = 0.50        # recargo hora extraordinaria (sobre hora ordinaria)
    perentoria_pct: float = 0.75   # recargo hora perentoria (sobre hora ordinaria)


# --- Pluses por día -------------------------------------------------------

@dataclass
class PlusesPorDia:
    transporte: float = 2.80       # €/día trabajado
    manutencion: float = 6.37      # €/día si el turno cubre 14-16h o 21-23h y jornada continua >= 6h
    madrugue: float = 6.37         # €/día si el turno empieza entre las 4:00 y las 6:55
    jornada_fraccionada: float = 11.22  # €/día si se trabaja en 2 tramos horarios


@dataclass
class Convenio:
    jornada_anual_horas: int = JORNADA_ANUAL_HORAS
    salario_anual_bruto: float = SALARIO_ANUAL_BRUTO_DEFAULT
    precio_hora_manual: float = None  # si se indica, tiene prioridad sobre el cálculo anual
    horas: PlusesPorHora = field(default_factory=PlusesPorHora)
    dias: PlusesPorDia = field(default_factory=PlusesPorDia)

    @property
    def precio_hora_ordinaria(self) -> float:
        if self.precio_hora_manual is not None:
            return self.precio_hora_manual
        return self.salario_anual_bruto / self.jornada_anual_horas


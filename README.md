# Calculadora de nómina - Handling aeroportuario

App para calcular el salario mensual según horas trabajadas y pluses del
V Convenio Colectivo General de asistencia en tierra en aeropuertos, más
un calendario de turnos/descansos para el patrón fijo de Azul Handling.

## Uso en local (tu propio ordenador)

```bash
cd ryanair_nomina
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Se abrirá en el navegador (normalmente http://localhost:8501).

## 🌐 Compartir la app con tus compañeros (Streamlit Community Cloud)

Esto permite que tus compañeros usen la app solo con un enlace, sin
instalar nada. Son 3 pasos:

### Paso 1: Crear un repositorio en GitHub

1. Ve a [github.com](https://github.com) y crea una cuenta gratuita si no
   tienes una.
2. Pulsa el botón verde "New" (o "+" arriba a la derecha → "New repository").
3. Ponle un nombre, por ejemplo `nomina-handling`. Puede ser público o
   privado (ambos funcionan con Streamlit Cloud).
4. Sube estos archivos al repositorio. La forma más sencilla, sin usar
   `git` desde terminal:
   - En la página del repo recién creado, pulsa "uploading an existing file"
   - Arrastra TODOS los archivos de esta carpeta (`app.py`, `config.py`,
     `calculo.py`, `calendario_turnos.py`, `persistencia.py`,
     `requirements.txt`, `.gitignore`) — **no subas** `datos_guardados.json`
     si ya se hubiera generado en local.
   - Pulsa "Commit changes"

### Paso 2: Desplegar en Streamlit Community Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión
   con tu cuenta de GitHub (botón "Continue with GitHub").
2. Pulsa "Create app" (o "New app").
3. Selecciona tu repositorio (`nomina-handling`), la rama (`main`) y el
   archivo principal: `app.py`.
4. Pulsa "Deploy". Tardará 1-2 minutos en instalar las dependencias y
   arrancar.

### Paso 3: Compartir el enlace

Streamlit te dará una URL parecida a:
`https://tu-usuario-nomina-handling.streamlit.app`

Pásasela a tus compañeros — eso es todo, solo necesitan esa URL y un
navegador.

## ⚠️ Importante: varias personas usando la misma app compartida

Todos vuestros compañeros van a compartir el MISMO despliegue (la misma
URL). Para que los datos de cada persona no se mezclen ni sean visibles
para los demás:

- La primera vez, cada persona elige "(nuevo usuario)", escribe su
  nombre, una contraseña, y elige/responde una pregunta de seguridad
  (por si la olvida).
- Las siguientes veces, elige su nombre del desplegable e introduce su
  contraseña para entrar y recuperar sus datos.
- Si olvida la contraseña, en el desplegable "¿Olvidaste tu
  contraseña?" puede responder su pregunta de seguridad y poner una
  nueva contraseña, sin perder ninguno de sus datos guardados.
- La contraseña y la respuesta de seguridad NO se guardan en texto
  plano (se guarda un hash SHA-256 con una sal aleatoria cada uno),
  pero **no es un sistema de seguridad robusto**: no hay límite de
  intentos, ni cifrado del archivo de datos en sí. Es suficiente para
  privacidad informal entre compañeros de confianza, pero no lo uses
  para nada sensible.

## Actualizar la app tras cambios

Si en el futuro cambias algo del código, solo tienes que subir el archivo
actualizado al repositorio de GitHub (mismo botón de "uploading a file" o
`git push` si usas git). Streamlit Community Cloud detecta el cambio y
redespliega automáticamente en menos de un minuto.

## Archivos

- `config.py` — Cifras y parámetros del convenio (100% editables).
- `calculo.py` — Lógica de cálculo por DÍAS trabajados (turnos múltiples,
  festivo/perentoria/horas extra a nivel de día).
- `calendario_turnos.py` — Genera el calendario de turnos mañana/tarde/
  descanso según el patrón fijo de 9 días de Azul Handling.
- `persistencia.py` — Guarda/carga los días y el histórico de cada
  usuario en `datos_guardados.json`.
- `app.py` — Interfaz Streamlit con dos pestañas:
  - **💶 Nómina del mes**: formulario para añadir un día cada vez (con
    sus turnos, festivo, perentoria y horas extra), lista de días
    guardados (solo lectura, con botón "Editar" explícito), cálculo del
    desglose y del histórico mes vencido.
  - **📅 Calendario de descansos**: indicas el primer día de un bloque
    de 3 días de descanso, y genera el calendario de los próximos meses
    marcando mañana/tarde/descanso.
- `requirements.txt` — Dependencias necesarias (para instalar en local o
  para que Streamlit Cloud sepa qué instalar).

## Cómo funciona el formulario de días

1. Escribe tu nombre arriba (la primera vez) o elígelo del desplegable.
2. Rellena la fecha con los 3 desplegables (Día/Mes/Año), marca
   festivo/perentoria si aplica, pon horas extra si las hubo, y añade
   uno o varios turnos con "➕ Añadir turno" (usa varios si es partido).
3. Pulsa "💾 Guardar día" y aparece en la lista de abajo.
4. La lista NO es editable directamente: para modificar un día ya
   guardado, pulsa su botón "✏️ Editar" o "🗑️ Eliminar" para borrarlo.
5. Cuando tengas todos los días del mes, pulsa "💰 Calcular salario del
   mes".

## Mes vencido (importante)

Según el art. 29 del convenio, el salario base de horas ordinarias se
paga ese mismo mes, pero los PLUSES (nocturnidad, festivos, extras,
transporte, etc.) se devengan un mes y se cobran al siguiente ("mes
vencido"). La app:

1. Al pulsar "Calcular", muestra lo DEVENGADO ese mes (no lo que entra
   en la cuenta).
2. Puedes "Guardar" cada mes en un histórico.
3. La tabla de histórico calcula el "Cobro estimado en la cuenta" de
   cada mes = salario base de ese mes + pluses devengados el mes
   anterior.
4. Usa "🧹 Vaciar todos los días de este mes" antes de empezar a
   introducir un mes nuevo.

## Calendario de descansos

El patrón de Azul Handling es cíclico cada 9 días: 3 días de mañana, 3
de tarde, 3 de descanso. Solo necesitas indicar una fecha que sepas que
es el PRIMER día de un bloque de descanso, y la app calcula el resto
(pasado y futuro) automáticamente.

## 🎨 Personalizar el estilo (colores, logo, tipografía)

- **Colores**: edita `.streamlit/config.toml`. Los 4 valores (`primaryColor`,
  `backgroundColor`, `secondaryBackgroundColor`, `textColor`) son códigos
  hexadecimales — puedes sacarlos de cualquier "color picker" online.
  Streamlit Cloud detecta este archivo automáticamente al desplegar.
- **Logo**: guarda tu imagen como `logo.png` en esta misma carpeta (junto
  a `app.py`) y aparecerá automáticamente arriba a la izquierda — no hay
  que tocar código. Si no subes ninguna, la app funciona igual sin logo.
- **Icono de la pestaña / título**: en `app.py`, la línea
  `st.set_page_config(page_title=..., page_icon=...)` — puedes poner
  cualquier emoji como icono, o la ruta a una imagen.
- **Tipografía/CSS más específico**: se puede inyectar CSS personalizado
  con `st.markdown("<style>...</style>", unsafe_allow_html=True)` en
  cualquier punto de `app.py`. Útil para una fuente concreta de Google
  Fonts, sombras, bordes redondeados, etc.

## Próximas mejoras posibles

- Añadir una contraseña sencilla por usuario si preocupa la privacidad
- Comparar el cálculo de la app contra tu nómina real (verificación)
- Añadir plus de antigüedad si aplica
- Exportar el desglose a PDF/Excel

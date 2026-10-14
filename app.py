"""
app.py — Interfaz web de Match Music (Streamlit).

Esta capa SOLO se ocupa de:
    1. Recoger las preferencias del usuario.
    2. Llamar al motor:            src.engine.recomendar(entrada)
    3. Formatear el resultado:     src.tracer.presentar(resultado, catalogo)
    4. Dibujar recomendaciones, explicación y caso "sin coincidencia".

No contiene reglas ni lógica de recomendación (separación exigida en Pautas §6.2).

Ejecutar desde la raíz del repo:   streamlit run app.py
"""

import base64
from html import escape
from pathlib import Path

import streamlit as st

from src.engine import ERAS, PAIS_LOCAL, cargar_catalogo, recomendar
from src.tracer import NIVELES, agrupar_por_nivel, legible, mapa_legible, presentar

RAIZ = Path(__file__).resolve().parent
RUTA_LOGO = RAIZ / "assets" / "logo.png"

st.set_page_config(
    page_title="Match Music",
    page_icon=str(RUTA_LOGO),
    layout="wide",
    initial_sidebar_state="auto",
)


# ═══════════════════════════════════════════════════════════════════════════
# RECURSOS (cacheados: se cargan una sola vez por sesión del servidor)
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data
def catalogo():
    return cargar_catalogo()


@st.cache_data
def logo_base64():
    return base64.b64encode(RUTA_LOGO.read_bytes()).decode()


CATALOGO = catalogo()
MAPA = mapa_legible(CATALOGO)

# Opciones de los selectores, derivadas del catálogo (no hardcodeadas).
OPCIONES_ESTILO = sorted({c["genero"].capitalize() for c in CATALOGO}
                         | {c["subgenero"].capitalize() for c in CATALOGO})
OPCIONES_PAIS = sorted({c["pais"] for c in CATALOGO})
OPCIONES_IDIOMA = sorted({c["idioma"].capitalize() for c in CATALOGO})
CUALQUIERA = "Cualquiera"


# ═══════════════════════════════════════════════════════════════════════════
# ESTILOS (paleta y tipografía tomadas del logo del Brief)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;500;700;800&display=swap');

:root{
  --rojo:#E30613; --amarillo:#FFD400; --negro:#000000; --blanco:#FFFFFF;
  --gris:#6B6459; --crema:#FFF6CC;
  --borde:3px solid var(--negro);
  --sombra:5px 5px 0 var(--negro);
}

.stApp{ font-family:'Archivo', system-ui, sans-serif; }
.stApp h1,.stApp h2,.stApp h3{ font-family:'Anton', Impact, sans-serif; font-weight:400; letter-spacing:.01em; }
.block-container{ padding-top:1.6rem; max-width:1180px; }

/* ── Encabezado: el único elemento audaz de la página ───────────────────── */
.mm-hero{ position:relative; display:flex; align-items:center; gap:2.2rem;
  padding:1.4rem 0 2.6rem; flex-wrap:wrap; }
.mm-hero img{ width:min(300px, 70vw); filter:drop-shadow(6px 6px 0 rgba(0,0,0,.9)); }
.mm-hero-txt{ flex:1 1 320px; }
.mm-hero h1{ font-size:clamp(2.4rem, 5vw, 3.8rem); line-height:.95; margin:0 0 .8rem;
  transform:skewX(-8deg); transform-origin:left; color:var(--negro); }
.mm-hero p{ font-size:1.1rem; line-height:1.5; max-width:46ch; color:#222; margin:0; }
.mm-banda{ background:var(--negro); color:var(--amarillo); font-family:'Anton',sans-serif;
  font-size:1.25rem; letter-spacing:.04em; padding:.45rem 1.4rem; display:inline-block;
  transform:rotate(-3deg) skewX(-8deg); border:3px solid var(--blanco);
  outline:3px solid var(--negro); margin-top:1.3rem;
  animation:mm-entra .7s cubic-bezier(.2,.9,.3,1.3) both .15s; }
@keyframes mm-entra{ from{ transform:translateX(-40px) rotate(-3deg) skewX(-8deg); opacity:0; } }
@media (prefers-reduced-motion:reduce){ .mm-banda{ animation:none; } }

/* ── Barra lateral (amarilla, como las líneas del globo) ───────────────── */
[data-testid="stSidebar"]{ background:var(--amarillo); border-right:var(--borde); }
[data-testid="stSidebar"] h2{ font-size:1.9rem; transform:skewX(-8deg); margin-bottom:.2rem; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div{
  background:var(--blanco); border:2px solid var(--negro); border-radius:6px; }
[data-testid="stSidebar"] [data-baseweb="tag"]{ background:var(--rojo); }
[data-testid="stSidebar"] label p{ font-weight:700; }

/* ── Botones con sombra dura de sticker ────────────────────────────────── */
.stButton > button{ font-family:'Anton',sans-serif; font-size:1.05rem; letter-spacing:.03em;
  border:var(--borde); border-radius:8px; box-shadow:4px 4px 0 var(--negro);
  transition:transform .08s, box-shadow .08s; }
.stButton > button p{ font-family:'Anton',sans-serif; font-size:1.08rem; letter-spacing:.03em; }
.stButton > button:hover{ border:var(--borde); }
.stButton > button:active{ transform:translate(3px,3px); box-shadow:1px 1px 0 var(--negro); }
[data-testid="stBaseButton-primary"]{ background:var(--rojo); color:var(--blanco); }
[data-testid="stBaseButton-primary"]:hover{ background:#c00510; color:var(--blanco); }
[data-testid="stBaseButton-secondary"]{ background:var(--blanco); color:var(--negro); }
[data-testid="stBaseButton-secondary"]:hover{ background:var(--amarillo); color:var(--negro); }
.stButton > button:focus-visible{ outline:3px solid var(--rojo); outline-offset:3px; }

/* ── Pestañas ──────────────────────────────────────────────────────────── */
/* Selectores por rol ARIA: estables entre versiones de Streamlit. */
.stTabs [role="tablist"]{ gap:.4rem; border-bottom:var(--borde); box-shadow:none; }
.stTabs [role="tab"]{ padding:.45rem 1.1rem; margin:0; border:var(--borde); border-bottom:none;
  border-radius:10px 10px 0 0; background:var(--blanco); color:var(--negro); }
.stTabs [role="tab"] p{ font-family:'Anton',sans-serif; font-size:1.2rem; letter-spacing:.02em; }
.stTabs [role="tab"]:hover{ background:var(--crema); }
.stTabs [role="tab"][aria-selected="true"]{ background:var(--negro); color:var(--amarillo); }
.stTabs [role="tab"][aria-selected="true"] p{ color:var(--amarillo); }
.stTabs [role="tab"]::after,.stTabs [role="tab"]::before{ display:none; }

/* ── Titular de resultados ─────────────────────────────────────────────── */
.mm-titular{ font-family:'Anton',sans-serif; font-size:2.4rem; line-height:1; margin:.4rem 0 .6rem;
  transform:skewX(-8deg); transform-origin:left; }
.mm-criterios{ display:flex; flex-wrap:wrap; gap:.4rem; margin-bottom:1.2rem; }
.mm-criterio{ background:var(--amarillo); border:2px solid var(--negro); border-radius:999px;
  padding:.15rem .75rem; font-weight:700; font-size:.9rem; }

/* ── Tarjeta de canción ────────────────────────────────────────────────── */
.mm-card{ display:grid; grid-template-columns:auto 1fr auto; gap:1.1rem; align-items:start;
  border:var(--borde); border-radius:14px; background:var(--blanco); box-shadow:var(--sombra);
  padding:1.1rem 1.2rem; margin:0 6px 1.3rem 0; }
.mm-rank{ width:2.8rem; height:2.8rem; border-radius:50%; background:var(--rojo); color:var(--blanco);
  border:3px solid var(--negro); display:grid; place-items:center;
  font-family:'Anton',sans-serif; font-size:1.4rem; }
.mm-title{ font-family:'Anton',sans-serif; font-size:1.65rem; line-height:1.05; }
.mm-artist{ font-size:1.05rem; font-weight:700; color:var(--rojo); margin:.15rem 0 .55rem; }
.mm-meta{ display:flex; flex-wrap:wrap; gap:.35rem; margin-bottom:.7rem; }
.mm-meta span{ border:1.5px solid var(--negro); border-radius:5px; padding:.05rem .5rem; font-size:.85rem; }
.mm-motivos{ margin:0 0 .75rem; padding:0; list-style:none; }
.mm-motivos li{ padding-left:1.4rem; position:relative; margin:.2rem 0; line-height:1.4; }
.mm-motivos li::before{ content:"✓"; position:absolute; left:0; font-weight:800; color:var(--rojo); }
.mm-score{ background:var(--amarillo); border:var(--borde); border-radius:50%; width:4.6rem; height:4.6rem;
  display:grid; place-content:center; text-align:center; transform:rotate(8deg); }
.mm-score b{ font-family:'Anton',sans-serif; font-size:1.9rem; line-height:1; font-weight:400; }
.mm-score small{ font-size:.72rem; font-weight:700; }

/* ── Cadena de reglas: cada eslabón es una regla disparada ─────────────── */
.mm-cadena{ display:flex; flex-wrap:wrap; align-items:center; gap:0; }
.mm-cadena-label{ font-size:.82rem; color:var(--gris); margin-right:.5rem; }
.mm-eslabon{ font-family:'Anton',sans-serif; font-size:.85rem; letter-spacing:.03em;
  padding:.12rem .5rem; border:2px solid var(--negro); border-radius:999px; cursor:help; }
.mm-eslabon + .mm-eslabon{ margin-left:14px; position:relative; }
.mm-eslabon + .mm-eslabon::before{ content:""; position:absolute; left:-16px; top:50%;
  width:14px; border-top:2px solid var(--negro); }
.n-1A,.n-1B{ background:var(--amarillo); }
.n-2,.n-2B{ background:var(--rojo); color:var(--blanco); }
.n-3{ background:var(--negro); color:var(--amarillo); }
.n-4{ background:var(--blanco); }
.n-cierre{ background:#ddd; }

/* ── Artistas y estilos ────────────────────────────────────────────────── */
.mm-stickers{ display:flex; flex-wrap:wrap; gap:.7rem; margin:.4rem 0 1.6rem; }
.mm-sticker{ border:var(--borde); border-radius:10px; padding:.5rem .9rem; background:var(--blanco);
  box-shadow:4px 4px 0 var(--negro); }
.mm-sticker b{ font-family:'Anton',sans-serif; font-weight:400; font-size:1.2rem; display:block; }
.mm-sticker small{ color:var(--gris); }
.mm-sticker:nth-child(3n+1){ transform:rotate(-1.5deg); }
.mm-sticker:nth-child(3n+2){ transform:rotate(1deg); }

/* ── Traza ─────────────────────────────────────────────────────────────── */
.mm-tubo{ display:flex; flex-wrap:wrap; align-items:center; gap:.3rem; margin:.4rem 0 1.4rem; }
.mm-tubo span.etapa{ border:2px solid var(--negro); border-radius:8px; padding:.3rem .7rem; font-weight:700; }
.mm-tubo span.flecha{ font-weight:800; }
.mm-paso{ display:grid; grid-template-columns:3rem 3.6rem 1fr; gap:.6rem; align-items:baseline;
  padding:.35rem 0; border-bottom:1px dashed #bbb; font-size:.93rem; }
.mm-paso .num{ color:var(--gris); text-align:right; font-variant-numeric:tabular-nums; }

[data-testid="stExpander"] details{ border:2px solid var(--negro); border-radius:10px; }
[data-testid="stExpander"] summary p{ font-weight:700; }

/* ── Sin coincidencia ──────────────────────────────────────────────────── */
.mm-vacio{ border:var(--borde); border-radius:14px; background:var(--amarillo); box-shadow:var(--sombra);
  padding:1.5rem 1.6rem; margin:.6rem 6px 1.6rem 0; }
.mm-vacio h3{ font-size:1.9rem; margin:0 0 .5rem; transform:skewX(-8deg); transform-origin:left; }
.mm-vacio p{ font-size:1.08rem; margin:0 0 .4rem; max-width:62ch; }
.mm-vacio ul{ margin:.5rem 0 0; }

.mm-pie{ margin-top:3rem; padding-top:1rem; border-top:var(--borde); color:var(--gris); font-size:.88rem; }

@media (max-width:640px){
  .mm-card{ grid-template-columns:1fr auto; }
  .mm-rank{ display:none; }
  .mm-paso{ grid-template-columns:2.2rem 3.2rem 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ESTADO Y EJEMPLOS RÁPIDOS
# ═══════════════════════════════════════════════════════════════════════════

VALORES_INICIALES = {
    "f_estilos": [], "f_periodo": "Cualquiera", "f_decada": "80s", "f_anio": 1990,
    "f_pais": CUALQUIERA, "f_local": False, "f_idioma": CUALQUIERA,
}
for clave, valor in VALORES_INICIALES.items():
    st.session_state.setdefault(clave, valor)
st.session_state.setdefault("consulta", None)

# Ejemplos para probar el sistema con un clic (útiles también para la demo en video).
EJEMPLOS = {
    "Rock de los 80": {"f_estilos": ["Rock"], "f_periodo": "Una década", "f_decada": "80s"},
    "Música local en español": {"f_local": True, "f_idioma": "Español"},
    "Reggaeton": {"f_estilos": ["Reggaeton"]},
    "Synth-pop": {"f_estilos": ["Synth-pop"]},
}


def aplicar_ejemplo(nombre):
    """Carga un ejemplo en el formulario y lanza la búsqueda."""
    st.session_state.update(VALORES_INICIALES)
    st.session_state.update(EJEMPLOS[nombre])
    buscar()


def limpiar():
    st.session_state.update(VALORES_INICIALES)
    st.session_state["consulta"] = None


def entrada_desde_formulario():
    """Traduce el estado de los controles al dict que espera el motor."""
    s = st.session_state
    entrada = {"generos": s.f_estilos, "local": s.f_local}
    if s.f_periodo == "Una década":
        entrada["epoca"] = s.f_decada
    elif s.f_periodo == "Un año puntual":
        entrada["anio"] = s.f_anio
    if s.f_pais != CUALQUIERA:
        entrada["pais"] = s.f_pais
    if s.f_idioma != CUALQUIERA:
        entrada["idioma"] = s.f_idioma
    return entrada


def buscar():
    st.session_state["consulta"] = entrada_desde_formulario()


# ═══════════════════════════════════════════════════════════════════════════
# BARRA LATERAL: preferencias del usuario (Brief §7, Entradas)
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("¿Qué querés escuchar?")
    st.caption("Completá solo lo que te importe. Lo que dejes vacío no se usa.")

    st.multiselect("Estilos", OPCIONES_ESTILO, key="f_estilos",
                   placeholder="Rock, pop, reggaeton…",
                   help="Podés elegir géneros amplios o subgéneros, y combinar varios.")
    st.radio("Período", ["Cualquiera", "Una década", "Un año puntual"],
             key="f_periodo", horizontal=True)
    if st.session_state.f_periodo == "Una década":
        st.select_slider("Década", options=list(ERAS), key="f_decada")
    elif st.session_state.f_periodo == "Un año puntual":
        st.number_input("Año", min_value=1950, max_value=2026, step=1, key="f_anio",
                        help="Se buscan canciones de ese año, dos antes y dos después.")
    st.selectbox("País de origen", [CUALQUIERA] + OPCIONES_PAIS, key="f_pais")
    st.toggle(f"Priorizar música local ({legible(PAIS_LOCAL, MAPA)})", key="f_local")
    st.selectbox("Idioma del canto", [CUALQUIERA] + OPCIONES_IDIOMA, key="f_idioma")

    st.write("")
    st.button("Recomendar", type="primary", width="stretch", on_click=buscar)
    st.button("Borrar filtros", width="stretch", on_click=limpiar)


# ═══════════════════════════════════════════════════════════════════════════
# ENCABEZADO
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    f'<div class="mm-hero">'
    f'<img src="data:image/png;base64,{logo_base64()}" alt="Logo de Match Music">'
    f'<div class="mm-hero-txt">'
    f'<h1>Descubrí música que va con vos</h1>'
    f'<p>Contanos qué te gusta y te recomendamos canciones, artistas y estilos. '
    f'Cada recomendación viene con el razonamiento que la justifica.</p>'
    f'<div class="mm-banda">Recomendador, no reproductor</div>'
    f'</div></div>',
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# PIEZAS DE PRESENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def html_criterios(entrada):
    """Etiquetas con los criterios usados en la consulta."""
    chips = list(entrada.get("generos", []))
    if "epoca" in entrada:
        chips.append(f"Década {entrada['epoca']}")
    if "anio" in entrada:
        chips.append(f"Año {entrada['anio']}")
    if "pais" in entrada:
        chips.append(entrada["pais"])
    if entrada.get("local"):
        chips.append("Música local")
    if "idioma" in entrada:
        chips.append(f"Cantada en {entrada['idioma'].lower()}")
    if not chips:
        return ""
    return '<div class="mm-criterios">' + "".join(
        f'<span class="mm-criterio">{escape(str(c))}</span>' for c in chips) + "</div>"


def html_cadena(cadena):
    """Eslabones de reglas. El color indica el nivel; el tooltip, el nombre de la regla."""
    eslabones = "".join(
        f'<span class="mm-eslabon n-{r["nivel"]}" title="{escape(r["id"])}: {escape(r["nombre"])} '
        f'(nivel {escape(r["nivel"])})">{escape(r["id"])}</span>'
        for r in cadena)
    return f'<div class="mm-cadena"><span class="mm-cadena-label">Reglas aplicadas</span>{eslabones}</div>'


def html_tarjeta(posicion, rec):
    meta = [str(rec["anio"]), rec["pais"], rec["idioma"].capitalize(),
            f'{rec["genero"].capitalize()} / {rec["subgenero"]}']
    return (
        '<div class="mm-card">'
        f'<div class="mm-rank" aria-label="Puesto {posicion}">{posicion}</div>'
        '<div>'
        f'<div class="mm-title">{escape(rec["titulo"])}</div>'
        f'<div class="mm-artist">{escape(rec["artista"])}</div>'
        '<div class="mm-meta">' + "".join(f"<span>{escape(m)}</span>" for m in meta) + "</div>"
        '<ul class="mm-motivos">' + "".join(f"<li>{escape(m)}</li>" for m in rec["motivos"]) + "</ul>"
        f'{html_cadena(rec["cadena"])}'
        '</div>'
        f'<div class="mm-score"><b>{rec["puntaje"]}</b><small>puntos</small></div>'
        '</div>'
    )


def mostrar_traza(datos):
    grupos = agrupar_por_nivel(datos["traza"])
    st.markdown(
        "El motor razona en cadena: cada nivel solo trabaja con lo que dedujo el nivel anterior. "
        "Así se encadenaron las reglas en esta búsqueda:"
    )
    tubo = '<span class="flecha">→</span>'.join(
        f'<span class="etapa n-{n}" title="{escape(NIVELES[n])}">{escape(n)} ({len(p)})</span>'
        for n, p in grupos.items())
    st.markdown(f'<div class="mm-tubo">{tubo}</div>', unsafe_allow_html=True)

    for nivel, pasos in grupos.items():
        with st.expander(f"{NIVELES[nivel]} ({len(pasos)} disparos)", expanded=nivel in ("1A", "1B")):
            filas = "".join(
                f'<div class="mm-paso"><span class="num">{p["paso"]}</span>'
                f'<span class="mm-eslabon n-{p["nivel"]}" title="{escape(p["nombre"])}">{p["regla"]}</span>'
                f'<span><b>{escape(p["nombre"])}.</b> {escape(p["descripcion"])}</span></div>'
                for p in pasos)
            st.markdown(filas, unsafe_allow_html=True)

    if datos["descartes"]:
        with st.expander(f"Canciones descartadas ({len(datos['descartes'])})"):
            st.dataframe(
                [{"Canción": d["titulo"], "Motivo": d["motivo"], "Regla": d["regla"]}
                 for d in datos["descartes"]],
                hide_index=True, width="stretch",
            )


def mostrar_sin_coincidencia(datos, entrada):
    st.markdown(
        '<div class="mm-vacio">'
        '<h3>No encontramos una buena coincidencia</h3>'
        f'<p>{escape(datos["sin_coincidencia"])}</p>'
        '<ul>'
        '<li>Sacá el filtro de idioma o de período: son los que más descartan.</li>'
        '<li>Probá con un estilo más amplio (por ejemplo, «Rock» en lugar de un subgénero).</li>'
        '<li>Mirá la pestaña de razonamiento para ver qué se descartó y por qué.</li>'
        '</ul></div>',
        unsafe_allow_html=True,
    )
    if not entrada.get("generos") and len(entrada) <= 1 and not entrada.get("local"):
        st.info("No elegiste ningún criterio. Completá al menos uno en el panel de la izquierda.")


# ═══════════════════════════════════════════════════════════════════════════
# CUERPO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

entrada = st.session_state["consulta"]

if entrada is None:
    # Estado inicial: invitación a usar el sistema.
    st.markdown("### ¿No sabés por dónde empezar? Probá con un ejemplo")
    columnas = st.columns(len(EJEMPLOS))
    for col, nombre in zip(columnas, EJEMPLOS):
        col.button(nombre, width="stretch", on_click=aplicar_ejemplo, args=(nombre,))
    st.caption("O armá tu propia búsqueda en el panel de la izquierda.")

else:
    datos = presentar(recomendar(entrada, CATALOGO), CATALOGO)
    recs = datos["recomendaciones"]

    if recs:
        cantidad = "1 canción" if len(recs) == 1 else f"{len(recs)} canciones"
        st.markdown(f'<div class="mm-titular">{cantidad} para vos</div>', unsafe_allow_html=True)
    st.markdown(html_criterios(entrada), unsafe_allow_html=True)

    tab_canciones, tab_artistas, tab_razonamiento = st.tabs(
        ["Canciones", "Artistas y estilos", "Cómo llegamos acá"])

    with tab_canciones:
        if recs:
            st.markdown("".join(html_tarjeta(i, r) for i, r in enumerate(recs, start=1)),
                        unsafe_allow_html=True)
            st.caption("Pasá el cursor sobre cada regla para ver su nombre. "
                       "Amarillo: lectura y contexto. Rojo: comparación. Negro: decisión.")
        else:
            mostrar_sin_coincidencia(datos, entrada)

    with tab_artistas:
        if recs:
            canciones_por_artista = {}
            for r in recs:
                canciones_por_artista.setdefault(r["artista"], []).append(r["titulo"])
            st.markdown("### Artistas y bandas")
            st.markdown(
                '<div class="mm-stickers">' + "".join(
                    f'<div class="mm-sticker"><b>{escape(a)}</b>'
                    f'<small>{escape(", ".join(t))}</small></div>'
                    for a, t in sorted(canciones_por_artista.items())) + "</div>",
                unsafe_allow_html=True)
            st.markdown("### Estilos para explorar")
            st.markdown(
                '<div class="mm-stickers">' + "".join(
                    f'<div class="mm-sticker"><b>{escape(e["subgenero"])}</b>'
                    f'<small>dentro de {escape(e["genero"].lower())}</small></div>'
                    for e in datos["estilos"]) + "</div>",
                unsafe_allow_html=True)
        else:
            st.markdown("Sin canciones recomendadas no hay artistas ni estilos para sugerir.")

    with tab_razonamiento:
        mostrar_traza(datos)

st.markdown(
    '<div class="mm-pie">Match Music sugiere qué escuchar: no reproduce, descarga ni distribuye música. '
    'Sistema experto desarrollado por el Grupo A para el Grupo B, Análisis de Datos II, UNICABA 2026.</div>',
    unsafe_allow_html=True,
)
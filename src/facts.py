"""
facts.py — Representación del conocimiento: tipos de HECHOS de Match Music.

Cada clase hereda de experta.Fact y representa una "plantilla" de hecho de la
memoria de trabajo del motor. Se agrupan según su ORIGEN en la cadena de
inferencia:

    ┌──────────────────────┬───────────────────────────────────────────────┐
    │ Hechos de ENTRADA    │ UserPreferences, Song                         │
    │ Nivel 1 (contexto)   │ DerivedPreference                             │
    │ Nivel 2 (compatib.)  │ Coincidencia, Descarte                        │
    │ Nivel 3 (decisión)   │ Evaluacion, Recommendation                    │
    │ Nivel 4 (síntesis)   │ ArtistaRecomendado, EstiloRecomendado         │
    │ Caso sin conclusión  │ SinCoincidencia                               │
    └──────────────────────┴───────────────────────────────────────────────┘

Convención: los valores categóricos (género, país, idioma) se guardan
NORMALIZADOS (minúsculas, sin tildes) para que el pattern matching del motor
compare de forma consistente. Los textos "lindos" para mostrar se recuperan
del catálogo original por `cancion_id`.

Los campos `regla` y `origen` de los hechos derivados existen para la
TRAZABILIDAD: cada hecho sabe qué regla lo produjo y a partir de qué hecho
anterior, lo que permite reconstruir la cadena de razonamiento de cada
recomendación (requisito de explicabilidad, §6.2 y §7 de las pautas).
"""

from experta import Fact, Field


# ════════════════════════════════════════════════════════════════════════
# HECHOS DE ENTRADA
# ════════════════════════════════════════════════════════════════════════

class UserPreferences(Fact):
    """
    Preferencias expresadas por el usuario (Brief §7 — Entradas).

    Todos los campos son opcionales: el usuario completa sólo los criterios
    que le interesan. Si un campo no se declara, ninguna regla que dependa
    de él se activa (comportamiento natural del pattern matching).

    Campos posibles:
        generos  : tuple[str]  — uno o varios estilos (RF-03, RF-08)
        epoca    : str         — '60s', '70s', '80s', '90s', '2000s', '2010s', '2020s' (RF-04)
        anio     : int         — año puntual (RF-04)
        pais     : str         — país de origen (RF-05)
        local    : bool        — preferencia por música local (RF-06)
        idioma   : str         — idioma del canto (RF-07)
    """
    pass


class Song(Fact):
    """
    Una canción del catálogo (base de hechos del dominio).
    Se declara una instancia por cada entrada de data/catalog.json.
    """
    cancion_id = Field(str, mandatory=True)
    titulo = Field(str, mandatory=True)
    artista = Field(str, mandatory=True)
    genero = Field(str, mandatory=True)      # normalizado
    subgenero = Field(str, mandatory=True)   # normalizado
    anio = Field(int, mandatory=True)
    pais = Field(str, mandatory=True)        # normalizado
    idioma = Field(str, mandatory=True)      # normalizado ('instrumental' si no tiene canto)


# ════════════════════════════════════════════════════════════════════════
# NIVEL 1 — Contexto derivado de las preferencias
# ════════════════════════════════════════════════════════════════════════

class DerivedPreference(Fact):
    """
    Preferencia inferida a partir de UserPreferences (o de otra
    DerivedPreference). Es el "puente" entre lo que el usuario dijo y lo
    que el motor sabe comparar contra el catálogo.

    tipo puede ser:
        'genero'        → estilo pedido explícitamente     (valor=str)
        'genero_afin'   → estilo relacionado por afinidad  (valor=str, origen=género base)
        'rango_anios'   → período temporal                 (desde=int, hasta=int)
        'pais'          → país buscado                     (valor=str)
        'idioma'        → idioma buscado                   (valor=str)
        'contexto'      → concepto compuesto del dominio   (valor='musica_latina' | 'rock_80s')

    regla  : id de la regla que lo derivó
    cadena : tuple con todas las reglas que llevaron a este hecho,
             p.ej. ('R01', 'R07') para un género afín (trazabilidad)
    """
    tipo = Field(str, mandatory=True)
    regla = Field(str, mandatory=True)
    cadena = Field(tuple, mandatory=True)


# ════════════════════════════════════════════════════════════════════════
# NIVEL 2 — Compatibilidad canción ↔ preferencias
# ════════════════════════════════════════════════════════════════════════

class Coincidencia(Fact):
    """
    Evidencia a favor: la canción `cancion_id` cumple un criterio.
    `peso` es el aporte al puntaje de relevancia (ver PESOS en engine.py).
    `cadena` = cadena de la preferencia usada + la regla de este nivel,
    p.ej. ('R01', 'R07', 'R13').
    """
    cancion_id = Field(str, mandatory=True)
    tipo = Field(str, mandatory=True)
    detalle = Field(str, mandatory=True)
    peso = Field(int, mandatory=True)
    regla = Field(str, mandatory=True)
    cadena = Field(tuple, mandatory=True)


class Descarte(Fact):
    """
    Evidencia excluyente: la canción viola una restricción dura
    (idioma o época pedidos, o no comparte ningún estilo). Una canción
    con Descarte nunca llega a Evaluacion.
    """
    cancion_id = Field(str, mandatory=True)
    motivo = Field(str, mandatory=True)
    regla = Field(str, mandatory=True)


# ════════════════════════════════════════════════════════════════════════
# NIVEL 3 — Decisión
# ════════════════════════════════════════════════════════════════════════

class Evaluacion(Fact):
    """Puntaje consolidado de una canción candidata (suma de Coincidencias)."""
    cancion_id = Field(str, mandatory=True)
    puntaje = Field(int, mandatory=True)
    regla = Field(str, mandatory=True)


class Recommendation(Fact):
    """
    Recomendación final de una canción (RF-01), con su justificación.

    motivos : tuple[str]  — criterios del dominio que la justifican (Brief §7 "Motivo")
    cadena  : tuple[str]  — reglas disparadas en orden, p.ej. ('R01','R07','R12','R22','R23')
    """
    cancion_id = Field(str, mandatory=True)
    artista = Field(str, mandatory=True)
    genero = Field(str, mandatory=True)
    subgenero = Field(str, mandatory=True)
    puntaje = Field(int, mandatory=True)
    motivos = Field(tuple, mandatory=True)
    cadena = Field(tuple, mandatory=True)


# ════════════════════════════════════════════════════════════════════════
# NIVEL 4 — Síntesis (artistas y estilos a partir de canciones recomendadas)
# ════════════════════════════════════════════════════════════════════════

class ArtistaRecomendado(Fact):
    """Artista/banda que surge de al menos una canción recomendada (RF-02)."""
    artista = Field(str, mandatory=True)
    regla = Field(str, mandatory=True)


class EstiloRecomendado(Fact):
    """Género/subgénero que surge de las canciones recomendadas (RF-03)."""
    genero = Field(str, mandatory=True)
    subgenero = Field(str, mandatory=True)
    regla = Field(str, mandatory=True)


# ════════════════════════════════════════════════════════════════════════
# CASO SIN CONCLUSIÓN
# ════════════════════════════════════════════════════════════════════════

class SinCoincidencia(Fact):
    """Se declara sólo si el motor terminó sin ninguna Recommendation (Brief §7)."""
    mensaje = Field(str, mandatory=True)
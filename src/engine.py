"""
engine.py — Base de reglas y motor de inferencia de Match Music.

Motor: Experta (encadenamiento hacia adelante / forward chaining, algoritmo RETE).
Este módulo NO importa nada de la interfaz: la UI (Streamlit) sólo llama a
`recomendar(preferencias)` y recibe un diccionario con resultados y traza.

─────────────────────────────────────────────────────────────────────────────
ORGANIZACIÓN DE LA BASE DE REGLAS (41 reglas)
─────────────────────────────────────────────────────────────────────────────
El orden de ejecución entre niveles se garantiza con `salience` (prioridad):
una regla de mayor salience se dispara antes. Como cada nivel CONSUME hechos
producidos por el nivel anterior, el encadenamiento es real: si un nivel no
produce hechos, el siguiente no tiene nada que activar.

Las reglas R01–R27 son la versión presentada en la reunión 2 (22/10/2026).
Las reglas R00 y R28–R40 se agregaron para cubrir las observaciones del
Grupo B en esa reunión (casos CA-01, CA-02, CA-05 y CA-07). Se numeraron a
continuación para no alterar las referencias a R01–R27 en la documentación.

  Nivel 0   (sal. 100) R00           Validación: consulta sin criterios → EntradaInsuficiente
  Nivel 1A  (sal. 50)  R01–R06       Normalización de la entrada → DerivedPreference
                       R28–R29       Artista / canción de referencia → DerivedPreference
  Nivel 1B  (sal. 45)  R07–R10       Contexto compuesto del dominio → DerivedPreference
                       R30–R31       Género que contiene al subgénero pedido; subgéneros vecinos
                       R32–R34       Rasgos de la referencia y sus estilos vecinos
  Nivel 2   (sal. 30)  R11–R20       Compatibilidad canción ↔ preferencia → Coincidencia / Descarte
                       R35           Coincide un subgénero vecino del pedido
            (R13 y R35 con sal. 29: se evalúan después de las coincidencias exactas)
                       R36–R38       Similitud con la referencia → Coincidencia
                       R39–R40       Descarte de la propia referencia
  Nivel 2B  (sal. 25)  R21           Descarte por no compartir estilo
  Nivel 3   (sal. 20)  R22           Consolidación del puntaje → Evaluacion
            (sal. 15)  R23–R24       Decisión → Recommendation (o descarte por puntaje)
  Nivel 4   (sal. 10)  R25–R26       Síntesis → ArtistaRecomendado / EstiloRecomendado
  Cierre    (sal.-100) R27           Sin coincidencia suficiente → SinCoincidencia

Cadena más larga posible (6 saltos sobre hechos derivados):
  UserPreferences ─R28→ referencia ─R32→ rasgo_ref ─R34→ estilo_vecino_ref
                  ─R37→ Coincidencia ─R22→ Evaluacion ─R23→ Recommendation
                  ─R25→ ArtistaRecomendado
─────────────────────────────────────────────────────────────────────────────
"""

import json
import unicodedata
from pathlib import Path

from experta import AS, MATCH, NOT, TEST, W, DefFacts, KnowledgeEngine, Rule

from src.facts import (
    ArtistaRecomendado,
    Coincidencia,
    Descarte,
    DerivedPreference,
    EntradaInsuficiente,
    EstiloRecomendado,
    Evaluacion,
    Recommendation,
    SinCoincidencia,
    Song,
    UserPreferences,
)

RUTA_CATALOGO = Path(__file__).resolve().parent.parent / "data" / "catalog.json"


# ═══════════════════════════════════════════════════════════════════════════
# CONOCIMIENTO DEL DOMINIO (tablas de apoyo de las reglas)
# ⚠ Valores PRELIMINARES propuestos por el proveedor: deben validarse contra
#   las fuentes del Brief §9 y/o acordarse con el cliente en la reunión 2.
# ═══════════════════════════════════════════════════════════════════════════

# Eras musicales como décadas cerradas (Glosario del Brief: "Era musical").
# Desde los años 20 para poder cargar el caso límite CA-06 del cliente.
ERAS = {
    "20s": (1920, 1929), "30s": (1930, 1939), "40s": (1940, 1949),
    "50s": (1950, 1959), "60s": (1960, 1969), "70s": (1970, 1979),
    "80s": (1980, 1989), "90s": (1990, 1999), "2000s": (2000, 2009),
    "2010s": (2010, 2019), "2020s": (2020, 2029),
}

# Tolerancia al pedir un año puntual: un año se contextualiza con su entorno
# inmediato (supuesto del proveedor: ±2 años).
TOLERANCIA_ANIO = 2

# País considerado "local" (RF-06). Supuesto: usuario en Argentina.
PAIS_LOCAL = "argentina"

# Afinidad entre géneros (habilita recomendaciones "no evidentes", RF-11).
# Relación NO simétrica a propósito: se lee "a quien le gusta X, puede
# interesarle Y".
GENEROS_AFINES = {
    "rock": {"pop", "metal", "blues"},
    "pop": {"rock", "urbano latino", "electronica"},
    "urbano latino": {"pop", "cumbia"},
    "tango": {"folklore", "jazz"},
    "jazz": {"blues", "tango"},
    "metal": {"rock"},
    "blues": {"rock", "jazz"},
    "electronica": {"pop"},
    "cumbia": {"urbano latino"},
    "folklore": {"tango", "folk"},
    "folk": {"folklore", "indie"},
    "indie": {"rock", "pop", "folk"},
}

# Vecindad entre subgéneros: estilos que comparten escena, época o sonido.
# La usan dos familias de reglas: los subgéneros vecinos de un estilo pedido
# (R31, R35) y la similitud con un artista o canción de referencia (R34, R37).
SUBGENEROS_VECINOS = {
    "rock nacional": {"rock en espanol", "new wave", "pop rock"},
    "rock en espanol": {"rock nacional", "rock alternativo", "pop rock"},
    "rock alternativo": {"rock en espanol", "grunge", "indie rock"},
    "pop rock": {"rock en espanol", "rock nacional"},
    "new wave": {"synth-pop", "post-punk", "rock nacional"},
    "synth-pop": {"new wave", "dance-pop"},
    "dance-pop": {"synth-pop", "pop"},
    "hard rock": {"heavy metal", "grunge"},
    "heavy metal": {"hard rock"},
    "grunge": {"rock alternativo", "hard rock"},
    "indie rock": {"rock alternativo", "indie pop"},
    "indie pop": {"indie rock", "pop rock"},
    "folktronica": {"indie pop", "nueva cancion"},
    "nueva cancion": {"folktronica"},
    "reggaeton": {"pop latino"},
    "pop latino": {"reggaeton"},
}

# Contexto "Música latina": géneros de raíz latinoamericana y países de América Latina.
GENEROS_LATINOS = {"urbano latino", "cumbia", "salsa", "tango", "folklore", "bachata", "bolero"}
PAISES_LATINOS = {
    "argentina", "bolivia", "brasil", "chile", "colombia", "costa rica", "cuba",
    "ecuador", "el salvador", "guatemala", "honduras", "mexico", "nicaragua",
    "panama", "paraguay", "peru", "puerto rico", "republica dominicana",
    "uruguay", "venezuela",
}

# Países que se ofrecen en la interfaz además de los del catálogo: el usuario
# puede pedir un país sin canciones cargadas (caso límite CA-06) y el sistema
# debe responder "sin coincidencia" en lugar de impedir la consulta.
PAISES_CONOCIDOS = [
    "Alemania", "Argentina", "Australia", "Brasil", "Canadá", "Chile", "Colombia",
    "Corea del Sur", "Cuba", "España", "Estados Unidos", "Francia", "India", "Irlanda",
    "Italia", "Jamaica", "Japón", "México", "Noruega", "Perú", "Puerto Rico",
    "Reino Unido", "Suecia", "Uruguay",
]

# Contexto "Rock de los 80": subgéneros representativos de esa década.
SUBGENEROS_ROCK_80S = {"new wave", "hard rock", "rock nacional", "post-punk", "glam metal"}

# Pesos de cada tipo de coincidencia y umbral mínimo para recomendar.
PESOS = {
    "genero": 3, "subgenero": 3, "genero_afin": 1, "epoca": 2,
    "pais": 2, "idioma": 2, "contexto": 1,
    "similitud": 3, "similitud_vecina": 2, "idioma_ref": 1,
}
UMBRAL_MINIMO = 3

MENSAJE_SIN_COINCIDENCIA = (
    "No se encontraron recomendaciones con coincidencia suficiente para los "
    "criterios seleccionados. Modifique o amplíe los criterios de búsqueda."
)  # Texto literal exigido por el Brief §7

MENSAJE_ENTRADA_VACIA = (
    "Sin conclusión posible: Ingrese al menos un criterio (estilo, artista, "
    "década o país) para ejecutar la recomendación."
)  # Texto literal del caso CA-07 del Grupo B

# Catálogo de reglas: id → (nivel, nombre legible).
# Lo usa la traza y la interfaz; sirve también como índice para la documentación.
REGLAS = {
    "R00": ("0", "Validación de datos mínimos"),
    "R01": ("1A", "Estilos pedidos"),
    "R02": ("1A", "Era convertida en período"),
    "R03": ("1A", "Año convertido en período (±2)"),
    "R04": ("1A", "País pedido"),
    "R05": ("1A", "Música local como país local"),
    "R06": ("1A", "Idioma pedido"),
    "R07": ("1B", "Géneros afines"),
    "R08": ("1B", "Contexto latino por género"),
    "R09": ("1B", "Contexto latino por país"),
    "R10": ("1B", "Contexto rock de los 80"),
    "R11": ("2", "Coincide el género"),
    "R12": ("2", "Coincide el subgénero"),
    "R13": ("2", "Coincide un género relacionado"),
    "R14": ("2", "Coincide la época"),
    "R15": ("2", "Coincide el país"),
    "R16": ("2", "Coincide el idioma"),
    "R17": ("2", "Encaja en música latina"),
    "R18": ("2", "Encaja en rock de los 80"),
    "R19": ("2", "Descarte por idioma"),
    "R20": ("2", "Descarte por época"),
    "R21": ("2B", "Descarte por estilo"),
    "R22": ("3", "Puntaje consolidado"),
    "R23": ("3", "Recomendación emitida"),
    "R24": ("3", "Puntaje insuficiente"),
    "R25": ("4", "Artista recomendado"),
    "R26": ("4", "Estilo sugerido"),
    "R27": ("cierre", "Sin coincidencia suficiente"),
    "R28": ("1A", "Artista de referencia"),
    "R29": ("1A", "Canción de referencia"),
    "R30": ("1B", "Género que contiene al subgénero pedido"),
    "R31": ("1B", "Subgéneros vecinos del estilo pedido"),
    "R32": ("1B", "Rasgos del artista de referencia"),
    "R33": ("1B", "Rasgos de la canción de referencia"),
    "R34": ("1B", "Estilos vecinos de la referencia"),
    "R35": ("2", "Coincide un subgénero vecino"),
    "R36": ("2", "Mismo estilo que la referencia"),
    "R37": ("2", "Estilo vecino de la referencia"),
    "R38": ("2", "Mismo idioma que la referencia"),
    "R39": ("2", "Descarte: es el artista de referencia"),
    "R40": ("2", "Descarte: es la canción de referencia"),
}

# Saliences por nivel
N0, N1A, N1B, N2, N2B, N3_EVAL, N3_DEC, N4, CIERRE = 100, 50, 45, 30, 25, 20, 15, 10, -100
# Dentro del nivel 2, las coincidencias por estilo RELACIONADO (R13, R35) se evalúan
# después de las exactas (R11, R12): así no suman si la canción ya coincidió exactamente.
N2_REL = 29


def normalizar(texto):
    """Minúsculas, sin tildes ni espacios sobrantes (para comparar categorías)."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


# ═══════════════════════════════════════════════════════════════════════════
# MOTOR
# ═══════════════════════════════════════════════════════════════════════════

class MatchMusicEngine(KnowledgeEngine):

    def __init__(self, catalogo, preferencias):
        super().__init__()
        self.catalogo = catalogo          # lista de dicts (catalog.json)
        self.preferencias = preferencias  # dict ya normalizado
        self.traza = []                   # registro ordenado de reglas disparadas

    # ── Utilidad de trazabilidad ─────────────────────────────────────────
    def _trazar(self, regla, descripcion):
        """Registra un disparo. El nivel sale del catálogo REGLAS (única fuente de verdad)."""
        self.traza.append({
            "paso": len(self.traza) + 1,
            "regla": regla,
            "nivel": REGLAS[regla][0],
            "descripcion": descripcion,
        })

    # ── Hechos iniciales (se cargan en cada reset) ───────────────────────
    @DefFacts()
    def _hechos_iniciales(self):
        for c in self.catalogo:
            yield Song(
                cancion_id=c["id"], titulo=c["titulo"], artista=c["artista"],
                genero=normalizar(c["genero"]), subgenero=normalizar(c["subgenero"]),
                anio=int(c["anio"]), pais=normalizar(c["pais"]),
                idioma=normalizar(c["idioma"]),
                artista_n=normalizar(c["artista"]), titulo_n=normalizar(c["titulo"]),
            )
        yield UserPreferences(**self.preferencias)

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 0 — Validación de la entrada (caso CA-07 del cliente)
    # ═════════════════════════════════════════════════════════════════════

    # R00 — Si la consulta no trae NINGÚN criterio, no hay nada que razonar:
    #       se declara EntradaInsuficiente y se detiene el motor antes de
    #       comparar el catálogo. Cada NOT verifica la ausencia de un campo.
    @Rule(UserPreferences(),
          NOT(UserPreferences(generos=W())), NOT(UserPreferences(epoca=W())),
          NOT(UserPreferences(anio=W())), NOT(UserPreferences(pais=W())),
          NOT(UserPreferences(local=W())), NOT(UserPreferences(idioma=W())),
          NOT(UserPreferences(artista=W())), NOT(UserPreferences(cancion=W())),
          salience=N0)
    def r00_validar_entrada(self):
        self.declare(EntradaInsuficiente(mensaje=MENSAJE_ENTRADA_VACIA))
        self._trazar("R00", "La consulta no trae ningún criterio: el motor se detiene "
                            "sin evaluar el catálogo.")
        self.halt()

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 1A — Normalización de la entrada (UserPreferences → DerivedPreference)
    # ═════════════════════════════════════════════════════════════════════

    # R01 — Cada estilo pedido se convierte en una preferencia de género (RF-03, RF-08).
    @Rule(UserPreferences(generos=MATCH.generos), salience=N1A)
    def r01_generos_explicitos(self, generos):
        for g in generos:
            self.declare(DerivedPreference(tipo="genero", valor=g, regla="R01", cadena=("R01",)))
            self._trazar("R01", f"El usuario pide el estilo '{g}'.")

    # R02 — Una era (década) se traduce a un rango de años (RF-04).
    @Rule(UserPreferences(epoca=MATCH.epoca), TEST(lambda epoca: epoca in ERAS), salience=N1A)
    def r02_epoca_a_rango(self, epoca):
        desde, hasta = ERAS[epoca]
        self.declare(DerivedPreference(tipo="rango_anios", desde=desde, hasta=hasta,
                                       regla="R02", cadena=("R02",)))
        self._trazar("R02", f"La era '{epoca}' equivale al período {desde}–{hasta}.")

    # R03 — Un año puntual se amplía a un rango ±TOLERANCIA_ANIO (RF-04).
    @Rule(UserPreferences(anio=MATCH.anio), salience=N1A)
    def r03_anio_a_rango(self, anio):
        desde, hasta = anio - TOLERANCIA_ANIO, anio + TOLERANCIA_ANIO
        self.declare(DerivedPreference(tipo="rango_anios", desde=desde, hasta=hasta,
                                       regla="R03", cadena=("R03",)))
        self._trazar("R03", f"El año {anio} se contextualiza como {desde}–{hasta}.")

    # R04 — País de origen explícito (RF-05).
    @Rule(UserPreferences(pais=MATCH.pais), salience=N1A)
    def r04_pais_explicito(self, pais):
        self.declare(DerivedPreference(tipo="pais", valor=pais, regla="R04", cadena=("R04",)))
        self._trazar("R04", f"El usuario busca música de '{pais}'.")

    # R05 — "Música local" equivale al país local configurado (RF-06).
    @Rule(UserPreferences(local=True), salience=N1A)
    def r05_local_a_pais(self):
        self.declare(DerivedPreference(tipo="pais", valor=PAIS_LOCAL, regla="R05", cadena=("R05",)))
        self._trazar("R05", f"Preferencia por música local ⇒ país '{PAIS_LOCAL}'.")

    # R06 — Idioma del canto (RF-07).
    @Rule(UserPreferences(idioma=MATCH.idioma), salience=N1A)
    def r06_idioma(self, idioma):
        self.declare(DerivedPreference(tipo="idioma", valor=idioma, regla="R06", cadena=("R06",)))
        self._trazar("R06", f"El usuario busca canciones cantadas en '{idioma}'.")

    # R28 — Artista o banda de referencia: "quiero algo parecido a X" (RF-02, caso CA-02).
    @Rule(UserPreferences(artista=MATCH.a), salience=N1A)
    def r28_artista_referencia(self, a):
        self.declare(DerivedPreference(tipo="referencia", clase="artista", valor=a,
                                       regla="R28", cadena=("R28",)))
        self._trazar("R28", f"El usuario busca música parecida a la de '{a}'.")

    # R29 — Canción de referencia: "quiero algo parecido a esta canción" (RF-01, Brief §7).
    @Rule(UserPreferences(cancion=MATCH.t), salience=N1A)
    def r29_cancion_referencia(self, t):
        self.declare(DerivedPreference(tipo="referencia", clase="cancion", valor=t,
                                       regla="R29", cadena=("R29",)))
        self._trazar("R29", f"El usuario busca canciones parecidas a '{t}'.")

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 1B — Contexto compuesto (DerivedPreference → DerivedPreference)
    # Estas reglas NO leen la entrada: sólo hechos ya derivados por el 1A
    # (y, como conocimiento del dominio, la taxonomía del catálogo).
    # ═════════════════════════════════════════════════════════════════════

    # R07 — Afinidad de géneros: de un género pedido se derivan géneros afines (RF-11).
    @Rule(AS.pref << DerivedPreference(tipo="genero", valor=MATCH.g),
          TEST(lambda g: g in GENEROS_AFINES), salience=N1B)
    def r07_generos_afines(self, pref, g):
        for afin in sorted(GENEROS_AFINES[g]):
            self.declare(DerivedPreference(tipo="genero_afin", valor=afin, base=g, relacion="afin",
                                           regla="R07", cadena=pref["cadena"] + ("R07",)))
        self._trazar("R07", f"'{g}' tiene afinidad con: {', '.join(sorted(GENEROS_AFINES[g]))}.")

    # R08 — Contexto "Música latina" a partir de un género de raíz latina.
    @Rule(AS.pref << DerivedPreference(tipo="genero", valor=MATCH.g),
          TEST(lambda g: g in GENEROS_LATINOS),
          NOT(DerivedPreference(tipo="contexto", valor="musica_latina")), salience=N1B)
    def r08_contexto_latino_por_genero(self, pref, g):
        self.declare(DerivedPreference(tipo="contexto", valor="musica_latina",
                                       regla="R08", cadena=pref["cadena"] + ("R08",)))
        self._trazar("R08", f"'{g}' es de raíz latina ⇒ contexto 'Música latina'.")

    # R09 — Contexto "Música latina" a partir de un país latinoamericano.
    @Rule(AS.pref << DerivedPreference(tipo="pais", valor=MATCH.p),
          TEST(lambda p: p in PAISES_LATINOS),
          NOT(DerivedPreference(tipo="contexto", valor="musica_latina")), salience=N1B)
    def r09_contexto_latino_por_pais(self, pref, p):
        self.declare(DerivedPreference(tipo="contexto", valor="musica_latina",
                                       regla="R09", cadena=pref["cadena"] + ("R09",)))
        self._trazar("R09", f"'{p}' es un país latinoamericano ⇒ contexto 'Música latina'.")

    # R10 — Contexto "Rock de los 80": género rock + período dentro de 1980–1989.
    @Rule(AS.pg << DerivedPreference(tipo="genero", valor="rock"),
          AS.pr << DerivedPreference(tipo="rango_anios", desde=MATCH.d, hasta=MATCH.h),
          TEST(lambda d, h: d >= 1980 and h <= 1989),
          NOT(DerivedPreference(tipo="contexto", valor="rock_80s")), salience=N1B)
    def r10_contexto_rock_80s(self, pg, pr, d, h):
        self.declare(DerivedPreference(tipo="contexto", valor="rock_80s", regla="R10",
                                       cadena=pg["cadena"] + pr["cadena"] + ("R10",)))
        self._trazar("R10", f"Rock + período {d}–{h} ⇒ contexto 'Rock de los 80'.")

    # R30 — Taxonomía: si se pide un subgénero, el género que lo contiene también
    #       es relevante (quien pide 'rock nacional' acepta otro rock argentino).
    #       La pertenencia subgénero → género se toma del catálogo (caso CA-01).
    @Rule(Song(subgenero=MATCH.s, genero=MATCH.g),
          AS.pref << DerivedPreference(tipo="genero", valor=MATCH.s),
          TEST(lambda s, g: s != g),
          NOT(DerivedPreference(tipo="genero", valor=MATCH.g)),
          NOT(DerivedPreference(tipo="genero_afin", valor=MATCH.g, base=MATCH.s)),
          salience=N1B)
    def r30_genero_que_contiene(self, s, g, pref):
        self.declare(DerivedPreference(tipo="genero_afin", valor=g, base=s, relacion="padre",
                                       regla="R30", cadena=pref["cadena"] + ("R30",)))
        self._trazar("R30", f"'{s}' es un subgénero de '{g}' ⇒ '{g}' también es relevante.")

    # R31 — Subgéneros vecinos del estilo pedido (misma escena, época o sonido).
    #       Ej.: 'hard rock' es vecino de 'heavy metal' (caso CA-05).
    @Rule(AS.pref << DerivedPreference(tipo="genero", valor=MATCH.s),
          TEST(lambda s: s in SUBGENEROS_VECINOS), salience=N1B)
    def r31_subgeneros_vecinos(self, pref, s):
        for v in sorted(SUBGENEROS_VECINOS[s]):
            self.declare(DerivedPreference(tipo="subgenero_vecino", valor=v, base=s,
                                           regla="R31", cadena=pref["cadena"] + ("R31",)))
        self._trazar("R31", f"'{s}' tiene subgéneros vecinos: "
                            f"{', '.join(sorted(SUBGENEROS_VECINOS[s]))}.")

    # R32 — Rasgos del artista de referencia: cada canción suya en el catálogo
    #       aporta un perfil (subgénero + idioma) contra el cual comparar.
    @Rule(AS.ref << DerivedPreference(tipo="referencia", clase="artista", valor=MATCH.a),
          Song(artista_n=MATCH.a, subgenero=MATCH.s, idioma=MATCH.i),
          NOT(DerivedPreference(tipo="rasgo_ref", subgenero=MATCH.s, idioma=MATCH.i)),
          salience=N1B)
    def r32_rasgos_artista(self, ref, a, s, i):
        self.declare(DerivedPreference(tipo="rasgo_ref", subgenero=s, idioma=i, origen=a,
                                       regla="R32", cadena=ref["cadena"] + ("R32",)))
        self._trazar("R32", f"'{a}' hace '{s}' cantado en '{i}'.")

    # R33 — Rasgos de la canción de referencia (mismo perfil que R32, para una canción).
    @Rule(AS.ref << DerivedPreference(tipo="referencia", clase="cancion", valor=MATCH.t),
          Song(titulo_n=MATCH.t, subgenero=MATCH.s, idioma=MATCH.i),
          NOT(DerivedPreference(tipo="rasgo_ref", subgenero=MATCH.s, idioma=MATCH.i)),
          salience=N1B)
    def r33_rasgos_cancion(self, ref, t, s, i):
        self.declare(DerivedPreference(tipo="rasgo_ref", subgenero=s, idioma=i, origen=t,
                                       regla="R33", cadena=ref["cadena"] + ("R33",)))
        self._trazar("R33", f"'{t}' es '{s}' cantado en '{i}'.")

    # R34 — Estilos vecinos de cada rasgo de la referencia (similitud no evidente, RF-11).
    @Rule(AS.rasgo << DerivedPreference(tipo="rasgo_ref", subgenero=MATCH.s),
          TEST(lambda s: s in SUBGENEROS_VECINOS), salience=N1B)
    def r34_vecinos_referencia(self, rasgo, s):
        for v in sorted(SUBGENEROS_VECINOS[s]):
            self.declare(DerivedPreference(tipo="estilo_vecino_ref", valor=v, base=s,
                                           regla="R34", cadena=rasgo["cadena"] + ("R34",)))
        self._trazar("R34", f"Estilos vecinos de '{s}': {', '.join(sorted(SUBGENEROS_VECINOS[s]))}.")

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 2 — Compatibilidad (Song × DerivedPreference → Coincidencia/Descarte)
    # ═════════════════════════════════════════════════════════════════════

    def _coincidir(self, sid, tipo, detalle, regla, pref):
        self.declare(Coincidencia(cancion_id=sid, tipo=tipo, detalle=detalle, peso=PESOS[tipo],
                                  regla=regla, cadena=pref["cadena"] + (regla,)))
        self._trazar(regla, f"[{sid}] coincide por {detalle} (+{PESOS[tipo]}).")

    # R11 — La canción pertenece a un género pedido.
    @Rule(Song(cancion_id=MATCH.sid, genero=MATCH.g),
          AS.pref << DerivedPreference(tipo="genero", valor=MATCH.g), salience=N2)
    def r11_coincide_genero(self, sid, g, pref):
        self._coincidir(sid, "genero", f"género '{g}'", "R11", pref)

    # R12 — El subgénero de la canción es el estilo pedido (el usuario pidió algo específico,
    #       p.ej. 'synth-pop'). Si subgénero == género, ya lo cubre R11 (evita doble conteo).
    @Rule(Song(cancion_id=MATCH.sid, subgenero=MATCH.s, genero=MATCH.g),
          AS.pref << DerivedPreference(tipo="genero", valor=MATCH.s),
          TEST(lambda s, g: s != g), salience=N2)
    def r12_coincide_subgenero(self, sid, s, g, pref):
        self._coincidir(sid, "subgenero", f"subgénero '{s}'", "R12", pref)

    # R13 — La canción es de un género RELACIONADO con uno pedido: afín (R07) o el
    #       género que contiene al subgénero pedido (R30). Recomendación no evidente (RF-11).
    #       Sólo si ese género no fue pedido explícitamente y sin duplicar.
    @Rule(Song(cancion_id=MATCH.sid, genero=MATCH.g),
          AS.pref << DerivedPreference(tipo="genero_afin", valor=MATCH.g, base=MATCH.base),
          NOT(DerivedPreference(tipo="genero", valor=MATCH.g)),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="subgenero")),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="genero_afin")), salience=N2_REL)
    def r13_coincide_genero_afin(self, sid, g, base, pref):
        if pref.get("relacion") == "padre":
            detalle = f"género '{g}', que incluye al estilo pedido '{base}'"
        else:
            detalle = f"género '{g}', afín a '{base}'"
        self._coincidir(sid, "genero_afin", detalle, "R13", pref)

    # R14 — El año de la canción cae dentro del período pedido.
    @Rule(Song(cancion_id=MATCH.sid, anio=MATCH.a),
          AS.pref << DerivedPreference(tipo="rango_anios", desde=MATCH.d, hasta=MATCH.h),
          TEST(lambda a, d, h: d <= a <= h),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="epoca")), salience=N2)
    def r14_coincide_epoca(self, sid, a, d, h, pref):
        self._coincidir(sid, "epoca", f"año {a} dentro de {d}–{h}", "R14", pref)

    # R15 — La canción es del país pedido (o del país local).
    @Rule(Song(cancion_id=MATCH.sid, pais=MATCH.p),
          AS.pref << DerivedPreference(tipo="pais", valor=MATCH.p),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="pais")), salience=N2)
    def r15_coincide_pais(self, sid, p, pref):
        self._coincidir(sid, "pais", f"país '{p}'", "R15", pref)

    # R16 — La canción está cantada en el idioma pedido.
    @Rule(Song(cancion_id=MATCH.sid, idioma=MATCH.i),
          AS.pref << DerivedPreference(tipo="idioma", valor=MATCH.i), salience=N2)
    def r16_coincide_idioma(self, sid, i, pref):
        self._coincidir(sid, "idioma", f"idioma '{i}'", "R16", pref)

    # R17 — Contexto latino: la canción es de un país o género latino.
    @Rule(Song(cancion_id=MATCH.sid, pais=MATCH.p, genero=MATCH.g),
          AS.pref << DerivedPreference(tipo="contexto", valor="musica_latina"),
          TEST(lambda p, g: p in PAISES_LATINOS or g in GENEROS_LATINOS), salience=N2)
    def r17_coincide_contexto_latino(self, sid, p, g, pref):
        self._coincidir(sid, "contexto", "pertenencia al contexto 'Música latina'", "R17", pref)

    # R18 — Contexto rock 80s: el subgénero es representativo de esa escena.
    @Rule(Song(cancion_id=MATCH.sid, subgenero=MATCH.s),
          AS.pref << DerivedPreference(tipo="contexto", valor="rock_80s"),
          TEST(lambda s: s in SUBGENEROS_ROCK_80S), salience=N2)
    def r18_coincide_contexto_rock80s(self, sid, s, pref):
        self._coincidir(sid, "contexto", f"subgénero '{s}', representativo del rock de los 80", "R18", pref)

    # R19 — DESCARTE: el idioma pedido es una restricción dura ("respeta el idioma", RF-07).
    @Rule(Song(cancion_id=MATCH.sid, idioma=MATCH.si),
          DerivedPreference(tipo="idioma", valor=MATCH.i),
          TEST(lambda si, i: si != i),
          NOT(Descarte(cancion_id=MATCH.sid)), salience=N2)
    def r19_descarte_idioma(self, sid, si, i):
        self.declare(Descarte(cancion_id=sid, motivo=f"idioma '{si}' ≠ '{i}'", regla="R19"))
        self._trazar("R19", f"[{sid}] descartada: idioma '{si}' distinto de '{i}'.")

    # R20 — DESCARTE: el período pedido es una restricción dura ("respeta el período", RF-04).
    @Rule(Song(cancion_id=MATCH.sid, anio=MATCH.a),
          DerivedPreference(tipo="rango_anios", desde=MATCH.d, hasta=MATCH.h),
          TEST(lambda a, d, h: not (d <= a <= h)),
          NOT(Descarte(cancion_id=MATCH.sid)), salience=N2)
    def r20_descarte_epoca(self, sid, a, d, h):
        self.declare(Descarte(cancion_id=sid, motivo=f"año {a} fuera de {d}–{h}", regla="R20"))
        self._trazar("R20", f"[{sid}] descartada: año {a} fuera de {d}–{h}.")

    # R35 — La canción es de un subgénero VECINO del estilo pedido (derivado por R31).
    #       Cuenta como evidencia de estilo relacionado (mismo peso que un género afín),
    #       sin duplicar otra coincidencia de ese tipo.
    @Rule(Song(cancion_id=MATCH.sid, subgenero=MATCH.v),
          AS.pref << DerivedPreference(tipo="subgenero_vecino", valor=MATCH.v, base=MATCH.base),
          NOT(DerivedPreference(tipo="genero", valor=MATCH.v)),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="genero_afin")), salience=N2_REL)
    def r35_coincide_subgenero_vecino(self, sid, v, base, pref):
        self._coincidir(sid, "genero_afin", f"subgénero '{v}', vecino de '{base}'", "R35", pref)

    # R36 — Similitud fuerte: la canción comparte subgénero con la referencia.
    @Rule(Song(cancion_id=MATCH.sid, subgenero=MATCH.s),
          AS.pref << DerivedPreference(tipo="rasgo_ref", subgenero=MATCH.s, origen=MATCH.o),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="similitud")), salience=N2)
    def r36_mismo_estilo_referencia(self, sid, s, o, pref):
        self._coincidir(sid, "similitud", f"mismo subgénero que '{o}' ('{s}')", "R36", pref)

    # R37 — Similitud media: la canción es de un estilo vecino de la referencia (derivado por R34).
    @Rule(Song(cancion_id=MATCH.sid, subgenero=MATCH.v),
          AS.pref << DerivedPreference(tipo="estilo_vecino_ref", valor=MATCH.v, base=MATCH.base),
          NOT(DerivedPreference(tipo="rasgo_ref", subgenero=MATCH.v)),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="similitud_vecina")), salience=N2)
    def r37_estilo_vecino_referencia(self, sid, v, base, pref):
        self._coincidir(sid, "similitud_vecina",
                        f"subgénero '{v}', vecino de '{base}' de la referencia", "R37", pref)

    # R38 — Refuerzo: la canción se canta en el mismo idioma que la referencia.
    @Rule(Song(cancion_id=MATCH.sid, idioma=MATCH.i),
          AS.pref << DerivedPreference(tipo="rasgo_ref", idioma=MATCH.i),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="idioma_ref")), salience=N2)
    def r38_mismo_idioma_referencia(self, sid, i, pref):
        self._coincidir(sid, "idioma_ref", f"mismo idioma que la referencia ('{i}')", "R38", pref)

    # R39 — DESCARTE: no se recomienda al propio artista de referencia (ya lo conoce).
    @Rule(Song(cancion_id=MATCH.sid, artista_n=MATCH.a),
          DerivedPreference(tipo="referencia", clase="artista", valor=MATCH.a),
          NOT(Descarte(cancion_id=MATCH.sid)), salience=N2)
    def r39_descarte_artista_referencia(self, sid, a):
        self.declare(Descarte(cancion_id=sid, motivo=f"es del artista de referencia '{a}'", regla="R39"))
        self._trazar("R39", f"[{sid}] descartada: es del artista de referencia '{a}'.")

    # R40 — DESCARTE: no se recomienda la propia canción de referencia.
    @Rule(Song(cancion_id=MATCH.sid, titulo_n=MATCH.t),
          DerivedPreference(tipo="referencia", clase="cancion", valor=MATCH.t),
          NOT(Descarte(cancion_id=MATCH.sid)), salience=N2)
    def r40_descarte_cancion_referencia(self, sid, t):
        self.declare(Descarte(cancion_id=sid, motivo=f"es la canción de referencia '{t}'", regla="R40"))
        self._trazar("R40", f"[{sid}] descartada: es la canción de referencia.")

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 2B — Descarte por estilo (necesita que el nivel 2 haya terminado)
    # ═════════════════════════════════════════════════════════════════════

    # R21 — Si el usuario pidió estilos y la canción no comparte ninguno
    #       (ni exacto, ni subgénero, ni relacionado, ni similar a la referencia),
    #       no corresponde recomendarla (RF-03).
    @Rule(Song(cancion_id=MATCH.sid),
          Coincidencia(cancion_id=MATCH.sid),
          DerivedPreference(tipo="genero"),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="genero")),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="subgenero")),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="genero_afin")),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="similitud")),
          NOT(Coincidencia(cancion_id=MATCH.sid, tipo="similitud_vecina")),
          NOT(Descarte(cancion_id=MATCH.sid)), salience=N2B)
    def r21_descarte_sin_estilo(self, sid):
        self.declare(Descarte(cancion_id=sid, motivo="no comparte ningún estilo pedido", regla="R21"))
        self._trazar("R21", f"[{sid}] descartada: no comparte ningún estilo pedido.")

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 3 — Consolidación y decisión
    # ═════════════════════════════════════════════════════════════════════

    # R22 — Toda canción con evidencia a favor y sin descarte se evalúa:
    #       su puntaje es la suma de los pesos de sus coincidencias.
    #       (Experta no tiene "accumulate" como CLIPS/Drools: la suma se hace
    #        recorriendo la memoria de trabajo dentro de la regla.)
    @Rule(Song(cancion_id=MATCH.sid),
          Coincidencia(cancion_id=MATCH.sid),
          NOT(Descarte(cancion_id=MATCH.sid)),
          NOT(Evaluacion(cancion_id=MATCH.sid)), salience=N3_EVAL)
    def r22_evaluar(self, sid):
        puntaje = sum(c["peso"] for c in self._coincidencias(sid))
        self.declare(Evaluacion(cancion_id=sid, puntaje=puntaje, regla="R22"))
        self._trazar("R22", f"[{sid}] puntaje consolidado = {puntaje}.")

    # R23 — Si el puntaje alcanza el umbral, se emite la Recommendation con su justificación.
    @Rule(Evaluacion(cancion_id=MATCH.sid, puntaje=MATCH.p),
          TEST(lambda p: p >= UMBRAL_MINIMO),
          Song(cancion_id=MATCH.sid, artista=MATCH.a, genero=MATCH.g, subgenero=MATCH.s),
          salience=N3_DEC)
    def r23_recomendar(self, sid, p, a, g, s):
        coincidencias = self._coincidencias(sid)
        motivos = tuple(c["detalle"] for c in coincidencias)
        reglas = []
        for c in coincidencias:
            reglas.extend(r for r in c["cadena"] if r not in reglas)
        cadena = tuple(sorted(reglas)) + ("R22", "R23")
        self.declare(Recommendation(cancion_id=sid, artista=a, genero=g, subgenero=s,
                                    puntaje=p, motivos=motivos, cadena=cadena))
        self._trazar("R23", f"[{sid}] RECOMENDADA (puntaje {p} ≥ {UMBRAL_MINIMO}).")

    # R24 — Si no alcanza el umbral, la evidencia es insuficiente.
    @Rule(Evaluacion(cancion_id=MATCH.sid, puntaje=MATCH.p),
          TEST(lambda p: p < UMBRAL_MINIMO), salience=N3_DEC)
    def r24_puntaje_insuficiente(self, sid, p):
        self.declare(Descarte(cancion_id=sid, motivo=f"puntaje {p} < {UMBRAL_MINIMO}", regla="R24"))
        self._trazar("R24", f"[{sid}] descartada: puntaje {p} menor al umbral {UMBRAL_MINIMO}.")

    # ═════════════════════════════════════════════════════════════════════
    # NIVEL 4 — Síntesis: artistas y estilos (RF-02, RF-03)
    # ═════════════════════════════════════════════════════════════════════

    # R25 — Un artista con al menos una canción recomendada es un artista recomendado.
    @Rule(Recommendation(artista=MATCH.a),
          NOT(ArtistaRecomendado(artista=MATCH.a)), salience=N4)
    def r25_artista_recomendado(self, a):
        self.declare(ArtistaRecomendado(artista=a, regla="R25"))
        self._trazar("R25", f"Artista recomendado: {a}.")

    # R26 — El estilo (género/subgénero) de una canción recomendada es un estilo sugerido.
    @Rule(Recommendation(genero=MATCH.g, subgenero=MATCH.s),
          NOT(EstiloRecomendado(genero=MATCH.g, subgenero=MATCH.s)), salience=N4)
    def r26_estilo_recomendado(self, g, s):
        self.declare(EstiloRecomendado(genero=g, subgenero=s, regla="R26"))
        self._trazar("R26", f"Estilo sugerido: {g} / {s}.")

    # ═════════════════════════════════════════════════════════════════════
    # CIERRE — Caso "sin conclusión posible" (Pautas §6.3, Brief §7)
    # ═════════════════════════════════════════════════════════════════════

    # R27 — Prioridad mínima: sólo se dispara si, agotadas todas las demás
    #       reglas, no existe ninguna Recommendation.
    @Rule(UserPreferences(), NOT(Recommendation()), NOT(EntradaInsuficiente()), salience=CIERRE)
    def r27_sin_coincidencia(self):
        self.declare(SinCoincidencia(mensaje=MENSAJE_SIN_COINCIDENCIA))
        self._trazar("R27", "Ninguna canción alcanzó coincidencia suficiente.")

    # ── Auxiliar ─────────────────────────────────────────────────────────
    def _coincidencias(self, sid):
        return [f for f in self.facts.values()
                if isinstance(f, Coincidencia) and f["cancion_id"] == sid]


# ═══════════════════════════════════════════════════════════════════════════
# API PÚBLICA (lo único que usa la interfaz)
# ═══════════════════════════════════════════════════════════════════════════

def cargar_catalogo(ruta=RUTA_CATALOGO):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)["canciones"]


def preparar_preferencias(entrada):
    """Limpia la entrada de la UI: descarta vacíos y normaliza textos."""
    prefs = {}
    if entrada.get("generos"):
        prefs["generos"] = tuple(normalizar(g) for g in entrada["generos"])
    if entrada.get("epoca"):
        prefs["epoca"] = entrada["epoca"]
    if entrada.get("anio"):
        prefs["anio"] = int(entrada["anio"])
    if entrada.get("pais"):
        prefs["pais"] = normalizar(entrada["pais"])
    if entrada.get("local"):
        prefs["local"] = True
    if entrada.get("idioma"):
        prefs["idioma"] = normalizar(entrada["idioma"])
    if entrada.get("artista"):
        prefs["artista"] = normalizar(entrada["artista"])
    if entrada.get("cancion"):
        prefs["cancion"] = normalizar(entrada["cancion"])
    return prefs


def recomendar(entrada, catalogo=None):
    """
    Ejecuta el motor y devuelve un dict serializable:
        recomendaciones : list[dict] ordenada por puntaje (desc)
        artistas        : list[str]
        estilos         : list[str]
        descartes       : list[dict]
        sin_coincidencia: str | None   (R27: se evaluó y nada alcanzó el umbral)
        sin_conclusion  : str | None   (R00: no había criterios para evaluar)
        traza           : list[dict]   (paso, regla, nivel, descripcion)
    """
    catalogo = catalogo if catalogo is not None else cargar_catalogo()
    por_id = {c["id"]: c for c in catalogo}

    motor = MatchMusicEngine(catalogo, preparar_preferencias(entrada))
    motor.reset()
    motor.run()

    hechos = list(motor.facts.values())
    recs = sorted(
        (f for f in hechos if isinstance(f, Recommendation)),
        key=lambda r: (-r["puntaje"], por_id[r["cancion_id"]]["titulo"]),
    )
    sin = next((f["mensaje"] for f in hechos if isinstance(f, SinCoincidencia)), None)
    vacia = next((f["mensaje"] for f in hechos if isinstance(f, EntradaInsuficiente)), None)

    return {
        "recomendaciones": [
            {**por_id[r["cancion_id"]], "puntaje": r["puntaje"],
             "motivos": list(r["motivos"]), "cadena": list(r["cadena"])}
            for r in recs
        ],
        "artistas": sorted({f["artista"] for f in hechos if isinstance(f, ArtistaRecomendado)}),
        "estilos": sorted({f"{f['genero']} / {f['subgenero']}" for f in hechos
                           if isinstance(f, EstiloRecomendado)}),
        "descartes": [{"id": f["cancion_id"], "titulo": por_id[f["cancion_id"]]["titulo"],
                       "motivo": f["motivo"], "regla": f["regla"]}
                      for f in hechos if isinstance(f, Descarte)],
        "sin_coincidencia": sin,
        "sin_conclusion": vacia,
        "traza": motor.traza,
    }

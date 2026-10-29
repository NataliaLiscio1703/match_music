"""
casos_prueba.py — Casos de prueba oficiales del Grupo B (cliente).

Fuente: «Casos de Prueba - Match Music (Grupo B para Grupo A)», reunión 2
(22/10/2026). Cada caso tiene la entrada tal como la define el cliente, el
resultado esperado copiado de su ficha y una verificación automática.

Lo usan demo.py (consola) y casos_cliente.ipynb (notebook). No contiene reglas:
sólo llama a la API pública del motor, igual que la interfaz.

Criterio de aprobación del cliente (§1 de su documento): un caso es OK si
  (1) la recomendación coincide con las preferencias o el artista base,
  (2) la traza expone hechos de entrada, reglas disparadas y motivo, y
  (3) el sistema responde sin excepciones no controladas.
"""

from src.engine import (
    MENSAJE_ENTRADA_VACIA,
    MENSAJE_SIN_COINCIDENCIA,
    REGLAS,
    recomendar,
)


def _reglas(r):
    return {p["regla"] for p in r["traza"]}


def _niveles(cadena):
    return {REGLAS[x][0] for x in cadena}


# ── Verificaciones: cada una devuelve una lista de (descripción, cumple) ──────

def verificar_ca01(r):
    artistas = set(r["artistas"])
    return [
        ("Devuelve al menos una recomendación", len(r["recomendaciones"]) >= 1),
        ("Incluye referentes del rock nacional (Charly García o Soda Stereo)",
         bool(artistas & {"Charly García", "Soda Stereo"})),
        ("Todas las recomendaciones son de Argentina",
         all(x["pais"] == "Argentina" for x in r["recomendaciones"])),
        ("La traza muestra coincidencia directa por estilo (R12) y por país (R15)",
         {"R12", "R15"} <= _reglas(r)),
    ]


def verificar_ca02(r):
    artistas = set(r["artistas"])
    return [
        ("Devuelve Virus, Babasónicos y Zoé",
         {"Virus", "Babasónicos", "Zoé"} <= artistas),
        ("No recomienda al propio artista de referencia", "Soda Stereo" not in artistas),
        ("La traza muestra la relación por subgénero (R36 / R37)",
         {"R36", "R37"} <= _reglas(r)),
    ]


def verificar_ca03(r):
    recs = r["recomendaciones"]
    return [
        ("Devuelve recomendaciones", len(recs) >= 1),
        ("Todas son de 1980–1989", all(1980 <= x["anio"] <= 1989 for x in recs)),
        ("Incluye a Depeche Mode y Michael Jackson",
         {"Depeche Mode", "Michael Jackson"} <= set(r["artistas"])),
        ("La traza muestra la restricción temporal (R02 → R14 / R20)",
         {"R02", "R14", "R20"} <= _reglas(r)),
    ]


def verificar_ca04(r):
    recs = r["recomendaciones"]
    return [
        ("Devuelve recomendaciones", len(recs) >= 1),
        ("Las primeras posiciones son indie o folk local",
         recs[0]["artista"] in {"Él Mató a un Policía Motorizado", "Bandalos Chinos", "Juana Molina"}),
        ("Todas las recomendaciones son en español",
         all(x["idioma"] == "español" for x in recs)),
        ("La traza muestra la ponderación por música local e idioma (R05, R15, R16)",
         {"R05", "R15", "R16"} <= _reglas(r)),
    ]


def verificar_ca05(r):
    recs = r["recomendaciones"]
    black_dog = next((x for x in recs if x["titulo"] == "Black Dog"), None)
    return [
        ("Devuelve Led Zeppelin, Black Sabbath y Deep Purple",
         {"Led Zeppelin", "Black Sabbath", "Deep Purple"} <= set(r["artistas"])),
        ("Todas son de Reino Unido, años 70 y en inglés",
         all(x["pais"] == "Reino Unido" and 1970 <= x["anio"] <= 1979 and x["idioma"] == "inglés"
             for x in recs)),
        ("La cadena de «Black Dog» encadena al menos 3 niveles (1A → 2 → 3)",
         black_dog is not None and {"1A", "2", "3"} <= _niveles(black_dog["cadena"])),
    ]


def verificar_ca06(r):
    return [
        ("No devuelve recomendaciones", not r["recomendaciones"]),
        ("Emite el mensaje literal del Brief §7", r["sin_coincidencia"] == MENSAJE_SIN_COINCIDENCIA),
        ("El catálogo se evaluó completo y cerró con R27", "R27" in _reglas(r)),
    ]


def verificar_ca07(r):
    return [
        ("Emite el mensaje literal del caso", r["sin_conclusion"] == MENSAJE_ENTRADA_VACIA),
        ("El motor se detiene antes de evaluar el catálogo (sólo dispara R00)",
         _reglas(r) == {"R00"}),
        ("No devuelve recomendaciones", not r["recomendaciones"]),
    ]


def verificar_ca08(r):
    niveles = {p["nivel"] for p in r["traza"]}
    return [
        ("La traza tiene pasos numerados con regla y descripción",
         all({"paso", "regla", "nivel", "descripcion"} <= p.keys() for p in r["traza"])),
        ("Cubre lectura de la entrada, comparación, decisión y síntesis",
         {"1A", "2", "3", "4"} <= niveles),
        ("Cada recomendación trae motivos y cadena de reglas",
         all(x["motivos"] and x["cadena"] for x in r["recomendaciones"])),
    ]


CASOS = [
    {
        "id": "CA-01", "prioridad": "MUST", "requisitos": "RF-01 / RF-03",
        "titulo": "Recomendación por estilo y país (rock nacional)",
        "entrada": {"generos": ["Rock nacional"], "pais": "Argentina"},
        "esperado": "Al menos una canción o artista referente (ej. Charly García, Soda Stereo, "
                    "Spinetta). Coincidencia directa por género y origen.",
        "verificar": verificar_ca01,
    },
    {
        "id": "CA-02", "prioridad": "MUST", "requisitos": "RF-02 / RF-08",
        "titulo": "Artistas similares a una banda base",
        "entrada": {"artista": "Soda Stereo"},
        "esperado": "Artistas compatibles (ej. Virus, Babasónicos, Zoé), vinculados por "
                    "subgénero pop rock / alternativo.",
        "verificar": verificar_ca02,
    },
    {
        "id": "CA-03", "prioridad": "SHOULD", "requisitos": "RF-04",
        "titulo": "Filtrado por época (años 80)",
        "entrada": {"generos": ["Pop", "Synth-pop"], "epoca": "80s", "idioma": "Inglés"},
        "esperado": "Artistas o temas de 1980 a 1989 (ej. Michael Jackson, Madonna, "
                    "Depeche Mode). Excluye lanzamientos posteriores a 1989.",
        "verificar": verificar_ca03,
    },
    {
        "id": "CA-04", "prioridad": "SHOULD", "requisitos": "RF-06 / RF-07",
        "titulo": "Música local e idioma",
        "entrada": {"generos": ["Indie", "Folk"], "idioma": "Español", "local": True},
        "esperado": "Bandas locales en español (ej. Él Mató a un Policía Motorizado, "
                    "Bandalos Chinos), con incremento de puntaje por idioma y música local.",
        "verificar": verificar_ca04,
    },
    {
        "id": "CA-05", "prioridad": "MUST", "requisitos": "RF-01 / RF-03 / RF-05",
        "titulo": "Consulta multiatributo",
        "entrada": {"generos": ["Hard rock"], "pais": "Reino Unido", "epoca": "70s",
                    "idioma": "Inglés"},
        "esperado": "Led Zeppelin, Black Sabbath, Deep Purple. Encadenamiento hacia adelante "
                    "de al menos 3 niveles.",
        "verificar": verificar_ca05,
    },
    {
        "id": "CA-06", "prioridad": "Caso límite", "requisitos": "RF-01 / RF-07",
        "titulo": "Búsqueda sin coincidencias",
        "entrada": {"generos": ["Heavy metal"], "pais": "Japón", "epoca": "20s"},
        "esperado": "No falla. Emite: «No se encontraron recomendaciones con coincidencia "
                    "suficiente para los criterios seleccionados. Modifique o amplíe los "
                    "criterios de búsqueda.»",
        "verificar": verificar_ca06,
    },
    {
        "id": "CA-07", "prioridad": "Caso límite", "requisitos": "RF-01",
        "titulo": "Entrada vacía",
        "entrada": {},
        "esperado": "Advertencia: «Sin conclusión posible: Ingrese al menos un criterio "
                    "(estilo, artista, década o país) para ejecutar la recomendación.»",
        "verificar": verificar_ca07,
    },
    {
        "id": "CA-08", "prioridad": "MUST", "requisitos": "RF-08",
        "titulo": "Explicabilidad (sobre la consulta de CA-05)",
        "entrada": {"generos": ["Hard rock"], "pais": "Reino Unido", "epoca": "70s",
                    "idioma": "Inglés"},
        "esperado": "Bloque de inferencia con hechos de entrada, reglas disparadas con "
                    "nombre y conclusión final.",
        "verificar": verificar_ca08,
    },
]


def ejecutar(caso):
    """Ejecuta un caso y devuelve (resultado del motor, verificaciones, aprobado)."""
    resultado = recomendar(caso["entrada"])
    checks = caso["verificar"](resultado)
    return resultado, checks, all(ok for _, ok in checks)

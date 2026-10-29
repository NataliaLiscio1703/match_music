"""
tracer.py — Presentación de la traza de inferencia y de los resultados.

Capa intermedia entre el motor (engine.py) y la interfaz (app.py):
    • NO contiene reglas ni toma decisiones: sólo traduce lo que el motor produjo.
    • NO depende de Streamlit: puede usarse desde la UI, desde demo.py o desde un notebook.

Responsabilidades:
    1. Devolver los valores normalizados a su forma legible ('espanol' → 'Español').
    2. Enriquecer cada paso de la traza con el nombre de la regla y su nivel.
    3. Agrupar la traza por nivel de encadenamiento.
"""

import re

from src.engine import REGLAS, normalizar

# Nombre de cada nivel de la cadena de inferencia (para la explicación en pantalla).
NIVELES = {
    "0": "Nivel 0: validación de la consulta",
    "1A": "Nivel 1A: lectura de tus preferencias",
    "1B": "Nivel 1B: contexto musical deducido",
    "2": "Nivel 2: comparación con el catálogo",
    "2B": "Nivel 2B: filtro por estilo",
    "3": "Nivel 3: puntaje y decisión",
    "4": "Nivel 4: artistas y estilos sugeridos",
    "cierre": "Cierre: sin coincidencia suficiente",
}
ORDEN_NIVELES = list(NIVELES)

# Formas legibles que no siempre aparecen en el catálogo.
EXTRAS_LEGIBLES = {
    "musica_latina": "Música latina",
    "rock_80s": "Rock de los 80",
    "espanol": "Español",
    "ingles": "Inglés",
    "aleman": "Alemán",
    "frances": "Francés",
    "portugues": "Portugués",
    "italiano": "Italiano",
    "instrumental": "Instrumental",
    "electronica": "Electrónica",
    "metal": "Metal",
    "blues": "Blues",
    "jazz": "Jazz",
    "cumbia": "Cumbia",
    "folklore": "Folklore",
    "japon": "Japón",
}


def mapa_legible(catalogo):
    """Diccionario {valor normalizado → valor legible} construido desde el catálogo."""
    mapa = dict(EXTRAS_LEGIBLES)
    for c in catalogo:
        for campo in ("genero", "subgenero", "pais", "idioma", "artista", "titulo"):
            original = c[campo]
            # Artistas y títulos se respetan tal cual (p. ej. "a-ha"); el resto se capitaliza.
            legible = original if campo in ("artista", "titulo") else original[:1].upper() + original[1:]
            mapa.setdefault(normalizar(original), legible)
    return mapa


def legible(valor, mapa):
    """Valor suelto en forma legible (si no se conoce, se capitaliza)."""
    return mapa.get(valor, valor[:1].upper() + valor[1:])


def embellecer(texto, mapa):
    """Reemplaza cada 'valor' entre comillas simples por su forma legible."""
    return re.sub(r"'([^']+)'", lambda m: f"«{legible(m.group(1), mapa)}»", texto)


def describir_regla(regla_id):
    """Devuelve (nivel, nombre) de una regla."""
    return REGLAS.get(regla_id, ("?", regla_id))


def presentar(resultado, catalogo):
    """
    Toma el dict que devuelve engine.recomendar() y devuelve una copia lista
    para mostrar: textos legibles, estilos como pares, y traza enriquecida.
    """
    mapa = mapa_legible(catalogo)

    recomendaciones = []
    for rec in resultado["recomendaciones"]:
        recomendaciones.append({
            **rec,
            "motivos": [embellecer(m, mapa) for m in rec["motivos"]],
            "cadena": [{"id": r, "nivel": describir_regla(r)[0], "nombre": describir_regla(r)[1]}
                       for r in rec["cadena"]],
        })

    estilos = []
    for e in resultado["estilos"]:
        genero, subgenero = (p.strip() for p in e.split("/", 1))
        estilos.append({"genero": legible(genero, mapa), "subgenero": legible(subgenero, mapa)})

    traza = []
    for paso in resultado["traza"]:
        nivel, nombre = describir_regla(paso["regla"])
        traza.append({**paso, "nivel": nivel, "nombre": nombre,
                      "descripcion": embellecer(paso["descripcion"], mapa)})

    descartes = [{**d, "motivo": embellecer(d["motivo"], mapa)} for d in resultado["descartes"]]

    return {
        "recomendaciones": recomendaciones,
        "artistas": resultado["artistas"],
        "estilos": estilos,
        "descartes": descartes,
        "sin_coincidencia": resultado["sin_coincidencia"],
        "sin_conclusion": resultado.get("sin_conclusion"),
        "traza": traza,
    }


def agrupar_por_nivel(traza):
    """{nivel: [pasos]} respetando el orden de la cadena de inferencia."""
    grupos = {n: [] for n in ORDEN_NIVELES}
    for paso in traza:
        grupos.setdefault(paso["nivel"], []).append(paso)
    return {n: pasos for n, pasos in grupos.items() if pasos}
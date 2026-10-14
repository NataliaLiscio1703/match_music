"""
demo.py — Ejecuta casos de prueba sobre el motor desde consola (sin interfaz).
Uso (desde la raíz del repo):  python demo.py

Los casos son PROVISORIOS del proveedor; se reemplazarán por los casos de
prueba que entregue el Grupo B (Pautas §5.3 y §6.2).
"""

from src.engine import recomendar

CASOS = [
    ("Rock de los 80", {"generos": ["Rock"], "epoca": "80s"}),
    ("Música local en español", {"local": True, "idioma": "Español"}),
    ("Reggaeton (contexto latino)", {"generos": ["Urbano latino"]}),
    ("Subgénero puntual", {"generos": ["synth-pop"]}),
    ("Sin coincidencia: tango en alemán", {"generos": ["Tango"], "idioma": "Alemán"}),
    ("Sin criterios", {}),
]


def mostrar(nombre, entrada):
    print("=" * 78)
    print(f"CASO: {nombre}   entrada={entrada}")
    r = recomendar(entrada)
    if r["sin_coincidencia"]:
        print(f"  ⚠ {r['sin_coincidencia']}")
    for rec in r["recomendaciones"]:
        print(f"  ♪ [{rec['puntaje']}] {rec['titulo']} — {rec['artista']} ({rec['anio']}, {rec['pais']})")
        print(f"      motivos: {'; '.join(rec['motivos'])}")
        print(f"      cadena : {' → '.join(rec['cadena'])}")
    if r["artistas"]:
        print(f"  Artistas: {', '.join(r['artistas'])}")
        print(f"  Estilos : {', '.join(r['estilos'])}")
    print(f"  Traza: {len(r['traza'])} disparos — reglas distintas: "
          f"{sorted({t['regla'] for t in r['traza']})}")


if __name__ == "__main__":
    for nombre, entrada in CASOS:
        mostrar(nombre, entrada)
"""
demo.py — Ejecuta los casos de prueba del Grupo B (cliente) desde consola, sin interfaz.
Uso (desde la raíz del repo):  python demo.py

Los casos están definidos en casos_prueba.py (fuente: documento de casos de
prueba del Grupo B, reunión 2, 22/10/2026). La misma batería, con la traza
completa, se presenta en casos_cliente.ipynb.
"""

from casos_prueba import CASOS, ejecutar


def mostrar(caso):
    print("=" * 78)
    print(f"{caso['id']} [{caso['prioridad']}] {caso['titulo']}   ({caso['requisitos']})")
    print(f"  entrada : {caso['entrada']}")
    print(f"  esperado: {caso['esperado']}")
    r, checks, aprobado = ejecutar(caso)
    if r["sin_conclusion"]:
        print(f"  ⚠ {r['sin_conclusion']}")
    if r["sin_coincidencia"]:
        print(f"  ⚠ {r['sin_coincidencia']}")
    for rec in r["recomendaciones"]:
        print(f"  ♪ [{rec['puntaje']}] {rec['titulo']} — {rec['artista']} ({rec['anio']}, {rec['pais']})")
        print(f"      cadena : {' → '.join(rec['cadena'])}")
    print(f"  Traza: {len(r['traza'])} disparos — reglas distintas: "
          f"{sorted({t['regla'] for t in r['traza']})}")
    for descripcion, ok in checks:
        print(f"    {'✔' if ok else '✘'} {descripcion}")
    print(f"  RESULTADO: {'OK' if aprobado else 'NO OK'}")
    return aprobado


if __name__ == "__main__":
    resultados = [mostrar(c) for c in CASOS]
    print("=" * 78)
    print(f"Casos aprobados: {sum(resultados)} de {len(resultados)}")

# Experta 1.9.4 (copia incluida en el repositorio)

Esta carpeta contiene el código fuente **sin modificaciones** de
[Experta 1.9.4](https://pypi.org/project/experta/1.9.4/)
(repositorio original: https://github.com/nilp0inter/experta),
distribuido bajo licencia **GNU LGPL v3** (ver `LICENSE`).

## Por qué se incluye acá y no en `requirements.txt`

Experta 1.9.4 (última versión, 2019) declara como dependencias
`frozendict==1.2` y `schema==0.6.7`, que no se instalan en Python 3.10 o superior.
El código de Experta en sí funciona con versiones actuales de esas librerías
(`frozendict 2.4.7`, `schema 0.7.7`, fijadas en `requirements.txt`).

En una instalación local esto se resolvía con `pip install --no-deps experta==1.9.4`,
pero Streamlit Community Cloud instala solo lo que dice `requirements.txt` y ese
archivo no admite `--no-deps` por paquete. Incluir la librería en el repo es la
forma reproducible de desplegar sin depender de las versiones viejas.

Para actualizarla: reemplazar esta carpeta por la de una versión nueva de Experta
y volver a ejecutar `python demo.py`.

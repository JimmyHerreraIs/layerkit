# layerkit

[![CI](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml/badge.svg)](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**Convierte cualquier imagen plana en capas editables: un PNG transparente por objeto, más un manifiesto para volver a armarla.**

[English](README.md) · Español

> **Estado: v0.0, esqueleto del proyecto.** Las herramientas, el CI y la estructura
> del paquete están listos. Las funciones de imagen **aún no están implementadas**.
> Mira la [hoja de ruta](#hoja-de-ruta).

## La idea

Entra una foto plana. Sale una carpeta de capas:

```text
output/
  00_background.png   <- la escena con los huecos rellenados
  01_mug.png          <- solo la taza, fondo transparente
  02_plant.png        <- solo la planta
  manifest.json       <- dónde va cada capa y en qué orden
```

El manifiesto es lo que hace útil la salida: cada capa recuerda su posición y
su orden de apilado, así la imagen se puede volver a armar o editar pieza por
pieza en cualquier editor.

```json
{
  "source": "mug.jpg",
  "width": 1920,
  "height": 1080,
  "layers": [
    {"name": "background", "file": "00_background.png", "x": 0,   "y": 0,   "w": 1920, "h": 1080, "z": 0},
    {"name": "mug",        "file": "01_mug.png",        "x": 640, "y": 300, "w": 410,  "h": 520,  "z": 1}
  ]
}
```

`x`, `y` es la esquina superior izquierda de la capa; una `z` mayor va al frente.

## Instalación

```bash
pip install "git+https://github.com/JimmyHerreraIs/layerkit.git"
layerkit --version
```

El paquete en PyPI está planeado para la v0.3.

## Uso planeado

> Esta es la interfaz objetivo. **Todavía no está disponible.**

```bash
layerkit photo.jpg --out output/
```

```python
from layerkit import decompose

layers = decompose("photo.jpg")
```

## Alcance

| Qué hace | Qué NO hace (y por qué) |
|---|---|
| Quita el fondo de una imagen | Editar la imagen: no cambia colores ni agrega sombras. Es un separador, no un editor |
| Separa cada objeto en su propia capa PNG | Reconocer personas ni leer texto: sin reconocimiento facial ni OCR |
| Guarda posición y orden en `manifest.json` | Procesar video en v1: solo imágenes fijas |
| Exporta PNGs, ZIP y archivos con capas | Exportar SVG vectorial real en v1: convertir píxeles a vectores es otro proyecto |
| Corre en local, en CPU, sin enviar imágenes a nadie | Ser un servicio en la nube ni tener cuentas de usuario |
| Se usa como librería, CLI o API | Traer una interfaz gráfica de escritorio |
| Permite cambiar de modelo por configuración | Entrenar modelos: usa modelos abiertos ya entrenados |

## Hoja de ruta

| Versión | Qué entra |
|---|---|
| **v0.0** | Esqueleto: estructura del paquete, CI, pre-commit, plantillas, docs *(actual)* |
| v0.1 | Quitar fondo como librería y CLI |
| v0.2 | Separar en N capas, limpieza de máscaras, `manifest.json` |
| v0.3 | Exportar ZIP, archivos con capas y publicar en PyPI |
| v0.4 | Demo en el navegador y benchmark |
| v1.0 | Servidor FastAPI opcional, documentación completa |

Las ideas fuera del alcance actual se registran como issues y se revisan después de la v1.0.

## Desarrollo

```bash
git clone https://github.com/JimmyHerreraIs/layerkit.git
cd layerkit
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate
pip install -e ".[dev]"
pre-commit install

ruff check . && ruff format --check . && mypy && pytest
```

El código tiene tres puertas de entrada sobre un mismo núcleo: `layerkit.core`
contiene el pipeline y no sabe nada de la CLI ni de ninguna API web.

## Contribuir

Las contribuciones son bienvenidas. Lee primero [CONTRIBUTING.md](CONTRIBUTING.md)
(en inglés). Para reportar una vulnerabilidad, mira [SECURITY.md](SECURITY.md).

## Licencia

[MIT](LICENSE) © 2026 Jimmy Herrera

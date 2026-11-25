# layerkit

[![CI](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml/badge.svg)](https://github.com/JimmyHerreraIs/layerkit/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

**Convierte cualquier imagen plana en capas editables: un PNG transparente por objeto, más un manifiesto para volver a armarla.**

[English](README.md) · Español

> **Estado: v0.1.** Quitar el fondo funciona como comando y como librería de
> Python: una foto se convierte en una capa de fondo y un sujeto recortado.
> Separar en varios objetos llega en la v0.2. Mira la [hoja de ruta](#hoja-de-ruta).

## Qué hace

Entra una foto plana. Sale una carpeta de capas:

```text
photo-layers/
  00_background.png   <- la imagen original, completa
  01_subject.png      <- solo el sujeto principal, fondo transparente
  manifest.json       <- dónde va cada capa y en qué orden
```

El manifiesto es lo que hace útil la salida: cada capa recuerda su posición y
su orden de apilado, así la imagen se puede volver a armar o editar pieza por
pieza en cualquier editor.

Todo corre **en local, en la CPU**. Tus imágenes no se envían a ningún sitio.

## Instalación

El modelo por defecto corre con [rembg](https://github.com/danielgatis/rembg),
que es un extra opcional porque pesa mucho (unos 480 MB con sus dependencias):

```bash
pip install "layerkit[rembg] @ git+https://github.com/JimmyHerreraIs/layerkit.git"
layerkit --version
```

La primera ejecución descarga los pesos del modelo una sola vez (4,6 MB el
modelo por defecto) y los guarda en `~/.rembg/models/`. El paquete en PyPI está
planeado para la v0.3.

Sin el extra, `pip install "git+https://github.com/JimmyHerreraIs/layerkit.git"`
instala solo el núcleo ligero (Pillow). Después puedes conectar tu propio
modelo, mira [Usa tu propio modelo](#usa-tu-propio-modelo).

## Línea de comandos

```bash
layerkit photo.jpg                    # escribe photo-layers/
layerkit photo.jpg -o resultado       # elige la carpeta
layerkit photo.jpg --model isnet-general-use --overwrite
```

```text
Saved 2 layers to photo-layers
  00_background.png
  01_subject.png
  manifest.json
```

(Los mensajes del programa están en inglés.)

| Opción | Significado |
|---|---|
| `-o`, `--output DIR` | Carpeta de salida (por defecto: `<nombre de la imagen>-layers`) |
| `--model NAME` | `u2netp` (por defecto, rápido) o `isnet-general-use` (más lento, mejor con varios objetos) |
| `--max-pixels N` | Imagen más grande que se acepta (por defecto: 25 millones de píxeles) |
| `--overwrite` | Reemplaza archivos de capas que ya existan (si no, se niega y no escribe nada) |
| `--version` | Muestra la versión |

Se aceptan JPEG, PNG y WebP. Los errores salen en una línea que empieza por
`error:` y el código de salida es `1`; las opciones inválidas salen con `2`.

## Python

```python
from layerkit import decompose
from layerkit.exporters.png import export_png

result = decompose("photo.jpg")  # fondo + sujeto
for layer in result.layers:
    print(layer.name, layer.box, layer.z)

export_png(result, "photo-layers")  # archivos PNG + manifest.json
```

`decompose` devuelve una `Decomposition` con objetos `Layer` inmutables (imagen
RGBA de Pillow, caja y orden de apilado). Todo error que layerkit lanza a
propósito hereda de `layerkit.LayerkitError`.

### Usa tu propio modelo

Sirve cualquier objeto con un `name` y un método `predict_mask(image)` que
devuelva una máscara en escala de grises de 8 bits (`255` es primer plano) del
mismo tamaño. Así el extra pesado `rembg` es opcional:

```python
from PIL import Image
from layerkit import decompose


class MyModel:
    name = "my-model"

    def predict_mask(self, image: Image.Image) -> Image.Image:
        # Devuelve una máscara modo "L" del mismo tamaño que `image`.
        raise NotImplementedError


result = decompose("photo.jpg", model=MyModel())
```

## El manifiesto

```json
{
  "version": 1,
  "source": "photo.jpg",
  "width": 1920,
  "height": 1080,
  "layers": [
    {"name": "background", "file": "00_background.png", "x": 0,   "y": 0,   "width": 1920, "height": 1080, "z": 0},
    {"name": "subject",    "file": "01_subject.png",    "x": 640, "y": 300, "width": 410,  "height": 520,  "z": 1}
  ]
}
```

El archivo real va con sangría; aquí cada capa se muestra en una línea para que
se lea mejor. `x`, `y` es la esquina superior izquierda de la capa en la imagen
completa; una `z` mayor va al frente. Las capas se listan de atrás hacia delante. Los nombres
de archivo son nombres simples, nunca rutas, y layerkit rechaza cualquier
manifiesto que intente apuntar a otro sitio. `version` permite que el formato
evolucione sin romper a quien lo lee.

## Modelos

Medido en una CPU de portátil de 8 hilos; el método está en el
[ADR 0001](docs/adr/0001-background-removal-model.md) (en inglés):

| Modelo | Pesos | Tiempo por imagen | Memoria máxima | Úsalo para |
|---|---|---|---|---|
| `u2netp` (por defecto) | 4,6 MB | 0,75 s | 0,7 GB | un recorte rápido y ligero |
| `isnet-general-use` | 179 MB | 4,6 s | 1,7 GB | varios objetos, resultado más limpio |

Las dos familias de modelos tienen licencia Apache-2.0 en su origen y layerkit
no los redistribuye: tu máquina los descarga del proyecto rembg. No se revisaron
los términos de los datasets con que se entrenaron; compruébalos antes de
cualquier uso comercial.

## Límites de la v0.1

- **Una sola capa de sujeto.** Todo lo que el modelo considera el sujeto
  principal queda en una capa. Separar en varios objetos llega en la v0.2.
- **El fondo es la imagen original**, sin tocar. Rellenar el hueco que deja el
  sujeto (inpainting) también llega en la v0.2.
- **Sin objeto claro, sin salida.** Si la máscara cubre menos del 0,5 % o más del
  95 % de la imagen, layerkit se detiene con `No clear object was found` en vez
  de escribir un mal recorte.
- Las imágenes de más de 25 millones de píxeles se rechazan antes de ejecutar
  ningún modelo.
- Solo CPU; todavía sin soporte de GPU.

## Alcance

| Qué hace | Qué NO hace (y por qué) |
|---|---|
| Quita el fondo de una imagen | Editar la imagen: no cambia colores ni agrega sombras. Es un separador, no un editor |
| Separa cada objeto en su propia capa PNG | Reconocer personas ni leer texto: sin reconocimiento facial ni OCR |
| Guarda posición y orden en `manifest.json` | Procesar video en v1: solo imágenes fijas |
| Exporta PNGs, ZIP y archivos con capas | Exportar SVG vectorial real en v1: convertir píxeles a vectores es otro proyecto |
| Corre en local, en CPU, sin enviar imágenes a nadie | Ser un servicio en la nube ni tener cuentas de usuario |
| Se usa como librería, CLI o API | Traer una interfaz gráfica de escritorio |
| Permite cambiar de modelo | Entrenar modelos: usa modelos abiertos ya entrenados |

Las filas de arriba describen el objetivo de la v1; la hoja de ruta dice qué
existe hoy.

## Hoja de ruta

| Versión | Qué entra |
|---|---|
| v0.0 | Esqueleto: estructura del paquete, CI, pre-commit, plantillas, docs |
| **v0.1** | Quitar fondo como librería y CLI *(actual)* |
| v0.2 | Separar en N capas, rellenar el fondo, limpieza de máscaras |
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

Los tests usan un modelo falso, así que no descargan nada. Un test marcado
ejecuta el modelo real por defecto: `pip install -e ".[rembg]"` y
`pytest -m integration`.

El código tiene tres puertas de entrada sobre un mismo núcleo: `layerkit.core`
contiene el pipeline y no sabe nada de la CLI ni de ninguna API web. Las
decisiones de diseño están en [`docs/adr/`](docs/adr/) (en inglés).

## Contribuir

Las contribuciones son bienvenidas. Lee primero [CONTRIBUTING.md](CONTRIBUTING.md)
(en inglés). Para reportar una vulnerabilidad, mira [SECURITY.md](SECURITY.md).

## Licencia

[MIT](LICENSE) © 2026 Jimmy Herrera

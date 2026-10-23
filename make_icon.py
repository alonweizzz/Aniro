"""Generate Windows icon from the project's original logo.png."""
from pathlib import Path
from PIL import Image

source=Path(__file__).resolve().parent/"logo.png"
if not source.is_file():
    raise SystemExit("Missing logo.png in repository root")
with Image.open(source) as original:
    image=original.convert("RGBA")
    image.save(source.with_name("Aniro.ico"),format="ICO",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Generated Aniro.ico")

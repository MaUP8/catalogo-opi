#!/usr/bin/env python3
"""Arma el sitio del Catálogo OPI · Interior del país (repo MaUP8/catalogo-opi-interior)
a partir de este repo. Uso: python3 tools/generar_interior.py [carpeta_destino]
(por defecto ../catalogo-opi-interior, el clon local del repo del interior).

- index.html: la misma página, con la variante 'interior' fijada (teléfono, mínimo $7.500,
  precio consumidor final bajo el mínimo, video del Outlet propio).
- data/: tonos.json y disponibles.json (los mismos datos que publica este repo).
- img/: fotos de producto, logo, ayuda y el video del Outlet del interior.
Correr después de cualquier cambio en index.html o en las imágenes. Los datos de stock y precio
los copia la tarea programada en cada actualización."""
import os, re, sys, shutil
base = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
dest = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, '..', 'catalogo-opi-interior'))
s = open(os.path.join(base, 'index.html'), encoding='utf-8').read()
s = s.replace('<!doctype html>', '<!doctype html>\n<!-- Generado desde MaUP8/catalogo-opi con tools/generar_interior.py: no editar a mano. -->', 1)
s = re.sub(r'<title>.*?</title>', '<title>Catálogo OPI · Interior del país</title>', s, count=1)
s = s.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf',
              "<script>window.VARIANTE='interior'</script>\n<script src=\"https://cdnjs.cloudflare.com/ajax/libs/jspdf", 1)
s = re.sub(r'img/outlet\.mp4\?v=\d+', 'img/outlet-interior.mp4?v=1', s)
assert "window.VARIANTE='interior'" in s
os.makedirs(dest, exist_ok=True)
open(os.path.join(dest, 'index.html'), 'w', encoding='utf-8').write(s)
for d in ('data', 'img', 'img/p'): os.makedirs(os.path.join(dest, d), exist_ok=True)
for f in ('data/tonos.json', 'data/disponibles.json', 'img/opi.svg', 'img/opi.png', 'img/ayuda.mp4',
          'img/ayuda.jpg', 'img/outlet.jpg', 'img/outlet-interior.mp4'):
    shutil.copy2(os.path.join(base, f), os.path.join(dest, f))
src = os.path.join(base, 'img/p'); n = 0
for f in os.listdir(src):
    a, b = os.path.join(src, f), os.path.join(dest, 'img/p', f)
    if not os.path.exists(b) or os.path.getsize(a) != os.path.getsize(b) or open(a,'rb').read() != open(b,'rb').read():
        shutil.copy2(a, b); n += 1
print(f'Sitio del interior listo en {dest} ({n} imágenes copiadas o actualizadas)')

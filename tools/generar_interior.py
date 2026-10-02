#!/usr/bin/env python3
"""Genera interior/index.html (Catálogo OPI interior del país) a partir de index.html.
Misma página, mismos datos e imágenes (base href="../"); el teléfono y el pedido mínimo
salen de la variante 'interior' definida en index.html según la ruta /interior/.
Correr después de cualquier cambio en index.html: python3 tools/generar_interior.py"""
import os, re
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
s = open(os.path.join(base, 'index.html'), encoding='utf-8').read()
s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<base href="../">', 1)
s = re.sub(r'<title>.*?</title>', '<title>Catálogo OPI · Interior del país</title>', s, count=1)
os.makedirs(os.path.join(base, 'interior'), exist_ok=True)
s = s.replace('<!doctype html>', '<!doctype html>\n<!-- Generado por tools/generar_interior.py: no editar a mano. -->', 1)
open(os.path.join(base, 'interior/index.html'), 'w', encoding='utf-8').write(s)
print('interior/index.html listo')

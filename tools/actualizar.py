#!/usr/bin/env python3
"""Regenera data/disponibles.json a partir del resultado de Power BI.

Uso: python3 tools/actualizar.py resultado.txt [--forzar]
resultado.txt: una línea por grupo, "precio_neto|IMESI|n|sku,sku,..."
  precio_neto: lista GRAL sin impuestos (vacío si no tiene precio)
  IMESI: A (aplica) o N (no aplica); n: cantidad de SKUs del grupo
Solo entran productos que ya están en data/tonos.json. Precio final = neto x 1,115 (si aplica IMESI) x 1,22.
"""
import json, sys, datetime, collections, re, os
IMESI, IVA = 1.115, 1.22
LINEAS_ESMALTE = {0, 1, 2, 3, 4}          # tonos: siempre llevan IMESI
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tonos = json.load(open(os.path.join(base, 'data/tonos.json')))
linea = {t[0]: t[3] for t in tonos['t']}
dest = os.path.join(base, 'data/disponibles.json')
previo = json.load(open(dest))['d'] if os.path.exists(dest) else {}

stock = {}
for ln in open(sys.argv[1], encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    p, im, n, skus = ln.split('|')
    skus = [s.strip() for s in skus.split(',') if s.strip()]
    if len(skus) != int(n):
        sys.exit(f'ERROR: el grupo {p}|{im} trae {len(skus)} SKUs y Power BI informó {n}. Dato mal copiado.')
    for s in skus:
        if not re.fullmatch(r'[0-9A-Za-z.\-]+', s): sys.exit(f'ERROR: SKU inválido {s!r}')
        stock[s] = (float(p.replace(',', '.')) if p else None, im.strip().upper().startswith('A'))

netos = collections.defaultdict(collections.Counter)
for k, (p, _) in stock.items():
    if k in linea and p: netos[linea[k]][p] += 1
d, sin_precio = {}, []
for k, (p, aplica) in stock.items():
    if k not in linea: continue
    L = linea[k]
    if L in LINEAS_ESMALTE:
        aplica = True
        if not p and netos[L]: p = netos[L].most_common(1)[0][0]
    if not p:
        sin_precio.append(k); continue   # sin precio en lista: no se publica
    d[k] = round(p * (IMESI if aplica else 1) * IVA, 2)

orden = [t[0] for t in tonos['t'] if t[0] in d]
d = {k: d[k] for k in orden}
altas = [k for k in d if k not in previo]; bajas = [k for k in previo if k not in d]
precio = [k for k in d if k in previo and abs(d[k] - previo[k]) > 0.005]
print(f'Disponibles: {len(d)} (antes {len(previo)}). Altas {len(altas)}, bajas {len(bajas)}, cambios de precio {len(precio)}, sin precio {len(sin_precio)}.')
if previo and len(d) < 0.6 * len(previo) and '--forzar' not in sys.argv:
    sys.exit('FRENO: los disponibles caen más de 40 %. No se escribió nada; revisar antes de publicar.')
json.dump({'fecha': datetime.date.today().isoformat(), 'd': d}, open(dest, 'w'), separators=(',', ':'))

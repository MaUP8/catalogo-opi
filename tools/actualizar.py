#!/usr/bin/env python3
"""Regenera data/disponibles.json a partir de los resultados de Power BI.

Uso: python3 tools/actualizar.py resultado.txt [outlet.txt] [--forzar]

resultado.txt: una línea por grupo, "gral_neto|opi_neto|IMESI|n|sku,sku,..."
  gral_neto: lista GRAL sin impuestos (vacío si no tiene precio) -> precio profesional
  opi_neto:  lista O.P.I. sin impuestos (vacío si no tiene)       -> precio consumidor final
  IMESI: A (aplica) o N; n: cantidad de SKUs del grupo
  (también acepta el formato viejo "gral_neto|IMESI|n|skus")
outlet.txt: una línea por SKU, "sku|lote:unid;lote:unid" = stock actual (dep 1, STF) de los
  lotes que ya tenían saldo antes de 2022. tools/outlet_tope.json guarda, por SKU y lote, las
  unidades que siguen siendo anteriores a 2022 (FIFO sobre ingresos y reposiciones); acá solo
  bajan: tope = min(tope, stock del lote). Un lote que no viene más queda en 0.
Precio final = neto x 1,115 (si aplica IMESI; los tonos siempre) x 1,22.
"""
import json, sys, datetime, collections, re, os
IMESI, IVA = 1.115, 1.22
LINEAS_ESMALTE = {0, 1, 2, 3, 4}          # tonos: siempre llevan IMESI; solo tonos van al outlet
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tonos = json.load(open(os.path.join(base, 'data/tonos.json')))
linea = {t[0]: t[3] for t in tonos['t']}
dest = os.path.join(base, 'data/disponibles.json')
fichero_tope = os.path.join(base, 'tools/outlet_tope.json')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
previo = json.load(open(dest))['d'] if os.path.exists(dest) else {}

def num(x):
    x = x.strip()
    return float(x.replace('.', '').replace(',', '.')) if ',' in x else (float(x) if x else None)

stock = {}
for ln in open(args[0], encoding='utf-8'):
    ln = ln.strip()
    if not ln: continue
    f = ln.split('|')
    if len(f) == 5: pg, po, im, n, skus = f
    elif len(f) == 4: (pg, im, n, skus), po = f, ''
    else: sys.exit(f'ERROR: línea con formato inesperado: {ln[:80]}')
    skus = [s.strip() for s in skus.split(',') if s.strip()]
    if len(skus) != int(n):
        sys.exit(f'ERROR: el grupo {pg}|{po}|{im} trae {len(skus)} SKUs y Power BI informó {n}. Dato mal copiado.')
    for s in skus:
        if not re.fullmatch(r'[0-9A-Za-z.\-]+', s): sys.exit(f'ERROR: SKU inválido {s!r}')
        stock[s] = (num(pg), num(po), im.strip().upper().startswith('A'))

netos = collections.defaultdict(collections.Counter)
for k, (p, _, _) in stock.items():
    if k in linea and p: netos[linea[k]][p] += 1
d, pp, sin_precio = {}, {}, []
for k, (p, po, aplica) in stock.items():
    if k not in linea: continue
    L = linea[k]
    if L in LINEAS_ESMALTE:
        aplica = True
        if not p and netos[L]: p = netos[L].most_common(1)[0][0]
    if not p:
        sin_precio.append(k); continue   # sin precio profesional: no se publica
    f = (IMESI if aplica else 1) * IVA
    d[k] = round(p * f, 2)
    if po: pp[k] = round(po * f, 2)      # sin lista O.P.I.: solo precio profesional

# Outlet
o = {}
if len(args) > 1:
    tope = json.load(open(fichero_tope))
    hoy = {}
    for ln in open(args[1], encoding='utf-8'):
        ln = ln.strip()
        if not ln: continue
        s, lotes = ln.split('|', 1)
        hoy[s.strip()] = {l.rsplit(':', 1)[0]: float(l.rsplit(':', 1)[1]) for l in lotes.split(';') if ':' in l}
    for s in list(tope):
        for l in list(tope[s]):
            t = min(tope[s][l], hoy.get(s, {}).get(l, 0))
            if t > 0: tope[s][l] = int(t)
            else: del tope[s][l]
        if not tope[s]: del tope[s]
    json.dump(tope, open(fichero_tope, 'w'), indent=0, sort_keys=True)
    for s, ls in tope.items():
        if s in d and linea.get(s) in LINEAS_ESMALTE:
            o[s] = sum(ls.values())
else:
    o = json.load(open(dest)).get('o', {}) if os.path.exists(dest) else {}
    o = {k: v for k, v in o.items() if k in d}

orden = [t[0] for t in tonos['t'] if t[0] in d]
d = {k: d[k] for k in orden}
pp = {k: pp[k] for k in orden if k in pp}
o = {k: o[k] for k in orden if k in o}
altas = [k for k in d if k not in previo]; bajas = [k for k in previo if k not in d]
precio = [k for k in d if k in previo and abs(d[k] - previo[k]) > 0.005]
print(f'Disponibles: {len(d)} (antes {len(previo)}). Altas {len(altas)}, bajas {len(bajas)}, '
      f'cambios de precio {len(precio)}, sin precio {len(sin_precio)}. '
      f'Con precio público: {len(pp)}. Outlet: {len(o)} tonos, {sum(o.values())} unidades.')
if previo and len(d) < 0.6 * len(previo) and '--forzar' not in sys.argv:
    sys.exit('FRENO: los disponibles caen más de 40 %. No se escribió nada; revisar antes de publicar.')
json.dump({'fecha': datetime.date.today().isoformat(), 'd': d, 'pp': pp, 'o': o},
          open(dest, 'w'), separators=(',', ':'))

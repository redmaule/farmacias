#!/usr/bin/env python3
"""Genera index.html con las farmacias de turno de la Region del Maule (fuente: Farmanet, Minsal)."""
import json, html, sys, urllib.request, unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://midas.minsal.cl/farmacia_v2/WS/getLocalesTurnos.php"
COMUNAS_MAULE = ["TALCA","CONSTITUCION","CUREPTO","EMPEDRADO","MAULE","PELARCO","PENCAHUE","RIO CLARO",
 "SAN CLEMENTE","SAN RAFAEL","CAUQUENES","CHANCO","PELLUHUE","CURICO","HUALANE","LICANTEN","MOLINA",
 "RAUCO","ROMERAL","SAGRADA FAMILIA","TENO","VICHUQUEN","LINARES","COLBUN","LONGAVI","PARRAL","RETIRO",
 "SAN JAVIER","VILLA ALEGRE","YERBAS BUENAS"]

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())

def titulo(s):
    s = " ".join(str(s or "").split())
    return s.title() if s.isupper() else s

def hora(s):
    s = str(s or "").strip()
    return s[:5] if len(s) >= 5 else s

ahora = datetime.now(ZoneInfo("America/Santiago"))
status = {"actualizado": ahora.isoformat(), "fuente": URL}
try:
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*", "Accept-Language": "es-CL,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8-sig", "replace")
        status["http"] = r.status
    data = json.loads(raw)
except Exception as e:
    status["error"] = repr(e)[:500]
    body = getattr(e, "read", lambda: b"")()
    status["respuesta"] = body[:300].decode("utf-8", "replace") if body else ""
    json.dump(status, open("status.json", "w"), ensure_ascii=False, indent=1)
    print(status); sys.exit(0)  # se mantiene el index.html anterior

maule = [d for d in data if str(d.get("fk_region", "")).lstrip("0") == "7" or norm(d.get("comuna_nombre")) in COMUNAS_MAULE]
status.update({"total_pais": len(data), "total_maule": len(maule), "campos": sorted(data[0].keys()) if data else []})

por_comuna = {}
for d in maule:
    por_comuna.setdefault(titulo(d.get("comuna_nombre")), []).append(d)

fecha_txt = ahora.strftime("%d-%m-%Y")
dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
fecha_larga = f"{dias[ahora.weekday()]} {ahora.day} de {meses[ahora.month-1]} de {ahora.year}"

secciones = []
for comuna in sorted(por_comuna, key=norm):
    items = []
    for d in sorted(por_comuna[comuna], key=lambda x: norm(x.get("local_nombre"))):
        nombre = html.escape(titulo(d.get("local_nombre")))
        direccion = html.escape(titulo(d.get("local_direccion")))
        localidad = titulo(d.get("localidad_nombre"))
        if localidad and norm(localidad) != norm(comuna):
            direccion += f", {html.escape(localidad)}"
        ap, ci = hora(d.get("funcionamiento_hora_apertura")), hora(d.get("funcionamiento_hora_cierre"))
        horario = f"{ap} a {ci} hrs." if ap and ci else ""
        tel = str(d.get("local_telefono") or "").strip()
        lat, lng = d.get("local_lat"), d.get("local_lng")
        mapa = f'<a href="https://www.google.com/maps?q={lat},{lng}" target="_blank" rel="noopener">Ver mapa</a>' if lat and lng else ""
        tel_html = f'<a href="tel:{html.escape(tel)}">{html.escape(tel)}</a>' if tel and tel not in ("+560", "0") else ""
        extra = " · ".join(x for x in (horario, tel_html, mapa) if x)
        items.append(f'<li><strong>{nombre}</strong><span>{direccion}</span><small>{extra}</small></li>')
    secciones.append(f'<section data-c="{html.escape(norm(comuna))}"><h2>{html.escape(comuna)}</h2><ul>{"".join(items)}</ul></section>')

if not secciones:
    secciones = ['<p class="vacio">Hoy no hay farmacias de turno informadas para la Región del Maule.</p>']

page = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farmacias de turno en el Maule – {fecha_txt}</title>
<style>
:root{{--rojo:#c8102e;--tinta:#1e1e1e;--gris:#666;--linea:#e6e6e6}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;color:var(--tinta);background:#fff;line-height:1.4}}
.wrap{{max-width:760px;margin:0 auto;padding:16px}}
.tag{{display:inline-block;background:var(--rojo);color:#fff;font-weight:600;font-size:13px;padding:3px 10px;border-radius:3px;letter-spacing:.03em}}
h1{{font-size:22px;margin:10px 0 2px}}.fecha{{color:var(--gris);font-size:14px;margin:0 0 14px}}
input{{width:100%;padding:11px 12px;font-size:16px;border:1px solid #ccc;border-radius:6px;margin-bottom:8px}}
h2{{font-size:17px;margin:18px 0 6px;padding-bottom:4px;border-bottom:2px solid var(--rojo)}}
ul{{list-style:none;margin:0;padding:0}}li{{padding:9px 0;border-bottom:1px solid var(--linea);display:flex;flex-direction:column;gap:2px}}
li span{{font-size:15px}}li small{{color:var(--gris);font-size:13px}}a{{color:var(--rojo)}}
.pie{{color:var(--gris);font-size:12px;margin-top:18px}}.vacio{{color:var(--gris)}}
</style></head><body><div class="wrap">
<span class="tag">Farmacias de turno</span>
<h1>Región del Maule</h1>
<p class="fecha">Turnos para hoy, {fecha_larga} · Actualizado {ahora.strftime("%H:%M")} hrs.</p>
<input id="q" type="search" placeholder="Busca tu comuna (ej. Talca, Curicó, Linares)" aria-label="Buscar comuna">
{"".join(secciones)}
<p class="pie">Fuente: Farmanet, Ministerio de Salud. Los turnos pueden cambiar; ante dudas, llama a la farmacia antes de ir. RedMaule.com</p>
</div><script>
var q=document.getElementById('q');q.addEventListener('input',function(){{var t=q.value.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toUpperCase().trim();
document.querySelectorAll('section').forEach(function(s){{s.style.display=!t||s.dataset.c.indexOf(t)>-1?'':'none'}});avisar()}});
function avisar(){{try{{parent.postMessage({{farmaciasAltura:document.documentElement.scrollHeight}},'*')}}catch(e){{}}}}
window.addEventListener('load',avisar);
</script></body></html>"""
open("index.html", "w", encoding="utf-8").write(page)
json.dump(status, open("status.json", "w"), ensure_ascii=False, indent=1)
print(status)

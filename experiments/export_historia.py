#!/usr/bin/env python3
"""Cartel estático: solo datos grabados, sin reloj, red ni dependencias."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'experiments/results/eval_b2b.json'
OUT = ROOT / 'docs/historia/index.html'
CONDITIONS = ('B-', 'B+', 'C3')
LABELS = ('B− · sin lección', 'B+ · con lección', 'C3 · de otro tipo')
COLORS = ('#536779', '#174f85', '#c9a227')
ORDER = ('cotizacion', 'propuesta_tecnica', 'reporte_cliente',
         'respuesta_soporte', 'ficha_tecnica')
CSP = ("default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
       "base-uri 'none'; form-action 'none'; frame-src 'none'")


def esc(value):
    return html.escape(str(value), quote=True)


def fraction(metric):
    return esc(metric['fraction'])


def words(metric):
    return esc(f"{metric['k']} de {metric['n']}")


def interval(metric):
    return esc(metric['wilson95']['display'])


def change_phrase(label, block):
    before, after = block['B-'], block['B+']
    delta = after['k'] * before['n'] - before['k'] * after['n']
    if delta == 0:
        phrase = f"se quedó en {after['fraction']}"
    else:
        verb = 'pasó de' if delta > 0 else 'empeoró: de'
        phrase = f"{verb} {before['fraction']} a {after['fraction']}"
    return esc(f'{label} {phrase}')


def svg_start(name, title, description, width, height, css='diagram'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="{css}" '
            f'viewBox="0 0 {width} {height}" role="img" '
            f'aria-labelledby="{name}-title {name}-desc">'
            f'<title id="{name}-title">{esc(title)}</title>'
            f'<desc id="{name}-desc">{esc(description)}</desc>')


def text(x, y, value, size=18, anchor='start', color='#182637'):
    return (f'<text x="{x}" y="{y}" font-size="{size}" '
            f'text-anchor="{anchor}" fill="{color}">{esc(value)}</text>')


def rect(x, y, width, height, fill='#fff', stroke='#536779', extra=''):
    return (f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="6" fill="{fill}" stroke="{stroke}" {extra}/>')


def line(x1, y1, x2, y2, color='#536779', extra='', width=2):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{width}" {extra}/>')


def header_icons():
    s = svg_start('mini', 'De la corrección al siguiente documento',
                  'Documento con error → lápiz → aprobación humana → documento correcto.',
                  320, 64, 'mini')
    for x in (12, 256):
        s += rect(x, 8, 40, 48, '#fff', '#fff')
        s += line(x + 9, 22, x + 30, 22)
        s += line(x + 9, 31, x + 30, 31)
    s += text(32, 49, '×', 22, 'middle', '#9b2424')
    s += text(276, 49, '✓', 22, 'middle', '#174f85')
    s += text(77, 40, '→', 24, color='#fff')
    s += '<path d="M116 44 L135 16 L144 23 L125 51 L113 54 Z" fill="#f6d56f"/>'
    s += text(164, 40, '→', 24, color='#fff')
    s += text(211, 44, '✓', 34, 'middle', '#f6d56f')
    s += text(236, 40, '→', 24, 'middle', '#fff')
    return s + '</svg>'


def problem_svg():
    description = ('Semana 1: Cliente Demo 01, sin vigencia ni pago. Lucía corrige a mano. '
                   'Semana 2: Cliente Demo 02, otra vez sin vigencia ni pago. Corrige otra vez. '
                   'Semana 3: Cliente Demo 03, mismo hueco. '
                   'La corrección se queda en el documento, no en la herramienta.')
    s = svg_start('problema', 'El problema: el mismo hueco cada semana', description, 940, 210)
    for i in range(3):
        x = 10 + i * 345
        s += rect(x, 15, 240, 150)
        s += text(x + 16, 43, f'Semana {i + 1}')
        s += text(x + 16, 69, f'Cliente Demo {i + 1:02}')
        s += text(x + 16, 94, 'Cotización', 16)
        s += rect(x + 12, 109, 216, 40, '#fff4f2', '#9b2424', 'stroke-dasharray="5 4"')
        s += text(x + 23, 135, 'Faltan: vigencia y pago', 16, color='#9b2424')
        if i < 2:
            cx = x + 292
            s += line(x + 244, 90, x + 338, 90)
            s += f'<circle cx="{cx}" cy="60" r="9" fill="#182637"/>'
            s += line(cx, 70, cx, 102)
            s += line(cx, 80, cx + 19, 67)
            s += line(cx + 19, 67, cx + 26, 50, '#876600')
            s += text(cx, 193, 'Lucía corrige' if i == 0 else 'Corrige otra vez', 15, 'middle')
    return s + '</svg>'


def loop_svg():
    description = ('La IA redacta → una persona corrige → se propone una lección por tipo de documento. '
                   'Compuerta: ¿alguien la aprueba? Sí: lección aprobada; el siguiente documento '
                   'del mismo tipo la usa y el ciclo vuelve a empezar. No o retirada: no entra. '
                   'Sin reentrenar el modelo; tú puedes retirar la lección.')
    s = svg_start('loop', 'El loop con aprobación humana', description, 780, 430)
    nodes = ((20, 25, '1 · La IA redacta', 'Un documento nuevo'),
             (445, 25, '2 · Una persona corrige', 'Señala lo que falta'),
             (445, 185, '3 · Se propone una lección', 'Por tipo de documento'),
             (20, 320, '4 · El siguiente documento', 'Del mismo tipo la usa'))
    for x, y, a, b in nodes:
        s += rect(x, y, 310, 85, '#f0f5fa')
        s += text(x + 15, y + 33, a)
        s += text(x + 15, y + 61, b, 16)
    for coords in ((335, 68, 432, 68), (600, 112, 600, 178),
                   (445, 228, 335, 228), (175, 279, 175, 315)):
        s += line(*coords)
    s += text(380, 61, '→', 24)
    s += text(610, 153, '↓', 24)
    s += text(380, 219, '←', 24)
    s += text(164, 315, '↓', 22)
    s += '<path d="M175 165 L330 222 L175 279 L20 222 Z" fill="#c9a227" stroke="#876600"/>'
    s += text(175, 219, '¿Aprobada?', 22, 'middle')
    s += text(175, 244, 'Compuerta humana', 16, 'middle')
    s += text(188, 298, 'Sí: lección aprobada', 16)
    s += '<path d="M20 363 H5 V68 H18" fill="none" stroke="#536779" stroke-width="2" stroke-dasharray="5 4"/>'
    s += text(8, 75, '›', 24)
    s += text(20, 139, '↻ vuelve a redactar', 16)
    s += line(335, 244, 426, 297)
    s += text(437, 310, 'No / retirada → no entra', 18)
    s += text(360, 370, 'Sin reentrenar el modelo', 17)
    s += text(360, 399, 'Tú puedes retirar la lección', 17)
    return s + '</svg>'


def design_svg(recorded):
    rows = recorded['by_type']
    total = sum(recorded[k]['n'] for k in CONDITIONS)
    description = f"{len(rows)} tipos; " + '; '.join(
        f"{r['label']}: " + ', '.join(
            f"{key} {r[key]['n']} {'documento' if r[key]['n'] == 1 else 'documentos'}"
            for key in CONDITIONS)
        for r in rows)
    description += f'. Total: {total} corridas. Cada cuadrito es un documento generado y guardado.'
    width = len(rows) * 178 + 80
    s = svg_start('diseno', 'Diseño del experimento', description, width, 350)
    for i, r in enumerate(rows):
        x = 75 + i * 178
        label = r['label'].split(' ', 1)
        for j, chunk in enumerate(label):
            s += text(x + 50, 28 + j * 24, chunk, 17, 'middle')
        for j, key in enumerate(CONDITIONS):
            y = 95 + j * 68
            if i == 0:
                s += text(8, y + 18, key, 17)
            for square in range(r[key]['n']):
                s += rect(x + (square % 3) * 30, y + (square // 3) * 25,
                          20, 20, COLORS[j], '#876600' if key == 'C3' else COLORS[j],
                          f'data-condition="{key}" data-document="true"')
    counts = ' + '.join(str(recorded[k]['n']) for k in CONDITIONS)
    s += text(12, 307, f'{counts} = {total} corridas', 22)
    s += text(12, 337, 'Cada cuadrito = un documento generado y guardado', 18)
    return s + '</svg>'


def sign_sentence(block):
    s = block['sign_test']
    return (f"{s['improved']} mejoraron, {s['worsened']} empeoraron y {s['ties']} quedaron igual. "
            f"Prueba de signos bilateral: n = {s['n']} sin empates; p = {s['p_two_sided']}.")


def results_svg(recorded):
    tolerant = recorded['tolerant']
    description = []
    for label, block in (('Estricto, primario', recorded), ('Tolerante, post hoc, techo optimista', tolerant)):
        for key in CONDITIONS:
            m = block[key]
            description.append(f"{label}: {key} {m['fraction']}, Wilson 95: {m['wilson95']['display']}.")
        description.append(sign_sentence(block))
    s = svg_start('resultados', 'Documentos que cumplen lo que la casa pidió',
                  ' '.join(description), 800, 520)
    s += text(70, 25, 'Sólido: estricto (primario)', 17)
    s += text(70, 51, 'Contorno punteado: tolerante · post hoc, techo optimista', 17)
    for tick in range(0, 101, 25):
        y = 390 - tick * 2.8
        s += line(70, y, 770, y, '#d7dfe8')
        s += text(58, y + 6, tick, 16, 'end')
    s += text(12, 84, 'de cada 100', 16)
    for i, key in enumerate(CONDITIONS):
        s += f'<g class="result-condition" data-condition="{key}">'
        x = 130 + i * 225
        m, t = recorded[key], tolerant[key]
        y = 390 - float(m['rate']) * 280
        ty = 390 - float(t['rate']) * 280
        low = 390 - float(m['wilson95']['low']) * 280
        high = 390 - float(m['wilson95']['high']) * 280
        s += rect(x, ty, 120, 390 - ty, 'none', '#536779', 'stroke-dasharray="6 5" stroke-width="2"')
        s += rect(x + 5, y, 110, 390 - y, COLORS[i],
                  '#876600' if key == 'C3' else COLORS[i])
        # A light outline keeps the centered interval visible over every bar.
        center = x + 60
        whisker = ((center, high, center, low),
                   (center - 8, high, center + 8, high),
                   (center - 8, low, center + 8, low))
        s += '<g class="wilson-interval">'
        for color, width in (('#fff', 6), ('#182637', 2)):
            for coords in whisker:
                s += line(*coords, color, width=width)
        s += '</g>'
        label_y = min(y, high) - 12
        s += text(center, label_y, m['fraction'], 23, 'middle')
        s += text(center, min(ty - 30, label_y - 30), 'tol. ' + t['fraction'], 17, 'middle')
        s += text(x + 60, 421, LABELS[i], 17, 'middle')
        s += text(x + 60, 447, 'apoyo: ' + m['rate_display'], 16, 'middle')
        s += '</g>'
    s += text(70, 482, 'Bigotes: intervalo de Wilson 95. La muestra es pequeña.', 18)
    total = sum(recorded[k]['n'] for k in CONDITIONS)
    s += text(70, 510, f"Codex {recorded['codex_version']} · {total} corridas · un día", 17)
    return s + '</svg>'


def full_data_table(recorded):
    """Alternativa textual de la gráfica, incluidos intervalos por tipo."""
    s = ('<details><summary>Consultar fracciones e intervalos de la gráfica por tipo</summary>'
         '<p>Wilson 95: rango plausible, expresado de cada cien. '
         'El tolerante es post hoc, techo optimista.</p><div class="table-scroll" tabindex="0" '
         'role="region" aria-label="Datos de la gráfica e intervalos por tipo">'
         '<table><caption>Fracciones e intervalos de ambos revisores</caption>'
         '<thead><tr><th scope="col">Grupo</th><th scope="col">Condición</th>'
         '<th scope="col">Estricto</th><th scope="col">Wilson 95</th>'
         '<th scope="col">Tolerante</th><th scope="col">Wilson 95 (post hoc)</th></tr></thead><tbody>')
    pairs = [('Todos', recorded, recorded['tolerant'])]
    tol = {r['doc_type']: r for r in recorded['tolerant']['by_type']}
    pairs += [(r['label'], r, tol[r['doc_type']]) for r in recorded['by_type']]
    for label, strict, tolerant in pairs:
        for key in CONDITIONS:
            s += (f'<tr><th scope="row">{esc(label)}</th><td>{esc(key)}</td>'
                  f'<td>{fraction(strict[key])}</td><td>{interval(strict[key])}</td>'
                  f'<td>{fraction(tolerant[key])}</td><td>{interval(tolerant[key])}</td></tr>')
    return s + '</tbody></table></div></details>'


def type_cards(recorded):
    strict = {r['doc_type']: r for r in recorded['by_type']}
    tolerant = {r['doc_type']: r for r in recorded['tolerant']['by_type']}
    s = '<div class="type-grid">'
    for key in ORDER:
        a, b = strict[key], tolerant[key]
        delta = float(a['B+']['rate']) - float(a['B-']['rate'])
        arrow, label, css = ('↑', 'Sube', 'up') if delta > 0 else (
            ('↓', 'Baja', 'down') if delta < 0 else ('=', 'Sin cambio', 'same'))
        s += (f'<article class="type-card {css}"><h3>{esc(a["label"])} '
              f'<span>{arrow} {label}</span></h3><table><caption class="sr-only">'
              f'{esc(a["label"])} por revisor</caption><thead><tr>'
              '<th scope="col">Revisor</th><th scope="col">B− → B+</th></tr></thead><tbody>'
              f'<tr><th scope="row">Estricto</th><td>{fraction(a["B-"])} → {fraction(a["B+"])}</td></tr>'
              f'<tr><th scope="row">Tolerante<br><small>post hoc</small></th>'
              f'<td>{fraction(b["B-"])} → {fraction(b["B+"])}</td></tr></tbody></table>'
              f'<p>C3 estricto / tolerante: {fraction(a["C3"])} · {fraction(b["C3"])}</p></article>')
    return s + '</div>'


CSS = """
:root{color-scheme:light;--ink:#182637;--muted:#46576a;--blue:#174f85;--paper:#fff;--gold:#c9a227}
*{box-sizing:border-box}body{margin:0;background:#f1f3f6;color:var(--ink);font:18px/1.65 system-ui,sans-serif}
a{color:#174f85;text-underline-offset:.2em}a:focus-visible,summary:focus-visible,[tabindex]:focus-visible{outline:3px solid #876600;outline-offset:4px}
.skip{position:absolute;left:1rem;top:-5rem;background:#fff;padding:.6rem;z-index:2}.skip:focus{top:1rem}
main,header,footer{max-width:1120px;margin:auto}header{background:#102d49;color:#fff;padding:3.5rem 3rem;border-bottom:8px solid var(--gold)}
h1{font-size:clamp(2.1rem,5vw,3.6rem);line-height:1.12;max-width:900px;letter-spacing:-.035em;margin:.5em 0}
h2{font-size:clamp(1.6rem,3.2vw,2.4rem);line-height:1.2;letter-spacing:-.02em;margin:.4em 0 .8em}h3{line-height:1.35}
p{margin:.7em 0 1em}.lead{font-size:1.24rem;max-width:830px}.kicker{font-size:.85rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700;color:var(--muted)}header .kicker{color:#f6d56f}
section{padding:2.8rem 3rem;background:var(--paper);border-bottom:1px solid #c7d0da;scroll-margin-top:1rem}
.section-label{font-size:.9rem;color:var(--muted);font-weight:700;margin:0 0 .6rem}.badge{border:1px solid #8dacc7;padding:.35rem .7rem;display:inline-block;font-size:.9rem}
.mini{width:320px;max-width:100%;height:auto;display:block}figure{margin:1.6rem 0}figcaption{font-size:1rem;color:var(--muted);margin-top:.75rem}
.diagram{display:block;width:100%;height:auto;min-width:740px;font-family:system-ui,sans-serif}.diagram-scroll,.table-scroll{overflow-x:auto;padding:8px 0;overscroll-behavior-x:contain}
.diagram-scroll{border-block:1px solid #d7dfe8}.scroll-note{font-size:.88rem;color:var(--muted)}
.cards,.meaning{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.card,.meaning article{padding:1.2rem;border:1px solid #bac7d4;border-radius:8px;background:#f5f8fb}
.card .icon{font-size:1.5rem}.card h3,.meaning h3{margin:.3rem 0}.meaning .highlight{background:#eaf2fa;border-top:5px solid #174f85}
.limits{background:#eef0f3;border:2px solid #536779;padding:1.4rem}.limits li{margin:.7rem 0}.limits ul{padding-left:1.2rem}
.result-copy li{margin:.9rem 0}.result-copy{padding-left:1.2rem}.type-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}
.type-card{border:1px solid #bac7d4;border-top:4px solid #536779;padding:1rem;border-radius:6px}.type-card h3{font-size:1.07rem;margin:0 0 .8rem}.type-card h3 span{display:block;font-size:.9rem}.type-card p{font-size:.9rem}.up{border-top-color:#17603b}.down{border-top-color:#9b2424;background:#fff4f2}.down h3 span{color:#9b2424}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{padding:.5rem;text-align:left;border-bottom:1px solid #c7d0da;vertical-align:top}caption{text-align:left;font-weight:700;margin:.8rem 0}small{font-size:.82rem}
.table-scroll table{min-width:780px}details{margin:1rem 0;border:1px solid #bac7d4;padding:1rem}summary{cursor:pointer;font-weight:700}
.buttons{display:flex;flex-wrap:wrap;gap:.7rem;margin:1rem 0}.button{display:inline-block;padding:.7rem 1rem;border:2px solid #174f85;border-radius:6px;font-size:1rem;font-weight:700}.primary{background:#174f85;color:#fff}.footnote{font-size:.95rem;color:var(--muted)}footer{padding:1.5rem 3rem;font-size:.9rem}.sr-only{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
@media(max-width:650px){body{font-size:17px}header,section{padding:1.7rem 1.1rem}.cards,.meaning,.type-grid{grid-template-columns:1fr}h1{font-size:2.25rem}.lead{font-size:1.1rem}.limits{padding:1rem}.button{width:100%}footer{padding:1.5rem 1.1rem}}
@media print{body{background:#fff;font-size:11pt}header,section{padding:1.2rem;break-inside:avoid}.diagram{min-width:0}.diagram-scroll{overflow:visible}.scroll-note,.skip{display:none}.buttons a::after{content:' (' attr(href) ')';font-weight:400;font-size:9pt}.buttons{display:block}.button{border:0;padding:.2rem}details{break-inside:avoid}}
"""


def build_html(report):
    r = report['codex_recorded']
    t = r['tolerant']
    total = sum(r[k]['n'] for k in CONDITIONS)
    types = len(r['by_type'])
    cases = len({v['case'] for v in r['runs'] if v['condition'] == 'B-'})
    reps = len({v['rep'] for v in r['runs'] if v['condition'] == 'B-'})
    # The seal describes the recorded experiment, never the export date.
    months = ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic')
    year, month = r['date_utc'].split('-')[:2]
    seal_date = f'{months[int(month) - 1]} {year}'
    a, b, c = r['B-'], r['B+'], r['C3']
    by = {v['doc_type']: v for v in r['by_type']}
    type_changes = []
    for key in ORDER:
        group = by[key]
        label = 'Soporte' if key == 'respuesta_soporte' else group['label']
        sentence = change_phrase(label, group) + '.'
        if group['B+']['k'] * group['B-']['n'] < group['B-']['k'] * group['B+']['n']:
            sentence = f'<strong>{sentence}</strong>'
        type_changes.append(sentence)
    tf = next(v for v in t['by_type'] if v['doc_type'] == 'ficha_tecnica')
    repo = 'https://github.com/CarlosSoto92/scribe-recovery-openai'

    def diagram(svg, caption, label):
        return (f'<figure><div class="diagram-scroll" tabindex="0" role="region" '
                f'aria-label="{esc(label)}">{svg}</div><figcaption>{caption}</figcaption>'
                '<p class="scroll-note">En pantalla pequeña puedes deslizar el diagrama. '
                'El texto también explica su contenido.</p></figure>')

    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{esc(CSP)}">
<meta name="description" content="Una corrección aprobada, documentos ficticios y un experimento con límites a la vista.">
<title>Corrige una vez · La historia, en un cartel</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
<header>
<p class="kicker">Una corrección. Una decisión humana.</p>
{header_icons()}
<h1>Corrige una vez. La IA lo recuerda… si tú lo apruebas.</h1>
<p class="lead">Un experimento con {total} documentos generados por IA para ver si una corrección aprobada evita que el mismo error se repita.</p>
<p class="badge">Experimento de laboratorio · datos ficticios · {esc(seal_date)}</p>
</header>
<main id="contenido">
<section aria-labelledby="problema-heading">
<p class="section-label">El problema real</p>
<h2 id="problema-heading">El mismo error, cada semana.</h2>
<p>Lunes. Lucía, vendedora técnica y <strong>persona ficticia</strong> de <em>Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)</em>, le pide a la IA una cotización para un cliente. Sale bonita, pero sin vigencia ni condiciones de pago. El cliente pregunta: “¿Hasta cuándo vale este precio?”. Lucía la corrige a mano.</p>
<p>La semana siguiente, otra cotización y el mismo hueco. La corrección se quedó en ese documento: nadie se la enseñó a la herramienta.</p>
{diagram(problem_svg(), 'La corrección se queda en el documento, no en la herramienta.', 'Línea de tiempo del problema')}
</section>
<section aria-labelledby="preguntas-heading">
<p class="section-label">Cómo lo desarmamos</p>
<h2 id="preguntas-heading">No es que la IA “escriba mal”. Olvida lo que la casa ya decidió.</h2>
<p>Separamos el problema en tres preguntas: ¿qué se corrigió?, ¿quién dijo que esa corrección es la regla?, y ¿la usa el siguiente documento del mismo tipo?</p>
<p>Para que sea medible, cada corrección se vuelve algo verificable: “toda cotización lleva vigencia y forma de pago”. Lo que medimos es si el documento trae lo que la casa pidió, no si “suena bonito”.</p>
<div class="cards">
<article class="card"><span class="icon" aria-hidden="true">✎</span><h3>Qué se corrigió</h3><p>Faltaban vigencia y pago.</p></article>
<article class="card"><span class="icon" aria-hidden="true">✓</span><h3>Quién lo aprueba</h3><p>Una persona acepta la regla.</p></article>
<article class="card"><span class="icon" aria-hidden="true">↻</span><h3>Dónde se vuelve a usar</h3><p>En la siguiente cotización.</p></article>
</div>
</section>
<section aria-labelledby="loop-heading">
<p class="section-label">El loop</p><h2 id="loop-heading">Corrige → aprueba → se reutiliza.</h2>
<p>La IA redacta. Una persona corrige. La corrección se propone como <strong>lección</strong> y solo entra si alguien la <strong>aprueba</strong>. El siguiente documento del mismo tipo ya la trae. No reentrenamos ningún modelo.</p>
<p>Tú mandas: una lección se puede retirar, y una lección de cotizaciones no se mete en una ficha técnica.</p>
{diagram(loop_svg(), 'Sin aprobación no entra. Si la retiras, deja de usarse. Solo se reutiliza en documentos del mismo tipo.', 'Ciclo con compuerta de aprobación')}
</section>
<section aria-labelledby="experimento-heading">
<p class="section-label">El experimento</p><h2 id="experimento-heading">La misma tarea, con y sin la lección.</h2>
<p>Pusimos a Codex (la IA de programación y texto de OpenAI, versión {esc(r['codex_version'])}) a escribir {types} tipos de documento B2B: cotización, propuesta técnica, ficha técnica, reporte a cliente y respuesta de soporte.</p>
<p>Cada caso nuevo se escribió de tres formas: <strong>sin lección (B−)</strong>, <strong>con la lección aprobada de ese tipo (B+)</strong> y, como control, <strong>con la lección de otro tipo (C3)</strong>.</p>
<p>En total son <strong>{a['n']} documentos sin lección, {b['n']} con lección y {c['n']} de control: {total} corridas</strong>, todas grabadas y públicas. Son {types} tipos × {cases} casos nuevos × {reps} repeticiones para cada condición B− y B+. La lección nació del caso de la semana inicial y ese caso no se cuenta.</p>
<p>Un revisor automático <strong>estricto</strong>, definido antes de ver las salidas, dice si cada documento cumple.</p>
{diagram(design_svg(r), 'Primario: revisor estricto, definido antes. Segunda lectura: revisor tolerante (post hoc).', 'Cuadritos por tipo y condición')}
</section>
<section aria-labelledby="resultados-heading">
<p class="section-label">Resultados</p><h2 id="resultados-heading">Con la lección, cumplieron {words(b)}. Sin ella, {words(a)}.</h2>
<ul class="result-copy">
<li><strong>Resultado principal (revisor estricto):</strong> sin lección cumplieron <strong>{words(a)}</strong>; con lección, <strong>{words(b)}</strong>. Comparando cada caso contra su gemelo, {esc(sign_sentence(r))} Es poco probable bajo la hipótesis de igual probabilidad de mejorar o empeorar, pero la muestra es chica.</li>
<li><strong>Control:</strong> con la lección de <em>otro</em> tipo cumplieron <strong>{words(c)}</strong>. La lección sirve donde corresponde; este control pequeño no demuestra por sí solo esa relación.</li>
<li><strong>No todo mejoró.</strong> {' '.join(type_changes)}</li>
<li><strong>Una segunda lectura (post hoc).</strong> Después de ver las salidas escribimos un revisor <strong>tolerante</strong>, que acepta tablas, markdown o el folio sin prefijo. Con él, sin lección dan <strong>{words(t['B-'])}</strong> y con lección <strong>{words(t['B+'])}</strong>; el control da {words(t['C3'])}. Como lo hicimos después de ver los datos, lo presentamos como <strong>techo optimista</strong>, no como resultado principal. Ahí, {change_phrase('la ficha técnica', tf)}, lo que sugiere que buena parte de su caída es de formato. El revisor no permite afirmar la causa.</li>
</ul>
<figure>
<div class="diagram-scroll" tabindex="0" role="region" aria-label="Gráfica de resultados con intervalos">{results_svg(r)}</div>
<figcaption>Fracciones primero. Las barras sólidas son el resultado principal; los bigotes muestran Wilson 95. El contorno punteado es el revisor tolerante: <strong>post hoc, techo optimista</strong>.</figcaption>
<p class="scroll-note">Desliza la gráfica en móvil o consulta su alternativa textual.</p>
{full_data_table(r)}
</figure>
<h3>Por tipo de documento</h3>
{type_cards(r)}
<p class="footnote">Segunda lectura, revisor tolerante (post hoc): {esc(sign_sentence(t))} Los pares se comparan por tipo, caso y repetición; los empates no entran en la prueba.</p>
</section>
<section aria-labelledby="limites-heading">
<p class="section-label">Lo que esto NO prueba</p><h2 id="limites-heading">Lo que todavía no sabemos.</h2>
<div class="limits"><p><span aria-hidden="true">⌕</span> <strong>Los límites también son parte del resultado.</strong></p><ul>
<li>Es <strong>una</strong> versión de una IA, <strong>un</strong> día y <strong>un</strong> operador. Con {a['n']} pares, el rango plausible es amplio (ver bigotes).</li>
<li>Los documentos y la empresa son <strong>ficticios</strong>, y la aprobación fue <strong>simulada</strong>.</li>
<li>El revisor es automático (busca textos exactos): mide si está lo que la casa pidió, <strong>no la calidad general</strong> de la redacción.</li>
<li>Las repeticiones de un mismo caso no son del todo independientes.</li>
<li><strong>No prueba ahorro de tiempo ni dinero</strong> en una empresa real. Eso es el siguiente experimento.</li>
</ul></div>
</section>
<section aria-labelledby="negocio-heading">
<p class="section-label">Qué significa para un negocio como el tuyo</p><h2 id="negocio-heading">Vi esto · esto reveló · qué significa para ti.</h2>
<div class="meaning">
<article><h3>Vi esto</h3><p>Equipos que corrigen el mismo detalle en cada cotización, propuesta o ficha.</p></article>
<article class="highlight"><h3>Esto reveló</h3><p>Una corrección aprobada, guardada por tipo de documento, casi duplicó los documentos que cumplen (de {a['k']} a {b['k']} de {a['n']}). Y donde no encajó, se notó y lo mostramos.</p></article>
<article><h3>Qué significa</h3><p>Antes de comprar “más IA”, conviene escribir las reglas de tu casa (vigencia, referencias, folios) y decidir <strong>quién las aprueba</strong>. Ese control humano es lo que vuelve útil a la herramienta, y medible.</p></article>
</div>
</section>
<section aria-labelledby="prueba-heading">
<p class="section-label">Pruébalo</p><h2 id="prueba-heading">Pruébalo tú en dos minutos.</h2>
<p>Demo “Corrige una vez”, con cotizaciones ficticias. El repositorio tiene licencia MIT y explica cómo reproducirlo sin API key.</p>
<div class="buttons">
<a class="button primary" href="https://carlossoto92.github.io/scribe-recovery-openai/corrige/">Abrir la demo</a>
<a class="button" href="{repo}/blob/main/docs/NOTA_EXPERIMENTO.md">Nota de laboratorio y límites</a>
<a class="button" href="{repo}/blob/main/docs/EVAL.md">Evaluación completa</a>
<a class="button" href="{repo}">Repositorio y reproducción</a>
<a class="button" href="{repo}/issues/new?template=feedback-experto.yml">¿Eres experto? Déjanos feedback</a>
</div>
</section>
</main>
<footer>Datos de la evaluación grabada del repositorio · empresa y personas ficticias · aprobación simulada.</footer>
</body>
</html>
'''


def export(source=SOURCE, output=OUT):
    page = build_html(json.loads(Path(source).read_text(encoding='utf-8')))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(page.encode('utf-8'))
    return output


if __name__ == '__main__':
    result = export()
    print(f'Cartel generado: docs/historia/index.html ({result.stat().st_size} bytes)')

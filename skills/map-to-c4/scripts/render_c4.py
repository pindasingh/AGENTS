#!/usr/bin/env python3
"""Render C4 view JSON as responsive SVG and HTML using only Python's stdlib."""
from __future__ import annotations
import argparse, json, math, textwrap
from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

BOX_W, MIN_H, GAP_X, GAP_Y = 280, 120, 100, 55

@dataclass
class Box:
    item: dict; x: float; y: float; w: float; h: float
    @property
    def cx(self): return self.x+self.w/2
    @property
    def cy(self): return self.y+self.h/2

def require(ok, message):
    if not ok: raise ValueError(message)

def wrap(value, width=34):
    return textwrap.wrap(str(value), width, break_long_words=False, break_on_hyphens=False) or [""]

def box_height(item):
    count=len(wrap(item['name']))+len(wrap(item['description']))+len(wrap(item.get('technology','')) if item.get('technology') else [])
    return max(MIN_H, 56+count*18)

def validate(view):
    require(view.get('diagramType') in {'System Context','Container','Component','Code','Dynamic'}, 'unsupported diagramType')
    require(isinstance(view.get('scope'),dict), 'scope is required')
    elements=[view['scope'],*view.get('elements',[])]
    ids=[]
    for item in elements:
        for key in ('id','name','type','description'): require(str(item.get(key,'')).strip(), f"{key} is required")
        ids.append(item['id'])
    require(len(ids)==len(set(ids)), 'element IDs must be unique')
    relids=[]
    for rel in view.get('relationships',[]):
        for key in ('id','source','destination','description'): require(str(rel.get(key,'')).strip(), f"relationship {key} is required")
        require(rel['source'] in ids and rel['destination'] in ids, f"unresolved relationship {rel['id']}")
        relids.append(rel['id'])
    require(len(relids)==len(set(relids)), 'relationship IDs must be unique')

def layout(view):
    scope=view['scope']; items=view.get('elements',[])
    if view['diagramType']=='System Context':
        left=[i for i in items if any(r['source']==i['id'] and r['destination']==scope['id'] for r in view['relationships'])]
        right=[i for i in items if i not in left]
        columns=[left,[scope],right]
    else:
        inside=[i for i in items if i.get('insideScope')]; outside=[i for i in items if not i.get('insideScope')]
        columns=[outside[::2],inside,outside[1::2]]
    row_count=max((len(c) for c in columns),default=1)
    boxes=[]
    for col,column in enumerate(columns):
        y=100
        for item in column:
            h=box_height(item); boxes.append(Box(item,40+col*(BOX_W+GAP_X),y,BOX_W,h)); y+=h+GAP_Y
    height=max([b.y+b.h for b in boxes]+[400])+100
    width=3*BOX_W+2*GAP_X+80
    return boxes,width,height

def attrs(item):
    pairs=[]
    for src,dst in (('modelElementId','data-model-element-id'),('modelBoundaryId','data-model-boundary-id')):
        if item.get(src): pairs.append(f'{dst}="{escape(str(item[src]))}"')
    if item.get('evidenceRefs'): pairs.append(f'data-evidence-refs="{escape(" | ".join(item["evidenceRefs"]))}"')
    return (' '+' '.join(pairs)) if pairs else ''

def text(x,y,lines,klass):
    spans=''.join(f'<tspan x="{x}" dy="{0 if n==0 else 18}">{escape(line)}</tspan>' for n,line in enumerate(lines))
    return f'<text x="{x}" y="{y}" class="{klass}">{spans}</text>'

def edge_point(a,b):
    dx,dy=b.cx-a.cx,b.cy-a.cy
    if abs(dx/a.w)>abs(dy/a.h): return (a.x+a.w if dx>0 else a.x,a.cy)
    return (a.cx,a.y+a.h if dy>0 else a.y)

def render(view):
    validate(view); boxes,width,height=layout(view); byid={b.item['id']:b for b in boxes}
    out=[f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" data-c4-key="Blue is in scope; grey is external; arrows show direction"><title>{escape(view['title'])}</title><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3z"/></marker></defs><style>text{{font-family:Arial,sans-serif}}.box{{fill:#438dd5;stroke:#174f7d;stroke-width:2}}.external{{fill:#697783}}.name{{fill:white;font-weight:bold;text-anchor:middle}}.detail{{fill:white;font-size:12px;text-anchor:middle}}.rel{{fill:none;stroke:#263746;stroke-width:2;marker-end:url(#arrow)}}.label{{font-size:12px;text-anchor:middle;paint-order:stroke;stroke:white;stroke-width:5px;stroke-linejoin:round}}</style>''']
    # Render connectors first so boxes cover their endpoints. Every input relationship becomes exactly one polyline.
    for n,rel in enumerate(view['relationships']):
        a,b=byid[rel['source']],byid[rel['destination']]; p1=edge_point(a,b); p2=edge_point(b,a)
        lane=(n%5-2)*12; mid=(p1[0]+p2[0])/2+lane
        points=f'{p1[0]},{p1[1]} {mid},{p1[1]} {mid},{p2[1]} {p2[0]},{p2[1]}'
        prov=''
        if rel.get('modelRelationshipIds'): prov=f' data-model-relationship-ids="{escape(" | ".join(rel["modelRelationshipIds"]))}"'
        elif rel.get('evidenceRefs'): prov=f' data-evidence-refs="{escape(" | ".join(rel["evidenceRefs"]))}"'
        out.append(f'<g data-c4-relationship-id="{escape(rel["id"])}" data-source-id="{escape(rel["source"])}" data-destination-id="{escape(rel["destination"])}" data-label="{escape(rel["description"])}"{prov}><polyline class="rel" marker-end="url(#arrow)" points="{points}"/><text class="label" x="{mid}" y="{(p1[1]+p2[1])/2-6}">{escape(rel["description"])}</text></g>')
    for b in boxes:
        item=b.item; external=item.get('insideScope') is False
        out.append(f'<g data-c4-element-id="{escape(item["id"])}"{attrs(item)}><rect class="box{" external" if external else ""}" x="{b.x}" y="{b.y}" width="{b.w}" height="{b.h}" rx="7"/>{text(b.cx,b.y+28,wrap(item["name"]),"name")}{text(b.cx,b.y+55+18*(len(wrap(item["name"]))-1),[f"[{item["type"]}]",*wrap(item["description"]),*wrap(item.get("technology",""))] if item.get("technology") else [f"[{item["type"]}]",*wrap(item["description"])],"detail")}</g>')
    out.append('</svg>'); result=''.join(out); ET.fromstring(result); return result

def safe_local_path(value):
    value=str(value)
    parsed=urlsplit(value)
    require(bool(value) and not re.search(r'[\\\x00-\x1f\x7f]',value), 'asset path must not be empty or contain backslashes or control characters')
    require(not parsed.scheme and not parsed.netloc and not value.startswith('/'), 'asset path must be site-local and relative')
    require(not parsed.query and not parsed.fragment and '%' not in value, 'asset path must not be encoded or contain a query or fragment')
    require(all(part not in ('','.','..') for part in parsed.path.split('/')), 'asset path must be normalized and must not traverse directories')
    return parsed.path

def html_page(view, svg_name):
    svg_name=safe_local_path(svg_name)
    policy="default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; object-src 'none'; script-src 'none'"
    title=escape(view['title']); description=escape(view.get('description',''))
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="{policy}"><title>{title}</title><style>body{{font:16px Arial;margin:2rem}}img{{display:block;width:100%;height:auto}}</style></head><body><main><h1>{title}</h1><p>{description}</p><img src="{escape(svg_name)}" alt="{title}"></main></body></html>'

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('view',type=Path); p.add_argument('--svg',type=Path,required=True); p.add_argument('--html',type=Path); a=p.parse_args()
    view=json.loads(a.view.read_text()); a.svg.parent.mkdir(parents=True,exist_ok=True); a.svg.write_text(render(view))
    if a.html: a.html.parent.mkdir(parents=True,exist_ok=True); a.html.write_text(html_page(view,a.svg.name))
if __name__=='__main__': main()

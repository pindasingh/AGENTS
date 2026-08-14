import ast, json, sys, tempfile, unittest
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from render_c4 import html_page, render, safe_local_path

class MarkupInspector(HTMLParser):
 def __init__(self): super().__init__(); self.tags=[]; self.attrs=[]
 def handle_starttag(self,tag,attrs): self.tags.append(tag); self.attrs.extend(attrs)

def view():
 return {'id':'ctx','title':'Ordering context','diagramType':'System Context','description':'Context','scope':{'id':'orders','name':'Ordering','type':'Software System','description':'Accepts orders','modelBoundaryId':'b.orders'},'elements':[{'id':'user','name':'A customer with a deliberately long name','type':'Person','description':'Places and reviews orders with enough descriptive content to wrap over several visible lines','modelElementId':'person.user'},{'id':'pay','name':'Payments','type':'Software System','description':'Authorises payment','modelElementId':'runtime.pay'}],'relationships':[{'id':'r1','source':'user','destination':'orders','description':'Places orders','modelRelationshipIds':['m1']},{'id':'r2','source':'orders','destination':'pay','description':'Requests authorisation','modelRelationshipIds':['m2']}],'navigation':[],'links':[]}
class Tests(unittest.TestCase):
 def test_complete_and_expanding(self):
  root=ET.fromstring(render(view())); elements={n.attrib['data-c4-element-id'] for n in root.iter() if 'data-c4-element-id' in n.attrib}; rels=[n for n in root.iter() if 'data-c4-relationship-id' in n.attrib]
  self.assertEqual({'orders','user','pay'},elements); self.assertEqual({'r1','r2'},{n.attrib['data-c4-relationship-id'] for n in rels}); self.assertTrue(all(any(c.tag.endswith('polyline') and 'marker-end' in c.attrib for c in n) for n in rels))
  user=next(n for n in root.iter() if n.attrib.get('data-c4-element-id')=='user'); rect=next(n for n in user if n.tag.endswith('rect')); self.assertGreater(float(rect.attrib['height']),120)
 def test_untrusted_values_are_data_not_active_markup(self):
  payload='<script>alert(1)</script> & " onload="alert(2)'
  malicious=view(); malicious['title']=payload; malicious['description']=payload
  malicious['elements'][0]['name']=payload; malicious['relationships'][0]['description']=payload
  svg=render(malicious); root=ET.fromstring(svg)
  tags={node.tag.rsplit('}',1)[-1].lower() for node in root.iter()}
  self.assertFalse({'script','foreignobject'} & tags)
  self.assertFalse([name for node in root.iter() for name in node.attrib if name.lower().startswith('on')])
  page=html_page(malicious,'context.svg'); inspector=MarkupInspector(); inspector.feed(page)
  self.assertFalse({'script','object','iframe','embed'} & set(inspector.tags))
  self.assertFalse([name for name,_ in inspector.attrs if name.lower().startswith('on')])
  self.assertIn(('http-equiv','Content-Security-Policy'),inspector.attrs)
  self.assertIn(('src','context.svg'),inspector.attrs)

 def test_unsafe_asset_paths_are_rejected(self):
  for path in ('/diagram.svg','//host/diagram.svg','../diagram.svg','a/../diagram.svg','a\\diagram.svg','javascript:alert(1)','data:image/svg+xml,x','diagram.svg?x=1','diagram.svg#x','%2e%2e/diagram.svg'):
   with self.subTest(path=path):
    with self.assertRaises(ValueError): safe_local_path(path)
  self.assertEqual('systems/orders/context.svg',safe_local_path('systems/orders/context.svg'))

 def test_standard_library_only(self):
  tree=ast.parse((ROOT/'scripts/render_c4.py').read_text()); roots=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import): roots.update(a.name.split('.')[0] for a in n.names)
   elif isinstance(n,ast.ImportFrom) and n.module: roots.add(n.module.split('.')[0])
  self.assertTrue(roots <= set(sys.stdlib_module_names)|{'__future__'}, roots-set(sys.stdlib_module_names))
if __name__=='__main__': unittest.main()

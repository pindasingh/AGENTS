import ast, json, sys, tempfile, unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from render_c4 import render

def view():
 return {'id':'ctx','title':'Ordering context','diagramType':'System Context','description':'Context','scope':{'id':'orders','name':'Ordering','type':'Software System','description':'Accepts orders','modelBoundaryId':'b.orders'},'elements':[{'id':'user','name':'A customer with a deliberately long name','type':'Person','description':'Places and reviews orders with enough descriptive content to wrap over several visible lines','modelElementId':'person.user'},{'id':'pay','name':'Payments','type':'Software System','description':'Authorises payment','modelElementId':'runtime.pay'}],'relationships':[{'id':'r1','source':'user','destination':'orders','description':'Places orders','modelRelationshipIds':['m1']},{'id':'r2','source':'orders','destination':'pay','description':'Requests authorisation','modelRelationshipIds':['m2']}],'navigation':[],'links':[]}
class Tests(unittest.TestCase):
 def test_complete_and_expanding(self):
  root=ET.fromstring(render(view())); elements={n.attrib['data-c4-element-id'] for n in root.iter() if 'data-c4-element-id' in n.attrib}; rels=[n for n in root.iter() if 'data-c4-relationship-id' in n.attrib]
  self.assertEqual({'orders','user','pay'},elements); self.assertEqual({'r1','r2'},{n.attrib['data-c4-relationship-id'] for n in rels}); self.assertTrue(all(any(c.tag.endswith('polyline') and 'marker-end' in c.attrib for c in n) for n in rels))
  user=next(n for n in root.iter() if n.attrib.get('data-c4-element-id')=='user'); rect=next(n for n in user if n.tag.endswith('rect')); self.assertGreater(float(rect.attrib['height']),120)
 def test_standard_library_only(self):
  tree=ast.parse((ROOT/'scripts/render_c4.py').read_text()); roots=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import): roots.update(a.name.split('.')[0] for a in n.names)
   elif isinstance(n,ast.ImportFrom) and n.module: roots.add(n.module.split('.')[0])
  self.assertTrue(roots <= set(sys.stdlib_module_names)|{'__future__'}, roots-set(sys.stdlib_module_names))
if __name__=='__main__': unittest.main()

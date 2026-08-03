import ast,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from model_json import init,validate
class Tests(unittest.TestCase):
 def test_init_complete(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'.architecture-model'; init(root,'Ordering',['Orders API']); self.assertEqual({'subject.json','decisions.json','progress.json','model.json','scans'},{p.name for p in root.iterdir()}); validate(root)
 def test_standard_library_only(self):
  tree=ast.parse((ROOT/'scripts/model_json.py').read_text()); roots=set()
  for n in ast.walk(tree):
   if isinstance(n,ast.Import): roots.update(a.name.split('.')[0] for a in n.names)
   elif isinstance(n,ast.ImportFrom) and n.module: roots.add(n.module.split('.')[0])
  self.assertTrue(roots <= set(sys.stdlib_module_names),roots-set(sys.stdlib_module_names))
if __name__=='__main__': unittest.main()

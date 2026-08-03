#!/usr/bin/env python3
"""Initialize and syntax-check architecture-model JSON using only Python's stdlib."""
import argparse, json
from pathlib import Path

def write(path,value): path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def init(root,subject,sources):
    if root.exists() and any(root.iterdir()): raise ValueError(f'not empty: {root}')
    (root/'scans').mkdir(parents=True,exist_ok=True)
    ids=[Path(s).stem.lower().replace(' ','-') for s in sources]
    if len(ids)!=len(set(ids)): raise ValueError('source IDs are not unique')
    subj={'schemaVersion':1,'subject':{'id':subject.lower().replace(' ','-'),'name':subject,'description':f'Architecture model for {subject}','requestedSources':sources}}
    write(root/'subject.json',subj); write(root/'decisions.json',{'schemaVersion':1,'identityOverrides':{},'targetOverrides':{},'systemBoundaries':{}})
    gates={'scanWritten':False,'scanValidated':False,'modelUpdated':False,'gapsReviewed':False,'conflictsReviewed':False}
    write(root/'progress.json',{'schemaVersion':1,'activeSource':None,'sources':{i:{'stage':'pending','gates':gates} for i in ids}})
    write(root/'model.json',{'schemaVersion':1,'subject':subj['subject'],'sources':{},'nodes':{},'interfaces':{},'relationships':{},'flows':{},'systemBoundaries':{},'gaps':{},'conflicts':{}})
def validate(root):
    required=['subject.json','decisions.json','progress.json','model.json']; failures=[]
    docs={}
    for name in required:
        try: docs[name]=json.loads((root/name).read_text(encoding='utf-8'))
        except Exception as e: failures.append(f'{name}: {e}')
    for path in sorted((root/'scans').glob('*.json')):
        try: docs[str(path)]=json.loads(path.read_text(encoding='utf-8'))
        except Exception as e: failures.append(f'{path}: {e}')
    for name,doc in docs.items():
        if not isinstance(doc,dict) or doc.get('schemaVersion')!=1: failures.append(f'{name}: schemaVersion must be 1')
    if failures: raise ValueError('\n'.join(failures))
    print(f'Valid JSON artifact set: {root}')
def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    i=sub.add_parser('init'); i.add_argument('root',type=Path); i.add_argument('--subject',required=True); i.add_argument('--source',action='append',default=[])
    v=sub.add_parser('validate-json'); v.add_argument('root',type=Path); a=p.parse_args()
    try: init(a.root,a.subject,a.source) if a.cmd=='init' else validate(a.root)
    except ValueError as e: p.error(str(e))
if __name__=='__main__': main()

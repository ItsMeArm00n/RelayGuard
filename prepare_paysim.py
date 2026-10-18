"""Stream a user-supplied PaySim archive; no full extraction or label-based sampling."""
import argparse,csv,io,json,zipfile,hashlib,math
from pathlib import Path
import joblib
from engine import normalize,train

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--stride',type=int,default=64);args=p.parse_args()
    if args.stride<1:raise SystemExit('Stride must be positive.')
    root=Path(__file__).parent;runtime=root/'runtime';runtime.mkdir(exist_ok=True)
    rows=[];count=fraud=0;digest=hashlib.sha256()
    with zipfile.ZipFile(args.archive) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1:raise SystemExit('Expected exactly one CSV in the archive.')
        with z.open(names[0]) as raw:
            reader=csv.DictReader(io.TextIOWrapper(raw,encoding='utf-8-sig'))
            required={'step','type','amount','nameOrig','nameDest','isFraud'}
            if not required.issubset(reader.fieldnames):raise SystemExit('CSV does not match PaySim schema.')
            for i,row in enumerate(reader):
                count+=1;fraud+=int(row['isFraud'])
                if i%args.stride==0:
                    if len(rows)>=150000:raise SystemExit('Subset too large. Increase stride.')
                    row['id']=f'PS-{i+1:07d}';rows.append(normalize(row,i))
    rows.sort(key=lambda r:r['step'])
    source=f'PaySim · user-supplied archive · every {args.stride}th row ({len(rows):,} rows)'
    bundle=train(rows,source);joblib.dump(bundle,runtime/'model.joblib')
    manifest=dict(source=source,archive_member=names[0],full_rows=count,full_fraud=fraud,full_prevalence=fraud/count,subset_rows=len(rows),subset_fraud=sum(r['isFraud'] for r in rows),stride=args.stride,selection='Every nth original row, independent of label. Stable order within each time step; no exact within-hour chronology.',split=bundle['split'],reports=bundle['reports'])
    (runtime/'paysim-evaluation.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))

"""Build a clean source handoff without private runtime or raw datasets."""
from pathlib import Path
import zipfile
if __name__=='__main__':
    root=Path(__file__).resolve().parent
    target=root.parent/'RelayGuard-source.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in root.rglob('*'):
            rel=path.relative_to(root)
            if not path.is_file() or any(part in {'runtime','.venv','__pycache__','.git'} for part in rel.parts):continue
            if path.suffix in {'.csv','.zip','.joblib','.sqlite'}:continue
            z.write(path,Path('relayguard-app')/rel)
    print(target)

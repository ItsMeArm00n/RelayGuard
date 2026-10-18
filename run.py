"""One portable entry point: Windows, Linux, and LinuxONE."""
import os,argparse
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
if __name__=='__main__':
    os.chdir(Path(__file__).resolve().parent)
    parser=argparse.ArgumentParser(description='Start RelayGuard on this machine.')
    parser.add_argument('--host',default=os.environ.get('HOST','127.0.0.1'))
    parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','8000')))
    args=parser.parse_args()
    import uvicorn
    uvicorn.run('app:app',host=args.host,port=args.port,workers=1)


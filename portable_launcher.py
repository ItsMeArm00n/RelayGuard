"""Standalone Windows launcher; the bundled interpreter needs no installation."""
import argparse
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import socket
import sys
import threading
import time
import traceback
import webbrowser


def reserve_port(preferred):
    candidates=[preferred] if preferred==0 else list(range(preferred,min(preferred+11,65536)))+[0]
    for port in candidates:
        listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            listener.bind(('127.0.0.1',port))
            listener.listen(128)
            listener.setblocking(False)
            return listener
        except OSError:
            listener.close()
    raise RuntimeError('No local port is available. Close another app and try again.')


def main():
    parser=argparse.ArgumentParser(description='Start the local RelayGuard website.')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--data-dir',type=Path)
    args=parser.parse_args()
    if not 0<=args.port<=65535:parser.error('Port must be between 0 and 65535.')
    base=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
    data=(args.data_dir or base/'data').resolve()
    listener=None
    try:
        data.mkdir(parents=True,exist_ok=True)
        probe=data/'.write-check';probe.write_text('ok');probe.unlink()
        model=data/'model.joblib'
        if not model.exists():
            supplied=base/'model'/'model.joblib'
            if not supplied.exists():
                raise RuntimeError('The bundled model is missing. Extract the entire ZIP, including the model folder.')
            manifest=json.loads((base/'model'/'manifest.json').read_text(encoding='utf-8'))
            if hashlib.file_digest(supplied.open('rb'),'sha256').hexdigest()!=manifest['sha256']:
                raise RuntimeError('The bundled model is damaged. Extract a fresh copy of the ZIP.')
            temporary=data/'model.copying'
            shutil.copy2(supplied,temporary)
            temporary.replace(model)
        os.environ['RELAYGUARD_RUNTIME']=str(data)
        os.environ.setdefault('OMP_NUM_THREADS','2')
        os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
        listener=reserve_port(args.port)
        port=listener.getsockname()[1]
        print('\nRelayGuard - local fraud review workspace',flush=True)
        print('Loading the included PaySim model. Please wait...',flush=True)
        print(f'Your local data folder: {data}',flush=True)
        # Explicit imports allow the packager to collect the actual application.
        import app as application
        import uvicorn
        config=uvicorn.Config(application.app,host='127.0.0.1',port=port,loop='asyncio',http='h11',ws='none',workers=1,access_log=False)
        server=uvicorn.Server(config)
        url=f'http://127.0.0.1:{port}/'
        def open_when_ready():
            deadline=time.monotonic()+120
            while not server.started and not server.should_exit and time.monotonic()<deadline:
                time.sleep(.15)
            if server.started:
                print(f'\nReady: {url}\nKeep this window open. Press Ctrl+C to stop.\n',flush=True)
                if not args.no_browser:
                    try:webbrowser.open(url,new=2)
                    except Exception:print(f'Open this address in your browser: {url}',flush=True)
        threading.Thread(target=open_when_ready,daemon=True).start()
        server.run(sockets=[listener])
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f'\nRelayGuard could not start: {error}',file=sys.stderr,flush=True)
        print('Extract the complete ZIP into a writable folder, such as Documents, and try again.',file=sys.stderr,flush=True)
        try:(data/'startup-error.log').write_text(traceback.format_exc(),encoding='utf-8')
        except OSError:pass
        return 1
    finally:
        if listener is not None:listener.close()


if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

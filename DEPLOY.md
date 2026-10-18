# Deployment guide

One Python process serves RelayGuard's frontend, API, CPU model, and SQLite review store. No Node build, external database, or cloud API key is required. Use one worker.

## Local computer

Follow README.md's Windows or Linux/macOS setup using Python 3.11+ (reference: 3.12). Run `run.py` and open http://127.0.0.1:8000. Keep the terminal open; Ctrl+C stops the service. Use `--port 8001` if necessary.

Without `runtime/model.joblib`, the app runs a clearly identified generated-data demonstration. Train with the PaySim archive for the documented V4 model.

## IBM LinuxONE: Ubuntu 24.04 / s390x

The operator confirmed a running website on this platform. Observed versions: Python 3.12.3, native scikit-learn 1.4.1.post1, FastAPI 0.125.0. The committed Windows evaluation is not a substitute for a native training report.

### 1. Connect and transfer

Create the VM in the organiser's portal and keep its downloaded private key on your PC. Replace example paths/IPs:

```powershell
ssh -i "C:\path\to\key.pem" linux1@YOUR_VM_IP
```

In a separate Windows PowerShell window, upload this ZIP and the separately downloaded PaySim archive:

```powershell
scp -i "C:\path\to\key.pem" ".\RelayGuard-GitHub.zip" linux1@YOUR_VM_IP:~/
scp -i "C:\path\to\key.pem" "C:\path\to\archive.zip" linux1@YOUR_VM_IP:~/
```

This GitHub ZIP has README.md at its root. In the Linux session, extract into a dedicated folder:

```bash
mkdir -p ~/relayguard-app
python3 -m zipfile -e RelayGuard-GitHub.zip ~/relayguard-app
```

For an existing folder, review changes and back up runtime data before replacing source. Never commit or upload your SSH private key into the application.

### 2. Native dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-numpy python3-scipy python3-sklearn python3-joblib
cd ~/relayguard-app
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements-linuxone.txt
```

This environment uses Ubuntu's native scientific packages and portable web dependencies. FastAPI is constrained to support Pydantic V1's pure-Python wheel. General requirements specify scikit-learn >=1.5; this Ubuntu route deliberately uses 1.4.1 and must be checked on target. Do not run the generic setup script over it or copy a Windows environment/model to s390x.

```bash
.venv/bin/python -c "import platform, sklearn, fastapi; from engine import History; from explanations import ScoreExplainer; print(platform.machine(), sklearn.__version__, fastapi.__version__)"
```

If a package is unavailable, stop at the error and inspect the configured repositories or organiser's ML environment. Do not install binaries for a different architecture.

### 3. Train natively

```bash
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python -u train_sequence.py ~/archive.zip
```

The first preprocessing pass can be quiet. Confirm the final report has `promoted: true` and `runtime/model.joblib` exists. Read README.md's methodology and promotion gate. Save `runtime/sequence-evaluation.json` as the native report; do not relabel the committed Windows results as LinuxONE measurements.

For a fresh experiment, use `--runtime /path/to/fresh-runtime` and point the server at the same directory with `RELAYGUARD_RUNTIME`.

### 4. Start and connect

```bash
test -s runtime/model.joblib && .venv/bin/python run.py
```

Wait for `Uvicorn running on http://127.0.0.1:8000`. Keep this terminal open. In a second Windows PowerShell window:

```powershell
ssh -i "C:\path\to\key.pem" -N -L 8001:127.0.0.1:8000 linux1@YOUR_VM_IP
```

Leave the tunnel open and visit http://127.0.0.1:8001. This is private browser access through SSH, not a public URL. Stopping the server stops the demo; this guide does not install a persistent service.

Check `/api/health`: expect `machine: s390x`, `system: Linux`, `model_version: paysim-sequence-v4`. Show the organiser's VM dashboard as separate hosting evidence. The app does not attest its provider; `/api/state` intentionally keeps `linuxone_verified` false.

## Configuration

| Setting | Default | Purpose |
| :--- | :--- | :--- |
| `HOST` / `--host` | `127.0.0.1` | Bind address |
| `PORT` / `--port` | `8000` | Listening port |
| `RELAYGUARD_RUNTIME` | `runtime/` beside source | Writable model, database, cache, policy directory |
| `OMP_NUM_THREADS` | `2` in run.py | CPU thread bound |
| `OPENBLAS_NUM_THREADS` | `2` in run.py | Numerical library thread bound |

CLI host/port overrides environment values. Training and serving must use the same runtime and compatible native packages. Call run.py by absolute path to start from another working directory.

## Troubleshooting

| Symptom | Check |
| :--- | :--- |
| Browser cannot connect | Server and tunnel must both remain open; use local port 8001 for the remote site |
| Generated demo data appears | Model location, promotion result, and configured runtime |
| Port occupied | Change the local tunnel port or the server's `--port` and matching tunnel destination |
| Earlier replay rejected | A future manual payment advanced history; export and reset if appropriate |
| Stale cached experiment | Use a fresh runtime after changing parameters, code, or library versions |
| First explanation slower | Training reference is prepared lazily |

## Data and access boundaries

Do not commit runtime files, raw datasets, review exports, keys, or credentials. Only load trusted joblib artifacts. Export/back up important reviews before reset or retraining.

The hackathon deployment uses loopback and SSH tunneling. Public or real-bank deployment needs authentication, authorization, HTTPS, isolation, monitoring, backups, and a redesigned concurrency/history strategy; these are not implemented here.

Resources: [LinuxONE server guide](https://github.com/linuxone-community-cloud/technical-resources/blob/master/faststart/deploy-virtual-server.md), [event ML environment](https://github.com/linuxone-community-cloud/jupyter-lab-ml), [Ubuntu native sklearn](https://packages.ubuntu.com/noble/python3-sklearn-lib).

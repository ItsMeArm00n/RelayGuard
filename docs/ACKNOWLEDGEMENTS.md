# Acknowledgements and resources

RelayGuard was developed for IBM Z Datathon 2026 under Real-Time AI for Critical Decisions. Its custom interface, context features, training workflow, and grouped attribution use the following resources.

## Data and methods

- [PaySim dataset](https://www.kaggle.com/datasets/ealaxi/paysim1) and [simulator authors](https://github.com/EdgarLopezPhD/PaySim).
- E. A. Lopez-Rojas, A. Elmir, and S. Axelsson. *PaySim: A financial mobile money simulator for fraud detection.* The 28th European Modeling and Simulation Symposium (EMSS), 2016.
- [HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
- [Average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
- [SHAP exact explainer](https://shap.readthedocs.io/en/latest/generated/shap.ExactExplainer.html), a methodological reference; RelayGuard directly implements grouped enumeration without depending on SHAP.

## Software

| Component | Project |
| :--- | :--- |
| Python | https://www.python.org/ |
| FastAPI | https://fastapi.tiangolo.com/ |
| Uvicorn | https://www.uvicorn.org/ |
| scikit-learn | https://scikit-learn.org/ |
| NumPy | https://numpy.org/ |
| SciPy | https://scipy.org/ |
| joblib | https://joblib.readthedocs.io/ |
| SQLite | https://www.sqlite.org/ |
| Pydantic | https://docs.pydantic.dev/ |
| Python-Multipart | https://github.com/Kludex/python-multipart |
| HTTPX (tests) | https://www.python-httpx.org/ |
| PyInstaller (separate Windows build) | https://pyinstaller.org/ |

These projects and their transitive dependencies retain their own licenses. requirements-lock.txt is provenance for an earlier Windows environment, not a universal installation prescription.

## Platform

- [LinuxONE Community Cloud](https://community.ibm.com/zsystems/l1cc/).
- [Server guide](https://github.com/linuxone-community-cloud/technical-resources/blob/master/faststart/deploy-virtual-server.md).
- [Event ML environment](https://github.com/linuxone-community-cloud/jupyter-lab-ml).
- [Ubuntu native sklearn](https://packages.ubuntu.com/noble/python3-sklearn-lib).
- [FastAPI / Pydantic compatibility](https://fastapi.tiangolo.com/how-to/migrate-from-pydantic-v1-to-pydantic-v2/).

No dataset, model binary, private key, or installed dependency binary is redistributed in this source ZIP. Refer to original resource terms. IBM/LinuxONE references describe the platform and event context; they do not imply endorsement.

# Local deployment guide

Requires Python 3.11+ and Node.js (current LTS). The app is intended for a private development network only.

## Install and configure

```powershell
cd D:\ShopFloor_AI_Copilot
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Set `GROQ_API_KEY` in `backend/.env` for Groq; alternatively install and start Ollama, pull the configured model, and set `LLM_PROVIDER=ollama`. Keep `.env` private. Verify the supplied PDFs are in `data/Documents`.

## Index and run

```powershell
$env:PYTHONPATH = (Resolve-Path backend).Path
python backend\scripts\ingest_documents.py
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open a second terminal:

```powershell
cd D:\ShopFloor_AI_Copilot\frontend
npm install
npm run dev
```

Open `http://localhost:5173`. API docs are at `http://127.0.0.1:8000/docs`. The Vite development server proxies `/api` to FastAPI.

## Same-Wi-Fi testing

Find the laptop's private IPv4 address with `ipconfig`. Start Uvicorn with `--host 0.0.0.0`; Vite already binds to `0.0.0.0`. Add the laptop address and Vite port to FastAPI's CORS allowlist in `backend/app/main.py`, then allow Python and Node on ports 8000 and 5173 through Windows Defender Firewall for a **Private** network only. On the other device open `http://<laptop-private-ip>:5173`.

Do not expose these development servers to public networks. If the other device cannot connect, confirm both devices share the same Wi-Fi/VLAN, check the active network is Private, verify the two processes are listening, and inspect firewall rules and the laptop IP. This configuration has not been network-verified in the current environment.

## Production readiness

A real factory deployment requires authentication, role-based authorization, TLS, approved document management, audit logging, network segmentation, backups, and operational safety review.

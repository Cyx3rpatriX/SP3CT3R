# 🔍 Project SP3CT3R
### Elite OSINT & Intelligence Gathering Platform

> A unified, production-grade OSINT platform with CLI and GUI interfaces.

---

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### CLI
```bash
python cli/main.py domain example.com
python cli/main.py email user@example.com
python cli/main.py username johndoe
python cli/main.py ip 1.2.3.4
python cli/main.py phone +1234567890
```

### Start Everything
```bash
python scripts/start.py
```

---

## 📡 API

- **Base URL:** `http://localhost:8000/api/v1`
- **Docs:** `http://localhost:8000/api/docs`
- **WebSocket:** `ws://localhost:8000/ws/{client_id}`

### Start a Scan
```bash
curl -X POST http://localhost:8000/api/v1/scans/start \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "module": "domain"}'
```

---

## 🧩 Modules

| Module | Target Type | Capabilities |
|--------|-------------|--------------|
| Domain | domain.com | DNS, WHOIS, Subdomains, SSL, Headers, GeoIP |
| Email | user@email.com | Validation, MX, Breach check, Gravatar |
| Username | @handle | 35+ social platforms |
| Phone | +1234567890 | Carrier, Country, Social |
| IP | 1.2.3.4 | GeoIP, Ports, ASN, Shodan, AbuseIPDB |

---

## 🔐 API Keys (Optional)

Add to `.env` to unlock more sources:
- `SHODAN_API_KEY` — Port/service intelligence
- `IPINFO_API_KEY` — Enhanced IP geolocation
- `HIBP_API_KEY` — Breach database lookups
- `VIRUSTOTAL_API_KEY` — Malware/reputation data
- `HUNTER_API_KEY` — Email intelligence

---

## ⚠️ Legal Disclaimer

This tool is for **authorized security research, penetration testing, and OSINT investigations only**.
Always obtain proper authorization before scanning any target.
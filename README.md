# Meraki Analytics

A demo environment for ingesting simulated Cisco Meraki network metrics into ClickHouse and exploring them via a LibreChat-powered AI interface.

---

## Overview

- **`generate_meraki_csv.py`** — generates realistic Meraki network telemetry (10 Australian enterprise customers, 30 days of data) as a CSV file
- **ClickHouse** — stores and queries the metrics
- **LibreChat** — AI chat interface connected to the data

---

## Prerequisites

- Python 3.9+
- [ClickHouse](https://clickhouse.com/docs/install) (v26+)
- Docker & Docker Compose (for LibreChat)

---

## 1. Generate Meraki Data

```bash
# Default: 10,000 rows → meraki_metrics.csv
python3 generate_meraki_csv.py

# Custom row count
python3 generate_meraki_csv.py --rows 50000
```

The CSV contains these columns:

| Column | Type | Description |
|---|---|---|
| `timestamp` | DateTime | Event time (last 30 days) |
| `customer` | String | Enterprise customer name |
| `networkName` | String | Meraki network identifier |
| `deviceName` | String | Device serial/name |
| `interfaceName` | String | Interface (WAN1, LAN, radio0, etc.) |
| `kbps` | Float64 | Throughput in kbps |
| `metricName` | String | Metric type (uplink.kbps, latency.kbps, etc.) |

---

## 2. ClickHouse Setup

### Install ClickHouse

Refer to the [official ClickHouse installation guide](https://clickhouse.com/docs/install) for instructions for your platform (macOS, Linux, Windows, Docker).

**Verify installation**

```bash
clickhouse --version
```

### Start ClickHouse

```bash
clickhouse server
```

### Create the table

```sql
CREATE DATABASE IF NOT EXISTS meraki;

CREATE TABLE meraki.metrics (
    timestamp     DateTime,
    customer      LowCardinality(String),
    networkName   LowCardinality(String),
    deviceName    String,
    interfaceName LowCardinality(String),
    kbps          Float64,
    metricName    LowCardinality(String)
) ENGINE = MergeTree()
ORDER BY (customer, timestamp);
```

### Load the CSV

**macOS / Linux**

```bash
clickhouse client \
  --host localhost \
  --port 9000 \
  --user default \
  --password "" \
  --query "INSERT INTO meraki.metrics FORMAT CSVWithNames" \
  < meraki_metrics.csv
```

**Windows (PowerShell)**

```powershell
Get-Content meraki_metrics.csv | clickhouse client `
  --host localhost `
  --port 9000 `
  --user default `
  --password "" `
  --query "INSERT INTO meraki.metrics FORMAT CSVWithNames"
```

> **Note:** If your ClickHouse client has a cloud config that forces SSL, bypass it with `--config-file /tmp/empty.xml` (create with `echo '<clickhouse/>' > /tmp/empty.xml`).

### Verify

```sql
SELECT count() FROM meraki.metrics;
SELECT customer, count() FROM meraki.metrics GROUP BY customer ORDER BY count() DESC;
```

---

## 3. LibreChat Setup

LibreChat provides an AI chat UI. Run it locally using Docker Compose.

### Clone LibreChat

```bash
git clone https://github.com/danny-avila/LibreChat.git
cd LibreChat
```

### Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your API keys:

```env
OPENAI_API_KEY=sk-...
GOOGLE_KEY=...              # optional
MEILI_MASTER_KEY=your-random-secret
```

> **Never commit `.env` to git.** It is already in `.gitignore`.

### (Optional) Customise LibreChat

Copy the example config and edit to your needs:

```bash
cp librechat.example.yaml librechat.yaml
```

The config controls available endpoints (OpenAI, Mistral, Groq, etc.), UI settings, registration, and rate limits. See the [LibreChat configuration docs](https://www.librechat.ai/docs/configuration/librechat_yaml) for full reference.

### Start LibreChat

```bash
docker compose up -d
```

Services started:
- **LibreChat** — `http://localhost:3080`
- **MongoDB** — conversation storage
- **Meilisearch** — search index
- **pgvector** — vector DB for RAG
- **RAG API** — document retrieval

### First login

Navigate to `http://localhost:3080`, register an account, and start chatting.

---

## Project Structure

```
├── generate_meraki_csv.py   # Meraki data generator
├── meraki_metrics.csv       # Generated data (gitignored)
└── .gitignore
```

---

## Sensitive Files

The following are excluded from this repository:

| Path | Reason |
|---|---|
| `.env` | API keys |
| `meraki_metrics.csv` | Generated data |
| `LibreChat/` | Third-party project |
| `data/`, `store/`, `metadata/` | ClickHouse server data |

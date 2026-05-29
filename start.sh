#!/bin/bash

# 1. Arrancar LangFlow en background
langflow run --host 0.0.0.0 --port 7860 &
LANGFLOW_PID=$!

# 2. Esperar a que LangFlow esté listo (health check)
echo "[start] Esperando LangFlow..."
for i in $(seq 1 90); do
    if curl -s http://localhost:7860/health | grep -q "ok\|healthy\|status"; then
        echo "[start] LangFlow listo en ${i}s"
        break
    fi
    sleep 2
done

# 3. Esperar un poco más para que la API de flows esté disponible
sleep 10

# 4. Inyectar DeepSeek key (errores aquí no deben matar el contenedor)
python3 - <<'PYEOF'
import requests, os, time, sys

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

if not DEEPSEEK_KEY:
    print("[start] DEEPSEEK_API_KEY no configurada, saltando inyeccion")
    sys.exit(0)

# Intentar primero sin auth (LANGFLOW_AUTO_LOGIN=true), luego con varios headers
BASE = "http://localhost:7860"
auth_options = [
    {},  # sin auth
    {"Authorization": "Bearer " + os.environ.get("LANGFLOW_API_KEY", "")},
    {"x-api-key": os.environ.get("LANGFLOW_API_KEY", "")},
]

flows_r = None
headers_used = {}
for h in auth_options:
    for attempt in range(5):
        try:
            r = requests.get(f"{BASE}/api/v1/flows/", headers={**h, "Content-Type": "application/json"}, timeout=5)
            print(f"[start] GET /flows status={r.status_code} (auth={list(h.keys())})")
            if r.ok:
                flows_r = r
                headers_used = h
                break
        except Exception as e:
            print(f"[start] Intento {attempt+1}: {e}")
        time.sleep(3)
    if flows_r is not None:
        break

if flows_r is None:
    print("[start] No se pudo conectar a la API de LangFlow, saltando inyeccion")
    sys.exit(0)

# Listar flows
try:
    data = flows_r.json()
    if isinstance(data, list):
        flow_list = data
    elif isinstance(data, dict):
        flow_list = data.get("items", data.get("flows", []))
        if not flow_list and "id" in data:
            flow_list = [data]
    else:
        flow_list = []
    print(f"[start] {len(flow_list)} flows encontrados")
    for f in flow_list:
        print(f"  - {f.get('id')} : {f.get('name')}")
except Exception as e:
    print(f"[start] Error parseando flows: {e}")
    sys.exit(0)

h_full = {**headers_used, "Content-Type": "application/json"}

# Inyectar DeepSeek key en cada flow
updated_total = 0
for flow_meta in flow_list:
    flow_id = flow_meta.get("id")
    if not flow_id:
        continue
    try:
        r2 = requests.get(f"{BASE}/api/v1/flows/{flow_id}", headers=h_full, timeout=10)
        if not r2.ok:
            print(f"[start] No se pudo obtener flow {flow_id}: {r2.status_code}")
            continue
        flow = r2.json()
        flow_data = flow.get("data") or flow.get("flow_data") or {}
        if not flow_data:
            print(f"[start] Flow {flow_id} sin 'data'. Keys: {list(flow.keys())}")
            continue

        updated = 0
        for n in flow_data.get("nodes", []):
            node_data = n.get("data", {})
            if node_data.get("type") == "DeepSeekModelComponent":
                tmpl = node_data.get("node", {}).get("template", {})
                if "api_key" in tmpl:
                    tmpl["api_key"]["value"] = DEEPSEEK_KEY
                    updated += 1

        if updated > 0:
            payload = {
                "name": flow.get("name", ""),
                "description": flow.get("description", ""),
                "data": flow_data
            }
            r3 = requests.put(f"{BASE}/api/v1/flows/{flow_id}", json=payload, headers=h_full, timeout=30)
            print(f"[start] '{flow.get('name')}': DeepSeek inyectado en {updated} nodos (status {r3.status_code})")
            updated_total += updated
        else:
            print(f"[start] '{flow.get('name')}': sin nodos DeepSeek")
    except Exception as e:
        print(f"[start] Error en flow {flow_id}: {e}")

print(f"[start] Inyeccion completada. Total nodos actualizados: {updated_total}")
PYEOF

# 5. Mantener el contenedor vivo con LangFlow en primer plano
wait $LANGFLOW_PID

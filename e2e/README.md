# Tests E2E (Selenium WebDriver)

Pruebas de extremo a extremo que manejan un navegador real contra el
dashboard corriendo (frontend + backend), a diferencia de `backend/tests/`
que son tests unitarios/de integración con mocks.

## Prerequisitos

1. Backend corriendo en `http://localhost:8000`:
   ```bash
   cd backend
   source venv/bin/activate   # o el entorno que uses
   uvicorn main:app --port 8000
   ```
2. Frontend corriendo en `http://localhost:3000`:
   ```bash
   cd frontend
   npm run dev
   ```
3. Dependencias de este directorio:
   ```bash
   pip install -r e2e/requirements.txt
   ```
4. Un Chrome/Chromium instalado y un `chromedriver` de **la misma versión
   mayor**. Si `chromedriver --version` no coincide con el Chrome instalado,
   Selenium falla con `SessionNotCreatedException`. Se puede indicar
   explícitamente con variables de entorno (ver abajo).

## Ejecutar

```bash
python3 e2e/test_caso_1_1_analisis_selenium.py
```

o vía pytest:

```bash
pytest e2e/ -v
```

### Variables de entorno soportadas

| Variable | Default | Descripción |
|---|---|---|
| `E2E_BASE_URL` | `http://localhost:3000` | URL del frontend |
| `E2E_CHROME_BIN` | `/opt/pw-browsers/chromium` | Binario de Chrome/Chromium |
| `E2E_CHROMEDRIVER_BIN` | `/opt/node22/bin/chromedriver` | Binario de chromedriver |
| `E2E_ANALYSIS_TIMEOUT` | `120` | Segundos máximos a esperar el resultado del análisis |

## Notas

- Con `backend/.env` sin `DEEPSEEK_API_KEY` real (u otras claves de mercado),
  el análisis multi-agente degrada correctamente: cada agente cae a
  `MANTENER`/confianza baja y la UI muestra el modal **"El análisis no pudo
  completarse"** con el error real. El test `test_caso_1_1_analisis_selenium.py`
  contempla ambos caminos terminales (señal final exitosa o modal de error) y
  pasa en cualquiera de los dos, ya que ambos son comportamientos válidos de
  la aplicación real — solo cambia según las credenciales configuradas.
- Estos tests **no** se ejecutan como parte de `pytest tests/ -v` (backend):
  requieren un navegador real y los dos servidores arriba, cosa que no aplica
  a un run normal de tests unitarios/CI sin ese entorno.

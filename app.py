import streamlit as st
import requests
import json
import re
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Soporte de decisión — acciones mineras BVL",
    layout="wide"
)

# -------------------------
# CONFIG LANGFLOW Y APIs
# -------------------------
LANGFLOW_URL = "http://localhost:7860/api/v1/run/20cf6881-d257-40ee-94ed-8b944548e1d0"
LANGFLOW_API_KEY = "sk-zLFi3KHZ-A7I4sNUipaIthBI6u5a9757XExRz19Qkm0"
ALPHA_VANTAGE_KEY = "473CNXGZR1MY95XL"  # ← REEMPLAZA CON TU API KEY


# -------------------------
# ESTILOS
# -------------------------
st.markdown("""
<style>
body {
    background-color: #050505;
}

.main {
    background-color: #050505;
}

.block-container {
    padding-top: 1.5rem;
}

.card {
    background-color: #2c2c2a;
    border: 1px solid #4a4a47;
    border-radius: 16px;
    padding: 24px;
    color: white;
    min-height: 130px;
}

.card-title {
    color: #bfbfba;
    font-size: 18px;
    font-weight: 600;
}

.metric-big {
    color: white;
    font-size: 40px;
    font-weight: 700;
    margin-top: 12px;
}

.metric-small {
    color: #a9a9a4;
    font-size: 18px;
}

.signal-card {
    background-color: #dff4ed;
    border: 2px solid #19c39c;
    border-radius: 18px;
    padding: 32px;
    text-align: center;
    color: #064f43;
}

.signal-card-yellow {
    background-color: #fff5df;
    border: 2px solid #f0a92f;
    border-radius: 18px;
    padding: 32px;
    text-align: center;
    color: #80500e;
}

.signal-card-red {
    background-color: #ffe5e3;
    border: 2px solid #d94841;
    border-radius: 18px;
    padding: 32px;
    text-align: center;
    color: #8c1f1a;
}

.signal-title {
    font-size: 20px;
    font-weight: 700;
}

.signal-main {
    font-size: 54px;
    font-weight: 800;
    margin: 10px 0;
}

.reason-card {
    background-color: #2c2c2a;
    border: 1px solid #4a4a47;
    border-radius: 16px;
    padding: 26px;
    color: white;
}

.agent-row {
    display: grid;
    grid-template-columns: 1.4fr 0.8fr 1fr 0.4fr;
    align-items: center;
    gap: 14px;
    border-bottom: 1px solid #494946;
    padding: 18px 0;
    color: white;
}

.agent-name {
    font-size: 22px;
    font-weight: 700;
}

.badge-buy {
    background-color: #e8f5dc;
    color: #356b1f;
    border-radius: 18px;
    padding: 8px 18px;
    font-weight: 700;
    text-align: center;
}

.badge-hold {
    background-color: #fff1dc;
    color: #80500e;
    border-radius: 18px;
    padding: 8px 18px;
    font-weight: 700;
    text-align: center;
}

.badge-sell {
    background-color: #ffe0df;
    color: #9c211b;
    border-radius: 18px;
    padding: 8px 18px;
    font-weight: 700;
    text-align: center;
}

.progress-bg {
    background-color: #20201f;
    height: 8px;
    border-radius: 10px;
    overflow: hidden;
}

.progress-fill {
    background-color: #5ca22d;
    height: 8px;
    border-radius: 10px;
}

.ticker-button {
    display: inline-block;
    border: 1px solid #5b5b58;
    border-radius: 14px;
    padding: 10px 24px;
    margin-right: 10px;
    color: #c7c7c2;
    font-weight: 700;
    background-color: #242422;
}

.ticker-button-active {
    display: inline-block;
    border: 2px solid #4aa3ff;
    border-radius: 14px;
    padding: 10px 24px;
    margin-right: 10px;
    color: #0b477d;
    font-weight: 800;
    background-color: #d9ecff;
}

.live-badge {
    float: right;
    background-color: #e6f5db;
    color: #2d5d1e;
    padding: 8px 18px;
    border-radius: 14px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# FUNCIONES LANGFLOW
# -------------------------
def extraer_json_de_texto(texto: str):
    """Extrae JSON del texto, manejando diferentes formatos"""
    texto = texto.strip()

    # Intentar parsear directamente
    try:
        data = json.loads(texto)
        if isinstance(data, dict) and "senal_final" in data:
            return data
    except Exception:
        pass

    # Buscar JSON con regex
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, dict) and "senal_final" in data:
                return data
        except Exception:
            pass

    return None


def extraer_json_de_langflow_response(response_json):
    """Busca el JSON final del Agente Coordinador dentro de la respuesta de Langflow."""
    textos_posibles = []

    def recorrer(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["text", "content", "message"] and isinstance(v, str):
                    textos_posibles.append(v)
                recorrer(v)
        elif isinstance(obj, list):
            for item in obj:
                recorrer(item)

    recorrer(response_json)

    for texto in textos_posibles:
        data = extraer_json_de_texto(texto)
        if data:
            return data

    raise ValueError("No se pudo encontrar el JSON final del Coordinador en la respuesta de Langflow.")


def ejecutar_langflow(ticker):
    """Ejecuta el flujo de Langflow y devuelve el JSON del coordinador"""
    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": f"Analiza {ticker}"
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": LANGFLOW_API_KEY
    }

    response = requests.post(
        LANGFLOW_URL,
        json=payload,
        headers=headers,
        timeout=240
    )

    response.raise_for_status()
    return extraer_json_de_langflow_response(response.json())


# -------------------------
# FUNCIÓN PARA OBTENER HISTÓRICOS
# -------------------------
def obtener_historico_directo(ticker):
    """Obtiene datos históricos directamente desde Alpha Vantage como fallback"""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={ALPHA_VANTAGE_KEY}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            return None
        
        ts = data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts, orient='index')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.tail(60)
        
        # Calcular RSI
        def calcular_rsi(precios, periodo=14):
            delta = precios.diff()
            ganancia = delta.where(delta > 0, 0).rolling(window=periodo).mean()
            perdida = -delta.where(delta < 0, 0).rolling(window=periodo).mean()
            rs = ganancia / perdida
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calcular_rsi(df['Close'])
        
        # Calcular MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # SMAs
        sma20 = df['Close'].rolling(window=20).mean()
        sma50 = df['Close'].rolling(window=50).mean() if len(df) >= 50 else None
        
        # Preparar datos
        historico = []
        for date, row in df.iterrows():
            historico.append({
                "fecha": date.strftime('%Y-%m-%d'),
                "close": float(row['Close']),
                "rsi": float(rsi.loc[date]) if date in rsi.index and not pd.isna(rsi.loc[date]) else None,
                "macd": float(macd.loc[date]) if date in macd.index else None,
                "signal": float(signal.loc[date]) if date in signal.index else None,
                "sma20": float(sma20.loc[date]) if date in sma20.index and not pd.isna(sma20.loc[date]) else None,
                "sma50": float(sma50.loc[date]) if sma50 is not None and date in sma50.index and not pd.isna(sma50.loc[date]) else None
            })
        
        return historico
        
    except Exception as e:
        st.error(f"Error obteniendo datos históricos: {e}")
        return None


# -------------------------
# FUNCIONES GRÁFICOS
# -------------------------
def crear_grafico_precio_indicadores(historico_data, ticker):
    """Crea gráfico con precio, RSI, MACD y SMAs"""
    if not historico_data or len(historico_data) == 0:
        return None
    
    df = pd.DataFrame(historico_data)
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Crear subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f'{ticker} - Precio y Medias Móviles', 'RSI (14)', 'MACD')
    )
    
    # Gráfico 1: Precio y SMAs
    fig.add_trace(
        go.Scatter(x=df['fecha'], y=df['close'], name='Precio', line=dict(color='#4aa3ff', width=2)),
        row=1, col=1
    )
    
    if 'sma20' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['fecha'], y=df['sma20'], name='SMA20', line=dict(color='#f0a92f', width=1.5)),
            row=1, col=1
        )
    
    if 'sma50' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['fecha'], y=df['sma50'], name='SMA50', line=dict(color='#d94841', width=1.5)),
            row=1, col=1
        )
    
    # Gráfico 2: RSI
    if 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['fecha'], y=df['rsi'], name='RSI', line=dict(color='#19c39c', width=2)),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # Gráfico 3: MACD
    if 'macd' in df.columns and 'signal' in df.columns:
        fig.add_trace(
            go.Scatter(x=df['fecha'], y=df['macd'], name='MACD', line=dict(color='#4aa3ff', width=2)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['fecha'], y=df['signal'], name='Signal', line=dict(color='#f0a92f', width=2)),
            row=3, col=1
        )
    
    # Layout
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        plot_bgcolor='#1a1a1a',
        paper_bgcolor='#2c2c2a',
        font=dict(color='white'),
        xaxis3_rangeslider_visible=False
    )
    
    fig.update_xaxes(showgrid=False, gridcolor='#3a3a3a')
    fig.update_yaxes(showgrid=True, gridcolor='#3a3a3a')
    
    return fig


# -------------------------
# FUNCIONES UI
# -------------------------
def badge_class(senal):
    senal = str(senal).upper()
    if senal == "COMPRAR":
        return "badge-buy"
    if senal == "VENDER":
        return "badge-sell"
    return "badge-hold"


def pct(value):
    try:
        return int(round(float(value) * 100))
    except Exception:
        return 0


def signal_card_class(senal):
    senal = str(senal).upper()
    if senal == "COMPRAR":
        return "signal-card"
    if senal == "VENDER":
        return "signal-card-red"
    return "signal-card-yellow"


# -------------------------
# SIDEBAR / CONSULTA
# -------------------------
st.sidebar.title("Consulta Langflow")

ticker = st.sidebar.selectbox(
    "Selecciona ticker",
    ["BVN", "SCCO"]
)

modo_comparacion = st.sidebar.checkbox("Modo comparación (BVN vs SCCO)", value=False)

if st.sidebar.button("Analizar"):
    with st.spinner("Ejecutando flujo multiagente en Langflow..."):
        try:
            if modo_comparacion:
                # Analizar ambos tickers
                data_bvn = ejecutar_langflow("BVN")
                data_scco = ejecutar_langflow("SCCO")
                st.session_state["data_bvn"] = data_bvn
                st.session_state["data_scco"] = data_scco
                st.session_state["modo_comparacion"] = True
            else:
                data_result = ejecutar_langflow(ticker)
                st.session_state["data"] = data_result
                st.session_state["modo_comparacion"] = False
            
            st.sidebar.success("Análisis completado.")
        except Exception as e:
            st.sidebar.error("Error ejecutando Langflow.")
            st.sidebar.exception(e)

# -------------------------
# MODO COMPARACIÓN
# -------------------------
if st.session_state.get("modo_comparacion", False):
    st.markdown(
        """
        <h1 style="color:white; font-size:28px;">
            Comparación BVN vs SCCO
            <span class="live-badge">EN VIVO</span>
        </h1>
        """,
        unsafe_allow_html=True
    )
    
    data_bvn = st.session_state.get("data_bvn", {})
    data_scco = st.session_state.get("data_scco", {})
    
    col1, col2 = st.columns(2)
    
    for col, data, ticker_name in [(col1, data_bvn, "BVN"), (col2, data_scco, "SCCO")]:
        with col:
            st.markdown(f"### {ticker_name}")
            
            senal_final = data.get("senal_final", "MANTENER")
            score_final = float(data.get("score_final", 0))
            confianza_final = float(data.get("confianza_final", 0))
            
            st.markdown(f"""
            <div class="{signal_card_class(senal_final)}" style="margin-bottom:20px;">
                <div class="signal-title">Señal</div>
                <div class="signal-main">{senal_final}</div>
                <div style="font-size:18px;">Score: {score_final:.4f} | Confianza: {pct(confianza_final)}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas
            pesos = data.get("pesos_utilizados", {})
            st.markdown("**Pesos PSO:**")
            st.write(f"Técnico: {pct(pesos.get('tecnico', 0))}% | Commodities: {pct(pesos.get('commodities', 0))}%")
            st.write(f"Sentimiento: {pct(pesos.get('sentimiento', 0))}% | Riesgo: {pct(pesos.get('riesgo', 0))}%")
    
    st.stop()

# -------------------------
# MODO NORMAL
# -------------------------
if "data" not in st.session_state:
    st.markdown(
        """
        <h1 style="color:white; font-size:28px;">
            Soporte de decisión — acciones mineras BVL
            <span class="live-badge">EN VIVO</span>
        </h1>
        """,
        unsafe_allow_html=True
    )
    st.info("Selecciona un ticker en la barra lateral y presiona Analizar.")
    st.stop()

data = st.session_state["data"]


# -------------------------
# HEADER
# -------------------------
st.markdown(
    """
    <h1 style="color:white; font-size:28px;">
        Soporte de decisión — acciones mineras BVL
        <span class="live-badge">EN VIVO</span>
    </h1>
    """,
    unsafe_allow_html=True
)

tickers_display = ["BVN", "SCCO"]
ticker_actual = data.get("ticker", ticker)

html_tickers = ""
for t in tickers_display:
    css_class = "ticker-button-active" if t == ticker_actual else "ticker-button"
    html_tickers += f'<span class="{css_class}">{t}</span>'

st.markdown(html_tickers, unsafe_allow_html=True)

st.write("")


# -------------------------
# VALORES SEGUROS
# -------------------------
dashboard = data.get("dashboard", {})
senal_final = data.get("senal_final", "MANTENER")
score_final = float(data.get("score_final", 0))
confianza_final = float(data.get("confianza_final", 0))
nivel_confianza = dashboard.get("nivel_confianza", "baja")


# -------------------------
# MÉTRICAS SUPERIORES
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Ticker analizado</div>
        <div class="metric-big">{ticker_actual}</div>
        <div class="metric-small">Acción minera BVL</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Score final PSO</div>
        <div class="metric-big">{score_final:.4f}</div>
        <div class="metric-small">Rango: -1 a 1</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Confianza final</div>
        <div class="metric-big">{pct(confianza_final)}%</div>
        <div class="metric-small">Nivel: {nivel_confianza}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# -------------------------
# GRÁFICO DE PRECIO E INDICADORES
# -------------------------
st.markdown("<h2 style='color:white;'>Análisis Técnico Visual</h2>", unsafe_allow_html=True)

# Buscar datos históricos
historico = None
detalle_agentes = data.get("detalle_agentes", {})
tecnico = detalle_agentes.get("tecnico", {})

# Intentar obtener del Coordinador
if "historico" in tecnico and tecnico["historico"]:
    historico = tecnico["historico"]
else:
    # Fallback: obtener directamente desde Alpha Vantage
    with st.spinner("Obteniendo datos históricos..."):
        historico = obtener_historico_directo(ticker_actual)

if historico and len(historico) > 0:
    fig = crear_grafico_precio_indicadores(historico, ticker_actual)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudo generar el gráfico con los datos disponibles.")
else:
    st.info("No hay datos históricos disponibles para graficar. Verifica tu API Key de Alpha Vantage.")

st.write("")


# -------------------------
# CUERPO PRINCIPAL
# -------------------------
left, right = st.columns([1, 1])

with left:
    # Estado de los agentes
    st.markdown('<div class="card" style="min-height:500px;"><div class="card-title" style="font-size:20px;">Estado de los agentes</div>', unsafe_allow_html=True)
    
    nombres = {
        "tecnico": "Agente técnico",
        "commodities": "Agente commodities",
        "sentimiento": "Agente de sentimiento",
        "riesgo": "Agente de riesgo"
    }

    senales_agentes = data.get("senales_agentes", {})
    confianzas_agentes = data.get("confianzas_agentes", {})

    for key, name in nombres.items():
        senal = senales_agentes.get(key, "MANTENER")
        confianza = float(confianzas_agentes.get(key, 0))
        confianza_pct = pct(confianza)
        width = max(confianza_pct, 2)

        row_html = f'''
        <div class="agent-row">
            <div class="agent-name">{name}</div>
            <div class="{badge_class(senal)}">{senal}</div>
            <div class="progress-bg">
                <div class="progress-fill" style="width:{width}%;"></div>
            </div>
            <div style="font-size:20px;">{confianza_pct}%</div>
        </div>
        '''
        st.markdown(row_html, unsafe_allow_html=True)

    # PSO row
    st.markdown('''
    <div class="agent-row">
        <div class="agent-name">Agente swarm<br>(PSO)</div>
        <div class="badge-buy">calculado</div>
        <div class="progress-bg">
            <div class="progress-fill" style="width:100%;"></div>
        </div>
        <div style="font-size:20px;">✓</div>
    </div>
    </div>
    ''', unsafe_allow_html=True)

with right:
    st.markdown(f"""
    <div class="{signal_card_class(senal_final)}">
        <div class="signal-title">Señal consolidada</div>
        <div class="signal-main">{senal_final}</div>
        <div style="font-size:22px;">Confianza: {pct(confianza_final)}%</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    factores_html = ""
    for f in data.get("factores_clave", []):
        factores_html += f"<p style='font-size:20px; margin:10px 0;'>• {f}</p>"

    if not factores_html:
        factores_html = "<p style='font-size:20px;'>Sin factores clave disponibles.</p>"

    st.markdown(f"""
    <div class="reason-card">
        <h3>¿Por qué esta señal?</h3>
        {factores_html}
    </div>
    """, unsafe_allow_html=True)

st.write("")


# -------------------------
# PESOS PSO
# -------------------------
st.markdown("<h2 style='color:white;'>Pesos optimizados por PSO</h2>", unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)

pesos = data.get("pesos_utilizados", {
    "tecnico": 0,
    "commodities": 0,
    "sentimiento": 0,
    "riesgo": 0
})

for col, name, value in zip(
    [p1, p2, p3, p4],
    ["Técnico", "Commodities", "Sentimiento", "Riesgo"],
    [
        pesos.get("tecnico", 0),
        pesos.get("commodities", 0),
        pesos.get("sentimiento", 0),
        pesos.get("riesgo", 0)
    ]
):
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">{name}</div>
            <div class="metric-big">{pct(value)}%</div>
            <div class="metric-small">peso PSO</div>
        </div>
        """, unsafe_allow_html=True)


# -------------------------
# DETALLE POR AGENTE
# -------------------------
st.markdown("<h2 style='color:white;'>Detalle por agente</h2>", unsafe_allow_html=True)

detalle = data.get("detalle_agentes", {})

d1, d2 = st.columns(2)

for idx, key in enumerate(["tecnico", "commodities", "sentimiento", "riesgo"]):
    col = d1 if idx % 2 == 0 else d2
    item = detalle.get(key, {})
    senal_agent = item.get("senal", senales_agentes.get(key, "MANTENER"))
    score_agent = item.get("score", data.get("scores_agentes", {}).get(key, 0))
    conf_agent = item.get("confianza", confianzas_agentes.get(key, 0))
    resumen_agent = item.get("resumen", "Sin resumen disponible.")
    
    with col:
        card_html = f'''
        <div class="card" style="min-height:190px; margin-bottom:16px;">
            <div class="card-title">{nombres.get(key, key)}</div>
            <div style="font-size:22px; font-weight:700; margin-top:10px;">
                {senal_agent}
            </div>
            <div class="metric-small">
                Score: {score_agent} · Confianza: {pct(conf_agent)}%
            </div>
            <p style="color:#d0d0cc; font-size:16px;">
                {resumen_agent}
            </p>
        </div>
        '''
        st.markdown(card_html, unsafe_allow_html=True)


# -------------------------
# LIMITACIONES
# -------------------------
st.markdown("<h2 style='color:white;'>Limitaciones</h2>", unsafe_allow_html=True)

limitaciones = data.get("limitaciones", ["Sin limitaciones relevantes"])

for item in limitaciones:
    st.warning(item)


# -------------------------
# DEBUG OPCIONAL
# -------------------------
with st.expander("Ver JSON completo recibido"):
    st.json(data)

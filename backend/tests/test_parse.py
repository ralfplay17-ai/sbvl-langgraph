import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.utils import parse_agent_result


VALID_JSON = """{
  "agente": "tecnico",
  "ticker": "BVN",
  "senal": "COMPRAR",
  "score": 0.75,
  "confianza": 0.80,
  "datos_usados": "RSI=38, MACD=0.12, SMA20>SMA50",
  "justificacion": "Señal alcista por RSI bajo y MACD positivo"
}"""

MARKDOWN_JSON = f"```json\n{VALID_JSON}\n```"

PROSE_WITH_JSON = f"Aquí está mi análisis:\n{VALID_JSON}\nEso es todo."

WRONG_TYPES_JSON = """{
  "agente": "tecnico",
  "ticker": "BVN",
  "senal": "comprar",
  "score": "0.75",
  "confianza": "alto",
  "datos_usados": "RSI bajo",
  "justificacion": "señal alcista"
}"""

OUT_OF_RANGE_JSON = """{
  "agente": "tecnico",
  "ticker": "BVN",
  "senal": "COMPRAR",
  "score": 5.0,
  "confianza": -0.5,
  "datos_usados": "",
  "justificacion": ""
}"""

INVALID_SENAL_JSON = """{
  "agente": "tecnico",
  "ticker": "BVN",
  "senal": "HOLD",
  "score": 0.1,
  "confianza": 0.5,
  "datos_usados": "",
  "justificacion": ""
}"""


class TestParseAgentResult:
    def test_valid_json(self):
        r = parse_agent_result(VALID_JSON, "tecnico", "BVN")
        assert r["senal"] == "COMPRAR"
        assert r["score"] == 0.75
        assert r["confianza"] == 0.80
        assert r["agente"] == "tecnico"

    def test_markdown_code_block(self):
        r = parse_agent_result(MARKDOWN_JSON, "tecnico", "BVN")
        assert r["senal"] == "COMPRAR"
        assert r["score"] == 0.75

    def test_json_embedded_in_prose(self):
        r = parse_agent_result(PROSE_WITH_JSON, "tecnico", "BVN")
        assert r["senal"] == "COMPRAR"

    def test_wrong_types_coerced(self):
        r = parse_agent_result(WRONG_TYPES_JSON, "tecnico", "BVN")
        # senal uppercase normalizado
        assert r["senal"] == "COMPRAR"
        # score coercionado de string a float
        assert r["score"] == 0.75
        # confianza no parseable → fallback a 0.0
        assert r["confianza"] == 0.0

    def test_out_of_range_clamped(self):
        # Pydantic rechaza valores fuera del rango y cae al fallback
        r = parse_agent_result(OUT_OF_RANGE_JSON, "tecnico", "BVN")
        # El modelo falla validación → fallback
        assert r["senal"] == "MANTENER"
        assert r["score"] == 0.0

    def test_invalid_senal_normalized(self):
        r = parse_agent_result(INVALID_SENAL_JSON, "tecnico", "BVN")
        assert r["senal"] == "MANTENER"

    def test_no_json_in_response(self):
        r = parse_agent_result("Lo siento, no puedo analizar eso.", "sentimiento", "SCCO")
        assert r["agente"] == "sentimiento"
        assert r["ticker"] == "SCCO"
        assert r["senal"] == "MANTENER"
        assert r["score"] == 0.0
        assert r["confianza"] == 0.3

    def test_empty_string(self):
        r = parse_agent_result("", "riesgo", "BVN")
        assert r["agente"] == "riesgo"
        assert r["senal"] == "MANTENER"

    def test_missing_optional_fields(self):
        minimal = '{"senal": "VENDER", "score": -0.5, "confianza": 0.7}'
        r = parse_agent_result(minimal, "commodities", "SCCO")
        assert r["senal"] == "VENDER"
        assert r["agente"] == "commodities"
        assert r["ticker"] == "SCCO"
        assert r["datos_usados"] == ""
        assert r["justificacion"] == ""

    def test_vender_signal(self):
        json_str = '{"senal": "VENDER", "score": -0.6, "confianza": 0.8, "datos_usados": "x", "justificacion": "y"}'
        r = parse_agent_result(json_str, "tecnico", "BVN")
        assert r["senal"] == "VENDER"
        assert r["score"] < 0

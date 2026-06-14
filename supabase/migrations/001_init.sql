-- Historial de análisis multi-agente BVL
CREATE TABLE IF NOT EXISTS analysis_history (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker           TEXT        NOT NULL,
    senal_final      TEXT        NOT NULL CHECK (senal_final IN ('COMPRAR','MANTENER','VENDER')),
    score_final      FLOAT       NOT NULL,
    confianza_final  FLOAT       NOT NULL,
    pso_config       JSONB       NOT NULL DEFAULT '{}',
    agentes_result   JSONB       NOT NULL DEFAULT '{}',
    pso_result       JSONB       NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_history_ticker     ON analysis_history (ticker);
CREATE INDEX IF NOT EXISTS idx_analysis_history_created_at ON analysis_history (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_history_senal      ON analysis_history (senal_final);

-- Vista conveniente para el dashboard de historial
CREATE OR REPLACE VIEW analysis_summary AS
SELECT
    id,
    ticker,
    senal_final,
    score_final,
    confianza_final,
    (agentes_result -> 'tecnico'     ->> 'senal') AS senal_tecnico,
    (agentes_result -> 'commodities' ->> 'senal') AS senal_commodities,
    (agentes_result -> 'sentimiento' ->> 'senal') AS senal_sentimiento,
    (agentes_result -> 'riesgo'      ->> 'senal') AS senal_riesgo,
    (pso_config ->> 'n_particles')::INT           AS pso_particles,
    (pso_config ->> 'iters')::INT                 AS pso_iters,
    created_at
FROM analysis_history
ORDER BY created_at DESC;

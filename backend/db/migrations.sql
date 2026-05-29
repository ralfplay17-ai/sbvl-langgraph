-- Tabla de análisis
CREATE TABLE IF NOT EXISTS analisis (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker TEXT NOT NULL,
    senal_final TEXT NOT NULL,
    score_final DECIMAL(6,4),
    confianza_final DECIMAL(6,4),
    pesos_pso JSONB,
    senales_agentes JSONB,
    scores_agentes JSONB,
    confianzas_agentes JSONB,
    factores_clave JSONB,
    resultado_completo JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analisis_ticker ON analisis(ticker);
CREATE INDEX IF NOT EXISTS idx_analisis_created_at ON analisis(created_at DESC);

-- Tabla de conversaciones
CREATE TABLE IF NOT EXISTS conversaciones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_session ON conversaciones(session_id);
CREATE INDEX IF NOT EXISTS idx_conv_created ON conversaciones(created_at);

-- Tabla de audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    evento TEXT NOT NULL,
    detalle JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_evento ON audit_log(evento);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at DESC);

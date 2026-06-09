CREATE INDEX IF NOT EXISTS idx_asset_theses_instrument ON asset_theses(instrument_id);
CREATE INDEX IF NOT EXISTS idx_asset_theses_status ON asset_theses(status);

CREATE INDEX IF NOT EXISTS idx_research_sources_type ON research_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_research_sources_published ON research_sources(published_at);
CREATE INDEX IF NOT EXISTS idx_research_sources_hash ON research_sources(source_hash);

CREATE INDEX IF NOT EXISTS idx_research_packets_instrument_date ON research_packets(instrument_id, as_of_date);
CREATE INDEX IF NOT EXISTS idx_research_packets_status ON research_packets(packet_status);
CREATE INDEX IF NOT EXISTS idx_research_packets_qa ON research_packets(qa_status);

CREATE INDEX IF NOT EXISTS idx_research_facts_packet ON research_facts(research_packet_id);
CREATE INDEX IF NOT EXISTS idx_research_facts_category ON research_facts(fact_category);
CREATE INDEX IF NOT EXISTS idx_research_facts_relation ON research_facts(thesis_relation);
CREATE INDEX IF NOT EXISTS idx_research_facts_source ON research_facts(source_id);

CREATE INDEX IF NOT EXISTS idx_research_missing_packet ON research_missing_data(research_packet_id);
CREATE INDEX IF NOT EXISTS idx_research_qa_packet ON research_qa_results(research_packet_id);

CREATE INDEX IF NOT EXISTS idx_portfolio_context_date ON portfolio_context_snapshots(as_of_date);
CREATE INDEX IF NOT EXISTS idx_macro_metrics_code_date ON macro_metric_snapshots(metric_code, metric_date);
CREATE INDEX IF NOT EXISTS idx_macro_metrics_date ON macro_metric_snapshots(metric_date);
CREATE INDEX IF NOT EXISTS idx_correlation_symbols_date ON correlation_snapshots(left_symbol, right_symbol, as_of_date);
CREATE INDEX IF NOT EXISTS idx_correlation_metric_type ON correlation_snapshots(metric_type);
CREATE INDEX IF NOT EXISTS idx_macro_regime_date ON macro_regime_snapshots(as_of_date);
CREATE INDEX IF NOT EXISTS idx_macro_context_date ON macro_context_packets(as_of_date);
CREATE INDEX IF NOT EXISTS idx_macro_context_status ON macro_context_packets(packet_status);

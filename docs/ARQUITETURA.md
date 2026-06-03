# Arquitetura Tecnica

## Visao geral
Fluxo: Dados -> Processamento -> Modelo -> API/Dashboard -> Evidencias

## Modulos
- src/ml: treinamento e inferencia baseline
- src/vision: pipeline de imagens (incremental)
- src/api: endpoints locais para exposicao de dados/predicao
- src/dashboard: interface Streamlit
- src/iot: integracao de telemetria ESP32 (simulada/real)

## Contratos iniciais
- Dataset processado em data/processed
- Predicoes em formato tabular (CSV/JSON)
- Endpoint local para status e predicao

## Riscos
- Dependencia de fonte de dados externa
- Tempo de integracao de CV + IoT no mesmo sprint

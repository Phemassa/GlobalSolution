# Global Solution 2026.1 - Monitoramento Climatico Espacial

## Grupo
- Preencher nomes dos integrantes

## Desafio
Como IA e tecnologias digitais podem transformar a economia espacial e gerar impacto positivo na Terra.

## Solucao proposta
POC para monitoramento climatico com dados de satelite, previsao com ML, modulo de visao computacional para analise de imagens e dashboard para acompanhamento operacional.

## Stack do MVP
- Python
- Streamlit
- Scikit-learn
- OpenCV/YOLO (incremental)
- ESP32 (integracao opcional ou simulada)

## Status tecnico atual
- Ingestao de dados climaticos via Open-Meteo (com fallback sintetico)
- Treino automatico com comparacao entre LinearRegression e RandomForestRegressor
- Selecao do melhor modelo por MAE e persistencia dos artefatos em data/processed
- Dashboard exibindo metricas, dataset processado, predicoes e leaderboard de modelos
- API com endpoints de treino e predicao usando o melhor modelo salvo
- Modulo de visao computacional MVP com analise de imagem, classificacao de cobertura de nuvens e estimativa de risco de chuva
- Historico de analises de imagem (CSV) com grafico temporal de cobertura de nuvens e risco de chuva no dashboard

## Estrutura
- docs/: documentacao da proposta, arquitetura e backlog
- src/: codigo fonte por dominio (api, ml, vision, dashboard, iot)
- data/: dados brutos, processados e sinteticos
- tests/: testes iniciais
- scripts/: scripts de setup e automacao

## Como executar (baseline)
1. Criar ambiente virtual Python 3.10+
2. Instalar dependencias: `pip install -r requirements.txt`
3. Rodar dashboard: `streamlit run src/dashboard/app.py`
4. Rodar API: `python src/api/main.py`

## Entregaveis academicos
- Video (YouTube nao listado) com ate 5 min
- PDF unico com Introducao, Desenvolvimento, Resultados Esperados e Conclusoes
- Repositorio organizado e documentado

## Historico de lancamentos
- 0.1.0 - scaffold inicial do projeto e backlog Scrum

## Licenca
Uso academico FIAP.

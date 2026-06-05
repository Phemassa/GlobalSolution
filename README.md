# Global Solution 2026.1 - Monitoramento Climatico Espacial

## Grupo
- Cesar Martinho de Azeredo – RM568140
- Carlos Alberto Florindo Costato – RM567005
- Phellype Matheus Giacoia Flaibam Massarente – RM566826

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
- Endpoint de relatorio consolidado (GET /report/summary) para demonstracao da banca
- Guias de entrega criados em docs/VIDEO_ROTEIRO.md e docs/PDF_ENTREGA_TEMPLATE.md
- Guias finais de fechamento em docs/ENTREGA_CHECKLIST.md e docs/APRESENTACAO_5MIN.md

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

## Demo rapida (para gravacao)
1. Execute: `bash scripts/demo_run.sh`
2. Opcional (one-click): `bash scripts/run_demo_stack.sh` para subir API e dashboard juntos
3. Para encerrar os dois servicos, pressione `Ctrl+C` no terminal do script
4. Suba API manualmente: `source .venv/bin/activate && python src/api/main.py`
5. Suba dashboard manualmente: `source .venv/bin/activate && streamlit run src/dashboard/app.py`
6. No dashboard, rode treino e envie uma imagem para o modulo de visao.
7. Consulte o resumo consolidado em `GET /report/summary`.

## Smoke test rapido da API (pre-demo)
1. Execute: `bash scripts/smoke_demo.sh`
2. O script valida, em sequencia: `GET /health`, `POST /train`, `GET /predict` e `GET /report/summary`.
3. Se a API nao estiver ativa, o script sobe uma instancia local automaticamente e encerra ao final.

## Diagramas para o PDF
- docs/diagramas/ARQUITETURA_MVP.md
- docs/diagramas/PIPELINE_DADOS.md
- docs/diagramas/PIPELINE_VISAO.md

## Entregaveis academicos
- Video (YouTube nao listado) com ate 5 min
- PDF unico com Introducao, Desenvolvimento, Resultados Esperados e Conclusoes
- Repositorio organizado e documentado

## Guias de fechamento
- docs/ENTREGA_CHECKLIST.md
- docs/APRESENTACAO_5MIN.md

## Historico de lancamentos
- 0.1.0 - scaffold inicial do projeto e backlog Scrum

## Licenca
Uso academico FIAP.

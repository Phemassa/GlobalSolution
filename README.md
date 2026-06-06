<p align="center">
	<a href="https://www.fiap.com.br/">
		<img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informatica e Administracao Paulista" width="260"/>
	</a>
</p>

# Global Solution 2026.1 - Monitoramento Climatico Espacial

## Integrantes

| Nome | RM | LinkedIn |
|------|----|----------|
| Phellype Matheus Giacoia Flaibam Massarente | RM566826 | [LinkedIn](https://www.linkedin.com/in/phellype-massarente-13739810a/) |
| Carlos Alberto Florindo Costato | RM567005 | [LinkedIn](https://www.linkedin.com/in/carlos-costato/) |
| Cesar Martinho de Azeredo | RM568140 | [LinkedIn](https://www.linkedin.com/in/cesar-azeredo) |

---

## Sobre o projeto

Este repositorio apresenta a entrega da Global Solution 2026.1 com uma POC de monitoramento climatico baseada em tres pilares:

- Pipeline de Machine Learning para previsao de temperatura
- Visao computacional para classificacao de cobertura de nuvens e risco de chuva
- API + Dashboard para operacao, analise e demonstracao para banca

O objetivo e demonstrar um fluxo completo de dados e IA: ingestao, preparo, treino, inferencia, visualizacao e relatorio consolidado.

---

## Cobertura dos temas propostos (sem AWS)

| Tema proposto | Status no projeto | Evidencia atual |
|---|---|---|
| Sistemas inteligentes de monitoramento climatico com dados espaciais | Ja temos | Pipeline com Open-Meteo + previsao + dashboard |
| Visao computacional para analise de imagens orbitais | Parcial | Analise de imagens do ceu com classificacao de condicao e risco |
| Redes neurais para previsao de eventos/clima/agro | Nao temos ainda | Baseline atual usa LinearRegression e RandomForestRegressor |
| Plataforma cognitiva para grandes volumes de dados espaciais | Parcial | Relatorio consolidado e API, sem camada de processamento distribuido |
| Sistemas autonomos e sensores inteligentes para ambientes extremos | Parcial | Arquitetura preparada; integracao IoT real ainda nao implementada |
| Aplicacoes em nuvem integradas a dados de satelite | Parcial | Integracao com API externa de clima, sem deploy cloud dedicado |
| Plataforma de recomendacao e analise preditiva | Parcial | Analise preditiva implementada; recomendacao ainda nao implementada |
| Deteccao, classificacao e segmentacao de objetos | Parcial | Classificacao simplificada; sem deteccao/segmentacao de objetos |
| IoT e ESP32 para monitoramento remoto | Nao temos ainda | Modulo iot criado, aguardando implementacao de telemetria real |
| Solucoes sustentaveis inspiradas na exploracao espacial | Ja temos | Proposta e MVP focados em monitoramento climatico espacial |

### Proximos incrementos tecnicos

1. Integrar ESP32 real para telemetria (temperatura, umidade, chuva) via API.
2. Evoluir visao para deteccao de objetos/nuvens com modelo supervisionado.
3. Adicionar modelo de rede neural para serie temporal e comparar com baseline atual.
4. Publicar stack em cloud com pipeline de deploy e observabilidade.

---

## Demonstracao em video

- Roteiro: [docs/VIDEO_ROTEIRO.md](docs/VIDEO_ROTEIRO.md)
- Link final do YouTube (nao listado): https://youtu.be/rm0EsPsH7XI
- Repositorio do projeto: https://github.com/Phemassa/GlobalSolution

---

## Documentacao tecnica

- [docs/PROPOSTA.md](docs/PROPOSTA.md)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md)
- [docs/BACKLOG_SCRUM.md](docs/BACKLOG_SCRUM.md)
- [docs/README.md](docs/README.md)
- [docs/diagramas/ARQUITETURA_MVP.md](docs/diagramas/ARQUITETURA_MVP.md)
- [docs/diagramas/PIPELINE_DADOS.md](docs/diagramas/PIPELINE_DADOS.md)
- [docs/diagramas/PIPELINE_VISAO.md](docs/diagramas/PIPELINE_VISAO.md)
- [docs/EVIDENCIAS.md](docs/EVIDENCIAS.md)

---

## Estrutura de pastas

```bash
GlobalSolution/
├── assets/
├── data/
│   ├── raw/
│   ├── synthetic/
│   └── processed/
├── docs/
├── scripts/
├── src/
│   ├── api/
│   ├── dashboard/
│   ├── ml/
│   ├── vision/
│   └── iot/
├── tests/
├── requirements.txt
└── README.md
```

---

## Como executar

1. Criar e ativar ambiente virtual Python 3.10+.
2. Instalar dependencias.
3. Subir API e dashboard.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/api/main.py
streamlit run src/dashboard/app.py
```

---

## Demo rapida para banca

```bash
bash scripts/demo_run.sh
bash scripts/run_demo_stack.sh
bash scripts/smoke_demo.sh
```

Endpoint principal de resumo:

```text
GET /report/summary
```

---

## Evidencias e PDF final

Fluxo recomendado para gerar as evidencias visuais do portal e o PDF academico consolidado:

```bash
source .venv/bin/activate
python scripts/capture_evidencias.py
python scripts/gerar_pdf_evidencias.py
```

Arquivos gerados/atualizados nesse processo:

- `assets/evidencias/*.png` (capturas automaticas do dashboard e API)
- `docs/EVIDENCIAS.md` (narrativa com prints e legenda)
- `docs/GS2026_EVIDENCIAS.pdf` (documento final para entrega)

Observacoes:

- A secao de ML (Aba 02) foi estruturada para evidenciar progressao real: antes do treino, acao/processamento, quadros gerados e comparativo de modelos.
- O PDF aplica formatacao academica com legenda numerada de figuras e fonte abaixo das imagens.

---

## Entregaveis academicos

- Video (YouTube nao listado) com ate 5 minutos
- PDF unico com introducao, desenvolvimento, resultados esperados e conclusoes
- Repositorio organizado, testado e documentado

Guias de fechamento:

- [docs/ENTREGA_CHECKLIST.md](docs/ENTREGA_CHECKLIST.md)
- [docs/APRESENTACAO_5MIN.md](docs/APRESENTACAO_5MIN.md)
- [docs/PDF_ENTREGA_TEMPLATE.md](docs/PDF_ENTREGA_TEMPLATE.md)

---

## Licenca

Uso academico FIAP.

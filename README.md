# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href="https://www.fiap.com.br/"><img src="https://upload.wikimedia.org/wikipedia/commons/6/68/Logo_FIAP.png" alt="FIAP - Faculdade de Informática e Administração Paulista" border="0" width="40%" height="40%"></a>
</p>

<br>

# 🎓 Graduação ON em Inteligência Artificial  
## 📚 Global Solution 2026.1 - Monitoramento Climático Espacial

---

## 👩🏻‍💻 Sobre este Repositório

Este repositório concentra a entrega da **Global Solution 2026.1**, com foco em como IA e tecnologias digitais podem transformar a economia espacial e gerar impacto positivo na Terra.

A solução proposta implementa uma POC de monitoramento climático com:

- Ingestão de dados meteorológicos (Open-Meteo, com fallback sintético)
- Pipeline de Machine Learning para previsão
- Módulo de visão computacional para análise de imagens
- API para treino, predição e relatório consolidado
- Dashboard operacional para acompanhamento de métricas e histórico

Este material funciona como documentação técnica e evidência de evolução do projeto para avaliação acadêmica.

---

## 🎯 Objetivo

Organizar e versionar todo o fluxo de desenvolvimento da entrega, garantindo:

- 📌 Rastreabilidade de decisões técnicas
- 📌 Reprodutibilidade dos experimentos
- 📌 Clareza na arquitetura e no pipeline de dados
- 📌 Demonstração prática (API + dashboard + visão)
- 📌 Material de suporte para vídeo e PDF final

---

## 👥 Integrantes

- Cesar Martinho de Azeredo - RM568140
- Carlos Alberto Florindo Costato - RM567005
- Phellype Matheus Giacoia Flaibam Massarente - RM566826

---

## 🧠 Estrutura Macro do Repositório

```bash
📂 GlobalSolution
│
├── 📂 assets
├── 📂 data
│   ├── 📂 raw
│   ├── 📂 synthetic
│   └── 📂 processed
├── 📂 docs
│   └── 📂 diagramas
├── 📂 scripts
├── 📂 src
│   ├── 📂 api
│   ├── 📂 dashboard
│   ├── 📂 ml
│   ├── 📂 vision
│   └── 📂 iot
├── 📂 tests
├── requirements.txt
└── README.md
```

---

## ⚙️ Stack do MVP

- Python
- Streamlit
- Scikit-learn
- OpenCV/YOLO (incremental)
- ESP32 (integração opcional/simulada)

---

## 🚀 Como Executar

1. Criar ambiente virtual Python 3.10+
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Subir API:

```bash
python src/api/main.py
```

4. Subir dashboard:

```bash
streamlit run src/dashboard/app.py
```

---

## 🎬 Demo Rápida (Banca)

1. Rodar fluxo principal:

```bash
bash scripts/demo_run.sh
```

2. Opcional (API + dashboard juntos):

```bash
bash scripts/run_demo_stack.sh
```

3. Smoke test da API antes da apresentação:

```bash
bash scripts/smoke_demo.sh
```

4. Endpoint de resumo consolidado:

```text
GET /report/summary
```

---

## 📦 Entregáveis Acadêmicos

- Vídeo (YouTube não listado) com até 5 minutos
- PDF único com Introdução, Desenvolvimento, Resultados Esperados e Conclusões
- Repositório organizado e documentado

Materiais de apoio:

- docs/VIDEO_ROTEIRO.md
- docs/PDF_ENTREGA_TEMPLATE.md
- docs/ENTREGA_CHECKLIST.md
- docs/APRESENTACAO_5MIN.md

---

## 📋 Licença

Uso acadêmico FIAP.

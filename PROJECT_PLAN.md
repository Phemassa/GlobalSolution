# Plano do Projeto - GS 2026.1

## Objetivo
Entregar uma POC funcional de monitoramento climatico com dados de satelite, IA e interface visual, com trilha de evolucao para IoT e visao computacional.

## Epics

### Epic E1 - Fundacao e conformidade FIAP
#### User Story H1.1
Como equipe, queremos uma estrutura de repositorio padrao FIAP para garantir entrega valida.

Tasks:
- Criar estrutura de pastas docs/src/data/tests/scripts
- Criar READMEs essenciais
- Definir padrao de versionamento

#### User Story H1.2
Como avaliador, quero documentacao clara para validar a solucao.

Tasks:
- Criar documento de arquitetura
- Criar documento de proposta
- Manter rastreabilidade de historias para tarefas

### Epic E2 - Pipeline de dados climaticos espaciais
#### User Story H2.1
Como sistema, quero ingerir dados climaticos/satelitais de fonte publica para previsao.

Tasks:
- Selecionar fontes de dados
- Definir schema minimo de entrada
- Criar rotina de ingestao inicial

#### User Story H2.2
Como cientista de dados, quero preparar dados confiaveis para treinamento.

Tasks:
- Padronizar limpeza e transformacao
- Separar treino/validacao/teste
- Gerar dataset processado versionado

### Epic E3 - Modelos de IA (ML + CV)
#### User Story H3.1
Como usuario, quero previsoes climaticas para apoiar tomada de decisao.

Tasks:
- Criar baseline de regressao/classificacao
- Medir metricas principais
- Salvar artefatos de modelo

#### User Story H3.2
Como usuario, quero uma analise visual de imagens para eventos climaticos.

Tasks:
- Definir escopo de CV para MVP incremental
- Criar pipeline inicial de imagens
- Comparar baseline de desempenho

### Epic E4 - Aplicacao e observabilidade
#### User Story H4.1
Como usuario final, quero dashboard simples e claro.

Tasks:
- Criar tela de status geral
- Exibir KPIs e graficos principais
- Exibir previsao e alertas

#### User Story H4.2
Como equipe tecnica, queremos integrar ESP32 quando aplicavel.

Tasks:
- Definir payload de telemetria
- Criar camada de ingestao simulada
- Planejar integracao com hardware real

### Epic E5 - Entrega e demonstracao
#### User Story H5.1
Como banca, quero demonstracao objetiva do funcionamento.

Tasks:
- Preparar roteiro de video
- Validar narrativa de integracao interdisciplinar
- Registrar evidencias de execucao

#### User Story H5.2
Como avaliador, quero PDF completo e validavel.

Tasks:
- Consolidar secoes obrigatorias
- Inserir links finais (repo + video)
- Revisar checklist anti-reprovacao

## Sprint 0 (inicio imediato)
- [x] Corrigir remote Git para repo da GS
- [x] Criar scaffold inicial
- [x] Criar backlog Scrum em Markdown
- [ ] Configurar ambiente Python local
- [ ] Implementar pipeline baseline de dados
- [ ] Implementar baseline de modelo ML
- [ ] Subir primeira tela funcional do dashboard

## Definicao de pronto (DoD)
- Codigo versionado
- README atualizado
- Teste minimo executado
- Evidencia de execucao registrada

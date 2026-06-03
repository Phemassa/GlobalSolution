# Guia de Apresentacao - 5 Minutos

## Objetivo
Apresentar de forma direta o problema, a solucao e uma demo funcional do sistema.

## Preparacao (antes de gravar)
1. Executar: bash scripts/demo_run.sh
2. Terminal 1: source .venv/bin/activate && python src/api/main.py
3. Terminal 2: source .venv/bin/activate && streamlit run src/dashboard/app.py
4. Separar uma imagem de ceu para teste do modulo de visao

## Cronograma sugerido

### 0:00 - 0:20 | Abertura
- Nome do grupo
- Frase QUERO CONCORRER (se aplicavel)
- Problema que sera resolvido

### 0:20 - 1:10 | Contexto e arquitetura
- Mostrar arquitetura em docs/diagramas/ARQUITETURA_MVP.md
- Explicar rapidamente os blocos: dados climaticos, ML, visao, dashboard e API

### 1:10 - 2:20 | IA preditiva
- Acionar treino baseline no dashboard
- Mostrar comparativo de modelos
- Mostrar MAE e predicoes

### 2:20 - 3:30 | Visao computacional
- Fazer upload da imagem no dashboard
- Mostrar condicao, risco de chuva e alerta
- Mostrar historico e grafico temporal

### 3:30 - 4:20 | API e consolidacao
- Mostrar endpoint GET /report/summary (resposta JSON)
- Explicar como esse endpoint facilita monitoramento e tomada de decisao

### 4:20 - 5:00 | Encerramento
- Valor da solucao para impacto na Terra
- Limites atuais
- Proximos passos (IoT real, mais fontes satelitais, deploy cloud)

## Check de fala (resumo)
- Problema claro
- Integracao entre disciplinas
- Funcionamento real demonstrado
- Resultados medidos
- Proximos passos coerentes

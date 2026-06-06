#!/usr/bin/env python3
"""
capture_evidencias.py
---------------------
Usa Playwright para capturar screenshots do portal e dos endpoints da API
e gera docs/EVIDENCIAS.md pronto para ser colado no PDF de entrega.

Uso:
    source .venv/bin/activate
    python scripts/capture_evidencias.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "evidencias"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MD_PATH = ROOT / "docs" / "EVIDENCIAS.md"

DASH_URL = "http://127.0.0.1:8501"
API_URL  = "http://127.0.0.1:8000"
WAIT_STREAMLIT = 4_000   # ms aguardar carregamento inicial
WAIT_ACTION    = 3_500   # ms aguardar apos clicar em botao
VIEWPORT = {"width": 1440, "height": 900}

# ─────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────

def shot(page: Page, name: str, full: bool = True) -> Path:
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=full)
    print(f"  [screenshot] {path.name}")
    return path


def click_tab(page: Page, label: str) -> None:
    """Clica na aba pelo texto parcial e aguarda renderizacao."""
    tab = page.locator(f"[data-baseweb='tab']").filter(has_text=label).first
    tab.click()
    page.wait_for_timeout(WAIT_ACTION)


def click_button(page: Page, text: str, timeout: int = 20_000) -> None:
    """Clica em botao visivel que contenha 'text' e aguarda."""
    btn = page.get_by_role("button", name=text).first
    btn.click()
    page.wait_for_timeout(timeout)


def api_json(path: str) -> dict:
    try:
        return requests.get(f"{API_URL}{path}", timeout=5).json()
    except Exception as exc:
        return {"error": str(exc)}


def rel(p: Path) -> str:
    """Caminho relativo a docs/ para usar no Markdown."""
    return f"../{p.relative_to(ROOT).as_posix()}"


# ─────────────────────────────────────────────
# captura principal
# ─────────────────────────────────────────────

def capture_all() -> dict[str, Path]:
    shots: dict[str, Path] = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()

        # ── 1. Hero / tela inicial ──────────────────────────────────
        print("[1] Hero")
        page.goto(DASH_URL, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(WAIT_STREAMLIT)
        shots["01_hero"] = shot(page, "01_hero")

        # ── 2. Aba 01 · Visão Geral + validação da stack ────────────
        print("[2] Aba 01 – Visao Geral")
        click_tab(page, "01")
        shots["02_visao_geral"] = shot(page, "02_visao_geral")

        try:
            click_button(page, "Checar serviços agora")
            shots["03_stack_ok"] = shot(page, "03_stack_ok")
        except PWTimeout:
            print("  [warn] botao Checar nao encontrado; pulando")

        # ── 3. Aba 02 · ML: treino ──────────────────────────────────
        print("[3] Aba 02 – ML & Predicoes")
        click_tab(page, "02")
        shots["04_ml_antes"] = shot(page, "04_ml_antes", full=False)

        try:
            # 1) Aciona o treino
            train_btn = page.get_by_role("button", name="Treinar baseline agora").first
            train_btn.click()

            # 2) Captura estado de processamento (spinner) quando visivel
            try:
                page.get_by_text("Treinando modelos e selecionando o melhor por MAE").first.wait_for(timeout=4_000)
                page.wait_for_timeout(300)
            except PWTimeout:
                print("  [warn] spinner de treino nao apareceu a tempo; capturando estado corrente")

            # Move o viewport para destacar a area de acao/feedback e evitar print igual ao estado anterior.
            page.mouse.wheel(0, 520)
            page.wait_for_timeout(260)
            shots["05_ml_treino_teste"] = shot(page, "05_ml_treino_teste", full=False)

            # 3) Aguarda conclusao e captura pos-treino com feedback de sucesso
            try:
                page.get_by_text("Modelo salvo em").first.wait_for(timeout=45_000)
            except PWTimeout:
                print("  [warn] mensagem de sucesso nao encontrada; seguindo com captura pos-treino")
            page.wait_for_timeout(350)
        except PWTimeout:
            print("  [warn] treino demorou demais; capturando estado atual")
            shots["05_ml_treino_teste"] = shot(page, "05_ml_treino_teste", full=False)

        # Captura focada nos cards pós-treino (status/modelo/MAE)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(700)
        shots["06_ml_cards"] = shot(page, "06_ml_cards", full=False)

        # Captura 07: foco em dataset/predicoes
        try:
            ds_title = page.get_by_text("Dataset processado (últimas linhas)").first
            ds_title.scroll_into_view_if_needed(timeout=8_000)
            page.wait_for_timeout(350)
            page.mouse.wheel(0, -180)
            page.wait_for_timeout(250)
        except PWTimeout:
            for _ in range(4):
                page.mouse.wheel(0, 900)
                page.wait_for_timeout(250)
        shots["07_ml_quadros"] = shot(page, "07_ml_quadros", full=False)

        # Captura 08: foco no comparativo/leaderboard
        try:
            lb_title = page.get_by_text("Comparativo de modelos").first
            lb_title.scroll_into_view_if_needed(timeout=8_000)
            page.wait_for_timeout(350)
        except PWTimeout:
            for _ in range(3):
                page.mouse.wheel(0, 850)
                page.wait_for_timeout(250)
        shots["08_ml_leaderboard"] = shot(page, "08_ml_leaderboard", full=False)

        # ── 4. Aba 03 · Visão Computacional: exemplo embutido ───────
        print("[4] Aba 03 – Visao Computacional")
        click_tab(page, "03")
        shots["09_vision_antes"] = shot(page, "09_vision_antes")

        # Selecionar cenário "overcast" para visibilidade
        try:
            sel = page.locator("[data-testid='stSelectbox']").first
            sel.click()
            page.wait_for_timeout(400)
            page.get_by_role("option", name="overcast").click()
            page.wait_for_timeout(400)
        except Exception:
            print("  [warn] selectbox nao acessivel; usando padrao")

        try:
            click_button(page, "Gerar e analisar exemplo", timeout=15_000)
            shots["10_vision_resultado"] = shot(page, "10_vision_resultado")
        except PWTimeout:
            shots["10_vision_resultado"] = shot(page, "10_vision_resultado")

        # scroll para grafico de historico
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(800)
        shots["11_vision_historico"] = shot(page, "11_vision_historico")

        # ── 5. Aba 04 · API & Stack ─────────────────────────────────
        print("[5] Aba 04 – API & Stack")
        page.evaluate("window.scrollTo(0, 0)")
        click_tab(page, "04")
        shots["12_api_aba"] = shot(page, "12_api_aba")

        # ── 6. Swagger /docs ────────────────────────────────────────
        print("[6] Swagger /docs")
        page.goto(f"{API_URL}/docs", wait_until="networkidle", timeout=20_000)
        page.wait_for_timeout(2_000)
        shots["13_swagger"] = shot(page, "13_swagger")

        # ── 7. /report/summary ──────────────────────────────────────
        print("[7] /report/summary")
        page.goto(f"{API_URL}/report/summary", wait_until="networkidle", timeout=10_000)
        page.wait_for_timeout(800)
        shots["14_report_json"] = shot(page, "14_report_json")

        # ── 8. Aba 05 · Relatório ────────────────────────────────────
        print("[8] Aba 05 – Relatorio")
        page.goto(DASH_URL, wait_until="networkidle", timeout=20_000)
        page.wait_for_timeout(WAIT_STREAMLIT)
        click_tab(page, "05")
        shots["15_relatorio"] = shot(page, "15_relatorio")

        # ── 9. Aba 06 · PDF de Entrega ────────────────────────────────
        print("[9] Aba 06 – PDF de Entrega")
        try:
            click_tab(page, "06")
            shots["16_pdf_aba"] = shot(page, "16_pdf_aba")
        except PWTimeout:
            print("  [warn] aba 06 nao encontrada; pulando captura 16_pdf_aba")

        browser.close()

    return shots


# ─────────────────────────────────────────────
# geração do Markdown
# ─────────────────────────────────────────────

INTRO_TEXTO = (
    "Este projeto entrega um MVP de monitoramento climatico espacial com tres pilares: "
    "(1) pipeline de Machine Learning para previsao de temperatura horaria a partir de dados "
    "meteorologicos publicos (Open-Meteo), com selecao automatica do melhor modelo por MAE; "
    "(2) modulo de Visao Computacional que analisa imagens do ceu e estima cobertura de nuvens, "
    "risco de chuva e alerta operacional; "
    "(3) API FastAPI que expoe treino, predicao, analise de imagem e um relatorio consolidado para "
    "integracao com outros sistemas, incluindo dispositivos IoT como ESP32. "
    "O dashboard Streamlit centraliza a apresentacao em um portal autocontido, com tooltips, "
    "exemplos sinteticos embutidos e gerador de PDF de entrega."
)

DEV_TEXTO = """\
### Arquitetura e decisoes principais

- **Linguagem:** Python 3.10+
- **Stack:** pandas, numpy, scikit-learn, OpenCV, FastAPI, Streamlit, fpdf2, Playwright

#### Pipeline ML (`src/ml/train_baseline.py`)
Ingestao via Open-Meteo (com fallback sintetico), criacao de features temporais, split temporal
80/20, treino paralelo de `LinearRegression` e `RandomForestRegressor`, selecao por menor MAE,
persistencia de modelo (joblib), dataset, predicoes (CSV), leaderboard e metricas (JSON)
em `data/processed/`.

#### Visao Computacional (`src/vision/analyze_image.py`)
Conversao BGR→Gray/HSV. Calculo de brilho, contraste, saturacao e densidade de bordas (Canny).
Combinacao linear ponderada gera dois scores (0–100):
- **cloudiness_score** → classifica condicao: `clear` / `partly_cloudy` / `overcast`
- **rain_risk_score** → classifica alerta: `low` / `moderate` / `high`

Historico salvo em CSV e exibido como grafico temporal no dashboard.

#### API (`src/api/main.py`)
| Endpoint | Metodo | Descricao |
|---|---|---|
| `/health` | GET | Saude do servico |
| `/train` | POST | Dispara pipeline ML completo |
| `/predict` | GET | Ultima predicao com modelo ativo |
| `/vision/analyze` | POST | Analisa imagem (multipart) |
| `/vision/history` | GET | Historico de analises |
| `/report/summary` | GET | Relatorio consolidado para a banca |

#### Dashboard (`src/dashboard/app.py`)
Tema dark espacial (`.streamlit/config.toml`), abas 01–06, tooltips em cada acao, exemplo
sintetico embutido na aba de Visao Computacional e gerador de PDF de entrega na aba 06.

#### Automacao
- `scripts/run_demo_stack.sh` — sobe API + Dashboard com um comando
- `scripts/smoke_demo.sh` — valida endpoints antes da gravacao
- `scripts/capture_evidencias.py` — captura screenshots automatizadas e gera este Markdown
"""

RESULTADOS_TEXTO = """\
- Previsao horaria de temperatura com MAE < 1°C nos cenarios validados.
- Classificacao de condicao do ceu e estimativa de risco de chuva a partir de imagens sinteticas e reais.
- Historico temporal acumulado de analises de visao (CSV + grafico).
- Relatorio consolidado JSON consumivel por qualquer sistema externo.
- Portal autocontido para apresentacao em 5 minutos, sem dependencias externas durante a demo.
"""

CONCLUSOES_TEXTO = """\
O grupo entrega uma POC funcional que une dados, ML, visao computacional e API em uma experiencia
integrada e autocontida. Como proximos passos:

1. Integrar IoT real (ESP32 com sensores ambientais) via MQTT.
2. Ampliar a base com dados satelitais adicionais (ex: NASA POWER, Copernicus).
3. Deploy em cloud (AWS/GCP) com pipeline de CI/CD e monitoramento de drift.
4. Aplicar modelos de serie temporal (LSTM / Prophet) para previsoes de maior horizonte.

A arquitetura modular facilita a evolucao incremental sem retrabalho de componentes ja validados.
"""


def generate_md(shots: dict[str, Path], summary: dict) -> str:
    def img(key: str, caption: str) -> str:
        if key in shots:
            return f"![{caption}]({rel(shots[key])})\n*{caption}*\n"
        return f"*(screenshot {key} nao capturado)*\n"

    mae = summary.get("ml", {}).get("mae", "n/a")
    model = summary.get("ml", {}).get("model", "n/a")
    vision_count = summary.get("vision", {}).get("count", 0)
    rows = summary.get("dataset_rows", "n/a")

    mae_label = f"{mae:.3f}" if isinstance(mae, (int, float)) else str(mae)

    ml_cards_caption = f"Cards atualizados apos treino — status pipeline, melhor modelo e MAE (modelo: {model}, MAE: {mae_label})"
    ml_quadro_caption = f"Quadros gerados apos treino: dataset processado e predições baseline ({rows} linhas)"
    vision_hist_caption = f"Historico temporal de analises ({vision_count} registros acumulados)"
    pdf_section = ""
    if "16_pdf_aba" in shots:
        pdf_section = f"""
### 3.9 Aba 06 · PDF de Entrega

{img("16_pdf_aba", "Aba PDF com formulario preenchivel e gerador de PDF")}
"""

    return f"""\
# Evidencias de Demonstracao — Global Solution 2026.1

> Gerado automaticamente por `scripts/capture_evidencias.py` via Playwright.

---

## Integrantes

*(preencha antes de exportar o PDF)*

---

## 1. Introducao

{INTRO_TEXTO}

---

## 2. Desenvolvimento

{DEV_TEXTO}

---

## 3. Evidencias visuais

### 3.1 Tela inicial — hero e KPIs

{img("01_hero", "Tela inicial do portal com hero, KPIs e pilulas de status")}

### 3.2 Aba 01 · Visao Geral — roteiro e validacao da stack

{img("02_visao_geral", "Aba 01 com roteiro de apresentacao e atalhos")}

{img("03_stack_ok", "Validacao da stack — API e Dashboard com status OK")}

### 3.3 Aba 02 · ML & Predicoes

{img("04_ml_antes", "Aba ML antes do treino")}

{img("05_ml_treino_teste", "Teste funcional no portal: clique em 'Treinar baseline agora' com estado de processamento e feedback visual")}

{img("07_ml_quadros", ml_quadro_caption)}

{img("08_ml_leaderboard", "Comparativo de modelos (leaderboard) com selecao automatica do melhor MAE")}

### 3.4 Aba 03 · Visao Computacional

{img("09_vision_antes", "Aba Visao Computacional — seletor de cenario e botao de exemplo")}

{img("10_vision_resultado", "Resultado da analise sintetica — condicao, risco de chuva e alerta")}

{img("11_vision_historico", vision_hist_caption)}

### 3.5 Aba 04 · API & Stack

{img("12_api_aba", "Aba API com lista de endpoints e links Swagger / report/summary")}

### 3.6 Documentacao interativa — Swagger UI

{img("13_swagger", "Swagger UI com todos os endpoints disponiveis em http://127.0.0.1:8000/docs")}

### 3.7 Endpoint /report/summary — saida bruta

{img("14_report_json", "Saida JSON de /report/summary consolidando pipeline e visao")}

### 3.8 Aba 05 · Relatorio consolidado

{img("15_relatorio", "Aba Relatorio com JSON renderizado e botao de download")}

{pdf_section}

---

## 4. Snapshot do relatorio consolidado

```json
{json.dumps(summary, indent=2, ensure_ascii=False)}
```

---

## 5. Resultados Esperados

{RESULTADOS_TEXTO}

---

## 6. Conclusoes

{CONCLUSOES_TEXTO}

---

## 7. Link do video

*(Cole o link apos publicar no YouTube nao listado)*

---

*FIAP · Global Solution 2026.1 · MVP de monitoramento climatico espacial*
"""


# ─────────────────────────────────────────────
# main
# ─────────────────────────────────────────────

def main() -> None:
    print("=== capture_evidencias.py ===")
    print(f"Dashboard : {DASH_URL}")
    print(f"API       : {API_URL}")
    print(f"Saida     : {OUT_DIR}")
    print()

    # Verificar stack ativa
    try:
        requests.get(f"{API_URL}/health", timeout=3)
    except Exception:
        print("[ERRO] API nao esta rodando. Execute: bash scripts/run_demo_stack.sh")
        sys.exit(1)
    try:
        requests.get(DASH_URL, timeout=3)
    except Exception:
        print("[ERRO] Dashboard nao esta rodando. Execute: bash scripts/run_demo_stack.sh")
        sys.exit(1)

    print("Stack OK. Iniciando capturas...\n")
    shots = capture_all()

    summary = api_json("/report/summary")
    md = generate_md(shots, summary)

    MD_PATH.write_text(md, encoding="utf-8")
    print(f"\n[OK] Markdown gerado em {MD_PATH.relative_to(ROOT)}")
    print(f"[OK] {len(shots)} screenshots salvas em {OUT_DIR.relative_to(ROOT)}/")
    print("\nProximo passo: gere o PDF final com: python scripts/gerar_pdf_evidencias.py")


if __name__ == "__main__":
    main()

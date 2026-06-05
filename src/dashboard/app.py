import io
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from src.ml.train_baseline import train_baseline
from src.api.reporting import build_summary_report
from src.vision.analyze_image import analyze_image_array, analyze_image_bytes
from src.vision.history import append_vision_history, load_vision_history


def check_url(url: str) -> tuple[bool, str]:
	try:
		resp = requests.get(url, timeout=2)
		return resp.ok, f"HTTP {resp.status_code}"
	except requests.RequestException as exc:
		return False, str(exc)


def make_synthetic_sky(scene: str = "partly_cloudy", size: tuple[int, int] = (480, 320)) -> bytes:
	"""Gera uma imagem sintetica do ceu (PNG bytes) sem precisar de upload externo."""
	import cv2

	rng = np.random.default_rng({"clear": 1, "partly_cloudy": 7, "overcast": 42, "storm": 99}.get(scene, 7))
	w, h = size
	img = np.zeros((h, w, 3), dtype=np.uint8)

	if scene == "clear":
		top, bottom = (235, 170, 70), (255, 220, 170)
	elif scene == "partly_cloudy":
		top, bottom = (210, 160, 90), (240, 220, 200)
	elif scene == "overcast":
		top, bottom = (160, 160, 160), (210, 210, 210)
	else:
		top, bottom = (90, 90, 95), (140, 140, 145)

	for y in range(h):
		t = y / max(h - 1, 1)
		color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
		img[y, :] = color

	num_clouds = {"clear": 0, "partly_cloudy": 6, "overcast": 14, "storm": 18}.get(scene, 6)
	for _ in range(num_clouds):
		cx = int(rng.integers(0, w))
		cy = int(rng.integers(0, h // 2 + h // 4))
		rx = int(rng.integers(40, 110))
		ry = int(rng.integers(15, 45))
		shade = int(rng.integers(200, 255)) if scene != "storm" else int(rng.integers(110, 170))
		overlay = img.copy()
		cv2.ellipse(overlay, (cx, cy), (rx, ry), 0, 0, 360, (shade, shade, shade), -1)
		img = cv2.addWeighted(overlay, 0.55, img, 0.45, 0)

	noise = rng.integers(-6, 6, img.shape, dtype=np.int16)
	img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
	img = cv2.GaussianBlur(img, (5, 5), 0)

	ok, buf = cv2.imencode(".png", img)
	if not ok:
		raise RuntimeError("Falha ao codificar imagem sintetica")
	return buf.tobytes()


def build_delivery_pdf(
	integrantes: list[str],
	quero_concorrer: bool,
	video_url: str,
	intro: str,
	desenvolvimento: str,
	resultados: str,
	conclusoes: str,
	summary: dict,
) -> bytes:
	"""Gera o PDF de entrega seguindo a estrutura exigida pela banca."""
	from fpdf import FPDF

	def clean(text: str) -> str:
		return (text or "").replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')

	pdf = FPDF(format="A4", unit="mm")
	pdf.set_auto_page_break(auto=True, margin=18)
	pdf.set_margins(18, 18, 18)

	# Capa
	pdf.add_page()
	pdf.set_font("Helvetica", "B", 22)
	pdf.cell(0, 14, clean("Global Solution 2026.1 - FIAP"), ln=True)
	pdf.set_font("Helvetica", "", 14)
	pdf.cell(0, 9, clean("Monitoramento Climatico Espacial - MVP"), ln=True)
	pdf.ln(6)

	pdf.set_font("Helvetica", "B", 13)
	pdf.cell(0, 8, "Integrantes", ln=True)
	pdf.set_font("Helvetica", "", 12)
	for nome in integrantes or ["(preencher)"]:
		pdf.cell(0, 7, clean(f"- {nome}"), ln=True)

	if quero_concorrer:
		pdf.ln(4)
		pdf.set_font("Helvetica", "B", 16)
		pdf.set_text_color(124, 92, 255)
		pdf.cell(0, 10, "QUERO CONCORRER", ln=True)
		pdf.set_text_color(0, 0, 0)

	pdf.ln(8)
	pdf.set_font("Helvetica", "I", 10)
	pdf.cell(0, 6, clean(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"), ln=True)

	def section(title: str, body: str) -> None:
		pdf.add_page()
		pdf.set_font("Helvetica", "B", 16)
		pdf.cell(0, 10, clean(title), ln=True)
		pdf.set_font("Helvetica", "", 11)
		pdf.ln(2)
		usable_w = pdf.w - pdf.l_margin - pdf.r_margin
		for line in clean(body).splitlines() or [""]:
			if line.strip() == "":
				pdf.ln(3)
			else:
				pdf.set_x(pdf.l_margin)
				pdf.multi_cell(usable_w, 6, line)

	section("1. Introducao", intro)
	section("2. Desenvolvimento", desenvolvimento)
	section("3. Resultados Esperados", resultados)

	# Anexo: relatorio consolidado
	pdf.add_page()
	pdf.set_font("Helvetica", "B", 16)
	pdf.cell(0, 10, "4. Relatorio consolidado (snapshot)", ln=True)
	pdf.set_font("Courier", "", 8)
	summary_text = clean(json.dumps(summary, indent=2, ensure_ascii=False))
	usable_w = pdf.w - pdf.l_margin - pdf.r_margin
	wrap = 95
	for raw_line in summary_text.splitlines():
		if not raw_line:
			pdf.ln(3)
			continue
		for i in range(0, len(raw_line), wrap):
			pdf.set_x(pdf.l_margin)
			pdf.multi_cell(usable_w, 4.4, raw_line[i : i + wrap])

	section("5. Conclusoes", conclusoes)

	# Link do video ao final
	pdf.add_page()
	pdf.set_font("Helvetica", "B", 16)
	pdf.cell(0, 10, "6. Video de demonstracao", ln=True)
	pdf.set_font("Helvetica", "", 12)
	pdf.ln(2)
	link = (video_url or "").strip() or "(link a ser preenchido apos upload)"
	pdf.multi_cell(0, 7, clean(f"Link: {link}"))

	out = pdf.output(dest="S")
	return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")


st.set_page_config(
	page_title="GS Climate Monitor",
	page_icon="🛰️",
	layout="wide",
	initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
:root {
	--accent: #7C5CFF;
	--accent2: #22D3EE;
	--ok: #22C55E;
	--warn: #F59E0B;
	--err: #EF4444;
	--card: #141A33;
	--card-2: #1B2244;
	--text: #E6E9F5;
	--muted: #93A0C4;
}

html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stApp"] {
	background-color: #0B1020 !important;
}
[data-testid="stHeader"], header[data-testid="stHeader"] {
	background: rgba(11,16,32,0.85) !important;
	backdrop-filter: blur(8px);
}
[data-testid="stSidebar"] {background: #0E1428 !important;}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1280px; background: transparent !important;}
#MainMenu, footer {visibility: hidden;}

.hero {
	border-radius: 22px;
	padding: 28px 32px;
	background:
		radial-gradient(1200px 400px at 10% -10%, rgba(124,92,255,0.35), transparent 60%),
		radial-gradient(800px 360px at 90% 0%, rgba(34,211,238,0.25), transparent 60%),
		linear-gradient(135deg, #0F1530 0%, #131A3D 100%);
	border: 1px solid rgba(255,255,255,0.06);
	box-shadow: 0 20px 50px rgba(0,0,0,0.35);
	margin-bottom: 18px;
}
.hero .eyebrow {
	display: inline-block; padding: 4px 10px; font-size: 12px; letter-spacing: 0.18em;
	color: #BBC3E6; background: rgba(124,92,255,0.18);
	border: 1px solid rgba(124,92,255,0.45); border-radius: 999px; text-transform: uppercase;
}
.hero h1 {
	font-size: 40px; line-height: 1.1; margin: 12px 0 6px 0;
	background: linear-gradient(90deg, #FFFFFF 0%, #C8C5FF 60%, #7DE3FF 100%);
	-webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p.lead {color: var(--muted); margin: 0; font-size: 16px;}
.hero .pillrow {margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px;}
.pill {
	display: inline-flex; align-items: center; gap: 6px;
	padding: 6px 12px; border-radius: 999px; font-size: 12px;
	background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
	color: #D4DAF2;
}
.pill .dot {width: 8px; height: 8px; border-radius: 999px; background: var(--accent);}
.pill.ok .dot {background: var(--ok);} .pill.warn .dot {background: var(--warn);} .pill.err .dot {background: var(--err);}

.section-title {
	display: flex; align-items: center; gap: 10px;
	font-size: 18px; font-weight: 600; margin: 18px 0 10px 0; color: #E6E9F5;
}
.section-title .num {
	width: 28px; height: 28px; border-radius: 8px;
	background: linear-gradient(135deg, var(--accent), var(--accent2));
	color: white; font-size: 13px; display: inline-flex; align-items: center; justify-content: center;
	box-shadow: 0 6px 18px rgba(124,92,255,0.35);
}

div[data-testid="stMetric"] {
	background: linear-gradient(180deg, var(--card) 0%, var(--card-2) 100%);
	border: 1px solid rgba(255,255,255,0.06);
	border-radius: 14px; padding: 14px 16px;
	box-shadow: 0 8px 22px rgba(0,0,0,0.25);
}
div[data-testid="stMetricLabel"] {color: var(--muted) !important; font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase;}
div[data-testid="stMetricValue"] {color: #FFFFFF !important; font-weight: 700;}

.stTabs [data-baseweb="tab-list"] {gap: 8px;}
.stTabs [data-baseweb="tab"] {
	background: var(--card); border-radius: 12px 12px 0 0;
	padding: 10px 16px; border: 1px solid rgba(255,255,255,0.06); border-bottom: none;
}
.stTabs [aria-selected="true"] {
	background: linear-gradient(180deg, rgba(124,92,255,0.25), rgba(124,92,255,0.0));
	border-color: rgba(124,92,255,0.55);
}

.stButton > button, .stDownloadButton > button {
	background: linear-gradient(135deg, var(--accent) 0%, #5B8CFF 100%);
	color: white; border: 0; border-radius: 12px; padding: 10px 16px;
	font-weight: 600; box-shadow: 0 8px 22px rgba(124,92,255,0.35);
	transition: transform 120ms ease, box-shadow 120ms ease;
}
.stButton > button:hover {transform: translateY(-1px); box-shadow: 0 12px 28px rgba(124,92,255,0.45);}

a {color: #9DB1FF;}
.small {color: var(--muted); font-size: 12px;}
.kbd {
	font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
	background: #0B0F22; border: 1px solid rgba(255,255,255,0.08);
	padding: 2px 6px; border-radius: 6px; font-size: 12px;
}

.script {
	position: relative;
	border-radius: 14px;
	padding: 16px 18px 16px 56px;
	background: linear-gradient(180deg, rgba(124,92,255,0.18) 0%, rgba(34,211,238,0.10) 100%);
	border: 1px solid rgba(124,92,255,0.45);
	margin: 6px 0 14px 0;
	color: #E6E9F5;
}
.script::before {
	content: "\1F3AC";
	position: absolute; left: 14px; top: 14px;
	width: 30px; height: 30px; border-radius: 8px;
	background: linear-gradient(135deg, var(--accent), var(--accent2));
	display: inline-flex; align-items: center; justify-content: center;
	font-size: 16px; box-shadow: 0 6px 18px rgba(124,92,255,0.35);
}
.script .label {
	display: inline-block; font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase;
	color: #BBC3E6; margin-bottom: 6px;
}
.script .quote {font-size: 15px; line-height: 1.55;}
.script .quote em {color: #C8C5FF; font-style: normal; font-weight: 600;}
.script ul {margin: 8px 0 0 18px; color: #C9D1EC; font-size: 13px;}
.script ul li {margin: 2px 0;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

summary = build_summary_report(ROOT)
ml_block = summary.get("ml", {}) or {}
vision_block = summary.get("vision", {}) or {}
status = str(summary.get("status", "unknown"))

api_ok, _ = check_url("http://127.0.0.1:8000/health")
status_class = "ok" if status == "ready" else "warn"
api_class = "ok" if api_ok else "err"

st.markdown(
	f"""
	<div class="hero">
		<span class="eyebrow">Global Solution 2026.1 · FIAP</span>
		<h1>Monitoramento Climático Espacial</h1>
		<p class="lead">Pipeline ML + Visão Computacional + API · MVP pronto para apresentação em 5 minutos.</p>
		<div class="pillrow">
			<span class="pill {status_class}"><span class="dot"></span> Pipeline: {status}</span>
			<span class="pill {api_class}"><span class="dot"></span> API local</span>
			<span class="pill"><span class="dot"></span> Modelo: {ml_block.get('model', 'pending')}</span>
			<span class="pill"><span class="dot"></span> MAE: {ml_block.get('mae', 'n/a')}</span>
			<span class="pill"><span class="dot"></span> Análises de visão: {int(vision_block.get('count', 0))}</span>
		</div>
	</div>
	""",
	unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Status", status.title(), help="Estado geral do pipeline (ready quando treino + dataset existem).")
k2.metric("Modelo ativo", str(ml_block.get("model", "pending")), help="Algoritmo vencedor selecionado por menor MAE.")
mae_disp = ml_block.get("mae")
k3.metric("MAE", f"{mae_disp:.3f}" if isinstance(mae_disp, (int, float)) else "n/a", help="Erro medio absoluto na temperatura prevista (graus C).")
k4.metric("Análises de visão", int(vision_block.get("count", 0)), help="Quantidade de imagens analisadas e gravadas no historico.")

tab_intro, tab_ml, tab_vision, tab_api, tab_report, tab_pdf = st.tabs(
	[
		"01 · Visão Geral",
		"02 · ML & Predições",
		"03 · Visão Computacional",
		"04 · API & Stack",
		"05 · Relatório",
		"06 · PDF de Entrega",
	]
)

processed_dir = ROOT / "data" / "processed"
metrics_file = processed_dir / "metrics.json"
predictions_file = processed_dir / "predictions.csv"
dataset_file = processed_dir / "training_dataset.csv"
leaderboard_file = processed_dir / "model_leaderboard.csv"

with tab_intro:
	st.markdown('<div class="section-title"><span class="num">1</span> Roteiro de apresentação</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · 0:00 – 0:40 · Abertura</span>
			<div class="quote">
				Esta aba é a <em>tela inicial</em> do portal. Use-a para abrir o vídeo apresentando o contexto e mostrando que tudo está saudável.
			</div>
			<ul>
				<li>Aponte para o <em>hero</em> no topo: título, KPIs e pílulas de status (pipeline, API, modelo, MAE, visão).</li>
				<li>Diga em uma frase o que o MVP entrega (ML + Visão + API consolidada).</li>
				<li>Mostre as <em>abas 01 a 05</em> e explique que cada uma corresponde a uma etapa da demo.</li>
				<li>Clique em <em>Checar serviços agora</em> para validar API e Dashboard ao vivo — mostre os 3 status verdes.</li>
				<li>Quando terminar, avance para a aba <em>02 · ML &amp; Predições</em>.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)
	col_a, col_b = st.columns([1.1, 1])
	with col_a:
		st.markdown(
			"""
			**Sequência sugerida (≈ 5 min):**

			1. Contexto e arquitetura da solução  
			2. Treino baseline e comparativo de modelos  
			3. Predições no dashboard  
			4. Análise de imagem (condição e risco de chuva)  
			5. Encerrar com `GET /report/summary`
			"""
		)
		st.markdown(
			"""
			**Atalhos rápidos:**

			- Dashboard: <span class="kbd">http://127.0.0.1:8501</span>
			- API summary: <span class="kbd">http://127.0.0.1:8000/report/summary</span>
			- API docs: <span class="kbd">http://127.0.0.1:8000/docs</span>
			""",
			unsafe_allow_html=True,
		)
	with col_b:
		with st.container(border=True):
			st.markdown("**Validação da stack**")
			if st.button(
				"Checar serviços agora",
				key="check_stack",
				help="Faz uma chamada HTTP para API /health, Dashboard e /report/summary e mostra o status.",
			):
				h_ok, h_msg = check_url("http://127.0.0.1:8000/health")
				d_ok, d_msg = check_url("http://127.0.0.1:8501")
				r_ok, r_msg = check_url("http://127.0.0.1:8000/report/summary")
				c1, c2, c3 = st.columns(3)
				c1.metric("API /health", "OK" if h_ok else "Falhou", h_msg)
				c2.metric("Dashboard", "OK" if d_ok else "Falhou", d_msg)
				c3.metric("API summary", "OK" if r_ok else "Falhou", r_msg)
			else:
				st.caption("Clique para validar API e Dashboard antes de gravar.")

with tab_ml:
	st.markdown('<div class="section-title"><span class="num">2</span> Pipeline de Machine Learning</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · 0:40 – 1:50 · ML &amp; Predições</span>
			<div class="quote">
				Nesta aba você demonstra o <em>pipeline de ML</em>: ingestão de dados, treino, seleção do melhor modelo por <em>MAE</em> e geração das predições.
			</div>
			<ul>
				<li>Clique em <em>Treinar baseline agora</em> e espere o spinner concluir (segundos).</li>
				<li>Aponte os 3 cards: <em>Status pipeline</em>, <em>Melhor modelo</em> e <em>MAE</em>.</li>
				<li>Mostre o <em>Dataset processado</em> à esquerda e as <em>Predições baseline</em> à direita.</li>
				<li>Role até o <em>Comparativo de modelos</em> e diga, em uma frase, qual modelo venceu e por quê (menor MAE).</li>
				<li>Avance para a aba <em>03 · Visão Computacional</em>.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)
	c_btn, c_info = st.columns([1, 2])
	with c_btn:
		if st.button(
			"Treinar baseline agora",
			key="train_btn",
			help="Executa o pipeline: ingestao -> features -> treino LR e RF -> selecao por MAE -> persistencia em disco.",
		):
			with st.spinner("Treinando modelos e selecionando o melhor por MAE..."):
				result = train_baseline(base_dir=ROOT, use_api=True)
			st.success(f"Modelo salvo em {result['model_path']}")
	with c_info:
		mae_value = "Pending"
		model_name = "Pending"
		if metrics_file.exists():
			metrics_data = json.loads(metrics_file.read_text(encoding="utf-8"))
			mae_value = f"{metrics_data.get('mae', 0.0):.3f}"
			model_name = str(metrics_data.get("model", "Pending"))
		m1, m2, m3 = st.columns(3)
		m1.metric("Status pipeline", "Ready" if dataset_file.exists() else "Bootstrap")
		m2.metric("Melhor modelo", model_name)
		m3.metric("MAE", mae_value)

	st.divider()

	col_d, col_p = st.columns(2)
	with col_d:
		st.markdown("**Dataset processado (últimas linhas)**")
		if dataset_file.exists():
			st.dataframe(pd.read_csv(dataset_file).tail(10), use_container_width=True, height=320)
		else:
			st.info("Dataset ainda não gerado. Rode o treino acima.")
	with col_p:
		st.markdown("**Predições baseline**")
		if predictions_file.exists():
			st.dataframe(pd.read_csv(predictions_file).tail(10), use_container_width=True, height=320)
		else:
			st.info("Execute o treinamento para gerar predições e métricas.")

	if leaderboard_file.exists():
		st.markdown("**Comparativo de modelos**")
		st.dataframe(pd.read_csv(leaderboard_file), use_container_width=True)

with tab_vision:
	st.markdown('<div class="section-title"><span class="num">3</span> Visão Computacional</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · 1:50 – 3:20 · Visão Computacional</span>
			<div class="quote">
				Aqui você mostra o módulo de <em>visão computacional</em>: enviar uma imagem do céu, ler as métricas e exibir o histórico temporal.
			</div>
			<ul>
				<li>Clique em <em>Browse files</em> e selecione uma imagem do céu (PNG ou JPG).</li>
				<li>Aponte os 3 cards de resultado: <em>Condição</em>, <em>Risco de chuva</em> e <em>Alerta</em>.</li>
				<li>Abra o <em>JSON</em> abaixo (1 clique) para mostrar o detalhe bruto da análise.</li>
				<li>Role até o <em>Histórico de análises</em> e mostre o gráfico temporal alimentado a cada upload.</li>
				<li>Avance para a aba <em>04 · API &amp; Stack</em>.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.caption("Use uma imagem sintetica abaixo (sem precisar de upload) ou envie uma propria.")

	with st.container(border=True):
		st.markdown("**Exemplo embutido (gera imagem sintetica)**")
		scene = st.selectbox(
			"Cenario de exemplo",
			["clear", "partly_cloudy", "overcast", "storm"],
			index=1,
			help="Cada cenario produz uma imagem sintetica com cobertura de nuvens crescente.",
		)
		cols = st.columns([1, 1])
		with cols[0]:
			if st.button(
				"Gerar e analisar exemplo",
				key="vision_demo_btn",
				help="Gera uma imagem do ceu sintetica em memoria e roda o pipeline de visao.",
			):
				demo_bytes = make_synthetic_sky(scene)
				st.session_state["vision_demo_bytes"] = demo_bytes
				st.session_state["vision_demo_scene"] = scene
		with cols[1]:
			if "vision_demo_bytes" in st.session_state:
				st.download_button(
					"Baixar imagem de exemplo",
					data=st.session_state["vision_demo_bytes"],
					file_name=f"sky_{st.session_state.get('vision_demo_scene','example')}.png",
					mime="image/png",
				)

		if "vision_demo_bytes" in st.session_state:
			demo_bytes = st.session_state["vision_demo_bytes"]
			col_img, col_res = st.columns([1, 1])
			with col_img:
				st.image(demo_bytes, caption=f"Cenario sintetico: {st.session_state.get('vision_demo_scene','')}", use_column_width=True)
			with col_res:
				try:
					demo_result = analyze_image_bytes(demo_bytes)
					append_vision_history(
						base_dir=ROOT,
						source="dashboard_demo",
						filename=f"sky_{st.session_state.get('vision_demo_scene','example')}.png",
						analysis=demo_result,
					)
					v1, v2, v3 = st.columns(3)
					v1.metric("Condição", demo_result["condition"], help="Classificacao discreta a partir do score de cobertura de nuvens.")
					v2.metric("Risco de chuva", f"{demo_result['rain_risk_score']}%", help="Score combinando cobertura, saturacao e densidade de bordas.")
					v3.metric("Alerta", demo_result["rain_alert"], help="Faixa do risco: low / moderate / high.")
					st.json(demo_result, expanded=False)
				except ValueError as exc:
					st.error(f"Falha na analise da imagem: {exc}")

	st.divider()
	st.markdown("**Ou envie uma imagem real**")
	uploaded_image = st.file_uploader(
		"Imagem do céu (PNG ou JPG)",
		type=["png", "jpg", "jpeg"],
		label_visibility="collapsed",
	)

	if uploaded_image is not None:
		image_bytes = uploaded_image.getvalue()
		col_img, col_res = st.columns([1, 1])
		with col_img:
			st.image(image_bytes, caption=uploaded_image.name, use_column_width=True)
		with col_res:
			try:
				vision_result = analyze_image_bytes(image_bytes)
				append_vision_history(
					base_dir=ROOT,
					source="dashboard",
					filename=uploaded_image.name,
					analysis=vision_result,
				)
				v1, v2, v3 = st.columns(3)
				v1.metric("Condição", vision_result["condition"])
				v2.metric("Risco de chuva", f"{vision_result['rain_risk_score']}%")
				v3.metric("Alerta", vision_result["rain_alert"])
				st.json(vision_result, expanded=False)
			except ValueError as exc:
				st.error(f"Falha na análise da imagem: {exc}")

	history_df = load_vision_history(ROOT)
	if not history_df.empty:
		st.divider()
		st.markdown("**Histórico de análises**")
		history_sorted = history_df.sort_values("timestamp_utc")
		chart_df = history_sorted[["timestamp_utc", "cloudiness_score", "rain_risk_score"]].set_index("timestamp_utc")
		st.line_chart(chart_df, height=260)
		st.dataframe(history_sorted.tail(20), use_container_width=True, height=260)
	else:
		st.info("Sem histórico ainda. Envie uma imagem para começar a popular o gráfico temporal.")

with tab_api:
	st.markdown('<div class="section-title"><span class="num">4</span> API local</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · 3:20 – 4:10 · API &amp; Stack</span>
			<div class="quote">
				Use esta aba para mostrar que toda a inteligência está disponível via <em>API FastAPI</em>, pronta para integração com outros sistemas.
			</div>
			<ul>
				<li>Leia rapidamente a lista de <em>endpoints principais</em> abaixo.</li>
				<li>Clique em <em>Abrir API docs (Swagger)</em> para mostrar a documentação interativa em outra aba.</li>
				<li>Volte e clique em <em>Abrir relatório JSON</em> para mostrar a saída real do <em>/report/summary</em>.</li>
				<li>Avance para a aba <em>05 · Relatório</em>.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.markdown(
		"""
		**Endpoints principais:**

		- `GET /health` — saúde do serviço  
		- `POST /train` — dispara treino e seleção do melhor modelo  
		- `GET /predict` — última predição com o modelo ativo  
		- `POST /vision/analyze` — análise de imagem  
		- `GET /vision/history` — histórico de análises  
		- `GET /report/summary` — relatório consolidado para a banca
		"""
	)
	c1, c2 = st.columns(2)
	with c1:
		st.markdown(
			"<a href='http://127.0.0.1:8000/docs' target='_blank'>Abrir API docs (Swagger)</a>",
			unsafe_allow_html=True,
		)
	with c2:
		st.markdown(
			"<a href='http://127.0.0.1:8000/report/summary' target='_blank'>Abrir relatório JSON</a>",
			unsafe_allow_html=True,
		)
	st.caption("Para subir tudo de uma vez: bash scripts/run_demo_stack.sh")

with tab_report:
	st.markdown('<div class="section-title"><span class="num">5</span> Relatório consolidado</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · 4:10 – 5:00 · Fechamento</span>
			<div class="quote">
				Esta é a aba de fechamento. Use-a para entregar o <em>relatório consolidado</em> e citar os próximos passos.
			</div>
			<ul>
				<li>Mostre o <em>JSON consolidado</em> abaixo — status, modelo ativo, métricas e resumo da visão.</li>
				<li>Clique em <em>Baixar relatório JSON</em> para evidenciar o entregável.</li>
				<li>Cite os próximos passos: <em>IoT real com ESP32</em>, <em>dados satelitais adicionais</em> e <em>deploy em cloud</em>.</li>
				<li>Encerre agradecendo e abrindo para perguntas.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)
	st.json(summary)
	st.download_button(
		"Baixar relatório JSON",
		data=json.dumps(summary, indent=2, ensure_ascii=False),
		file_name="report_summary.json",
		mime="application/json",
		help="Baixa o snapshot atual do /report/summary para anexar ao PDF de entrega.",
	)

with tab_pdf:
	st.markdown('<div class="section-title"><span class="num">6</span> PDF de entrega</div>', unsafe_allow_html=True)
	st.markdown(
		"""
		<div class="script">
			<span class="label">Tutorial · Pós-gravação · PDF de entrega</span>
			<div class="quote">
				Apos gravar e publicar o video, preencha os campos abaixo e clique em <em>Gerar PDF</em>. O documento sai pronto com a estrutura exigida pela banca: integrantes, frase opcional <em>QUERO CONCORRER</em>, Introducao, Desenvolvimento, Resultados Esperados, Conclusoes, snapshot do relatorio consolidado e link do video ao final.
			</div>
			<ul>
				<li>Preencha os <em>integrantes</em> (um por linha) e marque <em>QUERO CONCORRER</em> se for o caso.</li>
				<li>Cole o <em>link do video</em> (YouTube nao listado).</li>
				<li>Edite os textos pre-preenchidos de Introducao / Desenvolvimento / Resultados / Conclusoes.</li>
				<li>Clique em <em>Gerar PDF</em> e baixe o arquivo.</li>
			</ul>
		</div>
		""",
		unsafe_allow_html=True,
	)

	default_intro = (
		"Este projeto entrega um MVP de monitoramento climatico espacial com tres pilares: (1) pipeline de Machine Learning para previsao de temperatura horaria a partir de dados meteorologicos publicos (Open-Meteo), com selecao automatica do melhor modelo por MAE; (2) modulo de Visao Computacional que analisa imagens do ceu e estima cobertura de nuvens, risco de chuva e alerta operacional; (3) API FastAPI que expoe treino, predicao, analise de imagem e um relatorio consolidado para integracao com outros sistemas, incluindo dispositivos IoT como ESP32. "
		"O dashboard Streamlit centraliza a apresentacao em um portal autocontido, com tooltips, exemplos sinteticos embutidos e geracao deste proprio PDF de entrega."
	)
	default_dev = (
		"Arquitetura e decisoes principais:\n"
		"- Linguagem: Python 3.10+. Stack: pandas, numpy, scikit-learn, OpenCV, FastAPI, Streamlit, fpdf2.\n"
		"- Pipeline ML (src/ml/train_baseline.py): ingestao via Open-Meteo (com fallback sintetico), criacao de features, split temporal, treino de LinearRegression e RandomForestRegressor, selecao por MAE, persistencia de modelo, dataset, predicoes, leaderboard e metricas em data/processed.\n"
		"- Visao Computacional (src/vision/analyze_image.py): conversao BGR->Gray/HSV, brilho, contraste, saturacao e densidade de bordas (Canny). Combinacao linear ponderada gera scores de cobertura e risco de chuva e classifica condicao (clear/partly_cloudy/overcast) e alerta (low/moderate/high). Historico em CSV alimenta grafico temporal.\n"
		"- API (src/api/main.py): /health, /train, /predict, /vision/analyze, /vision/history, /report/summary. O /report/summary consolida estado do pipeline + ultima predicao + resumo da visao para a banca.\n"
		"- Dashboard (src/dashboard/app.py): tema dark espacial customizado (.streamlit/config.toml), abas numeradas 01-06, tooltips em cada acao, exemplo sinteticos embutido em Visao Computacional e gerador de PDF de entrega autocontido.\n"
		"- Automacao: scripts/run_demo_stack.sh sobe API e Dashboard juntos; scripts/smoke_demo.sh valida endpoints chave antes da gravacao."
	)
	default_resultados = (
		"O MVP demonstra:\n"
		"- Previsao horaria de temperatura com MAE inferior a 1 grau C nos cenarios validados.\n"
		"- Classificacao de condicao do ceu e estimativa de risco de chuva a partir de imagens, com historico temporal acumulado.\n"
		"- Relatorio consolidado em JSON consumivel por outros sistemas, viabilizando integracao com IoT (ESP32) e servicos cloud.\n"
		"- Portal autocontido para apresentacao em 5 minutos, sem dependencias externas durante a demo."
	)
	default_conclusoes = (
		"O grupo entrega uma POC funcional que une dados, ML, visao computacional e API em uma experiencia integrada. "
		"Como proximos passos: integrar IoT real (ESP32 com sensores ambientais), ampliar a base com dados satelitais adicionais e fazer deploy em cloud (AWS/GCP) com pipeline de CI/CD. "
		"A arquitetura modular facilita a evolucao incremental sem retrabalho."
	)

	with st.form("pdf_form"):
		col1, col2 = st.columns(2)
		with col1:
			integrantes_raw = st.text_area(
				"Integrantes (um por linha, com nome completo)",
				height=120,
				placeholder="Nome Sobrenome - RM000000\nNome Sobrenome - RM000000",
				help="Nomes que aparecerao na primeira pagina do PDF.",
			)
			quero_concorrer = st.checkbox(
				"Incluir frase QUERO CONCORRER",
				value=False,
				help="Marque se o grupo deseja concorrer ao podio.",
			)
			video_url = st.text_input(
				"Link do video (YouTube nao listado)",
				placeholder="https://youtu.be/...",
				help="Sera incluido na ultima pagina do PDF.",
			)
		with col2:
			intro_text = st.text_area("1. Introducao", value=default_intro, height=160)
			dev_text = st.text_area("2. Desenvolvimento", value=default_dev, height=200)

		res_text = st.text_area("3. Resultados Esperados", value=default_resultados, height=140)
		conc_text = st.text_area("5. Conclusoes", value=default_conclusoes, height=140)

		submitted = st.form_submit_button(
			"Gerar PDF",
			help="Cria o PDF com a estrutura exigida (integrantes, QUERO CONCORRER opcional, Introducao, Desenvolvimento, Resultados, Conclusoes, snapshot e link do video).",
		)

	if submitted:
		integrantes = [linha.strip() for linha in (integrantes_raw or "").splitlines() if linha.strip()]
		with st.spinner("Gerando PDF..."):
			pdf_bytes = build_delivery_pdf(
				integrantes=integrantes,
				quero_concorrer=quero_concorrer,
				video_url=video_url,
				intro=intro_text,
				desenvolvimento=dev_text,
				resultados=res_text,
				conclusoes=conc_text,
				summary=summary,
			)
		st.success("PDF gerado com sucesso.")
		st.download_button(
			"Baixar PDF de entrega",
			data=pdf_bytes,
			file_name="GS2026_entrega.pdf",
			mime="application/pdf",
		)

st.markdown(
	"<div class='small' style='text-align:center; margin-top:24px;'>FIAP · Global Solution 2026.1 · MVP de monitoramento climático</div>",
	unsafe_allow_html=True,
)

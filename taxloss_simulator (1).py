"""
==============================================================
  TAXLOSS SIMULATOR — Matriz Avanzada de PDN
  Simulador de Pérdidas Tributarias Netas (Art. 50° LIR)
  Normativa SUNAT — Perú | Python + Streamlit
==============================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TaxLoss Simulator — PDN Avanzada",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

UIT_2024 = 5250
LIMITE_TRAMO1_RMT = 15 * UIT_2024   # S/ 78,750

# ─────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #1b2838 60%, #0f3460 100%);
}
[data-testid="stSidebar"] * { color: #cfd8dc !important; }

.kpi-card {
    background: linear-gradient(135deg, #0d2137, #1a3a5f);
    border: 1px solid #2e6da4; border-radius: 14px;
    padding: 20px 24px; text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4); margin-bottom: 12px;
}
.kpi-title { font-size: 0.75rem; color: #8fb3d4; font-weight: 700;
             text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; }
.kpi-value { font-size: 1.75rem; font-weight: 900; color: #4fc3f7; }
.kpi-sub   { font-size: 0.72rem; color: #78909c; margin-top: 4px; }

.kpi-green .kpi-value  { color: #69f0ae; }
.kpi-red   .kpi-value  { color: #ff5252; }
.kpi-gold  .kpi-value  { color: #ffd740; }

.rec-box {
    border-radius: 12px; padding: 18px 22px; margin: 10px 0;
    font-size: 0.9rem; font-weight: 500; line-height: 1.6;
}
.rec-a { background: #0d2a1a; border: 2px solid #00c853; color: #b9f6ca; }
.rec-b { background: #2a1a0d; border: 2px solid #ff6d00; color: #ffe0b2; }

.section-hdr {
    background: linear-gradient(90deg, #1565c0, #0288d1);
    padding: 10px 18px; border-radius: 8px; margin: 16px 0 10px 0;
    color: white; font-size: 1rem; font-weight: 700;
}
.badge { display: inline-block; background: #1a237e; color: #90caf9;
         border-radius: 20px; padding: 2px 10px; font-size: 0.72rem;
         font-style: italic; margin: 2px; }
.perdida-tag { color: #ff5252; font-weight: 700; }
.ok-tag      { color: #69f0ae; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# BACKEND — MOTOR DE CÁLCULO
# ─────────────────────────────────────────────

def calcular_ir(renta_neta: float, regimen: str) -> float:
    """Calcula el IR según régimen tributario."""
    if renta_neta <= 0:
        return 0.0
    if regimen == "RMT (10% / 29.5%)":
        if renta_neta <= LIMITE_TRAMO1_RMT:
            return round(renta_neta * 0.10, 2)
        else:
            return round(LIMITE_TRAMO1_RMT * 0.10 + (renta_neta - LIMITE_TRAMO1_RMT) * 0.295, 2)
    else:  # Régimen General
        return round(renta_neta * 0.295, 2)


def simular_sistema_a(pdn: float, rentas: list[float], regimen: str) -> list[dict]:
    """
    Sistema A — Art. 50° LIR:
    Compensación hasta 100% de renta neta, máximo 4 años.
    Al año 5, saldo pendiente se castiga (beneficio perdido).
    """
    saldo = pdn
    resultados = []
    for i, renta in enumerate(rentas):
        año = i + 1
        if año <= 4 and saldo > 0:
            compensada = min(saldo, renta)
            saldo = round(saldo - compensada, 2)
        else:
            compensada = 0.0
            if año == 5 and saldo > 0:
                beneficio_perdido = saldo
                saldo = 0.0
            else:
                beneficio_perdido = 0.0

        renta_imponible = max(0, renta - compensada)
        ir = calcular_ir(renta_imponible, regimen)

        resultados.append({
            "año": año,
            "renta_neta": renta,
            "compensada": compensada,
            "saldo_pdn": saldo,
            "renta_imponible": renta_imponible,
            "ir": ir,
            "beneficio_perdido": beneficio_perdido if año == 5 else 0.0,
        })
    return resultados


def simular_sistema_b(pdn: float, rentas: list[float], regimen: str) -> list[dict]:
    """
    Sistema B — Art. 50° LIR:
    Compensación máximo 50% de renta neta por año, sin límite temporal.
    """
    saldo = pdn
    resultados = []
    for i, renta in enumerate(rentas):
        año = i + 1
        if saldo > 0:
            limite_50 = round(renta * 0.50, 2)
            compensada = min(saldo, limite_50)
            saldo = round(saldo - compensada, 2)
        else:
            compensada = 0.0

        renta_imponible = max(0, renta - compensada)
        ir = calcular_ir(renta_imponible, regimen)

        resultados.append({
            "año": año,
            "renta_neta": renta,
            "compensada": compensada,
            "saldo_pdn": saldo,
            "renta_imponible": renta_imponible,
            "ir": ir,
            "beneficio_perdido": 0.0,
        })
    return resultados


def calcular_van(flujos_ir: list[float], cok: float) -> float:
    """VAN de salidas de impuestos: menor VAN = menor carga en valor presente."""
    van = sum(ir / (1 + cok) ** t for t, ir in enumerate(flujos_ir, start=1))
    return round(van, 2)


# ─────────────────────────────────────────────
# SIDEBAR — PANEL DE CONFIGURACIÓN
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ TaxLoss Simulator")
    st.markdown("**Matriz Avanzada de PDN**")
    st.caption("Art. 50° TUO LIR · SUNAT Perú")
    st.divider()

    st.markdown("### 🔧 Parámetros Globales")

    pdn_input = st.number_input(
        "Pérdida Tributaria Neta — Año 0 (S/)",
        min_value=0.0, max_value=10_000_000.0,
        value=18578.0, step=1000.0,
        help="PDN generada en el primer ejercicio (Art. 50° LIR)"
    )

    regimen = st.selectbox(
        "Régimen del IR",
        ["RMT (10% / 29.5%)", "Régimen General (29.5%)"],
        help="RMT: D. Leg. 1269 — 10% hasta 15 UIT, 29.5% exceso"
    )

    cok_pct = st.slider(
        "COK / Tasa de Descuento (%)",
        min_value=5.0, max_value=30.0, value=12.0, step=0.5,
        help="Costo de Oportunidad del Capital para el VAN"
    )
    cok = cok_pct / 100

    st.divider()
    st.markdown("### 📅 Rentas Netas Proyectadas")
    st.caption("Utilidad antes de impuestos (sin IGV)")

    rentas = []
    defaults = [35000, 55000, 70000, 85000, 100000]
    for i in range(5):
        r = st.number_input(
            f"Año {i+1} (S/)", min_value=0.0, max_value=5_000_000.0,
            value=float(defaults[i]), step=1000.0, key=f"renta_{i}"
        )
        rentas.append(r)

    st.divider()
    st.caption(f"UIT 2024 = S/ {UIT_2024:,} | 15 UIT = S/ {LIMITE_TRAMO1_RMT:,}")

# ─────────────────────────────────────────────
# CÁLCULOS PRINCIPALES
# ─────────────────────────────────────────────
res_a = simular_sistema_a(pdn_input, rentas, regimen)
res_b = simular_sistema_b(pdn_input, rentas, regimen)

ir_a = [r["ir"] for r in res_a]
ir_b = [r["ir"] for r in res_b]

van_a = calcular_van(ir_a, cok)
van_b = calcular_van(ir_b, cok)

ahorro = round(abs(van_a - van_b), 2)
sistema_optimo = "A" if van_a <= van_b else "B"
van_optimo = min(van_a, van_b)
van_peor   = max(van_a, van_b)

total_ir_a = sum(ir_a)
total_ir_b = sum(ir_b)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("⚖️ TaxLoss Simulator — Matriz Avanzada de PDN")
st.caption(
    f"Pérdida simulada: **S/ {pdn_input:,.2f}** · "
    f"Régimen: **{regimen}** · "
    f"COK: **{cok_pct}%** · "
    f"Normativa: Art. 50° TUO LIR — D.S. N.° 179-2004-EF"
)
st.divider()

# ─────────────────────────────────────────────
# KPIs PRINCIPALES
# ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">VAN Impuesto — Sistema A</div>
        <div class="kpi-value">S/ {van_a:,.2f}</div>
        <div class="kpi-sub">4 años · 100% renta neta</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">VAN Impuesto — Sistema B</div>
        <div class="kpi-value">S/ {van_b:,.2f}</div>
        <div class="kpi-sub">Indefinido · 50% renta neta</div>
    </div>""", unsafe_allow_html=True)

with c3:
    color_cls = "kpi-green" if sistema_optimo == "A" else "kpi-gold"
    st.markdown(f"""
    <div class="kpi-card {color_cls}">
        <div class="kpi-title">Sistema Óptimo</div>
        <div class="kpi-value">Sistema {sistema_optimo}</div>
        <div class="kpi-sub">Menor VAN = menor carga en valor presente</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card kpi-gold">
        <div class="kpi-title">Ahorro Financiero (VAN)</div>
        <div class="kpi-value">S/ {ahorro:,.2f}</div>
        <div class="kpi-sub">Sistema {sistema_optimo} vs. Sistema {"B" if sistema_optimo=="A" else "A"}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RECOMENDACIÓN DINÁMICA
# ─────────────────────────────────────────────
beneficio_perdido_a = sum(r["beneficio_perdido"] for r in res_a)
saldo_final_b = res_b[-1]["saldo_pdn"]

if sistema_optimo == "A":
    st.markdown(f"""
    <div class="rec-box rec-a">
        ✅ <strong>SISTEMA A RECOMENDADO</strong> — En valor presente, el Sistema A genera un menor desembolso
        de impuestos por <strong>S/ {ahorro:,.2f}</strong> respecto al Sistema B.
        La absorción completa de la PDN en los primeros 4 años maximiza el escudo fiscal inmediato.
        {"⚠️ Nota: Quedan S/ " + f"{beneficio_perdido_a:,.2f} de PDN sin compensar al vencer el plazo (beneficio perdido)." if beneficio_perdido_a > 0 else ""}
        <span class="badge">Art. 50° LIR — Sistema A</span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="rec-box rec-b">
        🔶 <strong>SISTEMA B RECOMENDADO</strong> — El Sistema B genera un menor desembolso en VAN
        por <strong>S/ {ahorro:,.2f}</strong>. Al distribuir la compensación en el tiempo (50% indefinido),
        la carga fiscal se diferiere de forma más eficiente según las proyecciones ingresadas.
        {"Saldo PDN pendiente al Año 5: S/ " + f"{saldo_final_b:,.2f} (se arrastra indefinidamente)." if saldo_final_b > 0 else ""}
        <span class="badge">Art. 50° LIR — Sistema B</span>
    </div>""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────
# TABLA COMPARATIVA AÑO A AÑO
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">📋 Tabla Dinámica Comparativa — Año a Año (Sistemas A vs. B)</div>',
            unsafe_allow_html=True)

años = [f"Año {r['año']}" for r in res_a]
df_tabla = pd.DataFrame({
    "Año":                  años,
    "Renta Neta (S/)":      [f"{r['renta_neta']:,.2f}" for r in res_a],
    # Sistema A
    "A — Compensada":       [f"{r['compensada']:,.2f}" for r in res_a],
    "A — Saldo PDN":        [f"{r['saldo_pdn']:,.2f}" for r in res_a],
    "A — Renta Imponible":  [f"{r['renta_imponible']:,.2f}" for r in res_a],
    "A — IR Pagado":        [f"{r['ir']:,.2f}" for r in res_a],
    # Sistema B
    "B — Compensada (50%)": [f"{r['compensada']:,.2f}" for r in res_b],
    "B — Saldo PDN":        [f"{r['saldo_pdn']:,.2f}" for r in res_b],
    "B — Renta Imponible":  [f"{r['renta_imponible']:,.2f}" for r in res_b],
    "B — IR Pagado":        [f"{r['ir']:,.2f}" for r in res_b],
})

# Agregar fila de totales
totales = {
    "Año": "TOTAL",
    "Renta Neta (S/)": f"{sum(rentas):,.2f}",
    "A — Compensada": f"{sum(r['compensada'] for r in res_a):,.2f}",
    "A — Saldo PDN": "—",
    "A — Renta Imponible": f"{sum(r['renta_imponible'] for r in res_a):,.2f}",
    "A — IR Pagado": f"{total_ir_a:,.2f}",
    "B — Compensada (50%)": f"{sum(r['compensada'] for r in res_b):,.2f}",
    "B — Saldo PDN": f"{saldo_final_b:,.2f}",
    "B — Renta Imponible": f"{sum(r['renta_imponible'] for r in res_b):,.2f}",
    "B — IR Pagado": f"{total_ir_b:,.2f}",
}
df_tabla = pd.concat([df_tabla, pd.DataFrame([totales])], ignore_index=True)
st.dataframe(df_tabla, use_container_width=True, height=260)

# Nota pie de tabla
if beneficio_perdido_a > 0:
    st.warning(f"⚠️ Sistema A: S/ {beneficio_perdido_a:,.2f} de PDN venció al Año 5 sin ser compensada (beneficio perdido). "
               f"Esto reduce la ventaja del Sistema A o puede invertir la recomendación.")
if saldo_final_b > 0:
    st.info(f"ℹ️ Sistema B: Queda un saldo de PDN de S/ {saldo_final_b:,.2f} pendiente al Año 5. "
            f"Se arrastra indefinidamente según el Art. 50° LIR.")

st.divider()

# ─────────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────────
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    st.markdown('<div class="section-hdr">📊 IR Pagado por Año — Velocidad de Absorción del Escudo Fiscal</div>',
                unsafe_allow_html=True)

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Sistema A — IR Pagado",
        x=años, y=ir_a,
        marker_color="#1565c0", opacity=0.9,
        text=[f"S/ {v:,.0f}" for v in ir_a],
        textposition="outside", textfont=dict(size=11, color="#90caf9"),
    ))
    fig_bar.add_trace(go.Bar(
        name="Sistema B — IR Pagado",
        x=años, y=ir_b,
        marker_color="#ef6c00", opacity=0.9,
        text=[f"S/ {v:,.0f}" for v in ir_b],
        textposition="outside", textfont=dict(size=11, color="#ffcc80"),
    ))
    fig_bar.update_layout(
        barmode="group", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.22),
        yaxis=dict(title="Impuesto a la Renta (S/)"),
        margin=dict(l=10, r=10, t=20, b=60), height=380,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_g2:
    st.markdown('<div class="section-hdr">📉 Evolución del Saldo de PDN Pendiente</div>',
                unsafe_allow_html=True)

    saldo_a = [pdn_input] + [r["saldo_pdn"] for r in res_a]
    saldo_b = [pdn_input] + [r["saldo_pdn"] for r in res_b]
    ejes_x  = ["Año 0"] + años

    fig_saldo = go.Figure()
    fig_saldo.add_trace(go.Scatter(
        x=ejes_x, y=saldo_a, name="Saldo PDN — Sistema A",
        mode="lines+markers", line=dict(color="#4fc3f7", width=2.5, dash="solid"),
        marker=dict(size=8), fill="tozeroy", fillcolor="rgba(79,195,247,0.08)"
    ))
    fig_saldo.add_trace(go.Scatter(
        x=ejes_x, y=saldo_b, name="Saldo PDN — Sistema B",
        mode="lines+markers", line=dict(color="#ff8f00", width=2.5, dash="dot"),
        marker=dict(size=8), fill="tozeroy", fillcolor="rgba(255,143,0,0.08)"
    ))
    fig_saldo.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.25),
        yaxis=dict(title="Saldo PDN (S/)"),
        margin=dict(l=10, r=10, t=20, b=60), height=380,
    )
    st.plotly_chart(fig_saldo, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# ANÁLISIS VAN DETALLADO
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">🧮 Descomposición del VAN — Flujo de Salida de Impuestos Descontados</div>',
            unsafe_allow_html=True)

factores = [round(1 / (1 + cok) ** t, 6) for t in range(1, 6)]
van_a_anual = [round(ir * f, 2) for ir, f in zip(ir_a, factores)]
van_b_anual = [round(ir * f, 2) for ir, f in zip(ir_b, factores)]

df_van = pd.DataFrame({
    "Año": años,
    f"Factor Desc. (COK={cok_pct}%)": [f"{f:.6f}" for f in factores],
    "A — IR Nominal": [f"S/ {v:,.2f}" for v in ir_a],
    "A — IR Descontado": [f"S/ {v:,.2f}" for v in van_a_anual],
    "B — IR Nominal": [f"S/ {v:,.2f}" for v in ir_b],
    "B — IR Descontado": [f"S/ {v:,.2f}" for v in van_b_anual],
})
totales_van = {
    "Año": "VAN TOTAL",
    f"Factor Desc. (COK={cok_pct}%)": "—",
    "A — IR Nominal": f"S/ {total_ir_a:,.2f}",
    "A — IR Descontado": f"S/ {van_a:,.2f}",
    "B — IR Nominal": f"S/ {total_ir_b:,.2f}",
    "B — IR Descontado": f"S/ {van_b:,.2f}",
}
df_van = pd.concat([df_van, pd.DataFrame([totales_van])], ignore_index=True)
st.dataframe(df_van, use_container_width=True)

# ─────────────────────────────────────────────
# WATERFALL — AHORRO VAN
# ─────────────────────────────────────────────
st.markdown('<div class="section-hdr">💧 Diferencial de Ahorro Fiscal (VAN) — Año a Año</div>',
            unsafe_allow_html=True)

diff_van = [round(b - a, 2) for a, b in zip(van_a_anual, van_b_anual)]
colores_diff = ["#69f0ae" if d > 0 else "#ff5252" for d in diff_van]

fig_wf = go.Figure(go.Bar(
    x=años, y=diff_van,
    marker_color=colores_diff,
    text=[f"S/ {v:+,.2f}" for v in diff_van],
    textposition="outside",
    name="VAN(B) − VAN(A) por año"
))
fig_wf.add_hline(y=0, line_dash="dot", line_color="#78909c")
fig_wf.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(title="Diferencial S/ (positivo = A es mejor ese año)"),
    margin=dict(l=10, r=10, t=20, b=20), height=280,
    annotations=[dict(
        text=f"Total diferencial VAN: S/ {sum(diff_van):+,.2f} → Sistema {sistema_optimo} óptimo",
        x=0.5, y=1.08, xref="paper", yref="paper",
        showarrow=False, font=dict(color="#ffd740", size=12)
    )]
)
st.plotly_chart(fig_wf, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# BASE LEGAL Y NOTAS
# ─────────────────────────────────────────────
with st.expander("📚 Base Legal y Metodología"):
    st.markdown("""
    | Norma | Descripción |
    |---|---|
    | **Art. 50° TUO LIR** (D.S. 179-2004-EF) | Sistemas A y B de compensación de Pérdidas Tributarias Netas |
    | **D. Leg. N.° 1269** — Art. 6° | Tasas RMT: 10% hasta 15 UIT, 29.5% por exceso |
    | **D.S. N.° 309-2023-EF** | UIT 2024 = S/ 5,250 |

    **Sistema A:** Absorción del 100% de la renta neta por año, con límite de 4 ejercicios gravables contados
    desde el ejercicio siguiente al de la pérdida. Saldo no compensado al vencer el plazo: beneficio perdido.

    **Sistema B:** Compensación del 50% de la renta neta de cada ejercicio posterior, sin límite temporal.
    El saldo se arrastra indefinidamente hasta agotarse.

    **VAN del impuesto:** Mide el valor presente de la carga fiscal futura. El sistema con **menor VAN**
    implica menor desembolso real de dinero en términos de valor presente → sistema óptimo.

    **Fórmula:** VAN = Σ [ IR_t / (1 + COK)^t ] para t = 1 … n
    """)

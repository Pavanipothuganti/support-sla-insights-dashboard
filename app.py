"""Streamlit dashboard for the generated SLA reports."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from run_analysis import run

st.set_page_config(page_title="Support SLA Breach Analysis", page_icon="SLA", layout="wide")
REPORTS = Path("reports")


@st.cache_data
def load_report(name: str) -> pd.DataFrame:
    return pd.read_csv(REPORTS / name)


st.title("Support SLA Breach Analysis Dashboard")
st.caption("Weekly first-response SLA performance by agent and shift")
with st.sidebar:
    st.header("Controls")
    cost = st.number_input("Cost per breached ticket", min_value=0.0, value=350.0, step=50.0)
    target = st.number_input("Target breach rate (%)", min_value=0.0, max_value=100.0, value=15.0, step=1.0)
    if st.button("Run analysis", type="primary"):
        try:
            run(cost_per_breach=cost, target_rate=target)
            load_report.clear()
            st.success("Reports generated")
        except Exception as exc:
            st.error(str(exc))

page = st.sidebar.radio("Page", ("Dashboard Overview", "Agent Analysis", "Shift Analysis", "Weekly Trends", "Business Impact"))
try:
    weekly = load_report("weekly_sla_report.csv")
    agents = load_report("agent_performance_report.csv")
    shifts = load_report("shift_performance_report.csv")
    impact = load_report("business_impact_report.csv")
except FileNotFoundError:
    st.info("Add the source files to data/ and click Run analysis.")
    st.stop()

if page == "Dashboard Overview":
    current = float((weekly["breaches"].sum() / weekly["total_tickets"].sum()) * 100) if len(weekly) else 0
    first, second, third = st.columns(3)
    first.metric("Tickets analysed", f"{weekly['total_tickets'].sum():,.0f}")
    second.metric("Current breach rate", f"{current:.2f}%")
    third.metric("Total breaches", f"{weekly['breaches'].sum():,.0f}")
    st.plotly_chart(px.line(weekly, x="week", y="breach_rate_pct", markers=True, title="Weekly breach rate"), use_container_width=True)
elif page == "Agent Analysis":
    st.subheader("Top agents by breached tickets")
    st.dataframe(agents.head(10), use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(agents.head(10), x="agent", y="breached_tickets", color="breach_percentage", title="Top 10 agents"), use_container_width=True)
elif page == "Shift Analysis":
    st.dataframe(shifts, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(shifts, x="shift", y="breach_percentage", title="Breach rate by shift"), use_container_width=True)
elif page == "Weekly Trends":
    st.dataframe(weekly, use_container_width=True, hide_index=True)
    st.plotly_chart(px.line(weekly, x="week", y=["total_tickets", "breaches"], markers=True, title="Weekly volume and breaches"), use_container_width=True)
else:
    st.subheader("Business impact")
    st.dataframe(impact.T.rename(columns={0: "value"}), use_container_width=True)

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="NairaBits",
    page_icon="🇳🇬",
    layout="wide"
)

DB_PATH = "NairaBits-pipeline/nairabits.db"

@st.cache_resource
def get_conn():
    return duckdb.connect(DB_PATH, read_only=True)

@st.cache_data
def query(sql):
    return get_conn().execute(sql).df()

def latest_and_prev(df, col):
    valid = df[df[col].notna()][col]
    if len(valid) >= 2:
        return valid.iloc[-1], valid.iloc[-2]
    elif len(valid) == 1:
        return valid.iloc[-1], None
    return None, None

def fmt_metric(val, fmt, suffix=""):
    return f"{val:{fmt}}{suffix}" if val is not None else "N/A"

def fmt_delta(now, prev, fmt="+.1f", suffix=""):
    if now is None or prev is None:
        return None
    return f"{now - prev:{fmt}}{suffix}"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("NairaBits")
st.caption(
    "Nigeria's economic reality in data — Naira collapse, growth gaps "
    "and the electricity access crisis across 10 African nations."
)

# ── Hero metrics ──────────────────────────────────────────────────────────────
ngn = query("""
    SELECT avg_rate, monthly_return_pct
    FROM analytics.naira_volatility
    WHERE currency = 'NGN'
    ORDER BY month DESC LIMIT 1
""")

worst = query("""
    SELECT month, monthly_return_pct
    FROM analytics.naira_volatility
    WHERE currency = 'NGN'
    ORDER BY monthly_return_pct DESC LIMIT 1
""")

top_gdp = query("""
    SELECT country_name, gdp_growth
    FROM analytics.gdp_growth
    WHERE year = (
        SELECT MAX(year) FROM analytics.gdp_growth
        WHERE gdp_growth IS NOT NULL
    )
    ORDER BY gdp_growth DESC LIMIT 1
""")

elec = query("""
    SELECT ROUND(AVG(electricity_access), 1) AS avg_access
    FROM analytics.gdp_growth
    WHERE year = (
        SELECT MAX(year) FROM analytics.gdp_growth
        WHERE electricity_access IS NOT NULL
    )
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "USD/NGN — current month avg",
    fmt_metric(ngn['avg_rate'].iloc[0], ",.0f"),
    fmt_delta(ngn['monthly_return_pct'].iloc[0], 0, fmt="+.1f", suffix="% vs prior month")
)
col2.metric(
    "Worst NGN month on record",
    pd.to_datetime(worst['month'].iloc[0]).strftime("%b %Y"),
    f"{worst['monthly_return_pct'].iloc[0]:+.1f}% depreciation"
)
col3.metric(
    "Fastest growing economy",
    top_gdp['country_name'].iloc[0],
    f"{top_gdp['gdp_growth'].iloc[0]:+.1f}% GDP growth"
)
col4.metric(
    "Avg electricity access",
    fmt_metric(elec['avg_access'].iloc[0], ".1f", "%"),
    "across 10 African nations"
)

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "💸 The Naira Collapse",
    "🇳🇬 Nigeria Deep Dive",
    "🌍 Continental View"
])

# ── Tab 1: Naira Collapse ─────────────────────────────────────────────────────
with tab1:
    st.subheader("How African currencies moved against the USD")
    st.caption(
        "A rising line means the currency is weakening — "
        "you need more of it to buy one US dollar."
    )

    fx = query("""
        SELECT month, currency, avg_rate, monthly_return_pct, volatility
        FROM analytics.naira_volatility
        ORDER BY month
    """)

    selected = st.multiselect(
        "Compare currencies",
        options=["NGN", "KES", "ZAR", "GHS", "EGP"],
        default=["NGN", "KES", "GHS"]
    )
    filtered = fx[fx["currency"].isin(selected)]

    # Normalise to 100 at start so all currencies are comparable on one chart
    def normalise(df):
        out = []
        for cur, grp in df.groupby("currency"):
            grp = grp.sort_values("month").copy()
            base = grp["avg_rate"].iloc[0]
            grp["indexed"] = (grp["avg_rate"] / base) * 100
            out.append(grp)
        return pd.concat(out)

    norm = normalise(filtered)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.line(
            norm, x="month", y="indexed", color="currency",
            title="Depreciation index (start = 100)",
            labels={"indexed": "Index (start=100)", "month": ""},
        )
        fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(legend_title="Currency")
        st.plotly_chart(fig, width="stretch")

    with col_b:
        fig2 = px.line(
            filtered, x="month", y="monthly_return_pct", color="currency",
            title="Monthly return % (negative means the currency strengthened)",
            labels={"monthly_return_pct": "Monthly return %", "month": ""}
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig2, width="stretch")

    st.subheader("Naira crash timeline — worst months")
    ngn_monthly = fx[fx["currency"] == "NGN"].sort_values("month")
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=ngn_monthly["month"],
        y=ngn_monthly["monthly_return_pct"],
        marker_color=ngn_monthly["monthly_return_pct"].apply(
            lambda x: "#e74c3c" if x > 0 else "#2ecc71"
        ),
        name="Monthly return %"
    ))
    fig3.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig3.update_layout(
        title="NGN monthly return % (red bars = Naira lost value)",
        yaxis_title="Return %",
        xaxis_title="",
        showlegend=False
    )
    st.plotly_chart(fig3, width="stretch")

    st.subheader("Volatility — which currency is most turbulent?")
    fig4 = px.line(
        filtered, x="month", y="volatility", color="currency",
        title="30-day rolling volatility",
        labels={"volatility": "Volatility (std dev)", "month": ""}
    )
    st.plotly_chart(fig4, width="stretch")


# ── Tab 2: Nigeria Deep Dive ──────────────────────────────────────────────────
with tab2:
    st.subheader("Nigeria — YoY currency, growth, and the power deficit")

    ng = query("""
        SELECT year, gdp_growth, inflation, electricity_access,
               unemployment, avg_usd_ngn
        FROM analytics.nigeria_focus
        ORDER BY year
    """)

    gdp_now,  gdp_prev  = latest_and_prev(ng, "gdp_growth")
    ngn_now,  ngn_prev  = latest_and_prev(ng, "avg_usd_ngn")
    elec_now, elec_prev = latest_and_prev(ng, "electricity_access")
    inf_now,  inf_prev  = latest_and_prev(ng, "inflation")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("GDP growth",
                 fmt_metric(gdp_now, ".1f", "%"),
                 fmt_delta(gdp_now, gdp_prev, suffix=" vs prior year"))
    col_b.metric("USD/NGN — yearly avg",
             fmt_metric(ngn_now, ",.0f"),
             fmt_delta(ngn_now, ngn_prev, fmt="+,.0f", suffix=" vs prior year"))
    col_c.metric("Electricity access",
                 fmt_metric(elec_now, ".1f", "%"),
                 fmt_delta(elec_now, elec_prev, suffix=" vs prior year"))
    col_d.metric("Inflation",
                 fmt_metric(inf_now, ".1f", "%"),
                 fmt_delta(inf_now, inf_prev, suffix=" vs prior year"))

    # Dual axis: GDP vs NGN rate
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ng["year"], y=ng["gdp_growth"],
        name="GDP growth %",
        marker_color="#3498db",
        yaxis="y"
    ))
    fig.add_trace(go.Scatter(
        x=ng["year"], y=ng["avg_usd_ngn"],
        name="USD/NGN rate",
        line=dict(color="#e74c3c", width=2),
        yaxis="y2"
    ))
    fig.update_layout(
        title="Nigeria: GDP growth vs Naira depreciation",
        yaxis=dict(title="GDP Growth %", side="left"),
        yaxis2=dict(title="USD/NGN", overlaying="y",
                    side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        xaxis_title=""
    )
    st.plotly_chart(fig, width="stretch")

    col_a, col_b = st.columns(2)
    with col_a:
        fig2 = px.line(
            ng.dropna(subset=["electricity_access"]),
            x="year", y="electricity_access",
            markers=True,
            title="Electricity access (% of population)",
            labels={"electricity_access": "%", "year": ""}
        )
        fig2.update_traces(line_color="#f39c12")
        st.plotly_chart(fig2, width="stretch")

    with col_b:
        fig3 = px.line(
            ng.dropna(subset=["inflation"]),
            x="year", y="inflation",
            markers=True,
            title="Inflation rate %",
            labels={"inflation": "%", "year": ""}
        )
        fig3.update_traces(line_color="#e74c3c")
        st.plotly_chart(fig3, width="stretch")


# ── Tab 3: Continental View ───────────────────────────────────────────────────
with tab3:
    st.subheader("How do Africa's economies compare?")

    gdp_data = query("""
        SELECT country_name, year, gdp_growth, inflation,
               fdi_pct_gdp, electricity_access, gdp_3yr_avg, growth_rank
        FROM analytics.gdp_growth
        ORDER BY year, growth_rank
    """)

    valid_years = sorted(
        gdp_data.dropna(subset=["gdp_growth"])["year"].unique(), reverse=False
    )
    year = st.select_slider("Select year", options=valid_years)
    year_data = gdp_data[gdp_data["year"] == year].sort_values(
        "gdp_growth", ascending=True
    )

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            year_data.dropna(subset=["gdp_growth"]),
            x="gdp_growth", y="country_name",
            orientation="h",
            title=f"GDP growth ranking — {year}",
            labels={"gdp_growth": "GDP Growth %", "country_name": ""},
            color="gdp_growth",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0
        )
        fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

    with col_b:
        elec_data = year_data.dropna(subset=["electricity_access"])

        # If selected year has no electricity data, fall back to nearest year that does
        if elec_data.empty:
            fallback_year = (
                gdp_data.dropna(subset=["electricity_access"])
                .query("year <= @year")["year"]
                .max()
            )
            elec_data = gdp_data[
                gdp_data["year"] == fallback_year
            ].dropna(subset=["electricity_access"])
            elec_title = f"Electricity access — % of population ({int(fallback_year)}, latest available)"
        else:
            elec_title = f"Electricity access — % of population ({year})"

        elec_data = elec_data.sort_values("electricity_access", ascending=True)

        fig2 = px.bar(
            elec_data,
            x="electricity_access", y="country_name",
            orientation="h",
            title=elec_title,
            labels={"electricity_access": "%", "country_name": ""},
            color="electricity_access",
            color_continuous_scale="YlOrRd"
        )
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, width="stretch")

    st.subheader("Growth vs inflation — the pressure map")
    scatter_data = gdp_data[
        (gdp_data["year"] == year) &
        gdp_data["gdp_growth"].notna() &
        gdp_data["inflation"].notna()
    ]
    fig3 = px.scatter(
        scatter_data,
        x="inflation", y="gdp_growth",
        text="country_name",
        title=f"GDP growth vs inflation — {year}",
        labels={"inflation": "Inflation %", "gdp_growth": "GDP Growth %"},
        color="electricity_access",
        color_continuous_scale="Blues",
        size_max=20
    )
    fig3.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
    fig3.update_traces(textposition="top center")
    fig3.update_layout(coloraxis_colorbar=dict(title="Electricity<br>access %"))
    st.plotly_chart(fig3, width="stretch")
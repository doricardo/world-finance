import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta, timezone

# ---------- Configuration ------------------------------------------------
INDEXES = {
    "S&P 500":             {"ticker": "^GSPC",     "calendar": "NYSE",  "country": "us"},
    "NASDAQ":              {"ticker": "^IXIC",     "calendar": "NASDAQ","country": "us"},
    "FTSE 100":            {"ticker": "^FTSE",     "calendar": "LSE",   "country": "gb"},
    "DAX":                 {"ticker": "^GDAXI",    "calendar": "XETR",  "country": "de"},
    "Nikkei 225":          {"ticker": "^N225",     "calendar": "JPX",   "country": "jp"},
    "S&P/ASX 200":         {"ticker": "^AXJO",     "calendar": "ASX",   "country": "au"},
    "IBOVESPA":            {"ticker": "^BVSP",     "calendar": "B3",    "country": "br"},
    "CSI 300":             {"ticker": "000300.SS", "calendar": "SSE",   "country": "cn"},
    "CSI 1000":            {"ticker": "000852.SS", "calendar": "SSE",   "country": "cn"},
}
REFRESH_EVERY = 60
TODAY_UTC      = datetime.now(timezone.utc).date()
# -------------------------------------------------------------------------

@st.cache_data(ttl=REFRESH_EVERY, show_spinner=False)
def fetch_today_series(ticker: str) -> pd.Series:
    for interval in ("1m", "5m"):
        df = yf.download(ticker, interval=interval, period="7d",
                         auto_adjust=False, progress=False, threads=False)
        close = df.get("Close")
        if close is None or close.empty:
            continue
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        today = close[close.index.date == TODAY_UTC].dropna()
        if not today.empty:
            return today.tz_convert("UTC")

    df_daily = yf.download(ticker, interval="1d", period="1d",
                           auto_adjust=False, progress=False, threads=False)
    close = df_daily.get("Close")
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    if not close.empty:
        value = close.iloc[0]
        return pd.Series(value,
                         index=pd.date_range(start=datetime.combine(TODAY_UTC, datetime.min.time(), tzinfo=timezone.utc),
                                             end=datetime.now(timezone.utc), freq="1min"),
                         name="Close")

    df_daily = yf.download(ticker, interval="1d", period="5d",
                           auto_adjust=False, progress=False, threads=False)
    close = df_daily.get("Close")
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    if close.empty:
        return pd.Series(dtype=float)

    value = close.iloc[-1]
    return pd.Series(value,
                     index=pd.date_range(start=datetime.combine(TODAY_UTC, datetime.min.time(), tzinfo=timezone.utc),
                                         end=datetime.now(timezone.utc), freq="1min"),
                     name="Close")

def is_market_open(calendar_code: str) -> bool:
    cal   = mcal.get_calendar(calendar_code)
    now   = datetime.now(timezone.utc)
    sched = cal.schedule(start_date=(now - timedelta(days=1)).date(),
                         end_date=(now + timedelta(days=1)).date())
    if sched.empty:
        return False
    try:
        return cal.open_at_time(sched, now)
    except ValueError:
        return False

# ---------- UI -----------------------------------------------------------
st.set_page_config(page_title="World Indices Live", layout="wide")
st_autorefresh(interval=REFRESH_EVERY * 1000, key="data_refresh")

# ↓ smaller font for metric value
st.markdown(
    """
    <style>
    div[data-testid="stMetricValue"] > div {
        font-size: 1.25rem;
        line-height: 1.2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 📈 Global Stock‑Market")

cols = st.columns(len(INDEXES))

for col, (name, cfg) in zip(cols, INDEXES.items()):
    series = fetch_today_series(cfg["ticker"])
    if series.empty:
        col.warning("No data")
        continue

    last_price = float(series.iloc[-1])
    open_price = float(series.iloc[0])
    pct_series = (series - open_price) / open_price * 100
    delta_pct  = pct_series.iloc[-1]

    # ---------- custom header with flag + name --------------------------
    flag_url = f"https://flagcdn.com/20x15/{cfg['country']}.png"
    col.markdown(
        f"<div style='display:flex; align-items:center; gap:4px;'>"
        f"<img src='{flag_url}' width='20' height='15'>"
        f"<strong>{name}</strong></div>",
        unsafe_allow_html=True,
    )

    # metric (label left blank to save vertical space)
    col.metric(
        label="\u00A0",  # NBSP → satisfaz o Streamlit, mas não aparece
        value=f"{last_price:,.2f}",
        delta=f"{delta_pct:+.2f}%"
    )
    #col.metric(label="", value=f"{last_price:,.2f}", delta=f"{delta_pct:+.2f}%")

    # market status
    status = "🟢 **Open**" if is_market_open(cfg["calendar"]) else "🔴 **Closed**"
    col.caption(status)

    # chart
    col.line_chart(pct_series.to_frame(name="Δ%"), height=200)

    # last update
    last_ts = series.index[-1].tz_convert("UTC")
    col.caption(f"Last update: {last_ts.strftime('%H:%M')} UTC")

st.caption(
    f"⏱️ Auto‑refresh every {REFRESH_EVERY} s — free Yahoo feed delay ≈ 15 min."
)

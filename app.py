import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta, timezone

# ---------- Configuration ------------------------------------------------
# Each market includes its Yahoo ticker, market calendar code, and ISO country code
# (lower‑case for use in the flag URL)
INDEXES = {
    "S&P 500": {"ticker": "^GSPC", "calendar": "NYSE", "country": "us"},
    "NASDAQ": {"ticker": "^IXIC", "calendar": "NASDAQ", "country": "us"},
    "FTSE 100": {"ticker": "^FTSE", "calendar": "LSE", "country": "gb"},
    "DAX": {"ticker": "^GDAXI", "calendar": "XETR", "country": "de"},
    "Nikkei 225": {"ticker": "^N225", "calendar": "JPX", "country": "jp"},
    "S&P/ASX 200": {"ticker": "^AXJO", "calendar": "ASX", "country": "au"},
    "IBOVESPA": {"ticker": "^BVSP", "calendar": "B3", "country": "br"},
    "CSI 300": {"ticker": "000300.SS", "calendar": "SSE", "country": "cn"},
    "CSI 1000": {"ticker": "000852.SS", "calendar": "SSE", "country": "cn"},
}
REFRESH_EVERY = 60  # seconds
TODAY_UTC = datetime.now(timezone.utc).date()


# -------------------------------------------------------------------------

@st.cache_data(ttl=REFRESH_EVERY, show_spinner=False)
def fetch_today_series(ticker: str) -> pd.Series:
    """
    Fetch today's price series using the best granularity available.
    1. Tries intraday data (1m then 5m) for the last 7 days and returns only today's data.
    2. Else, uses daily data for today expanded to minutes.
    3. If still nothing, uses the last available daily close (up to 5 days back) expanded to minutes.
    Returns a tz‑aware Series indexed in UTC.
    """
    for interval in ("1m", "5m"):
        df = yf.download(
            tickers=ticker,
            interval=interval,
            period="7d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        close = df.get("Close")
        if close is None or close.empty:
            continue
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        # Only include today's rows
        today = close[close.index.date == TODAY_UTC].dropna()
        if not today.empty:
            return today.tz_convert("UTC")

    df_daily = yf.download(
        tickers=ticker,
        interval="1d",
        period="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    close = df_daily.get("Close")
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    if not close.empty:
        val = close.iloc[0]
        return pd.Series(
            val,
            index=pd.date_range(
                start=datetime.combine(TODAY_UTC, datetime.min.time(), tzinfo=timezone.utc),
                end=datetime.now(timezone.utc),
                freq="1min",
            ),
            name="Close",
        )

    # Last daily close up to 5 days back
    df_daily = yf.download(
        tickers=ticker,
        interval="1d",
        period="5d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )
    close = df_daily.get("Close")
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()
    if close.empty:
        return pd.Series(dtype=float)

    val = close.iloc[-1]
    return pd.Series(
        val,
        index=pd.date_range(
            start=datetime.combine(TODAY_UTC, datetime.min.time(), tzinfo=timezone.utc),
            end=datetime.now(timezone.utc),
            freq="1min",
        ),
        name="Close",
    )


def is_market_open(calendar_code: str) -> bool:
    """Determine if the market is open at the current UTC time using the market calendar."""
    cal = mcal.get_calendar(calendar_code)
    now = datetime.now(timezone.utc)
    sched = cal.schedule(
        start_date=(now - timedelta(days=1)).date(),
        end_date=(now + timedelta(days=1)).date(),
    )
    if sched.empty:
        return False
    try:
        return cal.open_at_time(sched, now)
    except ValueError:
        return False


# ---------- UI -----------------------------------------------------------
st.set_page_config(page_title="World Indices Live", layout="wide")

# CSS adjustments to reduce top spacing and vertical margins for captions
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
    }
    /* Reduce vertical spacing for caption elements */
    [data-testid="stCaption"] {
        margin-top: 2px;
        margin-bottom: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st_autorefresh(interval=REFRESH_EVERY * 1000, key="data_refresh")

# Title using markdown
st.markdown("### 📈 Global Stock‑Market")

# Prepare market data and group markets by open/closed status.
market_data = []
for name, cfg in INDEXES.items():
    series = fetch_today_series(cfg["ticker"])
    if series.empty:
        continue
    last_price = float(series.iloc[-1])
    open_price = float(series.iloc[0])
    pct_series = (series - open_price) / open_price * 100
    delta_pct = pct_series.iloc[-1]
    status_bool = is_market_open(cfg["calendar"])
    status = "🟢 Open" if status_bool else "🔴 Closed"
    flag_url = f"https://flagcdn.com/20x15/{cfg['country']}.png"
    last_ts = series.index[-1].tz_convert("UTC")

    market_data.append({
        "name": name,
        "flag_url": flag_url,
        "last_price": last_price,
        "delta_pct": delta_pct,
        "pct_series": pct_series,
        "status": status,
        "is_open": status_bool,
        "last_ts": last_ts,
    })

# Group open and closed markets into separate lists.
open_markets = [m for m in market_data if m["is_open"]]
closed_markets = [m for m in market_data if not m["is_open"]]

# --- Display Open Markets Group ---
if open_markets:
    st.markdown("##### Open Markets")
    cols = st.columns(len(open_markets))
    for col, market in zip(cols, open_markets):
        # Flag and market name (HTML)
        col.markdown(
            f"""
            <p style="margin-bottom: 0px;">
                <img src="{market['flag_url']}" width="20" style="vertical-align:middle;margin-right:5px;">
                <strong>{market['name']}</strong>
            </p>
            """,
            unsafe_allow_html=True,
        )
        # Update time immediately below (show only HH:MM UTC)
        col.caption(f"{market['last_ts'].strftime('%H:%M')} UTC")

        col.metric(
            label="\u00A0",  # non-breaking space for accessibility (empty label)
            value=f"{market['last_price']:,.2f}",
            delta=f"{market['delta_pct']:+.2f}%"
        )
        col.caption(market["status"])
        col.line_chart(market["pct_series"].to_frame(name="Δ%"), height=200)

# --- Display Closed Markets Group ---
if closed_markets:
    st.markdown("##### Closed Markets")
    cols = st.columns(len(closed_markets))
    for col, market in zip(cols, closed_markets):
        col.markdown(
            f"""
            <p style="margin-bottom: 0px;">
                <img src="{market['flag_url']}" width="20" style="vertical-align:middle;margin-right:5px;">
                <strong>{market['name']}</strong>
            </p>
            """,
            unsafe_allow_html=True,
        )
        col.caption(f"{market['last_ts'].strftime('%H:%M')} UTC")

        col.metric(
            label="\u00A0",
            value=f"{market['last_price']:,.2f}",
            delta=f"{market['delta_pct']:+.2f}%"
        )
        col.caption(market["status"])
        col.line_chart(market["pct_series"].to_frame(name="Δ%"), height=200)

st.caption(
    f"⏱️ Auto‑refresh every {REFRESH_EVERY} s — free Yahoo feed delay ≈ 15 min."
)

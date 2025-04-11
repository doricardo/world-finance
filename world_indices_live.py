from datetime import timedelta
import pytz
import yfinance as yf
import pandas as pd
import pandas_market_calendars as mcal
import matplotlib.pyplot as plt

# --- CONFIG -------------------------------------------------------------
INDEXES = {
    "S&P 500":   {"ticker": "^GSPC",  "calendar": "NYSE"},
    "NASDAQ":    {"ticker": "^IXIC",  "calendar": "NASDAQ"},
    "FTSE 100":  {"ticker": "^FTSE",  "calendar": "LSE"},
    "DAX":       {"ticker": "^GDAXI", "calendar": "XETR"},   # <‑‑ aqui!
    "Nikkei 225":{"ticker": "^N225",  "calendar": "JPX"},
}


INTERVAL = "1m"      # granularidade
PERIOD   = "1d"      # somente hoje
# ------------------------------------------------------------------------

def is_market_open(calendar_code):

    try:
        cal = mcal.get_calendar(calendar_code)
    except RuntimeError:
        # calendário não encontrado → considere como fechado
        return False

    # corrigido ↓
    now_utc = pd.Timestamp.utcnow()  # já em UTC e tz‑aware

    start = (now_utc - timedelta(days=3)).date()
    end   = (now_utc + timedelta(days=3)).date()
    sched = cal.schedule(start_date=start, end_date=end)

    if sched.empty:
        return False

    try:
        return cal.open_at_time(sched, now_utc)
    except ValueError:
        return False


def fetch_intraday(ticker):
    """Baixa histórico intradiário do dia atual."""
    return yf.download(
        tickers=ticker,
        interval=INTERVAL,
        period=PERIOD,
        progress=False
    )["Close"]

def main():
    fig, ax = plt.subplots()
    open_status = {}

    for name, cfg in INDEXES.items():
        series = fetch_intraday(cfg["ticker"])
        series.index = series.index.tz_convert("UTC")  # normaliza
        ax.plot(series.index, series, label=name)
        open_status[name] = is_market_open(cfg["calendar"])

    ax.set_title("Índices globais – evolução intradiária")
    ax.set_xlabel("Horário (UTC)")
    ax.set_ylabel("Pontos")
    ax.legend()
    ax.grid(True)

    # Mostra status das bolsas no console
    print("----- STATUS DAS BOLSAS -----")
    for name, status in open_status.items():
        print(f"{name:10} : {'ABERTA' if status else 'FECHADA'}")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()

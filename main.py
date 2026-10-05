"""M10 PMLS Assignment 1 - Skin clinic campaign response analysis, served by FastAPI."""
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

DATA = Path(__file__).parent / "skin_clinic_campaign.csv"
TARGET = "Response_to_Campaign"

app = FastAPI(title="Skin Clinic Campaign Analysis")


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    # Extract: bin unique products purchased into 1-4, 5-8, >8
    df["Product_Usage"] = pd.cut(
        df["Unique_Products_Purchased"], bins=[0, 4, 8, float("inf")], labels=["1-4", "5-8", ">8"]
    )
    df["AgeGroup"] = pd.Categorical(df["AgeGroup"], categories=["<30", "30-50", ">50"], ordered=True)
    df["Responded"] = df[TARGET].eq("Yes")
    return df


def response_rate(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Aggregate: one row per category of `by` -> customers, responders, response rate (%)."""
    out = df.groupby(by, observed=True)["Responded"].agg(Customers="count", Responders="sum")
    out["Response Rate (%)"] = (100 * out["Responders"] / out["Customers"]).round(2)
    return out.reset_index()


SECTIONS = {
    "1. Gender vs Campaign Response": "Gender",
    "2. Age Group vs Campaign Response": "AgeGroup",
    "3. Purchase in Last Quarter vs Campaign Response": "Purchase_Last_Quarter",
    "4. Product Usage (unique products, last year) vs Campaign Response": "Product_Usage",
}

STYLE = """<style>
body{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#222}
table{border-collapse:collapse;width:100%;margin-bottom:2rem}
th,td{border:1px solid #ccc;padding:.5rem .75rem;text-align:right}
th:first-child,td:first-child{text-align:left}
th{background:#f0f0f0} h2{font-size:1.05rem;margin-top:2rem}
</style>"""


def tables() -> dict[str, pd.DataFrame]:
    df = load()
    return {title: response_rate(df, col) for title, col in SECTIONS.items()}


@app.get("/", response_class=HTMLResponse)
def home():
    return '<p>See <a href="/campaign-analysis">/campaign-analysis</a> (HTML tables) or <a href="/campaign-analysis/json">/campaign-analysis/json</a>.</p>'


@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis():
    body = "".join(f"<h2>{t}</h2>{d.to_html(index=False, border=0)}" for t, d in tables().items())
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Campaign Analysis</title>{STYLE}</head><body><h1>Skin Clinic Campaign Analysis</h1>{body}</body></html>"


@app.get("/campaign-analysis/json")
def campaign_analysis_json():
    return {t: d.astype({d.columns[0]: str}).to_dict(orient="records") for t, d in tables().items()}

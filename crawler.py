# file: crawler.py
import requests, pandas as pd, datetime as dt
from urllib.parse import quote

BASE = "https://pcc.mlwmlw.org/api"

UNITS = [
    "經濟部水利署第一河川分署",
    "宜蘭縣大同鄉公所",
    "農業部農村發展及水土保持署臺北分署",
    "宜蘭縣三星鄉公所",
    "宜蘭縣冬山鄉公所",
    "宜蘭縣員山鄉公所",
    "宜蘭縣羅東鎮公所",
    "宜蘭縣五結鄉公所",
    "宜蘭縣宜蘭市公所",
    "交通部公路局東區養護工程分局",
    "宜蘭縣政府",
    "國軍退除役官兵輔導委員會武陵農場",
]

def fetch_unit_month(unit: str, month: str | None = None) -> pd.DataFrame:
    """
    下載單一機關、單一月份的招標案件
    month 例：'2025-07'；None 表示抓最新月。
    """
    month = month or ""
    url = f"{BASE}/unit/{quote(unit)}/{month}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()             # pcc 回傳 list[dict]
    if not data:                # 沒資料直接回空表
        return pd.DataFrame()
    df = pd.json_normalize(data)
    df["機關"] = unit
    return df

# utils.py
import pandas as pd

# 欄位英→中對照
COLS_MAP = {
    "category":   "分類",
    "tender_no":  "標案案號",
    "name":       "標案名稱",
    "budget":     "預算金額",
    "date":       "初次招標日",
    "unit":       "主管機關",
    "url":        "招標網址",
    "award.date": "決標日",
    "award.type": "決標狀態",
    "award.url":  "決標網址",
}

SHOW_ORDER = list(COLS_MAP.values())     # 顯示順序

def tidy_for_display(df_raw: pd.DataFrame) -> pd.DataFrame:
    """取指定欄位 + 繁中名稱 + URL 變超連結"""
    # --- 1. 把 award.* flatten 成同層欄位 ---
    if "award" in df_raw.columns:
        # 轉成 DataFrame 再 join
        award_df = pd.json_normalize(df_raw["award"])
        award_df.columns = [f"award.{c}" for c in award_df.columns]
        df = pd.concat([df_raw.drop(columns="award"), award_df], axis=1)
    else:
        df = df_raw.copy()

    # --- 2. 換欄名 + 預防缺欄 ---
    df = df.rename(columns=COLS_MAP)
    df = df.reindex(columns=SHOW_ORDER)   # 缺欄位自動補 NaN

    # --- 3. 把網址欄位轉 <a> ---
    link_cols = ["招標網址", "決標網址"]
    for col in link_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("")
                .apply(lambda x: f'<a href="{x}" target="_blank">連結</a>' if x else "")
            )

    return df

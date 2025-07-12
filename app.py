import streamlit as st
import pandas as pd
from datetime import date
from crawler import UNITS, fetch_unit_month
from utils import tidy_for_display

st.set_page_config(page_title="標案即時整理", layout="wide")
st.title("📋 指定機關招標案件整理")

# ---------- Sidebar ----------
st.sidebar.header("查詢條件")

sel_units = st.sidebar.multiselect("選擇機關", UNITS, default=UNITS)
sel_date = st.sidebar.date_input("查詢月份 (選任一日即可)", value=date.today())
month_str = sel_date.replace(day=1).strftime("%Y-%m")

# ---------- 開始抓取 ----------
if st.sidebar.button("開始抓取"):
    dfs = [fetch_unit_month(u, month_str) for u in sel_units]
    time.sleep(4)
    df_all = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    if df_all.empty:
        st.warning(f"{month_str} 無資料")
    else:
        st.success(f"{month_str} 共取得 {len(df_all)} 筆標案")

        # ---------- 攤平 award 欄位 ----------
        if 'award' in df_all.columns:
            award_df = pd.json_normalize(df_all['award'])
            award_df.columns = [f"award.{col}" for col in award_df.columns]
            df_all = pd.concat([df_all.drop(columns=["award"]), award_df], axis=1)
                # 👉 只保留分類為「工程類」
        if "category" in df_all.columns:
            df_all = df_all[df_all["category"] == "工程類"]
            st.info(f"⚙️ 已過濾為『工程類』，剩下 {len(df_all)} 筆")

        # ---------- 指定欄位 ----------
        selected_columns = [
            "category", "id", "name", "price", "publish", "unit",
            "url", "end_date", "award.type", "award.url"
        ]
        existing_columns = [col for col in selected_columns if col in df_all.columns]

        if not existing_columns:
            st.error("❌ 找不到指定欄位，請確認資料格式是否正確")
        else:
            df_show = df_all[existing_columns].copy()

            # ---------- 中文欄名轉換 ----------
            rename_dict = {
                "category": "分類",
                "id": "標案案號",
                "name": "標案名稱",
                "price": "預算金額",
                "publish": "初次招標日",
                "unit": "主管機關",
                "url": "招標網址",
                "end_date": "決標日",
                "award.type": "決標狀態",
                "award.url": "決標網址"
            }
            df_show.rename(columns={col: rename_dict[col] for col in existing_columns if col in rename_dict}, inplace=True)

            # ---------- 超連結格式處理 ----------
            if "招標網址" in df_show.columns:
                df_show["招標網址"] = df_show["招標網址"].apply(lambda x: f'<a href="{x}" target="_blank">連結</a>' if pd.notna(x) else "")
            if "決標網址" in df_show.columns:
                df_show["決標網址"] = df_show["決標網址"].apply(lambda x: f'<a href="{x}" target="_blank">連結</a>' if pd.notna(x) else "")

            # ---------- 顯示表格 ----------
            st.write(df_show.to_html(index=False, escape=False), unsafe_allow_html=True)

            # ---------- CSV 下載（原始欄位）----------
            csv = df_all.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "📥 下載 CSV（原始欄位）",
                csv,
                file_name=f"tenders_{month_str}.csv",
                mime="text/csv",
            )

            # ---------- 關鍵字過濾 ----------
            keyword = st.text_input("🔍 即時關鍵字過濾（標案名稱）")
            if keyword:
                filtered = df_show[df_show["標案名稱"].str.contains(keyword, na=False)]
                st.write(filtered.to_html(index=False, escape=False), unsafe_allow_html=True)

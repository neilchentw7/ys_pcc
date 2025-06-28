# -*- coding: utf-8 -*-
"""
app.py
Streamlit 介面：呼叫 crawler.crawl_all() 取得資料並顯示
"""
import streamlit as st
from crawler import crawl_all, AGENCIES

st.set_page_config(page_title="政府電子採購網標案快查", layout="wide")
st.title("📝 政府電子採購網　八大機關最新標案")

st.write(
    f"本工具將依序爬取以下 **{len(AGENCIES)}** 個機關的第一頁標案：\n\n"
    + "、".join(AGENCIES)
    + "\n\n"
    "後端採用 Selenium (headless Chrome)，每個機關之間隨機休息 3–8 秒，"
    "以降低被官方反爬機制封鎖的風險。"
)

if st.button("🚀 開始抓取", type="primary"):
    with st.spinner("資料擷取中，請稍候…"):
        df = crawl_all()

    st.success(f"完成！共取得 {len(df)} 筆資料。")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("💾 下載 CSV", csv, file_name="pcc_tenders.csv", mime="text/csv")
else:
    st.info("點擊上方按鈕開始抓取。")

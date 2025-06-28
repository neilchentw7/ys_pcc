# -*- coding: utf-8 -*-
"""
crawler.py
以 Selenium 取得政府電子採購網八個指定機關的第一頁標案列表
"""
import random
import time
from typing import List

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# ------ 基本設定 -----------------------------------------------------------
URL = "https://web.pcc.gov.tw/prkms/tender/common/bulletion/indexBulletion"

AGENCIES = [
    "經濟部水利署第一河川分署",
    "農業部農村發展及水土保持署臺北分署",
    "交通部公路局東區養護工程分局",
    "宜蘭縣三星鄉公所",
    "宜蘭縣政府",
    "宜蘭縣大同鄉公所",
    "農田水利署宜蘭",
    "台灣中油股份有限公司探採事業部",
]
# ---------------------------------------------------------------------------


# ---------- Selenium 共用工具 ----------------------------------------------
def _launch_driver() -> webdriver.Chrome:
    """啟動無頭 Chrome 並設定常見 UA，降低被擋機率。"""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--log-level=3")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opts
    )
    driver.set_window_size(1366, 900)
    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {
            "userAgent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    return driver


def _click_query(driver: webdriver.Chrome) -> None:
    """
    嘗試多種方式點擊『查詢』；若皆失敗則直接呼叫網頁 JS。
    """
    wait = WebDriverWait(driver, 10)
    locators = [
        (By.ID, "queryBtn"),  # 舊版
        (By.ID, "doQuery"),   # 新版常見
        (By.XPATH, "//a[contains(text(),'查詢')][contains(@class,'btn')]"),
        (By.XPATH, "//button[contains(text(),'查詢')]"),
    ]
    for by, val in locators:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, val)))
            btn.click()
            return
        except TimeoutException:
            continue
        except NoSuchElementException:
            continue

    # 保底：直接執行內建 JS 函式
    driver.execute_script("if (typeof goQuery === 'function') goQuery();")
# ---------------------------------------------------------------------------


# --------------------- 主要爬取流程 -----------------------------------------
def fetch_first_page(agency: str, driver: webdriver.Chrome) -> pd.DataFrame:
    """
    進入首頁 → 輸入機關 → 點查詢 → 切入 iframe → 讀第一頁表格
    回傳 DataFrame；若逾時或無資料，仍回傳含「訊息」欄的 DF。
    """
    driver.get(URL)

    # 1. 輸入機關名稱
    inp = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "dep"))
    )
    inp.clear()
    inp.send_keys(agency)
    # 有些情況需要 blur 觸發建議清單 → ENTER 保險
    inp.send_keys(Keys.RETURN)

    # 2. 點『查詢』
    _click_query(driver)

    try:
        # 3. 等待 iframe 出現並切換
        WebDriverWait(driver, 20).until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.CSS_SELECTOR, "iframe#listIframe")
            )
        )
        # 4. 等待表格
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        # 5. 用 pandas 直接擷取 HTML 中的第一張表
        df = pd.read_html(driver.page_source, flavor="bs4")[0]
        df.insert(0, "查詢機關", agency)

    except TimeoutException:
        # 逾時或查無資料，回傳備註
        df = pd.DataFrame(
            {"查詢機關": [agency], "訊息": ["Timeout / 無資料"]}, index=[0]
        )

    finally:
        driver.switch_to.default_content()

    return df


def crawl_all() -> pd.DataFrame:
    """輪詢八個機關並整合結果。"""
    driver = _launch_driver()
    all_df: List[pd.DataFrame] = []

    try:
        for idx, agency in enumerate(AGENCIES, start=1):
            df = fetch_first_page(agency, driver)
            all_df.append(df)

            # 機關之間隨機休息 3 ~ 8 秒
            if idx < len(AGENCIES):
                time.sleep(random.uniform(3, 8))
    finally:
        driver.quit()

    return pd.concat(all_df, ignore_index=True)
# ---------------------------------------------------------------------------


# 測試（直接 python crawler.py 可以單機跑）
if __name__ == "__main__":
    out = crawl_all()
    out.to_csv("pcc_tenders.csv", index=False, encoding="utf-8-sig")
    print("已存檔 pcc_tenders.csv")

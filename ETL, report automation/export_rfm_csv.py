#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
📤 Экспорт RFM-сегментации из DuckDB в CSV для визуализации
Генерирует:
  - rfm_segment_summary.csv   (агрегация по сегментам)
  - rfm_customer_scatter.csv  (данные на уровне клиента)
"""
import os
import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Пути (берутся из .env или используются дефолтные)
DB_PATH = os.getenv("DB_PATH", "./retail_analytics.duckdb")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def export_rfm_data(db_path: str, reports_dir: str):
    """Экспорт RFM-данных в два CSV-файла"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"❌ База данных не найдена: {db_path}")

    con = duckdb.connect(db_path)

    # 🔹 1. Агрегированная сводка (для Pie/Bar/KPI)
    summary_query = """
    SELECT
        rfm_segment,
        COUNT(*) AS customer_count,
        ROUND(AVG(monetary), 2) AS avg_monetary,
        SUM(monetary) AS total_monetary,
        ROUND(AVG(frequency), 1) AS avg_frequency,
        ROUND(AVG(recency_days), 0) AS avg_recency_days
    FROM analytics.fct_customer_metrics
    GROUP BY rfm_segment
    ORDER BY total_monetary DESC
    """
    df_summary = con.execute(summary_query).df()

    # 🔹 2. Данные на уровне клиента (для Scatter/Bubble plots)
    customer_query = """
    SELECT
        customer_id,
        country,
        frequency,
        monetary,
        recency_days,
        rfm_segment
    FROM analytics.fct_customer_metrics
    ORDER BY monetary DESC
    """
    df_customers = con.execute(customer_query).df()
    con.close()

    # Создаём папку, если нет
    os.makedirs(reports_dir, exist_ok=True)

    # Пути к файлам
    summary_path = os.path.join(reports_dir, "rfm_segment_summary.csv")
    customers_path = os.path.join(reports_dir, "rfm_customer_scatter.csv")

    # 💾 Сохранение
    df_summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"✅ Сводка по сегментам сохранена: {summary_path}")
    print(df_summary.to_string(index=False))

    df_customers.to_csv(customers_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ Данные для scatter-графика сохранены: {customers_path}")
    print(f"   📊 Строк: {len(df_customers)}, Сегментов: {df_customers['rfm_segment'].nunique()}")

    return df_summary, df_customers


if __name__ == "__main__":
    try:
        export_rfm_data(DB_PATH, REPORTS_DIR)
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        raise
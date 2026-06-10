import os
import subprocess
import sys
from datetime import datetime
from prefect import flow, task
from dotenv import load_dotenv

load_dotenv()

# Абсолютные пути относительно этого файла
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(SCRIPT_DIR, "retail_analytics.duckdb"))
RAW_PATH = os.getenv("RAW_DATA_PATH", os.path.join(SCRIPT_DIR, "data", "online_retail.xlsx"))
REPORT_PATH = os.getenv("REPORT_OUTPUT_PATH", os.path.join(SCRIPT_DIR, "reports", "daily_metrics.csv"))
DBT_DIR = os.path.join(SCRIPT_DIR, "sales_dbt")

@task(log_prints=True, retries=1, retry_delay_seconds=5)
def run_extract_load():
    from extract_load import load_and_clean_retail_data, load_to_raw
    df = load_and_clean_retail_data(RAW_PATH)
    load_to_raw(df, DB_PATH)
    print(f"✅ Extracted & loaded {len(df)} rows")
    return {"rows": len(df)}

@task(log_prints=True)
def run_dbt_transform():
    result = subprocess.run(
        ["dbt", "run", "--target", "dev"],
        cwd=DBT_DIR,  # 🔑 КРИТИЧЕСКИ: запускаем dbt ВНУТРИ папки sales_dbt
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    if result.returncode != 0:
        print(f"❌ dbt run STDOUT:\n{result.stdout}")
        print(f"❌ dbt run STDERR:\n{result.stderr}")
        raise RuntimeError("dbt run failed. See logs above.")
    print("✅ dbt transform completed")
    return {"status": "success"}

@task(log_prints=True)
def run_dbt_test():
    result = subprocess.run(
        ["dbt", "test"],
        cwd=DBT_DIR,
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    if result.returncode != 0:
        print(f"❌ dbt test STDOUT:\n{result.stdout}")
        print(f"❌ dbt test STDERR:\n{result.stderr}")
        raise RuntimeError("dbt test failed. See logs above.")
    print("✅ dbt tests passed")
    return {"status": "passed"}

@task(log_prints=True)
def generate_report():
    import duckdb
    import pandas as pd
    
    con = duckdb.connect(DB_PATH)
    df = con.execute("""
    SELECT 
        order_date, 
        country, 
        ROUND(daily_revenue) AS daily_revenue,        
        ROUND(avg_order_value, 2) AS avg_order_value,
        unique_customers 
    FROM analytics.fct_daily_sales 
    ORDER BY order_date DESC
    LIMIT 300 -- для примера 
""").df()
    con.close()
    
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    df.to_csv(REPORT_PATH, index=False, encoding="utf-8-sig")
    print(f"📄 Report saved to {REPORT_PATH}")
    return {"path": REPORT_PATH}

@flow(name="online-retail-pipeline", log_prints=True)
def retail_pipeline():
    print(f"🚀 Pipeline started at {datetime.now().isoformat()}")
    print(f"📂 Working dir: {os.getcwd()} | DB: {DB_PATH}")
    
    extract = run_extract_load()
    transform = run_dbt_transform()
    test = run_dbt_test()
    report = generate_report()
    
    print(f"✅ Pipeline finished successfully")
    return {"extract": extract, "transform": transform, "test": test, "report": report}

if __name__ == "__main__":
    # Современный запуск с локальным агентом и шедулером
    retail_pipeline.serve(
        name="retail-daily-pipeline",
        cron="0 9 * * *",
        tags=["retail", "production", "portfolio"]
    )

 
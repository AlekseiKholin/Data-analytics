import pandas as pd
import duckdb
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./retail_analytics.duckdb")
RAW_PATH = os.getenv("RAW_DATA_PATH", "./data/online_retail.xlsx") 

def load_and_clean_retail_data(filepath: str) -> pd.DataFrame:
    """
    Загрузка и очистка Online Retail dataset (.xlsx)
    """
    # ✅ 1. Читаем Excel
    df = pd.read_excel(filepath, engine='openpyxl')
    
    # ✅ 2. Убираем возможные пробелы в названиях столбцов
    df.columns = df.columns.str.strip()
    
    # Проверка наличия ключевых столбцов
    required_cols = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"❌ Отсутствуют столбцы: {missing}. Доступные: {df.columns.tolist()}")

    # ✅ 3. Базовая очистка под специфику датасета
    df = df.copy()
    
    # Приводим InvoiceNo к строке для корректной фильтрации отмен ('C' в начале)
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    
    # Удаляем отменённые инвойсы
    df = df[~df['InvoiceNo'].str.startswith('C', na=False)].copy()
    
    # Удаляем строки с отрицательным количеством или ценой (возвраты/ошибки ввода)
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()
    
    # Рассчитываем Revenue
    df['Revenue'] = (df['Quantity'] * df['UnitPrice']).round(2)
    
    # Парсим даты
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['InvoiceDate']) # Убираем строки, где дата не распарсилась
    
    df['OrderDate'] = df['InvoiceDate'].dt.date
    df['OrderHour'] = df['InvoiceDate'].dt.hour
    
    # Помечаем гостевые заказы (без CustomerID)
    df['is_guest'] = df['CustomerID'].isna()
    
    print(f"✅ Загружено {len(df)} валидных строк из {filepath}")
    return df

def load_to_raw(df: pd.DataFrame, db_path: str):
    con = duckdb.connect(db_path)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("DROP TABLE IF EXISTS raw.online_retail_raw")
    con.execute("CREATE TABLE raw.online_retail_raw AS SELECT * FROM df")
    
    # Создаём pre-aggregated view для ускорения dbt
    con.execute("""
        CREATE OR REPLACE VIEW raw.orders_summary AS
        SELECT 
            InvoiceNo, CustomerID, Country,
            COUNT(DISTINCT StockCode) AS unique_items,
            SUM(Quantity) AS total_quantity,
            SUM(Revenue) AS total_revenue,
            MIN(InvoiceDate) AS order_timestamp
        FROM raw.online_retail_raw
        GROUP BY 1,2,3
    """)
    print(f"✅ Данные загружены в {db_path}")
    con.close()

if __name__ == "__main__":
    df = load_and_clean_retail_data(RAW_PATH)
    load_to_raw(df, DB_PATH)
{{ config(materialized='view') }}

SELECT
    InvoiceNo AS order_id,
    CustomerID AS customer_id,
    Country AS country,
    DATE_TRUNC('day', InvoiceDate) AS order_date,
    EXTRACT(MONTH FROM InvoiceDate) AS order_month,
    COUNT(DISTINCT StockCode) AS items_count,
    SUM(Quantity) AS total_quantity,
    SUM(Revenue) AS order_revenue,
    MIN(InvoiceDate) AS order_timestamp
FROM {{ source('raw', 'online_retail_raw') }}
GROUP BY 1,2,3,4,5
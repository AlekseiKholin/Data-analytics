
  
  create view "retail_analytics"."analytics"."stg_orders__dbt_tmp" as (
    

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
FROM "retail_analytics"."raw"."online_retail_raw"
GROUP BY 1,2,3,4,5
  );

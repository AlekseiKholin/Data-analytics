

SELECT
    order_date,
    country,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(order_revenue) AS daily_revenue,
    AVG(order_revenue) AS avg_order_value,
    SUM(total_quantity) AS units_sold,
    -- Метрика: % заказов от зарегистрированных клиентов
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN customer_id IS NOT NULL THEN order_id END) 
          / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS registered_customer_pct
FROM "retail_analytics"."analytics"."stg_orders"
GROUP BY 1, 2
ORDER BY 1
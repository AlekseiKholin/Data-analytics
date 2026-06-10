

WITH global_max_date AS (
    -- Вычисляем максимальную дату один раз
    SELECT MAX(order_date) AS max_date FROM "retail_analytics"."analytics"."stg_orders"
),

customer_stats AS (
    SELECT
        s.customer_id,
        s.country,
        COUNT(DISTINCT s.order_id) AS frequency,
        SUM(s.order_revenue) AS monetary,
        MAX(s.order_date) AS last_order_date,
        MIN(s.order_date) AS first_order_date,
        DATE_DIFF('day', MIN(s.order_date), MAX(s.order_date)) AS customer_lifetime_days,
        -- Recency считаем через CROSS JOIN, чтобы не было подзапроса в алиасе
        DATE_DIFF('day', MAX(s.order_date), g.max_date) AS recency_days
    FROM "retail_analytics"."analytics"."stg_orders" s
    CROSS JOIN global_max_date g
    WHERE s.customer_id IS NOT NULL
    GROUP BY 1, 2, g.max_date
)

SELECT
    customer_id,
    country,
    frequency,
    monetary,
    last_order_date,
    first_order_date,
    customer_lifetime_days,
    recency_days,
    CASE 
        WHEN frequency >= 10 AND monetary >= 500 THEN 'Champions'
        WHEN frequency >= 5 AND monetary >= 200 THEN 'Loyal'
        WHEN recency_days <= 30 THEN 'Recent'
        WHEN recency_days > 180 THEN 'At Risk'
        ELSE 'Regular'
    END AS rfm_segment
FROM customer_stats
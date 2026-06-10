



select
    1
from "retail_analytics"."analytics"."fct_daily_sales"

where not(daily_revenue >= 0)


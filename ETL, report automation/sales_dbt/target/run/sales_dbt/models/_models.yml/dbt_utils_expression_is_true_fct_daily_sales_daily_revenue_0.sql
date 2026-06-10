
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  



select
    1
from "retail_analytics"."analytics"."fct_daily_sales"

where not(daily_revenue >= 0)


  
  
      
    ) dbt_internal_test
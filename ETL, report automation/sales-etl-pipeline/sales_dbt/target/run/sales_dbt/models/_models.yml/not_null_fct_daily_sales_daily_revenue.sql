
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select daily_revenue
from "retail_analytics"."analytics"."fct_daily_sales"
where daily_revenue is null



  
  
      
    ) dbt_internal_test
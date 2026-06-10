
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select Revenue
from "retail_analytics"."raw"."online_retail_raw"
where Revenue is null



  
  
      
    ) dbt_internal_test
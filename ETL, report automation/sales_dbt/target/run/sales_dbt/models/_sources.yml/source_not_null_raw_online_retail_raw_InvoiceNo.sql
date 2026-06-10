
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select InvoiceNo
from "retail_analytics"."raw"."online_retail_raw"
where InvoiceNo is null



  
  
      
    ) dbt_internal_test

    
    

select
    customer_id as unique_field,
    count(*) as n_records

from "retail_analytics"."analytics"."fct_customer_metrics"
where customer_id is not null
group by customer_id
having count(*) > 1



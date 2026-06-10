
    
    

with all_values as (

    select
        rfm_segment as value_field,
        count(*) as n_records

    from "retail_analytics"."analytics"."fct_customer_metrics"
    group by rfm_segment

)

select *
from all_values
where value_field not in (
    'Champions','Loyal','Recent','At Risk','Regular'
)



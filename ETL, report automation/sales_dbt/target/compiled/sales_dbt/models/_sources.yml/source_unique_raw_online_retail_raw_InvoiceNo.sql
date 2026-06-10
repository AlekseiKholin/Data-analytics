
    
    

select
    InvoiceNo as unique_field,
    count(*) as n_records

from "retail_analytics"."raw"."online_retail_raw"
where InvoiceNo is not null
group by InvoiceNo
having count(*) > 1



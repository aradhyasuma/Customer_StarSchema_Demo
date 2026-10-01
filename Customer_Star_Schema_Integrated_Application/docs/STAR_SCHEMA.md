# Star Schema Design

```text
                 DimRegion
                     |
DimCustomer — FactCustomerSpending — DimChannel
                     |
               DimMembership
                     |
                  DimDate
```

**Fact:** `fact_customer_spending`  
**Grain:** one spending snapshot for each customer per refresh date.  
**Measures:** `spending_score`, `annual_spend`.  
**Degenerate/classification descriptor:** `spending_behavior`.  
**Dimensions:** customer demographics/tenure, region, channel, membership, date.

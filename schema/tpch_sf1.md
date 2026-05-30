# TPCH_SF1 Schema (Snowflake sample data)

Database: `SNOWFLAKE_SAMPLE_DATA`  
Schema: `TPCH_SF1`

## CUSTOMER

- C_CUSTKEY: customer ID (integer)
- C_NAME: customer name (text)
- C_ADDRESS: customer address (text)
- C_NATIONKEY: nation ID (integer)
- C_PHONE: phone number (text)
- C_ACCTBAL: account balance (number)
- C_MKTSEGMENT: market segment like BUILDING, AUTOMOBILE, etc. (text)

## ORDERS

- O_ORDERKEY: order ID (integer)
- O_CUSTKEY: customer ID who placed order (integer)
- O_ORDERSTATUS: status like F (fulfilled), O (open), P (pending) (text)
- O_TOTALPRICE: total order amount in dollars (number)
- O_ORDERDATE: order date (date)
- O_ORDERPRIORITY: priority like 1-URGENT, 3-MEDIUM, etc. (text)

## NATION

- N_NATIONKEY: nation ID (integer)
- N_NAME: nation name like UNITED STATES, CANADA, etc. (text)
- N_REGIONKEY: region ID (integer)

## Query rules

- Use Snowflake SQL syntax
- Use fully qualified table names: `TPCH_SF1.CUSTOMER`, `TPCH_SF1.ORDERS`, etc.
- SELECT only in the sandbox POC

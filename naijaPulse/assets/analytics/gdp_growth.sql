/* @bruin

name: analytics.gdp_growth
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - stg.economics

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

@bruin */

SELECT
    country_code, country_name, year,
    gdp_growth, inflation, fdi_pct_gdp,
    unemployment, electricity_access,
    ROUND(AVG(gdp_growth) OVER (
        PARTITION BY country_code
        ORDER BY year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 3) AS gdp_3yr_avg,
    RANK() OVER (PARTITION BY year ORDER BY gdp_growth DESC) AS growth_rank
FROM stg.economics
WHERE gdp_growth IS NOT NULL
ORDER BY country_code, year

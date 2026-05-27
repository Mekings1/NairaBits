/* @bruin

name: analytics.africa_overview
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - stg.economics
  - stg.energy

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

@bruin */

SELECT
    e.country, e.year,
    e.renewables_pct, e.fossil_pct,
    e.energy_per_capita_kwh, e.energy_profile,
    m.gdp_growth, m.inflation,
    m.fdi_pct_gdp, m.electricity_access
FROM stg.energy e
LEFT JOIN stg.economics m
    ON m.country_name = e.country AND m.year = e.year
ORDER BY e.country, e.year

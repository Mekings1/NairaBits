/* @bruin

name: analytics.nigeria_focus
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - stg.currencies
  - stg.economics
  - stg.energy

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

@bruin */

WITH fx AS (
    SELECT
        YEAR(date) AS year,
        ROUND(AVG(rate), 2) AS avg_usd_ngn
    FROM stg.currencies
    WHERE target_currency = 'NGN'
    GROUP BY 1
)
SELECT
    m.year, m.country_name,
    m.gdp_growth, m.inflation,
    m.electricity_access, m.unemployment,
    f.avg_usd_ngn,
    e.renewables_pct, e.fossil_pct, e.energy_profile
FROM stg.economics m
LEFT JOIN fx        f ON f.year = m.year
LEFT JOIN stg.energy e ON e.country = 'Nigeria' AND e.year = m.year
WHERE m.country_code = 'NGA'
ORDER BY m.year

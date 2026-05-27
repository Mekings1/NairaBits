/* @bruin

name: stg.economics
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - raw.wb_indicators

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

columns:
  - name: country_code
    type: VARCHAR
    checks:
      - name: not_null
  - name: year
    type: BIGINT
    checks:
      - name: not_null
  - name: country_name
    type: VARCHAR
  - name: electricity_access
    type: DOUBLE
  - name: fdi_pct_gdp
    type: DOUBLE
  - name: gdp_growth
    type: DOUBLE
  - name: inflation
    type: DOUBLE
  - name: unemployment
    type: DOUBLE

@bruin */

SELECT
    country_code,
    country_name,
    year,
    MAX(CASE WHEN indicator_name = 'gdp_growth'        THEN ROUND(value, 4) END) AS gdp_growth,
    MAX(CASE WHEN indicator_name = 'inflation'         THEN ROUND(value, 4) END) AS inflation,
    MAX(CASE WHEN indicator_name = 'fdi_pct_gdp'       THEN ROUND(value, 4) END) AS fdi_pct_gdp,
    MAX(CASE WHEN indicator_name = 'electricity_access' THEN ROUND(value, 4) END) AS electricity_access,
    MAX(CASE WHEN indicator_name = 'unemployment'      THEN ROUND(value, 4) END) AS unemployment
FROM raw.wb_indicators
GROUP BY country_code, country_name, year
ORDER BY country_code, year

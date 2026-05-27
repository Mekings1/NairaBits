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

PIVOT (
    SELECT country_code, country_name, year,
        indicator_name, ROUND(value, 4) AS value
    FROM raw.wb_indicators
)
ON indicator_name
USING FIRST(value)
ORDER BY country_code, year

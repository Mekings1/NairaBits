/* @bruin

name: stg.currencies
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - raw.exchange_rates

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

columns:
  - name: date
    type: DATE
    checks:
      - name: not_null
  - name: rate
    type: DOUBLE
    checks:
      - name: not_null
      - name: positive
  - name: base_currency
    type: VARCHAR
  - name: target_currency
    type: VARCHAR
  - name: daily_change_pct
    type: DOUBLE
  - name: rolling_30d_volatility
    type: DOUBLE

@bruin */

SELECT
    CAST(date AS DATE) AS date,
    base_currency,
    target_currency,
    CASE 
        WHEN rate > 100 AND target_currency = 'GHS' THEN rate / 100.0 
        ELSE rate 
    END AS rate,
    ROUND(
        ((rate - LAG(rate) OVER (PARTITION BY target_currency ORDER BY date))
        / NULLIF(LAG(rate) OVER (PARTITION BY target_currency ORDER BY date), 0)) * 100,
    4) AS daily_change_pct,
    STDDEV(rate) OVER (
        PARTITION BY target_currency
        ORDER BY date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30d_volatility
FROM raw.exchange_rates
ORDER BY date, target_currency

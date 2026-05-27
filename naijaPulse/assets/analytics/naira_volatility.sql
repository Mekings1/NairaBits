/* @bruin

name: analytics.naira_volatility
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - stg.currencies

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

@bruin */

SELECT
    DATE_TRUNC('month', date) AS month,
    target_currency AS currency,
    ROUND(AVG(rate), 4)       AS avg_rate,
    ROUND(MAX(rate), 4)       AS high,
    ROUND(MIN(rate), 4)       AS low,
    ROUND(STDDEV(rate), 6)    AS volatility,
    ROUND(((LAST(rate ORDER BY date) - FIRST(rate ORDER BY date))
        / NULLIF(FIRST(rate ORDER BY date), 0)) * 100, 2) AS monthly_return_pct,
    ROUND((MAX(rate) - MIN(rate))
        / NULLIF(AVG(rate), 0) * 100, 2) AS monthly_range_pct
FROM stg.currencies
WHERE target_currency IN ('NGN', 'KES', 'ZAR', 'GHS')
GROUP BY 1, 2
ORDER BY currency, month

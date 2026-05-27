/* @bruin

name: stg.energy
type: duckdb.sql
connection: duckdb-default

materialization:
  type: table

depends:
  - raw.energy_data

secrets:
  - key: duckdb-default
    inject_as: duckdb-default

columns:
  - name: country
    type: VARCHAR
  - name: year
    type: BIGINT
  - name: renewables_pct
    type: DOUBLE
  - name: fossil_pct
    type: DOUBLE
  - name: energy_per_capita_kwh
    type: DOUBLE
  - name: carbon_intensity
    type: DOUBLE
  - name: energy_profile
    type: VARCHAR

@bruin */

SELECT
    country, year,
    ROUND(renewables_share_energy, 2) AS renewables_pct,
    ROUND(fossil_share_energy, 2)     AS fossil_pct,
    ROUND(energy_per_capita, 2)       AS energy_per_capita_kwh,
    ROUND(carbon_intensity_elec, 2)   AS carbon_intensity,
    CASE
        WHEN renewables_share_energy >= 50 THEN 'Green leader'
        WHEN renewables_share_energy >= 25 THEN 'Transitioning'
        ELSE 'Fossil dependent'
    END AS energy_profile
FROM raw.energy_data
WHERE year >= 2010
ORDER BY country, year

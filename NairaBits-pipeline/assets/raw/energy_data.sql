/* @bruin
name: raw.energy_data
type: duckdb.sql
connection: duckdb-default
materialization:
    type: table
description: |
    Reads Our World in Data's open energy dataset directly from GitHub
    via DuckDB's read_csv. Captures renewable share, fossil fuel share,
    energy per capita, and carbon intensity for ten African nations
    from 2000 onward.
tags:
    - energy
    - climate
    - africa
    - raw
    - owid
@bruin */

SELECT country, year,
    renewables_share_energy,
    fossil_share_energy,
    energy_per_capita,
    carbon_intensity_elec,
    electricity_demand
FROM read_csv(
    'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv',
    delim=',',
    quote='"',
    header=true,
    ignore_errors=true
)
WHERE country IN (
    'Nigeria','Kenya','South Africa','Ghana',
    'Ethiopia','Tanzania','Egypt','Rwanda','Senegal','Uganda'
)
AND year >= 2000

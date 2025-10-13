# FastAPI app serving data on retail sites from a PostgreSQL/PostGIS database

This repository contains a FastAPI application that serves data on retail sites from a PostgreSQL/PostGIS database. The application provides endpoints to retrieve information about retail locations, including their geographical data, address, name, brand, services offered.

## Data

The data is stored in a PostgreSQL database with PostGIS extension enabled. 

The database contains a current snapshot of data aggregated from multiple sources including company websites, OpenStreetMaps, government data, and other public datasets. The data is updated periodically to ensure accuracy. Data is transformed in a data warehouse before being loaded into the PostgreSQL database.

## Features

- Retrieve the closest retail sites based on latitude and longitude. Options to filter by distance brand and services.
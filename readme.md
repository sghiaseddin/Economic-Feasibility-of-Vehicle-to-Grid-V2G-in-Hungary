This repository contains the research code and exploratory analysis for a university project investigating the economic feasibility of Vehicle-to-Grid (V2G) systems in Hungary.

The goal of the project is to evaluate whether electric vehicle batteries can economically support grid operations by providing distributed energy storage and participating in electricity markets.

* The analysis is currently work in progress. This repository represents an initial public version of the project and will evolve as the economic modeling and simulations are refined.

## Version 0.0.2

# Project Motivation

Hungary is experiencing rapidly increasing renewable electricity production, particularly from solar PV. This has created structural imbalances in the electricity system:
- Midday oversupply and low/negative electricity prices
- Evening peak demand and higher marginal generation costs
- Rising grid balancing costs

Vehicle-to-Grid (V2G) technology could potentially help address these issues by allowing electric vehicles to act as distributed energy storage resources.

This project attempts to perform a data-driven microeconomic assessment of V2G feasibility in Hungary.  ￼

# Research Objectives

The project evaluates V2G from the perspective of grid operators and the electricity system, focusing on microeconomic impacts.

Key research questions include:
- What is the potential arbitrage revenue per EV?
- What grid-level economic value could V2G generate?
- How much peak load reduction could V2G provide?
- What is the payback period for grid-side investments?
- What would be the Net Present Value (NPV) of a V2G program?

The analysis also explores sensitivity scenarios, including incentive packages for EV owners.  ￼

# Project Status

* Work in progress

Current repository version includes:
- Data ingestion and preprocessing
- Initial exploratory analysis
- Early-stage economic modeling
- Visualization and investigation of electricity market behavior

The current outputs may not yet fully align with the final objectives defined in the project charter, as the modeling and simulation components are still under development.

Future updates will include:
- refined economic simulations
- scenario analysis
- final economic evaluation

# Repository Structure

#todo

The main analytical workflow is currently implemented in a Jupyter notebook.

# Data Sources

The analysis uses a combination of electricity market and energy system datasets including:

## Electricity Market Data: Hungarian wholesale electricity prices

Source: https://ember-energy.org/data/european-wholesale-electricity-price-data/

This dataset provides time-series electricity prices.

## Electric Vehicle Statistics

### EV fleet size in Hungary

Source: https://alternative-fuels-observatory.ec.europa.eu/transport-mode/road/hungary

This dataset provides statistics on the number of electric vehicles registered in Hungary, including:
- Battery Electric Vehicles (BEV)
- Plug-in Hybrid Electric Vehicles (PHEV)
- other alternative fuel vehicles

The data is used to estimate the potential size of the V2G-capable fleet.  ￼

### Top selling electric vehicles in Hungary

Source: https://alternative-fuels-observatory.ec.europa.eu/transport-mode/road/hungary

This dataset contains information about the most common EV models in Hungary.

### Usable battery capacity of electric vehicles

Source: https://ev-database.org/cheatsheet/useable-battery-capacity-electric-car

This dataset provides the usable battery capacity of EV models.  ￼

## V2G Infrastructure Cost Data

Source: https://doi.org/10.1016/j.apenergy.2024.123679 (Table 3)

This dataset provides estimated infrastructure costs related to V2G charging stations, including equipment and hardware components.

# Methodology Overview

The analysis follows several steps:

1. Data Processing
- Data ingestion
- Cleaning and normalization
- Time-series alignment

2. Exploratory Data Analysis
- Electricity price dynamics

3. V2G Simulation
- Modeling EV battery availability
- Simulating charge/discharge strategies
- Estimating arbitrage potential

4. Economic Evaluation
- Revenue estimation
- Cost assumptions
- Net present value analysis
- Payback period estimation

# Tools and Technologies

The project is implemented using:
- Python
- Jupyter Notebook
- Pandas
- NumPy
- Matplotlib / visualization libraries

All analysis is performed using reproducible computational workflows.

# Limitations

This project focuses exclusively on microeconomic feasibility and therefore does not cover:
- Technical feasibility of V2G hardware
- Regulatory or legislative analysis
- Battery degradation engineering studies
- Detailed infrastructure installation costs
- Consumer behavior analysis

# Team

Project team:
- Shayan Ghiaseddin: MSc Business Informatics – Corvinus University of Budapest
- Sofia Nikolaeva: MSc Business Informatics – Corvinus University of Budapest
- Nurzada Nasirova: MSc Business Informatics – Corvinus University of Budapest

This is group project for **Data Science project in Business** course by Tibor Kovács, at Corvinus University of Budapest, Spring 2026

# Disclaimer

This repository contains academic research in progress.
Results, assumptions, and models are subject to revision as the project develops.

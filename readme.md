This repository contains the research code and exploratory analysis for a university project investigating the economic feasibility of Vehicle-to-Grid (V2G) systems in Hungary.

The goal of the project is to evaluate whether electric vehicle batteries can economically support grid operations by providing distributed energy storage and participating in electricity markets.

This repository represents the final analytical version of the project including data processing, time-series modeling, economic simulation, and Net Present Value evaluation.


## Version 2.0.3


# Project Motivation

Hungary is experiencing rapidly increasing renewable electricity production, particularly from solar PV. This has created structural imbalances in the electricity system:

- Midday oversupply and low / negative electricity prices  
- Evening peak demand and higher marginal generation costs  
- Increasing need for grid balancing services  

Vehicle-to-Grid (V2G) technology could potentially help address these issues by allowing electric vehicles to act as distributed energy storage resources.

This project performs a data-driven microeconomic assessment of V2G feasibility in Hungary.


# Research Objectives

The project evaluates V2G from the perspective of the electricity system and grid economics.

Key research questions:

- What is the potential arbitrage revenue per EV?
- What grid-level economic value could V2G generate?
- How many EVs could realistically participate in V2G?
- What are the infrastructure costs of V2G deployment?
- What is the Net Present Value (NPV) of a 10-year V2G program?
- What level of incentive is required for EV owners to participate?


# Project Status

Completed analytical version.

Current repository includes:

- Data ingestion and preprocessing
- Exploratory time-series analysis
- Electricity price forecasting to 2030
- EV fleet projection to 2030
- V2G economic simulation (2021-2030)
- Infrastructure cost modeling
- Incentive calculation
- Net Present Value (NPV) analysis
- Output export (CSV + PNG)


# Repository Structure
```
project/
├─ app
├─ data
│       Raw input datasets
├─ output
│       Generated tables and figures (CSV / PNG)
├── notebook
│   ├── analysis.html
│   └── analysis.ipynb
└── readme.md
```

The entire workflow is implemented in `analysis.ipynb`.

Running the notebook will:

- load datasets
- run the model
- generate graphs
- save outputs to `/output`


# Data Sources


## Electricity Market Data

Hungarian wholesale electricity prices

Source  
https://ember-energy.org/data/european-wholesale-electricity-price-data/

Used for:

- price dynamics analysis
- daily spread calculation
- time-series forecasting


## Electric Vehicle Statistics

Source  
https://alternative-fuels-observatory.ec.europa.eu/transport-mode/road/hungary

Used for:

- EV fleet size
- BEV + PHEV counts
- fleet projection


## Top selling EV models

Source  
https://alternative-fuels-observatory.ec.europa.eu/transport-mode/road/hungary

Used to estimate:

- average battery capacity


## Battery capacity dataset

Source  
https://ev-database.org/cheatsheet/useable-battery-capacity-electric-car

Used for:

- usable battery size
- safe discharge limits


## V2G infrastructure cost data

Source  
https://doi.org/10.1016/j.apenergy.2024.123679 (Table 3)

Used for:

- station conversion cost
- amortized investment cost
- yearly cost interpolation


# Methodology Overview


## 1. Data Processing

- cleaning datasets
- time alignment
- interpolation
- normalization


## 2. Exploratory Data Analysis

- hourly price patterns
- weekday vs weekend
- seasonal patterns
- daily price spreads


## 3. Forecasting

Electricity price forecast to 2030 using:

- PyTimeTK
- Random Forest regression
- seasonal features


EV fleet projection using:

- logistic growth model
- upper saturation cap


Infrastructure cost projection using:

- linear interpolation


## 4. V2G Simulation Model

For each year 2021-2030:

- EV participation assumptions
- charging / discharging windows
- safe battery limits
- price-based dispatch
- station cost accumulation
- yearly profit calculation


## 5. Incentive Model

Profit is redistributed to EV owners as price surplus:
```
Surplus = Annual profit / (Eligible EV × Battery Usable Energy × total discharge hours)
```

This represents a market-based incentive.


## 6. Economic Evaluation

- annual income
- annual cost
- annual profit
- discounted profit
- Net Present Value (NPV)


# Tools and Technologies

- Python
- Jupyter Notebook
- Pandas
- NumPy
- Matplotlib
- PyTimeTK
- scikit-learn


All figures are saved automatically.


# Limitations

This project focuses on microeconomic feasibility only.

Not included:

- hardware engineering analysis
- grid stability simulation
- regulatory analysis
- battery degradation modeling
- consumer psychology


# Team

Project team:

- Shayan Ghiaseddin  
- Sofia Nikolaeva  
- Nurzada Nasirova  

MSc Business Informatics  
Corvinus University of Budapest

Course:

Data Science Project in Business, by Associate Professor Tibor Kovács
Spring 2026


# Disclaimer

- This repository contains academic research.
- Results depend on assumptions and scenario parameters.
- The model is intended for educational and analytical purposes.
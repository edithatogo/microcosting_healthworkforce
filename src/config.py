# src/config.py
"""
Central configuration file for the microcosting application.

This file consolidates all hardcoded paths, constants, and mappings
to make the application more maintainable and easier to configure.
"""

# --- File Paths and Names ---
DATA_FILE_PATH = "data/Labour Model - v3, 20240328.xlsx"
LABOUR_PRICES_SHEET = "Labour - Prices"
DSA_VALIDATION_SHEET = "Labour - Prices (DSA, Values)"
FORMULAS_FILE_PATH = "data/formulas.json"
DSA_SCENARIOS_FILE_PATH = "data/dsa_scenarios.json"
PSA_SCENARIOS_FILE_PATH = "data/psa_scenarios.json"


# --- Model Parameters ---
PROJECTION_YEARS = 5


# --- DSA Scenario to Validation Column Mapping ---
# Maps the name of a DSA scenario to the corresponding column name in the
# 'Labour - Prices (DSA, Values)' validation sheet.
DSA_SCENARIO_VALIDATION_MAPPING = {
    "Super Rate +10%": "Superannuation Rate_Base Salary + Costs_MP",
    "Super Rate -10%": "Superannuation Rate_Base Salary + Costs_MP",
    "Productive Time +5%": "Hours worked per week_Base Salary + Costs_MP",
    "Productive Time -5%": "Hours worked per week_Base Salary + Costs_MP",
    "Average Penalties +10%": "Average Penalties_Base Salary + Costs_MP",
    "Average Penalties -10%": "Average Penalties_Base Salary + Costs_MP",
    "Public Holiday Penalty +10%": "Public Holiday Penalty_Base Salary + Costs_MP",
    "Public Holiday Penalty -10%": "Public Holiday Penalty_Base Salary + Costs_MP",
    "Private Practice Loading +10%": "Private Practice Loading_Base Salary + Costs_MP",
    "Private Practice Loading -10%": "Private Practice Loading_Base Salary + Costs_MP",
    "Retention Allowance +10%": (
        "Attraction and Retention Allowance_Base Salary + Costs_MP"
    ),
    "Retention Allowance -10%": (
        "Attraction and Retention Allowance_Base Salary + Costs_MP"
    ),
    "Sick Leave +10%": "Sick Leave_Base Salary + Costs_MP",
    "Sick Leave -10%": "Sick Leave_Base Salary + Costs_MP",
    "Prof. Dev. Allowance +$500": (
        "Professional Development Allowance_Base Salary + Costs_MP"
    ),
    "Prof. Dev. Allowance -$500": (
        "Professional Development Allowance_Base Salary + Costs_MP"
    ),
    "Annual Leave +1 Week": "Annual Leave_Base Salary + Costs_MP",
    "Annual Leave -1 Week": "Annual Leave_Base Salary + Costs_MP",
    "Annual Leave Loading +10%": "Leave Loading (%)_Base Salary + Costs_MP",
    "Annual Leave Loading -10%": "Leave Loading (%)_Base Salary + Costs_MP",
}

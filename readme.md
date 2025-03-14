# AliveWatch

AliveWatch is a service that monitors the status of British and 
US celebrities and public figures who are no longer prominent. Alivewatch 
members must be at least 85 years old, and be famous to an extent, but not
too famous.

## Overview

The system:
- Tracks individuals based on notability rankings and age criteria
- Updates statuses daily through GitHub Actions
- Retains past copies of the Alivewatch list
- Provides a web page to view the data

## Data Categories

The system maintains several data files:
- A comprehensive list of celebrities and their current status (Alivewatch.csv.gz)
- Current individuals being monitored (`data/On_Alivewatch.csv`)
- Those who passed while being monitored (`data/Died_under_watch.csv`)
- Cases missed by the system (`data/Missed_by_alivewatch.csv`)
- Historical tracking by date added (`data/Alivewatch_by_date_added.csv`)

## Source Data

Alivewatch uses the dataset created for Laouenan M, Bhargava P, Eyméoud JB, Gergaud O, 
Plique G, Wasmer E. A cross-verified database of notable people, 3500BC-2018AD. Sci Data. 2022 Jun 9;9:290. 
doi: 10.1038/s41597-022-01369-4. PMCID: PMC9184645.

This is not updated, so Alivewatch will become gradually obsolete over a timeframe of years.
In particular, old people who become famous in old age will be missed by Alivewatch. But in general,
assuming that old famous people became famous when young, it will be good for a long time.

'Notability' is based on the 'ranking_visib_5criteria' feature.

## Parameters

The system filters individuals using the following criteria:
- Maximum birth year: current year minus 85
- Notability ('ranking_visib_5criteria) rank range: 1,000 - 100,000
  - Lower bound prevents tracking extremely famous individuals
  - Upper bound excludes less notable persons
The prioritisation in the list is then calculated as a function of both
age and notability.

## Technical Details

- **Backend**: Python script (`AliveWatch.py`) with pandas for data processing
- **Frontend**: HTML/CSS for data visualization
- **Automation**: Daily updates via GitHub Actions
- **Data Storage**: Compressed CSV format (Alivewatch.csv.gz)

## Web Interface

- index.html: Displays current AliveWatch members
- died.html: Shows individuals who have passed

## To do

- Show Alivewatch priority at time of death on the 'passed' list
- Show change in priority (e.g. over the last month) on the Alivewatch list


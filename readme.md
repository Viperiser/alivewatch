# AliveWatch

AliveWatch is an automated system that tracks and monitors notable individuals over the age of 85, maintaining a public record of their status and documenting when changes occur.

![AliveWatch Logo](images/20250222-Alivewatch Logo.png)

## Overview

The system automatically:
- Tracks individuals based on notability rankings and age criteria
- Updates statuses daily through GitHub Actions
- Maintains records of both current and historical data
- Provides a web interface to view the data

## Data Categories

The system maintains several data files:
- Current individuals being monitored (`data/On_Alivewatch.csv`)
- Those who passed while being monitored (`data/Died_under_watch.csv`)
- Cases missed by the system (`data/Missed_by_alivewatch.csv`)
- Historical tracking by date added (`data/Alivewatch_by_date_added.csv`)

## Parameters

The system uses the following criteria:
- Minimum age: 85 years
- Notability rank range: 1,000 - 100,000
  - Lower bound prevents tracking extremely famous individuals
  - Upper bound excludes less notable persons

## Technical Details

- **Backend**: Python script (`AliveWatch.py`) with pandas for data processing
- **Frontend**: HTML/CSS interface for data visualization
- **Automation**: Daily updates via GitHub Actions
- **Data Storage**: Compressed CSV format (Alivewatch.csv.gz)

## Setup

1. Install dependencies:
```sh
pip install -r requirements.txt
```

2. Run the update script:
```sh
python AliveWatch.py
```

## Web Interface

- index.html: Displays current AliveWatch members
- died.html: Shows individuals who have passed
- Updates automatically based on the CSV data files


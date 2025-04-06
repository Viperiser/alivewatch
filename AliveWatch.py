# Project: Alivewatch
# File Created: 2023-10-01

# Import libraries
import datetime
import re
import os
import requests
import pandas as pd


def clean_name(name):
    """
    Cleans up the name of a person by removing underscores, leading/trailing quotes, and multiple spaces.

    Parameters:
    name (str): The name of the person to be cleaned.

    Returns:
    str: The cleaned name.
    """
    # Remove underscores and replace with spaces
    name = name.replace("_", " ")
    # Remove leading/trailing quotes
    name = name.strip('"')
    # Remove multiple spaces (if underscores were next to each other)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# Date of death is property P570
def deathdate(id):
    """
    Returns the date of death for a given Wikidata ID.

    Parameters:
    id (str): The Wikidata ID of the person.

    Returns:
    str: The date of death in the format YYYY-MM-DD, or an empty string if no date is found.
    """
    # Get the date of death from Wikidata
    uri = (
        "https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&ids="
        + id
        + "&format=json"
    )
    r = requests.get(uri).json()
    datetime = ""
    if "P570" in r["entities"][id]["claims"]:
        datetime = r["entities"][id]["claims"]["P570"][0]["mainsnak"]["datavalue"][
            "value"
        ]["time"]
    # extract date from datetime
    if datetime != "":
        datetime = datetime[1:11]
    # note this is already in format YYYY-MM-DD
    return datetime


def todays_date():
    """
    Returns today's date in the format YYYY-MM-DD.

    Parameters:
    None

    Returns:
    str: Today's date in the format YYYY-MM-DD.
    """
    # Returns today's date in format YYYY-MM-DD
    now = datetime.datetime.now()
    year = str(now.year)
    month = str(now.month)
    if len(month) == 1:
        month = "0" + month
    day = str(now.day)
    if len(day) == 1:
        day = "0" + day
    return year + "-" + month + "-" + day


def compare_dates(date1, date2):
    """
    Compares two dates in the format YYYY-MM-DD. Returns True if date1 is later than date2.

    Parameters:
    date1 (str): The first date to compare.
    date2 (str): The second date to compare.

    Returns:
    bool: True if date1 is later than date2, False otherwise. If date1 is blank, returns False. If date2 is blank, returns True.

    """
    if date1 == "":
        return False
    elif date2 == "":
        return True
    else:
        year1 = int(date1[0:4])
        year2 = int(date2[0:4])
        if year1 > year2:
            return True
        elif year1 < year2:
            return False
        else:
            month1 = int(date1[5:7])
            month2 = int(date2[5:7])
            if month1 > month2:
                return True
            elif month1 < month2:
                return False
            else:
                day1 = int(date1[8:10])
                day2 = int(date2[8:10])
                if day1 > day2:
                    return True
                else:
                    return False

def find_death_position(data, id):
    """
    Finds the position in Alivewatch at the time of death, for a given Wikidata ID.
    Returns the position as a string or 'n/k' if not found.
    
    Parameters:
    data (DataFrame): The DataFrame containing Alivewatch data.
    id (str): The Wikidata ID of the person.
    
    Returns:
    str: The position at the time of death or 'n/k' if not found.
    """
    # Get the death date for the given ID
    death_date = data[data["wikidata_code"] == id]['deathstamp'].values[0]
    addeddate = data[data["wikidata_code"] == id]['date_added_to_alivewatch'].values[0]
    
    # If no death date is found, return empty string - they haven't died yet
    if death_date == " ":
        return ""
    
    # If date of death is before 2024-01-03, return 'n/k' - this is when the ranking system was introduced
    if compare_dates("2024-01-03", death_date):
        return "n/k"
    
    # Find name corresponding to the ID in Alivewatch
    name = data[data["wikidata_code"] == id]['name'].values[0]
    namecolumn = 'name'
    addedcolumn = 'date_added_to_alivewatch' 
    
    # If date of death is before 2025-02-22, use raw name, otherwise use cleaned name
    if compare_dates(death_date, "2025-02-21"):
        name = clean_name(name)
        namecolumn = 'Name'
        addedcolumn = 'Date Added to Alivewatch'
    
    # Look for the latest file of the form 'YYYY-MM-DD-On_Alivewatch.csv' before the death date
    files = os.listdir("old_data")
    files = [f for f in files if re.match(r"\d{4}-\d{2}-\d{2}-On_Alivewatch\.csv", f)]
    files = sorted(files, reverse=True)  # Sort files in reverse order
    # Remove files that are on or after the death date
    files = [f for f in files if compare_dates(death_date, f[:10])]
    # If no files are found, return 'n/k'
    if not files:
        return "n/k"
    # Read the latest file
    latest_file = files[0]
    df = pd.read_csv(os.path.join("old_data", latest_file))
    
    # If the date of the latest file is before 2024-01-05, convert the date format from a string YYYY-MM-DD to a string DD/MM/YYYY - this is when I changed the date format
    if compare_dates("2024-01-05", latest_file[:10]):
        day = latest_file[8:10]
        month = latest_file[5:7]
        year = latest_file[0:4]
        addeddate = f'{day}/{month}/{year}'
    
    # Check if the name is in the latest file
    if name in df[namecolumn].values:
        # Get the position of the name in the latest file - also use date added for disambiguation
        position = df[(df[namecolumn] == name) & (df[addedcolumn] == addeddate)].index[0] + 1
        return str(position)
    else: # Name not found
        return "n/k"

# Update Alivewatch
def update(maxyear, minrank, maxrank):
    """
    Updates Alivewatch.csv with the latest death dates from Wikipedia.
    Also updates the last updated date in last_updated.txt.

    Parameters:
    maxyear (int): The maximum year of birth for people to be included in Alivewatch.
    minrank (int): The minimum notability rank for people to be included in Alivewatch.
    maxrank (int): The maximum notability rank for people to be included in Alivewatch.

    Returns:
    None
    """

    data = pd.read_csv("Alivewatch.csv.gz", na_filter = False, compression="gzip", encoding="utf-8")
    newdata = data.copy()
    num = len(data)
    deathstampnew = data["deathstamp"].copy()  # Use existing date unless updated below
    alivewatchnew = data[
        "alivewatch?"
    ].copy()  # Use existing value unless updated below
    dateaddednew = data[
        "date_added_to_alivewatch"
    ].copy()  # Use existing date unless updated below
    deathpositionnew = data["position_at_death"].copy()  # Use existing value unless updated below
    
    for i in range(num):
        # check if died
        if (
            data["deathstamp"][i] != " "
        ):  # They are already recorded as dead
            fate = "Already dead"
            # Find the day of the month recorded in their death date
            deathday = int(data["deathstamp"][i][8:10])
            if (
                deathday == 0
            ):  # This means that the precise date was previously unknown, so update it
                ded = deathdate(data["wikidata_code"][i])
                if ded != "":
                    deathstampnew[i] = ded
                    fate = "Died - date updated to " + ded
            
            if data["alivewatch?"][i] == 1 and data["deathstamp"][i] != " " and data["position_at_death"][i] == "": # Need to add their position at time of death
                death_position = find_death_position(data, data["wikidata_code"][i])
                deathpositionnew[i] = death_position
                fate = "Already dead - position at death updated to " + death_position
        
        else:  # They are still alive
            if (
                data["birth"][i] > maxyear
            ):  # They are too young to be on Alivewatch, so no further action required
                continue
            else:
                if (
                    data["ranking_visib_5criteria"][i] < minrank
                ):  # They are too famous to be on Alivewatch, so no further action required
                    continue
                else:
                    if (
                        data["ranking_visib_5criteria"][i] > maxrank
                    ):  # They are too obscure to be on Alivewatch, so no further action required
                        continue
                    else:  # They are in the right age range and notability range to be on Alivewatch, and still alive
                        ded = deathdate(
                            data["wikidata_code"][i]
                        )  # Find their death date from Wikipedia
                        if ded == "":  # No death date found, so they are still alive
                            fate = "Still alive - already on Alivewatch"  # Default fate, unless...
                            alivewatchnew[i] = 1
                            if (
                                data["alivewatch?"][i] == 0
                            ):  # Oops! They are not already on Alivewatch, so...
                                dateaddednew[i] = todays_date()
                                fate = "Still alive - added to Alivewatch"  # ...they are now!
                        else:  # They do have a deathdate, so they have died
                            fate = "Died under watch:" + ded
                            deathstampnew[i] = ded
                            if data["alivewatch?"][i] == 0:
                                fate = "Died - missed by Alivewatch"
        if fate != "":
            print("Processing ", str(i) + "/" + str(num), data["name"][i], fate)
    newdata["deathstamp"] = deathstampnew
    newdata["alivewatch?"] = alivewatchnew
    newdata["date_added_to_alivewatch"] = dateaddednew
    newdata["position_at_death"] = deathpositionnew
    print("Saving updated Alivewatch file")
    newdata.to_csv(
        "Alivewatch.csv.gz", index=False, compression="gzip", encoding="utf-8"
    )

    # Update the last updated date in last_updated.txt
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/last_updated.txt", "w") as f:
        f.write(now)


def report(maxyear, maxrank):
    """
    Produces a set of csv files from Alivewatch.csv, including:
    - all the people who are still alive, on alivewatch, ranked by risk factor
    - all the people who died since the last update, but weren't on alivewatch
    - all the people who were on alivewatch but have died since the last update
    - all the people who were added to alivewatch since the last update
    Saves these files in the data directory and in the old_data directory with a date stamp.

    Parameters:
    maxyear (int): The maximum year of birth for people to be included in Alivewatch.
    maxrank (int): The maximum notability rank for people to be included in Alivewatch.

    Returns:
    None
    """

    # Read in data
    data = pd.read_csv(
        "Alivewatch.csv.gz",
        na_filter=False,
        compression="gzip",
        encoding="utf-8",
        dtype={"date_added_to_alivewatch": "object"},
        low_memory=False,
    )
    num = len(data)

    # Clean up values
    data["name"] = data["name"].apply(clean_name)
    data["level3_main_occ"] = data["level3_main_occ"].str.replace("_", " ").str.title()

    # Create new dataframes
    alive = pd.DataFrame(
        columns=[
            "name",
            "profession",
            "age",
            "ranking_visib_5criteria",
            "date_added_to_alivewatch",
            "risk_factor",
        ]
    )
    died = pd.DataFrame(columns=["name", "profession", "birth", "deathstamp"])
    diedsince = pd.DataFrame(
        columns=[
            "name",
            "profession",
            "birth",
            "deathstamp",
            "date_added_to_alivewatch",
        ]
    )
    added = pd.DataFrame(
        columns=[
            "name",
            "profession",
            "birth",
            "ranking_visib_5criteria",
            "date_added_to_alivewatch",
        ]
    )

    # Populate new dataframes
    alive_list = []
    died_list = []
    diedsince_list = []

    # Populate lists instead of concatenating DataFrames in a loop
    for i in range(num):
        if (
            data["deathstamp"][i] == " " and data["alivewatch?"][i] == 1
        ):  # Still alive and on Alivewatch
            alive_list.append(
                {
                    "name": data["name"][i],
                    "profession": data["level3_main_occ"][i],
                    "age": int(todays_date()[0:4]) - data["birth"][i],
                    "ranking_visib_5criteria": data["ranking_visib_5criteria"][i],
                    "date_added_to_alivewatch": data["date_added_to_alivewatch"][i],
                }
            )

        if (
            data["deathstamp"][i] != " " and data["alivewatch?"][i] == 0
        ):  # Dead, but not on Alivewatch
            died_list.append(
                {
                    "name": data["name"][i],
                    "profession": data["level3_main_occ"][i],
                    "birth": data["birth"][i],
                    "deathstamp": data["deathstamp"][i],
                }
            )

        if (
            data["deathstamp"][i] != " " and data["alivewatch?"][i] == 1
        ):  # Died under Alivewatch
            diedsince_list.append(
                {
                    "name": data["name"][i],
                    "profession": data["level3_main_occ"][i],
                    "birth": data["birth"][i],
                    "deathstamp": data["deathstamp"][i],
                    "date_added_to_alivewatch": data["date_added_to_alivewatch"][i],
                }
            )

    # Convert lists to DataFrames in one go (avoiding repeated concatenation)
    alive = pd.DataFrame(alive_list)
    died = pd.DataFrame(died_list)
    diedsince = pd.DataFrame(diedsince_list)

    # Add risk factor to Alivewatch
    riskfactors = []
    for i in range(len(alive)):
        nextfactor = (
            6600 * alive["age"][i]
            - alive["ranking_visib_5criteria"][i]
            - 6600 * (int(todays_date()[0:4]) - maxyear)
            + maxrank
        ) / 200000
        riskfactors.append(nextfactor)
    alive["risk_factor"] = riskfactors

    # Sort dataframes
    alive = alive.sort_values(
        by=["risk_factor"], ascending=False
    )  # Currently on Alivewatch
    died = died.sort_values(by=["deathstamp"], ascending=False)  # Missed by Alivewatch
    diedsince = diedsince.sort_values(
        by=["deathstamp"], ascending=False
    )  # Died under Alivewatch, sorted by date of death - most recent first
    added = alive.copy().sort_values(
        by=["date_added_to_alivewatch"], ascending=False
    )  # Alivewatch sorted by date added - most recent first

    # Add priority number to 'alive'
    alive.insert(0, "priority", range(1, len(alive) + 1))

    # Drop unnecessary columns
    alive = alive.drop(columns=["risk_factor", "ranking_visib_5criteria"])
    diedsince = diedsince.drop(columns=["date_added_to_alivewatch"])
    added = added.drop(columns=["ranking_visib_5criteria", "risk_factor"])

    # Rename columns
    alive = alive.rename(
        columns={
            "priority": "Priority Rank",
            "name": "Name",
            "profession": "Profession",
            "age": "Approximate Age",
            "date_added_to_alivewatch": "Date Added to Alivewatch",
        }
    )
    diedsince = diedsince.rename(
        columns={
            "name": "Name",
            "profession": "Profession",
            "birth": "Birth Year",
            "deathstamp": "Date of Death",
        }
    )
    died = died.rename(
        columns={
            "name": "Name",
            "profession": "Profession",
            "birth": "Birth Year",
            "deathstamp": "Date of Death",
        }
    )
    added = added.rename(
        columns={
            "name": "Name",
            "age": "Approximate Age",
            "profession": "Profession",
            "birth": "Birth Year",
            "date_added_to_alivewatch": "Date Added to Alivewatch",
        }
    )

    # Write the date-named versions of the dataframes to csv in old_data
    print("Saving copies to the old data directory")
    filepath = "old_data/"
    alive.to_csv(
        filepath + todays_date() + "-On_Alivewatch.csv", index=False, encoding="utf-8"
    )
    died.to_csv(
        filepath + todays_date() + "-Missed_by_alivewatch.csv",
        index=False,
        encoding="utf-8",
    )
    diedsince.to_csv(
        filepath + todays_date() + "-Died_under_watch.csv",
        index=False,
        encoding="utf-8",
    )
    added.to_csv(
        filepath + todays_date() + "-Alivewatch_by_date_added.csv",
        index=False,
        encoding="utf-8",
    )

    # Write the non-dated versions to the data directory
    print("Saving the latest versions to the data directory")
    alive.to_csv("data/On_Alivewatch.csv", index=False, encoding="utf-8")
    died.to_csv("data/Missed_by_alivewatch.csv", index=False, encoding="utf-8")
    diedsince.to_csv("data/Died_under_watch.csv", index=False, encoding="utf-8")
    added.to_csv("data/Alivewatch_by_date_added.csv", index=False, encoding="utf-8")

def main():
    """
    Main function to run the update and report functions. Updates the Alivewatch.csv file and generates reports.

    Parameters:
    None

    Returns:
    None
    """

    # Set parameters
    maxyear = datetime.datetime.now().year - 85
    minrank = 1000  # minimum notability rank (excludes people who are too famous)
    maxrank = 100000  # maximum notability rank (excludes people who are too obscure)

    # Update Alivewatch from wikipedia
    update(maxyear, minrank, maxrank)

    # Create reports
    report(maxyear, maxrank)


if __name__ == "__main__":
    main()

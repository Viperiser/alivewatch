# Updates death dates in Alivewatch.csv meeting criteria
# Then outputs still-living people meeting these criteria, in birth order, as an 'Alivewatch' csv

# Libraries
import datetime
import re
import requests
import pandas as pd
import os


def clean_name(name):
    # Remove underscores and replace with spaces
    name = name.replace("_", " ")
    # Remove leading/trailing quotes
    name = name.strip('"')
    # Remove multiple spaces (if underscores were next to each other)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

# Date of death is property P570
def deathdate(id):
    # Returns date of death if it exists
    print(id)
    uri = "https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&ids="+id+"&format=json"
    r = requests.get(uri).json()
    datetime = ''
    if 'P570' in r['entities'][id]['claims']:
        datetime = r['entities'][id]['claims']['P570'][0]['mainsnak']['datavalue']['value']['time']
    # extract date from datetime
    if datetime != '':
        datetime = datetime[1:11]
    # note this is already in format YYYY-MM-DD
    return datetime

def todays_date():
    # Returns today's date in format YYYY-MM-DD
    now = datetime.datetime.now()
    year = str(now.year)
    month = str(now.month)
    if len(month) == 1:
        month = '0'+month
    day = str(now.day)
    if len(day) == 1:
        day = '0'+day
    return year+'-'+month+'-'+day

def compare_dates(date1, date2):
    # returns True if date1 is later than date2
    # date1 and date2 are strings in format YYYY-MM-DD
    # if date1 is later than date2, returns True
    # if date1 is earlier than date2, returns False
    # if date1 is the same as date2, returns False
    # if date1 is blank, returns False
    # if date2 is blank, returns True
    if date1 == '':
        return False
    elif date2 == '':
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

# Update Alivewatch
def update(maxyear, minrank, maxrank):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/last_updated.txt", "w") as f:
        f.write(now)
    
    data = pd.read_csv('Alivewatch.csv.gz', compression = 'gzip', encoding='utf-8')
    newdata = data.copy()
    num = len(data)
    deathstampnew = data['deathstamp'].copy() # Use existing date unless updated below
    alivewatchnew = data['alivewatch?'].copy() # Use existing value unless updated below
    dateaddednew = data['date_added_to_alivewatch'].copy() # Use existing date unless updated below
    for i in range(num):
        # check if died
        if data['deathstamp'][i] != ' ': # They are already recorded as dead, so no further action required
            fate = 'Already dead'
            # Find the day of the month recorded in their death date
            deathday = int(data['deathstamp'][i][8:10])
            if deathday ==0: # This means that the precise date was previously unknown, so update it
                ded = deathdate(data['wikidata_code'][i])
                if ded != '':
                    deathstampnew[i] = ded
                    fate = 'Died - date updated to '+ded
        else:
            if data['birth'][i] > maxyear: # They are too young to be on Alivewatch, so no further action required
                continue
            else:
                if data['ranking_visib_5criteria'][i] < minrank: # They are too famous to be on Alivewatch, so no further action required
                    continue
                else:
                    if data['ranking_visib_5criteria'][i] > maxrank: # They are too obscure to be on Alivewatch, so no further action required
                        continue
                    else: # They are in the right age range and notability range to be on Alivewatch, and still alive
                        ded = deathdate(data['wikidata_code'][i]) # Find their death date from Wikipedia
                        if ded == '': # No death date found, so they are still alive
                            fate = 'Still alive - already on Alivewatch' # Default fate, unless...
                            alivewatchnew[i] = 1 
                            if data['alivewatch?'][i] == 0: # Oops! They are not already on Alivewatch, so...
                                dateaddednew[i] = todays_date()
                                fate = 'Still alive - added to Alivewatch' # ...they are now!
                        else: # They do have a deathdate, so they have died
                            fate = 'Died under watch:'+ ded
                            deathstampnew[i] = ded
                            if data['alivewatch?'][i] == 0:
                                fate = 'Died - missed by Alivewatch'
        if fate != '':
            print("Processing ", str(i)+"/"+str(num),data['name'][i], fate)
    newdata['deathstamp'] = deathstampnew
    newdata['alivewatch?'] = alivewatchnew
    newdata['date_added_to_alivewatch'] = dateaddednew
    print("Saving updated Alivewatch file")
    newdata.to_csv('Alivewatch.csv.gz', index=False, compression = 'gzip', encoding='utf-8')

def report(maxyear, maxrank):
    '''Produce a spreadsheet with tabs for:
    - all the people who are still alive, on alivewatch, ranked by fame
    - all the people who died since the last update, but weren't on alivewatch
    - all the people who were on alivewatch but have died since the last update
    - all the people who were added to alivewatch since the last update
    '''
    
    # Read in data
    data = pd.read_csv('Alivewatch.csv.gz', compression = 'gzip', encoding='utf-8', dtype = {'date_added_to_alivewatch': 'object'}, low_memory = False)
    num = len(data)
    
    # Clean up values
    data['name'] = data['name'].apply(clean_name)
    data['level3_main_occ'] = data['level3_main_occ'].str.replace("_", " ").str.title()
    
    # Create new dataframes
    alive = pd.DataFrame(columns=['name','profession', 'age','ranking_visib_5criteria','date_added_to_alivewatch','risk_factor'])
    died = pd.DataFrame(columns=['name','profession', 'birth','deathstamp'])
    diedsince = pd.DataFrame(columns=['name','profession','birth','deathstamp', 'date_added_to_alivewatch'])
    added = pd.DataFrame(columns=['name','profession', 'birth','ranking_visib_5criteria','date_added_to_alivewatch'])
    
    # Populate new dataframes
    alive_list = []
    died_list = []
    diedsince_list = []

    # Populate lists instead of concatenating DataFrames in a loop
    for i in range(num):
        if data['deathstamp'][i] == ' ' and data['alivewatch?'][i] == 1:  # Still alive and on Alivewatch
            alive_list.append({
                'name': data['name'][i],
                'profession': data['level3_main_occ'][i],
                'age': int(todays_date()[0:4]) - data['birth'][i],
                'ranking_visib_5criteria': data['ranking_visib_5criteria'][i],
                'date_added_to_alivewatch': data['date_added_to_alivewatch'][i]
            })

        if data['deathstamp'][i] != ' ' and data['alivewatch?'][i] == 0:  # Dead, but not on Alivewatch
            died_list.append({
                'name': data['name'][i],
                'profession': data['level3_main_occ'][i],
                'birth': data['birth'][i],
                'deathstamp': data['deathstamp'][i]
            })

        if data['deathstamp'][i] != ' ' and data['alivewatch?'][i] == 1:  # Died under Alivewatch
            diedsince_list.append({
                'name': data['name'][i],
                'profession': data['level3_main_occ'][i],
                'birth': data['birth'][i],
                'deathstamp': data['deathstamp'][i],
                'date_added_to_alivewatch': data['date_added_to_alivewatch'][i]
            })

    # Convert lists to DataFrames in one go (avoiding repeated concatenation)
    alive = pd.DataFrame(alive_list)
    died = pd.DataFrame(died_list)
    diedsince = pd.DataFrame(diedsince_list)
   
    # Add risk factor to Alivewatch
    riskfactors = []
    for i in range(len(alive)):
        nextfactor = (6600 * alive['age'][i] - alive['ranking_visib_5criteria'][i] - 6600 * (int(todays_date()[0:4]) - maxyear) + maxrank)/200000
        riskfactors.append(nextfactor)
    alive['risk_factor'] = riskfactors

    # Sort dataframes
    alive = alive.sort_values(by=['risk_factor'], ascending=False) # Currently on Alivewatch
    died = died.sort_values(by=['deathstamp'], ascending = False) # Missed by Alivewatch
    diedsince = diedsince.sort_values(by=['deathstamp'], ascending=False) # Died under Alivewatch, sorted by date of death - most recent first
    added = alive.copy().sort_values(by=['date_added_to_alivewatch'], ascending = False) # Alivewatch sorted by date added - most recent first

    # Add priority number to 'alive'
    alive.insert(0, 'priority', range(1, len(alive)+1))
    
    # Drop unnecessary columns
    alive = alive.drop(columns=['risk_factor', 'ranking_visib_5criteria'])
    diedsince = diedsince.drop(columns=['date_added_to_alivewatch'])
    added = added.drop(columns=['ranking_visib_5criteria', 'risk_factor'])
    
    # Rename columns
    alive = alive.rename(columns={'priority': 'Priority Rank', 'name': 'Name', 'profession': 'Profession', 'age': 'Approximate Age', 'date_added_to_alivewatch': 'Date Added to Alivewatch'})
    diedsince = diedsince.rename(columns={'name': 'Name', 'profession': 'Profession', 'birth': 'Birth Year', 'deathstamp': 'Date of Death'})
    died = died.rename(columns={'name': 'Name', 'profession': 'Profession', 'birth': 'Birth Year', 'deathstamp': 'Date of Death'})
    added = added.rename(columns={'name': 'Name', 'age': 'Approximate Age', 'profession': 'Profession', 'birth': 'Birth Year', 'date_added_to_alivewatch': 'Date Added to Alivewatch'})

    # Write the date-named versions of the dataframes to csv in old_data
    print("Saving copies to the old data directory")
    filepath = 'old_data/'
    alive.to_csv(filepath+todays_date()+'-On_Alivewatch.csv', index=False, encoding='utf-8')
    died.to_csv(filepath+todays_date()+'-Missed_by_alivewatch.csv', index=False, encoding='utf-8')
    diedsince.to_csv(filepath+todays_date()+'-Died_under_watch.csv', index=False, encoding='utf-8')
    added.to_csv(filepath+todays_date()+'-Alivewatch_by_date_added.csv', index=False, encoding='utf-8')

    # Write the non-dated versions to the data directory
    print("Saving the latest versions to the data directory")
    alive.to_csv('data/On_Alivewatch.csv', index=False, encoding='utf-8')
    died.to_csv('data/Missed_by_alivewatch.csv', index=False, encoding='utf-8')
    diedsince.to_csv('data/Died_under_watch.csv', index=False, encoding='utf-8')
    added.to_csv('data/Alivewatch_by_date_added.csv', index=False, encoding='utf-8')
    
    print("📂 Checking files in old_data/ before commit:")

    # List all files in old_data/ and print them
    files = os.listdir("old_data")
    if files:
        print("✅ Files in old_data/:", files)
    else:
        print("❌ No files found in old_data/")

def main():
    # Run update to update Alivewatch.csv.
    # Then run report to produce reports.
    # Parameters 
    maxyear = datetime.datetime.now().year - 85
    minrank = 1000 # minimum notability rank (excludes people who are too famous)
    maxrank = 100000 # maximum notability rank (excludes people who are too obscure)

    # Run to update Alivewatch from wikipedia
    update(maxyear, minrank, maxrank)

    # Then create reports
    report(maxyear, maxrank)

if __name__ == "__main__":
    main()


# Updates death dates in Alivewatch.csv meeting criteria
# Then outputs still-living people meeting these criteria, in birth order, as an 'Alivewatch' csv

# Libraries
import datetime
import requests
import pandas
import re

def clean_name(name):
    # Remove underscores and replace with spaces
    name = name.replace("_", " ")
    # Remove leading/trailing quotes
    name = re.sub(r'^"|"$', '', name)
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
    data = pandas.read_csv('Alivewatch.csv.gz', compression = 'gzip', encoding='utf-8')
    newdata = data.copy()
    num = len(data)
    deathstampnew = data['deathstamp'].copy()
    alivewatchnew = data['alivewatch?'].copy()
    dateaddednew = data['date_added_to_alivewatch'].copy()
    for i in range(num):
        # check if died
        if data['deathstamp'][i] != ' ':
            fate = 'Already dead'
        else:
            if data['birth'][i] > maxyear:
                continue
            else:
                if data['ranking_visib_5criteria'][i] < minrank:
                    continue
                else:
                    if data['ranking_visib_5criteria'][i] > maxrank:
                        continue
                    else:
                        ded = deathdate(data['wikidata_code'][i])
                        if ded == '':
                            fate = 'Still alive - already on Alivewatch'
                            alivewatchnew[i] = 1
                            if data['alivewatch?'][i] == 0:
                                dateaddednew[i] = todays_date()
                                fate = 'Still alive - added to Alivewatch'
                        else:
                            fate = 'Died under watch:'+ ded
                            deathstampnew[i] = ded
                            if data['alivewatch?'][i] == 0:
                                fate = 'Died - missed by Alivewatch'
        if fate != '':
            print("Processing ", str(i)+"/"+str(num),data['name'][i], fate)
    newdata['deathstamp'] = deathstampnew
    newdata['alivewatch?'] = alivewatchnew
    newdata['date_added_to_alivewatch'] = dateaddednew
    newdata.to_csv('Alivewatch.csv.gz', index=False, compression = 'gzip', encoding='utf-8')

# Report
def report(maxyear, maxrank):
    # Produce a spreadsheet with tabs for:
    # - all the people who are still alive, on alivewatch, ranked by fame
    # - all the people who died since the last update, but weren't on alivewatch
    # - all the people who were on alivewatch but have died since the last update
    # - all the people who were added to alivewatch since the last update

    # Read in data
    data = pandas.read_csv('Alivewatch.csv.gz', compression = 'gzip', encoding='utf-8')
    num = len(data)
    
    # Clean up names
    data['name'] = data['name'].apply(clean_name)
    
    # Create new dataframes
    alive = pandas.DataFrame(columns=['name','profession', 'age','ranking_visib_5criteria','date_added_to_alivewatch','risk_factor'])
    died = pandas.DataFrame(columns=['name','profession', 'birth','deathstamp'])
    diedsince = pandas.DataFrame(columns=['name','profession','birth','deathstamp', 'date_added_to_alivewatch'])
    added = pandas.DataFrame(columns=['name','profession', 'birth','ranking_visib_5criteria','date_added_to_alivewatch'])
    
    # Populate new dataframes
    for i in range(num):
        if data['deathstamp'][i] == ' ' and data['alivewatch?'][i] == 1: # still alive and on Alivewatch
            alive = pandas.concat([alive, pandas.DataFrame([{'name':data['name'][i],'profession':data['level3_main_occ'][i], 'age':(int(todays_date()[0:4]) - data['birth'][i]),'ranking_visib_5criteria':data['ranking_visib_5criteria'][i],'date_added_to_alivewatch':data['date_added_to_alivewatch'][i]}])], ignore_index=True)
        if data['deathstamp'][i] != ' ' and data['alivewatch?'][i] == 0: # dead, but not on Alivewatch
            died = pandas.concat([died, pandas.DataFrame([{'name':data['name'][i],'profession':data['level3_main_occ'][i],'birth':data['birth'][i],'deathstamp':data['deathstamp'][i]}])], ignore_index=True)
        if data['deathstamp'][i] != ' ' and data['alivewatch?'][i] == 1: # died under Alivewatch
            diedsince = pandas.concat([diedsince, pandas.DataFrame([{'name':data['name'][i],'profession':data['level3_main_occ'][i],'birth':data['birth'][i],'deathstamp':data['deathstamp'][i], 'date_added_to_alivewatch':data['date_added_to_alivewatch'][i]}])], ignore_index=True)

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

    # Write the date-named versions of the dataframes to csv in old_data
    filepath = 'old_data/'
    alive.to_csv(filepath+todays_date()+'-On_Alivewatch.csv', index=False, encoding='utf-8')
    died.to_csv(filepath+todays_date()+'-Missed_by_alivewatch.csv', index=False, encoding='utf-8')
    diedsince.to_csv(filepath+todays_date()+'-Died_under_watch.csv', index=False, encoding='utf-8')
    added.to_csv(filepath+todays_date()+'-Alivewatch_by_date_added.csv', index=False, encoding='utf-8')

    # Write the non-dated versions to the data directory
    alive.to_csv('data/On_Alivewatch.csv', index=False, encoding='utf-8')
    died.to_csv('data/Missed_by_alivewatch.csv', index=False, encoding='utf-8')
    diedsince.to_csv('data/Died_under_watch.csv', index=False, encoding='utf-8')
    added.to_csv('data/Alivewatch_by_date_added.csv', index=False, encoding='utf-8')

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

# main()
report(1940, 100000) # for testing

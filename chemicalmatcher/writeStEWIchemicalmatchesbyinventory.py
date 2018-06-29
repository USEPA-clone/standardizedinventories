#Retrieves all unique flow names from the StEWI flow list
import requests
import pandas as pd
import os
import re

from chemicalmatcher.globals import query_SRS_by_alternate_id
from chemicalmatcher.globals import query_SRS_by_substance_name

#datapath = 'chemicalmatcher/data/'
#outputpath = 'chemicalmatcher/output/'
#outputfilename = 'SRSlistfomCASlist.csv'
#outputfilename = 'SRSlistfromCASlist2.csv'

#import list of names
#filename = 'examplecaslistforepaNamelookup.csv'
#filename = '../standardizedinventories/stewi/output/flow/TRI_2016.csv'

stewi_facility_dir = 'stewi/output/flow/'

try: flowlists = os.listdir(stewi_facility_dir)
except: print('Directory missing')

all_list_names = pd.DataFrame(columns=["FlowName","FlowID","Source","Waste Code Type"])

flowlist_cols = {"RCRAInfo":['FlowName','FlowID','Waste Code Type'],
                 "eGRID": ['FlowName'],
                 "TRI": ['FlowName','FlowID'],
                 "NEI":['FlowName'],
                 "GHGRP":['FlowName']}

#First loop through flows lists to create a list of all unique flows
for l in flowlists:
    source_name = l[0:l.find("_")]
    source_cols = flowlist_cols[source_name]
    list_names = pd.read_csv(stewi_facility_dir+l,header=0,usecols=source_cols)
    list_names['Source'] = source_name
    all_list_names = pd.concat([all_list_names,list_names])
    #namelist_unique = pd.unique(namelist['FlowName'])

#Drop duplicates
all_list_names.drop_duplicates(inplace=True)
#For RCRAInfo, only keep for SRS queries if waste code types are associated with lists in SRS
RCRA_waste_code_types_SRS = ['F','K','P','U']
all_list_names = all_list_names[(all_list_names["Source"]=="RCRAInfo") & (all_list_names["Waste Code Type"].isin(RCRA_waste_code_types_SRS))]

#Reset index after removing flows
all_list_names.reset_index(inplace=True,drop=True)

#NEI names like '4,4 -Methylenediphenyl Diisocyanate' should be '4,4'-Methylenediphenyl Diisocyanate
#Only for querying NEI by name
#Use a regular expression to fix it
def temp_NEI_name_fix(name):
    if re.search(r'\d\s-', name):
        name = name.replace(" -","'-")
    return name


#RCRAInfo using ' (OR)' or ' (R' or ' (C' or ' (T' R in the names but this won't lookup. Grab the string before the start of this
#Only for querying RCRAInfo by name
def fix_rcra_or_cuttoff(name):
    match_object = re.search(r'\s\([ORTC]', name)
    if match_object:
        #Get name from beginning to point of matching the ' ('
        name = name[0:match_object.start()]
     return name

#Determine whether to use the id or name to query SRS
inventory_query_type = {"RCRAInfo":"id",
                        "TRI":"id",
                        "NEI":"id",
                        "eGRID":"name"}

#Create a df to store the results
all_lists_srs_ids = pd.DataFrame(columns=["FlowName","SRS_ID","SRS_CAS","Source"])
errors_srs = pd.DataFrame(columns=["FlowName","Source","ErrorType"])

for r in range(0,len(all_list_names)-1):
    chemical_srs_info = pd.DataFrame(columns=["FlowName", "SRS_ID", "SRS_CAS", "Source"])
    error_srs = pd.DataFrame(columns=["FlowName","Source","ErrorDescription"])
    name = all_list_names["FlowName"][r]
    id = all_list_names["FlowID"][r]
    source = all_list_names["Source"][r]
    if inventory_query_type[source] == 'id':
        result = query_SRS_by_alternate_id(id, source)
    if inventory_query_type[source] == 'name':
        result = query_SRS_by_substance_name(name)
    if type(result) is 'str':
        #This is an error
        error_srs.loc[0, 'FlowName'] = name
        error_srs.loc[0, 'Source'] = source
        error_srs.loc[0, 'ErrorType'] = result
    else:
        chemical_srs_info = result
        chemical_srs_info.loc[0, "FlowName"] = name
        chemical_srs_info.loc[0, "Source"] = source
    errors_srs = pd.concat([errors_srs,error_srs])
    all_lists_srs_ids = pd.concat([all_lists_srs_ids, chemical_srs_info])

#Old code to query 10 names at a time .. faster but problem with lack of ordering of json response
# for i in range(0, len(all_list_names), 10):
#    print(i)
#    names_for_query  = ""
#    try:
#       all_list_names['FlowName'][i + 10 - 1]
#       index_of_last = i + 10 - 1
#    except: index_of_last = len(all_list_names) - 1
#    for n in all_list_names['FlowName'][i:index_of_last]:
#        names_for_query = names_for_query+n+'|'
#    #add on last name
#    names_for_query = names_for_query + all_list_names['FlowName'][index_of_last]
#
#    #Enoode the name to make it safe for the URL
#    names_for_query = urllib.parse.quote(names_for_query)
#
#    #perform query
#    url = base+namelistprefix+names_for_query+excludeSynonyms
#    chemicallistresponse = requests.get(url)
#    chemicallistjson = json.loads(chemicallistresponse.text)
#    len(chemicallistjson)
#    #Careful! Order of json response is not the same order as chemicals in the request
#    #Loop through each chemical in the response
#    #add each one to a dictionary
#    sequence_num = i
#    for chemical in chemicallistjson:
#       #get SRS
#       chemicaldict = {}
#       chemicaldict['FlowName'] = all_list_names['FlowName'][sequence_num]
#       chemicaldict['SRS_ID'] = chemical['subsKey']
#       chemicaldict['SRS_CAS'] = chemical['currentCasNumber']
#       chemicaldict['Source'] = all_list_names['Source'][sequence_num]
#       #get epaName
#       #chemicaldict['epaName'] = chemical['epaName']
#       list_srs_ids = list_srs_ids.append(chemicaldict,ignore_index=True)
#       sequence_num=sequence_num+1
#
# #Name source
# name_frs_ids['Source'] = l
# #Add to master df
# all_lists_frs_ids = pd.concat([all_lists_frs_ids,name_frs_ids])


#Write to csv
all_lists_srs_ids.to_csv(outputpath+'ChemicalsByInventorywithSRS_IDS_forStEWI.csv', index=False)






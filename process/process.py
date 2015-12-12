########################
# Threat intelligence matching using Pandas and Open Source Intel Feeds
# Author: MetaStack, Inc -- BRB
# Date: 12/7/2015
#
# This script will load multiple threat intelligence feeds and compare it to data sets
# placed in the "Raw" folder. The output is a single "merged" data set that can be
# passed to data graphing utility for threat identification and analysis.
#########################

import pandas as pd
import numpy as np
import os
import glob # necessary if using csv matching instead of download of open source feeds


#### Specify data paths for matching with threat intel and output file for enriched dataset
data = 'raw' + os.sep + 'data.csv'  #Raw network data set
output ='..' + os.sep + 'examples' + os.sep + 'output.csv'  #output directory for enriched csv - DO NOT CHANGE


#### Identify and collect threat intel feeds
def threat_collect():

    # Includes Malc0de, emerging threats and Zeus Tracker as examples
    url_malc0de = 'http://malc0de.com/bl/IP_Blacklist.txt'
    url_et = 'http://rules.emergingthreats.net/blockrules/compromised-ips.txt'
    url_zeus = 'https://zeustracker.abuse.ch/blocklist.php?download=ipblocklist'
    url_zeus_domains = 'https://zeustracker.abuse.ch/blocklist.php?download=domainblocklist'

    #Convert to DataFrames
    df_malc0de = pd.read_table(url_malc0de, index_col=None, skiprows=6, header=None, names=['actor'])
    df_et = pd.read_table(url_et, index_col=None, skiprows=5, header=0, names=['actor'])
    df_zeus = pd.read_table(url_zeus, index_col=None, skiprows=6, header=0, names=['actor'])
    df_zeus_domains = pd.read_table(url_zeus_domains, index_col=None, skiprows=6, header=0, names=['actor'])

    # Alternatively, put a bunch of threat intel CSVs in the "intel" directory
    #
    # Read all threat intel from intel folder
    # intel_path ='intel'
    # all = glob.glob(intel_path + "/*.csv")
    # ti_combine = pd.DataFrame()
    # ti_list_ = []
    # for file_ in all:
    #     new_frame = pd.read_csv(file_,index_col=None, header=0, names=['actor'])
    #     ti_list_.append(new_frame)
    # ti_combine = pd.concat(ti_list_)

    # Combine dataframes
    ti_combine = pd.concat([df_malc0de, df_et, df_zeus, df_zeus_domains], axis=0)

    return ti_combine


#### Take combined threat intel lists and match against raw dataset. Return properly formatted dataframe.
def threat_matcher():

    # grab combined threat intel
    ti_combine = threat_collect()

    # Read raw network data
    df_data = pd.read_csv(data, error_bad_lines=False, keep_default_na=False, na_values=[''], skiprows=1, names=['datetime','source', 'target'], parse_dates=['datetime'])

    # Find and combine hits
    ti_src = pd.merge(left=df_data, right=ti_combine, left_on='source', right_on='actor')
    ti_tgt = pd.merge(left=df_data, right=ti_combine, left_on='target', right_on='actor')
    hits_combine = pd.concat([ti_src, ti_tgt], axis=0)

    # Merge or Concatenate TI hits and raw data. Using left join to ensure raw dataset remains and hits are "merged"
    enriched = pd.merge(left=df_data,right=hits_combine, how='left', left_on=['datetime','source', 'target'], right_on=['datetime','source', 'target'])

    # Add columns for src and tgt hits, clean up dataframe and format date time column as a datetime object
    # Next two lines add a column called src_hit or target_hit based on which field matched the indicator
    enriched['src_hit'] = np.where(enriched['source']==enriched['actor'], 'true', '')
    enriched['target_hit'] = np.where(enriched['target']==enriched['actor'], 'true', '')

    # Remove "actor" field
    enriched = enriched.drop('actor', 1)

    # Add new column called "Event Time" based on a conversion of datetime to datetime object
    enriched['Event Time'] = enriched['datetime'].astype('int').astype('datetime64[s]')

    # Reformat dataframe to change column order
    enriched = enriched[['Event Time', 'source', 'target', 'src_hit', 'target_hit']]

    return enriched


#### Will result in one enriched data set to CSV with proper header and formats to app directory for visualization
def main():

    # Return output of match_writer which should be a properly formatted and enriched data set.
    enriched = threat_matcher()

    # Write to CSV in examples directory for visualization
    enriched.to_csv(output, columns = ['Event Time', 'source', 'target', 'src_hit', 'target_hit'],
                    header = ['Event Time', 'sourceAddress', 'destinationAddress', 'src_hit', 'target_hit'], index=False)

main()
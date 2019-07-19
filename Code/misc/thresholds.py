"""
Weather-Thresholds_9306121.html

Description:

"The following table defines Weather thresholds used to determine the classification of Weather as Normal, Alert,
Adverse or Extreme. Note that the 'Alert' interval is inside the 'Normal' range."

"These are national thresholds. Route-specific thresholds may also be defined at some point."

"""

import os

import pandas as pd
from pyhelpers.dir import cdd
from pyhelpers.store import load_pickle, save_pickle


# Change directory to "Incidents"
def cdd_schedule8(*directories):
    path = cdd("Incidents")
    for directory in directories:
        path = os.path.join(path, directory)
    return path


#
def read_thresholds_from_html():
    # thr: thresholds
    html_filename = "Weather-Thresholds_9306121.html"
    path_to_html = cdd("METEX\\Weather\\Thresholds", html_filename)
    thr = pd.read_html(path_to_html)
    thr = thr[0]
    # Specify column names
    hdr = thr.loc[0].tolist()
    thr.columns = hdr
    # Drop the first row, which has been used as the column names
    thr.drop(0, inplace=True)
    # cls: classification
    assert isinstance(thr, pd.DataFrame)
    cls = thr[pd.isnull(thr).any(axis=1)]['Classification']
    cls_list = []
    for i in range(len(cls)):
        # rpt: repeat
        to_rpt = (cls.index[i + 1] - cls.index[i] - 1) if i + 1 < len(cls) else (thr.index[-1] - cls.index[i])
        cls_list += [cls.iloc[i]] * to_rpt
    thr.drop(cls.index, inplace=True)
    thr.index = cls_list
    thr.index.names = ['Classification']
    thr.rename(columns={'Classification': 'Description'}, inplace=True)

    # Add 'VariableName' and 'Unit'
    variables = ['T', 'x', 'r', 'w']
    units = ['celsius degree', 'cm', 'mm', 'mph']
    variables_list, units_list = [], []
    for i in range(len(cls)):
        variables_temp = [variables[i]] * thr.index.tolist().count(cls.iloc[i])
        units_temp = [units[i]] * thr.index.tolist().count(cls.iloc[i])
        variables_list += variables_temp
        units_list += units_temp
    thr.insert(1, 'VariableName', variables_list)
    thr.insert(2, 'Unit', units_list)

    # Retain main description
    desc_temp = thr['Description'].tolist()
    for i in range(len(desc_temp)):
        desc_temp[i] = desc_temp[i].replace('\xa0', ' ')
        desc_temp[i] = desc_temp[i].replace(' ( oC )', '')
        desc_temp[i] = desc_temp[i].replace(', x (cm)', '')
        desc_temp[i] = desc_temp[i].replace(', r (mm)', '')
        desc_temp[i] = desc_temp[i].replace(', w (mph)', '')
        desc_temp[i] = desc_temp[i].replace(' (mph)', ' ')
    thr['Description'] = desc_temp

    # Upper and lower boundaries
    def boundary(df, col, sep1=None, sep2=None):
        if sep1:
            lst_lb = [thr[col].iloc[0].split(sep1)[0]]
            lst_lb += [v.split(sep2)[0] for v in thr[col].iloc[1:]]
            df.insert(df.columns.get_loc(col) + 1, col + 'LowerBound', lst_lb)
        if sep2:
            lst_ub = [thr[col].iloc[0].split(sep2)[1]]
            lst_ub += [v.split(sep1)[-1] for v in thr[col].iloc[1:]]
            if sep1:
                df.insert(df.columns.get_loc(col) + 2, col + 'UpperBound', lst_ub)
            else:
                df.insert(df.columns.get_loc(col) + 1, col + 'Threshold', lst_ub)

    boundary(thr, 'Normal', sep1=None, sep2='up to ')  # Normal
    boundary(thr, 'Alert', sep1=' \u003C ', sep2=' \u2264 ')  # Alert
    boundary(thr, 'Adverse', sep1=' \u003C ', sep2=' \u2264 ')  # Adverse
    extreme = [thr['Extreme'].iloc[0].split(' \u2264 ')[1]]  # Extreme
    extreme += [v.split(' \u2265 ')[1] for v in thr['Extreme'].iloc[1:]]
    thr['ExtremeThreshold'] = extreme

    return thr


# The threshold data is also available in the following file: "Schedule8WeatherIncidents-02062006-31032014.xlsm"
def read_thresholds_from_workbook(update=False):
    pickle_filename = "Spreadsheets", "Worksheet_Thresholds.pickle"
    path_to_pickle = cdd_schedule8(pickle_filename)
    if os.path.isfile(path_to_pickle) and not update:
        thresholds = load_pickle(path_to_pickle)
    else:
        try:
            thresholds = pd.read_excel(
                cdd_schedule8("Spreadsheets", "Schedule8WeatherIncidents-02062006-31032014.xlsm"),
                sheetname="Thresholds", parse_cols="A:F")
            thresholds.dropna(inplace=True)
            thresholds.index = range(len(thresholds))
            thresholds.columns = [col.replace(' ', '') for col in thresholds.columns]
            thresholds.WeatherHazard = thresholds.WeatherHazard.map(lambda x: x.upper().strip())
            save_pickle(thresholds, path_to_pickle)
        except Exception as e:
            print("Failed to read \"Weather thresholds\" from the workbook. {}.".format(e))
            thresholds = None
    return thresholds


def get_weather_thresholds(update=False):
    pickle_filename = "Thresholds.pickle"
    path_to_pickle = cdd("METEX\\Weather\\Thresholds", pickle_filename)
    if os.path.isfile(path_to_pickle) and not update:
        thresholds = load_pickle(path_to_pickle)
    else:
        try:
            thr0 = read_thresholds_from_html()
            thr1 = read_thresholds_from_workbook(update)
            thresholds = [thr0, thr1]
            save_pickle(thresholds, path_to_pickle)
        except Exception as e:
            print("Failed to get \"Weather thresholds\". {}.".format(e))
            thresholds = None
    return thresholds
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind

states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National', 'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana', 'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont', 'ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan', 'IN': 'Indiana', 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi', 'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', 'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa', 'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana', 'KS': 'Kansas', 'NY': 'New York', 'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California', 'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island', 'MN': 'Minnesota', 'VI': 'Virgin Islands', 'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', 'ND': 'North Dakota', 'VA': 'Virginia'}

towns = pd.read_csv("university_towns.txt",
                     header=None, sep="\n", names=(["toedit", "State", "RegionName"]))

towns["State"] = towns.where(towns["toedit"].str.contains("\[edit")).fillna(method="ffill")

towns["RegionName"] = towns.where(~towns["toedit"].str.contains("\[edit"))

towns.dropna(inplace=True)

towns.drop("toedit", axis=1, inplace=True)

towns["State"] = towns["State"].str.replace("\[.+", "")
towns["RegionName"] = towns["RegionName"].str.replace("\s*\(.+.*", "")

towns.reset_index(drop=True, inplace=True)

def get_list_of_university_towns():

    return towns

gdp = pd.read_excel("gdplev.xls",
                    header=None, skiprows=220, parse_cols=[4, 6],
                    names=["Quarter", "GDP"])

recession_quarters = {}

def get_recession_start():

    def find_recession(value):
        index = gdp[gdp["GDP"] == value].index[0]

        if index == 0:
            pass
        elif value < gdp.iloc[index - 1]["GDP"]:

            if gdp.iloc[index + 1]["GDP"] < value:

                current = index
                next = index + 1

                while gdp.iloc[next]["GDP"] < gdp.iloc[current]["GDP"]:
                    current += 1
                    next += 1

                if gdp.iloc[next]["GDP"] < gdp.iloc[next + 1]["GDP"]:
                    recession_quarters["Start Quarter"] = gdp.iloc[index - 2]["Quarter"]
                    recession_quarters["Bottom Quarter"] = gdp.iloc[current]["Quarter"]
                    recession_quarters["End Quarter"] = gdp.iloc[next + 1]["Quarter"]

        return value

    gdp["GDP"].apply(find_recession)

    return recession_quarters["Start Quarter"]

get_recession_start()

def get_recession_bottom():

    return recession_quarters["Bottom Quarter"]

get_recession_bottom()

def convert_housing_data_to_quarters():

    housing_data = (pd.read_csv("City_Zhvi_AllHomes.csv", index_col=["State", "RegionName"])
                    .filter(regex="20\d{2}-\d{2}")
                    .rename_axis(states))

    housing_data = housing_data.groupby(pd.PeriodIndex(housing_data.columns, freq='q'), axis=1).mean()

    housing_data.columns = housing_data.columns.strftime('%Yq%q')

    return housing_data

convert_housing_data_to_quarters()

def run_ttest():

    recession_housing_prices = convert_housing_data_to_quarters().copy()
    university_towns = get_list_of_university_towns().copy()
    recession_start = get_recession_start()
    recession_bottom = get_recession_bottom()
    different = False
    better = ""

    def find_difference(row):

        row["Recession Difference"] = row[recession_start] - row[recession_bottom]

        return row

    recession_housing_prices = recession_housing_prices.apply(find_difference, axis=1)

    university_towns["University Town"] = "Yes"

    recession_housing_prices = (recession_housing_prices
                                .reset_index()
                                .merge(university_towns, how="outer")
                                .set_index(["State", "RegionName"])
                                )

    recession_housing_prices["University Town"].replace(to_replace=np.nan, value="No", inplace=True)

    utowns_diff = recession_housing_prices["Recession Difference"][recession_housing_prices["University Town"] == "Yes"]

    non_utowns_diff = recession_housing_prices["Recession Difference"][recession_housing_prices["University Town"] == "No"]

    ttest_result = ttest_ind(utowns_diff, non_utowns_diff, nan_policy="omit")

    p = ttest_result[1]

    if p < 0.01:
        different = True

    if np.mean(utowns_diff) < np.mean(non_utowns_diff):
        better = "university town"
    else:
        better = "non-university town"

    return (different, p, better)

ttest_result = run_ttest()

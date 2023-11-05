
'''
The code goes to grants.gov and downloads the XML file for today. 
It then extracts the XML file and reads it into a dataframe.
The dataframe is then cleaned and filtered to only show grants that are open.
The results are then printed to a text file for sharing.

Note: The code downloads the XML file to a local directory.
As a result, the download time may vary based on your internet connection.
With high speed internet (300 mbps), the download takes about 15 seconds.

The code is written in Python 3.11.3 and uses the following libraries:
pandas, requests, xml.etree.ElementTree, datetime, zipfile, os

You may need to install the libraries if you do not have them installed.

If you are new, it is recommended to install Anaconda.
Anaconda is a free and open-source distribution of the Python and R programming languages 
for scientific computing,that aims to simplify package management and deployment.
Anaconda comes with many of the libraries you will need to get started.

Anaconda: https://www.anaconda.com/products/individual

After the download, the code demonstartes a few methods to 
query the dataframe based on the column name and value.
It also shows how to format the EstimatedTotalProgramFunding column
and print the results for easy sharing.

The difference bewteen V1 and V2 is that V@ checks for the raw data, and if it is there, 
the code will not download the file again. This saves time and bandwidth.

#https://www.grants.gov/xml-extract.html website reference

The code is written by Andrew Walker
Aew5044@gmail.com

'''
#%%
#Global variables to change to your unique environment
download_space = r"C:\Users\aew50\Downloads"
py_space = r"C:\Python\Grants_dot_gov"

# %%
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import zipfile
import os

#%%
# Your provided function
def xml_to_df(xml_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    # Extracting the data from the 'OpportunitySynopsisDetail_1_0' tag
    data = []
    for opportunity in root.findall('{http://apply.grants.gov/system/OpportunityDetail-V1.0}OpportunitySynopsisDetail_1_0'):
        record = {}
        for child in opportunity:
            record[child.tag.split('}')[-1]] = child.text
        data.append(record)
    
    # Convert the list of dictionaries into a pandas DataFrame
    df = pd.DataFrame(data)
    
    return df

# Generate URL with today's date
today_date = datetime.today().strftime('%Y%m%d')
url = f"https://prod-grants-gov-chatbot.s3.amazonaws.com/extracts/GrantsDBExtract{today_date}v2.zip"

# Local path to save the downloaded ZIP file
#zip_path = r"C:\Users\aew50\Downloads\GrantsDBExtract{}v2.zip".format(today_date)

# XML file name based on today's date
xml_file_name = f"GrantsDBExtract{today_date}v2.xml"
xml_file_path = os.path.join(py_space, xml_file_name)

zip_file_name = f"GrantsDBExtract{today_date}v2.zip"
download_file_path = os.path.join(download_space, zip_file_name)
zip_path = download_file_path


# Download the ZIP file content
if not os.path.exists(download_file_path):
    print('Downloading zip file')
    response = requests.get(url)
    if response.status_code == 200:
        # Save the content to a local ZIP file
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        # Extract the XML file from the ZIP archive
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Assuming the XML file inside the ZIP has a predictable name
            z.extract(xml_file_name, py_space)

        # # Now use your provided function to read the XML into a DataFrame
        # df = xml_to_df(xml_file_path)
        # print(df)

else:
    print('Zip file was already downloaded for today')
    # xml_file_name = f"GrantsDBExtract{today_date}v2.xml"
    if os.path.exists(xml_file_name):
        print('XML file already exists')
    else:
        print('Extracting XML file')
        with zipfile.ZipFile(zip_path, 'r') as z:
        # Assuming the XML file inside the ZIP has a predictable name
            # xml_file_name = f"GrantsDBExtract{today_date}v2.xml"
            z.extract(xml_file_name, py_space)

#if df already exists, run the following code
#Now use your provided function to read the XML into a DataFrame

try:
    df
    print('df already exists')
except NameError:
    print('df does not exist - extracting XML file')
    df = xml_to_df(xml_file_path)


# %%

#This code is used to clean the dataframe
#It converts the columns to the correct data types
#It also converts the columns to categories to save memory

col = df.columns

df_clean = (df[col]
            #convert CloseDate to date from MMDDYYYY
            .assign(CloseDate = lambda x: pd.to_datetime(x['CloseDate'], format='%m%d%Y'),
                    PostDate = lambda x: pd.to_datetime(x['PostDate'], format='%m%d%Y'),
                    LastUpdatedDate = lambda x: pd.to_datetime(x['PostDate'], format='%m%d%Y'),
                    AwardCeiling = lambda x: pd.to_numeric(x['AwardCeiling'], errors='coerce'),
                    AwardFloor = lambda x: x.AwardFloor.astype(float).astype('Int32'),
                    EstimatedTotalProgramFunding = lambda x: x.EstimatedTotalProgramFunding.astype(float).astype('Int64'),
                    OpportunityCategory = lambda x: x.OpportunityCategory.astype(str).astype('category'),
                    FundingInstrumentType = lambda x: x.FundingInstrumentType.astype(str).astype('category'),
                    CategoryOfFundingActivity = lambda x: x.CategoryOfFundingActivity.astype(str).astype('category'),
                    CategoryExplanation = lambda x: x.CategoryExplanation.astype(str).astype('category'),
                    EligibleApplicants = lambda x: x.EligibleApplicants.astype(str).astype('category'),
                    AdditionalInformationOnEligibility = lambda x: x.AdditionalInformationOnEligibility.astype(str),
                    AgencyCode = lambda x: x.AgencyCode.astype(str).astype('category'),
                    AgencyName = lambda x: x.AgencyName.astype(str).astype('category'),
                    ExpectedNumberOfAwards = lambda x: x.ExpectedNumberOfAwards.astype(float).astype('Int32'),
                    Version = lambda x: x.Version.astype(str).astype('category'),
                    CostSharingOrMatchingRequirement = lambda x: x.CostSharingOrMatchingRequirement.astype(str).astype('category')     
                    ))          

del df
#%%
#An example of creating a data quality check and sending the results to the console for sharing
print(f'Number of unique agencies: {df_clean["AgencyName"].nunique()}')
# %%
#This prints out the number of null values and unique values in each column
#An example of creating simple data quality checks and sending the results to a text file for sharing
col = df_clean.columns

today = datetime.today()

#Send the print statements to a text file

#add today's date to the file name
filename = f"value_statements_{today.strftime('%Y%m%d')}.txt"

with open(filename, "a") as f:
    f.write(f'Date of extraction is {today.strftime("%m/%d/%Y")}\n')
    for c in col:
        f.write(f'There are {df_clean[c].isnull().sum()} null values in {c} column\n')
        f.write(f'There are {df_clean[c].nunique()} unique values in {c} column\n') 
        f.write('\n')

# %%
#this is the method to query the dataframe based on the column name and value
today = datetime.today()

DE = df_clean.query('AgencyName == "Department of Education" \
              and CloseDate >= @today')

#This is the method to format and sum the EstimatedTotalProgramFunding column
#and print the results to the console for easy sharing.
formatted_funding = "${:,.0f}".format(DE["EstimatedTotalProgramFunding"].sum())
print(f'There is a possible Estimated Total ProgramFunding of {formatted_funding} for the Department of Education available as of {today.strftime("%m/%d/%Y")}')

# %%
#Filter out all rows where the CloseDate is greater then today's date
#Group by AgencyName and sum the EstimatedTotalProgramFunding
#Sort the values in descending order

today = datetime.today()
agencies = df_clean \
            .query('CloseDate >= @today') \
            .groupby('AgencyName') \
            .agg({'EstimatedTotalProgramFunding': 'sum'}) \
            .sort_values(by='EstimatedTotalProgramFunding', ascending=False) \
            .reset_index() \
            .assign(in_MM = lambda x: x.EstimatedTotalProgramFunding/1000000) 
            
agencies = agencies[agencies['EstimatedTotalProgramFunding'] > 0]

agencies

# %%

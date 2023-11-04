
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

The code is written by Andrew Walker
Aew5044@gmail.com

'''
# %%
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import zipfile
import os
#https://www.grants.gov/xml-extract.html website reference

#%%
# Your provided function
def xml_to_df(file_path):
    # Parse the XML file
    tree = ET.parse(file_path)
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
zip_path = r"C:\Users\aew50\Downloads\GrantsDBExtract{}.zip".format(today_date)

# Download the ZIP file content
response = requests.get(url)
if response.status_code == 200:
    # Save the content to a local ZIP file
    with open(zip_path, 'wb') as f:
        f.write(response.content)

    # Extract the XML file from the ZIP archive
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Assuming the XML file inside the ZIP has a predictable name
        xml_file_name = f"GrantsDBExtract{today_date}v2.xml"
        z.extract(xml_file_name, r"C:\Python\xml")

    # Now use your provided function to read the XML into a DataFrame
    xml_file_path = os.path.join(r"C:\Python\xml", xml_file_name)
    df = xml_to_df(xml_file_path)
    print(df)

else:
    print(f"Failed to download file. HTTP Status Code: {response.status_code}")

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

for c in col:
    print(f'There are {df_clean[c].isnull().sum()} null values in {c} column') 
    print(f'There are {df_clean[c].nunique()} unique values in {c} column')

    #Send the print statements to a text file
    with open(r"value_statements.txt", "a") as f:
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
            
agencies = agencies[agencies['EstimatedTotalProgramFunding'] > 0]

agencies

# %%

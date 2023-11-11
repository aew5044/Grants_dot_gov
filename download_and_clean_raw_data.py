
from datetime import datetime
import zipfile
import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd


def global_variables():
    today_date = datetime.today().strftime('%Y%m%d')
    url = f"https://prod-grants-gov-chatbot.s3.amazonaws.com/extracts/GrantsDBExtract{today_date}v2.zip"
    return url, today_date


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

def download(url, py_space, download_space, today_date):
    xml_file_name = f"GrantsDBExtract{today_date}v2.xml"
    xml_file_path = os.path.join(py_space, xml_file_name)

    zip_file_name = f"GrantsDBExtract{today_date}v2.zip"
    download_file_path = os.path.join(download_space, zip_file_name)
    zip_path = download_file_path

    # Check if the zip file exists
    if not os.path.exists(download_file_path):
        print('Downloading zip file')
        response = requests.get(url)
        if response.status_code == 200:
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extract(xml_file_name, py_space)
    else:
        print('Zip file was already downloaded for today')

    # Check if the XML file exists after extraction
    if not os.path.exists(xml_file_path):
        if os.path.exists(zip_path):
            print('Extracting XML file')
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extract(xml_file_name, py_space)
        else:
            print("Zip file not found.")
            return None
    else:
        print('XML file already exists')

    # Now use your provided function to read the XML into a DataFrame
    df = xml_to_df(xml_file_path)
    return df


def clean_df(df):
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
    return df_clean
    

def create_log_file(df_clean, today, col):
    #add today's date to the file name
    filename = f"value_statements_{today.strftime('%Y%m%d')}.txt"

    with open(filename, "a") as f:
        f.write(f'Date of extraction is {today.strftime("%m/%d/%Y")}\n')
        for c in col:
            f.write(f'There are {df_clean[c].isnull().sum()} null values in {c} column\n')
            f.write(f'There are {df_clean[c].nunique()} unique values in {c} column\n') 
            f.write('\n')

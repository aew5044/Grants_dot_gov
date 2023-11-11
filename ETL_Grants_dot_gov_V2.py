
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
# %%

download_space = r"C:\Users\aew50\Downloads"
py_space = r"C:\Python\Grants_dot_gov"
import pandas as pd
import plotly.express as px
# import requests
# import xml.etree.ElementTree as ET
from datetime import datetime
# import zipfile
# import os

#User defined functions
from download_and_clean_raw_data import global_variables, download, clean_df

df_clean = None
#%%

def main():
    # Get the global variables
    url, today_date = global_variables()
    global df_clean
    df = download(url=url, py_space=py_space, download_space=download_space, today_date=today_date)
    if df_clean is None:
        df_clean = clean_df(df)
    else:
        print('clean_df already exists')

if __name__ == "__main__":
    main()

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

# Load the dataset
file_path = r"C:\Python\Grants_dot_gov\GrantsDBExtract20211006v2.csv"  # Update with the path to your data file
grants_data = pd.read_csv(file_path)

# Convert CloseDate to datetime and calculate the number of days from today
grants_data['CloseDate'] = pd.to_datetime(grants_data['CloseDate'], errors='coerce')
today = datetime.now()
grants_data['DaysUntilClose'] = (grants_data['CloseDate'] - today).dt.days

# # Handle NaN values in 'EstimatedTotalProgramFunding'
filtered_data = grants_data.dropna(subset=['EstimatedTotalProgramFunding'])

# Group by AgencyName and sum the EstimatedTotalProgramFunding, then take the top 20
top_agencies = filtered_data.groupby('AgencyName')['EstimatedTotalProgramFunding'].sum().nlargest(20).index

# Filter the dataset for only these top agencies
filtered_data = filtered_data[filtered_data['AgencyName'].isin(top_agencies)].query('CloseDate >= @today')    
filtered_data2 = filtered_data[filtered_data['DaysUntilClose'] > 0]

# Create the bubble plot with the adjusted data
fig = px.scatter(
    filtered_data2,
    x="DaysUntilClose",
    y="ExpectedNumberOfAwards",
    size="EstimatedTotalProgramFunding",
    color="AgencyName",
    hover_name="AgencyName",
    size_max=60,
    title="Bubble Plot of Grant Opportunities by Top Funding Agencies"
)

fig.show()

# %%

fig.write_html("Bubble.html")  # Replace with your desired file path
#%%

# %%

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, paragraph    
from reportlab.lib.units import inch
#%%
#Create a PDF witht the title "My Title"

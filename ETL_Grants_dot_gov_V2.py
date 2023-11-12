
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

#User defined functions
from download_and_clean_raw_data import global_variables, download, clean_df, create_line_chart, create_pdf

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

    create_line_chart(df_clean, today_date)

    create_pdf(df_clean, today_date)

if __name__ == "__main__":
    main()


# %%

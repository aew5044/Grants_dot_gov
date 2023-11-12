
from datetime import datetime
import zipfile
import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib as mpl

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Image



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

def create_line_chart(df_clean, today_date):
    # Set the default font to Arial or a similar sans-serif font
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = 'Arial'

    # Assuming df_clean has CloseDate and EstimatedTotalProgramFunding columns
    # Convert CloseDate to month and filter for the next 12 months
    df_clean['Month'] = df_clean['CloseDate'].dt.to_period('M')
    next_12_months = pd.period_range(start=datetime.now(), periods=12, freq='M')
    df_clean = df_clean[df_clean['Month'].isin(next_12_months)]

    # Group by month and sum the funding
    monthly_funding = df_clean.groupby('Month')['EstimatedTotalProgramFunding'].sum()

    # Convert funding to millions for the Y axis
    monthly_funding_in_millions = monthly_funding / 1e6

    # Plotting
    plt.figure(figsize=(6, 2))  # Adjust the size to fit 1/3rd of the PDF page height
    plt.plot(monthly_funding_in_millions.index.astype(str), monthly_funding_in_millions.values, 
            marker='', linestyle='-', linewidth=1)
    plt.xticks(rotation=45)
    plt.xlabel('Month')
    plt.ylabel('In Million')
    plt.title('Estimated Total Program Funding')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.tight_layout()

    # Save the plot as an image
    plt.savefig('line_chart.png')
    plt.close()

def create_pdf(df_clean, today):

    DE = df_clean.query('AgencyName == "Department of Education" \
              and CloseDate >= @today')

    #This is the method to format and sum the EstimatedTotalProgramFunding column
    #and print the results to the console for easy sharing.
    formatted_funding = "${:,.0f}".format(DE["EstimatedTotalProgramFunding"].sum())

    # Define the PDF file name
    filename = "Current_Opportunities.pdf"

    # Create a canvas
    c = canvas.Canvas(filename, pagesize=letter)

    # Define title and sub-header
    title = "Current Opportunities"
    today_date = datetime.now().strftime("%B %d, %Y")  # Date in long format

    # Add title and sub-header to the canvas
    c.setFont("Helvetica-Bold", 16)
    c.drawString(inch, 10*inch, title)
    c.setFont("Helvetica", 12)
    c.drawString(inch, 9.75*inch, today_date)

    # Create a paragraph with three generic sentences
    styles = getSampleStyleSheet()
    paragraph_text = (
        "In the realm of educational advancement, the Department of Education consistently offers a multitude of "
        "grant opportunities, aiming to foster innovation and progress in learning environments. Key values essential "
        "for the success of these grants include a deep commitment to educational equity, a thorough understanding of "
        "pedagogical best practices, and a strong alignment of project goals with the Department's vision. Currently, "
        f"there is a notable Estimated Total Program Funding of {formatted_funding}, accessible as of {today_date}, "
        "a testament to the Department's dedication to empowering educational initiatives. Successful grant applications "
        "typically demonstrate not only a robust educational impact but also a sustainable and scalable model, ensuring "
        "that the benefits of the grant extend beyond the immediate project scope and contribute meaningfully to the "
        "broader educational landscape."
    )
    paragraph = Paragraph(paragraph_text, style=styles["Normal"])

    # Draw the paragraph on the canvas
    paragraph.wrapOn(c, 6.5*inch, 9*inch)
    paragraph.drawOn(c, inch, 8*inch)

    chart_image = Image('line_chart.png')
    chart_image.drawHeight = 3*inch  # Adjust the height to 1/3rd of the page height
    chart_image.drawWidth = 7*inch  # Adjust the width to fit the page
    chart_image.wrapOn(c, 7.5*inch, 9*inch)
    chart_image.drawOn(c, inch, 5*inch)  # Adjust the position as needed

    # Additional paragraph text
    additional_paragraph_text = ("As we can see, there are millions of dollars in funding available for the next 12 months."
                                "The chart above shows the estimated total program funding by month for the next 12 months."
                                "The chart was created using Python and the Pandas and Matplotlib libraries."
                                "Contact us to learn more about how we can help you with your grant application.")

    # Create a Paragraph object with the additional paragraph
    additional_paragraph = Paragraph(additional_paragraph_text, style=styles["Normal"])

    # Draw the additional paragraph on the canvas
    additional_paragraph.wrapOn(c, 6.5*inch, 9*inch)
    additional_paragraph.drawOn(c, inch, 4*inch)  # Adjust the position as needed
    # Save the PDF
    c.save()


def create_bubble_plot():
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


def agencies(df_clean):
    today = datetime.today()
    agencies = df_clean \
                .query('CloseDate >= @today') \
                .groupby('AgencyName') \
                .agg({'EstimatedTotalProgramFunding': 'sum'}) \
                .sort_values(by='EstimatedTotalProgramFunding', ascending=False) \
                .reset_index() \
                .assign(in_MM = lambda x: x.EstimatedTotalProgramFunding/1000000) 
                
    agencies = agencies[agencies['EstimatedTotalProgramFunding'] > 0]

    return agencies

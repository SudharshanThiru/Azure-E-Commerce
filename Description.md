# **END-TO-END DATA ENGINEERING PROJECT**
## **Basic Project Description**

This end-to-end project aims at covering a variety of tools and services within Azure Cloud platform, Databricks and Snowflake.
It includes a complete Data Engineering module with the end goal as drawing insights with the data.

## **About the Dataset**

The dataset used is the retails_sales_dataset.csv. The link to the dataset can be found [here](https://www.kaggle.com/datasets/mohammadtalib786/retail-sales-dataset)
The dataset contains of 1000 entries with the following columns
    Transaction ID - Unique ID representing the transaction _Can be considered as the Primary Key_
    Date - Date of the transaction _Format: YYYY-MM-DD_
    Customer ID - Every customer has a unique ID _Format: CUST001_
    Gender - Male or Female
    Age - Age of the Customer
    Product Category - Different product categories
    Quantity - Amount of that particular product bought in that order
    Price per Unit - Price of 1 unit of that product
    Total Amount - Total price of the order

## Data Engineering

### Snowflake
The first step in the project was to upload the dataset into Snowflake. Snowflake is a data warehousing platform used to store large amounts of data, analyze and share it securely. 
Though our data was not a large scale dataset, this step is included to mimic an actual data engineering pipeline.
There are 2 methods to push the data into Snowflake
    1. Use the Snowflake CLI and SnowSQL to create a Database and push the data from local storage into the created DB
        The following dependencies have to be installed in order to perform that.
            Snowflake CLI   - [Link](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)
            SnowSQL         - [Link](https://docs.snowflake.com/en/user-guide/snowsql-install-config)
        In the CLI use the following command _snowsql -a ACCOUNTNUMBER -u USERNAME_ The ACCOUNTNUMBER and USERNAME can be found in the bottom-left of the webpage _Account >> View Account Details_
        In the webpage, head over to _Data_ and within that, create a new Database.
        Back in the CLI, use the command *PUT FILE ://FILEPATH @DATABASENAME AUTO_COMPRESS=TRUE*
        *THIS STEP DIDN'T WORK SO I MOVED TO METHOD 2*

    2. Manually uploading the file through the web-interface
        In the webpage, head over to _Data_ and within that, create a new Database.
        Within the new Database, create a new schema and within the schema create a new table.
        Load the data into the table and choose the right file format
        The column names shouldn't contain spaces, so correct them in the same interface by either adding '_' or removing the space
Test the data upload by going to *Projects >> Worksheets* and performing a simple SQL command

### Azure Services Used 
#### FunctionApp
Function Apps is a serverless compute service on Azure that allows you to run code without managing servers. It's event-driven, meaning functions are triggered by specific events like HTTP requests, timer events, or messages in a queue. 
We will be using the Function App to trigger a HTTP Request that will fetch the data from our Database in Snowflake and upload it into a storage container *This is the final destination for the data but there will be certain intermediate steps that will be covered*
We use the *Consumption* Plan to create the function app. The settings are as follows:
    OS - Windows 
    Runtime Stack - Powershell Core
    Version - 7.3 *Keep the latest version available*
    Storage - *Choose the default given storage*
Keep other specs as it is and create the functionapp

#### Event Hub
Event Hubs is a fully managed, real-time data ingestion service that allows you to stream millions of events per second from any source. It acts as a "front door" for an event pipeline, receiving data from producers and making it available for consumption by various analytics and storage services.
We will use the Event Hub as the starting point in our Azure Data pipeline to fetch the data into an Azure Storage Container. 
The Function App will connect the Snowflake Database and Event Hub, and migrate the data into the Event Hub when a HTTP Request is sent.
Steps to create an Event Hub Namespace
    Search Event Hub in the azure portal 
    Click on create to create a new Event Hub Namespace- Use the default settings for all 
    Once the resource is deployed, go into it and create a new eventhub within that 
        Cleanup policy is delete
        Partition count is 1
Within the namespace, get the connection string
    Head over to *Shared Access Policies*
    Click on *RootManageSharedAccessKey*
    Copy the *Connection String*

#### Stream Analytics 
Azure Stream Analytics is a fully managed, real-time analytics service that allows you to analyze and process high volumes of streaming data from various sources. It enables you to perform complex event processing, generate insights, and trigger actions based on real-time data streams.
We will be using Stream Analytics to fetch the data from Event Hub and store it in Blob.
We use this intermediate layer as blob cannot directly fetch data from Event Hubs, so stream analytics fetches it and stores in Blob.
Use all default settings for the Stream Analytics job and make sure you connect it to the same Resource Group all your other services are hosted in.

#### Azure Data Factory 
Azure Data Factory is a service used for creating, maintaining and monitoring Data pipelines. It is a useful service that helps automate ETL process. It can be run at specific times or when a new file is being uploaded to a source directory (event based trigger).
We will be using Data Factory to create a Data Flow and automate the process of transforming and cleaning the raw-data. 
We will be using a Medallion architecture to store the data in (Bronze-Silver-Gold)
Use all default settings for the Data Factory and make sure you connect it to the sam Resource Group all your other services are hosted in.

### Migrating Data 

Required keys 
    Snowflake
        Account Number
        Username
        Password
    Event Hub
        Event Hub Name - Not the namespace but the Event Hub Name
        Connection String

Create Variables for each of the above mentioned keys in Azure Function App
    Go into *Configuration >> Blue ribbon >>* that should take you into *Environment Variables*
    Create a variable for each of the above mentioned keys

[insert-image-here]

Run the script that sends out a HTTP Request
    Open up a new directory in your preferred IDE (I use VSCode)
    Download the following extensions
        Azure Functions
        Azure Resources 
    Create a .env file which contains the above mentioned keys. The script will be fetching the values from this file. File format
        Snowflake_User = "USERKEY"
        Snowflake_Password = "PASSWORD"
        .
        .
        .
    *Make sure to keep the variables names consistent with the names you are using in the python script*
    Run the python script provided *I have named it eventhub.py*

Once the script runs without any errors, check the Event Hub overview for the graphs. It should show the incoming messages spike. If you don't see any updates in the graph give it a few minutes and refresh it.

Transfer data from Event Hub to Blob Storage container
    Once you have confirmed the messages being received into Event Hubs, you can query the data into Blob with the help of Stream Analytics
    Head over to your Stream Analytics Service and within that *Job Topology >> Query*
    Create an input - your Event Hub and an output - the desired Blob Storage Container
    Now use the following query
        SELECT *
        INTO
            *output-blob*
        FROM
            *input-event-hub*
    Check the Stream Analytics metrics after a few minutes and you should be seeing the messages being transferred
    After 5 minutes or so, check your Blob Storage Container and you should see the JSON file inside

Data Pipeline 
    This is responsible for our bronze to silver layer transformations
    Head into the Data Factory and click on the *Author* Tab - the pencil icon
    Create a new Dataset that links to the raw-data we have in the Blob. 
    Create a new Dataflow with the *Source* being the Dataset that we just created in the previous step. 
        Disable sampling
        Allow Schema Drift
        Within *Projection* we are going to change the data types of certain columns
            Integer for Transaction_ID, Age, Price_per_Unit, Total_Amount, Quantity
            Date for Date
        Within *Data preview*, enable *Data Flow Debug* - Present on the top left of the Dataflow window and check if there are any errors present in the data.
            Sometimes, the data might not load, in such cases, hit refresh and switch to *Projections* tab and head back into the *Data Preview* and you will see the data.
    Create a *Derived Column* - This is used to create new custom columns. We will be creating 2 new columns
        1. CustDC - toInteger(substring(CUSTOMER_ID, 5, length(CUSTOMER_ID) - 4))
        2. GenderDC - lower(trim(GENDER))
    Create a *Select Column* - This is used for removing unwanted columns in the dataset. We will be removing the following columns (All these columns contain the metadata from the Event Hub ingestion time)
        1. EventProcessedUtcTime
        2. PartitionId
        3. EventEnqueuedUtcTime
    Create a *Sink*. This is where the processed data will be dumped into. 
        We will create a new *Dataset* that will point to the location of the target. 
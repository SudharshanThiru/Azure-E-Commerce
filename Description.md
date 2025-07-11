# **END-TO-END DATA ENGINEERING PROJECT**
## **Basic Project Description**

This end-to-end project aims at covering a variety of tools and services within Azure Cloud platform, Databricks and Snowflake.  It includes a complete Data Engineering module with the end goal as drawing insights with the data.

## **About the Dataset**

The dataset used is the `retails_sales_dataset.csv`. The link to the dataset can be found [here](https://www.kaggle.com/datasets/mohammadtalib786/retail-sales-dataset).  
The dataset contains 1000 entries with the following columns:

1. **Transaction ID** - Unique ID representing the transaction  
    _Can be considered as the Primary Key_

2. **Date** - Date of the transaction  
    _Format: YYYY-MM-DD_

3. **Customer ID** - Every customer has a unique ID  
    _Format: CUST001_

4. **Gender** - Male or Female

5. **Age** - Age of the Customer

6. **Product Category** - Different product categories

7. **Quantity** - Amount of that particular product bought in that order

8. **Price per Unit** - Price of 1 unit of that product

9. **Total Amount** - Total price of the order


## Data Engineering

### Snowflake

The first step in the project was to upload the dataset into **Snowflake**.  
Snowflake is a data warehousing platform used to store large amounts of data, analyze, and share it securely.  

Though our dataset isn't large-scale, this step is included to mimic a real-world data engineering pipeline.

There are **2 methods** to push the data into Snowflake:

---

#### 1. Using the Snowflake CLI and SnowSQL

This method involves using the command line to create a database and upload the data from local storage.

**Dependencies** (install these first):
- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)
- [SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config)

**Steps:**
- Open your CLI and run the command:  
  ```bash
  snowsql -a ACCOUNTNUMBER -u USERNAME
  ```
  - `ACCOUNTNUMBER` and `USERNAME` can be found in the bottom-left of the Snowflake webpage:  
    _Account → View Account Details_

- On the Snowflake web interface:
  - Go to the **Data** tab and create a **new Database**.

- Back in the CLI, run the command:
  ```bash
  PUT file://<FILEPATH> @<DATABASENAME> AUTO_COMPRESS=TRUE
  ```

> ⚠️ **Note**: This step didn’t work due to CLI/filepath issues, so I moved on to **Method 2**.

---

#### 2. Manually Uploading the File via Web Interface

**Steps:**
- On the Snowflake web interface:
  - Go to the **Data** tab and create a **new Database**.
  - Inside the database, create a **new Schema**, then create a **new Table**.
  - Upload the CSV file and choose the appropriate **file format**.
  - Ensure column names don't contain spaces. You can rename them in the upload interface using `_` or by removing spaces.

**To verify the upload:**
- Go to **Projects → Worksheets**
- Run a basic SQL query such as:
  ```sql
  SELECT * FROM your_table_name LIMIT 10;
  ```

 
### Azure Services Used

---

#### Function App

Function Apps is a **serverless compute service** on Azure that allows you to run code without managing servers.  
It's **event-driven**, meaning functions are triggered by specific events like HTTP requests, timer events, or messages in a queue.

In this project, the Function App is used to:
- Trigger an **HTTP request**
- Fetch data from the **Snowflake Database**
- Upload it to a **storage container**

> _This is the final destination for the data, but there are intermediate steps covered below._

**Function App Settings** (Consumption Plan):
- **OS**: Windows  
- **Runtime Stack**: PowerShell Core  
- **Version**: 7.3 _(Use the latest version available)_  
- **Storage**: Use the default suggested storage

Keep other specifications as default and proceed to create the Function App.

---

#### Event Hub

Event Hubs is a **fully managed, real-time data ingestion service** that allows you to stream millions of events per second.  
It acts as a **front door** for the event pipeline — receiving data from producers and exposing it to downstream consumers.

In this setup:
- Event Hub is the **starting point** in the Azure Data pipeline
- The **Function App connects Snowflake → Event Hub**
- Data is migrated into the Event Hub upon an HTTP trigger

**Steps to create an Event Hub Namespace**:
1. Search for **Event Hub** in the Azure Portal
2. Click **Create** to set up a new Event Hub Namespace  
   _Use default settings for all fields_
3. Once deployed:
    - Go into the resource
    - Create a **new Event Hub**
      - **Cleanup Policy**: Delete  
      - **Partition Count**: 1

**Get the Connection String**:
- Go to **Shared Access Policies**
- Click on **RootManageSharedAccessKey**
- Copy the **Connection String** for later use

---

#### Stream Analytics

Azure Stream Analytics is a **real-time analytics service** used to process and analyze large volumes of streaming data.

In this project:
- It pulls data **from Event Hub**
- Writes processed data **into Blob Storage**

> _This intermediate layer is necessary because Blob Storage cannot directly ingest data from Event Hubs._

**Configuration**:
- Use **default settings**
- Ensure the **Stream Analytics job** is in the **same Resource Group** as the rest of your services

---

#### Azure Data Factory

Azure Data Factory is a platform for building, managing, and monitoring **data pipelines**.  
It helps automate **ETL (Extract, Transform, Load)** processes and supports event-based triggers or scheduled runs.

In this project:
- Data Factory is used to create a **Data Flow** to transform and clean the raw data
- We follow a **Medallion Architecture**:  
  - **Bronze**: Raw data  
  - **Silver**: Cleaned data  
  - **Gold**: Curated analytics-ready data

**Configuration**:
- Use **default settings**
- Make sure it is linked to the **same Resource Group** as the other services

---

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

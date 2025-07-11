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

---

#### 🔑 Required Keys

**Snowflake**
- `Account Number`
- `Username`
- `Password`

**Event Hub**
- `Event Hub Name` (Note: **not** the namespace)
- `Connection String`

---

#### 🛠️ Configure Environment Variables in Function App

1. Go to your **Azure Function App**
2. Navigate to:  
   `Configuration → Application settings (Blue ribbon)`
3. Add a **new application setting** for each key mentioned above (Snowflake and Event Hub)

> Each key should be added as an environment variable.

📌 *Keep the variable names consistent with what is used in your Python script.*

---

#### 🧪 Run the Script to Trigger HTTP Request

1. Open a new directory in your preferred IDE (e.g., VS Code)
2. Install the following **extensions**:
   - Azure Functions
   - Azure Resources

3. Create a `.env` file to store your credentials and keys:
    ```env
    Snowflake_User="USERKEY"
    Snowflake_Password="PASSWORD"
    Snowflake_Account="ACCOUNTNUMBER"
    EventHub_Name="EVENTHUBNAME"
    EventHub_Connection="CONNECTIONSTRING"
    ```

4. Run the provided Python script (e.g., `eventhub.py`) to:
   - Connect to Snowflake
   - Fetch data
   - Send it to Event Hub

✅ Once the script runs successfully, check your **Event Hub → Overview tab**  
📊 You should see a spike in **incoming messages**. If not, wait a few minutes and refresh the graph.

---

#### 📥 Transfer Data from Event Hub to Blob Storage

1. Go to your **Stream Analytics Job**
2. Navigate to: `Job Topology → Query`
3. Configure your **input** as:
   - **Event Hub**

4. Configure your **output** as:
   - **Blob Storage Container**

5. Use the following query:
    ```sql
    SELECT *
    INTO [output-blob]
    FROM [input-event-hub]
    ```

6. Save and start the job.

📈 After a few minutes, check the **Stream Analytics metrics**.  
📁 Then check your **Blob Storage container** — the JSON file should be present.

---

#### 🧱 Data Pipeline: Bronze → Silver

This section handles **transforming raw data (Bronze) into cleaned data (Silver)** using Azure Data Factory.

1. Open **Azure Data Factory**
2. Go to the **Author tab** (🖉 Pencil icon)
3. Create a new **Dataset** pointing to the raw data in Blob Storage
4. Create a new **Data Flow**:
    - **Source**: The dataset you just created
    - Disable **sampling**
    - Enable **schema drift**

5. Under **Projection**, change the data types:
    - `Transaction_ID`, `Age`, `Price_per_Unit`, `Total_Amount`, `Quantity` → `Integer`
    - `Date` → `Date`

6. In **Data Preview**:
    - Enable **Data Flow Debug**
    - If data doesn't load, switch to **Projections**, then back to **Data Preview**

7. Add a **Derived Column** transformation:
    - `CustDC` → `toInteger(substring(CUSTOMER_ID, 5, length(CUSTOMER_ID) - 4))`
    - `GenderDC` → `lower(trim(GENDER))`

8. Add a **Select Column** transformation:
    - Remove these Event Hub metadata columns:
      - `EventProcessedUtcTime`
      - `PartitionId`
      - `EventEnqueuedUtcTime`

9. Add a **Sink**:
    - This is the output destination for your transformed data
    - Create a new **Dataset** pointing to the **target location**

---

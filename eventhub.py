import logging
import os
import json
import datetime
import azure.functions as func
import snowflake.connector
from azure.eventhub import EventData, EventHubProducerClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Custom serializer for datetime objects
def default_serializer(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return str(obj)

def fetch_and_send_data():
    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=os.environ["SnowFlake_User"],
            password=os.environ["SF_Password"],
            account=os.environ["SF_Account"],
            warehouse="COMPUTE_WH",
            database="RETAIL_SALES",
            schema="RICHA"
        )

        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tables available:", tables)

        # Fetch data
        cursor.execute("SELECT * FROM SALES")
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        logging.info(f"Fetched {len(rows)} rows from Snowflake.")

        # Create Event Hub producer
        producer = EventHubProducerClient.from_connection_string(
            conn_str=os.environ["Eventhub_connection_string"],
            eventhub_name=os.environ["Event_hub_name"]
        )

        event_data_batch = producer.create_batch()
        added = 0

        # Add messages to batch
        for row in rows:
            message = json.dumps(dict(zip(columns, row)), default=default_serializer)
            try:
                event_data_batch.add(EventData(message))
                added += 1
            except ValueError:
                logging.warning(f"Row too large. Skipped: {message}")

        # Send to Event Hub
        if added > 0:
            producer.send_batch(event_data_batch)
            logging.info(f"{added} messages sent to Event Hub.")
        else:
            logging.warning("No messages were sent. Batch was empty.")

        return True

    except Exception as e:
        logging.error(f"Error during send: {str(e)}")
        return False

# Azure Function HTTP trigger
def main(req: func.HttpRequest) -> func.HttpResponse:
    success = fetch_and_send_data()
    if success:
        return func.HttpResponse("Data sent to Event Hub successfully!")
    else:
        return func.HttpResponse("Failed to send data.", status_code=500)

# Local test entry point
if __name__ == "__main__":
    result = fetch_and_send_data()
    if result:
        print("✅ Data sent to Event Hub successfully!")
    else:
        print("❌ Failed to send data to Event Hub.")
import argparse
import logging
from concurrent import futures
from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists, GoogleAPICallError

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Test Pub/Sub publish and acknowledge flow.")
parser.add_argument("--project_id", required=True, help="GCP project ID")
parser.add_argument("--topic_id", required=True, help="Pub/Sub topic ID")
parser.add_argument("--subscription_id", required=True, help="Pub/Sub subscription ID")
args = parser.parse_args()

project_id = args.project_id
topic_id = args.topic_id
subscription_id = args.subscription_id

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Initialize Clients ---
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

topic_path = publisher.topic_path(project_id, topic_id)
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# --- Step 1: Ensure Subscription Exists ---
try:
    subscriber.create_subscription(name=subscription_path, topic=topic_path)
    logging.info(f"📬 Created subscription: {subscription_path}")
except AlreadyExists:
    logging.info(f"ℹ️ Subscription already exists: {subscription_path}")
except GoogleAPICallError as e:
    logging.error(f"❌ Failed to create subscription: {e.message}")
    exit(1)
except Exception as e:
    logging.error(f"❌ Unexpected error while creating subscription: {e}")
    exit(1)

# --- Step 2: Publish Messages ---
message_payloads = [f"Test message {i}" for i in range(10)]
publish_futures = []

def publish_callback(future: pubsub_v1.publisher.futures.Future, message_data: str):
    def callback(future: pubsub_v1.publisher.futures.Future):
        try:
            message_id = future.result(timeout=60)
            logging.info(f"✅ Published via [{topic_id}]: '{message_data}' (Message ID: {message_id})")
        except Exception as e:
            logging.error(f"❌ Failed to publish via [{topic_id}]: '{message_data}'. Reason: {e}")
    return callback

try:
    for message_data in message_payloads:
        future = publisher.publish(topic_path, message_data.encode("utf-8"))
        future.add_done_callback(publish_callback(future, message_data))
        publish_futures.append(future)

    futures.wait(publish_futures, return_when=futures.ALL_COMPLETED)
except Exception as e:
    logging.error(f"❌ Error during publishing messages: {e}")
    exit(1)

# --- Step 3: Subscribe & Acknowledge Messages ---
received_messages = []

def subscriber_callback(message: pubsub_v1.subscriber.message.Message):
    try:
        message_text = message.data.decode("utf-8")
        logging.info(f"📩 Acknowledged via [{subscription_id}]: '{message_text}'")
        message.ack()
        received_messages.append(message_text)

        if len(received_messages) >= len(message_payloads):
            streaming_pull_future.cancel()
    except Exception as e:
        logging.error(f"❌ Error processing message: {e}")

try:
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=subscriber_callback)
    logging.info("📡 Listening for messages...\n")
    streaming_pull_future.result(timeout=30)
except futures.TimeoutError:
    logging.warning("⏳ Subscriber timed out after 30 seconds.")
except GoogleAPICallError as e:
    logging.error(f"❌ Subscriber API error: {e.message}")
except Exception as e:
    logging.error(f"❌ Unexpected error while receiving messages: {e}")
finally:
    subscriber.close()

logging.info("✅ Finished: All messages published and acknowledged.")

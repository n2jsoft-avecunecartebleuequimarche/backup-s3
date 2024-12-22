import os
import time
import json
from .aws_client import AWSClient
from .sqs import SQS
from .s3 import S3
from .log import logger
from .graceful_killer import GracefulKiller
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from concurrent.futures import ThreadPoolExecutor

class App:

    def __init__(self):
        self.__download_path = os.getenv("DOWNLOAD_PATH", "/download")
        self.__metadata_path = os.getenv("METADATA_PATH", "/metadata")
        self.__max_retries = int(os.getenv("MAX_RETRIES", 3))
        self.max_workers = int(os.getenv("MAX_WORKERS", 5))

        self.__aws = AWSClient()
        self.__sqs = SQS(self.__aws.session, self.__aws.endpoint_url)
        self.__s3 = S3(self.__aws.session, self.__download_path, self.__metadata_path, self.__aws.endpoint_url)

        self.__metrics = {
            'MessagesProcessed': Counter('sqs_messages_processed_total', 'Total number of messages processed'),
            'MessagesWaiting': Gauge('sqs_messages_waiting', 'Approximate number of messages waiting in the queue'),
            'FailedMessages': Counter('sqs_failed_messages_total', 'Total number of failed messages'),
            'MessagesProcessingTime': Histogram('sqs_messages_processing_time_seconds', 'Time taken to process a message')
        }

    def run(self):
        start_http_server(8000)
        logger.info("Prometheus metrics server started on port 8000.")
        self._process_sqs_messages()

    def _process_sqs_messages(self):
        logger.info("Listening for messages in batches...")
        killer = GracefulKiller()

        # Thread pool for parallel message processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                if killer.kill_now:
                    break
                try:
                    # Update the number of messages in the queue
                    self.__metrics['MessagesWaiting'].set(self.__sqs.get_queue_attributes())

                    # Receive messages in a batch (long polling)
                    response = self.__sqs.get_messages()

                    if 'Messages' not in response:
                        logger.info("No messages received. Waiting...")
                        continue

                    logger.debug(f"Received {len(response['Messages'])} messages.")

                    # Submit tasks to process messages in parallel
                    futures = {
                        executor.submit(self._process_message, message): message
                        for message in response['Messages']
                    }

                    for future in as_completed(futures):
                        message = futures[future]
                        process_start = time.time()
                        try:
                            future.result()  # Wait for the task to complete
                        except Exception as e:
                            self.__metrics['FailedMessages'].inc()
                            logger.error(f"Failed to process message {message}: {e}")
                        finally:
                            processing_time = time.time() - process_start
                            self.__metrics['MessagesProcessingTime'].observe(processing_time)

                except Exception as e:
                    logger.error("Error receiving messages:", e)

    def _process_message(self, message):
        """Process a single SQS message."""
        try:
            # Parse the message body
            body = json.loads(message['Body'])
            logger.debug(f"Processing SQS Message: {body}")

            # Extract S3 event information
            s3_event = json.loads(body['Message']) if 'Message' in body else body
            if 'Records' in s3_event:
                s3_records = s3_event['Records']
                for record in s3_records:
                    bucket_name = record['s3']['bucket']['name']
                    object_key = record['s3']['object']['key']
                    logger.debug(f"Processing S3 object: {bucket_name}/{object_key}")

                    self._retry_operation(lambda: self.__s3.download_file(bucket_name, object_key), "Downloading file")
                    metadata = self._retry_operation(lambda: self.__s3.fetch_metadata_and_tags(bucket_name, object_key), "Fetching metadata and tags")
                    self._retry_operation(lambda: self.__s3.write_metadata_to_file(object_key, metadata), "Writing metadata file")

            # Delete the processed message
            self.__sqs.delete_message(message['ReceiptHandle'])
            self.__metrics['MessagesProcessed'].inc()
            logger.debug("Message processed and deleted from the queue.")
        except Exception as e:
            raise Exception(f"Error processing message: {e}")

    def _retry_operation(self, operation, description):
        """Retry an operation up to MAX_RETRIES times."""
        for attempt in range(1, self.__max_retries + 1):
            try:
                return operation()
            except ClientError as e:
                logger.error(f"Attempt {attempt}/{self.__max_retries} failed for {description}: {e}")
                if attempt == self.__max_retries:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

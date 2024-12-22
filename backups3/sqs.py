import time
import os
import sys
from prometheus_client import Counter, Gauge, Histogram
from .log import logger
from .exceptions import InitException
import botocore

class SQS:

    def __init__(self, session, endpoint_url=None):
        self.__queue_url = os.getenv("QUEUE_URL")
        if not self.__queue_url:
            raise InitException("QUEUE_URL environment variable is required.")
        self.__sqs_client = session.client('sqs', endpoint_url=endpoint_url)
        try:
            self.get_queue_attributes()
        except botocore.exceptions.ClientError as e:
            logger.error("Init failed to get queue attributes:", e)
            sys.exit(1)
        self.__max_number_of_messages = os.getenv("MAX_NUMBER_OF_MESSAGES", 10)
        self.__wait_time_seconds = os.getenv("WAIT_TIME_SECONDS", 20)

    def get_queue_attributes(self):
        """Get approximate number of messages in the queue."""
        attributes = self.__sqs_client.get_queue_attributes(
            QueueUrl=self.__queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(attributes.get('Attributes', {}).get('ApproximateNumberOfMessages', 0))

    def get_messages(self):
        """ Receive messages in a batch with long polling."""
        return self.__sqs_client.receive_message(
            QueueUrl=self.__queue_url,
            MaxNumberOfMessages=self.__max_number_of_messages,  # Batch size
            WaitTimeSeconds=self.__wait_time_seconds  # Long polling timeout
        )

    def delete_message(self, receipt_handle):
        """ Delete the processed message."""
        self.__sqs_client.delete_message(
            QueueUrl=self.__queue_url,
            ReceiptHandle=receipt_handle
        )

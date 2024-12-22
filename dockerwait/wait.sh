#!/bin/sh
URL="$ENDPOINT/?Action=GetQueueUrl&QueueName=$QUEUE"
echo "Waiting for SQS at address $URL, attempting every 5s"
until curl --silent --fail "$URL" | grep -q "${QUEUE}"; do
  sleep 5
done
echo "Success: Reached SQS"

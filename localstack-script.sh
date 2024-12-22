#!/bin/bash

awslocal s3api create-bucket --bucket mybucket --region us-east-1
awslocal sqs create-queue --queue-name myqueue --region us-east-1 --attributes DelaySeconds=10,ReceiveMessageWaitTimeSeconds=20
awslocal s3api put-bucket-notification-configuration --bucket mybucket --notification-configuration file:///etc/localstack/init/ready.d/notification.json

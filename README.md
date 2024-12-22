# backup-s3

App to backup s3 bucket to local storage from sqs messages.
Listen to sqs queue with long pulling and download s3 object to local storage.
Store also metadata of s3 object in json format (key, size, tag, last_modified).

# Environment Variables

| Name | Description | Required | Default |
|------|-------------|----------|---------|
| AWS_ACCESS_KEY_ID | AWS Access Key ID | Yes | "" |
| AWS_SECRET_ACCESS_KEY | AWS Secret Access Key | Yes | "" |
| AWS_DEFAULT_REGION | AWS Default Region | Yes | "" |
| ASSUME_ROLE_ARN | AWS Role ARN to assume | No | "" |
| AWS_PROFILE | AWS Profile to use | No | "" |
| QUEUE_URL | SQS Queue URL to watch for messages from s3 create event | Yes | "" |
| DOWNLOAD_PATH | Prefix path to download s3 object | No | "/download" |
| METADATA_PATH | Prefix path to store metadata of s3 object | No | "/metadata" |
| MAX_RETRIES   | Maximum number of retries to download and write s3 object | No | 3 |
| ENDPOINT_URL  | Endpoint URL for aws endpoint (localstack) | No | "" |
| LOG_LEVEL     | Log level for the app | No | "INFO" |
| MAX_NUMBER_OF_MESSAGES | Maximum number of messages to fetch from sqs | No | 10 |
| WAIT_TIME_SECONDS | Wait time for long polling | No | 20 |

# Requirements

* localstack
* awslocal
* docker-compose & docker
* jq
* curl

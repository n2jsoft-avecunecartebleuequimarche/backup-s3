import boto3
from botocore.credentials import DeferredRefreshableCredentials
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from .log import logger


class AWSClient:
    def __init__(self):
        self.__endpoint_url = os.getenv("ENDPOINT_URL", None)
        self.__role_arn = os.getenv("ASSUME_ROLE_ARN", None)
        self.__session = self.initialize_session()

    @property
    def session(self):
        return self.__session

    @property
    def endpoint_url(self):
        return self.__endpoint_url

    def assume_role(self, session_name="BackupProcessingSession"):
        """
        Assume the role specified in the ASSUME_ROLE_ARN environment variable.
        """
        sts_client = boto3.client("sts")
        response = sts_client.assume_role(
            RoleArn=self.__role_arn, RoleSessionName=session_name
        )
        credentials = response["Credentials"]
        return {
            "aws_access_key_id": credentials["AccessKeyId"],
            "aws_secret_access_key": credentials["SecretAccessKey"],
            "aws_session_token": credentials["SessionToken"],
            "expiration": credentials["Expiration"],
        }

    def initialize_session(self):
        """
        Initialize a boto3 session with the specified role if ASSUME_ROLE_ARN is set.
        """
        try:
            if self.__role_arn:
                logger.debug(f"Assuming role: ${self.__role_arn}")
                refreshable_credentials = DeferredRefreshableCredentials(
                    method="assume_role",
                    refresh_using=self.get_fresh_credentials(),
                    time_to_live=3600,
                )
                session = boto3.Session(
                    aws_access_key_id=refreshable_credentials.access_key,
                    aws_secret_access_key=refreshable_credentials.secret_key,
                    aws_session_token=refreshable_credentials.token,
                )
            else:
                session = boto3.Session()
            return session
        except NoCredentialsError as e:
            logger.error("AWS credentials not found:", e)
            raise e
        except PartialCredentialsError as e:
            logger.error("Incomplete AWS credentials:", e)
            raise e

    def get_fresh_credentials(self):
        """
        Returns a function that will be used by `DeferredRefreshableCredentials`
        to get new credentials when the current ones expire.
        """

        def refresh():
            logger.debug("Refreshing credentials")
            # Re-assume the role to get new credentials
            new_credentials = self.assume_role()
            return {
                "access_key": new_credentials["AccessKeyId"],
                "secret_key": new_credentials["SecretAccessKey"],
                "token": new_credentials["SessionToken"],
                "expiry_time": new_credentials["Expiration"].isoformat(),
            }

        return refresh

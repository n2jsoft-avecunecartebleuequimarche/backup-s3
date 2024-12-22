import os
import time
import json
from prometheus_client import Counter, Gauge
from .log import logger
from pathlib import Path


class S3:
    def __init__(self, session, download_path, metadata_path, endpoint_url=None):
        self.__s3_client = session.client("s3", endpoint_url=endpoint_url)
        self.__download_path = download_path
        self.__metadata_path = metadata_path
        self.__metrics = {
            "BytesDownloadedTotal": Counter(
                "s3_bytes_downloaded_total", "Total number of bytes downloaded from S3"
            ),
            "DownloadRate": Gauge(
                "s3_download_rate_bytes_per_second",
                "Rate of bytes downloaded per second",
            ),
        }

    def download_file(self, bucket_name, object_key):
        """
        Download a file from S3 while tracking the bytes downloaded and rate.
        """
        file_path = os.path.join(self.__download_path, object_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        start_time = time.time()
        try:
            # Download the file and calculate its size
            self.__s3_client.download_file(bucket_name, object_key, file_path)
            file_size = os.path.getsize(file_path)  # Get file size in bytes

            # Update Prometheus metrics
            self.__metrics["BytesDownloadedTotal"].inc(file_size)
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                rate = file_size / elapsed_time
                self.__metrics["DownloadRate"].set(rate)

            logger.debug(
                f"File downloaded: {file_path} ({file_size} bytes at {rate:.2f} bytes/second)"
            )
        except Exception as e:
            logger.error("Failed to download file:", e)
            raise

    def fetch_metadata_and_tags(self, bucket_name, object_key):
        """Fetch metadata and tags for an S3 object."""
        metadata_response = self.__s3_client.head_object(
            Bucket=bucket_name, Key=object_key
        )
        metadata = metadata_response.get("Metadata", {})
        size = metadata_response.get("ContentLength", 0)
        last_modified = metadata_response.get("LastModified", "").isoformat()

        tags_response = self.__s3_client.get_object_tagging(
            Bucket=bucket_name, Key=object_key
        )
        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("TagSet", [])}

        return {
            "metadata": metadata,
            "tags": tags,
            "size": size,
            "last_modified": last_modified,
        }

    def write_metadata_to_file(self, object_key, metadata):
        """Write metadata and tags to a JSON file."""
        object_key_json = Path(object_key).with_suffix(".json")
        metadata_file = os.path.join(self.__metadata_path, object_key_json)
        os.makedirs(os.path.dirname(metadata_file), exist_ok=True)

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)
        logger.debug(f"Metadata file created: {metadata_file}")

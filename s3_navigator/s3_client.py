"""S3 client wrapper for interacting with AWS S3."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3  # type: ignore
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError


class S3Client:
    """Client for interacting with AWS S3 services."""

    def __init__(self, profile: Optional[str] = None, region: str = "eu-central-1") -> None:
        """Initialize the S3 client.

        Args:
            profile: AWS profile name to use for authentication
            region: AWS region to use
        """
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.client = self.session.client("s3")
        self.region = region

    @property
    def access_key_id(self) -> Optional[str]:
        """Return the AWS Access Key ID used by the session, if available."""
        try:
            credentials = self.session.get_credentials()
            if credentials:
                # get_frozen_credentials() ensures we get a static snapshot
                frozen_creds = credentials.get_frozen_credentials()
                return frozen_creds.access_key
        except Exception:
            # If there's any issue getting credentials (e.g., not configured)
            pass
        return None

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets.

        Returns:
            List of bucket dictionaries, an error dictionary if an error occurs, or an info dictionary if no buckets are found.
        """
        try:
            response = self.client.list_buckets()
            buckets_data = response.get("Buckets", [])

            if not buckets_data:  # No buckets returned by the API call
                return [
                    {
                        "type": "INFO",
                        "name": "No Buckets Found",
                        "message": "Either no S3 buckets exist for the current AWS profile/region, or the credentials lack permission to list them.",
                        "size": 0,
                        "last_modified": datetime.now(timezone.utc),
                    }
                ]
            
            buckets = []
            for bucket in buckets_data:
                buckets.append(
                    {
                        "name": bucket["Name"],
                        "type": "BUCKET",
                        "size": -1,  # Mark as not calculated yet
                        "last_modified": bucket["CreationDate"],
                    }
                )
            return buckets
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            error_code = "N/A"
            error_message = str(e)
            if isinstance(e, ClientError):
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
            
            return [
                {
                    "type": "ERROR",
                    "name": f"Error Listing Buckets: {error_code}",
                    "message": error_message,
                    "size": 0,
                    "last_modified": datetime.now(timezone.utc),
                }
            ]

    def list_objects(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List objects in the specified bucket with prefix.

        Args:
            bucket: The name of the S3 bucket
            prefix: The prefix to filter objects by

        Returns:
            List of objects with metadata, or an error dictionary if an error occurs.
        """
        result = []
        directories = set()

        try:
            # Add '..' directory if we're in a subdirectory
            if prefix:
                result.append(
                    {
                        "name": "..",
                        "type": "DIR",
                        "size": 0,
                        "last_modified": datetime.now(timezone.utc),
                    }
                )

            paginator = self.client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")

            for page in page_iterator:
                # Handle directories (CommonPrefixes)
                for common_prefix in page.get("CommonPrefixes", []):
                    dir_name = common_prefix["Prefix"].rstrip("/").split("/")[-1]
                    if dir_name and dir_name not in directories:
                        directories.add(dir_name)
                        result.append(
                            {
                                "name": dir_name,
                                "type": "DIR",
                                "size": -1, # Mark as not calculated yet
                                "last_modified": datetime.now(timezone.utc),  # Directories don't have a last modified time
                            }
                        )

                # Handle files (Contents)
                for content in page.get("Contents", []):
                    # Skip the directory marker if present
                    key = content["Key"]
                    if key == prefix or key.endswith("/"):
                        continue

                    # Get just the filename without the prefix
                    name = key[len(prefix) :]

                    # Skip if the file is actually in a subdirectory
                    if "/" in name:
                        continue

                    result.append(
                        {
                            "name": name,
                            "type": "FILE",
                            "size": content["Size"],
                            "last_modified": content["LastModified"],
                        }
                    )
            return result
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            error_code = "N/A"
            error_message = str(e)
            if isinstance(e, ClientError):
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
            
            # Return the error as a list containing a single error dictionary
            # This matches the structure expected by the navigator and display logic
            return [
                {
                    "type": "ERROR",
                    "name": f"Error accessing {bucket}/{prefix or ''}: {error_code}",
                    "message": error_message,
                    "size": 0,
                    "last_modified": datetime.now(timezone.utc),
                }
            ]

    def _calculate_directory_size(self, bucket: str, prefix: str) -> int:
        """Calculate the total size of a directory.

        Args:
            bucket: The name of the S3 bucket
            prefix: The directory prefix

        Returns:
            Total size in bytes
        """
        total_size = 0
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in page_iterator:
            for content in page.get("Contents", []):
                total_size += content["Size"]

        return total_size

    def collect_objects_for_deletion(self, bucket: str, prefix: str) -> tuple[list[str], int]:
        """Collect all objects under a prefix (directory) and return their keys and total size."""
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
        keys = []
        total_size = 0
        for page in page_iterator:
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
                total_size += obj["Size"]
        return keys, total_size

    def get_object_metadata(self, bucket: str, key: str) -> dict:
        """Get metadata for a single object."""
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return {"Size": response.get("ContentLength", 0)}
        except Exception:
            return {}

    def delete_object(self, bucket: str, key: str, log_callback=None) -> None:
        """Delete an object from S3. If key ends with '/', delete all objects with this prefix (recursive)."""
        if key.endswith("/") or key == "":
            # It's a directory, delete all objects with this prefix
            self._delete_directory(bucket, key, log_callback=log_callback)
        else:
            # It's a single object
            self.client.delete_object(Bucket=bucket, Key=key)
            if log_callback:
                log_callback(f"Deleted object: s3://{bucket}/{key}")

    def _delete_directory(self, bucket: str, prefix: str, log_callback=None) -> None:
        """Delete all objects with a specific prefix (directory)."""
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        delete_list = []
        total_deleted = 0
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    delete_list.append({"Key": obj["Key"]})

                    # Delete in batches of 1000 (S3 limit)
                    if len(delete_list) >= 1000:
                        self.client.delete_objects(
                            Bucket=bucket, Delete={"Objects": delete_list}
                        )
                        total_deleted += len(delete_list)
                        if log_callback:
                            log_callback(f"Deleted batch of {len(delete_list)} objects from s3://{bucket}/{prefix}")
                        delete_list = []

        # Delete any remaining objects
        if delete_list:
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": delete_list})
            total_deleted += len(delete_list)
            if log_callback:
                log_callback(f"Deleted final batch of {len(delete_list)} objects from s3://{bucket}/{prefix}")
        if log_callback:
            log_callback(f"Total deleted from s3://{bucket}/{prefix}: {total_deleted} objects.")

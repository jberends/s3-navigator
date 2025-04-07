"""S3 client wrapper for interacting with AWS S3."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3


class S3Client:
    """Client for interacting with AWS S3 services."""

    def __init__(self, profile: Optional[str] = None, region: str = "eu-central-1"):
        """Initialize the S3 client.

        Args:
            profile: AWS profile name to use for authentication
            region: AWS region to use
        """
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.client = self.session.client("s3")
        self.region = region

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all available S3 buckets.

        Returns:
            List of bucket objects with metadata
        """
        response = self.client.list_buckets()
        buckets = []

        for bucket in response.get("Buckets", []):
            buckets.append(
                {
                    "name": bucket["Name"],
                    "type": "BUCKET",
                    "size": 0,  # Buckets don't have a size
                    "last_modified": bucket.get("CreationDate", datetime.now()),
                }
            )

        return buckets

    def list_objects(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List objects in the specified bucket with prefix.

        Args:
            bucket: The name of the S3 bucket
            prefix: The prefix to filter objects by

        Returns:
            List of objects with metadata
        """
        result = []
        directories = set()

        # Add '..' directory if we're in a subdirectory
        if prefix:
            result.append(
                {
                    "name": "..",
                    "type": "DIR",
                    "size": 0,
                    "last_modified": datetime.now(),
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
                            "size": self._calculate_directory_size(
                                bucket, common_prefix["Prefix"]
                            ),
                            "last_modified": datetime.now(),  # Directories don't have a last modified time
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

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete an object from S3.

        Args:
            bucket: The name of the S3 bucket
            key: The object key to delete
        """
        if key.endswith("/"):
            # It's a directory, delete all objects with this prefix
            self._delete_directory(bucket, key)
        else:
            # It's a single object
            self.client.delete_object(Bucket=bucket, Key=key)

    def _delete_directory(self, bucket: str, prefix: str) -> None:
        """Delete all objects with a specific prefix (directory).

        Args:
            bucket: The name of the S3 bucket
            prefix: The directory prefix to delete
        """
        # List all objects with the prefix
        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        delete_list = []
        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    delete_list.append({"Key": obj["Key"]})

                    # Delete in batches of 1000 (S3 limit)
                    if len(delete_list) >= 1000:
                        self.client.delete_objects(
                            Bucket=bucket, Delete={"Objects": delete_list}
                        )
                        delete_list = []

        # Delete any remaining objects
        if delete_list:
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": delete_list})

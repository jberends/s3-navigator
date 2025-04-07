"""Tests for the S3 client module."""

import unittest
from datetime import datetime
from unittest import mock

from botocore.stub import Stubber

from s3_navigator.s3_client import S3Client


class TestS3Client(unittest.TestCase):
    """Test cases for the S3Client class."""

    def setUp(self):
        """Set up test fixtures."""
        self.s3_client = S3Client(region="us-east-1")
        self.stubber = Stubber(self.s3_client.client)

    def test_list_buckets(self):
        """Test listing buckets."""
        # Prepare mock response
        mock_response = {
            "Buckets": [
                {"Name": "test-bucket-1", "CreationDate": datetime(2021, 1, 1)},
                {"Name": "test-bucket-2", "CreationDate": datetime(2021, 2, 1)},
            ],
            "Owner": {"DisplayName": "test-owner", "ID": "test-owner-id"},
        }
        self.stubber.add_response("list_buckets", mock_response, {})

        # Test the method
        with self.stubber:
            buckets = self.s3_client.list_buckets()

        # Check results
        self.assertEqual(len(buckets), 2)
        self.assertEqual(buckets[0]["name"], "test-bucket-1")
        self.assertEqual(buckets[0]["type"], "BUCKET")
        self.assertEqual(buckets[1]["name"], "test-bucket-2")

    def test_list_objects(self):
        """Test listing objects in a bucket."""
        bucket_name = "test-bucket"
        prefix = "test-prefix/"

        # Prepare mock response
        mock_response = {
            "Contents": [
                {
                    "Key": "test-prefix/test-file-1.txt",
                    "Size": 100,
                    "LastModified": datetime(2021, 1, 1),
                },
                {
                    "Key": "test-prefix/test-file-2.txt",
                    "Size": 200,
                    "LastModified": datetime(2021, 2, 1),
                },
            ],
            "CommonPrefixes": [
                {"Prefix": "test-prefix/test-dir-1/"},
                {"Prefix": "test-prefix/test-dir-2/"},
            ],
            "KeyCount": 4,
            "MaxKeys": 1000,
            "Delimiter": "/",
            "Prefix": prefix,
            "IsTruncated": False,
        }

        # Since we're mocking pagination, we need to use the actual response
        expected_params = {"Bucket": bucket_name, "Prefix": prefix, "Delimiter": "/"}

        # Use mock instead of stubber for paginator
        with mock.patch.object(
            self.s3_client.client, "get_paginator"
        ) as mock_paginator:
            mock_paginate = mock.MagicMock()
            mock_paginator.return_value.paginate.return_value = [mock_response]
            mock_paginator.return_value.paginate = mock_paginate

            # Also mock _calculate_directory_size to return a fixed value
            with mock.patch.object(
                self.s3_client, "_calculate_directory_size", return_value=1000
            ):
                objects = self.s3_client.list_objects(bucket_name, prefix)

        # Check results
        mock_paginate.assert_called_once_with(
            Bucket=bucket_name, Prefix=prefix, Delimiter="/"
        )

        # We should have 5 items (2 files + 2 directories + '..')
        self.assertEqual(len(objects), 5)

        # Check '..' directory is included
        self.assertEqual(objects[0]["name"], "..")
        self.assertEqual(objects[0]["type"], "DIR")

        # Check file items
        file_items = [item for item in objects if item["type"] == "FILE"]
        self.assertEqual(len(file_items), 2)
        self.assertEqual(file_items[0]["name"], "test-file-1.txt")
        self.assertEqual(file_items[0]["size"], 100)
        self.assertEqual(file_items[1]["name"], "test-file-2.txt")
        self.assertEqual(file_items[1]["size"], 200)

        # Check directory items
        dir_items = [
            item for item in objects if item["type"] == "DIR" and item["name"] != ".."
        ]
        self.assertEqual(len(dir_items), 2)
        self.assertEqual(dir_items[0]["name"], "test-dir-1")
        self.assertEqual(dir_items[0]["size"], 1000)  # Our mocked value
        self.assertEqual(dir_items[1]["name"], "test-dir-2")
        self.assertEqual(dir_items[1]["size"], 1000)  # Our mocked value

    def test_delete_object(self):
        """Test deleting a single object."""
        bucket_name = "test-bucket"
        key = "test-key.txt"

        # Prepare mock response for delete_object
        self.stubber.add_response(
            "delete_object", {}, {"Bucket": bucket_name, "Key": key}
        )

        # Test the method
        with self.stubber:
            self.s3_client.delete_object(bucket_name, key)

        # Stubber will assert the expected call was made

    def test_delete_directory(self):
        """Test deleting a directory (prefix)."""
        bucket_name = "test-bucket"
        prefix = "test-dir/"

        # Mock paginator for listing objects
        mock_list_response = {
            "Contents": [
                {"Key": "test-dir/file1.txt"},
                {"Key": "test-dir/file2.txt"},
                {"Key": "test-dir/subdir/file3.txt"},
            ]
        }

        # Mock response for delete_objects
        mock_delete_response = {
            "Deleted": [
                {"Key": "test-dir/file1.txt"},
                {"Key": "test-dir/file2.txt"},
                {"Key": "test-dir/subdir/file3.txt"},
            ]
        }

        # Use mock instead of stubber for paginator and delete_objects
        with mock.patch.object(
            self.s3_client.client, "get_paginator"
        ) as mock_paginator:
            mock_paginate = mock.MagicMock()
            mock_paginator.return_value.paginate.return_value = [mock_list_response]
            mock_paginator.return_value.paginate = mock_paginate

            with mock.patch.object(
                self.s3_client.client,
                "delete_objects",
                return_value=mock_delete_response,
            ) as mock_delete:
                self.s3_client.delete_object(bucket_name, prefix)

        # Check the right calls were made
        mock_paginate.assert_called_once_with(Bucket=bucket_name, Prefix=prefix)
        mock_delete.assert_called_once_with(
            Bucket=bucket_name,
            Delete={
                "Objects": [
                    {"Key": "test-dir/file1.txt"},
                    {"Key": "test-dir/file2.txt"},
                    {"Key": "test-dir/subdir/file3.txt"},
                ]
            },
        )

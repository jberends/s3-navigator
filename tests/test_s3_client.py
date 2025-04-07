"""Basic tests for the S3Client class."""

import unittest
from unittest import mock
from datetime import datetime

import boto3
from botocore.stub import Stubber

from s3_navigator.s3_client import S3Client


class TestS3Client(unittest.TestCase):
    """Test cases for the S3Client class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.client = S3Client(region="us-east-1")
        # Create a stubber for the boto3 client
        self.stubber = Stubber(self.client.client)

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        self.stubber.deactivate()

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values."""
        client = S3Client()
        self.assertEqual(client.region, "eu-central-1")
        self.assertIsNotNone(client.client)
        self.assertIsNotNone(client.session)

    def test_init_with_profile_and_region(self) -> None:
        """Test initialization with profile and region."""
        with mock.patch("boto3.Session") as mock_session:
            mock_session_instance = mock.MagicMock()
            mock_client = mock.MagicMock()
            mock_session_instance.client.return_value = mock_client
            mock_session.return_value = mock_session_instance

            client = S3Client(profile="test-profile", region="us-west-2")
            
            # Verify Session was created with correct parameters
            mock_session.assert_called_once_with(
                profile_name="test-profile", region_name="us-west-2"
            )
            self.assertEqual(client.region, "us-west-2")

    def test_list_buckets_empty(self) -> None:
        """Test listing buckets when there are none."""
        # Define the expected response
        response = {"Buckets": []}
        
        # Add the expected API call
        self.stubber.add_response("list_buckets", response)
        
        # Activate the stubber
        self.stubber.activate()
        
        # Call the method and check the result
        buckets = self.client.list_buckets()
        self.assertEqual(len(buckets), 0)
        
        # Verify all expected API calls were made
        self.stubber.assert_no_pending_responses()

    def test_list_buckets_with_data(self) -> None:
        """Test listing buckets with sample data."""
        # Sample creation date
        creation_date = datetime.now()
        
        # Define the expected response
        response = {
            "Buckets": [
                {"Name": "test-bucket-1", "CreationDate": creation_date},
                {"Name": "test-bucket-2", "CreationDate": creation_date},
            ]
        }
        
        # Add the expected API call
        self.stubber.add_response("list_buckets", response)
        
        # Activate the stubber
        self.stubber.activate()
        
        # Call the method and check the result
        buckets = self.client.list_buckets()
        
        # Verify the result
        self.assertEqual(len(buckets), 2)
        self.assertEqual(buckets[0]["name"], "test-bucket-1")
        self.assertEqual(buckets[0]["type"], "BUCKET")
        self.assertEqual(buckets[0]["size"], 0)
        self.assertEqual(buckets[0]["last_modified"], creation_date)
        self.assertEqual(buckets[1]["name"], "test-bucket-2")
        
        # Verify all expected API calls were made
        self.stubber.assert_no_pending_responses()

    def test_list_objects_root(self) -> None:
        """Test listing objects at the root of a bucket."""
        # Mock the _calculate_directory_size method to avoid additional API calls
        with mock.patch.object(self.client, "_calculate_directory_size", return_value=1000):
            # Define the expected response for list_objects_v2
            last_modified = datetime.now()
            response = {
                "Contents": [
                    {
                        "Key": "file1.txt",
                        "Size": 1024,
                        "LastModified": last_modified,
                    },
                    {
                        "Key": "file2.txt",
                        "Size": 2048,
                        "LastModified": last_modified,
                    },
                ],
                "CommonPrefixes": [
                    {"Prefix": "folder1/"},
                    {"Prefix": "folder2/"},
                ],
            }
            
            # Add the expected API call
            self.stubber.add_response(
                "list_objects_v2",
                response,
                {"Bucket": "test-bucket", "Prefix": "", "Delimiter": "/"},
            )
            
            # Activate the stubber
            self.stubber.activate()
            
            # Call the method
            objects = self.client.list_objects("test-bucket")
            
            # Verify the result
            self.assertEqual(len(objects), 4)  # 2 files + 2 folders
            
            # Check files
            file_objects = [obj for obj in objects if obj["type"] == "FILE"]
            self.assertEqual(len(file_objects), 2)
            self.assertEqual(file_objects[0]["name"], "file1.txt")
            self.assertEqual(file_objects[0]["size"], 1024)
            self.assertEqual(file_objects[1]["name"], "file2.txt")
            self.assertEqual(file_objects[1]["size"], 2048)
            
            # Check folders
            folder_objects = [obj for obj in objects if obj["type"] == "DIR"]
            self.assertEqual(len(folder_objects), 2)
            self.assertEqual(folder_objects[0]["name"], "folder1")
            self.assertEqual(folder_objects[1]["name"], "folder2")
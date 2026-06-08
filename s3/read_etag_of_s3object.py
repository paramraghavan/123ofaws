#!/usr/bin/env python3
"""
S3 ETag Reading and Verification - Production-Ready Implementation

This module provides complete utilities for working with S3 ETags:
- Read ETags from S3 objects
- Verify file uploads (simple and multipart)
- Detect file changes over time
- Track uploads in databases
- Production-grade error handling

Author: AWS Developer
Version: 1.0.0
Last Updated: 2026-05-28
"""

import hashlib
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class ETagReader:
    """Read and analyze S3 object ETags"""

    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize ETag reader

        Args:
            region: AWS region (default: us-east-1)
        """
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)

    def get_etag(self, bucket: str, key: str) -> Optional[str]:
        """
        Get ETag for an S3 object without downloading it

        Args:
            bucket: S3 bucket name
            key: Object key (path)

        Returns:
            ETag string (without quotes), or None if error

        Example:
            >>> reader = ETagReader()
            >>> etag = reader.get_etag('my-bucket', 'documents/report.pdf')
            >>> print(etag)
            '5d41402abc4b2a76b9719d911017c592'
        """
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            etag = response['ETag'].strip('"')
            return etag
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"❌ Object not found: s3://{bucket}/{key}")
            elif error_code == 'AccessDenied':
                print(f"❌ Access denied to s3://{bucket}/{key}")
            else:
                print(f"❌ Error reading ETag: {error_code}")
            return None
        except NoCredentialsError:
            print("❌ AWS credentials not found")
            return None

    def is_multipart(self, etag: str) -> bool:
        """
        Check if ETag represents a multipart upload

        Multipart ETags contain a hyphen followed by part count:
        - Simple upload: "5d41402abc4b2a76b9719d911017c592"
        - Multipart: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"

        Args:
            etag: ETag string

        Returns:
            True if multipart, False if simple

        Example:
            >>> reader = ETagReader()
            >>> reader.is_multipart("9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5")
            True
            >>> reader.is_multipart("5d41402abc4b2a76b9719d911017c592")
            False
        """
        return '-' in etag

    def get_part_count(self, etag: str) -> Optional[int]:
        """
        Get number of parts for multipart upload

        Args:
            etag: ETag string

        Returns:
            Number of parts, or None if simple upload

        Example:
            >>> reader = ETagReader()
            >>> reader.get_part_count("9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5")
            5
        """
        if '-' in etag:
            try:
                return int(etag.split('-')[-1])
            except (ValueError, IndexError):
                return None
        return None

    def analyze_etag(self, bucket: str, key: str) -> Dict:
        """
        Complete ETag analysis for an object

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            Dictionary with analysis results

        Example:
            >>> reader = ETagReader()
            >>> analysis = reader.analyze_etag('my-bucket', 'data.zip')
            >>> print(analysis)
            {
                'etag': '9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5',
                'is_multipart': True,
                'part_count': 5,
                'upload_type': 'Multipart (5 parts)',
                'size': 524288000,
                'last_modified': datetime(...)
            }
        """
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            etag = response['ETag'].strip('"')
            is_multipart = self.is_multipart(etag)
            part_count = self.get_part_count(etag) if is_multipart else None

            upload_type = (
                f"Multipart ({part_count} parts)" if is_multipart
                else "Simple (single upload)"
            )

            return {
                'etag': etag,
                'is_multipart': is_multipart,
                'part_count': part_count,
                'upload_type': upload_type,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            print(f"❌ Error analyzing ETag: {e.response['Error']['Code']}")
            return None


class UploadVerifier:
    """Verify S3 uploads using ETags and metadata"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize upload verifier"""
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        self.reader = ETagReader(region)

    @staticmethod
    def calculate_local_md5(file_path: str) -> Optional[str]:
        """
        Calculate MD5 hash of a local file

        Args:
            file_path: Path to local file

        Returns:
            MD5 hash as hex string, or None if error

        Example:
            >>> md5 = UploadVerifier.calculate_local_md5('report.pdf')
            >>> print(md5)
            '5d41402abc4b2a76b9719d911017c592'
        """
        try:
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return None
        except IOError as e:
            print(f"❌ Error reading file: {e}")
            return None

    def verify_simple_upload(self, bucket: str, key: str, local_file: str) -> bool:
        """
        Verify a small file upload by comparing local MD5 to S3 ETag

        ✓ Works only for simple uploads (< 100 MB)
        ✓ Fast and reliable for small files
        ✗ Does NOT work for multipart uploads

        Args:
            bucket: S3 bucket name
            key: Object key in S3
            local_file: Path to local file

        Returns:
            True if verified, False otherwise

        Example:
            >>> verifier = UploadVerifier()
            >>> if verifier.verify_simple_upload('my-bucket', 'report.pdf', 'report.pdf'):
            ...     print("Upload is good!")
            ... else:
            ...     print("Upload verification failed!")
        """
        print(f"\n📋 Verifying simple upload: {key}")

        # Step 1: Calculate local MD5
        local_md5 = self.calculate_local_md5(local_file)
        if not local_md5:
            return False

        # Step 2: Get S3 ETag
        s3_etag = self.reader.get_etag(bucket, key)
        if not s3_etag:
            return False

        # Step 3: Check if multipart
        if self.reader.is_multipart(s3_etag):
            print(f"⚠️  Warning: Object is multipart upload!")
            print(f"    Cannot verify with simple MD5 comparison")
            print(f"    ETag: {s3_etag}")
            print(f"    This doesn't mean upload failed - just can't verify")
            return False

        # Step 4: Compare
        print(f"  Local MD5: {local_md5}")
        print(f"  S3 ETag:   {s3_etag}")

        if s3_etag == local_md5:
            print(f"  ✅ MATCH - Upload verified!")
            return True
        else:
            print(f"  ❌ MISMATCH - Upload verification failed!")
            return False

    def verify_by_size(self, bucket: str, key: str, expected_size: int) -> bool:
        """
        Verify upload by checking file size (works for all upload types)

        ✓ Works for simple AND multipart uploads
        ✓ Fast and reliable

        Args:
            bucket: S3 bucket name
            key: Object key
            expected_size: Expected file size in bytes

        Returns:
            True if size matches, False otherwise

        Example:
            >>> verifier = UploadVerifier()
            >>> file_size = os.path.getsize('large-archive.zip')
            >>> if verifier.verify_by_size('my-bucket', 'archive.zip', file_size):
            ...     print("Size verified!")
        """
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            actual_size = response['ContentLength']

            print(f"\n📏 Verifying file size: {key}")
            print(f"  Expected: {expected_size:,} bytes")
            print(f"  Actual:   {actual_size:,} bytes")

            if actual_size == expected_size:
                print(f"  ✅ Size verified!")
                return True
            else:
                print(f"  ❌ Size mismatch!")
                return False
        except ClientError as e:
            print(f"❌ Error: {e.response['Error']['Code']}")
            return False

    def verify_by_metadata(self, bucket: str, key: str, expected_md5: str) -> bool:
        """
        Verify upload by checking stored custom metadata

        ✓ Works for simple AND multipart uploads
        ✓ Most reliable method for large files

        Requires file uploaded with metadata:
            ExtraArgs={'Metadata': {'original-md5': md5_value}}

        Args:
            bucket: S3 bucket name
            key: Object key
            expected_md5: Expected MD5 value

        Returns:
            True if metadata MD5 matches, False otherwise

        Example:
            >>> verifier = UploadVerifier()
            >>> md5 = UploadVerifier.calculate_local_md5('archive.zip')
            >>> if verifier.verify_by_metadata('my-bucket', 'archive.zip', md5):
            ...     print("Metadata verified!")
        """
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            metadata = response.get('Metadata', {})
            stored_md5 = metadata.get('original-md5')

            print(f"\n🔐 Verifying stored metadata: {key}")
            print(f"  Expected MD5: {expected_md5}")
            print(f"  Stored MD5:   {stored_md5}")

            if not stored_md5:
                print(f"  ⚠️  No 'original-md5' in metadata")
                return False

            if stored_md5 == expected_md5:
                print(f"  ✅ Metadata verified!")
                return True
            else:
                print(f"  ❌ Metadata mismatch!")
                return False
        except ClientError as e:
            print(f"❌ Error: {e.response['Error']['Code']}")
            return False


class ChangeDetector:
    """Detect file changes using ETags"""

    def __init__(self, region: str = 'us-east-1'):
        """Initialize change detector"""
        self.region = region
        self.reader = ETagReader(region)

    def detect_change(self, bucket: str, key: str, last_known_etag: str) -> Tuple[bool, Optional[str]]:
        """
        Check if file changed since last known ETag

        ✓ Works for simple AND multipart uploads
        ✓ Fast way to detect modifications

        Args:
            bucket: S3 bucket name
            key: Object key
            last_known_etag: Previous ETag value

        Returns:
            Tuple of (changed: bool, current_etag: str or None)

        Example:
            >>> detector = ChangeDetector()
            >>> stored_etag = "5d41402abc4b2a76b9719d911017c592"
            >>> changed, new_etag = detector.detect_change('my-bucket', 'config.json', stored_etag)
            >>> if changed:
            ...     print(f"File changed! New ETag: {new_etag}")
        """
        current_etag = self.reader.get_etag(bucket, key)

        if current_etag is None:
            return False, None

        print(f"\n🔍 Detecting changes: {key}")
        print(f"  Previous ETag: {last_known_etag}")
        print(f"  Current ETag:  {current_etag}")

        changed = current_etag != last_known_etag

        if changed:
            print(f"  ⚠️  File has changed!")
            return True, current_etag
        else:
            print(f"  ✅ File unchanged")
            return False, current_etag


class UploadTracker:
    """Track uploads using ETags and DynamoDB"""

    def __init__(self, region: str = 'us-east-1', table_name: Optional[str] = None):
        """
        Initialize upload tracker

        Args:
            region: AWS region
            table_name: DynamoDB table name (optional - for tracking)
        """
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        self.reader = ETagReader(region)
        self.table_name = table_name

        if table_name:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=region)
                self.table = dynamodb.Table(table_name)
            except Exception as e:
                print(f"⚠️  Could not connect to DynamoDB table: {e}")
                self.table = None
        else:
            self.table = None

    def get_upload_info(self, bucket: str, key: str) -> Optional[Dict]:
        """
        Get complete upload information

        Args:
            bucket: S3 bucket name
            key: Object key

        Returns:
            Dictionary with upload metadata

        Example:
            >>> tracker = UploadTracker()
            >>> info = tracker.get_upload_info('my-bucket', 'report.pdf')
            >>> print(f"ETag: {info['etag']}")
            >>> print(f"Size: {info['size']} bytes")
        """
        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)
            analysis = self.reader.analyze_etag(bucket, key)

            upload_info = {
                'bucket': bucket,
                'key': key,
                'etag': analysis['etag'],
                'is_multipart': analysis['is_multipart'],
                'part_count': analysis['part_count'],
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'timestamp': datetime.utcnow().isoformat(),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'metadata': response.get('Metadata', {})
            }

            return upload_info
        except ClientError as e:
            print(f"❌ Error getting upload info: {e.response['Error']['Code']}")
            return None

    def track_upload(self, bucket: str, key: str, local_file: str) -> Optional[Dict]:
        """
        Upload file and track in DynamoDB (if table configured)

        Args:
            bucket: S3 bucket name
            key: Object key
            local_file: Path to local file

        Returns:
            Upload info dictionary

        Example:
            >>> tracker = UploadTracker(table_name='UploadTracking')
            >>> info = tracker.track_upload('my-bucket', 'report.pdf', 'report.pdf')
            >>> if info:
            ...     print(f"Upload tracked with ETag: {info['etag']}")
        """
        print(f"\n📤 Uploading and tracking: {key}")

        try:
            # Upload file
            self.s3.upload_file(local_file, bucket, key)
            print(f"  ✅ Upload complete")

            # Get upload info
            upload_info = self.get_upload_info(bucket, key)

            if upload_info and self.table:
                # Track in DynamoDB
                try:
                    self.table.put_item(Item=upload_info)
                    print(f"  ✅ Tracked in DynamoDB")
                except Exception as e:
                    print(f"  ⚠️  Could not track in DynamoDB: {e}")

            return upload_info

        except ClientError as e:
            print(f"❌ Upload failed: {e.response['Error']['Code']}")
            return None


# ============================================================================
# EXAMPLES - Show how to use all the classes
# ============================================================================

def example_1_basic_etag_reading():
    """Example 1: Read ETag from S3 object"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic ETag Reading")
    print("="*60)

    reader = ETagReader()

    # Get ETag
    etag = reader.get_etag('my-bucket', 'documents/report.pdf')

    if etag:
        # Analyze it
        is_multipart = reader.is_multipart(etag)
        part_count = reader.get_part_count(etag)

        print(f"\nETag: {etag}")
        print(f"Is Multipart: {is_multipart}")
        if is_multipart:
            print(f"Part Count: {part_count}")


def example_2_verify_simple_upload():
    """Example 2: Verify simple file upload"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Verify Simple Upload")
    print("="*60)

    verifier = UploadVerifier()

    # Upload local file to S3
    local_file = 'report.pdf'
    bucket = 'my-bucket'
    key = 'documents/report.pdf'

    # Verify by MD5 (works for small files)
    verifier.verify_simple_upload(bucket, key, local_file)


def example_3_verify_large_file():
    """Example 3: Verify large file upload"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Verify Large File Upload")
    print("="*60)

    verifier = UploadVerifier()

    local_file = 'large-archive.zip'
    bucket = 'my-bucket'
    key = 'archives/large-archive.zip'

    # Verify by size (works for all upload types)
    file_size = os.path.getsize(local_file)
    verifier.verify_by_size(bucket, key, file_size)


def example_4_detect_changes():
    """Example 4: Detect file changes"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Detect File Changes")
    print("="*60)

    detector = ChangeDetector()

    # Store ETag from first check
    stored_etag = "5d41402abc4b2a76b9719d911017c592"
    bucket = 'my-bucket'
    key = 'config.json'

    # Later, check if changed
    changed, new_etag = detector.detect_change(bucket, key, stored_etag)

    if changed:
        print(f"\n⚠️  File was modified!")
    else:
        print(f"\n✅ File unchanged")


def example_5_track_upload():
    """Example 5: Track upload with metadata"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Track Upload")
    print("="*60)

    tracker = UploadTracker(table_name='UploadTracking')

    local_file = 'report.pdf'
    bucket = 'my-bucket'
    key = 'documents/report.pdf'

    # Upload and track
    info = tracker.track_upload(bucket, key, local_file)

    if info:
        print(f"\n📊 Upload Info:")
        print(f"  ETag: {info['etag']}")
        print(f"  Size: {info['size']:,} bytes")
        print(f"  Type: {info['is_multipart'] and 'Multipart' or 'Simple'}")


if __name__ == '__main__':
    """
    Run examples (uncomment to test)

    Note: These examples require AWS credentials configured
    """

    # example_1_basic_etag_reading()
    # example_2_verify_simple_upload()
    # example_3_verify_large_file()
    # example_4_detect_changes()
    # example_5_track_upload()

    print("\n✅ Module ready. Import and use the classes above.")
    print("See examples above for usage patterns.")

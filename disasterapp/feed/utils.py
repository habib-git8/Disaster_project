# import boto3
# import logging
# from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# def create_bucket(bucket_name, region="us-east-1"):
#     """Create an S3 bucket if it does not already exist."""
#     try:
#         s3_client = boto3.client('s3', region_name=region)
#         s3_client.create_bucket(
#             Bucket=bucket_name,
#             CreateBucketConfiguration={'LocationConstraint': region}
#         )
#         print(f"Bucket '{bucket_name}' created successfully!")
#     except s3_client.exceptions.BucketAlreadyExists:
#         print(f"Bucket '{bucket_name}' already exists.")
#     except s3_client.exceptions.BucketAlreadyOwnedByYou:
#         print(f"Bucket '{bucket_name}' already owned by you.")
#     except NoCredentialsError:
#         print("AWS credentials not found. Please configure your credentials.")
#     except PartialCredentialsError:
#         print("Incomplete AWS credentials. Please check your credentials.")

# def upload_receipt(file_name, bucket, object_key=None):
#     """Uploads a receipt (file) to an S3 bucket."""
    
#     if object_key is None:
#         object_key = file_name

#     s3_client = boto3.client('s3')

#     try:
#         s3_client.upload_file(file_name, bucket, object_key)
#         print(f"Receipt uploaded successfully: s3://{bucket}/{object_key}")
#         return f"https://{bucket}.s3.amazonaws.com/{object_key}"
#     except NoCredentialsError:
#         print("AWS credentials not found. Please configure your credentials.")
#         return None
#     except PartialCredentialsError:
#         print("Incomplete AWS credentials. Please check your credentials.")
#         return None
# def list_receipts(bucket):
#     """Lists all receipt files in the S3 bucket."""
#     s3_client = boto3.client('s3')
    
#     try:
#         response = s3_client.list_objects_v2(Bucket=bucket)
#         if 'Contents' in response:
#             print("Receipts in bucket:")
#             for obj in response['Contents']:
#                 print(f"- {obj['Key']}")
#         else:
#             print("No receipts found.")
#     except NoCredentialsError:
#         print("AWS credentials not found. Please configure your credentials.")
#     except PartialCredentialsError:
#         print("Incomplete AWS credentials. Please check your credentials.")

# def download_receipt(bucket, object_key, destination_file):
#     """Downloads a receipt from S3."""
#     s3_client = boto3.client('s3')
    
#     try:
#         s3_client.download_file(bucket, object_key, destination_file)
#         print(f"Receipt downloaded successfully: {destination_file}")
#     except NoCredentialsError:
#         print("AWS credentials not found. Please configure your credentials.")
#     except PartialCredentialsError:
#         print("Incomplete AWS credentials. Please check your credentials.")

import boto3
import logging
import os
from botocore.exceptions import NoCredentialsError, ClientError

def create_s3_bucket(bucket_name, region="us-east-1"):
    """
    Creates an S3 bucket if it does not already exist.
    """
    s3_client = boto3.client("s3", region_name=region)
    
    try:
        # Check if bucket already exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        # If bucket does not exist, create it
        if e.response["Error"]["Code"] == "404":
            try:
                if region == "us-east-1":
                    s3_client.create_bucket(Bucket=bucket_name)
                else:
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )
                print(f"Bucket '{bucket_name}' created successfully.")
            except ClientError as e:
                print(f"Error creating bucket: {e}")
                return False
        else:
            print(f"Error checking bucket: {e}")
            return False
    return True


def upload_to_s3(file_path, bucket_name, object_key):
    """
    Uploads a file to an S3 bucket.
    """
    s3_client = boto3.client('s3')

    try:
        s3_client.upload_file(file_path, bucket_name, object_key)
        print(f"File uploaded successfully to {bucket_name}/{object_key}")
        return True
    except NoCredentialsError:
        print("AWS credentials not found.")
        return False
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generates a pre-signed URL for a file in S3.
    :param bucket_name: S3 bucket name
    :param object_key: S3 file path
    :param expiration: URL expiry time in seconds (default 1 hour)
    :return: Pre-signed URL (string) or None if error occurs
    """
    s3_client = boto3.client('s3')

    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        return presigned_url
    except ClientError as e:
        print(f"Error generating pre-signed URL: {e}")
        return None

# Load AWS credentials from environment variables or IAM roles
sns_client = boto3.client("sns", region_name="us-east-1")  

# Use your existing SNS topic ARN
TOPIC_ARN = "arn:aws:sns:us-east-1:592027060252:DisasterAlerts"

def create_sns_topic(topic_name="DisasterAlerts"):
    """Creates an SNS topic if it doesn’t exist and returns the topic ARN."""
    response = sns_client.create_topic(Name=topic_name)
    topic_arn = response["TopicArn"]
    print(f"✅ SNS Topic Created: {topic_arn}")
    return topic_arn

def subscribe_to_topic(email, topic_name="DisasterAlerts"):
    """Subscribes an email to the SNS topic."""
    topic_arn = create_sns_topic(topic_name)
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol="email",
        Endpoint=email,
    )
    print(f"✅ Subscription Pending. Confirm in {email}")
    return response["SubscriptionArn"]



def publish_to_topic(subject, message):
    """Publishes a message to the existing SNS topic."""
    try:
        response = sns_client.publish(
            TopicArn=TOPIC_ARN,
            Message=message,
            Subject=subject,
        )
        print(f"✅ SNS Message Published. Message ID: {response['MessageId']}")
        return response["MessageId"]
    except Exception as e:
        logging.error(f"❌ Error publishing to SNS: {e}")  # Log the error
        return None


import boto
import boto3
import boto.s3
from botocore.exceptions import ClientError
import io
import sys
from boto.s3.key import Key

AWS_ACCESS_KEY_ID = 'AKIAZC6GESDLWR3JRDV4'
AWS_SECRET_ACCESS_KEY = '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'
s3_client=boto3.client('s3', region_name='eu-west-2',aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def upload_my_file(bucket, folder, file_as_binary, file_name):
     file_as_binary = io.BytesIO(file_as_binary)
     key = folder + "/" + file_name
     try:
         s3_client.upload_fileobj(file_as_binary, bucket, key)
     except ClientError as e:
         print(e)
         return False
     return True

#get file as binary
file_binary = open(r"jan-dec-morocco-12pm.csv", "rb").read()
# #uploading file
upload_my_file("renanalyst-bucket", "text-data", file_binary, "jan-dec-morocco-12pm.csv")


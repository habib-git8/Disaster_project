# from django.db import models
# from django.contrib.auth.models import User



# class DisasterPost(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)  
#     # user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     location = models.CharField(max_length=255)
#     donation_required = models.IntegerField(default=0)  
#     donation_received = models.IntegerField(default=0) 
#     image = models.ImageField(upload_to='static/images', blank=True, null=True)  # Store images
#     created_at = models.DateTimeField(auto_now_add=True)  # Auto timestamp
#     user_email = models.EmailField(max_length=255, null=True, blank=True) 

#     def __str__(self):
#         return self.title
#     @property
#     def donation_progress(self):
#         if self.donation_required > 0:
#             return int((self.donation_received / self.donation_required) * 100)
#         return 0

#     @property
#     def remaining_donation(self):
#         return max(self.donation_required - self.donation_received, 0)
    
# class Donation(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(DisasterPost, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
#     created_at = models.DateTimeField(auto_now_add=True)


# import boto3
# import uuid
# from django.db import models
# from django.contrib.auth.models import User
# from django.conf import settings
# from django.core.files.storage import default_storage
# from django.conf import settings

# # Initialize DynamoDB resource
# # dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)

# # Define table names (ensure these tables exist in AWS DynamoDB)
# dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)

# # Initialize S3 client
# # s3_client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

# DISASTER_POSTS_TABLE = "DisasterPosts"
# DONATIONS_TABLE = "Donations"


# class DisasterPost(models.Model):
#     id = models.CharField(max_length=255, primary_key=True, default=uuid.uuid4)  # Unique identifier
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     location = models.CharField(max_length=255)
#     donation_required = models.IntegerField(default=0)
#     donation_received = models.IntegerField(default=0)
#     # image_url = models.URLField(max_length=1024, blank=True, null=True)
#     # image = models.ImageField(upload_to="uploads/", blank=True, null=True)  # Upload image
#     # image_url = models.URLField(max_length=1024, blank=True, null=True)  # Store S3 image URL
#     image = models.ImageField(upload_to="static/images", blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
#     user_email = models.EmailField(max_length=255, null=True, blank=True)

#     def save(self, *args, **kwargs):
#         """Override save method to upload image to S3 and store data in DynamoDB"""
#         # if self.image:
#         #     image_name = f"disaster_images/{self.id}.jpg"

#             # Upload image to S3
#             # s3_client.upload_fileobj(self.image, settings.AWS_STORAGE_BUCKET_NAME, image_name, ExtraArgs={'ACL': 'public-read'})

#             # # Generate public S3 URL
#             # self.image_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{image_name}"

#         # Store data in DynamoDB
#         table = dynamodb.Table(DISASTER_POSTS_TABLE)
#         table.put_item(
#             Item={
#                 'id': str(self.id),
#                 'user_id': str(self.user.id),
#                 'title': self.title,
#                 'description': self.description,
#                 'location': self.location,
#                 'donation_required': self.donation_required,
#                 'donation_received': self.donation_received,
#                 # 'image_url': self.image_url,
#                 'created_at': self.created_at.isoformat() if self.created_at else None,
#                 'user_email': self.user_email
#             }
#         )
#         return super().save(*args, **kwargs)

#     def delete(self, *args, **kwargs):
#         """Override delete method to remove entry from DynamoDB and delete image from S3"""
#         table = dynamodb.Table(DISASTER_POSTS_TABLE)
#         table.delete_item(Key={'id': str(self.id)})

#         # Delete image from S3
#         # if self.image_url:
#         #     image_name = self.image_url.split("/")[-1]  # Extract the filename
#         #     s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"disaster_images/{image_name}")

#         return super().delete(*args, **kwargs)

#     @property
#     def donation_progress(self):
#         if self.donation_required > 0:
#             return int((self.donation_received / self.donation_required) * 100)
#         return 0

#     @property
#     def remaining_donation(self):
#         return max(self.donation_required - self.donation_received, 0)

#     def __str__(self):
#         return self.title


# class Donation(models.Model):
#     id = models.CharField(max_length=255, primary_key=True, default=uuid.uuid4)  # Unique identifier
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(DisasterPost, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
#     created_at = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         """ Override save method to store data in DynamoDB instead of SQL database """
#         table = dynamodb.Table(DONATIONS_TABLE)

#         table.put_item(
#             Item={
#                 'id': str(self.id),
#                 'user_id': str(self.user.id),
#                 'post_id': str(self.post.id),
#                 'amount': str(self.amount),  # Store as string since DynamoDB doesn't support Decimal
#                 'payment_status': self.payment_status,
#                 'created_at': self.created_at.isoformat() if self.created_at else None            }
#         )
#         return super().save(*args, **kwargs)

#     def delete(self, *args, **kwargs):
#         """ Override delete method to remove entry from DynamoDB """
#         table = dynamodb.Table(DONATIONS_TABLE)
#         table.delete_item(Key={'id': str(self.id)})
#         return super().delete(*args, **kwargs)

#     def __str__(self):
#         return f"Donation {self.id} - {self.amount}"

import uuid
from django.db import models
from django.contrib.auth.models import User
from .utils import publish_to_topic
from django.dispatch import receiver
from django.db.models.signals import post_save

class DisasterPost(models.Model):
     # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    donation_required = models.IntegerField(default=0)
    donation_received = models.IntegerField(default=0)
    image = models.ImageField(upload_to="static/images", blank=True, null=True)  # Upload image locally
    created_at = models.DateTimeField(auto_now_add=True)
    user_email = models.EmailField(max_length=255, null=True, blank=True)

    @property
    def donation_progress(self):
        if self.donation_required > 0:
            return int((self.donation_received / self.donation_required) * 100)
        return 0

    @property
    def remaining_donation(self):
        return max(self.donation_required - self.donation_received, 0)

    def __str__(self):
        return self.title
    
@receiver(post_save, sender=DisasterPost)
def send_disaster_notification(sender, instance, created, **kwargs):
    if created:
        subject = "🚨 Disaster Alert: " + instance.title
        message = f"🚨 **New Disaster Reported** 🚨\n\n📍 Location: {instance.location}\n📝 Details: {instance.description}\n\nStay Safe!"
        publish_to_topic(subject, message)  # Send SNS Notification


class Donation(models.Model):
    # Unique identifier
    # id = models.AutoField(primary_key=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(DisasterPost, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Completed', 'Completed')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Donation {self.id} - {self.amount}"


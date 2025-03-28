import paypalrestsdk
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import MyForm
from .models import DisasterPost, Donation
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm , CustomUserCreationForm
from .forms import DonationForm
from django.conf import settings
from django.core.mail import EmailMessage
from .receipt_generator.generate_receipt import generate_donation_receipt
from django.http import FileResponse, HttpResponseNotFound
from django.http import HttpResponseRedirect, HttpResponseNotFound
import os
import uuid
from .utils import upload_to_s3, generate_presigned_url, create_s3_bucket
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
def home(request):
    return render(request, 'feed/home.html')

def profile(request):
    return render(request, 'feed/profile.html')
def donation(request):
    posts= DisasterPost.objects.all().order_by('-created_at')
    for post in posts:
        # Convert values to integers to avoid type errors
        donation_required = int(post.donation_required) if post.donation_required else 0
        donation_received = int(post.donation_received) if post.donation_received else 0

    return render(request, 'feed/donation.html', {'posts': posts})

def donation_page(request, post_id):
    post = get_object_or_404(DisasterPost, id=post_id)

    # Always initialize the form, whether it's a GET or POST request
    form = DonationForm()

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']

            # Ensure donation does not exceed remaining amount
            if amount > post.remaining_donation:
                messages.error(request, "You cannot donate more than the remaining amount!")
                return redirect('donation_page', post_id=post.id)

            # ✅ Update donation_received
            post.donation_received += amount
            post.save()

            messages.success(request, f"Thank you for donating ${amount}!")
            return redirect('feed')  # Redirect back to feed after donation

    # Render the donation page with the form
    return render(request, 'feed/donation_page.html', {'post': post, 'form': form})
def feed(request):
    posts = DisasterPost.objects.all().order_by('-created_at')  # Show latest posts first
    return render(request, 'feed/feed.html', {'posts': posts})
def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")  # Redirect to login after signup
    else:
        form = CustomUserCreationForm()
    return render(request, "feed/signup.html", {"form": form})

# Login View
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("feed")  # Redirect to feed after login
        else:
            return render(request, "feed/login.html", {"error": "Invalid credentials"})
    return render(request, "feed/login.html")

# Logout View
@login_required
def user_logout(request):
    logout(request)
    return redirect("login")


@login_required
def create_post(request):
    if request.method == "POST":
        form = MyForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)  
            post.user = request.user  # Set the user before saving
            post.save()
            return redirect('feed')  # Redirect to feed after posting
            
    else:
        form = MyForm()
    
    return render(request, 'feed/contact.html', {'form': form})


@login_required
def update_post(request, post_id):
    post = get_object_or_404(DisasterPost, id=post_id, user=request.user)  # Ensure only owner can edit
    if request.method == "POST":
        form = MyForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('feed')
    else:
        form = MyForm(instance=post)
    
    return render(request, 'feed/update_post.html', {'form': form})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(DisasterPost, id=post_id, user=request.user)
    if request.method == "POST":
        post.delete()
        return redirect('feed')
    
    return render(request, 'feed/delete_post.html', {'post': post})


@login_required
def paypalpayment(request, post_id):
    post = get_object_or_404(DisasterPost, id=post_id)

    if request.method == "POST":
        amount = request.POST.get('amount')

        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0 or amount > post.remaining_donation:
                raise ValueError("Invalid donation amount.")
        except (ValueError, TypeError):
            return render(request, 'feed/donation_page.html', {"post": post, "error": "Invalid donation amount."})

        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": request.build_absolute_uri('/paypal-success/'),
                "cancel_url": request.build_absolute_uri('/paypal-cancel/')
            },
            "transactions": [{
                "amount": {"total": str(amount), "currency": "USD"},
                "description": f"Donation for {post.title}"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    
                    # Generate a UUID for donation ID
                    donation = Donation.objects.create(
                        id=uuid.uuid4(),  # Ensure UUID is used
                        user=request.user,
                        post=post,
                        amount=amount,
                        payment_status="Pending"
                    )

                    request.session['donation_id'] = str(donation.id)  # Store as string
                    return redirect(approval_url)

        return render(request, 'feed/donation_page.html', {"post": post, "error": "Payment creation failed. Try again."})

    return render(request, 'feed/donation_page.html', {"post": post})
# def paypalpayment(request, post_id):
    post = get_object_or_404(DisasterPost, id=post_id)
    if request.method == "POST":
        amount = request.POST.get('amount')
        
        if not amount or float(amount) > post.remaining_donation:
            return render(request, 'donation_page.html', {"post": post, "error": "Invalid donation amount."})
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri('/paypal-success/'),
                "cancel_url": request.build_absolute_uri('/paypal-cancel/')
            },
            "transactions": [{
                "amount": {
                    "total": str(amount),
                    "currency": "USD"
                },
                "description": f"Donation for {post.title}"
            }]
        })

        if payment.create():
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    donation = Donation.objects.create(user=request.user, post=post, amount=amount, payment_status="Pending")
                    request.session['donation_id'] = donation.id
                    return redirect(approval_url)
        else:
            return render(request, 'feed/donation_page.html', {"post": post, "error": "Payment creation failed. Try again."})

    return render(request, 'feed/donation_page.html', {"post": post})


paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  # sandbox or live
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

@login_required
def paypal_success(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')

    donation_id = request.session.get('donation_id')
    donation = get_object_or_404(Donation, id=donation_id)

    if payment_id and payer_id:
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            donation.payment_status = "Completed"
            donation.post.donation_received += donation.amount
            donation.post.save()
            donation.save()

            # Generate the donation receipt
            receipt_path = generate_donation_receipt(donation)

# Create the email
            

            # Send the email and handle any exceptions

            return render(request, "feed/paypal_success.html", {"donation": donation})

    return redirect("paypal_cancel")

# def download_receipt(request, donation_id):
#     """
#     View to generate and serve a donation receipt as a downloadable PDF.
#     """
#     try:
#         # Fetch the donation instance
#         donation = Donation.objects.get(id=donation_id)

#         # Generate the receipt PDF
#         receipt_path = generate_donation_receipt(donation)

#         # Serve the file as a response
#         return FileResponse(open(receipt_path, 'rb'), as_attachment=True, filename=os.path.basename(receipt_path))

#     except Donation.DoesNotExist:
#         return HttpResponseNotFound("Donation record not found.")
#     except Exception as e:
#         return HttpResponseNotFound(f"Error generating receipt: {str(e)}")

S3_BUCKET_NAME = "your-receipt-bucket"

def download_receipt(request, donation_id):
    """
    View to generate a donation receipt, upload it to S3, and serve it via a pre-signed URL.
    """
    try:
        # Fetch the donation instance
        donation = Donation.objects.get(id=donation_id)
        create_s3_bucket(S3_BUCKET_NAME)

        # Generate the receipt PDF locally
        receipt_path = generate_donation_receipt(donation)
        receipt_key = f"receipts/donation_{donation_id}.pdf"  # Path in S3

        # Upload the receipt to S3
        upload_to_s3(receipt_path, S3_BUCKET_NAME, receipt_key)

        # Generate a pre-signed URL to allow secure download
        presigned_url = generate_presigned_url(S3_BUCKET_NAME, receipt_key)

        if presigned_url:
            return HttpResponseRedirect(presigned_url)  # Redirect to the S3 link

        return HttpResponseNotFound("Error generating download link.")

    except Donation.DoesNotExist:
        return HttpResponseNotFound("Donation record not found.")
    except NoCredentialsError:
        return HttpResponseNotFound("AWS credentials not found.")
    except Exception as e:
        return HttpResponseNotFound(f"Error processing receipt: {str(e)}")

# def paypal_success(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    
    donation_id = request.session.get('donation_id')
    donation = get_object_or_404(Donation, id=donation_id)
    disaster_post = donation.post  # Get the post related to donation

    if payment_id and payer_id:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Update donation and post status
            donation.payment_status = "Completed"
            donation.post.donation_received += donation.amount
            donation.post.save()
            donation.save()

            # **Send Payment to Disaster Owner**
            recipient_email = donation.post.user_email  # Email entered in form

            payout = paypalrestsdk.Payout({
                "sender_batch_header": {
                    "sender_batch_id": f"batch_{donation.id}",
                    "email_subject": "You have received a donation!"
                },
                "items": [{
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": str(donation.amount),
                        "currency": "USD"
                    },
                    "receiver": recipient_email,
                    "note": f"Donation received for {donation.post.title}",
                    "sender_item_id": f"item_{donation.id}"
                }]
            })

            if payout.create():
                return render(request, "feed/paypal_success.html", {"donation": donation, "payout": "Sent to user"})
            else:
                return render(request, "feed/paypal_success.html", {"donation": donation, "error": "Payout failed!"})

        else:
            return render(request, "feed/paypal_cancel.html", {"error": "Payment execution failed."})

    return redirect("paypal_cancel")

    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    
    donation_id = request.session.get('donation_id')
    donation = get_object_or_404(Donation, id=donation_id)

    if payment_id and payer_id:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            donation.payment_status = "Completed"
            donation.post.donation_received += donation.amount
            donation.post.save()
            donation.save()
            return render(request, "feed/paypal_success.html", {"donation": donation})
        else:
            return render(request, "feed/paypal_cancel.html", {"error": "Payment execution failed."})

    return redirect("paypal_cancel")

def paypal_cancel(request):
    return render(request, "feed/paypal_cancel.html", {"error": "Payment was canceled."})


# Create your views here.


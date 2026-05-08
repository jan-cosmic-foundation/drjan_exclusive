import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

import requests
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db.models import Sum
from .models import Participant, Child, Donation
import random
import string

REGISTRATION_FEE = 400
RETREAT_DAYS = 10
ACCOMMODATION_OPTIONS = [
    {"label": "GHS 120 per day - Single Room", "daily_rate": 120},
    {"label": "GHS 150 per day - Single Room", "daily_rate": 150},
    {"label": "GHS 200 per day - Single Room", "daily_rate": 200},
    {"label": "GHS 280 per day - Standard Room", "daily_rate": 280},
    {"label": "GHS 380 per day - Executive Room", "daily_rate": 380},
    {"label": "GHS 480 per day - Suite", "daily_rate": 480},
]


def get_accommodation_price(accommodation):
    if not accommodation or not accommodation.startswith('GHS '):
        return 0

    try:
        return int(accommodation.split()[1])
    except (IndexError, ValueError):
        return 0


def get_checkout_amount(project, requested_amount, reference):
    if project == 'retreat-registration':
        return REGISTRATION_FEE

    if project == 'retreat-registration-accommodation':
        try:
            participant = Participant.objects.get(payment_reference=reference)
        except Participant.DoesNotExist:
            return None

        accommodation_price = get_accommodation_price(participant.accommodation)
        if not accommodation_price:
            return None

        return REGISTRATION_FEE + (accommodation_price * RETREAT_DAYS)

    if project and project.startswith('retreat-accommodation-'):
        try:
            daily_rate = int(project.rsplit('-', 1)[1])
        except (IndexError, ValueError):
            return None

        valid_rates = [option["daily_rate"] for option in ACCOMMODATION_OPTIONS]
        if daily_rate not in valid_rates:
            return None

        return daily_rate * RETREAT_DAYS

    try:
        return Decimal(str(requested_amount))
    except (InvalidOperation, TypeError, ValueError):
        return None


def register(request):
    return render(request, 'registration/index.html')


def generate_payment_reference():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def index(request):
    if request.method == 'POST':
        data = request.POST
        print(data)
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        email = data.get('email')
        phone = data.get('phone')
        country = data.get('country')
        dob = data.get('dob')
        gender = data.get('gender')
        region = data.get('region')
        transport = data.get('transport')
        personal_transport = data.get('personalTransport')
        impartation = data.get('impartation')
        registered_student = data.get('registeredStudent')
        attending_gtc = data.get('attendingGuideTheChildren')
        spouse_or_child = data.get('spouseOrChild')
        accommodation = data.get('accommodation')
        arrival_date = data.get('arrivalDate')
        volunteering = ', '.join(data.getlist('volunteering'))
        coming_with_children = data.get('comingWithChildren')
        children_count = data.get('childrenCount')
        comments = data.get('comments')

        # generate payment reference
        payment_reference = generate_payment_reference()

        # Convert date of birth (dob) string to date object
        dob = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None

        # Convert arrival date string to date object
        arrival_date = datetime.strptime(arrival_date, '%Y-%m-%d').date() if arrival_date else None
        try:
            children_count = max(0, int(children_count)) if children_count else 0
        except (TypeError, ValueError):
            children_count = 0
        if coming_with_children != 'Yes':
            children_count = 0

        participant = Participant.objects.create(
            first_name=firstname,
            last_name=lastname,
            email=email,
            phone=phone,
            country=country,
            dob=dob,
            gender=gender,
            impartation=impartation,
            registered_student=registered_student,
            attending_gtc=attending_gtc,
            spouse_or_child=spouse_or_child,
            accommodation=accommodation,
            arrival_date=arrival_date,
            volunteering=volunteering,
            coming_with_children=coming_with_children,
            children_count=children_count,
            comments=comments,
            region=region,
            transport=transport,
            personal_transport=personal_transport,
            payment_reference=payment_reference
        )

        accommodation_price = get_accommodation_price(accommodation)
        payment_context = {
            "reference": payment_reference,
            "email": email,
            "name": f"{firstname} {lastname}".strip(),
            "registration_fee": REGISTRATION_FEE,
            "retreat_days": RETREAT_DAYS,
            "accommodation_options": ACCOMMODATION_OPTIONS,
            "accommodation": accommodation,
            "accommodation_price": accommodation_price,
            "accommodation_total": accommodation_price * RETREAT_DAYS,
            "registration_with_accommodation": REGISTRATION_FEE + (accommodation_price * RETREAT_DAYS),
        }

        return render(request, 'registration/payment.html', payment_context)
    return render(request, 'registration/index.html')


def payment(request):
    context = {
        "retreat_days": RETREAT_DAYS,
        "accommodation_options": ACCOMMODATION_OPTIONS,
    }
    if request.GET:
        support = request.GET.get('supportTo')

        context['support'] = support
    return render(request, 'registration/payment.html', context)


def analytics(request):
    participants = Participant.objects.all()
    total = participants.count()

    total_children = Child.objects.count() + (participants.aggregate(total=Sum('children_count'))['total'] or 0)

    q_3 = participants.filter(question_3='Yes')
    total_gen7 = q_3.count()

    for p in participants:
        if p.spouse_name:
            total_gen7 += 1

        total_gen7 += p.children.count() + p.children_count

    # number of participants not in ghana
    p_not_ghana = 0
    for p in participants:
        if p.country != 'Ghana':
            p_not_ghana += 1

    total_spouse = 0
    for p in participants:
        if p.spouse_name:
            total_spouse += 1

    context = {
        'total': total,
        'total_students_coming_GTC': q_3.count(),
        'total_spouse': total_spouse,
        'total_children': total_children,
        'total_gen7': total_gen7,
        'total_not_ghana': p_not_ghana,
    }
    return render(request, 'registration/analytics.html', context)


class CheckoutView(View):
    template_name = 'exclusive/payment.html'

    def get(self, request):
        amount = request.GET.get('amount')
        reference = request.GET.get('reference')
        email = request.GET.get('email')
        name = request.GET.get('name')
        project = request.GET.get('project')

        reference = generate_payment_reference() if not reference else reference
        amount = get_checkout_amount(project, amount, reference)
        if amount is None:
            return HttpResponseBadRequest("Invalid payment amount.")

        # create donation record
        Donation.objects.create(
            name=name,
            email=email,
            reference=reference,
            project=project,
            amount=amount,
        )

        # # get participant email
        # participant = Participant.objects.get(payment_reference=reference)
        # email = participant.email

        hostname = request.get_host()

        url = "https://api.paystack.co/transaction/initialize"

        payload = json.dumps({
            "email": email,
            "amount": float(amount) * 100,
            "callback_url": f"http://{hostname}/event-registration/confirm-payment/",
            "reference": reference,
            "channels": [
                "mobile_money",
                "card",
            ]
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        response_data = response.json()
        print(response_data)

        return redirect(response_data['data']['authorization_url'])


class ConfirmPaymentView(View):
    template_name = 'registration/payment_successful.html'

    def get(self, request):
        context = {}
        reference = request.GET.get('reference')
        trxref = request.GET.get('trxref')

        url = f"https://api.paystack.co/transaction/verify/{reference}"

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }

        response = requests.request("GET", url, headers=headers)
        response_data = response.json()

        status = response_data['data']['status']
        amount = response_data['data']['amount']

        context['status'] = status

        if status == 'success':
            d = Donation.objects.get(reference=reference)
            d.paid = True
            d.save()
            context['project'] = d.project

            if d.project == 'retreat-registration':
                context['payment_title'] = 'Registration Payment Successful! ✅'
                context['payment_message'] = 'Thank you for completing your retreat registration payment.'
                context['support_heading'] = 'Support the Program'
                context['support_message'] = 'Use the button below if you would like to make an additional donation to the foundation.'
                context['support_button_text'] = 'Donate'
            elif d.project == 'retreat-registration-accommodation':
                context['payment_title'] = 'Registration and Accommodation Payment Successful! ✅'
                context['payment_message'] = 'Thank you for completing your retreat registration and accommodation payment.'
                context['support_heading'] = 'Support the Program'
                context['support_message'] = 'Use the button below if you would like to make an additional donation to the foundation.'
                context['support_button_text'] = 'Donate'
            elif d.project and d.project.startswith('retreat-accommodation'):
                context['payment_title'] = 'Accommodation Payment Successful! ✅'
                context['payment_message'] = 'Thank you for completing your retreat accommodation payment.'
                context['support_heading'] = 'Support the Program'
                context['support_message'] = 'Use the button below if you would like to make an additional donation to the foundation.'
                context['support_button_text'] = 'Donate'
            else:
                context['payment_title'] = 'Donation Successful! ✅'
                context['payment_message'] = "Thank you for your generous donation! Your support means the world to us and helps make a real difference. We couldn't do it without you."
                context['support_heading'] = 'Support Another Program'
                context['support_message'] = 'Use the button below to donate again to the foundation.'
                context['support_button_text'] = 'Donate Again'

        print(context)
        return render(request, self.template_name, context)

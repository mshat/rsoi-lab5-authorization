from django.shortcuts import render, redirect
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import requests
from .env import get_uri
import sys
sys.path.append("..")
from my_modules import my_requests
import json
from rest_framework.decorators import api_view
from okta_jwt_verifier import BaseJWTVerifier
from time import time

OKTA_TOKEN = '00chPxFo6VIb9J5qZ82MWWdl3dNvrFfVcdQBpi66Ul'


@api_view(["GET"])
def real_callback(request):
    """Это не должно относиться к resource server, коим является gateway"""
    # get запрос на следующий адрес должен отправить client
    # затем юзер авторизуется на доверенном сервисе и Authorization server редиректит его на callback,
    # где юзер продолжает работать с Client, а Client на фоне обменивает полученный код на JWT токен
    # https://dev-40891315.okta.com/oauth2/default/v1/authorize?client_id=0oa3kpon2u0fA3ZZV5d7&response_type=code&scope=openid profile&redirect_uri=http://localhost:8000/api/v1/real_callback&state=state-296bc9a0-a2a2-4a57-be1a-d0e2fd9bb601
    code = request.query_params.get('code')
    return Response(status=status.HTTP_200_OK, data={'code': code})


@api_view(["GET"])
def authorize(request):
    """Это не должно относиться к resource server, коим является gateway"""
    redirect_uri = "http://localhost:8000/api/v1/callback"
    client_id = "0oa3kpon2u0fA3ZZV5d7"
    url = f"https://dev-40891315.okta.com/oauth2/default/v1/authorize?client_id={client_id}&response_type=code&" \
          f"scope=openid profile&redirect_uri={redirect_uri}&state=state-296bc9a0-a2a2-4a57-be1a-d0e2fd9bb601"

    return Response(status=status.HTTP_302_FOUND, headers={"Location": url})


@api_view(["GET"])
def callback(request):
    """Это не должно относиться к resource server, коим является gateway"""
    grant_type = "authorization_code"
    code = request.query_params.get('code')
    redirect_uri = "http://localhost:8000/api/v1/callback"
    client_id = "0oa3kpon2u0fA3ZZV5d7"
    client_secret = "nUfgl079UYWhWMNZRy8HolCUnCYiJ7OVhvoVn-Db"
    url = f"https://dev-40891315.okta.com/oauth2/default/v1/token?grant_type={grant_type}&" \
          f"code={code}&redirect_uri={redirect_uri}&client_id={client_id}&client_secret={client_secret}"
    headers = {
        "accept": "application/json",
        'content-type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url=url, headers=headers).json()
    id_token = response['id_token']
    return Response(status=status.HTTP_200_OK, data={'message': 'Authorization was successful'})


def validate_token(token):
    jwt_verifier = BaseJWTVerifier(
        'https://dev-40891315.okta.com/oauth2/default', "0oa3kpon2u0fA3ZZV5d7", 'api://default')
    try:
        jwt_verifier.verify_signature(token, {
            "keys": [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "kid": "alE87Lpd_vRG-JUGDL9GzmJpb82G6tUDSVORo5ETRcY",
                    "use": "sig",
                    "e": "AQAB",
                    "n": "idmUkCHkXQQvG6cLWaz4PrIyF2eqKXEnuE4BOsfoIFPrE5FwSLNNU9Y0glg-LMXeggNh6XNLftiq15LcJpmjuvtd-_T_3b0VMRnavX3kfpWCTPJCOStAyrABjd3aAoHAd23b6j1lQA1G416s5IXenuPWHCQ5CvUmJrmqTM6llv2L_Uyr3gEAl79eIaObvkwPZ8lp4l5Zilj9dLFLDqTFfNIl17BlQ6_6_kzGJg4JRmgTWn3xxgivjnNQSIrd8oRmHex8nwgfY9QJcz_YVDEY_sb-2Eld5vu7cPHDgSCSaRVfY-0n7SFk314_Ii6Fh5XavhhZ179MXD0TKd3d9c45sw"
                }
            ]
        })
    except:
        return False
    return True


def parse_token(token):
    jwt_verifier = BaseJWTVerifier('https://dev-40891315.okta.com/oauth2/default', "0oa3kpon2u0fA3ZZV5d7", 'api://default')
    headers, claims, signing_input, signature = jwt_verifier.parse_token(token)
    data = {
        'headers': headers,
        'claims': claims,
        'signing_input': signing_input,
        'signature': signature
    }
    return data


def get_user_by_token(token):
    if not token:
        return ''
    data = parse_token(token)
    login = data['claims']['sub']
    response = requests.get(
        f'https://dev-40891315.okta.com/api/v1/users/{login}',
        headers={
            'Authorization': f'SSWS {OKTA_TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    data = response.json()
    first_name = data['profile']['firstName']
    last_name = data['profile']['lastName']
    return f'{first_name} {last_name}'


def get_token(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    if not isinstance(token, str):
        return
    token = token.replace('Bearer ', '')
    token = token.replace(' ', '')
    return token


def authorized(decorated_function):
    def wrapper(*args, **kwargs):
        token = get_token(args[1])
        if not token:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'message': 'Authorisation Error'})

        if not validate_token(token):
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'message': 'Authorisation Error'})
        else:
            return decorated_function(*args, **kwargs)
    return wrapper


class PersonView(APIView):
    @authorized
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'reservations'
        reservations_response = requests.get(str(reservation_service_uri), headers={'token': request.META.get("HTTP_AUTHORIZATION")})

        loyalty_service_uri = get_uri('loyalty')
        username = get_user_by_token(get_token(request))
        loyalty_response = requests.get(str(loyalty_service_uri), headers={"X-User-Name": username})
        data = {
            "reservations": reservations_response.json(),
            "loyalty": loyalty_response.json()
        }
        return Response(status=status.HTTP_200_OK, data=data)


class HotelsListView(APIView):
    @authorized
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'hotels'
        if request.META['QUERY_STRING']:
            reservation_service_uri.query = request.META['QUERY_STRING']
        else:
            raise Exception()

        response = requests.get(str(reservation_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())


class ReservationsListView(APIView):
    @authorized
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'reservations'
        response = requests.get(str(reservation_service_uri), headers={'token': request.META.get("HTTP_AUTHORIZATION")})
        return Response(status=status.HTTP_200_OK, data=response.json())

    @authorized
    def post(self, request):
        reservation_service_uri = get_uri('reservation')
        loyalty_service_uri = get_uri('loyalty')

        username = get_user_by_token(get_token(request))
        request_data = request.data
        hotel_uid = request_data["hotelUid"]
        start_date = request_data["startDate"]
        end_date = request_data["endDate"]

        # Запрос к Reservation Service для проверки, что такой отель существует
        try:
            reservation_service_uri.path = 'hotels'
            hotels_get_response = requests.get(str(reservation_service_uri))
        except Exception as e:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE,
                            data={'message': 'Reservation Service unavailable'})
        if hotels_get_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE,
                            data={'message': 'Reservation Service unavailable'})
        elif hotels_get_response.status_code == 200:
            hotels_get_response_data = hotels_get_response.json()

            hotel_found = False
            for hotel in hotels_get_response_data:
                if hotel_uid == hotel['hotelUid']:
                    hotel_found = True
                    break
            if not hotel_found:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'Hotel not found'})

        # Запрос к Loyalty Service для увеличения счетчика бронирований
        try:
            loyalty_patch_response = requests.patch(str(loyalty_service_uri), headers={"X-User-Name": username})
        except Exception as e:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})
        if loyalty_patch_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})

        reservation_service_uri.path = 'reservations'
        reservation_post_response = requests.post(
            str(reservation_service_uri),
            data=json.dumps({"hotelUid": hotel_uid, "startDate": start_date, "endDate": end_date}),
            headers={"Content-Type": "application/json", "x-user-name": username, 'token': request.META.get("HTTP_AUTHORIZATION")}
        )

        if reservation_post_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})

        return Response(status=status.HTTP_200_OK, data=reservation_post_response.json())


class ReservationView(APIView):
    @authorized
    def get(self, request, uid):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = f'reservation/{uid}'

        response = requests.get(str(reservation_service_uri), headers={'token': request.META.get("HTTP_AUTHORIZATION")})
        return Response(status=status.HTTP_200_OK, data=response.json())

    @authorized
    def delete(self, request, uid):
        loyalty_service_uri = get_uri('loyalty')
        username = get_user_by_token(get_token(request))
        requests.delete(str(loyalty_service_uri), headers={"X-User-Name": username})

        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = f"reservation/{uid}"
        reservation_response = requests.get(str(reservation_service_uri), headers={'token': request.META.get("HTTP_AUTHORIZATION")})
        reservation = reservation_response.json()

        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f"payment/{reservation['payment_uid']}"
        payment_status_patch_request = my_requests.PatchRequest(payment_service_uri, data={"status": "CANCELED"})
        payment_status_patch_request.send()

        reservation_service_uri.path = f"reservation/{uid}"
        reservation_status_patch_request = my_requests.PatchRequest(reservation_service_uri, data={"status": "CANCELED"})
        reservation_status_patch_request.send()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LoyaltyView(APIView):
    @authorized
    def get(self, request):
        loyalty_service_uri = get_uri('loyalty')
        response = requests.get(str(loyalty_service_uri), headers={"X-User-Name": "Test Max"})
        if response.status_code == 404:
            return Response(status=status.HTTP_404_NOT_FOUND, data=response.json())
        return Response(status=status.HTTP_200_OK, data=response.json())


class PaymentsListView(APIView):
    @authorized
    def get(self, request):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = 'payments'

        response = requests.get(payment_service_uri)
        return Response(status=response.status_code, data=response.json())

    @authorized
    def post(self, request):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f'payments'

        price = request.data['price']
        response = requests.post(str(payment_service_uri), data={'price': price})
        if response.status_code == 200:
            return Response(status=status.HTTP_200_OK, data=response.json())
        else:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Payment service unavailable'})


class PaymentView(APIView):
    @authorized
    def get(self, request, uid):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f'payment/{uid}'

        response = requests.get(str(payment_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())

        





from django.shortcuts import render, redirect
import requests
import json

from env import URL_API

# Create your views here.


def index(request):
    print(request.method)
    if request.method == 'POST':
        email = request.POST.get('email')
        post_type = request.POST.get('post_type')

        json_data = json.dumps({'name': email})
        if post_type == 'sign-up':
            response = requests.post(f'{URL_API}/users', data=json_data)

            print(response.text)
        elif post_type == 'sign-in':
            response = requests.post(f'{URL_API}/users/login', data=json_data)

            if response.status_code == 201:
                response_data = response.json()
                
                messages = requests.get(
                    f'{URL_API}/messages?user_id={response_data["id"]}')
                
                first_message_received = getFirstReceivedMessage(messages.json(), response_data['id'])
                data = {
                    'id': response_data['id'],
                    'name': response_data['name'],
                    'messages': messages.json(),
                    'first_message': first_message_received,
                    'selected_message': first_message_received
                }

                print(data['first_message'])
                return render(request, 'dashboard.html', data)
            # print(response.text)

    return render(request, 'index.html')


def dashboard(request, data):
    return render(request, 'dashboard.html', data)


def getFirstReceivedMessage(messages, user_id):
    for message in messages:
        if message['addressee']['id'] == user_id:
            return message

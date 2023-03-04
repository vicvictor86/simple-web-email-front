import requests
import json

from django.shortcuts import render, redirect
from datetime import datetime

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
                messages_data = messages.json()

                for message in messages_data:
                    message['created_at'] = formatDate(message['created_at'])
                    message['user_character'] = getUserCharacter(message['sender']['name'])
                    print(message['created_at'])

                first_message_received = getFirstReceivedMessage(messages_data, response_data['id'])
                data = {
                    'id': response_data['id'],
                    'name': response_data['name'],
                    'messages': messages_data,
                    'first_message': first_message_received,
                    'selected_message': messages_data[-1]
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


def formatDate(date):
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%Y %H:%M:%S')

def getUserCharacter(username):
    return username[0].upper()
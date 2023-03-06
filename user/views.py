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
        elif post_type == 'sign-in':
            response = requests.post(f'{URL_API}/users/login', data=json_data)

            if response.status_code == 201:
                response_data = response.json()

                messages = requests.get(
                    f'{URL_API}/messages?user_id={response_data["id"]}')
                messages_data = messages.json()

                unread_messages = countUnreadMessages(messages_data, response_data["id"])

                updateMessageDataInfo(messages_data)
                    
                data = {
                    'user_id': response_data['id'],
                    'name': response_data['name'],
                    'messages': messages_data,
                    'selected_message': None,
                    'unread_messages': unread_messages,
                    'status': 'show',
                    'emails_status': 'received',
                }

                request.session['response_data'] = data

                return render(request, 'dashboard.html', data)

    return render(request, 'index.html')


def dashboard_status(request):
    status = request.GET.get('status')
    emails_status = request.GET.get('emails_status')

    if status is None:
        status = 'show'

    if emails_status is None:
        emails_status = 'received'

    data = request.session['response_data']
    data['status'] = status
    data['emails_status'] = emails_status

    return render(request, 'dashboard.html', data)


def dashboard(request, id):
    data = request.session['response_data']
    messages = data['messages']
    data['status'] = request.GET.get('status')
    data['emails_status'] = request.GET.get('emails_status')

    unread_messages = data['unread_messages']

    for message in messages:
        if message['id'] == id:
            json_data = json.dumps({'id': id ,'read': True})
            requests.put(f'{URL_API}/messages', data=json_data)            

            data['selected_message'] = message
            
            if message['read'] == False:
                message['read'] = True
                unread_messages -= 1
        
            break

    updateMessageDataInfo(messages, True)

    if unread_messages < 0:
        unread_messages = 0

    data['unread_messages'] = unread_messages

    request.session['response_data'] = data

    return render(request, 'dashboard.html', data)


def send_message(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        to_with_commas = request.POST.get('to')
        subject = request.POST.get('subject')
        text = request.POST.get('text')

        to = to_with_commas.split(',')

        json_data = json.dumps({
            'sender': user_id,
            'addressees': to,
            'subject': subject,
            'text': text
        })

        response = requests.post(f'{URL_API}/messages', data=json_data)
        response_data = response.json()

        if response.status_code == 201:
            return redirect(f'/dashboard/{response_data[0]["message_id"]}?status=show&emails_status=sent')
        else:
            data = request.session['response_data']
            messages = data['messages']
            firstMessage = getFirstReceivedMessage(messages, user_id)
            return redirect(f'/dashboard/{firstMessage["id"]}?status=show&emails_status=received')

    return redirect('/')

def delete_message(request, id): 
    session_data = request.session['response_data']
    response = requests.delete(f'{URL_API}/messages/{id}?user_id={session_data["user_id"]}')

    if response.status_code == 200:
        for message in session_data['messages']:
            if message['id'] == id:
                session_data['messages'].remove(message)
                break
        
        request.session['response_data'] = session_data
        return redirect('dashboard_status')
    else:
        print('não encontrou')
        return redirect('dashboard_status')

def getFirstReceivedMessage(messages, user_id):
    for message in messages:
        if message['addressee']['id'] == user_id:
            return message


def get_new_messages(request, user_id):
    messages = requests.get(f'{URL_API}/messages?user_id={user_id}')
    messages_data = messages.json()
    
    unread_messages = countUnreadMessages(messages_data, user_id)
    updateMessageDataInfo(messages_data)

    response_data = request.session['response_data']
    response_data['unread_messages'] = unread_messages

    data = {
        'user_id': user_id,
        'name': response_data['name'],
        'messages': messages_data,
        'selected_message': response_data['selected_message'],
        'unread_messages': unread_messages,
        'status': response_data['status'],
        'emails_status': response_data['emails_status'],
    }

    request.session['response_data'] = data

    return render(request, 'dashboard.html', data)


def formatDate(date):
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d/%m/%Y %H:%M:%S')


def getUserCharacter(username):
    return username[0].upper()

def countUnreadMessages(messages, user_id):
    unread_messages = 0
    for message in messages:
        if message['read'] == False and message['addressee']['id'] == user_id:
            unread_messages += 1

    return unread_messages

def updateMessageDataInfo(messages_data, date_already_formatted=False):
    for message in messages_data:
        if not date_already_formatted:
            message['created_at'] = formatDate(message['created_at'])
            
        message['user_character'] = getUserCharacter(message['sender']['name'])

        if message['read'] == False:
            message['read_color'] = 'bg-yellow-500'
        else:
            message['read_color'] = 'bg-indigo-200'
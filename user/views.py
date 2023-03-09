import requests
import json

from django.shortcuts import render, redirect
from datetime import datetime
from dateutil import tz
from user.utils import translateErrorMessage 

from env import URL_API


def index(request):
    print(request.method)

    if request.method == 'POST':
        email = request.POST.get('email')
        post_type = request.POST.get('post_type')

        json_data = json.dumps({'name': email})
        if post_type == 'sign-up':
            response = requests.post(f'{URL_API}/users', data=json_data).json()

            if has_error(response):
                error_message = response
                error_message['message'] = translateErrorMessage(error_message['message'])
                return render(request, 'index.html', error_message)
            
            success_message = {
               'message': 'Usuário criado com sucesso',
               'type': 'success'
            }
            
            return render(request, 'index.html', success_message)

        elif post_type == 'sign-in':
            response = requests.post(
                f'{URL_API}/users/login', data=json_data).json()

            if has_error(response):
                error_message = response
                error_message['message'] = translateErrorMessage(error_message['message'])
                return render(request, 'index.html', error_message)

            messages = requests.get(
                f'{URL_API}/messages?user_id={response["id"]}').json()

            if has_error(response):
                error_message = response
                error_message['message'] = translateErrorMessage(error_message['message'])
                return render(request, 'index.html', error_message)

            unread_messages = countUnreadMessages(messages, response["id"])

            updateMessageDataInfo(messages)

            data = updateData(response['id'], response['name'], messages,
                              None, unread_messages, 'show', 'received', False)

            request.session['session_data'] = data

            return render(request, 'dashboard.html', data)

    return render(request, 'index.html')


def dashboard_status(request):
    status = request.GET.get('status')
    emails_status = request.GET.get('emails_status')

    if status is None:
        status = 'show'

    if emails_status is None:
        emails_status = 'received'

    session_data = request.session['session_data']
    session_data['status'] = status
    session_data['emails_status'] = emails_status
    session_data['is_replying'] = False

    return render(request, 'dashboard.html', session_data)


def dashboard(request, id):
    session_data = request.session['session_data']
    messages = session_data['messages']
    session_data['status'] = request.GET.get('status')
    session_data['emails_status'] = request.GET.get('emails_status')
    need_update = request.GET.get('update')

    if need_update == 'true':
        messages = requests.get(
            f'{URL_API}/messages?user_id={session_data["user_id"]}').json()

        if has_error(messages):
            error_message = messages
            error_message['message'] = translateErrorMessage(error_message['message'])
            session_data['error_message'] = error_message
            return render(request, 'dashboard.html', session_data)

        updateMessageDataInfo(messages)

        session_data['messages'] = messages

    unread_messages = session_data['unread_messages']

    for message in messages:
        if message['id'] == id:
            if message['addressee_id'] == session_data['user_id']:
                json_data = json.dumps({'id': id, 'read': True})
                response = requests.put(f'{URL_API}/messages', data=json_data).json()

                if has_error(response):
                    error_message = response
                    error_message['message'] = translateErrorMessage(error_message['message'])
                    session_data['error_message'] = error_message
                    return render(request, 'dashboard.html', session_data)

            session_data['selected_message'] = message
            if message['read'] == False:
                message['read'] = True
                unread_messages -= 1

            break

    updateMessageDataInfo(messages, True)

    if unread_messages < 0:
        unread_messages = 0

    session_data['unread_messages'] = unread_messages

    request.session['session_data'] = session_data

    return render(request, 'dashboard.html', session_data)


def send_message(request):
    if request.method == 'POST':
        session_data = request.session['session_data']

        user_id = request.POST.get('user_id')
        to_with_commas = request.POST.get('to')
        subject = request.POST.get('subject')
        text = request.POST.get('text')

        print(to_with_commas.strip())
        to = to_with_commas.replace(' ', '').split(',')
        print(to)

        replying_to_id = request.POST.get('replying_to_id') or ""
        forwarding_to_id = request.POST.get('forwarding_to_id') or ""

        if forwarding_to_id != "":
            forward_data = json.dumps(
                {'userMessageId': session_data['selected_message']['id'], 'senderId': user_id, 'addressees': to})
            response = requests.post(f'{URL_API}/messages/forward', data=forward_data).json()
            
            if has_error(response):
                error_message = response
                error_message['message'] = translateErrorMessage(error_message['message'])
                session_data['error_message'] = error_message
                
                return render(request, 'dashboard.html', session_data)

            return redirect(f'/dashboard/{response[0]["id"]}?status=show&emails_status=received&update=true')

        json_data = json.dumps({
            'sender': user_id,
            'addressees': to,
            'subject': subject,
            'text': text,
            'replyingTo': replying_to_id
        })

        response = requests.post(f'{URL_API}/messages', data=json_data)
        response_data = response.json()

        if has_error(response_data):
            error_message = response_data
            error_message['message'] = translateErrorMessage(error_message['message'])
            session_data['error_message'] = error_message
            return render(request, 'dashboard.html', session_data)

        if response.status_code == 201:
            session_data['messages'].append(response_data[0])

            return redirect(f'/dashboard/{response_data[0]["id"]}?status=show&emails_status=sent&update=true')
        else:
            session_data = request.session['session_data']
            messages = session_data['messages']
            firstMessage = getFirstReceivedMessage(messages, user_id)
            return redirect(f'/dashboard/{firstMessage["id"]}?status=show&emails_status=received')

    return redirect('/')


def delete_message(request, id):
    session_data = request.session['session_data']
    response = requests.delete(
        f'{URL_API}/messages/{id}?user_id={session_data["user_id"]}')

    if has_error(response.json()):
        error_message = response.json()
        error_message['message'] = translateErrorMessage(error_message['message'])
        session_data['error_message'] = error_message
        return render(request, 'dashboard.html', session_data)

    if response.status_code == 200:
        for message in session_data['messages']:
            if message['id'] == id:
                session_data['messages'].remove(message)
                break

        request.session['session_data'] = session_data
    return redirect('dashboard_status')
    

def reply_message(request, id):
    session_data = request.session['session_data']
    messages = session_data['messages']

    session_data['status'] = request.GET.get('status')
    session_data['emails_status'] = request.GET.get('emails_status')

    for message in messages:
        if message['id'] == id:
            data = updateData(session_data['user_id'], session_data['name'], messages, message,
                              session_data['unread_messages'], session_data['status'], session_data['emails_status'], True)

            request.session['session_data'] = data

            return render(request, 'dashboard.html', data)

    return redirect('dashboard_status')


def forward_message(request, id):
    session_data = request.session['session_data']
    messages = session_data['messages']

    session_data['status'] = request.GET.get('status')
    session_data['emails_status'] = request.GET.get('emails_status')

    for message in messages:
        if message['id'] == id:
            data = updateData(session_data['user_id'], session_data['name'], messages, message,
                              session_data['unread_messages'], session_data['status'], session_data['emails_status'], False, True)

            request.session['session_data'] = data

            return render(request, 'dashboard.html', data)

    return redirect('dashboard_status')


def getFirstReceivedMessage(messages, user_id):
    for message in messages:
        if message['addressee']['id'] == user_id:
            return message


def get_new_messages(request, user_id):
    messages = requests.get(f'{URL_API}/messages?user_id={user_id}').json()

    if has_error(messages):
        error_message = messages
        error_message['message'] = translateErrorMessage(error_message['message'])
        request.session['session_data']['error_message'] = error_message
        return render(request, 'dashboard.html', request.session['session_data'])

    unread_messages = countUnreadMessages(messages, user_id)
    updateMessageDataInfo(messages)

    response_data = request.session['session_data']

    data = updateData(user_id, response_data['name'], messages, response_data['selected_message'],
                      unread_messages, response_data['status'], response_data['emails_status'])

    request.session['session_data'] = data

    return render(request, 'dashboard.html', data)


def formatDate(date):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('America/Sao_Paulo')

    utc = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
    utc = utc.replace(tzinfo=from_zone)

    central = utc.astimezone(to_zone)

    return central.strftime('%d/%m/%Y %H:%M:%S')


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
            message['read_color'] = 'bg-blue-400'


def updateData(user_id, name, messages, selected_message, unread_messages, status, email_status, is_replying=False, isForwarding=False):
    data = {
        'user_id': user_id,
        'name': name,
        'user_first_character': getUserCharacter(name),
        'messages': messages,
        'selected_message': selected_message,
        'unread_messages': unread_messages,
        'status': status,
        'emails_status': email_status,
        'is_replying': is_replying,
        'is_forwarding': isForwarding,
    }

    return data


def has_error(response):
    if 'status' in response and response['status'] == 'error':
        return True
    return False

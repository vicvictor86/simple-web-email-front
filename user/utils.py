translations = {
    'Missing attributes': 'Faltando argumento',
    'Addressee not found': 'O Destinatário não existe',
    'Message replying to not found': 'A menssagem que você está respondendo não existe',
    'Message not found': 'A menssagem não existe',
    'User not found': 'O usuário não existe',
    'Sender not in conversation': 'O remetente não está na conversa',
    'Id message is required': 'O id da menssagem é obrigatório',
    'Sender not found': 'O remetente não existe',
    'You are not the sender or addressee of this message': 'Você não é o remetente ou destinatário dessa menssagem',
    'Read must be boolean': 'Read deve ser booleano',
    'User already exists': 'O usuário já existe',
}   

def translateErrorMessage(error_message):
    if error_message in translations:
        translate_error_message = translations[error_message]
        return translate_error_message
    return error_message
    
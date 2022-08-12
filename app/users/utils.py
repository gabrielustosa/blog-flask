import secrets
import os

from flask import url_for, current_app
from flask_mail import Message
from PIL import Image

from app import mail


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_name = f'{random_hex}{file_extension}'
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_name)

    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size)

    img.save(picture_path)
    return picture_name


def send_reset_email(user):
    token = user.get_reset_token()
    message = Message('Password Reset Request', sender='noreply@gabrielustosa.com.br', recipients=[user.email])
    message.body = f'''
        To reset your password, visit the following link {url_for('users.reset_password', token=token, _external=True)}
    '''
    mail.send(message)

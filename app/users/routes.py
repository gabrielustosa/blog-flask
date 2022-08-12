from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, current_user, logout_user, login_required
from flask import Blueprint

from app.models import User
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from app import bcrypt, db
from .utils import save_picture, send_reset_email

users = Blueprint('users', __name__)


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(username=form.username.data, email=form.email.data, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        login_user(user)

        flash(f'You account has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('register.html', form=form)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            flash(f'You have been logged in!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash(f'Password or Email are incorrect!', 'danger')
    return render_template('login.html', form=form)


@users.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('main.home'))


@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('You account has been updated!', 'success')
        return redirect(url_for('users.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
    return render_template('profile.html', form=form, image_file=image_file)


@users.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RequestResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))

    return render_template('reset_request.html', form=form)


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_reset_token(token)

    if not user:
        flash('That is an invalid token.', 'warning')
        return redirect(url_for('users.reset_request'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

            user.password = hashed_password

            db.session.commit()

            login_user(user)

            flash(f'You password has been updated!', 'success')
            return redirect(url_for('main.home'))

    return render_template('reset_password.html', form=form)

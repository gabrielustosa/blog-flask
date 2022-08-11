import secrets
import os

from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_user, current_user, logout_user, login_required

from PIL import Image

from .models import User, Post
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from app import app, bcrypt, db


@app.route('/')
@app.route('/home')
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user = User(username=form.username.data, email=form.email.data, password=hashed_password)

        db.session.add(user)
        db.session.commit()

        login_user(user)

        flash(f'You account has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)

            flash(f'You have been logged in!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Password or Email are incorrect!', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()

    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_name = f'{random_hex}{file_extension}'
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_name)

    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size)

    img.save(picture_path)
    return picture_name


@app.route('/profile', methods=['GET', 'POST'])
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
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
    return render_template('profile.html', form=form, image_file=image_file)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', form=form)


@app.route('/post/<int:post_id>')
def post_view(post_id):
    post = Post.query.get_or_404(post_id)

    return render_template('post_view.html', post=post)


@app.route('/post/update/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_update(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        return redirect(url_for('post_view', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', form=form)


@app.route('/post/delete/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('delete_post.html', post=post)

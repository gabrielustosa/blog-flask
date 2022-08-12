from flask import render_template, flash, redirect, url_for, request, abort, Blueprint
from flask_login import current_user, login_required

from app.models import User, Post
from .forms import PostForm
from app import db

posts = Blueprint('posts', __name__)


@posts.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()

        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html', form=form)


@posts.route('/post/<int:post_id>')
def post_view(post_id):
    post = Post.query.get_or_404(post_id)

    return render_template('post_view.html', post=post)


@posts.route('/post/update/<int:post_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('posts.post_view', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', form=form)


@posts.route('/post/delete/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('main.home'))

    return render_template('delete_post.html', post=post)


@posts.route('/user/<username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    paginator = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=3)
    return render_template('user_posts.html', paginator=paginator, username=username)

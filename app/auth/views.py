from . import auth
from ..models import User, db
from flask import render_template, request, redirect, url_for, flash
from .forms import LoginForm, RegistrationForm, ChangePasswordForm
from flask_login import login_user, login_required, logout_user


@auth.route("/login", methods=["GET", "POST"])
def login():
    """登陆功能"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        password = request.form.get('password')
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash("无效的用户名或密码")
    return render_template('auth/login.html', form=form)


@auth.route("/logout")
@login_required
def logout():
    """注销"""
    logout_user()
    flash("您已注销")
    return redirect(url_for('main.index'))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """注册"""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.route("/changepassword", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            user.password = form.new_password.data
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.login'))
    return render_template('auth/changepassword.html', form=form, title="修改密码")


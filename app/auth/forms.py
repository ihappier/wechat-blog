from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms.validators import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired()])
    password = PasswordField("密码", validators=[DataRequired()])
    remember_me = BooleanField("记住密码")
    submit = SubmitField("登陆")


class Registration(FlaskForm):
    email = StringField("邮箱", validators=[DataRequired(), Length(1,64), Email])
    username = StringField("用户名", validators=[DataRequired(), Length(1,64),
                                              Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                                     "用户名只能包含字母数字下划线")])
    password = PasswordField("密码", validators=[DataRequired(), EqualTo('password2',
                                                                       message="密码必须一致")])
    password2 = PasswordField("在输入一次", validators=[DataRequired()])
    submit = SubmitField("注册")


    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("该邮箱已注册")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("该用户名已注册")
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired
from flask_pagedown.fields import PageDownField


class PostForm(FlaskForm):
    # title = StringField("题目", validators=[DataRequired()])
    # # body = TextAreaField("你的文章", validators=[DataRequired()])
    submit = SubmitField("提交")


class LoginForm(FlaskForm):
    username = StringField("用户名", validators=[DataRequired()])
    password = PasswordField("密码", validators=[DataRequired()])
    submit = SubmitField("登陆")
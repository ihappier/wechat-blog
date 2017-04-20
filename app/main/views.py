"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, redirect, url_for,\
    request, make_response, current_app, abort
from app.ueditor.uploader import Uploader
from flask_login import login_required, current_user

from . import main
from .. import db
from ..models import User, Post
from .forms import PostForm

import json
import os
import re


@main.route('/')
@main.route('/home', methods=['GET', 'POST'])
def index():
    """Renders the home page."""
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=10, error_out=False)
    posts = pagination.items
    return render_template(
        'index.html',
        title='主页',
        posts=posts,
        pagination=pagination
    )


@main.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )


@main.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )


@main.route('/post', methods=["GET", "POST"])
@login_required
def post():
    """发布新文章页面"""
    form = PostForm()
    if form.validate_on_submit():
        body = request.form.get("editorValue")
        article = Post(title=request.form.get("title"), body=body,
                       author_id=current_user._get_current_object().id)
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('main.article', id=article.id))
    return render_template("post.html", form=form)


@main.route('/article/<int:id>')
def article(id):
    """文章页面"""
    article = Post.query.get_or_404(id)
    author = User.query.get_or_404(article.author_id)
    return render_template('article.html', article=article, title=article.title, author=author)


@main.route('/user/<username>')
@login_required
def user(username):
    """用户界面"""
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author_id=user.id)
    return render_template('user.html', posts=posts, user=user)


@main.route('/edit/<int:id>', methods=["GET", "POST"])
@login_required
def edit(id):
    """修改文章页面"""
    form = PostForm()
    edit_post = Post.query.get_or_404(id)
    if form.validate_on_submit():
        edit_post.title = request.form.get('title')
        edit_post.body = request.form.get('editorValue')
        db.session.add(edit_post)
        db.session.commit()
        return redirect(url_for('main.article', id=id))
    return render_template('edit.html', form=form, post=edit_post)


@main.route('/upload/', methods=['GET', 'POST', 'OPTIONS'])
def upload():
    """UEditor文件上传接口
    config 配置文件
    result 返回结果
    """
    mimetype = 'application/json'
    result = {}
    action = request.args.get('action')
    # 解析JSON格式的配置文件
    with open(os.path.join(current_app.static_folder, 'ueditor', 'php',
                           'config.json')) as fp:
        try:
            # 删除 `/**/` 之间的注释
            CONFIG = json.loads(re.sub(r'\/\*.*\*\/', '', fp.read()))
        except:
            CONFIG = {}
    if action == 'config':
        # 初始化时，返回配置文件给客户端
        result = CONFIG
    elif action in ('uploadimage', 'uploadfile', 'uploadvideo'):
        # 图片、文件、视频上传
        if action == 'uploadimage':
            fieldName = CONFIG.get('imageFieldName')
            config = {
                "pathFormat": CONFIG['imagePathFormat'],
                "maxSize": CONFIG['imageMaxSize'],
                "allowFiles": CONFIG['imageAllowFiles']
            }
        elif action == 'uploadvideo':
            fieldName = CONFIG.get('videoFieldName')
            config = {
                "pathFormat": CONFIG['videoPathFormat'],
                "maxSize": CONFIG['videoMaxSize'],
                "allowFiles": CONFIG['videoAllowFiles']
            }
        else:
            fieldName = CONFIG.get('fileFieldName')
            config = {
                "pathFormat": CONFIG['filePathFormat'],
                "maxSize": CONFIG['fileMaxSize'],
                "allowFiles": CONFIG['fileAllowFiles']
            }
        if fieldName in request.files:
            field = request.files[fieldName]
            uploader = Uploader(field, config, current_app.static_folder)
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'
    elif action in ('uploadscrawl'):
        # 涂鸦上传
        fieldName = CONFIG.get('scrawlFieldName')
        config = {
            "pathFormat": CONFIG.get('scrawlPathFormat'),
            "maxSize": CONFIG.get('scrawlMaxSize'),
            "allowFiles": CONFIG.get('scrawlAllowFiles'),
            "oriName": "scrawl.png"
        }
        if fieldName in request.form:
            field = request.form[fieldName]
            uploader = Uploader(field, config, current_app.static_folder, 'base64')
            result = uploader.getFileInfo()
        else:
            result['state'] = '上传接口出错'
    elif action in ('catchimage'):
        config = {
            "pathFormat": CONFIG['catcherPathFormat'],
            "maxSize": CONFIG['catcherMaxSize'],
            "allowFiles": CONFIG['catcherAllowFiles'],
            "oriName": "remote.png"
        }
        fieldName = CONFIG['catcherFieldName']
        if fieldName in request.form:
            # 这里比较奇怪，远程抓图提交的表单名称不是这个
            source = []
        elif '%s[]' % fieldName in request.form:
            # 而是这个
            source = request.form.getlist('%s[]' % fieldName)
        _list = []
        for imgurl in source:
            uploader = Uploader(imgurl, config, current_app.static_folder, 'remote')
            info = uploader.getFileInfo()
            _list.append({
                'state': info['state'],
                'url': info['url'],
                'original': info['original'],
                'source': imgurl,
            })
        result['state'] = 'SUCCESS' if len(_list) > 0 else 'ERROR'
        result['list'] = _list
    else:
        result['state'] = '请求地址出错'
    result = json.dumps(result)
    if 'callback' in request.args:
        callback = request.args.get('callback')
        if re.match(r'^[\w_]+$', callback):
            result = '%s(%s)' % (callback, result)
            mimetype = 'application/javascript'
        else:
            result = json.dumps({'state': 'callback参数不合法'})
    res = make_response(result)
    res.mimetype = mimetype
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['Access-Control-Allow-Headers'] = 'X-Requested-With,X_Requested_With'
    return res

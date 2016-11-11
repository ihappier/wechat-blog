import re
import os
import base64
import datetime
import urllib.request
import random

from flask import url_for
from werkzeug.utils import secure_filename

"""
Created by JetBrains PhpStorm.
User: taoqili
Date: 12-7-18
Time: 上午11: 32
UEditor编辑器通用上传类
"""


class Uploader:
    stateMap = [  # 上传状态映射表，国际化用户需考虑此处数据的国际化
        "SUCCESS",  # //上传成功标记，在UEditor中内不可改变，否则flash判断会出错
        "文件大小超出 upload_max_filesize 限制",
        "文件大小超出 MAX_FILE_SIZE 限制",
        "文件未被完整上传",
        "没有文件被上传",
        "上传文件为空", ]
    stateError = {
        "ERROR_TMP_FILE": "临时文件错误",
        "ERROR_TMP_FILE_NOT_FOUND": "找不到临时文件",
        "ERROR_SIZE_EXCEED": "文件大小超出网站限制",
        "ERROR_TYPE_NOT_ALLOWED": "文件类型不允许",
        "ERROR_CREATE_DIR": "目录创建失败",
        "ERROR_DIR_NOT_WRITEABLE": "目录没有写权限",
        "ERROR_FILE_MOVE": "文件保存时出错",
        "ERROR_FILE_NOT_FOUND": "找不到上传文件",
        "ERROR_WRITE_CONTENT": "写入文件内容错误",
        "ERROR_UNKNOWN": "未知错误",
        "ERROR_DEAD_LINK": "链接不可用",
        "ERROR_HTTP_LINK": "链接不是http链接",
        "ERROR_HTTP_CONTENTTYPE": "链接contentType不正确",
        "INVALID_URL": "非法 URL",
        "INVALID_IP": "非法 IP"}

    # /**
    #  * 构造函数
    #  * @param string $fileField 表单名称
    #  * @param array $config 配置项
    #  * @param bool $base64 是否解析base64编码，可省略。若开启，则$fileField代表的是base64编码的字符串表单名
    #  */
    def __init__(self, fileField, config, static_folder, _type=None):
        self.fileField = fileField
        self.config = config
        self.static_folder = static_folder
        self._type = _type
        if _type == "remote":
            self.save_remote()
        elif _type == "base64":
            self.up_base64()
        else:
            self.up_file()

    def up_file(self):
        #  * 上传文件的主处理方法
        self.oriName = self.fileField.filename
        self.fileField.stream.seek(0, 2)
        self.fileSize = self.fileField.stream.tell()
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()

        self.check_files()

    def up_base64(self):

        img = base64.b64decode(self.fileField)
        self.oriName = self.config['oriName']
        self.fileSize = len(img)
        self.fileType = self.getFileExt()
        self.filePath = self.getFilePath()
        self.fullName = self.getFullName()

        self.check_files()

        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(img)
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError("ERROR_FILE_MOVE")
            return

    def check_files(self):
        """检查文件各种属性"""
        # // 检查文件大小是否超出限制
        if not self.checkSize():
            self.stateInfo = self.getStateError("ERROR_SIZE_EXCEED")
            return

        # // 检查是否不允许的文件格式
        if not self.checkType():
            self.stateInfo = self.getStateError("ERROR_TYPE_NOT_ALLOWED")
            return

        # 检查路径是否存在，不在就创建
        dir_name = os.path.dirname(self.filePath)
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
            except:
                self.stateInfo = self.getStateError("ERROR_CREATE_DIR")
            return
        elif not os.access(dir_name, os.W_OK):
            self.stateInfo = self.getStateError("ERROR_DIR_NOT_WRITEABLE")
            return
        try:
            self.fileField.save(self.filePath)
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError("ERROE_FILE_MOVE")
            return

    def save_remote(self):
        _file = urllib.request.urlopen(self.fileField)
        self.oriName = self.config['oriName']
        self.fileSize = 0
        self.fileType = self.getFileExt()
        self.fullName = self.getFullName()
        self.filePath = self.getFilePath()

        self.check_files()

        try:
            with open(self.filePath, 'wb') as fp:
                fp.write(_file.read())
            self.stateInfo = self.stateMap[0]
        except:
            self.stateInfo = self.getStateError('ERROR_FILE_MOVE')
            return

    def getStateError(self, errCode):
        # 上传错误检查
        return self.stateError.get(errCode, 'Unknow Error')

    def getFileExt(self):
        # 获取文件扩展名
        return ('.%s' % self.oriName.split('.')[-1]).lower()

    def getFullName(self):
        """ 重命名文件"""
        # 替换日期事件
        now = datetime.datetime.now()
        _time = now.strftime("%H%M%S")
        _format = self.config["pathFormat"]
        _format = _format.replace("{yyyy}", str(now.year))
        _format = _format.replace("{mm}", str(now.month))
        _format = _format.replace("{dd}", str(now.day))
        _format = _format.replace("{hh}", str(now.hour))
        _format = _format.replace("{ii}", str(now.minute))
        _format = _format.replace("{ss}", str(now.second))
        _format = _format.replace("{time}", _time)
        # 过滤文件名的非法自负, 并替换文件名
        _format = _format.replace("filename", secure_filename(self.oriName))
        # 替换随机字符串
        rand_re = r'\{rand\:(\d*)\}'
        _pattern = re.compile(rand_re, flags=re.I)
        _match = _pattern.search(_format)
        if _match is not None:
            n = int(_match.groups()[0])
            _format = _pattern.sub(str(random.randrange(10 ** (n - 1), 10 ** n)), _format)
        _ext = self.getFileExt()
        return '%s%s' % (_format, _ext)

    def getFilePath(self):
        # 获取文件完整路径
        rootPath = self.static_folder
        filePath = ''
        for path in self.fullName.split('/'):
            filePath = os.path.join(filePath, path)
        return os.path.join(rootPath, filePath)

    def checkType(self):
        # 文件类型检测
        return self.fileType.lower() in self.config["allowFiles"]

    def checkSize(self):
        # *文件大小检测
        return self.fileSize <= self.config["maxSize"]

    def getFileInfo(self):
        filename = re.sub(r'^/', '', self.fullName)
        # 获取当前上传成功文件的各项信息
        return {
            'state': self.stateInfo,
            'url': url_for('static', filename=filename, _external=True),
            'title': self.oriName,
            'original': self.oriName,
            'type': self.fileType,
            'size': self.fileSize,
        }

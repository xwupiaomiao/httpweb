#!/usr/bin/env python
# -*- coding:utf-8 -*-
# __author__ =
# -d：指定可访问的目录，一般用于从服务器下载文件到本地
# 启动一个简易版本http服务：python3 -m http.server 8000 -d /var/log
# 返台运行脚本命令：nohup python3 webhttp.py >webhttp.log 2>&1 &

from http import HTTPStatus, server
from urllib.parse import unquote
import socketserver
import io
import cgi
import os

PORT = 8000
UPLOAD_DIR = 'uploads'

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


class UploadHandler(server.SimpleHTTPRequestHandler):
    # 把根目录改为上传目录
    def translate_path(self, path):
        # 这里重写路径，将所有访问都定位到 UPLOAD_DIR
        # 这段代码是SimpleHTTPRequestHandler原先 translate_path 的简化修改版
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # 直接使用 UPLOAD_DIR 作为根目录
        # relpath = path.lstrip('/')
        relpath = os.path.normpath(unquote(path)).lstrip(os.sep)
        full_path = os.path.join(os.path.abspath(UPLOAD_DIR), relpath)
        # 确保full_path在UPLOAD_DIR之内
        if not full_path.startswith(os.path.abspath(UPLOAD_DIR)):
            print(full_path)
            return os.path.abspath(UPLOAD_DIR)
        return full_path

    def list_directory(self, path):
        """重写目录列表显示，返回自定义的HTML页面。"""
        try:
            # 获取目录下的文件列表
            file_list = os.listdir(path)
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "No permission to list directory")
            return None

        file_list.sort(key=lambda a: a.lower())
        f = []
        displaypath = unquote(self.path)

        # 构造自定义的HTML头部
        f.append(f'<!DOCTYPE html>')
        f.append(f'<html><head><meta charset="utf-8"><title>Index of {displaypath}</title></head>')
        f.append(f'<body>')
        f.append(f'<h1>文件列表: {displaypath}</h1>')
        # pattern = "^[a-zA-Z0-9]+$"：只允许输入字母和数字
        # pattern="^[\u4e00-\u9fa5a-zA-Z0-9]+$"：只允许输入字母数字和中文字符，< !-- 中文Unicode范围 \u4e00 -\u9fa5，英文数字和中文字符允许 -->
        f.append(
            '<form enctype="multipart/form-data" method="post" action="/">姓名：<input name="user" type="text" pattern="^[\u4e00-\u9fa5a-zA-Z0-9]+$" title="只能输入字母、数字、中文字符，不能有空格和特殊字符" required/>&nbsp;&nbsp;<input name="file" type="file"/>&nbsp;&nbsp;<input type="submit" value="上传"/>')
        f.append('<hr>')
        f.append('<ul style="list-style-type: decimal">')

        # 生成文件链接, 对目录加斜杠
        for name in file_list:
            fullname = os.path.join(path, name)
            display_name = name
            link_name = name
            if os.path.isdir(fullname):
                display_name = name + "/"
                link_name = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.append(f'<li><a href="{link_name}">{display_name}</a></li>')
        f.append('</ul>\n<hr>\n</body>\n</html>\n')
        encoded = '\n'.join(f).encode('utf-8', 'surrogateescape')
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return io.BytesIO(encoded)

    def do_POST(self):
        # 解析表单数据
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))

        if ctype == 'multipart/form-data':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            # 获取上传的文件字段
            if 'file' in form:
                username = form.getvalue('user')
                file_item = form['file']
                if file_item.filename:
                    self.filename = os.path.basename(file_item.filename)
                    if self.filename in os.listdir(UPLOAD_DIR):
                        self.filename = f"{self.filename.split('.')[0]}-{username}.{self.filename.split('.')[1]}"
                    filepath = os.path.join(UPLOAD_DIR, self.filename)
                    with open(filepath, 'wb') as f:
                        f.write(file_item.file.read())
                    self.send_response(200)
                    self.end_headers()
                    html = f'''
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                      <meta http-equiv="refresh" content="1" charset="UTF-8">
                      <title>Directory listing for /</title>
                    </head>
                    <body>
                    </body>
                    <script>window.alert("文件：{self.filename} 上传成功");</script>
                    </html>
                    '''
                    self.wfile.write(html.encode('utf-8'))
                return

        # 如果上传失败
        self.send_response(400)
        self.end_headers()
        html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta http-equiv="refresh" content="1" charset="UTF-8">
          <title>Directory listing for /</title>
        </head>
        <body>
        </body>
        <script>window.alert("文件：{self.filename} 上传失败");</script>
        </html>
        '''
        self.wfile.write(html.encode('utf-8'))

    # def do_GET(self):
    #     # 打开上传页面
    #     if self.path == '/upload':
    #         self.send_response(200)
    #         self.send_header('Content-type', 'text/html')
    #         self.end_headers()
    #         html = '''
    #         <!DOCTYPE html>
    #         <html lang="en">
    #         <head>
    #           <meta charset="UTF-8">
    #           <title>上传</title>
    #         </head>
    #         <body>
    #         <h2>上传文件</h2>
    #         <form enctype="multipart/form-data" method="post" action="/upload">
    #           <input name="file" type="file"/>
    #           <input type="submit" value="上传"/>
    #         </form>
    #         </body>
    #         </html>
    #         '''
    #         self.wfile.write(html.encode('utf-8'))
    #     else:
    #         # 其他请求走默认处理，比如显示当前目录
    #         print(f"GET request for {self.path}")
    #         filepath = self.translate_path(self.path)
    #         print(f"Translated file path: {filepath}")
    #         if os.path.isfile(filepath):
    #             super().do_GET()
    #         else:
    #             self.send_error(404, "File not found")


with socketserver.TCPServer(("", PORT), UploadHandler) as httpd:
    print(f"Serving at port {PORT}, root at '{os.path.abspath(UPLOAD_DIR)}'")
    httpd.serve_forever()

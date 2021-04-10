from flask import Flask, render_template, Response, request, flash
import cv2
import pymysql
import traceback
import os

from wtforms import Form
from wtforms.fields import simple
from wtforms.fields import html5
from wtforms.fields import core
from wtforms import widgets
from wtforms import validators
import json


class VideoCamera(object):
    def __init__(self):
        # 通过opencv获取实时视频流
        self.video = cv2.VideoCapture("rtsp://admin:sunnycamel2333@192.168.1.108/Streaming/Channels/1")
        # self.video = cv2.VideoCapture(0)
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # 因为opencv读取的图片并非jpeg格式，因此要用motion JPEG模式需要先将图片转码成jpg格式图片
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

app = Flask(__name__)

@app.route("/")   # 首页
def first_page():
    return render_template('login.html')

@app.route("/login/")   # 登陆
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        message = getLoginRequest()
        flash(message)
        return render_template('login.html')

@app.route('/loginuser/') #获取登录参数及处理
def getLoginRequest():
    db = pymysql.connect(host="localhost", user="root", password="12345", database="fall")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 查询语句
    sql = "select * from UserList where uname='"+request.args.get('user')+"' and upassword='"+request.args.get('password')+"'"
    try:
        # 执行sql语句
        cursor.execute(sql)
        results = cursor.fetchall()
        print(len(results))
        if len(results) == 1:
            return render_template('host.html')
        else:
            return '用户名或密码不正确'
        # 提交到数据库执行
        db.commit()
    except:
        # 如果发生错误则回滚
        traceback.print_exc()
        db.rollback()
    # 关闭数据库连接
    db.close()

@app.route('/index/')  # 监控页面
def index():
    # jinja2模板，具体格式保存在ui-carousel.html文件中
    return render_template('index.html')


###############视频回放 ui-collapse#########################
class UserForm(Form):
    city = core.SelectField(
        label='请选择回放记录',
        choices=(),
        coerce=int
    )

    def __init__(self,*args,**kwargs):
        super(UserForm,self).__init__(*args,**kwargs)
        db = pymysql.connect(host="localhost", user="root",
                             password="12345", database="fall")
        cursor = db.cursor()                    

        # pymysql 语句
        sql="select id,createTime from VideoList"
        cursor.execute(sql)
        self.city.choices=cursor.fetchall()
        db.commit()
        # 关闭数据库连接
        db.close()



testInfo = "static/video/WebcamClip_f0.webm"
testID = 0

@app.route('/test_post/nn',methods=['GET','POST'])# ajax路由
def test_post():
    global testInfo
    return json.dumps(testInfo)

@app.route('/delete_post/nn',methods=['GET','POST'])# ajax路由
def delete_post():
    global testInfo
    global testID
    print(testInfo)
    db = pymysql.connect(host="localhost", user="root",
                         password="12345", database="fall")
    cursor = db.cursor()

    # pymysql 语句
    sql = "delete from VideoList where id="+testID
    cursor.execute(sql)
    db.commit()
    # 关闭数据库连接
    db.close()
    #delete local file
    if os.path.exists(testInfo):
        os.remove(testInfo)
    else:
        return 'unsuccessfully delete'
    return 'successfully delete'

@app.route('/ui-collapse/', methods=['GET', 'POST'],strict_slashes=False) #回放视频页面路由
def ui_collapse():
    if request.method == 'GET':
        form = UserForm()
        return render_template('ui-collapse.html', form=form)

    form = UserForm(formdata=request.form)
    if request.method == 'POST':
        global testInfo
        global testID
        testInfo= request.form.get('city') #注意表名 字段名
        testID=request.form.get('city')
        testInfo="static/video/"+testInfo+".webm" #注意格式
        return render_template('ui-collapse.html', form=form)

###########################################################


@app.route("/reg/", methods=['GET', 'POST']) # 注册页面
def reg():
    if request.method == 'GET':
        return render_template('reg.html')
    else:
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        message = getRigistRequest()
        flash(message)
        return render_template('reg.html')

@app.route("/registuser/")  # 获取注册请求及处理
def getRigistRequest():
    # 连接数据库,此前在数据库中创建数据库Fall
    db = pymysql.connect(host="localhost", user="root", password="12345", database="fall")
    # 使用cursor()方法获取操作游标
    cursor = db.cursor()
    # SQL 插入语句
    # INSERT INTO UserList VALUES(NULL,'lsk','123456');
    sql = "INSERT INTO UserList VALUES(NULL, '"+request.args.get('user')+"', '"+request.args.get('password')+"');"
    try:
        # 执行sql语句
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
        # 注册成功之后跳转到登录页面
        return render_template('login.html')
    except:
        # 抛出错误信息
        traceback.print_exc()
        # 如果发生错误则回滚
        db.rollback()
        return '注册失败'
    # 关闭数据库连接
    db.close()

@app.route("/getpass/") # 忘记密码
def getpass():
    return render_template('getpass.html')

@app.route("/host/") # 管理页面
def host():
    return render_template('host.html')

@app.route("/charts/") # 用户信息
def charts():
    return render_template('charts.html')

@app.route("/tables-basic/") # 设备信息
def table_sbasic():
    return render_template('tables-basic.html')

@app.route("/ui-cards/") # 用户权限
def ui_cards():
    return render_template('ui-cards.html')

@app.route("/ui-alerts/") # 设备设置
def ui_alerts():
    return render_template('ui-alerts.html')

@app.route("/pro-profile/") # 个人信息
def pro_profile():
    return render_template('pro-profile.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')  # 这个地址返回视频流响应
def video_feed():
        return Response(gen(VideoCamera()),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9090)
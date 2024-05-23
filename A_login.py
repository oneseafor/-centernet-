from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import A_windows
import A_sql


class LoginUi(QMainWindow):
    def __init__(self):
        # 鼠标拖动界面设置参数
        self.press_x = 0
        self.press_y = 0
        # 页面生成
        super(LoginUi, self).__init__()
        self.resize(600, 320)
        self.setWindowTitle("智慧智能教室实时管理系统")
        self.setStyleSheet("QMainWindow{border: 1px solid #303030;}")

        self.title = QLabel(self)
        self.title.setText("智慧智能教室实时管理系统")
        self.title.setFixedSize(600, 40)
        self.title.move(0, 20)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("QLabel{color:#303030;font-weight:600;font-size:30px;font-family:'宋体'; }")

        self.user_id1 = QLabel(self)
        self.user_id1.setText("账号")
        self.user_id1.setFixedSize(60, 40)
        self.user_id1.move(100, 90)
        self.user_id1.setAlignment(Qt.AlignCenter)
        self.user_id1.setStyleSheet(
            " QLabel{color:#303030;border:none;font-weight:600;font-size:25px;font-family:'宋体'; border: 1px solid #000000;}")

        self.user_id2 = QLineEdit(self)
        self.user_id2.setEchoMode(QLineEdit.Normal)  # 正常显示字符
        self.user_id2.setPlaceholderText("请输入账号...")
        self.user_id2.setFixedSize(342, 40)
        self.user_id2.move(158, 90)
        self.user_id2.setStyleSheet(
            " QLineEdit{padding-left:10px;color:#303030;font-weight:600;font-size:18px;font-family:'宋体'; border: 1px solid #000000;}")

        self.user_pwd1 = QLabel(self)
        self.user_pwd1.setText("密码")
        self.user_pwd1.setFixedSize(60, 40)
        self.user_pwd1.move(100, 150)
        self.user_pwd1.setAlignment(Qt.AlignCenter)
        self.user_pwd1.setStyleSheet(
             " QLabel{color:#303030;border:none;font-weight:600;font-size:25px;font-family:'宋体'; border: 1px solid #000000;}")

        self.user_pwd2 = QLineEdit(self)
        self.user_pwd2.setEchoMode(QLineEdit.Password)  # 显示密码字符
        self.user_pwd2.setPlaceholderText("请输入密码...")
        self.user_pwd2.setFixedSize(342, 40)
        self.user_pwd2.move(158, 150)
        self.user_pwd2.setStyleSheet(
            " QLineEdit{padding-left:10px;color:#303030;font-weight:600;font-size:18px;font-family:'宋体'; border: 1px solid #000000;}")

        self.login_btn = QPushButton(self)
        self.login_btn.setText("登录")
        self.login_btn.resize(190, 50)
        self.login_btn.move(100, 210)
        self.login_btn.setStyleSheet("QPushButton{background:#ffffff;text-align:center;font-weight:600;"
                                     "color:#000000;font-size:25px;border-radius: 25px;border: 1px solid #000000;}")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.toSystem)

        self.register_btn = QPushButton(self)
        self.register_btn.setText("注册")
        self.register_btn.resize(190, 50)
        self.register_btn.move(310, 210)
        self.register_btn.setStyleSheet("QPushButton{background:#ffffff;text-align:center;font-weight:600;"
                                        "color:#000000;font-size:25px;border-radius: 25px;border: 1px solid #000000;}")
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.clicked.connect(self.toRegister)

    # ================================ 按钮功能函数 ================================ #
    # 去系统页面
    def toSystem(self):
        op_mysql = A_sql.OperationMysql()  # 连接数据库
        users_list = op_mysql.search("select * from users;")
        login_flag = 0
        user_id = ""
        user_pwd = ""
        for i in users_list:
            if self.user_id2.text() == i['user_id'] and self.user_pwd2.text() == i['user_pwd']:
                user_id = i['user_id']
                user_pwd = i['user_pwd']
                login_flag = 1
                break
        self.user_id2.setText("")
        self.user_pwd2.setText("")
        if login_flag == 1:
            self.hide()
            A_windows.Windows.system.user_list = [user_id, user_pwd]  # 传入账号密码信息
            A_windows.Windows.system.function_label.setText("当前用户：" + user_id)
            A_windows.Windows.system.show()
        else:
            # 创建一个消息框
            msg_box = QMessageBox()
            msg_box.setWindowTitle("提示")
            msg_box.setText("账号或密码错误，请重试!")
            # 显示消息框
            msg_box.exec_()

    # 去注册页面
    def toRegister(self):
        self.user_id2.setText("")
        self.user_pwd2.setText("")
        self.hide()
        A_windows.Windows.register.show()
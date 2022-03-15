"""
用于Windows和Linux之间的文件上传、下载和提供终端执行命令
"""
import paramiko
import os
import time
import datetime
import tkinter as tk
import tkinter.messagebox
import logging
from PyQt5 import QtGui, QtWidgets, QtCore
import sys
LocalPutPath = os.getcwd() + "\\workspace" #需要上传的文件放在此目录
LocalGetPath = os.getcwd() + "downloadfile" # 从远程服务器下载的文件放在此目录
RemotePutPath = "/sysadm/"  # 上传的文件放在远程服务器的此目录
RemoteGetPath = "/sysadm/downloadfile/"  # 从远程服务器的此目录下载文件

log = logging.getLogger("Foo")
logging.basicConfig(
    level=logging.INFO, format='%(levelname)s: %(filename)s - %(message)s')
log.setLevel(logging.DEBUG)


class ConsolePanelHandler(logging.Handler):

    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        self.parent.write(self.format(record))


class Foo(QtWidgets.QWidget):

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addWidget(self.textEdit)

    def write(self, s):
        self.textEdit.setFontWeight(QtGui.QFont.Normal)
        self.textEdit.append(s)
app = QtWidgets.QApplication(sys.argv)
console_panel = Foo()
handler = ConsolePanelHandler(console_panel)
log.addHandler(handler)

class CMD:
    STOP_SELINUX="sudo setenforce 0"
    TAR_FAIL="tar -xf %s"
    REBOOT="sudo reboot"
    CHMOD_INSTALL="cd %s && chmod +x install_expect.sh"
    INSTALL_SCADA="cd %s && echo -e \'#!/usr/bin/expect \nset timeout -1 \nspawn ./install_expect.sh > install.log  \nexpect \"*用户的密码\" {\nsend \"%s\\n\"\n}\ninteract\' > install.sh && chmod +x install.sh && chmod +x install_expect.sh && ./install.sh"
    SET_SECURE="cd %s && echo -e \'#!/usr/bin/expect \nset timeout -1 \nspawn ./precautions.sh \nexpect \"*password\" {\nsend \"%s\\n\"\n}\n \nexpect \"*password\" {\nsend \"%s\\n\"\n}\ninteract\' > install2.sh && chmod +x install2.sh && chmod +x precautions.sh && ./install2.sh"
execute=CMD()
class Pysftp(object):
    """
    python3 自动上传、下载文件
    """
    global LocalPutPath, LocalGetPath, RemotePutPath, RemoteGetPath

    def __init__(self, Host, Port, User, Password):
        self.Host = Host
        self.Port = Port
        self.User = User
        self.Password = Password

    def connect(self):
        """
        建立ssh连接
        """
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.Host, self.Port, self.User, self.Password)
            return True
        except Exception:
            return False

    def cmd(self, cmd):
        """
        需要执行的命令
        """
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        print(stdout.read().decode("utf8"))

    def mkdir(self):
        """
        创建本地文件夹，存放上传、下载的文件
        """
        for lp in [LocalPutPath, LocalGetPath]:
            if not os.path.exists(lp):
                os.makedirs(lp, 666)
                print("创建本地文件夹:{}".format(lp))
            else:
                print("本地文件夹:{}已存在".format(lp))

    def put(self):
        """
        上传文件
        """
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        for root, dirs, files in os.walk(LocalPutPath):
            for fname in files:
                local_full_name = os.path.join(root, fname)
                log.info("{}\n正在上传：本地文件:{}====>远程{}:{}\n".format(datetime.datetime.now(), local_full_name,
                                                                       self.Host, RemotePutPath))
                sftp.put(local_full_name, os.path.join(RemotePutPath, fname))
                log.info("{}\n上传成功：本地文件:{}====>远程{}:{}\n".format(datetime.datetime.now(), local_full_name,
                                                                       self.Host, RemotePutPath))
            return {"FileNames": files}

    def get(self):
        """
        下载文件
        """
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        for fname in sftp.listdir(RemoteGetPath):
            try:
                if fname.startwith('result-'):
                    remote_full_name = os.path.join(RemoteGetPath, fname)
                    self.remote_done_transffer(remote_full_name)
                    sftp.get(remote_full_name, os.path.join(LocalGetPath, fname))
                    print("[{}]下载成功：远程文件{}:{}====>本地{},已删除该远程文件\n".format(datetime.datetime.now(), self.Host,
                                                                          remote_full_name, LocalGetPath))
            except Exception as e:
                print(e)

    def stat(self, fpath):
        """
        检查远程服务器文件状态
        :param fpath:文件绝对路径
        """
        sftp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
        return sftp.stat(fpath)

    def remote_done_transffer(self, fpath):
        """
        检查文件是否传输完成
        :param fpath:远程服务器上待下载文件绝对路径
        """
        while True:
            old_size = self.stat(fpath).st_size
            time.sleep(3)
            new_size = self.stat(fpath).st_size
            if new_size <= old_size:  # 传输已完成
                return

    def close(self):
        """
        关闭ssh连接
        """
        self.ssh.close()
        log.info("SSH连接关闭")

    def local_done_write(self, fpath):
        """
        检查本地文件是否已写入完成
        :param fpath:本地待上传文件绝对路径
        """
        while True:
            old_size = os.stat(fpath).st_size
            time.sleep(3)
            new_size = os.stat(fpath).st_size
            if new_size <= old_size:  # 写入已完成
                return




def ssh_login_check(ip,port,user,passwd):
    try:
        # 实例化SSHClient
        client = paramiko.SSHClient()
        # 自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接SSH服务端，以用户名和密码进行认证
        client.connect(hostname=ip, port=port, username=user, password=passwd)
        stdin, stdout, stderr = client.exec_command(execute.STOP_SELINUX)
        # 打印执行结果
        display = stdout.read().decode("utf-8")
        client.close()
        return True
    except:
        return False


def workspace_check():
    # Display().mainloop()
    pass

def message_check():
    window = tk.Tk()
    window.title('Install SCADA')
    ##窗口尺寸
    window.geometry('350x600')
    canvas = tk.Canvas(window, height=350, width=600)  # 创建画布
    image_file = tk.PhotoImage(file='welcome.gif')  # 加载图片文件
    image = canvas.create_image(0, 0, anchor="nw", image=image_file)  # 将图片置于画布上
    canvas.pack(side='top')  # 放置画布
    tk.Label(window, text='服务器IP地址: ').place(x=50, y=260)
    tk.Label(window, text='SSH端口: ').place(x=50, y=300)
    tk.Label(window, text='root用户密码: ').place(x=50, y=340)
    tk.Label(window, text='sysadm用户密码: ').place(x=50, y=380)
    tk.Label(window, text='secadm用户密码: ').place(x=50, y=420)
    # IP输入框
    ip_Addr = tk.StringVar()  # 定义变量
    ip_addr = tk.Entry(window, textvariable=ip_Addr)
    ip_addr.place(x=160, y=260)
    Port = tk.StringVar()  # 定义变量
    port = tk.Entry(window, textvariable=Port)
    port.place(x=160, y=300)
    # 密码输入框
    root_Passwd = tk.StringVar()
    root_passwd = tk.Entry(window, textvariable=root_Passwd, show='*')
    root_passwd.place(x=160, y=340)
    sysadm_Passwd = tk.StringVar()
    sysadm_passwd = tk.Entry(window, textvariable=sysadm_Passwd, show='*')
    sysadm_passwd.place(x=160, y=380)
    secadm_Passwd = tk.StringVar()
    secadm_passwd = tk.Entry(window, textvariable=secadm_Passwd, show='*')
    secadm_passwd.place(x=160, y=420)

    def passwd_check():
        global ipaddr
        ipaddr = ip_Addr.get()
        global PORT
        PORT = Port.get()
        global rootPasswd
        rootPasswd = root_Passwd.get()
        global sysadmPasswd
        sysadmPasswd = sysadm_Passwd.get()
        global secadmPasswd
        secadmPasswd = secadm_Passwd.get()

        if not ssh_login_check(ipaddr, PORT, 'secadm', secadmPasswd):
            tkinter.messagebox.askokcancel(title='错误', message='secadm密码验证失败!')
            return
        if not ssh_login_check(ipaddr, PORT, 'root', rootPasswd):
            tkinter.messagebox.askokcancel(title='错误', message='root密码验证失败!')
            return
        global obj
        obj = Pysftp(ipaddr, PORT, "sysadm", sysadmPasswd)
        if not obj.connect():
            tkinter.messagebox.askokcancel(title='错误', message='sysadm密码错误请确认!')
            obj.close()
            return
        if tkinter.messagebox.askokcancel(title='成功', message='检测完成,请选择是否进行安装!'):
            window.destroy()
    install = tk.Button(window, text='开始检测', command=passwd_check)  # 定义一个`button`按钮，,触发命令为`passwd_check`
    install.place(x=150, y=490)
    ##显示出来
    window.mainloop()

def install_SCADA():
    TarFileName = obj.put()["FileNames"][0]
    log.info("正在解压文件%s" % (TarFileName))
    obj.cmd(execute.TAR_FAIL % (TarFileName))
    Filename = TarFileName.split('.')[0]
    log.info("成功解压文件%s" % (TarFileName))
    log.info("正在执行安装，请稍后...")
    log.info("执行时间较长，请勿关闭窗口，耐心等待...")
    obj.cmd(execute.INSTALL_SCADA % (Filename, secadmPasswd))
    log.info("已经完成安装")
    obj.cmd("cat %s/install.log"%Filename)
    if tkinter.messagebox.askokcancel(title='成功', message='已经完成安装，是否进行系统安全加固！'):
        log.info("开始进行系统加固")
        obj.cmd(execute.SET_SECURE % (Filename,secadmPasswd,rootPasswd))
        log.info("已经完成系统加固,请重启主机！")
    if tkinter.messagebox.askokcancel(title='成功', message='需要进行主机重启!'):
        obj.cmd(execute.REBOOT)

    obj.close()
# def set_secuer():
#     log.info("开始进行系统加固")
#     obj.cmd(execute.SET_SECURE % (Filename,secadmPasswd,rootPasswd))
#     log.info("已经完成系统加固")


if __name__ == '__main__':
    message_check()
    install_SCADA()













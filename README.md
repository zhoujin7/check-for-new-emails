# check-for-new-emails
A python script to check for new emails and send desktop notifications (supports Linux and Windows).

Tested only on Ubuntu 18.04/Linux Mint 19, Windows 10 (Python 3.6+)

需要beautifulsoup4, Ubuntu 18.04/Linux Mint 19已自带该模块.

安装beautifulsoup4
```bash
python3 -m pip install -U beautifulsoup4
```

**Windows 10**

需要额外安装PowerShell模块: BurntToast, 使用该模块发送桌面通知.

```powershell
# 用PowerShell执行以下命令
Set-ExecutionPolicy RemoteSigned -scope CurrentUser
Set-PSRepository -Name PSGallery -InstallationPolicy Trusted
Install-Module -Name BurntToast -Scope CurrentUser
```

**Debian/Ubuntu**

默认使用`notify-send`发送桌面通知, 如果系统没有该命令, 则会使用`notify2`发送桌面通知, 所以你必须保证这两者有其一.

安装notify-send (Ubuntu 18.04/Linux Mint 19自带了该命令, Kubuntu则没有它)
```bash
# 通过apt安装
sudo apt install libnotify-bin
```

或者安装notify2
```bash
# 通过apt安装
sudo apt install python3-notify2
# 或者通过pip安装
python3 -m pip install -U notify2
```

**配置**

编辑 check_for_new_emails.py
```python
# 只在指定时间段内接收邮件 9:00-23:00
now = datetime.datetime.now().time()
# datetime.time(hour: int, minute: int, second: int)
start_time = datetime.time(9, 0, 0)
end_time = datetime.time(23, 0, 0)
if start_time < now < end_time:
    # 参数user: 邮箱帐号, password: 邮箱密码
    check_emails(host='imap.qq.com', user='account@qq.com', password='')
    check_emails(host='outlook.office365.com', user='account@outlook.com', password='')
    check_emails(host='imap.gmail.com', user='account@gmail.com', password='')
```

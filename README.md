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

**Ubuntu 18.04/Linux Mint 19**

默认使用`notify-send`发送桌面通知, 如果系统没有该命令, 则会使用`notify2`发送桌面通知, 所以你必须保证这两者有其一.

安装notify-send (Ubuntu 18.04/Linux Mint 19自带了该命令, Kubuntu则没有它)
```bash
# 通过apt安装 (on Debian/Ubuntu)
sudo apt install libnotify-bin
```

或者安装notify2
```bash
# 通过apt安装 (on Debian/Ubuntu)
sudo apt install python3-notify2
# 或者通过pip安装
python3 -m pip install -U notify2
```

import datetime
import email.policy
import imaplib
import re
import subprocess
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup


class Mail:
    """邮件详情, 包括邮件的发件人、收件人、邮件主题、接收的时间、邮件正文"""
    from_: str = ''
    to_: str = ''
    subject: str = ''
    date: str = ''
    text_content: str = ''
    html_content: str = ''


def html_to_txt(html):
    soup = BeautifulSoup(html, 'html.parser')
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('style')]
    text = re.sub(r'(\r?\n)+', ' ', soup.text)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', '').replace("'", '')
    return text


def check_emails(host='', user='', password=''):
    imap_client = imaplib.IMAP4_SSL(host)
    imap_client.login(user, password)
    imap_client.select('INBOX')
    is_ok, msg_ids = imap_client.search(None, 'UnSeen')
    for msg_id in msg_ids[0].split():
        is_ok, raw_msg = imap_client.fetch(msg_id, '(RFC822)')
        policy = email.policy.default
        msg = email.message_from_bytes(raw_msg[0][1], policy=policy)

        mail = Mail()
        mail.from_ = msg.get('From')
        mail.to_ = msg.get('To')
        mail.subject = msg.get('Subject')
        mail.date = msg.get('Date')

        body = msg.get_body(preferencelist='plain')
        if body:
            mail.text_content = body.get_content()
        body = msg.get_body(preferencelist='html')
        if body:
            mail.html_content = body.get_content()

        mail.subject = html_to_txt(mail.subject)
        if mail.text_content:
            mail.text_content = html_to_txt(mail.text_content)
        else:
            mail.text_content = html_to_txt(mail.html_content)

        notify_send(mail)


def notify_send(mail):
    if len(mail.text_content) > 200:
        mail.text_content = f'{mail.text_content[:200]}...'

    icon = Path(__file__).resolve().parent.joinpath('email.png')

    if sys.platform.startswith('linux'):
        stderr = subprocess.run(
            f"notify-send -i '{icon}' '{mail.subject}', 'From: {mail.from_}\nTo: {mail.to_}\n{mail.text_content}'",
            shell=True, encoding='utf-8', stderr=subprocess.PIPE).stderr
        if stderr:
            import notify2
            notify2.init('email')
            n = notify2.Notification(mail.subject, f'From: {mail.from_}\nTo: {mail.to_}\n{mail.text_content}', icon)
            n.show()

    elif sys.platform.startswith('win32'):
        from_to = f'From: {mail.from_} To: {mail.to_}'
        subprocess.run(
            f'''powershell -command "New-BurntToastNotification -AppLogo '{icon}'\
            -Text '{mail.subject}', '{from_to}', '{mail.text_content}'"
            ''', shell=True)

    elif sys.platform.startswith('darwin'):
        # 没有苹果电脑→_→
        pass


def main():
    while True:
        # 只在指定时间段内接收邮件 9:00-22:00
        now = datetime.datetime.now().time()
        start_time = datetime.time(9, 0, 0)
        end_time = datetime.time(22, 0, 0)
        if start_time < now < end_time:
            # 参数user: 邮箱帐号, password: 邮箱密码
            check_emails(host='imap.qq.com', user='account@qq.com', password='')
            check_emails(host='outlook.office365.com', user='account@outlook.com', password='')
            check_emails(host='imap.gmail.com', user='account@gmail.com', password='')
        # 每隔5分钟检查一次新邮件
        time.sleep(60 * 5)


if __name__ == '__main__':
    main()

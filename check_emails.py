import datetime
import email.policy
import hashlib
import imaplib
import locale
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from threading import Timer

from bs4 import BeautifulSoup

py_script_root = str(Path(__file__).resolve().parent)
email_db_path = py_script_root + os.sep + 'check_emails.db'
logging.basicConfig(filename=py_script_root + os.sep + 'check_emails.log', level=logging.ERROR)


def create_email_db(db_path):
    conn = sqlite3.connect(db_path)
    with conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='email'"
        ).fetchone()
    # 如果email表不存在则创建它
    if not table:
        conn.executescript('''\
        PRAGMA foreign_keys = false;

        DROP TABLE IF EXISTS "email";
        CREATE TABLE "email" (
          "email_hash" TEXT NOT NULL,
          "create_time" INTEGER NOT NULL,
          PRIMARY KEY ("email_hash")
        );

        PRAGMA foreign_keys = true;
        ''')
    conn.close()


def cleanup_email_db():
    """每隔7天清理一次7天之前的表记录(如果一直不关机的话)"""
    conn = sqlite3.connect(email_db_path)
    with conn:
        conn.execute("DELETE FROM email WHERE create_time < (strftime('%s','now') - 60*60*24*7)")
    conn.close()
    Timer(60 * 60 * 24 * 7, cleanup_email_db).start()


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
    if sys.platform.startswith('linux'):
        text = text.replace('"', r'\"')
    elif sys.platform.startswith('win32'):
        text = text.replace("'", "''").replace("‘","‘‘").replace("’","’’")
    elif sys.platform.startswith('darwin'):
        # 没有苹果电脑→_→
        pass
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
        mail.from_ = html_to_txt(mail.from_)
        mail.to_ = html_to_txt(mail.to_)
        if mail.text_content:
            mail.text_content = html_to_txt(mail.text_content)
        else:
            mail.text_content = html_to_txt(mail.html_content)

        if is_new_email(mail):
            try:
                notify_send(mail)
            except Exception as e:
                logging.error(e)
                logging.error(f'Subject: {mail.subject}\nFrom: {mail.from_}\nTo: {mail.to_}')
                alert('Error occurred when call notify_send, see check_emails.log for details.')


def is_new_email(mail):
    mail_str = f'{mail.from_}{mail.to_}{mail.subject}{mail.date}{mail.text_content}{mail.html_content}'
    email_hash = hashlib.md5(mail_str.encode('utf-8')).hexdigest()
    conn = sqlite3.connect(email_db_path)
    with conn:
        old_email = conn.execute(
            "SELECT email_hash, create_time FROM email WHERE email_hash = ?", (email_hash,)
        ).fetchone()
    if old_email:
        conn.close()
        return False
    else:
        create_time = int(datetime.datetime.now().timestamp())
        with conn:
            conn.execute("INSERT INTO email(email_hash, create_time) VALUES (?, ?)", (email_hash, create_time))
        conn.close()
        return True


def notify_send(mail):
    if len(mail.text_content) > 200:
        mail.text_content = f'{mail.text_content[:200]}...'

    icon = py_script_root + os.sep + 'check_emails.png'

    if sys.platform.startswith('linux'):
        completed_process = subprocess.run(
            f'''notify-send -i "{icon}" "{mail.subject}" "From: {mail.from_}\nTo: {mail.to_}\n{mail.text_content}"''',
            shell=True, encoding=locale.getdefaultlocale()[1], stderr=subprocess.PIPE)
        if completed_process.returncode == 127:
            import notify2
            notify2.init('email')
            n = notify2.Notification(f"{mail.subject}", f"From: {mail.from_}\nTo: {mail.to_}\n{mail.text_content}",
                                     f"{icon}")
            n.show()
        elif completed_process.returncode != 0:
            logging.error(completed_process.stderr)
            logging.error(f'Subject: {mail.subject}\nFrom: {mail.from_}\nTo: {mail.to_}')
            alert('Error occurred when invoke notify-send, see check_emails.log for details.')

    elif sys.platform.startswith('win32'):
        from_to = f'From: {mail.from_} To: {mail.to_}'
        completed_process = subprocess.run(
            f'''powershell -command "New-BurntToastNotification -AppLogo '{icon}'\
            -Text '{mail.subject}', '{from_to}', '{mail.text_content}'"
            ''', shell=True, encoding=locale.getdefaultlocale()[1], stderr=subprocess.PIPE)
        if completed_process.returncode:
            logging.error(completed_process.stderr)
            logging.error(f'Subject: {mail.subject}\nFrom: {mail.from_}\nTo: {mail.to_}')
            alert('Error occurred when invoke New-BurntToastNotification, see check_emails.log for details.')

    elif sys.platform.startswith('darwin'):
        # 没有苹果电脑→_→
        pass


def alert(message):
    if sys.platform.startswith('linux'):
        returncode = subprocess.run(
            f'''zenity --error --text="{message}" --width=300''',
            shell=True, encoding=locale.getdefaultlocale()[1], stderr=subprocess.PIPE).returncode
        if returncode == 127:
            subprocess.run(
                f'''xmessage -center "{message}"''',
                shell=True, encoding=locale.getdefaultlocale()[1], stderr=subprocess.PIPE)

    elif sys.platform.startswith('win32'):
        subprocess.run(
            f'''powershell -command "Add-Type -AssemblyName PresentationFramework;\
                [System.Windows.MessageBox]::Show('{message}','Error','OK','Error') | Out-Null"
            ''', shell=True, encoding=locale.getdefaultlocale()[1], stderr=subprocess.PIPE)

    elif sys.platform.startswith('darwin'):
        # 没有苹果电脑→_→
        pass


def main():
    create_email_db(email_db_path)
    cleanup_email_db()
    while True:
        # 只在指定时间段内接收邮件 9:00-22:00
        now = datetime.datetime.now().time()
        # datetime.time(hour: int, minute: int, second: int)
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

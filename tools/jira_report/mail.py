from email.mime import text
import smtplib
import socket
import ssl
import threading


class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn

DNS_NAME = CachedDnsName()


class EmailBackend(object):

    def __init__(self, host=None, port=None, username=None,
                 password=None, use_tls=None, use_ssl=None,
                 from_email=None, timeout=None,
                 fail_silently=False, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.from_email = from_email
        self.timeout = timeout
        self.fail_silently = fail_silently

        self.connection = None
        self._lock = threading.RLock()

    def open(self):
        if self.connection:
            return False
        connection_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

        connection_params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        try:
            self.connection = connection_class(self.host, self.port,
                                               **connection_params)
            self.connection.set_debuglevel(1)
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
        except smtplib.SMTPException:
            print ("failed to open smtp connection")
            if not self.fail_silently:
                raise
        return True

    def close(self):
        if self.connection is None:
            return
        try:
            try:
                self.connection.quit()
            except (ssl.SSLError, smtplib.SMTPServerDisconnected):
                print ("failed to close smtp connection")
                self.connection.close()
            except smtplib.SMTPException:
                print ("failed to close smtp connection")
                if not self.fail_silently:
                    raise
        finally:
            self.connection = None

    def send_message(self, recipients, subject, message, type='html', **kwargs):
        if not message:
            return
        with self._lock:
            new_conn_created = self.open()
            if not self.connection:
                print ("failed to open smtp connection on %s:%s" % (
                    self.host, self.port))
                return
            msg = text.MIMEText(message, type, 'utf-8')
            msg['From'] = self.from_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            self.connection.sendmail(msg['From'], recipients, msg.as_string())
            if new_conn_created:
                self.close()


if __name__ == '__main__':
    c = EmailBackend(host="192.168.0.185",
                     port="25",
                     use_tls=False,
                     username="username",
                     password="password",
                     from_email="from@email.com")
    c.send_message(["guangyu@unitedstack.com", "578579544@qq.com"],
                   "hello", "this is a test from ustack")

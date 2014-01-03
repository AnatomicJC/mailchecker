#!/usr/bin/python
import DNS
import smtplib
import sys
import string  # string.ascii_letters
import random
import re
import logging
from optparse import OptionParser
from colorlog import get_logger


class CheckMail(object):
    def __init__(self, fakedomain='example.com', fakeuser='johndoe', log=False):
        self.fakedomain = fakedomain
        self.fakeuser = fakeuser
        self.smtp = smtplib.SMTP()
        DNS.DiscoverNameServers()
        self.logger = log and log or logging.getLogger()
        self.domain = ''
        self.mx_hosts = []

    def get_mx_hosts(self, mail):
        domain = mail.split('@')[1]
        if domain != self.domain or not self.mx_hosts:
            self.domain = domain
            try:
                self.mx_hosts = DNS.mxlookup(self.domain)
            except DNS.Base.ServerError:
                self.logger.error('It seems this domain has no MX entry: %s' % self.domain)
                sys.exit(1)
        self.logger.debug('MX hosts for domain %s:' % self.domain)
        for priority, mail_server in self.mx_hosts:
            self.logger.debug(" * %s %s" % (priority, mail_server))
        return self.mx_hosts

    def generate_random_user(self, size=12, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    def mail_server_accepts_all_mails(self):
        self.logger.debug('I will check if mail server accepts all mails')
        extra_check_result = True
        for x in xrange(3):
            random_user = self.generate_random_user()
            random_mail = '@'.join([random_user, self.domain])
            self.logger.debug('I will check if %s exists' % random_mail)
            code, msg = self.smtp.rcpt(random_mail)
            if code != 250:
                extra_check_result = False
                break
        if extra_check_result:
            self.logger.warn('This mail server seems to accept all mails addresses')
            return True
        return False

    def is_email(self, mail):
        email_re = re.compile(
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
            r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE)  # domain
        return email_re.search(mail)

    def exists(self, mail, extra_checking=False):
        if not self.is_email(mail):
            self.logger.warn('%s seems to not be a valid mail address' % mail)
            sys.exit(1)

        self.logger.debug("I will check if %s exists" % mail)
        for priority, mail_server in self.get_mx_hosts(mail):
            try:
                self.logger.debug('Connecting to %s %s' % (priority, mail_server))
                self.smtp.connect(mail_server)
            except smtplib.SMTPConnectError:
                self.logger.debug('Connection to %s failed' % (priority, mail_server))
                continue

            code, msg = self.smtp.helo(self.fakedomain)
            if code != 250:
                self.logger.error('HELO step failed: %s %s' % (code, msg))

            code, msg = self.smtp.mail('@'.join([self.fakeuser, self.fakedomain]))
            if code != 250:
                self.logger.error('MAIL FROM step failed: %s' % msg)

            code, msg = self.smtp.rcpt(mail)
            if code == 250:
                if extra_checking:
                    if self.mail_server_accepts_all_mails():
                        return False
                self.logger.info("Mail address %s exists." % mail)

                self.smtp.close()
                return True
            elif code == 450:
                self.logger.info("MX server %s uses greylisting... Try again in 1 or 2 minutes" % mail_server)
            else:
                self.logger.debug("Return code %s: %s" % (code, msg))
                self.logger.warn("Mail address %s doesn't exists." % mail)
            self.smtp.close()
            return False

if __name__ == "__main__":
    parser = OptionParser(usage="usage: %prog [options] mail_address")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                      help="Print debug messages")
    parser.add_option("--disable-extra-checking", action="store_true", dest="disable_extra_checking", default=False,
                      help="Disable extra-checking")

    # Parse and analyse args
    (options, args) = parser.parse_args()
    if options.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    extra_checking = True
    if options.disable_extra_checking:
        extra_checking = False

    if len(args) == 0:
        parser.print_help()
        sys.exit(0)

    log = get_logger(level)
    cm = CheckMail(log=log)
    for mail in args:
        cm.exists(mail, extra_checking)

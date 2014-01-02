mailchecker
===========

Check if a given mail address exists on a mail server

---

Usually, I search MX servers of a domain and use telnet with HELO, MAIL FROM and RCPT TO for checking if a mail address exists.

I wrote this small python script to do the job.

First, it gets list of mail servers of mail's domain, then it checks if mail address exists.

Usage:

    Usage: mailchecker.py [options] mail_address
    Options:
      -h, --help            show this help message and exit
      -d, --debug           Print debug messages
      --disable-extra-checking
                            Disable extra-checking

You need python-dns as dependency:

    # aptitude install python-dns

### Examples ###

    $ python mailchecker.py postmaster@gmail.com
    INFO    Mail address postmaster@gmail.com exists.

Some servers like Yahoo accept all mails and don't tell you if the mail address really exists:

    $ python mailchecker.py ooz9mahLee3aahag@yahoo.com
    WARNING This mail server seems to accept all mails addresses

Some servers use greylisting such as no-log.org:

    $ python mailchecker.py a-mail-address@no-log.org
    INFO    MX server mail.no-log.org uses greylisting... Try again in 1 or 2 minutes

In that case, try again 1 or 2 minutes later:

    $ python mailchecker.py a-mail-address@no-log.org
    WARNING Mail address a-mail-address@no-log.org doesn't exists.

Debug mode will tells you more what script is actually doing:

    $ python mailchecker.py -d a-mail-address@no-log.org
    DEBUG   I will check if a-mail-address@no-log.org exists
    DEBUG   MX hosts for domain no-log.org:
    DEBUG    * 10 mail.no-log.org
    DEBUG   Connecting to 10 mail.no-log.org
    DEBUG   Return code 550: 5.1.1 <a-mail-address@no-log.org>: Recipient address rejected: User unknown in virtual mailbox table
    WARNING Mail address a-mail-address@no-log.org doesn't exists.

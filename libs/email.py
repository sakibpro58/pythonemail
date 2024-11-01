import smtplib

def checkemail(email, mx):
    try:
        server = smtplib.SMTP()
        server.set_debuglevel(1)  # Enable verbose SMTP logging
        server.connect(mx)
        server.helo('Alice')
        server.mail('me@domain.com')
        code, message = server.rcpt(str(email))
        server.quit()
        return code, message.decode('utf-8'), 0  # Decode the message to a string
    except Exception as e:
        print('[!] Error connecting to SMTP server: {0}'.format(str(e)))
        return 666, str(e)

def findcatchall(email, mx):
    try:
        domain = email.split('@')[1]
        fake_email = 'thisisnotavalidemailaddress123456zzz@{0}'.format(domain)
        fake = checkemail(fake_email, mx)
        if fake[0] == 250:
            return 1
        else:
            return 0
    except Exception as e:
        print('[!] Catch All Error: {0}'.format(str(e)))
        return 0

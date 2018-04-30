import urllib2

import sendgrid
from sendgrid.helpers import mail

from flask import Flask, request


app = Flask(__name__)


SENDGRID_API_KEY = '<SENDGRID_API_KEY>'


ERR_MSG = '''
    Dear {email}

    Problem with Url: {url}
    Expected Status Code: {exp_status}
    Response Status Code: {status}

    Please contact your admin to fix it.

    Thanks,
    Hyperion

'''


def send_email_from_sendgrid(subject, body, recipient, sender):
    # sendgrid email
    sg = sendgrid.SendGridAPIClient(apikey=SENDGRID_API_KEY)
    to_email = mail.Email(recipient)
    from_email = mail.Email(sender)
    content = mail.Content('text/plain', body)
    message = mail.Mail(from_email, subject, to_email, content)
    # TODO: uncomment below lines in production
    response = sg.client.mail.send.post(request_body=message.get())
    print(response)


def send_email_to_user(recipient, exp_status, status, url):

    body = ERR_MSG.format(
        email=recipient, exp_status=exp_status, status=status, url=url)
    subject = 'Hyperion: {sub}'
    if status is None:
        subject = subject.format(
            sub="No response recieved from URL: %s" % (url))
    else:
        subject = subject.format(
            sub="Status code Mismatched at URL: %s" % (url))

    sender = 'hyperion@appspot.gserviceaccount.com'
    send_email_from_sendgrid(subject, body, recipient, sender)
    # google app engine email not working
    # message = mail.EmailMessage(
    #     sender=sender,
    #     subject=subject
    # )
    # message.to = '<%s>' % (email)
    # message.body = body
    # message.send()

    return body


@app.route('/')
def hello():
    return "Hello World"


@app.route('/check_status_code')
def check_status_code():
    url = request.args.get('url')
    exp_status_code = int(request.args.get('status'))
    email = request.args.get('email')

    # urllib2 check
    try:
        result = urllib2.urlopen(url)
        if result.code != exp_status_code:
            return send_email_to_user(email, exp_status_code, result.code, url)
    except urllib2.HTTPError as e:
        if hasattr(e, 'code'):
            if e.code != exp_status_code:
                return send_email_to_user(email, exp_status_code, e.code, url)
        raise e
    except Exception:
        return send_email_to_user(email, exp_status_code, None, url)
    # end
    return "200 OK"


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)

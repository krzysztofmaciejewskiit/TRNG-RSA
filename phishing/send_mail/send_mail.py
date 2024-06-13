import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Dane do logowania do serwera SMTP
smtp_server = 'mail.usos-uksw-edu.online'
port = 587
login = 'USOS@usos-uksw-edu.online'
password = 'YZL3ykxrcCG5GHRVZZrZ'

# Aktualna data i czas
subject = 'Twoje hasło w systemie USOS zostało zmienione.'

# Odczytanie adresów email z pliku
with open('emails.txt', 'r') as file:
    emails = file.read().splitlines()

# Ustanowienie połączenia z serwerem SMTP
with smtplib.SMTP(smtp_server, port) as server:
    server.login(login, password)

    for email in emails[:108]:
        body = f"""
        <html>
        <head></head>
        <body>
        <p># UWAGA -- Poniższa wiadomość nie posiada adresu zwrotnego. Prosimy na nią nie odpowiadać.</p>
        <p>Twoje hasło dla konta <a href="http://www.usos-uksw-edu.online/" style="color:blue"><u>{email}</u></a> w systemie USOS zostało zmienione.</p>
        <p>Jeżeli zmiana została dokonana przez Ciebie możesz zignorować tego maila.</p>
        
        Informacje:<br>
        Kraj: Polska<br>
        System: Windows 10<br>
        Przeglądarka: Google Chrome<br><br>
        
        Jeśli prośba o zmianę hasła nie została wysłana przez ciebie, twoje konto może być zagrożone. Postępuj zgodnie z wytycznymi:<br>
        <a href="http://www.usos-uksw-edu.online/" style="color:blue">1. <u>Zresetuj swoje hasło.</u></a><br>
        <a href="http://www.usos-uksw-edu.online/" style="color:blue">2. <u>Zgłoś to do administratora.</u></a><br>
        <a href="http://www.usos-uksw-edu.online/" style="color:blue">3. <u>Dowiedz się jak chronić swoje konto.</u></a><br>
        
        <p>--</p>
        Wiadomość wysłana przez system USOS.<br>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = login
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            server.sendmail(login, email, msg.as_string())
            print(f'Email wysłany do {email}')
        except Exception as e:
            print(f'Nie udało się wysłać emaila do {email}: {e}')

print('Wszystkie wiadomości zostały wysłane.')
# contains the texts of the notification emails in plain text and HTML format

class MailContent:

    def __init__(self, plain_version, html_version):
        self.plain_version = plain_version
        self.html_version = html_version

lsc_mail = MailContent('''\
                Lieber Herr %s,
                (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                Dies ist eine LSC-Testmail für
                www.laws-of-social-cohesion.de''', 
                
                '''\
                <html>
                    <body>
                    <p>Sehr geehrter Herr %s,<br>
                        <br>
                        wir aktualisieren gerade die Events auf der Seite des Projekts "Laws of Social Cohesion" und mir ist 
                        aufgefallen, dass dort eine Veranstaltung mit %s gelistet ist. Es wäre für mich wichtig zu erfahren, ob diese
                        Veranstaltung als "Hosted by LSI/FUELS/RiK" gekennzeichnet wurde. Wenn das der Fall ist, würde ich mich freuen,
                        wenn Sie mich darüber hier informieren könnten. Bitte folgen Sie dem Link auch dann, wenn die Veranstaltung
                        nicht von den einer der drei Partnerinstitutionen ausgerichtet werden sollte und Sie die Veranstaltung nicht
                        weiter auf der Website führen möchten (z. B. weil die Veranstaltung veraltet ist).
                        Soll ich die Meldung beibehalten, würde ich sie in folgender Form auf der Website aufführen:<br>
                        %s 
                        Sollten die Meldung entfernt werden, klicken Sie bitte <a href="%s">hier</a>. Sollten anderweitige Probleme
                        bestehen, helfe ich immer gerne.<br>
                        <br>
                        <br>
                        Mit freundlichen Grüßen,<br>
                        Ihr Benjamin Mantay<br>
                        <br>
                        -------------<br>
                        <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                        Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                        <br>
                        <br>
                        <br>
                    </p>
                    </body>
                </html>
                ''')

institute_mail = MailContent('''\
                    Lieber Herr %s,
                    (das ist die plain-text version der Email, bei Gelegenheit noch ergänzen)
                    Dies ist eine LSC-Testmail für
                    www.laws-of-social-cohesion.de''', 
                    
                    '''\
                    <html>
                        <body>
                        <p>Sehr geehrter Herr %s,<br>
                            <br>
                            eben ist mir aufgefallen, dass heute eine Veranstaltung mit %s auf der
                            Website gelistet wurde. Soll ich das Event auf die LSC-Seite übertragen? Falls ja, würde ich die Meldung
                            folgendermaßen gestalten:<br>
                            <h3><a href="%s">%s</a></h3>
                                    <blockquote>
                                    <p>%s, %s (physical/virtual event)</p>
                                    <p>Seminar with <strong>%s</strong> %s</p>
                                    <p>Hosted by FUELS</p>
                                    </blockquote>
                            Wenn diese Veranstaltung nicht der LSC-Seite hinzugefügt werden soll, klicken Sie bitte <a href="%s">hier</a>. 
                            Möchten Sie die Meldung in ihrer jetzigen Form annehmen, klicken Sie bitte <a href="%s">hier</a>. Sollten Sie die 
                            Meldung hochladen wollen, die Meldung aber fehlerhaft sein, können Sie mich darüber per Klick hier 
                            informieren. Sie brauchen sonst nichts weiter zu unternehmen. Ich lade sie dann später korrigiert hoch 
                            und lasse davor noch einmal einen Menschen einen Blick darauf werfen. Sollten anderweitige Probleme 
                            bestehen, helfe ich immer gerne.<br>
                            <br>
                            <br>
                            Mit freundlichen Grüßen,<br>
                            Ihr Benjamin Mantay<br>
                            <br>
                            -------------<br>
                            <a href="https://www.jura.fu-berlin.de/fachbereich/einrichtungen/zivilrecht/lehrende/engerta/Team/5_Externe-Wissenschaftler_innen/Benji">Dr. can. Benjamin Mantay</a> <br>
                            Head of IT und Tierischer Wissenschaftler (Postdog) am Lehrstuhl Engert<br>
                            <br>
                            <br>
                            <br>
                        </p>
                        </body>
                    </html>
                    ''')
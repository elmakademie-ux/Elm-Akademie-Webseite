"""
Die 15 Muster-E-Mails aus "DTZ B1.1 – 15 Muster-E-Mails" (Übungshilfen, keine offiziellen Prüfungslösungen).

Jede E-Mail:
  absaetze = Liste (Text, Punkt) – Punkt = Index des Aufgaben-Punktes (0–3), den der Absatz beantwortet,
             oder None (z. B. Einleitung/Bitte ohne eigenen Punkt)
"""

AUFGABEN = {
    1: dict(thema="Fernsehzeitschrift kündigen",
            text="Sie haben die Fernsehzeitschrift „TV aktuell“ abonniert. Die Zeitschrift gefällt Ihnen "
                 "nicht mehr und Sie möchten das Abonnement kündigen.",
            punkte=["Grund", "Was gefällt nicht?", "Kündigungstermin", "Bestätigung"]),
    2: dict(thema="Termin beim Jobcenter",
            text="Sie möchten mehr über Ihre Berufsmöglichkeiten erfahren und einen Termin bei Frau "
                 "Heberlein vom Jobcenter vereinbaren.",
            punkte=["Grund", "Wer Sie sind", "Schule & Fächer", "Interessen & Hobbys"]),
    3: dict(thema="Das Auto des Nachbarn ausleihen",
            text="Sie möchten am nächsten Samstag im Baumarkt einkaufen. Ihr Auto ist kaputt. Sie möchten "
                 "das Auto Ihres Nachbarn, Herrn Scholz, ausleihen.",
            punkte=["Grund", "Wie lange?", "Etwas mitbringen", "Zum Essen einladen"]),
    4: dict(thema="Kollegin zum Essen einladen",
            text="Sie sind aufs Land gezogen und möchten nächstes Wochenende eine Kollegin oder einen "
                 "Kollegen zum Essen einladen.",
            punkte=["Warum aufs Land?", "Neue Wohnung", "Wann ist das Essen?", "Etwas mitbringen"]),
    5: dict(thema="Einen kranken Kollegen vertreten",
            text="Ihr Kollege Herr Müller ist krank. Sie übernehmen seine Arbeit und informieren ihn über "
                 "die Neuigkeiten.",
            punkte=["Was gearbeitet?", "Neuigkeiten", "Problem", "Gesundheit"]),
}

EMAILS = [
    # ---------------------------------------------------------------- Aufgabe 1
    dict(aufgabe=1, beispiel=1, betreff="Kündigung meines Abonnements",
         anrede="Sehr geehrte Damen und Herren,",
         absaetze=[("ich schreibe Ihnen, weil ich mein Abonnement kündigen möchte.", 0),
                   ("Die Zeitschrift gefällt mir nicht mehr, weil die Artikel oft langweilig sind. "
                    "Außerdem bekomme ich sie manchmal zu spät.", 1),
                   ("Ich möchte mein Abonnement zum nächsten Monat kündigen. Bitte sagen Sie mir, "
                    "wann das möglich ist.", 2),
                   ("Könnten Sie mir bitte eine Bestätigung schicken?", 3),
                   ("Vielen Dank für Ihre Hilfe.", None)],
         gruss="Mit freundlichen Grüßen", name="Ali Hassan"),
    dict(aufgabe=1, beispiel=2, betreff="Ich möchte mein Abo kündigen",
         anrede="Sehr geehrte Damen und Herren,",
         absaetze=[("seit einem Jahr bekomme ich Ihre Zeitschrift. Jetzt möchte ich das Abonnement "
                    "kündigen, weil ich sie nicht mehr lese.", 0),
                   ("Die Zeitschrift ist mir zu teuer. Außerdem habe ich nicht genug Zeit zum Lesen.", 1),
                   ("Deshalb möchte ich mein Abo zum nächstmöglichen Termin beenden.", 2),
                   ("Bitte schicken Sie mir eine Bestätigung, damit ich weiß, dass alles erledigt ist.", 3),
                   ("Vielen Dank im Voraus.", None)],
         gruss="Mit freundlichen Grüßen", name="Sara Ahmed"),
    dict(aufgabe=1, beispiel=3, betreff="Kündigung der Zeitschrift",
         anrede="Sehr geehrte Damen und Herren,",
         absaetze=[("ich möchte meine Zeitschrift „TV aktuell“ kündigen, weil ich nicht mehr zufrieden bin.", 0),
                   ("Früher habe ich die Zeitschrift gerne gelesen, aber jetzt interessieren mich die Themen "
                    "nicht mehr. Außerdem möchte ich Geld sparen.", 1),
                   ("Bitte kündigen Sie mein Abonnement zum nächsten möglichen Termin.", 2),
                   ("Könnten Sie mir bitte schriftlich bestätigen, dass Sie meine Kündigung bekommen haben?", 3),
                   ("Vielen Dank.", None)],
         gruss="Mit freundlichen Grüßen", name="Mohammed Ali"),
    # ---------------------------------------------------------------- Aufgabe 2
    dict(aufgabe=2, beispiel=1, betreff="Bitte um einen Termin",
         anrede="Sehr geehrte Frau Heberlein,",
         absaetze=[("ich schreibe Ihnen, weil ich mehr über meine Berufsmöglichkeiten wissen möchte.", 0),
                   ("Mein Name ist Ahmad Karim. Ich bin 19 Jahre alt und besuche zurzeit einen Deutschkurs.", 1),
                   ("In meinem Heimatland war ich in der Schule. Meine Lieblingsfächer waren Mathematik und "
                    "Informatik, weil ich gerne mit Computern arbeite.", 2),
                   ("In meiner Freizeit spiele ich Fußball und höre Musik. Außerdem möchte ich gerne eine "
                    "Ausbildung machen.", 3),
                   ("Könnten Sie mir bitte einen Termin geben, damit wir darüber sprechen können?", None),
                   ("Vielen Dank.", None)],
         gruss="Mit freundlichen Grüßen", name="Ahmad Karim"),
    dict(aufgabe=2, beispiel=2, betreff="Beratung über meine berufliche Zukunft",
         anrede="Sehr geehrte Frau Heberlein,",
         absaetze=[("ich möchte gerne einen Termin bei Ihnen machen, weil ich eine Ausbildung finden möchte.", 0),
                   ("Mein Name ist Fatima Ali. Ich bin 22 Jahre alt und wohne seit zwei Jahren in Deutschland.", 1),
                   ("In meinem Heimatland habe ich die Schule besucht. Meine Lieblingsfächer waren Deutsch und "
                    "Englisch, weil ich gerne Sprachen lerne.", 2),
                   ("In meiner Freizeit lese ich Bücher und treffe meine Freunde. Außerdem möchte ich gerne als "
                    "Erzieherin arbeiten.", 3),
                   ("Könnten Sie mir bitte sagen, welche Möglichkeiten ich habe?", None),
                   ("Ich freue mich auf Ihre Antwort.", None)],
         gruss="Mit freundlichen Grüßen", name="Fatima Ali"),
    dict(aufgabe=2, beispiel=3, betreff="Anfrage für einen Beratungstermin",
         anrede="Sehr geehrte Frau Heberlein,",
         absaetze=[("ich schreibe Ihnen, weil ich einen passenden Beruf finden möchte.", 0),
                   ("Mein Name ist Omar Hassan. Ich bin 20 Jahre alt und habe in meinem Heimatland die Schule "
                    "besucht.", 1),
                   ("Biologie und Chemie waren meine Lieblingsfächer. Ich interessiere mich für Medizin, weil ich "
                    "gerne Menschen helfen möchte.", 2),
                   ("In meiner Freizeit treibe ich Sport und lese Bücher. Außerdem möchte ich später im "
                    "Krankenhaus arbeiten.", 3),
                   ("Ich möchte gerne wissen, ob ich eine Ausbildung im Krankenhaus machen kann.", None),
                   ("Könnten Sie mir bitte einen Termin geben?", None)],
         gruss="Mit freundlichen Grüßen", name="Omar Hassan"),
    # ---------------------------------------------------------------- Aufgabe 3
    dict(aufgabe=3, beispiel=1, betreff="Eine kleine Bitte",
         anrede="Lieber Herr Scholz,",
         absaetze=[("ich habe eine kleine Bitte. Am Samstag möchte ich zum Baumarkt fahren, weil ich einige "
                    "Sachen kaufen muss.", 0),
                   ("Leider ist mein Auto kaputt. Deshalb möchte ich Sie fragen, ob ich Ihr Auto ausleihen kann.", 0),
                   ("Ich brauche das Auto ungefähr drei Stunden. Danach bringe ich es Ihnen zurück.", 1),
                   ("Wenn Sie auch etwas kaufen möchten, kann ich es gerne für Sie mitbringen.", 2),
                   ("Als Dankeschön möchte ich Sie am Samstag zum Essen einladen.", 3),
                   ("Vielen Dank für Ihre Hilfe!", None)],
         gruss="Viele Grüße", name="Ali"),
    dict(aufgabe=3, beispiel=2, betreff="Darf ich Ihr Auto benutzen?",
         anrede="Lieber Herr Scholz,",
         absaetze=[("am nächsten Samstag muss ich zum Baumarkt fahren. Leider funktioniert mein Auto nicht mehr.", 0),
                   ("Könnten Sie mir bitte Ihr Auto leihen? Ich brauche es nur von 10 bis 13 Uhr.", 1),
                   ("Wenn Sie etwas aus dem Baumarkt brauchen, kann ich es auch für Sie kaufen.", 2),
                   ("Ich möchte mich bei Ihnen bedanken, deshalb lade ich Sie gerne am Sonntag zum "
                    "Mittagessen ein.", 3),
                   ("Bitte schreiben Sie mir, ob das möglich ist.", None)],
         gruss="Viele Grüße", name="Mohammed"),
    dict(aufgabe=3, beispiel=3, betreff="Bitte um Ihr Auto",
         anrede="Lieber Herr Scholz,",
         absaetze=[("mein Auto ist leider kaputt, deshalb brauche ich Ihre Hilfe.", 0),
                   ("Am Samstag möchte ich im Baumarkt einkaufen, weil ich neue Möbel brauche. Darf ich dafür "
                    "Ihr Auto benutzen?", 0),
                   ("Ich brauche es ungefähr vier Stunden. Natürlich werde ich vorsichtig fahren und das Auto "
                    "wieder zurückbringen.", 1),
                   ("Möchten Sie auch etwas aus dem Baumarkt haben? Dann kann ich es gerne mitbringen.", 2),
                   ("Als Dankeschön möchte ich Sie zum Abendessen einladen.", 3),
                   ("Ich freue mich auf Ihre Antwort.", None)],
         gruss="Viele Grüße", name="Ahmad"),
    # ---------------------------------------------------------------- Aufgabe 4
    dict(aufgabe=4, beispiel=1, betreff="Einladung zum Essen",
         anrede="Liebe Anna,",
         absaetze=[("wie geht es dir?", None),
                   ("Ich bin vor zwei Wochen aufs Land gezogen, weil es dort ruhiger ist.", 0),
                   ("Meine neue Wohnung ist sehr schön. Sie hat drei Zimmer und einen großen Balkon. Außerdem "
                    "gibt es einen kleinen Garten.", 1),
                   ("Ich möchte dich gerne am Samstag um 18 Uhr zum Abendessen einladen.", 2),
                   ("Kannst du bitte einen Salat mitbringen, wenn du Zeit hast?", 3),
                   ("Ich freue mich auf deinen Besuch!", None)],
         gruss="Liebe Grüße", name="Fatima"),
    dict(aufgabe=4, beispiel=2, betreff="Besuch in meiner neuen Wohnung",
         anrede="Lieber Michael,",
         absaetze=[("ich habe eine neue Wohnung auf dem Land. Ich bin umgezogen, weil es in der Stadt zu "
                    "laut war.", 0),
                   ("Meine Wohnung ist nicht sehr groß, aber sie ist gemütlich. Besonders schön finde ich den "
                    "Balkon.", 1),
                   ("Am Sonntag möchte ich dich zum Mittagessen einladen. Wir können zusammen essen und danach "
                    "spazieren gehen.", 2),
                   ("Könntest du vielleicht einen Kuchen mitbringen? Ich möchte gerne einen Nachtisch haben.", 3),
                   ("Ich hoffe, dass du kommen kannst.", None)],
         gruss="Viele Grüße", name="Omar"),
    dict(aufgabe=4, beispiel=3, betreff="Einladung zum Essen",
         anrede="Liebe Sara,",
         absaetze=[("ich möchte dich gerne in meine neue Wohnung einladen.", None),
                   ("Ich bin aufs Land gezogen, weil ich mehr Ruhe haben möchte. Außerdem ist die Luft hier "
                    "besser.", 0),
                   ("Meine neue Wohnung hat vier Zimmer und eine große Küche. Sie gefällt mir sehr gut.", 1),
                   ("Hast du am nächsten Samstag Zeit? Ich möchte dich um 13 Uhr zum Mittagessen einladen.", 2),
                   ("Wenn du möchtest, kannst du etwas zu trinken mitbringen. Ich werde das Essen vorbereiten.", 3),
                   ("Ich freue mich, wenn du kommst.", None)],
         gruss="Liebe Grüße", name="Maryam"),
    # ---------------------------------------------------------------- Aufgabe 5
    dict(aufgabe=5, beispiel=1, betreff="Neuigkeiten von der Arbeit",
         anrede="Lieber Herr Müller,",
         absaetze=[("wie geht es Ihnen? Ich hoffe, dass Sie bald wieder gesund werden.", 3),
                   ("In den letzten Tagen habe ich Ihre Arbeit übernommen. Ich habe E-Mails beantwortet und mit "
                    "Kunden telefoniert.", 0),
                   ("Es gibt auch eine Neuigkeit: Wir haben einen neuen Mitarbeiter. Er ist sehr nett und "
                    "arbeitet gerne mit uns.", 1),
                   ("Leider gibt es ein Problem mit dem Drucker, weil er nicht mehr funktioniert. Deshalb können "
                    "wir keine Dokumente drucken.", 2),
                   ("Sie müssen sich aber keine Sorgen machen. Wir kümmern uns darum.", None),
                   ("Ich wünsche Ihnen gute Besserung!", 3)],
         gruss="Viele Grüße", name="Ahmad"),
    dict(aufgabe=5, beispiel=2, betreff="Informationen aus der Firma",
         anrede="Lieber Herr Müller,",
         absaetze=[("ich hoffe, dass es Ihnen besser geht.", 3),
                   ("Ich möchte Ihnen kurz erzählen, was bei uns passiert ist.", None),
                   ("Zuerst habe ich Ihre Termine gemacht. Danach habe ich einige wichtige Dokumente vorbereitet. "
                    "Außerdem habe ich mit unseren Kunden gesprochen.", 0),
                   ("Unser Chef hat eine neue Mitarbeiterin eingestellt. Sie beginnt nächste Woche bei uns.", 1),
                   ("Im Moment haben wir viel Arbeit, aber wir schaffen alles zusammen.", 2),
                   ("Können Sie sich gut erholen? Ich hoffe, dass Sie bald wiederkommen können.", 3)],
         gruss="Gute Besserung und viele Grüße!", name="Mohammed"),
    dict(aufgabe=5, beispiel=3, betreff="Wie geht es Ihnen?",
         anrede="Lieber Herr Müller,",
         absaetze=[("wie geht es Ihnen? Ich hoffe, dass Sie nicht mehr so krank sind.", 3),
                   ("Während Ihrer Krankheit habe ich Ihre Aufgaben gemacht. Ich habe Rechnungen kontrolliert und "
                    "neue Bestellungen bearbeitet.", 0),
                   ("Es gibt eine gute Nachricht: Unsere Firma bekommt nächste Woche zwei neue Computer.", 1),
                   ("Leider haben wir auch ein kleines Problem. Ein Kunde hat seine Rechnung noch nicht bezahlt. "
                    "Deshalb habe ich ihm eine E-Mail geschrieben.", 2),
                   ("Wenn Sie wieder gesund sind, können wir darüber sprechen.", None),
                   ("Bitte ruhen Sie sich gut aus. Sie sollen schnell wieder gesund werden!", 3)],
         gruss="Viele Grüße", name="Sara"),
]

# Grammatik (aus der Grammatikübersicht des PDFs) – wird im Text farbig markiert
KONNEKTOREN = ["weil", "dass", "wenn", "obwohl", "damit", "deshalb", "außerdem", "aber", "ob", "danach", "zuerst"]
MODALVERBEN = ["möchte", "möchten", "möchtest", "kann", "kannst", "können", "könnten", "könntest",
               "muss", "müssen", "darf", "dürfen", "soll", "sollen", "will", "wollen"]

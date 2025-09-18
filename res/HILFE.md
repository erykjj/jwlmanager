## Anleitung
######
Öffne eine `.jwlibrary` Sicherungsdatei um die Anmerkungen (die Textfelder, die man in einigen der Publikationen selber ausfüllen kann), Lesezeichen, Favoriten, Markierungen, Notizen und Playlists anzuzeigen (**Kategorie**) die darin enthalten sind. Diese sind in einer Baumansicht organisiert, die nach Titel, Typ, Sprache gruppiert werden kann (**Gruppierung**), und (je nachdem, was du gerade ansiehst) hast du auch die Möglichkeit die Einträge, nach Jahr, Farbe oder Tag (Schlagwort) zu gruppieren.
######
Wenn du eine Sicherungsdatei öffnest, oder mit **drag-and-drop** in die App ziehst, und eine andere Datei bereits geöffnet ist, hast du die Möglichkeit die geöffnete Datei zu ersetzen oder die beiden zusammenzuführen. Wenn du **zusammenführen** wählst, werden *alle* Elemente (Kommentare, Lesezeichen, Favoriten, Markierungen, Notizen und Playlists) aus der zweiten Datei zu der bereits geöffneten hinzugefügt. Dabei werden alle identischen Einträge *überschrieben* (z.B., eine Notiz mit der selben ID). Beachte, dass du beim Zusammenführen *keine Kontrolle darüber hast* welche Elemente überschrieben werden. Ansonsten, *ist das Zusammenführen immer ergänzend*: Wenn du z.B. eine Notiz in der ursprünglichen Datei gelöscht hast und ein anderes importierst, das diese Notiz noch enthält, wird die Notiz wiederhergestellt; oder wenn du sie in der Datei, die du zusammenführen, gelöscht hast, sie aber in der ursprünglichen Datei noch vorhanden ist, bleibt sie erhalten. Daher empfiehlt es sich, die gewünschten Elemente aus der zweiten Dabei zu exportieren und sie in einem zweiten Schritt in die erste Datei zu importieren (benutze dazu die `Export` und `Import` Schaltflächen).
######
Wenn eine Instanz von JWLManager geöffnet ist, wird dort, wo sich die JWLManager.exe befindet eine `JWLManager.lock` Datei erstellt. Wenn die Anwendung aus irgendeinem Grund *unsauber* beendet wird, lösche diese Sperrdatei manuell.
######
Die Eigenschaften des Fensters (Größe, Position, Sprache und verschiedene Auswahlmöglichkeiten) werden in einer `JWLManager.conf` Datei gespeichert, die im Stammverzeichnis der App erstellt wird. Du kannst diese Datei löschen,um die Standardeinstellungen wiederherzustellen.
######
Notizen, die keiner Veröffentlichung zugeordnet sind (direkt im persönlichen Studienbereich erstellt), werden als `* ANDERE *` und mit `* KEINE SPRACHE *`gelistet. Notizen, die kein Tag haben werden als `* KEIN TAG *`.
######
Die **Statusleiste** ganz unten, zeigt den Namen der aktuell geöffneten Datei an. Die Spalte **Anzahl** zeigt die Anzahl aller Elemente eines Zweiges an.
######
Klicken auf die Spaltenüberschrift bewirkt das **sortieren** der Einträge; das erneute Klicken kehrt die Sortierung um.
#####
######
### Ansicht
######
The ***Ansicht*** Menü bietet zusätzliche Möglichkeiten (sie können auch durch eine Tastenkombination erreicht werden):
######
* **Darstellung (`Strg+T`)** - dunklen und hellen Modus umschalten
* **Alles ausklappen (`Strg+E`)** - macht alle Ebenen sichtbar
  * Hinweis: Ein **Doppelklick** klappt alle Unterebenen aus oder ein
* **Alles einklappen (`Strg+C`)** - klappt alle Ebenen ein
* **Alles Auswählen (`Strg+A`)** - Wählt alle Elemente aus
  * Hinweis: Ein **Rechtsklick** auf ein Element klappt alle Unterebenen ein oder aus
* **Alles abwählen (`Strg+Z`)** - entfernt jede Auswahl
* **Titeldarstellung** - ändert die Darstellung des Publikationsnamens
  * **Code** - Publikationscode
  * **Kurz** - Kurzbezeichnung
  * **Voll** - Vollständiger Name
######
Wenn du Änderungen an der Sicherungsdatei speichern willst, wähle **Speichern als...** und speichere unter einem neuen Namen. **Behalte immer deine originale** `.jwlibrary` Datei für den Fall, dass du nach einem Fehler den ursprünglichen Zustand wiederherstellen willst.
#####
######
### Tag
######
Du kannst Tags zu den ausgewählten **Notizen** hinzufügen oder daraus entfernen. `Strg+A` und `Strg+A` funktionieren in diesem Zusammenhang, um alle Einträge auszuwählen bzw. die Auswahl aufzuheben.
#####
######
### Farbe
######
Du kannst die Farbe der ausgewählten **Notizen** und **Markierungen** pauschal ändern (alle bekommen die gleiche Farbe), oder die Farbe einzelner Notizen im **Dateneditor** individuell ändern. Unabhängige Notizen (solche, die keiner Publikation zugeordnet sind) *können nicht* eingefärbt werden; sie sind immer grau.
#####
######
### Aufrufen
######
Zeigt die ausgewählten Notizen und Anmerkungen in einem **Datenbetrachter** an, der Titel und Text mit einem Filter durchsuchen, und das Ergebnis in einer Textdatei speichern kann. Du kann einzelne Einträge löschen oder im **Dateneditor** bearbeiten (Klick auf das Symbol mit Papier und Stift) . Du musst alle Änderungen im Editor und *zusätzlich* im Betrachter speichern, damit sie in die Datenbank übernommen werden. Natürlich musst du auch wie gewohnt die Datei speichern. Du kann mit den Schaltflächen (oder der `ESC` Taste) zurückgehen, ohne die Datenbank zu ändern.
#####
######
### Hinzufügen
######
Bei **Favoriten**, kann man damit eine Bibel hinzufügen, was in der JW Library selbst nicht möglich ist. Und bei **Playlists** kannst du *Bilder* ('bmp', 'gif', 'heic', 'jpg', 'png') zu einer Playlist hinzufügen oder eine neue Playlist anlegen.
#####
###### 
### Löschen
######
Wähle die Kategorie und die Einträge aus, die du aus der Datenbank entfernen möchtest. Beispielsweise kannst du Markierungen aus älteren Zeitschriften, längst vergessene Lesezeichen oder deine gesamten Favoriten löschen.
#####
######
### Export
######
**Notizen** und **Anmerkungen** aus den ausgewählten Veröffentlichungen können als MS Excel-Tabelle oder als Textdatei exportiert werden. Beide kannst du bearbeiten (Elemente hinzufügen, löschen oder ändern) und danach wieder in deine Sicherungsdatei importieren (oder mit jemand anderem teilen).
######
Du kannst sie auch als separate Markdown-Dateien (mit einem Metadaten-Header, der die Eigenschaften jeder einzelnen Datei auflistet) exportieren (aber nicht importieren), die in einem hierarchischen Verzeichnisbaum organisiert sind. Die Dokumentenkennung `document`, (im Fall von Bibelnotizen ist dies der Buch-Kapitel-Vers Code; bei anderen Publikationen ist es die Artikel-Dokument ID) wird in [[doppelte eckige Klammern]] eingeschlossen, um die Querverlinkung der Notizen in einigen Markdown-Viewern zu ermöglichen. Wenn du die die `Farbe` oder die `Sprache` auch auf diese Weise verlinken möchtest, wechsle zur entsprechenden **Gruppierung** bevor du den Export durchführst.
######
Anmerkungen sind sprachunabhängig - sie erscheinen in verschiedenen Sprachversionen *derselben* Veröffentlichung. Die `Link`s zu wol.jw.org in der generierten MS Excel-Datei dienen lediglich der Benutzerfreundlichkeit; sie werden nicht wieder importiert. Dasselbe gilt für die Spalte `Reference` , die die Bibelreferenz im BBCCCVVV-Format enthält.
######
Elemente aus verschiedenen **Playlists** können als eine`.jwlplaylist` Dabei exportiert werden, die eine Playlist (mit dem Namen der Datei) enthält.
######
Der Export von **Lesezeichen** und**Markierungen** ist ebenfalls möglich - nicht, um sie zu bearbeiten, sondern zum Teilen oder Zusammenführen mit einer anderen Sicherung.
#####
######
### Import
######
**Playlists** Wiedergabelisten werden, mithilfe der `Import` Schaltfläche entweder aus `.jwlplaylist` Dateien importiert, (sie enthalten eine einzelne Liste, wobei der Dateiname den Namen der Playlist festlegt) *oder* aus `.jwlibrary` Dateien. (Drag-and-Drop öffnet die Datei, anstatt die darin enthaltenen Wiedergabelisten zu importieren).
######
Du kannst mit der exportierten MS Excel-Datei arbeiten (unter Beibehaltung der vorhandenen Spaltenüberschriften) oder einer speziellen **UTF-8 codieren** Textdatei. Diese speziellen CSV Dateien müssen in der ersten Zeile folgende Überschriften enthalten: `{ANNOTATIONS}`, `{BOOKMARKS}`, `{FAVORITES}` oder `{HIGHLIGHTS}`. Du kannst die Textdateien einfach mit **drag-and-drop** übernehmen, solange sie die korrekte Kopfzeile enthalten. Vom Bearbeiten oder Neuerstellen einer **Lesezeichen** oder **Markierungen** Importdatei wird *abgeraten*. Exportierte Lesezeichen und Markierungen können in eine andere Sicherung integriert werden. Widersprüchliche/doppelte Einträge werden ersetzt, *überlappende Markierungen werden kombiniert, wobei die Farbe der importierten Markierung übernommen wird* (das kann die Anzahl beeinflussen).
######
#### Import von Notizen
######
Notizen können aus einer Excel-Datei oder einer Textdatei `.txt` importiert werden. In beiden Fällen werden doppelte Notizen nicht zweimal hinzugefügt, was sich auf die endgültige Anzahl auswirken kann.
######
Das `{NOTES=}` Attribut in der ersten Zeile *erforderlich* um eine Notizdatei zu identifizieren, und bietet eine bequeme Möglichkeit, alle Notizen zu löschen, deren Titel mit einem Sonderzeichen beginnen (z.B. `{NOTES=»}`). Dadurch wird es vermieden, doppelte Notizen zu erstellen, wenn der Titel geändert wird. Wenn diese Option aktiviert ist, werden alle Notizen mit Titeln, die mit diesem Buchstaben beginnen, gelöscht, *bevor* Notizen aus dieser Datei importiert werden. Andernfalls würden *Notizen mit gleichem Titel und gleichem 'Standort' überschrieben*, während bei Notizen deren der Titel auch nur geringfügig geändert wurde, eine fast identische, doppelte Notiz erstellt würde. (Bei Notizen ohne Überschrift wird der Inhalt verglichen; beim geringsten Unterschied wird eine neue Notiz hinzugefügt).
######
Schlüssel/Wert Paare eines Attributs müssen von `{}` umschlossen werden. Die Schlüssel entsprechen den Spaltenüberschriften der ersten Zeile in der MS Excel-Datei. Sie können in beliebiger Reihenfolge in der Notizkopfzeile stehen. Die Kopfzeile beginnt und endet mit `===`. Diese Kopfzeile ist für jede Notiz **erforderlich**, und muss *wenigstens* ein Attibutpaar enthalten. Die nächste Zeile ist die Überschrift der Notiz. Es folgt ein mehrzeiliger Text, der mit der Kopfzeile der nächsten Notiz oder der dateiabschließenden Zeile `==={END}===`.
######
##### Attribute für alle Notizen 
 - **CREATED**
  - Erstellungsdatum (yyyy-mm-dd oder yyyy-mm-ddTHH:MM:SS) - optional
  - wenn es nicht angegeben ist und die Notiz aktualisiert wird, wird ihr aktueller Wert verwendet; andernfalls wird das Änderungsdatum verwendet, falls verfügbar; falls nicht, werden das Datum und die Uhrzeit des Imports verwendet
  - z.B. `{CREATED=2018-12-10}`
 - **MODIFIED**
  - Änderungsdatum (yyyy-mm-dd oder yyyy-mm-ddTHH:MM:SS) - optional
  - falls nicht angegeben ist, werden das Datum und die Uhrzeit des Imports verwendet
  - z.B. `{MODIFIED=2019-12-10T22:15:00}`
 - **TAGS**
  - Tags (getrennt durch "|") - optional
  - wenn nicht angegeben, wird kein Tag hinzugefügt ; wenn eine Notiz eine andere ersetzt oder erneuert, werden ihr Tags erneuert oder entfernt
  - z.B. `{TAGS=Ministerium|Personal}`
######
##### Attribute, die keiner Publikation zugeordnet sind
 - **COLOR**
  - Farbe der Notiz (0 = Grau; 1 = Gelb; 2 = Grün; 3 = Blau; 4 = Rot; 5 = Orange; 6 = lila) - optional (wenn nicht angegeben, wird 0 = Grau verwendet)
  - z.B. `{COLOR=2}`
 - **RANGE**
  - ein oder mehrere aufeinanderfolgende hervorgehobene Bereiche, die durch Semikolon getrennt werden sollen - optional
  - Format: Blockidentifizierungnummer (Absatz/Vers) gefolgt von 0-basierter Anzahl der Tokens ("Wörter") die hervorgehoben sein sollen
  - wenn nicht angegeben, wird die Notiz an den Anfang des Verses/Absatzes angehängt (keine Markierung)
  - wenn keine Farbe (COLOR) angegeben ist (oder `{COLOR=0}`), wird der Bereich ignoriert
  - z.B. `{RANGE=1:4-11}`, `{RANGE=11:20-35;12:0-12}`
 - **LANG**
  - Sprache (für Notizen in Bibeln und Publikationen) - optional (ist 0 = Englisch wenn nicht angegeben)
  - z.B. `{LANG=1}`
 - **PUB**
  - Publikation - **erforderlich** für Notizen in der Publikation oder Bibel
  - wenn nicht angegeben, wird die Notiz als „unabhängig“ betrachtet und die unten aufgeführten Attribute werden ignoriert
  - z.B. `{PUB=nwtsty}`
 - **HEADING**
  - Gibt die Überschrift des Kapitels oder Absatzes an für den die Notiz erstellt wurde (oder Bibelbuch und Kapitel) - optional
  - wird hauptsächlich für den Komfort angegeben; kann frei bleiben
  - z.b. `{HEADING=Genesis 1}`
######
##### Attribute für Notizen in der Bibel
 - **BK**
  - Nummer des Bibelbuches (1-66) - **erforderlich**
  - z.B. `{BK=1}`
 - **CH**
  - Kapitelnummer - **erforderlich**
  - für Bücher mit nur einem Kapitel, 1 angeben
  - z.B. `{CH=45}`
 - **VS**
  - Versnummer - **erforderlich** (Sonderfälle siehe unten)
  - z.B. `{VS=6}`
  - **Sonderfälle**:
   - `{VS=0}` - für die Psalmenüberschriften
   - Attribut weggelassen – für Anmerkung am Anfang des Kapitels
   - Attribut weggelassen *und* `{BLOCK=1}` - für eine Anmerkung zum Titel des Bibelbuchs (vor Vers 1)
######
##### Attribute für Notizen in Publikationen:
 - **ISSUE**
  - Ausgabe (yyyymm00 oder yyyymm01 oder yyyymm15 ) - **erforderlich** regelmäßige Veröffentlichungen
  - z.B. `{ISSUE=20110400}`
 - **DOC**
  - document - **erforderlich**
  - z.B. `{DOC=202011126}`
 - **BLOCK**
  - "Absatz"
  - z.B. `{BLOCK=6}`
  - **special cases**:
   - attribute omitted - für Notizen am Anfang des Dokuments
######
##### Zu Beachten:
 - Unabhängige Notizen werden nach Titel und Inhalt verglichen. Wenn zwei Notizen importiert werden, die in diesen beiden Feldern identisch sind, wird nur eine importiert. Dies hilft, Duplikate zu vermeiden.
 - Sofern die entsprechenden farbigen Markierungen nicht ebenfalls importiert werden, werden die importierten Notizen am *Anfang* Absatzes oder Verses platziert, dem sie zugeordnet sind.
  - `{COLOR=}` mit Werten von 1 bis 6 *und* `{RANGE=}` → farbige Haftnotiz mit Hervorhebung
  - `{COLOR=}` mit Werten von 1 bis 6 und *kein* `{RANGE=}` → farbiger Haftnotiz (am Anfang des Absatzes/Verses ohne Hervorhebung)
  - `{COLOR=0}` (mit/ohne `{RANGE=}`) → graue Haftnotiz (am Anfang des Absatzes/Verses und keine Hervorhebung)
######
######
### Dienstprogramme
######
### Bereinigen
######
Beim Kopieren und Einfügen in Notizen und Anmerkungen können unsichtbare Zeichen eingefügt werden: nicht umbrechende Leerzeichen, schmale oder breite Leerzeichen und Verbindungszeichen. Alle diese Zeichen werden verwendet, um die Absatzformatierung in Rich-Text-Dokumenten umzusetzen. Diese Funktion entfernt diese Zeichen in *allen* Notizen und Anmerkungen, die sie enthalten. Außerdem werden alle Wagenrücklaufzeichen (`\r`) durch Zeilenumbruchzeichen (`\n`) ersetzt. Dies ist ein **Einwegverfahren**! Stelle sicher, dass du eine Sicherungskopie aufbewahrst, bis du ganz sicher bist, dass alles in Ordnung ist.
######
### Verschleiern
######
Wenn du anderen deine Sicherungsdatei *weitergeben* möchtest (für Diagnosezwecke, usw.) aber diese persönliche oder vertrauliche Informationen enthält, kannst du mit dieser Option die Textfelder in deiner Sicherung unkenntlich machen. Die Textlänge bleibt unverändert, alle Zahlen und Satzzeichen bleiben erhalten, alphabetische Zeichen werden jedoch durch bedeutungslose Ausdrücke wie „verdeckt“, „bla“, „bla“, „Kauderwelsch“ oder „børk“ überschrieben. Zur Bestätigung kannst du dir die Notizen im Betrachter ansehen. Nur Stichwörter werden nicht verschleiert. Das ist ein **gefährliches, destruktives Einwegverfahren!** Stelle sicher, dass du dein 'offizielles' Backup nicht veränderst! 
######
### Sortieren
######
Wenn im Bereich „Persönliches Studium“ (Notizen und Tags) der JW Library-App ein bestimmtes Tag (Schlagwort) ausgewählt wird, können die angezeigten Notizen manuell sortiert werden. Diese Funktion stellt alle Notizen in ihre „natürliche“ Reihenfolge zurück (basierend auf der `Notiz-ID`).

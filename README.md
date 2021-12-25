**NOTE**: This project is at mid-development stage. Some functions are not implemented as yet. All have to be fully tested. If you want a working implementation, have a look at my previous console-based Ruby script: <a href="https://gitlab.com/erykj/jwl-admin" target="_blank">jwl-admin</a>.

____

**DISCLAIMER**: KEEP A BACKUP of your original *.jwlibrary* file in case you need to restore after messing up ;-)

____
**PURPOSE**: This application allows for viewing and performing various operations on a *.jwlibrary* backup file (created from within the JW Library app[^1]: Personal Study > Backup and Restore > Create a backup). This resulting modified *.jwlibrary* file can then be restored within the app.

In addition to the main functions of exporting, importing, and deleting, the application can also clean up any residual/unused records from the database and re-index the various tables within the database.
____
**USAGE**: This is a Python 3 script implementing the QT framework.

Execute to run:

```
$ python3 JWLManager.py
```
Or, make it executable first and run directly:
```
$ chmod u+x ./JWLManager.py
$ ./JWLManager.py
```
A single-file Windows executable can be produced using `pyinstaller`

____
**IMPORTING**: NOT IMPLEMENTED YET

You need to provide a text file with the notes to import. You can use the file produced by exporting and modify the note text. Or you can create your own. The accepted format for the import file is like this:

```
{TITLE=»}
==={CAT=BIBLE}{LANG=1}{ED=Rbi8}{BK=1}{CH=1}{VER=1}{COLOR=1}{TAGS=}===
» Title
Multi-line...
...note
==={CAT=PUBLICATION}{LANG=1}{PUB=rsg17}{ISSUE=0}{DOC=1204075}{BLOCK=517}{COLOR=0}{TAGS=research}===
» Title
Multi-line...
...
...note
==={CAT=INDEPENDENT}{TAGS=personal}===
» Title
Multi-line...
...note
==={END}===
```
The *{TITLE=}* attribute in the first line provides a convenient way to delete any notes that have titles starting with this character (in this case "»"). This is to avoid creating duplicate notes if the title has changed. When set, all notes with titles starting with this character will be deleted before notes from the import file are imported. Otherwise, notes with same title at same location will be over-written, but those where the title was modified even slightly will create an almost duplicate note.

Each note definition starts with an attribute line. *{CAT=}* define the category. The *{LANG=}* attribute defines the language of the note (0 = English; 1 = Spanish; 2 = German; 3 = French; 4 = Italian; 5 = Brazilian Portuguese; 6 = Dutch; 7 = Japanese, etc.),  and *{ED=}* defines the Bible edition to associate the note with ("nwtsty" = Study Bible; "Rbi8" = Reference Bible) - *{PUB=}* for publications.

**Note**: the notes and "stickies" appear in all Bibles; the only difference is the Bible that is referenced at the bottom of the note in the "Personal Study" section. For some strange reason, the stickies *do not* show up in the Bible that is referenced, though the notes are there in the reference pane, and the stickies do show in all the *other* Bibles. This may be a bug (feature?) in the app itself. For now, I reference my notes with the Reference Bible (*Rbi8*) so that I can see the stickies in the Study Bible (*nwtsty*).

For Bible notes, *{BK=}{CH=}{VER=}* are all numeric and refer to the number of the book (1-66), the chapter and the verse, respectively. For books with just one chapter, use "1" for the chapter number. *{ISSUE=}{DOC=}{BLOCK=}* are the attributes associated with locations within a publication - they are, obviously, a bit more complicated to create, so it's best to simply modify the export file and re-import.

The *{COLOR=}* setting (0 = grey; 1 = yellow; 2 = green; 3 = blue; 4 = purple; 5 = red; 6 = orange) indicates the color of the note. The words themselves will not be highlighted; instead, there will be a colored sticky in the left margin next to the verse with the note.

*{TAGS=}* is used to add one or more tags to each note. If empty, no tag is added; if a note is replacing/updating another, its tags will be updated or removed.

Each note has to start with such a header. The very next line after the header is the note title. Titles will be automatically abbreviated with inner words being replaced with "\[...]" in order to meet the length limit and display properly. A multi-line body follows, terminated by the header of the next note or the file-terminating header *\=\=={END}===*.

Here is an example blue note for Jude 21 (in  Spanish):

```
==={CAT=BIBLE}{LANG=1}{ED=Rbi8}{BK=65}{CH=1}{VER=21}{COLOR=3}{TAGS=}===
» para mantenerse en el amor de Dios
1. _edificándonos sobre nuestra santísima fe_ mediante el **estudio** diligente de la Palabra de Dios y la participación en la obra de predicar
2. _**orando** con espíritu santo_, o en armonía con su influencia
3. ejerciendo **fe** en el sacrificio redentor de Jesucristo, que hace posible la _vida eterna_
```
On a side-note, I format my notes with markdown syntax (as above) for, even though JW Library doesn't allow rich-text formatting in the notes, that *may* change in the future and it should then be realtively easy to convert.

____
**FEEDBACK**: Feel free to [get in touch](https://gitlab.com/erykj/jwlmanager/-/issues) and post any issues and suggestions.

____
[^1]: <a href="https://www.jw.org/en/online-help/jw-library/" target="_blank">JW Library</a> is a registered trademark of *Watch Tower Bible and Tract Society of Pennsylvania*.


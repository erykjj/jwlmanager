## Operation
######
Open a `.jwlibrary` backup archive to see the Annotations (the editable text fields in some of the publications), Bookmarks, Favorites, Highlights, Notes and Playlists (**Category**) that are stored within it. These will be organized in a tree view, which can be grouped (**Grouping**) by either title, type, language, and (depending on what you are currently viewing) you may also have the option to group by year, color or tag.
######
If you **drag-and-drop** an archive into the app when another archive is already opened, you will have the option to "Open" it (replacing the current one) or "Merge". If you choose to **merge**, *all* the records (Annotations, Bookmarks, Highlights, Notes and Playlists) from this second archive will be added to the already opened one, *over-writing* any that may be the same (eg., a note at the same location and with the same title). Keep in mind that by merging you don't have any control over which records to import; thus, it is preferable to export the items you want from the second archive and import them into the first in two steps (using the `Export` and `Import` buttons).
######
The state of the application (size, position, language, and various selection choices) is preserved in a `JWLManager.conf` file created in the same directory as the app. You can delete that file to start with default settings.
######
Notes that are not associated with any publication (created directly in the Personal Study space), are listed as `* OTHER *` and with `* NO LANGUAGE *`. Notes that aren't tagged will be listed as `* NO TAG *`.
######
The **status bar** shows the name of the currently opened archive. The **Count** column shows the number of items for each branch of the tree.
######
Clicking on the column headers allows for **sorting** the tree; clicking the same header again reverses the sort.
#####
######
### View
######
The ***View*** menu has some additional options (also accessible directly via the key combination shortcut):
######
* **Theme (Ctrl+T)** - toggle between light and dark mode
* **Expand All (Ctrl+E)** - expand the tree to make all levels visible
  * Note: **double-clicking** on an entry will expand (or collapse) all its sub-levels
* **Collapse All (Ctrl+C)** - collapse all levels
* **Select All (Ctrl+A)** - a quick way to select all entries
  * Note: **right-clicking** on an entry will check/uncheck it and all its sub-levels
* **Unselect All (Ctrl+Z)** - unselect everything
* **Title View** - change how publication titles are displayed
  * **Code** - publication code
  * **Short** - abbreviated title
  * **Full** - complete title
######
If you modify an archive and intend to use the results to re-import into JW Library, make sure to **save** it (with a new name). **KEEP A BACKUP** of your original `.jwlibrary` archive in case you need to restore.
#####
######
### View (button)
######
Shows selected Notes and Annotations in a **Data Viewer** window, with a filter that searches within the title and body, and an option to save the results to a text file. You can delete and/or edit individual items. You have to confirm all edits within the **Data Editor** and *again* in the Data Viewer before they are written to the database (of course, you still have to save the archive as usual). You can go back via the buttons (or `Escape` key) without affecting the database.
#####
######
### Add
######
In the case of **Favorites**, used for adding a Bible translation to your favorites, since there is no direct way of doing that in the JW Library app itself. And with **Playlists** you can add *images* ('bmp', 'gif', 'heic', 'jpg', 'png') to an existing playlist or create a new list.
#####
######
### Delete
######
Select the Category and the item(s) you wish to eliminate from the database. For example, you may want to remove highlighting you made in some older magazines, or bookmarks you never knew you had, or clear your favorites completely, etc.
#####
######
### Export
######
**Notes** and **Annotations** from selected publications can be exported to an MS Excel spreadsheet or a custom text file - either one of which you can edit (add, delete or modify items) and later import into your archive (or share with someone else).
######
They can also be exported (but not imported) as separate markdown files (with a meta-data header listing the properties of each one) organized in a hierarchical directory tree. The `document` property (in the case of Bible notes this is the book-chapter-verse code; for other publications, it's the article document id) will be enclosed in [[double brackets]] to allow cross-linking the notes in some markdown viewers. If you want to have either the `color` or the `language` also cross-linked this way, swich to the corresponding **Grouping** before performing the export.
######
Annotations are language-agnostic - they show up in different language versions of the *same* publication. The `Link`s to wol.jw.org in the generated MS Excel file are for convenience only; they are not re-imported. The same goes for the `Reference` column, which is the Bible reference in BBCCCVVV format.
######
Items from differente **Playlists** can be exported to a `.jwlplaylist` archive containing one playlist (with the name of the archive) which can be imported as a playlist.
######
Exporting of **Bookmarks** and **Highlights** is also possible - not so much with a view of direct editing, but for sharing/merging into another archive.
#####
######
### Import
######
**Playlists** are imported from `.jwlplaylist` archives (containing a single list; the name of the archive defines the playlist name) *and* `.jwlibrary` archives (using the `Import` button only; drag-and-drop will open the archive instead of importing all the playlists it contains).
######
You can work with the exported MS Excel file (reusing the column headings) or use a special **UTF-8 encoded** text file with the **Notes**, **Highlights** or **Annotations** to import. You can use the file produced by exporting, or you can create your own. The Higlights file is a CSV text file with a `{HIGHLIGHTS}` header. The Annotations file must start with `{ANNOTATIONS}` on the first line. You can simply **drag-and-drop the import text files** into the app as long as they have the correct header line.
######
Editing or manually creating a **Bookmarks** or **Highlights** import file is *not* recommended. Exported Bookmarks and Highlights can be merged into another archive. Any conflicting/duplicate entries will be replaced and *overlapping highlights will be combined and the color changed to the one being imported* (this can affect the final number).
######
#### Importing Notes
######
The `{NOTES=}` attribute in the first line is *required* to identify a Notes export/import file, and provides a convenient way to delete any notes that have titles starting with a special character (for example, `{NOTES=»}`). This is to avoid creating duplicate notes if the title has changed. When set, all notes with titles starting with this character will be deleted *before* notes from the file are imported. Otherwise, *notes with the same title and at the same 'location' will be over-written*, but those where the title was modified even slightly will create an almost duplicate note. (Notes with an empty title will be compared by content; if there is even a tiny difference, a new note will be added.)
######
Attribute key and value pairs must be placed within `{}`. The keys correspond to the first-row column-headings in the MS Excel file. They can be in any order within the note-header. The header line starts and ends with `===`. This header is **required** for each note, and must contain *at least one* attribute pair. The very next line after the header is the note title. A multi-line body follows, terminated by the header of the next note or the file-terminating header or `==={END}===`.
######
##### Attributes for all notes (including "independent" ones)
  - **CREATED**
    - date note was created (yyyy-mm-dd or yyyy-mm-ddTHH:MM:SS) - optional
    - if not provided and note is being updated, its current value will be used; otherwise, modified date if available; if not, the date and time of import is used
    - eg. `{CREATED=2018-12-10}`
  - **MODIFIED**
    - date note was modified (yyyy-mm-dd or yyyy-mm-ddTHH:MM:SS) - optional
    - if not provided, the date and time of import is used
    - eg. `{MODIFIED=2019-12-10T22:15:00}`
  - **TAGS**
    - tags (separated by "|") - optional
    - if not provided, no tag is added; if a note is replacing/updating another, its tags will be updated or removed
    - eg. `{TAGS=Ministerio|Personal}`
######
##### Attributes for notes attached to any publication
  - **COLOR**
    - note color (0 = grey; 1 = yellow; 2 = green; 3 = blue; 4 = red; 5 = orange; 6 = purple) - optional (will be 0 = grey if not provided)
    - eg. `{COLOR=2}`
  - **RANGE**
    - 0-based index of the tokens ("words") to highlight - optional
    - if not provided, note will be attached to start of verse/paragraph (no highlighting)
    - if no COLOR is provided (or `{COLOR=0}`), token range will be ingnored
    - eg. `{RANGE=4-11}`
  - **LANG**
    - language (for Bible and publications notes) - optional (will be 0 = English if not provided)
    - eg. `{LANG=1}`
  - **PUB**
    - publication symbol - **required** for notes attached to any publication or Bible
    - if not provided, note will be considered "independent" and attributes listed below will be ignored
    - eg. `{PUB=nwtsty}`
  - **HEADING**
    - specifies the heading/chapter title where note is placed (or Bible book and chapter) - optional
    - this is included mostly for convenience; it may be blank, and is regenerated correctly when the JW Library app displays the Notes
    - eg. `{HEADING=Genesis 1}`
######
##### Attributes for Bible notes
  - **BK**
    - Bible book number (1-66) - **required**
    - eg. `{BK=1}`
  - **CH**
    - chapter number - **required**
    - for books with just one chapter, use 1
    - eg. `{CH=45}`
  - **VS**
    - verse number - **required** (see exceptions below)
    - eg. `{VS=6}`
    - **special cases**:
      - `{VS=0}` - for Psalm headings
      - attribute omitted - for note at top of chapter
      - attribute omitted *and* `{BLOCK=1}` - for note attached to Bible book title (before verse 1)
######
##### Attributes for publication notes:
  - **ISSUE**
    - issue (yyyymm00 or yyyymm01 or yyyymm15 ) - **required** for periodical publications
    - eg. `{ISSUE=20110400}`
  - **DOC**
    - document - **required**
    - eg. `{DOC=202011126}`
  - **BLOCK**
    - "paragraph" block
    - eg. `{BLOCK=6}`
    - **special cases**:
      - attribute omitted - for note at top of document
######
##### Observations:
  - Independent notes are compared by title and content. If two notes are imported that are equal in those two fields, only one will be imported. This helps eliminating duplicates.
  - Unless the corresponding colored highlights are also imported, the imported notes are placed at the *beginning* of the paragraph or verse that they are attached to.
    - `{COLOR=}` with value of 1 to 6 *and* `{RANGE=}` → colored stickie with highlight
    - `{COLOR=}` with value of 1 to 6 and *NO* `{RANGE=}` → colored stickie (at start of paragraph/verse and no highlight)
    - `{COLOR=0}` (with/without `{RANGE=}`) → grey stickie (at start of paragraph/verse and no highlight)
######
######
### UTILITIES
######
### Mask
######
If you need to *share* your complete archive (for diagnostic purposes, etc.) but have some personal or confidential information, you can use this option to obfuscate the text fields in your archive. The length of the text remains the same, leaving all numbers and punctuation in place, but alphabetic characters are over-written with meaningless expressions such as 'obscured', 'yada', 'bla', 'gibberish' or 'børk'. To confirm, view the notes in the Data Viewer. Only tags are not obscured. This is a **dangerous, destructive, one-way procedure**! Make sure you keep your 'official' backup!
#####
### Reindex
######
This function cleans up and re-orders the records in the archive database. It is not strictly required, though it *may* streamline and speed it up slightly. The process itself may take up to a minute, depending on the number of records the database contains. It does not need to be run more than once in a while.
#####
### Sort
######
When a specific tag is selected in the JW Library app's "Personal Study" (Notes and Tags) section, the displayed notes can be arranged manually. This function restores all notes to their "natural" order (based on `NoteId`).

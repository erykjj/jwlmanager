# JWLManager

## Purpose

This application allows for viewing and performing various operations on a *.jwlibrary* backup file (created from within the **JW Library** app[^1]: Personal Study > Backup and Restore > Create a backup). This resulting modified *.jwlibrary* file can then be restored within the app.

In addition to the main functions of exporting, importing, and deleting, the application can also clean up any residual/unused records from the database and re-index the various tables within the database.
____
## Usage

This is a Python3 script implementing the QT framework.

If you have Python3 installed, execute to run:

```
$ python3 JWLManager.py
```

Or, make it executable first and run directly:

```
$ chmod u+x ./JWLManager.py
$ ./JWLManager.py
```

You may have to `pip install` some of the required libraries (*PySide2*, etc.).

You can find a single-file <u>Windows executable</u> in the [Releases](https://gitlab.com/erykj/jwlmanager/-/releases) section.
____
## Operation

### <u>Viewing</u>

Open a *.jwlibrary* backup archive to see the Annotations (the editable progress fields in some of the newer publications), Bookmarks, Favorites, Highlights, and Notes (**Category**) that are stored within it. These will be organized in a tree view, which you can group (**Grouping**) by either the publication, the language, and (depending on what you are currently viewing) you may also have the option to group by year, color or tag.

The status bar shows the name of the currently opened archive. The **Count** column shows the number of items for each branch of the tree.

The ***View*** menu has some additional options (also accessible directly via the key combination shortcut):

* **Expand All (Ctrl+E)** - expands the tree to make all levels visible
  * Note: double-clicking on an entry will expand (or collapse) all *its* sub-levels
* **Collapse All (Ctrl+C)** - collapse all levels
* **Select All (Ctrl+A)** - a quick way to select all entries
* **Unselect All (Ctrl+Z)** - unselect everything
* **Grouped (Ctrl+G)** - when grouping by publication, this further classifies the publications into categories (books, brochures, periodicals, etc.)
* **Title View** - change how publication titles are displayed
  * **Code** - publication code
  * **Short Title** - abbreviated title
  * **Full Title** - complete title

If you modify an archive and intend to use the results to re-import into JW Library, make sure to save it (with a new name). KEEP A BACKUP of your original *.jwlibrary* file in case you need to restore after messing up ;-)

### <u>Deleting</u>

Select the Category and the item(s) you wish to eliminate from the database. For example, you may want to remove highlighting you made in some older magazines, or bookmarks you never knew you had, or clear your favorites completely, etc.

### <u>Exporting</u>

This is most useful for the Notes, as it exports notes from selected publications to a text file which you can edit directly (add, remove, modify) and later import into your archive (or share with someone else).

Exporting of Annotations and Highlights is also possible - not so much with a view of direct editing, but sharing/merging into another archive.

### <u>Importing</u>

**Not implemented yet**

### <u>Re-indexing</u>

This function cleans up and re-orders the records in database of the archive. It is not strictly required, though it *may* speed it up slightly. The process itself may take a few seconds, depending on the number of records the database contains. It does not need to be run more than once in a while.
____
## Feedback

Feel free to [get in touch](https://gitlab.com/erykj/jwlmanager/-/issues) and post any issues and suggestions.
____
[^1]: [JW Library](https://www.jw.org/en/online-help/jw-library/) is a registered trademark of *Watch Tower Bible and Tract Society of Pennsylvania*.

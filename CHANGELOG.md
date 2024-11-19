# JWLManager Changelog

## [Unreleased]

### Added

### Changed

- Imported .jwlplaylist filename deternmines the playlist name (instead of the name it was exported with)
- Proper suffixes on saved/exported files are added if missing (where applicable)

### Fixed

- Fixed edge case of language change not triggering regroup

### Removed

____
## [6.1.0] - 2024-11-14
### Changed

- `color` and `language` properties in meta-data of Notes exported to markdown will only be enclosed in [[double brackets]] if the corresponding Grouping is selected before the export

### Fixed

- Fixed link language in exported md files (thank you, @riggles)

## [6.0.0] - 2024-11-10
### Added

- **Light/dark mode toggle**

### Changed

- **Markdown export** (thank you @SchneiderSam for suggestions and testing)
  - Only notes with newer modification time will be replaced
- Many cosmetic/UI fixes/improvements
  - Fixed archive name color in dark mode
- Translation corrections

### Fixed

- Improved parent/child relationships between main app and dialogs

## [5.1.2] - 2024-10-24
### Changed

- Ensure UTF-8 encoding on all import text files

## [5.1.1] - 2024-10-23
### Fixed

- Fixed crash on import

## [5.1.0] - 2024-10-22

### Added

- Added **hierarchical markdown export** from main interface for Notes and Annotations
  - Organized by publication/issue/document or publication/book/chapter
  - Note names start with verse or paragraph number (if available) and are based on Note title or Annotation label
    - Exports over-writes previous entries with same directory/filename
- Added **check/uncheck on right-clicking on an entry** (not just left-clicking on checkbox)
- Added status-bar message when exporting

### Changed

- Fixed tooltip colors in Data Viewer
- Made filter field in Data Viewer wider
- Data Viewer save as TXT reverted to single-file export of visible items
- Updated translations
  - Some corrections in German
- Increased status message timeout

## [5.0.0] - 2024-10-18
### Added

- Added option to **save Notes in Data Viewer as individual markdown files**
- Added **Bookmark export and import**
- Added Bookmarks table to reindexing process
- Save and restore Help window geometry

### Changed

- Added item type on status bar on import
- Updated translations
- Updated publications catalog
- Disabled save button in Data Viewer until all notes are loaded
- Added notice in Viewer title while loading

### Fixed

- Fixed error on exporting from new (unsaved) archive
- Close Help window on application exit
- Fixed crash on NULL Note title

## [4.5.3] - 2024-09-18
### Changed

- Updated resources

### Fixed

- Fixed incorrect name of source archive used in export file header (minor)

## [4.5.2] - 2024-06-01
### Fixed
- Fixed importing Annotations with Null value (thank you @jonharrell)

## [4.5.1] - 2024-06-01
### Changed
- Build macOS app for MacOS >=12 instead of 'latest' (MacOS 14) (thank you @stecchio66)
- Corrected Polish translation
- Updated publications catalog

### Fixed
- Fixed crash when adding an image that is already a thumbnail in an existing playlist
- Fixed crash on Playlist export where there is no thumbnail (thank you @xKamil01)
- Added `* OTHER *` label for unrecognized Favorites

## [4.5.0] - 2024-05-26
### Added

- **Playlist management**
  - Exporting Playlist items to `.jwlplaylist` file
  - Importing Playlist items from `.jwlplaylist` or `.jwlibrary` files
  - Adding image files (`bmp`, `gif`, `heic`, `jpg`, `png`) through file selection dialog or drag-and-drop

### Changed

- Updated `requirements.txt`
  - Using latest PySide 6.7
  - Additional modules for image/file handling
- Various small changes
- Updated publications catalog
- Updated translations for new strings

### Fixed

- Updating LastModified date in database (minor)

## [4.4.1] - 2024-02-13
### Changed

- Adjust code for future upstream library changes (pandas)

### Fixed

- Fix for a 'nan' tag being added to untagged Notes on import

## [4.4.0] - 2024-02-10
### Changed

- Importing document-level notes (not attached to a paragraph, {BLOCK=} attribute not provided)
- Updated Document Viewer to include link for document-level notes

### Fixed

- Exporting notes attached to top of document (no paragraph block)
  - thank you @jonharrell for helping catch and troubleshoot!

## [4.3.3] - 2024-01-24
### Fixed

- Fixed crash when trying to view empty notes

## [4.3.2] - 2024-01-14
### Changed

- Updated translations
- Adjusted window sizing for greater flexibility

## [4.3.1] - 2024-01-13
### Added

- Added German translation
- Added Russian and Ukrainian translations (thank you @korotkiyYurii)

### Changed

- Updated publications catalog

## [4.3.0] - 2023-12-18

### Added

- Added **filter box** in Data Viewer
  - TXT toolbar button only saves visible (filtered) items
- New languages
  - **German** - needs revision ;-)
  - **Polish**

### Changed

- Updated publications catalog
- Updated translations

## [4.2.1] - 2023-12-06
### Added

- Added fix for buggy database tables

## [4.2.0] - 2023-12-05
### Added

- **Playlists** category to list (and delete) playlists and/or their content

### Changed

- More thourough database reindexing and cleaning up of the archives
- Updated resource db
- Updated translations
- Slight UI adjustments

### Fixed

- Various minor fixes

## [4.1.0] - 2023-11-30

### Added

- Utility to restore all notes to their "natural" sort order (after they have been moved around in the Tag view of "Personal Study" section of the JW Library app)

### Fixed

- Added some missing menu icons

## [4.0.2] - 2023-11-20
### Changed

- Updated some icons

### Fixed

- Fixed importing from custom text backup file with no Title character set

## [4.0.1] - 2023-11-16
### Fixed

- Fixed occasional crash caused by attempting to modify an already-closed Viewer window in rare circumstances

## [4.0.0] - 2023-11-15
### Added

- **Data Editor** (accessed via Data Viewer)
  - Edit Note titles and/or content
  - Edit Annotation content
- Added another level of detail (Bible chapter)
  - A bit slower with many notes/highlights, but with real-time loading
  - Because of this, the 'default' (start-up) grouping is by "Type"
- Added **update check** in About box
- `JWLManager.conf` file in app directory to **save session info** (delete the file to start with defaults)
  - Main interface and Data Viewer window position and size
  - Currently-opened archive
  - Current language
  - Current category
  - Current title format
  - Column width and sorting direction

### Changed

- Improved **Data Viewer** functionality
  - Delete individual Notes and Annotations
- Updated resource DB with new publication (*lmd*)
- Code restructuring/reorganization and improvements for (slightly) better performance
  - Moved some Qt-related UI code to `ui_extras.py` module
- Updated app translations

### Fixed

- Fixed double tree build on language change
- Fixed total from previous archive showing on new archive creation

## [3.0.3] - 2023-10-22
### Changed

- Updated resource DB with new publication (scl)
- Streamlined and cleaned up code
- Adjusted regex/processing of custom import files with missig title and/or note content

### Fixed

- Fixed language format for Favorite selection

## [3.0.2] - 2023-10-20
### Changed

- Adjusted crash box to point to Github issues (instead of previous Gitlab repo)
- Small adjustments to Qt-related code

### Fixed

- Fixes for export/import in various special cases:
  - Chapter-level Bible notes (no verse)
  - Notes in Bible book titles
  - Notes and annotations with no content
- Fixed language selection in Add Favorite

## [3.0.1] - 2023-10-09
### Added

- If HEADING is provided for Bible references in the import file, it will over-write/update the Location.Title field in the archive
  - If you do use that "feature", keep in mind the observation below...

### Changed

- Removed verse numbers from HEADING on export/import
  - That field (Location.Title) applies to the whole chapter and will display incorrectly if there is more than one note at that location

## [3.0.0] - 2023-10-07

**Major release**

### Added

- Added View button for Notes and Annotations (replacing the right-click funtionality)
- Added functionality to save Data Viewer content to a text file ('TXT' in toolbar of Data Viewer)
- Allow opening `.jwlplaylist` files (limited benefit)
- Location.Title is now included in Note export if defined (`{HEADING=}` attribute), and will be restored on import
  - This is *not* the note title, but the page heading/subheading where the note is located (or Bible book name and chapter)

### Changed

- **Export and import Notes and Annotations to/from Excel (default) or custom text file (with attribute headers)**
  - Use file-type dropdown to choose between `*.txt` and `*.xlsx`
- Attribute keys/labels simplified (see [HELP](res/HELP.md) file)
  - Tags separated with "|" (instead of ",")
  - **Not compatible with older export files**

- Data Viewer improvements
  - Colored notes, links to source (via wol.jw.org)
  - Close Data Viewer window on archive change (thank you, @vegsetup for the suggestion)

- Updated translations
- Updated Help file

- Packages built on Python 11
- **Removed support for older JW Library archives**
  - Only v14 and up - please update your app

### Fixed

- Fixed minor bugs

### Removed

- Removed right-clicking for Data Viewer
- Removed alert about UTF-8 on import (not applicable to MS Excel files)
- Removed confirmation on export (still required if over-writing an existing file)
- Removed unmaintained Qt5 branch from repo

## [2.4.2] - 2023-08-25
### Fixed

- Fixed crash when exporting notes with empty title and/or content fields (thank to @sircharlo)

## [2.4.1] - 2023-08-20
### Changed

- Improved Data Viewer
  - Can view up to 1500 Notes
  - Now showing source of Note, as well as any tags, and sorted more practically (instead of by NoteId)

## [2.4.0] - 2023-08-19
### Added

- Added platform info in debug/exception dialog

### Changed

- Removed language from Annotation export/import
  - Annotations are now cross-language: appearing in all languages of the same publication
  - **NOTE**: Importing Annotation files created with previous versions of JWLManager will fail
  - Also removed the sort by language option from Annotations - all are listed as "* NO LANGUAGE *"
- Progressive code clean-up/refinement

### Fixed

- Added code to handle older .jwlibrary archives (Note export)
- Fixed import errors on some Annotations
- Imported Notes attached to correct highlight if RANGE attribute provided
  - Careful not to overlap ranges
- Corrected UTC (time formats) and device name in modified manifest files

## [2.3.2] - 2023-07-24
### Fixed

- Fixed one playlist table not being reindexed along with the rest causing a crash

## [2.3.1] - 2023-07-20
### Changed

- Adjusted some date string formats

### Fixed

- Added check for empty/non-existent KeySymbol field causing crashes

## [2.3.0] - 2023-07-17
### Changed

- A long-time bug was fixed in JW Library v14, which eliminated the need for fancy work-around solutions for colored note stickies
  - Adjusted HELP.md accordingly
- Updated manifest file to be inline with new JW Library v14
- Updated blank database to include new playlist tables
- Notes export includes CREATED date and MODIFIED date, instead of the previous DATE (modified date)
- Notes import can handle older DATE= attribute, as well as new CREATED= and MODIFIED= attributes

### Fixed

- Fixed crash generated by reindexing a table that was removed from newer databases

## [2.2.4] - 2023-06-28
### Fixed

- Fixed incorrect TextTag selection affecting import/deletion of Annotations

## [2.2.3] - 2023-04-09
### Added

- Added Portuguese translation

## [2.2.2] - 2023-04-07
### Fixed

- Fixed start-up issue on recently released Qt6.5

## [2.2.1] - 2023-03-08
### Fixed

- Fixed duplicate Bible note export

## [2.2.0] - 2023-03-07
### Added

- Big adjustments in the **import/export mechanism** - please report any [issues](https://github.com/erykjj/jwlmanager/issues)
  - Exporting and importing now handles the associated highlight range *along* with the notes
    - I wanted to keep highlights and notes as separate entities, but unless both are imported, the note markers are not colored nor placed in the right place in the parragraph
  - So now there is also an **{RANGE=}** attribute in the note header (see [HELP](./res/HELP.md) for more info

## [2.1.3] - 2023-03-04
### Changed

- Updated translations

### Fixed

- Fixed more "unknown"-language issues
- Fixed publication issue date being processed incorrectly
- Fixed selection count not resetting on category change
- Fixed importing notes with no title

## [2.1.2] - 2023-03-01
### Changed

- Small error correction in HELP

### Fixed

- Fixed an issue with unrecognized languages

## [2.1.1] - 2023-02-05
### Fixed

- Fixed a bug resulting from trying to convert a string year to integer

## [2.1.0] - 2023-01-28
### Added

- Status bar message when the data is being processed (tree structure is being constructed)
  - The speed of this process depends on the hardware used and the amount of data to sort into the different tree levels
- Added [**SECURITY** info](https://github.com/erykjj/jwlmanager/blob/master/.github/SECURITY.md)

### Changed

- Significant **code rewrite to utilize Pandas** module for internal data handling
- Add Favorite only limits Bible editions available by the selected language (preventing adding a favorite for a publication that doesn't exist)
- Improved status bar messages
- More complete year classification for many publications
- Updated translations
  - Special thanks to @Nickyes & @AlessandroLucchet
- Slight layout adjustments

### Removed

- Removed options for Grouped and Detailed views
  - Replaced with additional Type grouping

## [2.0.2] - 2023-01-18
### Added

- Italian translation (mostly done)
  - Thank you to a couple of friends!
- **Automatic builds** (Windows and macOS packages)
  - Please report any issues ;-)

### Changed

- Multiple note tags are now separated by " | " instead of ","
- Updated README
- Updated French translations
- **Disabled Detailed View** option
  - It was very slow and causing problems with large data sets

### Fixed


### Removed

- Removed Detailed and Grouped options
  - Added a grouping option by Type instead

- Removed README.txt (text version of the README, which is in markdown format)

## [2.0.1] - 2023-01-04
### Added

- **Multi-language support** (internationalization/i18n)
  - Localization/L10n in English, French, Spanish
    - others in process of being translated on [Weblate](https://hosted.weblate.org/engage/jwlmanager/)
- Added alert box when change-over to Detailed view could take a long time (with many records to process)

### Changed

- **UI framework** transitioned from Qt5 to Qt6 (PySide2 to PySide6)
  - **NOTE**: Qt6 is not compatible with Windows 7/8
- Rearranged/cleaned up the folder structure
- Cosmetic/layout changes to GUI
- "Obscure" is now "Mask", which is a more appropriate term for this kind of data obfuscation
- Split off usage instructions from README to a separate HELP document

## [1.2.2] - 2022-12-20
### Added

- More precise manifest file included in saved archives

### Changed

- Link to Github repo in About box
- Links to Github in README
- Modified README to highlight multi-platform support

### Fixed

- Fixed some minor type-check warnings
- Fixed SQL for discarding unused records (trimming the DB)
- Blank/new archive had incomplete table structure

## [1.2.1] - 2022-04-25
### Fixed

- Fix for date not being set correctly on Note import

## [1.2.0] - 2022-04-24
### Added

- Last modification date field of notes can now be exported and imported (see README)

## [1.1.0] - 2022-04-12
### Changed

- More precise Note location for re-linking with highlights

### Fixed

- Fixed export/import of special Bible notes (in a book header, for example, instead of a regular verse)
- Fixed gray stickies not showing

## [1.0.1] - 2022-04-07
### Fixed

- Corrected slight mixup on Notes & Highlights color names

## [1.0.0] - 2022-03-27
### Changed

- Data Viewer
  - Modified formatting to include NoteId of each Note
  - Single instance with selection in title
  - Remember window size and position while app is open
- Help window
  - Only one instance
  - Remember window size and position while app is open

### Fixed

- Stop showing additional icon on taskbar when About dialog is opened

## [0.4.0] - 2022-03-20
### Added

- Added data view for Notes (with right-click)
- Added data view for Annotations (with right-click)
- Added drag-and-drop functionality to open archives
- Added drag-and-drop for importing

### Changed

- Independent notes (not related to any publication) are now listed as OTHER (instead of FREE)

### Fixed

- MAJOR FIX: backups made on iPhone/iPad devices have a different db name, which would make the app crash
- Fixed for icons/README not found when script executed from outside of directory
- Fixed opening URLs in default browser

## [0.3.2] - 2022-02-20
### Added

- Better exception handling and reporting

### Changed

- Adjusted About dialog box
- Adjusted Add Favorite dialog box
- Cosmetic/UI adjustments

### Fixed

- Working directory changed on save and export
- Export files weren't always UTF-8 encoded
- Fixed SQL rollback on aborted import
- Selected item count reset when new archive created

## [0.3.1] - 2022-02-10
### Added

- Better handling of export/import file encoding (UTF-8)
- App icon under Mac OS

### Changed

- Adjusted Annotation and Highlight import to accept more general CSV files

## [0.3.0] - 2022-02-04
### Added

- Added obscuring function
- Added general exception handling
- More status bar information on action being taken

### Changed

- Modified UserMark trimming SQL
- Readded reindexing function with progress bar
- Disabled detailed view on file open
- Disabled grouped view on file open
- Code clean-up

### Fixed

- Fixed Bookmark selection

## [0.2.4] - 2022-01-31
### Changed

- Slight adjustment in interface sizing and Help menu

### Fixed

- Fixed cases of unknown publications
- Fixed cases where issue is not a date
- Fixed some still-used UserMark records being trimmed

## [0.2.3] - 2022-01-29
### Added

- Handle unknown media items or publications in Favorites

### Changed

- Cleaned up resources (unnecessary icons, etc.)
- Specify encoding for export/import files

### Fixed

- Fixed SQL for untagged notes

## [0.2.2] - 2022-01-24
### Changed

- Highlights defined by BlockRange instead of UserMark
- Modified trim SQL to clean up unused UserMark records
- Slight adjustment to handle JW Broadcasting video segments in Favorites

## [0.2.1] - 2022-01-19
### Changed

- Re-added publication issue date to grouping by year
- Speeded up tree construction even more

## [0.2.0] - 2022-01-17
### Added

- Progress bar shown when a lot of elements need to be loaded and will slow down the app

### Changed

- Added Bible book number before name for better sorting
- Made Grouped and Detailed view mutually exclusive
- Code clean-up
- README updated
- Minor UI adjustment: slight increase in button height
- Speeded up tree construction

### Fixed

- Fix for tree being constructed twice under some conditions
- Fix for missing items in detailed view

## [0.1.0] - 2022-01-11
### Added

- App icon
- Implemented adding Favorites
- Added detailed view

### Fixed

- Corrected Bookmark count
- Speeded up reindexing

## [0.0.10] - 2022-01-08
### Added

- Changelog file
- Implemented importing Annotations
- Implemented importing Highlights
- Added some exception handling on failed imports

### Changed

- Enabled Save As as soon as an archive is opened
- Updated README with info on importing and adding
- Adjusted Annotations export to work better with importing
- Add current date to new archive manifest

### Fixed

- Line-breaks in Annotations

## [0.0.9] - 2022-01-02
### Added

- Implemented importing Notes
- Implemented creating a new/blank archive
- Added context-aware buttons to interface
  - Add - for Favorites only - process not implemented yet
  - Export - for Notes, Highlights, Annotations
  - Import - for Notes, Highlights, Annotations - process for the last two not implemente yet

### Changed

- Various cosmetic modifications and small bug fixes

## [0.0.8] - 2021-12-28
### Added

- Added option to group by publication type

### Changed

- Updated publications list
- Moved resources to SQLite db
- Improved About and Help dialogs

## [0.0.7] - 2021-12-24
### Added

- Implemented viewing, deleting, exporting, reindexing, saving

____
[Unreleased]: https://github.com/erykjj/jwlmanager
[6.1.0]:https://github.com/erykjj/jwlmanager/releases/tag/v6.1.0
[6.0.0]:https://github.com/erykjj/jwlmanager/releases/tag/v6.0.0
[5.1.2]:https://github.com/erykjj/jwlmanager/releases/tag/v5.1.2
[5.1.1]:https://github.com/erykjj/jwlmanager/releases/tag/v5.1.1
[5.1.0]:https://github.com/erykjj/jwlmanager/releases/tag/v5.1.0
[5.0.0]:https://github.com/erykjj/jwlmanager/releases/tag/v5.0.0
[4.5.3]:https://github.com/erykjj/jwlmanager/releases/tag/v4.5.3
[4.5.2]:https://github.com/erykjj/jwlmanager/releases/tag/v4.5.2
[4.5.1]:https://github.com/erykjj/jwlmanager/releases/tag/v4.5.1
[4.5.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.5.0
[4.4.1]:https://github.com/erykjj/jwlmanager/releases/tag/v4.4.1
[4.4.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.4.0
[4.3.3]:https://github.com/erykjj/jwlmanager/releases/tag/v4.3.3
[4.3.2]:https://github.com/erykjj/jwlmanager/releases/tag/v4.3.2
[4.3.1]:https://github.com/erykjj/jwlmanager/releases/tag/v4.3.1
[4.3.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.3.0
[4.2.1]:https://github.com/erykjj/jwlmanager/releases/tag/v4.2.1
[4.2.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.2.0
[4.1.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.1.0
[4.0.2]:https://github.com/erykjj/jwlmanager/releases/tag/v4.0.2
[4.0.1]:https://github.com/erykjj/jwlmanager/releases/tag/v4.0.1
[4.0.0]:https://github.com/erykjj/jwlmanager/releases/tag/v4.0.0
[3.0.3]:https://github.com/erykjj/jwlmanager/releases/tag/v3.0.3
[3.0.2]:https://github.com/erykjj/jwlmanager/releases/tag/v3.0.2
[3.0.1]:https://github.com/erykjj/jwlmanager/releases/tag/v3.0.1
[3.0.0]:https://github.com/erykjj/jwlmanager/releases/tag/v3.0.0
[2.4.2]:https://github.com/erykjj/jwlmanager/releases/tag/v2.4.2
[2.4.1]:https://github.com/erykjj/jwlmanager/releases/tag/v2.4.1
[2.4.0]:https://github.com/erykjj/jwlmanager/releases/tag/v2.4.0
[2.3.2]:https://github.com/erykjj/jwlmanager/releases/tag/v2.3.2
[2.3.1]:https://github.com/erykjj/jwlmanager/releases/tag/v2.3.1
[2.3.0]:https://github.com/erykjj/jwlmanager/releases/tag/v2.3.0
[2.2.4]:https://github.com/erykjj/jwlmanager/releases/tag/v2.2.4
[2.2.3]:https://github.com/erykjj/jwlmanager/releases/tag/v2.2.3
[2.2.2]:https://github.com/erykjj/jwlmanager/releases/tag/v2.2.2
[2.2.1]:https://github.com/erykjj/jwlmanager/releases/tag/v2.2.1
[2.2.0]:https://github.com/erykjj/jwlmanager/releases/tag/v2.2.0
[2.1.3]:https://github.com/erykjj/jwlmanager/releases/tag/v2.1.3
[2.1.2]:https://github.com/erykjj/jwlmanager/releases/tag/v2.1.2
[2.1.1]:https://github.com/erykjj/jwlmanager/releases/tag/v2.1.1
[2.1.0]:https://github.com/erykjj/jwlmanager/releases/tag/v2.1.0
[2.0.1]:https://github.com/erykjj/jwlmanager/releases/tag/v2.0.1
[2.0.2]:https://github.com/erykjj/jwlmanager/releases/tag/v2.0.2
[1.2.2]:https://github.com/erykjj/jwlmanager/releases/tag/v1.2.2
[1.2.1]:https://github.com/erykjj/jwlmanager/releases/tag/v1.2.1
[1.2.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v1.2.0
[1.1.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v1.1.0
[1.0.1]:https://gitlab.com/erykj/jwlmanager/-/releases/v1.0.1
[1.0.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v1.0.0
[0.4.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.4.0
[0.3.2]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.3.2
[0.3.1]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.3.1
[0.3.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.3.0
[0.2.4]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.2.4
[0.2.3]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.2.3
[0.2.2]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.2.2
[0.2.1]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.2.1
[0.2.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.2.0
[0.1.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.1.0
[0.0.10]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.10
[0.0.9]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.9
[0.0.8]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.8
[0.0.7]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.7

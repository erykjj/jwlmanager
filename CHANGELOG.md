# JWLManager Changelog

## [Unreleased]
### Added

- Progress bar shown when a lot of elements need to be loaded and will slow down the app

### Changed

- Added Bible book number before name for better sorting
- Made Grouped and Detailed view mutually exclusive
- Minor code clean-up
- README updated

### Fixed

- Fix for tree being constructed twice under some conditions

### Removed
____
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
[Unreleased]: https://gitlab.com/erykj/jwlmanager
[0.1.0]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.1.0
[0.0.10]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.10
[0.0.9]:https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.9
[0.0.8]: https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.8
[0.0.7]: https://gitlab.com/erykj/jwlmanager/-/releases/v0.0.7

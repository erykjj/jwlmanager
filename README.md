# JWLManager - v2[^#]
**Looking for help with translation on [Weblate](https://hosted.weblate.org/engage/jwlmanager/)**[^*]   ![Translation status](https://hosted.weblate.org/widgets/jwlmanager/-/qt-ui/88x31-black.png)

## Purpose

This is a **multi-platform application** for viewing and performing various operations on the *user* data stored in a *.jwlibrary* backup archive (created from within the **JW Library** app[^1]: Personal Study > Backup and Restore > Create a backup). A modified *.jwlibrary* archive can then be restored within the app.

In addition to the main functions of **viewing, exporting, importing, and deleting**, the application can also clean up any residual/unused records from the database and re-index the various tables within the database. Items from different backups can be **merged** by exporting the desired items and importing them into an existent archive or into a new one.

![preview](res/images/JWLManager.gif)

____
## Usage

### Windows and Mac OS

Simply [download](https://github.com/erykjj/jwlmanager/releases/latest) and launch the latest **Windows executable** or **macOS app**. If you receive **Windows Defender "unknown publisher" alerts**, you can safely choose "More info" and "Run anyway". See [here](https://github.com/erykjj/jwlmanager/issues/1) for a discussion on what's going on.

### Linux

[Download](https://github.com/erykjj/jwlmanager/releases/latest) and extract the latest release source code; then execute to run (from inside JWLManager folder):

```
$ python3 JWLManager.py
```

Or, make it executable first and run directly:

```
$ chmod +x JWLManager.py
$ ./JWLManager.py
```

You *may* have to install some of the required libraries[^2]. Do [let me know](https://github.com/erykjj/jwlmanager/issues) if you have any difficulties ;-)

If you use the -h flag, you'll see the following options:

```
usage: JWLManager.py [-h] [-v] [-en | -es | -fr]

Manage .jwlibrary backup archives

options:
  -h, --help     show this help message and exit
  -v, --version  show version and exit

interface language:
  -en or leave out for English

  -en            English (default)
  -es            Spanish (español)
  -fr            French (français)
```

Which means that (on all platforms) you can launch the GUI in the desired language by appending the corresponding language code parameter. So, if you want to start the app in Spanish (instead of the default English), you would invoke it as...
Linux terminal: `python3 JWLManager.py -es`
Windows Comand Prompt (or shortcut): `JWLManager.exe -es`
macOS Terminal: `open -a JWLManager.app --args -es`

____
## Operation

See [here](res/HELP.md) for an explanation of how to use.

____
## Feedback

Feel free to [get in touch](https://github.com/erykjj/jwlmanager/issues) and post any issues and suggestions.

[![RSS of releases](res/icons/rss-36.png)](https://github.com/erykjj/jwlmanager/releases.atom)

____
[^#]: This is the current (Qt6/PySide6-based) branch for newer operating systems (Linux, MS Windows 10/11, macOS 10.14 and up). For older systems, see the [v1 branch](https://github.com/erykjj/jwlmanager/tree/Qt5) (based on Qt5/PySide2).
[^*]: To start with: Chinese, French, German, Italian, Portuguese, Russian and Spanish; other volunteers also appreciated. Please contact me at the email in the *About...* box in the app.
[^1]: [JW Library](https://www.jw.org/en/online-help/jw-library/) is a registered trademark of *Watch Tower Bible and Tract Society of Pennsylvania*.
[^2]: `pip3 install argparse filehash PySide6 regex`.

JWLManager - v2*

Purpose

This is a multi-platform application for viewing and performing various
operations on the user data stored in a .jwlibrary backup archive (created from
within the JW Library app#: Personal Study > Backup and Restore > Create a
backup). A modified .jwlibrary archive can then be restored within the app.

In addition to the main functions of viewing, exporting, importing, and
deleting, the application can also clean up any residual/unused records from the
database and re-index the various tables within the database. Items from
different backups can be merged by exporting the desired items and importing
them into an existent archive or into a new one.

--------------------------------------------------------------------------------

Usage

Windows 10/11 and macOS 11+

Simply download and launch the latest Windows executable or macOS app.

Notes - If you receive Windows Defender “unknown publisher” alerts, you can
safely choose “More info” and “Run anyway”. See here for a discussion on what’s
going on.

Linux

Download and extract the latest release source code; then execute to run (from
inside JWLManager folder):

    $ python3 JWLManager.py

Or, make it executable first and run directly:

    $ chmod +x JWLManager.py
    $ ./JWLManager.py

You may have to install some of the required libraries^. Do let me know if you
have any difficulties ;-)

If you use the -h flag, you’ll see the following options:

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

Which means that (on all platforms) you can launch the GUI in the desired
language by appending the corresponding language code parameter. So, if you want
to start the app in Spanish (instead of the default English), you would invoke
it as… - Linux terminal: python3 JWLManager.py -es - Windows Comand Prompt (or
shortcut): JWLManager.exe -es - macOS Terminal:
open -a JWLManager.app --args -es



--------------------------------------------------------------------------------

* This is the current (Qt6/PySide6-based) branch for newer operating systems
(Linux, MS Windows 10/11, macOS 11 “Big Sur” and newer). For older systems, see
the v1 branch (based on Qt5/PySide2).

# JW Library is a registered trademark of Watch Tower Bible and Tract Society
of Pennsylvania.

^ pip3 install filehash PySide6 regex.

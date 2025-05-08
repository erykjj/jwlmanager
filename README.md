[![Static Badge](https://img.shields.io/badge/mirror-orange?style=plastic&logo=gitlab&logoColor=orange&color=black)](https://gitlab.com/erykj/jwlmanager) [![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/erykjj/jwlmanager/total?style=plastic)](https://github.com/erykjj/jwlmanager/releases/latest) [![CodeQL scan](https://img.shields.io/github/actions/workflow/status/erykjj/jwlmanager/github-code-scanning%2Fcodeql?style=plastic)](https://github.com/erykjj/jwlmanager/actions?query=workflow%3ACodeQL) [![Static Badge](https://img.shields.io/badge/releases-orange?style=plastic&logo=rss&logoColor=orange&color=black)](https://github.com/erykjj/jwlmanager/releases.atom)

# JWLManager

This is a **multi-platform[^#] and multi-language[^*] application** for viewing and performing various operations on the *user* data (Annotations, Bookmarks, Favorites, Highlights, Notes and Playlists) stored in a *.jwlibrary* backup archive (created from within the **JW Library** app[^1]: Personal Study → Backup and Restore → Create a backup). A modified *.jwlibrary* archive can then be restored within the app.

In addition to the main functions of **viewing, editing, exporting, importing and deleting**, the application can also clean up any residual/unused records from the database. Items from different backups can be **merged** directly or by exporting the desired items (to a MS Excel spreadsheet or a custom text file) and importing them into an existent archive or into a new one. Exporting Notes to markdown is also possible.

Keep in mind that the more items there are to be sorted into a tree structure, the longer it will take. Also, *do* keep a backup until you're convinced that all is well ;-)

See [here](res/HELP.md) for an explanation of features and options.

![preview](res/JWLManager.gif)

____
## Usage

You can [download](https://github.com/erykjj/jwlmanager/releases/latest) (unzip if necessary) and launch the latest **Linux binary**, **Windows executable**, or **macOS app**. These are self-contained packages (with Python and dependencies included).

* See the [SECURITY section](https://github.com/erykjj/jwlmanager/blob/master/.github/SECURITY.md) for information about **security alerts**, etc.
* The Linux binary needs to be given execute permissions: `chmod +x JWLManager_*`
* The macOS binary needs to have the Gatekeeper quarantine attribute removed: `xattr -dr com.apple.quarantine JWLManager.app`

The state of the application (including the current language) is preserved in a `JWLManager.conf` file created in the same directory as the app. You can delete that file to start with default settings.

You can force the GUI to launch in a language by appending the corresponding language code parameter. So, if you want to start the app in Spanish, you would invoke it as...
- Linux terminal: `python3 JWLManager.py -es`
- Windows Comand Prompt (or shortcut): `JWLManager.exe -es`
- macOS Terminal: `open -a JWLManager.app --args -es`

If you have Python3.11+ installed on your system and can install some of the required dependencies[^2], you can simply clone it:

```
git clone --depth 1 https://github.com/erykjj/jwlmanager.git
cd jwlmanager
pip install -r res/requirements.txt
```

Then...
```
python3 JWLManager.py
```

...or, make it executable first and run directly:

```
chmod +x JWLManager.py
./JWLManager.py
```

If you use the `-h` flag, you'll see the following options:

```
usage: JWLManager.py [-h] [-v] [-de | -en | -es | -fr | -it | -pl | -pt | -ru | -uk] [archive]

Manage .jwlibrary backup archives

positional arguments:
  archive        archive to open

options:
  -h, --help     show this help message and exit
  -v, --version  show version and exit

interface language:
  English by default

  -de            German (Deutsch)
  -en            English (default)
  -es            Spanish (español)
  -fr            French (français)
  -it            Italian (italiano)
  -pl            Polish (Polski)
  -pt            Portuguese (Português)
  -ru            Russian (Pусский)
  -uk            Ukrainian (українська)
```

____
## Feedback, etc.

Feel free to get in touch and post any [issues and/or suggestions](https://github.com/erykjj/jwlmanager/issues).

My other *JW Library* projects: [**JWPubLib**](https://github.com/erykjj/jwpublib) and [**jwlFusion**](https://github.com/erykjj/jwlFusion)

____
#### Footnotes:
[^#]: Requirements: Linux, MS Windows 10/11, macOS 13 "Ventura" and newer
[^*]: Available: Deutsch, English, español, français, italiano, Polski, Português, Pусский, українська; other languages also welcome: [Weblate](https://hosted.weblate.org/engage/jwlmanager/).
[^1]: [JW Library](https://www.jw.org/en/online-help/jw-library/) is a registered trademark of *Watch Tower Bible and Tract Society of Pennsylvania*.
[^2]: See [`/res/requirements.txt`](https://github.com/erykjj/jwlmanager/blob/master/res/requirements.txt).

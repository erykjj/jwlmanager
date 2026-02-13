# Windows and macOS packages

## **Windows Defender** *unknown publisher* alerts

These are due to the fact the the app is not signed with a valid certificate, which is too expensive for me to purchase just for this one (open-source) project. If you receive one of these alerts, you can safely choose "More info" and "Run anyway". *Apparently*, you only need to this once.

As to **virus alerts**, have a look here. These are the virus scan results for one recent Windows executable: https://www.virustotal.com/gui/file/329a4619a0758d4d93b5586115d5dbf20885b667ce5fd8b1483508de714d93c0/detection

You'll notice the great majority of anti-virus products report it as clean. In particular, notice the important/big players: Microsoft, Google, Avast, Kaspersky, McAfee, etc. The app is basically a Python 3 script, and I use [PyInstaller](https://pyinstaller.org/en/stable/) to package it up into a Windows executable. It's this process of compiling a script that some over-zealous anti-virus products *may* flag as dangerous.

## **macOS** slow start/no start

Again, this is because the app package (code) isn't signed with an (expensive) Apple Developer certificate. [Some say](https://forums.macrumors.com/threads/big-sur-apps-slow-to-launch.2279325/post-29855622), the slow start (we're talking 10 to 20 seconds!) is due to the fact that the app is being sent to Apple for "verification". *Apparently*, the launch is much faster if the internet is disabled - **someone please confirm that**.

You can try what is suggested in the *macOS User Guide*:
```
Open an app by overriding security settings

You can open an app that isn’t allowed to open by manually overriding the settings in Security & Privacy preferences.

- In the Finder on your Mac, locate the app you want to open.
  Most apps can be found in the Applications folder.
- Control-click the app icon, then choose Open from the shortcut menu.
- Click Open.

The app is saved as an exception to your security settings, and you can open it in the future by double-clicking it, just as you can any authorized app.
```

You can also do this in a terminal to remove all extended attributes (including the the Gatekeeper quarantine flag) with `xattr -cr JWLManager.app`.

## Alternative

Please keep in mind that I make these packages for convenience only. If they don't work, please try cloning the source locally, and execute the Python script directly. Of course, you must have Python installed, along with the required dependencies.
```
git clone --depth 1 https://github.com/erykjj/jwlmanager.git
cd jwlmanager
pip install -r res/requirements.txt
```
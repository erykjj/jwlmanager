# Windows and macOS packages

## **Windows Defender** *unknown publisher* alerts

These are due to the fact the the app is not signed with a valid certificate, which is too expensive for me to purchase just for this one (open-source) project. If you receive one of these alerts, you can safely choose "More info" and "Run anyway". *Apparently*, you only need to this once.

As to **virus alerts**, have a look here. These are the virus scan results for one of my Windows executable packages (an older one, true, but feel free to scan any more recent one): https://www.virustotal.com/gui/file/757c78220affad753af1d624331351516cffa96d8a81c32a805622c187771023/detection

You'll notice the great majority of anti-virus products report is as clean. In particular, notice the important/big players: Microsoft, Google, Avast, Kaspersky, McAfee, etc. So why do some report trojans and such? Well...

The app is basically a Python 3 script, and I use PyInstaller to package it up into a Windows executable. It's this process of packaging up a script that some over-zealous anti-virus products flag as dangerous, since the script could be malicious.

## **macOS** slow start

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

## Alternative

Please keep in mind that I make these packages for convenience only. If they don't work, please try downloading the [*Source code (zip)*](https://github.com/erykjj/jwlmanager/releases/latest), and execute the Python script directly from within the unzipped folder via `python3 JWLManager.py`. Of course, this requires you have Python installed, along with the required dependencies.
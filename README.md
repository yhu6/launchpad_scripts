# launchpad_scripts
host scripts to work with https://launchpad.net, such as exporting LP (issues).

HOW-TO-Use:
1. install python lib launchpadlib: 
```pip install launchpadlib```

2. run the script
```python launchpad_get_csv.py```

There are 2 user modes: authenticated and anonymous answer "y" on the promote:
Use Credentials? (N for Anonymous) [y/N]
Or otherwise "N" for anonymous access

In authentication mode, a web browser (such as Firefox) will be launched, so you need to have X11 display. 
If you are using ssh login your Linux host, you need to setup "forward X11 over SSH", the following page 
might give you tips about such a config: 
https://unix.stackexchange.com/questions/12755/how-to-forward-x-over-ssh-to-run-graphics-applications-remotely

If you are using ssh client on MacBook, you also have to install XQuartz on your MacBook (OSX).
Follow this guide: https://wikis.nyu.edu/display/ADRC/Enable+X11+Forwarding+on+Mac+OS+X

3. wait until the script finish the downloading. It could be minutes or longer, depending on how much info you
are downloading from your project in Launchpad.net


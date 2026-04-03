# PiCycle
Repository for my University of Galway computing systems hackathon project (IOT is bold).
The python scripts are supposed to work on a Raspberry Pi 3B with a Sense HAT 2 and Pi Camera V3 Module.
Although most features will most likely work as intended regardless of the hardware used, older hardware may lack certain features. 
Notably older Sense HAT models lack colour and brightness sensors.
It is essential that you run 'Main.py' before the other python scripts (preferably at boot) as 'Main.py' contains many of the devices features and is responsible for calling the features it doesnt directly contain.
all python scripts should also be stored in the same directory as eachother. (and the bash username may have to be changed accordingly depending on what you have named your raspberry pi).
also it should be noted that the 3d print case is in need of improvement as the gap intended for the pi-Cameras ribon cable is misplaced and it can be quite difficult to route the cable in a way that works.

Note that the user login for this project was 'igneus' and this appears in some of the code for file paths. If your username differs then replace this with whatever your username is, e.g., 'pi'.
If you are changing any of the file names be aware that you will also have to modify the file paths where these files are run as subprocesses in 'Main.py'.

In order to get the main script to run at boot, we decided to use sytemd per the recommendation of ChatGPT.
The following are the exact steps we took:
1) From terminal, run this command to edit sensemenu.service:
   sudo nano /etc/systemd/system/sensemenu.service
3) Paste the following, replacing 'igneus' with your username:
   [Unit]
  Description=Sense HAT Menu App
  After=multi-user.target

  [Service]
  ExecStart=/usr/bin/python3 /home/igneus/Main.py
  WorkingDirectory=/home/igneus
  StandardOutput=inherit
  StandardError=inherit
  Restart=always
  User=igneus
  Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target

3) Finally run following commands to enable it:
  sudo systemctl daemon-reexec
  sudo systemctl daemon-reload
  sudo systemctl enable sensemenu.service
  sudo systemctl start sensemenu.service

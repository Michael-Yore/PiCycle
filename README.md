# PiCycle
Repository for my University of Galway computing systems hackathon project (IOT is bold).
The python scripts are supposed to work on a Raspberry Pi 3B with a Sense HAT 2 and Pi Camera V3 Module.
Although most features will most likely work as intended regardless of the hardware used, older hardware may lack certain features. 
Notably older Sense HAT models lack colour and brightness sensors.
It is essential that you run main.py before the other python scripts (preferably at boot) as main.py contains many of the devices features and is responsible for calling the features it doesnt directly contain.
all python scripts should also be stored in the same directory as eachother. (and the bash username may have to be changed accordingly depending on what you have named your raspberry pi)
also it should be noted that the 3d print case is in need of improvement as the gap intended for the pi-Cameras ribon cable is misplaced and it can be quite difficult to route the cable in a way that works
(Charles required to explain how the script runs on boot.)

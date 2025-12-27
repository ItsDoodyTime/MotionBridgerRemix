# MotionBridgerRemix
Free motion tracking bridge for [PNGTubeRemix](https://github.com/MudkipWorld/PNGTuber-Remix) by [MudkipWorld (AKA TheMime)](https://github.com/MudkipWorld). Turn your PNG into a VTuber using webcam face, eye, body, and hand tracking. — No Live2D or paid software required!

![motionbridgerremix-social-banner](https://github.com/user-attachments/assets/14094005-f5b9-43d4-b81c-21e99605b282)

# This project is still a WIP!
Currently I don't have an ETA for release date. (Sorry, still working out the flaws and optimization.)

## Who is this tool for?
If you're a streamer, youtuber, short-form or long-form content creator, PNGTuber, and are looking to get yourself a VTuber model but don't want to spend hundreds of dollars on rigging commissions, and you are intimidated and overwhelmed by the amount of attributes in Live2D and VTubeStudio, **then this tool is for you!**

**All you need is a PNG of just art of your character.** If you already have your png, or if you already use PNGTubeRemix you're most of the way there! It doesn't even HAVE to be rigged for tracking, it can be rigged for normal use without tracking and it works just the same! (Of course, rigging it specifically for tracking will produce better and higher quality results.)

Don't worry! If that's something you're interested in, I will go over the entire rigging process with you, to get the best tracking results! :D
Before we start, there are 2 editions of this software. One for expert users and one for beginner to advanced users.

## Which one should you download?
**TL;DR of this section is:**
- if you know how to code in python, download vpngremix-dev-pack.zip
- if you don't know how to code, download vpngremix.exe

**Long version:**
**Dev Pack:**
- This includes EVERYTHING I used in the development process.
- It is very small inf file size since it's just the the source code.
- You need install python and dependencies YOURSELF. (I recommend doing it in a Virtual Environment.)
Use this version if you want to customize the code, or if your model is super advanced.
This just means if you don't know how to code, you need to learn and make your own script.
> **Dependencies to download:**
> - Python (Program Language)
> - OpenCV-Python (Core System - enabling some optimizations, allowing webcam use, and smoother functions)
> - MediaPipe (Motion Tracking)
> - Websocket-Client (Needed to connect to websockets)
> - Numpy (for quick math and arrays)

**MotionBridgeRemix.exe:**
- This is a onefile version that comes with all the dependencies and python bundled.
- It is as simple as install, configure, and run. :)
- It has SOME optimzations (though idk what im doing so it might not make a difference lol)
- It is smaller in size, but still larger than you would expect a translator script to be, due to it being a CV project.
- It limits you to the config file, so if I haven't added a feature or "sprite part", you can't change its values. :/

(I will add more info to this page soon!)

## [Privacy & Usage Notice](https://github.com/ItsDoodyTime/MotionBridgerRemix/blob/main/PRIVACY.md)


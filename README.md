# MotionBridgerRemix
Free motion tracking bridge for [PNGTubeRemix](https://github.com/MudkipWorld/PNGTuber-Remix) by [MudkipWorld (AKA TheMime)](https://github.com/MudkipWorld). Turn your PNG into a VTuber using webcam face, eye, body, and hand tracking. — No Live2D or paid software required!

![motionbridgerremix-social-banner](https://github.com/user-attachments/assets/14094005-f5b9-43d4-b81c-21e99605b282)

---

## 🚧 This Project is Still: Work in Progress!
There is currently **no ETA** for a public release.
> (Sorry, still working out the flaws and optimization.)
---

## Who is this tool for?

This tool is made for:
- Streamers & YouTubers
- Short-form or long-form content creators
- PNGTubers & VTubers
- People interested in VTubing, streaming, and rigging models.
- PNGTubeRemix Users

If you want a VTuber-style model but:
- don’t want to spend hundreds on rigging,
- feel overwhelmed by Live2D or VTube Studio,
- or just want something lightweight and flexible,

**This tool is for you!**

---

## What do you need?

**Just art of your character and [PNGTubeRemix](https://github.com/MudkipWorld/PNGTuber-Remix).** That’s it!

- This tool was made for PNGTubeRemix, **it WON'T work without it!**
- Your PNG **does not need to be specifically rigged for tracking** — standard PNGTuber rigs work just fine.

That said, rigging specifically for tracking will give **better results**.

Don't worry! If that's something you're interested in, I will go over the entire rigging process with you in the tool's documentation, to help you get the best tracking results! :)

---

## MotionBridgerRemix Editions

MotionBridgerRemix comes in **two editions**, depending on your experience level.

### Which one to Download? (TL;DR)

- **You know how to code in Python / want to customize things:**  
  → `MotionBridgeRemix-dev-pack.zip`
- **You don’t know how to code / want plug-and-play:**  
  → `MotionBridgerRemix.exe`

---

## Developer Pack (`MotionBridgeRemix-dev-pack.zip`)

Best for advanced users, developers, or heavy customization.

**What’s included:**
- All source code used during development with comments to help guide you.
- Very small file size (source only)

**Use this version if:**
- You want to modify or extend the code
- Your model rig is super advanced
- You’re comfortable writing or adjusting Python scripts (there's a slight learning curve!)

### Required Dependencies

- **Python** — core language  
- **OpenCV-Python** — webcam input, performance optimizations  
- **MediaPipe** — motion tracking  
- **WebSocket-Client** — communication with PNGTubeRemix
- **NumPy** — fast math and array handling  
> These dependencies are not included in the package!
Streamlined command to install all dependencies: `pip install opencv-python mediapipe websocket-client numpy`

---

## Pre-Packaged Tool (`MotionBridgerRemix.exe`)

Best for beginners and creators who want simplicity or to bring more life to their model.

**Features:**
- One-file executable
- Python and all dependencies bundled
- Simple workflow: **install → configure → run**
- Includes some optimizations (results may vary)


**Notes:**
- Larger file size due to all of the libraries and dependencies
- You're limited to the Configuration  
  - Meaning if I haven't added a feature or sprite part and it isn’t listed in the config, it can’t be modified. :/

This version prioritizes **ease of use over flexibility**.

---

## More Information

More documentation, guides, and examples will be added soon-ish!

---

## Privacy & Usage

Please read the **[Privacy & Usage Notice](https://github.com/ItsDoodyTime/MotionBridgerRemix/blob/main/PRIVACY.md)** before using this software.

---

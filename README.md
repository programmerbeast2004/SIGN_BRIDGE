<div align="center">
  <h1>🤟 SignBridge: Making Gestures Accessible</h1>
  <img src="https://raw.githubusercontent.com/programmerbeast2004/builder_base_assets/main/assets/team.gif" alt="Team GIF" width="100%"/>
  <br><br>
  <strong>Bridging Communication Gaps with Real-Time Gesture Translation</strong>  
  <br><br>
  <a href="https://hocruxsignbridge.netlify.app/">
    <img src="https://img.shields.io/badge/Visit_Website-Hocrux07.netlify.app-brightgreen?style=for-the-badge&logo=netlify" alt="Live Site"/>
  </a>
  <a href="https://drive.google.com/file/d/1uqRw9-hnZu-2L5haH2-s7Sz3mSWkO3Q5/view?usp=sharing">
    <img src="https://img.shields.io/badge/Download_EXE-Click_Here-blue?style=for-the-badge&logo=windows" alt="Download EXE"/>
  </a>
</div>

---

## ✨ At a Glance

| Category | Details |
|----------|---------|
| **Purpose** | Real-time sign language translation for video calls |
| **Tech Stack** | Python, TensorFlow/MediaPipe, OBS, JavaScript, |
| **Deployment** | Standalone EXE + OBS Virtual Camera |
| **Key Features** | Gesture recognition, dynamic overlays, TTS |
| **Team** | 4 developers (see below) |

---

## 🌟 Why SignBridge?

> "Because every gesture deserves to be seen and heard."

We solve three critical challenges in virtual communication:

1-👁️ **Visibility Issues** - Clear text overlays that stay visible for all participants  
2-🔄 **Platform Fragmentation** - Works with any video conferencing tool via OBS Virtual Cam  
3-⏱️ **Real-Time Lag** - Instant gesture-to-text translation with <200ms latency  

---

<table align="center" width="100%" style="max-width: 950px; text-align: center;">

  <tr>
    <td colspan="6" style="padding: 12px; font-size: 20px;"><strong>Technical Deep Dive</strong></td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" height="30" title="Python" /></td>
    <td><img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" height="30" title="TensorFlow" /></td>
    <td><img src="https://img.shields.io/badge/OBS Studio-302E31?style=for-the-badge&logo=obsstudio&logoColor=white" height="30" title="OBS Studio" /></td>
    <td><img src="https://img.shields.io/badge/HTML-E34F26?style=for-the-badge&logo=html5&logoColor=white" height="30" title="HTML" /></td>
    <td><img src="https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white" height="30" title="CSS" /></td>
    <td><img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" height="30" title="JavaScript" /></td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white" height="30" title="Jupyter Notebook" /></td>
    <td><img src="https://img.shields.io/badge/NSIS-00B5E2?style=for-the-badge&logo=nsis&logoColor=white" height="30" title="NSIS Installer" /></td>
    <td><img src="https://img.shields.io/badge/Batchfile-4B4B4B?style=for-the-badge&logo=windows&logoColor=white" height="30" title="Batch File" /></td>
    <td><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg" height="40" title="Bash" /></td>
    <td><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" height="40" title="GitHub" /></td>
    <td><img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg" height="40" title="Git" /></td>
  </tr>
</table>
---

## 🌐 Website Preview

<div align="center">
  <img src="https://raw.githubusercontent.com/programmerbeast2004/builder_base_assets/main/assets/website.gif" alt="Website Preview" width="100%"/>
</div>

---

## 👥 Meet The Team

| Name   | Role             | Contributions                                                                 | LinkedIn |
|--------|------------------|------------------------------------------------------------------------------|----------|
| [Arjit](https://github.com/Arjit74)  | Core Developer   | • Webcam/OBS pipeline<br>• TTS integration<br>• Cross-platform testing       | [LinkedIn](https://www.linkedin.com/in/arjit-sharma74?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app) |
| [Apoorv](https://github.com/programmerbeast2004) | ML Engineer      | • EXE packaging<br>• Model training<br>• Performance optimization            | [LinkedIn](https://www.linkedin.com/in/its-apoorv-?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app) |
| [Ishita](https://github.com/gitwithish) | UI/UX Designer   | • Website development<br>• Branding<br>• EXE download portal                 | [LinkedIn](https://www.linkedin.com/in/ishita-g-2591a1310?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BuxzcxJipSBGkPu2DjKreYQ%3D%3D) |
| [Sree](https://github.com/sreehitha3) | QA & Docs        | • Testing<br>• Documentation<br>• OBS scene templates                        | [LinkedIn](https://www.linkedin.com/in/sreehithathati03?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app) |

---
</div>


## 🚀 Getting Started

### 💿 Installation (For Users)
1. **Download** 👉 [SignBridgePro_Setup.exe]("https://drive.google.com/file/d/1uqRw9-hnZu-2L5haH2-s7Sz3mSWkO3Q5/view?usp=sharing")  
2. **Install** OBS Studio + Virtual Camera plugin  
3. **Run** SignBridge and follow the setup wizard

---

## 🔧 Manual Build (For Developers)

> This section is for developers who want to build, modify, or contribute to **SignBridgePro** locally. It includes complete details of the build pipeline, folder structure, and troubleshooting tips.

---

### 📁 Project Structure
```bash
1.Model Working logic/
├── model/                              # Trained model files
│   ├── label_map.npy
│   └── sign_model.h5
├── test_sequence/                      # Folder for test input sequences
├── generate_test_sequence.py           # Creates test image sequences
├── predict_from_images.py              # Predicts from static image folders
├── requirements.txt                    # Model-specific dependencies
├── SETUP.txt                           # Setup or instructions (optional)
├── simulate_sequence_video.py          # Simulates sign input from video
├── test_model.py                       # Model evaluation or testing script
└── train_model.ipynb                   # Notebook to train the sign recognition model

```
```bash
2.exe logic formation/
├── assets/                             # App icons and visuals
│   └── signBridge_icon.ico
├── build/                              # Auto-generated temp files during PyInstaller build
│   └── SignBridgePro/
├── dependencies/                       # System-level dependencies
│   └── VC_redist.x64.exe               # Required for running EXE on Windows
├── dist/                               # Final build artifacts
│   └── caption_output.txt              # Output from real-time translations
├── installers/                         # OBS installers for virtual camera support
│   ├── OBS-Studio-31.1.1-Windows-x64-installer.exe
│   └── OBS-VirtualCam2.0.4-installer.exe
├── model/                              # ML model and label mappings
│   ├── label_map.npy
│   └── sign_model.h5
├── build_exe.bat                       # Script to generate EXE from Python
├── create_installer.bat                # Script to generate Windows installer
├── LICENSE.TXT
├── main.py                             # Main Python script for real-time translation
├── README.md
├── requirements.txt                    # Python dependencies
├── settings.json                       # App config (e.g., voice toggle, overlay path)
├── SignBridgePro.spec                  # Auto-generated PyInstaller config
└── simple_installer.nsi               # NSIS script for installer creation
```
```bash
3.Website Code/
├── .gitignore                        # Git ignore rules
├── apoorv.jpg                        # Project asset
├── arijit.jpg                        # Project asset
├── GitHub_logo.png                   # GitHub icon
├── hand.jpg                          # Hand icon
├── Hocurx_ppt.pdf                    # Presentation
├── image.png                         # Web graphic
├── index.html                        # Main HTML entry point
├── ishita.jpg                        # Project asset
├── linkedin_logo.png                 # LinkedIn icon
├── logo_sb.jpg                       # Project logo
├── package.json                      # Node.js dependencies
├── package-lock.json                 # Exact dependency tree
├── script.js                         # Frontend JavaScript
├── server.js                         # Backend (Node.js) script
├── sree.jpg                          # Project asset
├── styles.css                        # Custom styling
└── .bolt/                            # Tool or config folder (purpose-defined)

```

---

### 🛠️ Build Process Explained

#### 1. 🔁 Clone & Setup the Project

```bash
git clone https://github.com/your-repo/SignBridge.git
cd SignBridge
pip install -r requirements.txt

```
#### 2. ⚙️ Generate Executable
```bash
build_exe.bat
```
##### This does the following:
###### 1. Generates SignBridgePro.spec
###### 2. Creates build/SignBridgePro/ folder (temp build files)
###### 3. Creates dist/ folder with final .exe and dependencies

### 3. 📦 Create Windows Installer
```bash
create_installer.bat
```
##### This uses simple_installer.nsi with NSIS to:
###### 1. Bundle the .exe from dist/
###### 2. Include dependencies (OBS, VirtualCam, VC_redist)
###### 3. Generate SignBridgePro_Setup.exe

---


### 💡 Pro Tips for Smooth Setup

#### ✅ First-Time Setup
1. Install NSIS from: [https://nsis.sourceforge.io/](https://nsis.sourceforge.io/)
2. Install OBS Studio + Virtual Camera Plugin
3. If EXE gives DLL errors → run `VC_redist.x64.exe` from `dependencies/`

---

### 🐛 Debugging Builds

1. Check `build/warn-SignBridgePro.txt` if the build fails  
2. Ensure all necessary files are present in the `dist/` folder  
3. OBS might lock files — **close OBS** before running `build_exe.bat`

---

### 🛠 Customizing the Installer

Edit the `simple_installer.nsi` script to:
1. Change the default installation directory  
2. Add uninstall shortcut or registry entries  
3. Embed a license agreement, changelog, or version notes

</div>

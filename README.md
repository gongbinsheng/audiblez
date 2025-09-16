# Audiblez Enhanced: Generate audiobooks from e-books

> **🚀 This is an enhanced fork** with additional features and improvements.
>
> **Original Repository**: [santinic/audiblez](https://github.com/santinic/audiblez)
> **Enhanced Features**: Settings persistence, smart engine detection, chapter title extraction, improved reliability

[![Installing via pip and running](https://github.com/santinic/audiblez/actions/workflows/pip-install.yaml/badge.svg)](https://github.com/santinic/audiblez/actions/workflows/pip-install.yaml)
[![Git clone and run](https://github.com/santinic/audiblez/actions/workflows/git-clone-and-run.yml/badge.svg)](https://github.com/santinic/audiblez/actions/workflows/git-clone-and-run.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/audiblez)
![PyPI - Version](https://img.shields.io/pypi/v/audiblez)

### v4 Now with Graphical interface, CUDA support, and many languages!

![Audiblez GUI on MacOSX](./imgs/mac.png)

## What's New in v0.4.10

This enhanced version includes all the improvements from the original v0.4.10 plus additional enhancements:

### Core v0.4.10 Features
- **Apple Silicon Support**: GPU acceleration for M1, M2, M3 Macs using Metal Performance Shaders (MPS)
- **Enhanced Performance**: Significant speed improvements on Apple Silicon hardware
- **Improved Stability**: Better resource management and error handling

### Additional Enhancements in This Fork

#### Smart Settings Persistence
- **Automatic Settings Memory**: The GUI now remembers your preferences (window size, engine, voice, speed, output folder) between sessions
- **YAML Storage**: Settings are saved to `~/.audiblez/settings.yaml` for easy backup and sharing
- **Intelligent Fallback**: If your saved engine isn't available on the current system, Audiblez automatically selects the best available option

#### Enhanced Chapter Navigation
- **Real Chapter Titles**: Extracts actual chapter names from your e-books instead of generic "Chapter 1, Chapter 2"
- **HTML Title Extraction**: Uses `<title>` tags from XHTML content for accurate chapter identification
- **Better Audiobook Experience**: Navigate your audiobooks with meaningful chapter names

#### Smart Engine Detection
- **Visual Indicators**: Engine options are automatically disabled if the hardware isn't available
- **Helpful Tooltips**: Hover over disabled options to understand why they're unavailable
- **Automatic Fallback**: When loading settings, unavailable engines automatically fall back to the best available option

#### Improved Reliability
- **Fixed M4B Generation**: Resolved critical issues where audiobook creation would fail or produce incomplete files
- **Better Error Handling**: More informative error messages and graceful failure recovery
- **WAV File Preservation**: Temporary audio files are preserved when errors occur for easier troubleshooting

#### Modern Development Setup
- **uv Package Manager**: Migrated from Poetry to `uv` for faster, more reliable dependency management
- **Streamlined Installation**: Simpler setup process with better dependency resolution

Audiblez generates `.m4b` audiobooks from regular `.epub` e-books,
using Kokoro's high-quality speech synthesis.

[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) is a recently published text-to-speech model with just 82M params and very natural sounding output.
It's released under Apache licence and it was trained on < 100 hours of audio.
It currently supports these languages: 🇺🇸 🇬🇧 🇪🇸 🇫🇷 🇮🇳 🇮🇹 🇯🇵 🇧🇷 🇨🇳

On a Google Colab's T4 GPU via Cuda, **it takes about 5 minutes to convert "Animal's Farm" by Orwell** (which is about 160,000 characters) to audiobook, at a rate of about 600 characters per second.

On my M2 MacBook Pro, on CPU, it takes about 1 hour, at a rate of about 60 characters per second.


## How to install this Enhanced Version

> **Note**: This is an enhanced fork with additional features. For the original version, see [santinic/audiblez](https://github.com/santinic/audiblez).

### Option 1: Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that handles virtual environments automatically:

```bash
# Install uv first (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh     # Unix/macOS
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install system dependencies
sudo apt install ffmpeg espeak-ng                   # on Ubuntu/Debian 🐧
# or
brew install ffmpeg espeak-ng                       # on Mac 🍏

# Clone and install this enhanced version
git clone https://github.com/YOUR_USERNAME/audiblez.git
cd audiblez
uv sync
uv run audiblez book.epub
```

### Option 2: Direct Git Installation

```bash
# Install system dependencies
sudo apt install ffmpeg espeak-ng                   # on Ubuntu/Debian 🐧
# or
brew install ffmpeg espeak-ng                       # on Mac 🍏

# Clone and install this enhanced version
git clone https://github.com/YOUR_USERNAME/audiblez.git
cd audiblez
pip install -e .
audiblez book.epub
```

### Option 3: Original PyPI Version

To install the original version without our enhancements:

```bash
sudo apt install ffmpeg espeak-ng                   # on Ubuntu/Debian 🐧
pip install audiblez                                 # Original version from PyPI
```

Then you can convert an .epub directly with:

```
audiblez book.epub -v af_sky
```

It will first create a bunch of `book_chapter_1.wav`, `book_chapter_2.wav`, etc. files in the same directory,
and at the end it will produce a `book.m4b` file with the whole book you can listen with VLC or any
audiobook player.
It will only produce the `.m4b` file if you have `ffmpeg` installed on your machine.

## How to run the Enhanced GUI

The GUI is an intuitive graphical interface with smart features and persistent settings.

> **Prerequisites**: You must have installed this enhanced version first (see installation section above).

```bash
# System dependencies (if not already installed)
sudo apt install ffmpeg espeak-ng
sudo apt install libgtk-3-dev        # just for Ubuntu/Debian 🐧, Windows/Mac don't need this

# If you used uv installation
cd audiblez  # your cloned directory
uv run audiblez-ui

# If you used pip installation
cd audiblez  # your cloned directory
pip install pillow wxpython  # additional GUI dependencies
audiblez-ui
```

### For Original Version GUI

To run the original GUI without enhancements:

```bash
pip install audiblez pillow wxpython
audiblez-ui
```

### GUI Features

- **Smart Engine Selection**: Engine options (CPU, CUDA, Apple Silicon) are automatically enabled/disabled based on your hardware
- **Persistent Settings**: Your preferences (window size, engine, voice, speed, output folder) are automatically saved and restored
- **Real-time Tooltips**: Hover over disabled engines to see why they're unavailable
- **Intelligent Fallback**: If your saved engine isn't available, the best alternative is automatically selected
- **Progress Tracking**: Visual progress indicators for each conversion step

## How to run on Windows

After many trials, on Windows we recommend to install audiblez in a Python venv:

1. Open a Windows terminal
2. Create anew folder: `mkdir audiblez`
3. Enter the folder: `cd audiblez`
4. Create a venv: `python -m venv venv`
5. Activate the venv: `.\venv\Scripts\Activate.ps1`
6. Install the dependencies: `pip install audiblez pillow wxpython`
7. Now you can run `audiblez` or `audiblez-ui`
8. For Cuda support, you need to install Pytorch accordingly: https://pytorch.org/get-started/locally/


## Speed

By default the audio is generated using a normal speed, but you can make it up to twice slower or faster by specifying a speed argument between 0.5 to 2.0:

```
audiblez book.epub -v af_sky -s 1.5
```

## Supported Voices

Use `-v` option to specify the voice to use. Available voices are listed here.
The first letter is the language code and the second is the gender of the speaker e.g. `im_nicola` is an italian male voice.

[For hearing samples of Kokoro-82M voices, go here](https://claudio.uk/posts/audiblez-v4.html)

| Language                  | Voices                                                                                                                                                                                                                                     |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 🇺🇸 American English     | `af_alloy`, `af_aoede`, `af_bella`, `af_heart`, `af_jessica`, `af_kore`, `af_nicole`, `af_nova`, `af_river`, `af_sarah`, `af_sky`, `am_adam`, `am_echo`, `am_eric`, `am_fenrir`, `am_liam`, `am_michael`, `am_onyx`, `am_puck`, `am_santa` |
| 🇬🇧 British English      | `bf_alice`, `bf_emma`, `bf_isabella`, `bf_lily`, `bm_daniel`, `bm_fable`, `bm_george`, `bm_lewis`                                                                                                                                          |
| 🇪🇸 Spanish              | `ef_dora`, `em_alex`, `em_santa`                                                                                                                                                                                                           |
| 🇫🇷 French               | `ff_siwis`                                                                                                                                                                                                                                 |
| 🇮🇳 Hindi                | `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`                                                                                                                                                                                                |
| 🇮🇹 Italian              | `if_sara`, `im_nicola`                                                                                                                                                                                                                     |
| 🇯🇵 Japanese             | `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo`                                                                                                                                                                         |
| 🇧🇷 Brazilian Portuguese | `pf_dora`, `pm_alex`, `pm_santa`                                                                                                                                                                                                           |
| 🇨🇳 Mandarin Chinese     | `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`                                                                                                                                 |

For more detaila about voice quality, check this document: [Kokoro-82M voices](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)

## How to run on GPU

By default, audiblez runs on CPU. You can use GPU acceleration with the following options:

- **CUDA**: Use `--cuda` to run on NVIDIA GPUs via CUDA
- **Apple Silicon**: Use `--apple` to run on Apple M1/M2/M3 chips via Metal Performance Shaders (MPS)

Check out this example: [Audiblez running on a Google Colab Notebook with Cuda ](https://colab.research.google.com/drive/164PQLowogprWQpRjKk33e-8IORAvqXKI?usp=sharing]).

## Manually pick chapters to convert

Sometimes you want to manually select which chapters/sections in the e-book to read out loud.
To do so, you can use `--pick` to interactively choose the chapters to convert (without running the GUI).


## Help page

For all the options available, you can check the help page `audiblez --help`:

```
usage: audiblez [-h] [-v VOICE] [-p] [-s SPEED] [-c] [-o FOLDER] epub_file_path

positional arguments:
  epub_file_path        Path to the epub file

options:
  -h, --help            show this help message and exit
  -v VOICE, --voice VOICE
                        Choose narrating voice: a, b, e, f, h, i, j, p, z
  -p, --pick            Interactively select which chapters to read in the audiobook
  -s SPEED, --speed SPEED
                        Set speed from 0.5 to 2.0
  -c, --cuda            Use GPU via Cuda in Torch if available
  -a, --apple           Use GPU via Apple Silicon (MPS) in Torch if available
  -o FOLDER, --output FOLDER
                        Output folder for the audiobook and temporary files

example:
  audiblez book.epub -l en-us -v af_sky

to use the GUI, run:
  audiblez-ui
```

## Troubleshooting

### Engine Availability Issues

If you see disabled engine options in the GUI:

- **CUDA Disabled**: Your system doesn't have a compatible NVIDIA GPU or CUDA isn't installed
  - Solution: Use CPU or Apple Silicon (on Mac) instead
  - CUDA installation: https://pytorch.org/get-started/locally/

- **Apple Silicon Disabled**: You're not on an Apple Silicon Mac (M1, M2, M3)
  - Solution: Use CPU or CUDA (if available) instead

- **Automatic Fallback**: The app automatically selects the best available engine when your saved preference isn't available

### Settings Issues

- **Settings Location**: `~/.audiblez/settings.yaml`
- **Reset Settings**: Delete the settings file to restore defaults
- **Backup Settings**: Copy the YAML file to preserve your preferences

### Conversion Issues

- **M4B Creation Fails**: Ensure `ffmpeg` is installed and in your PATH
- **Chapter Names Wrong**: The app now extracts real chapter titles from e-book HTML content
- **WAV Files Preserved**: If conversion fails, temporary WAV files are kept for troubleshooting

### Performance Tips

- **GPU Acceleration**: Use `--cuda` or `--apple` flags for faster processing
- **Speed Adjustment**: Use `-s 1.5` to increase narration speed
- **Chapter Selection**: Use `--pick` to convert only specific chapters

## Development Setup

For developers wanting to contribute:

```bash
# Clone the repository
git clone https://github.com/santinic/audiblez.git
cd audiblez

# Install with uv (recommended)
uv sync
uv run audiblez-ui

# Or create a virtual environment with pip
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e .
```

## Author

by [Claudio Santini](https://claudio.uk) in 2025, distributed under MIT licence.

Related Article: [Audiblez v4: Generate Audiobooks from E-books](https://claudio.uk/posts/audiblez-v4.html)

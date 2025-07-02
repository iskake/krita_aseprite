# Krita Aseprite file plugin

Plugin for loading aseprite files in Krita.

![Demo image](demo.png)

## Installation

To install this plugin, simply copy (or make a symbolic link of) both the `krita_aseprite.desktop` file and `krita_aseprite/` folder to the `pykrita/` folder in your resource folder (`Settings -> Manage Resources -> Open Resource Folder`)

Then simply enable the plugin in the Python Plugin Manager (`Settings -> Configure Krita -> Python Plugin Manager`)

## Usage

Open aseprite file: `Tools -> Scripts -> Open Aseprite file...`

## What works

This plugin is currently very wip!!

So far there is support for opening Aseprite files into a new document with all cels from the first frame.

## What doesn't

Here's a non-exhaustive list of things not yet implemented:
- Saving documents as `.aseprite` / `.ase` files
- Palettes
    - Transparent color idx in sprites with Indexed color mode
- Grids
- Anything involving tiles / tilesets
- Tags
- Any and all user data (e.g. custom layer colors)
- Files with more than one frame (such files still load, but only the cels in the first frame will be added to the document)
    - Additionally, due to how krita handles animations vs. aseprite (with tags and user data), this might require custom dockers to implement
- etc...

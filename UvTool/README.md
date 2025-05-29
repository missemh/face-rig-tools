# UV Transfer Tool for Maya

A PySide2-based UI tool for Autodesk Maya to transfer UVs between meshes using different sampling methods.

---

## Overview

This tool provides a user-friendly dialog inside Maya to:

- Select a **source mesh** to copy UVs from.
- Select one or multiple **target meshes** to apply the UVs.
- Choose the **sampling space** method for UV transfer.
- Transfer UVs with a single button click using Maya's native `transferAttributes` command.

The UI uses PySide2 for native integration and includes styled buttons and input fields for a clean experience.

---

## Features

- Load and clear source and target mesh selections.
- Choose from five sampling spaces:
  - World
  - Local
  - UV
  - Component
  - Topology
- Transfer UVs with history cleanup.
- Styled buttons and inputs for better user experience.
- Dialog stays on top of Maya windows.

---

## Requirements

- Autodesk Maya (version with PySide2 support, typically Maya 2017+)
- Python 2.7 or 3.x depending on your Maya version
- PySide2 (comes bundled with Maya)
- `maya.cmds` module (default in Maya)

---

## Installation

1. Copy the script into Maya's Script Editor or save as a `.py` file.
2. Run the script inside Maya's Python environment.
3. The UI dialog will appear and remain on top.

---

## Usage

1. Select the source mesh in Maya viewport or outliner.
2. Click **Load** next to "Source" to set it.
3. Select one or multiple target meshes.
4. Click **Load** next to "Target(s)" to set them.
5. Choose the desired sample space from the dropdown.
6. Click **Transfer UVs** to apply UVs from the source to targets.

---

## Code Structure

- `UvCopyUi` — Main dialog class implementing the UI.
- Utility function `get_maya_main_window()` — retrieves Maya's main window for parenting.
- Transfer logic uses Maya's `cmds.transferAttributes()` with sample space mapping.
- Custom button and input styles defined within the class.

---

## Example

```python
from your_uv_transfer_module import UvCopyUi, get_maya_main_window

ui = UvCopyUi(parent=get_maya_main_window())
ui.show()

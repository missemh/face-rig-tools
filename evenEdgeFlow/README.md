# edgeFlowTool

**Description:**  
Precisely redistributes edges with more control than the standard Relax tool.  
Designed and iconed by me, this tool runs Maya’s standard edge flow on each selected edge over three iterations.  
Useful for smoothing edge flow after removing or adding edges to make it more even.

---

## Installation

1. Copy the icon file `edgeFlowIcon.png` to your Maya preferences icons folder:  
   - macOS: `~/Library/Preferences/Autodesk/maya/<version>/prefs/icons`  
   - Windows: `Documents\maya\<version>\prefs\icons`

2. Place the script `edgeFlowTool.py` in your Maya scripts folder:  
   - macOS: `~/Library/Preferences/Autodesk/maya/<version>/prefs/scripts`  
   - Windows: `Documents\maya\<version>\prefs\scripts`

3. In Maya, open the Script Editor and run:

```python
import maya.cmds as cmds

# Name of your shelf (change if you want)
shelf_name = 'Custom'

# Check if the shelf exists; create it if it doesn't
if not cmds.shelfLayout(shelf_name, exists=True):
    cmds.shelfLayout(shelf_name, parent='ShelfLayout')

# Command to run when clicking the shelf button
command = """
import edgeFlowTool
edgeFlowTool.run_edge_flow_on_selection()
"""

# Icon filename (must be in the icons folder)
icon_path = 'edgeFlowIcon.png'

# Create the shelf button
cmds.shelfButton(
    parent=shelf_name,
    label='Edge Flow',
    command=command,
    image=icon_path,
    annotation='Run edge flow on selected edges',
    sourceType='python',
    enableCommandRepeat=True
)

print(f"Shelf button 'Edge Flow' created on shelf '{shelf_name}'.")

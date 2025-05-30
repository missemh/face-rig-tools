# Blendshape Management Utilities

This Python module provides a collection of useful functions designed to streamline and simplify blendshape management workflows in Autodesk Maya. It includes tools for adding new blendshape targets, handling corrective shapes, and automating common blendshape-related tasks.

## Features

- Add new blendshape targets with support for corrective and corrective-on-corrective deltas.
- Automatically find the next available target index on existing blendShape nodes.
- Manage control attributes for precise pose setup and resetting.
- Seamless integration with Maya's `cmds` module for pipeline-friendly workflows.

## Installation

Copy the Python script into your Maya scripts directory or any accessible Python path in Maya. Then import it in your scripts or Maya Python tab:

```python
import blendshape_utils
# ----------------------------------------------------------------------
"""
Function: find_index_for_next_target_on_blendshape
--------------------------------------------
Finds the highest existing target index on a blendShape node and returns the next available index.
Parameters:blendshape_node (str): The name of the blendShape node.
Returns: int: The next available target index (0 if none found).
Usage:
blendshape_node = "body_bs"
next_target_index = find_index_for_next_target_on_blendshape(blendshape_node)
"""

def find_index_for_next_target_on_blendshape(blendshape_node):
    aliases = cmds.aliasAttr(blendshape_node, q=True)
    if aliases:
        # Get every second item starting from index 1 (the attribute names)
        indices = []
        for attr in aliases[1::2]:
            # attr looks like "weight[0]", "weight[1]", etc.
            index = int(attr.split("[")[1].split("]")[0])
            indices.append(index)
        highest_index = max(indices)
        next_index = highest_index + 1
        print("Highest blendshape index:", highest_index)
        print("Next blendshape target index will be:", next_index)
        return next_index
    else:
        print("No blendshape targets found, starting at 0")
        return 0


# ----------------------------------------------------------------------
"""
Function: find_corrective_on_corrective_delta
--------------------------------------------
Creates a corrective delta mesh based on an existing corrective target,
by applying control attribute values and generating a new blendshape delta
on the neutral mesh.

Parameters:
    base_mesh (str): The original base mesh affected by skinning.
    neutral_mesh (str): The neutral mesh used for creating corrective shapes.
    skin_cluster (str): The name of the skinCluster node.
    blendshape_node (str): The blendShape node to enable/disable during processing.
    target_mesh (str): The corrective target mesh (usually with "_trgt" suffix).
    controls (list of str): Control objects to set for driving the delta pose.
    attrs (list of str): Attributes on controls to set.
    values (list of float): Values to apply to the controls' attributes.

Returns:
    str: The name of the newly created neutral delta mesh.

Usage:
neutral_delta = find_corrective_on_corrective_delta(
    base_mesh="body_geo",
    neutral_mesh="neutral_geo",
    skin_cluster="body_sc",
    blendshape_node="body_bs",
    target_mesh="LR_eyebrowInner_down_trgt",
    controls=["R_eyebrowInner_ctrl", "L_eyebrowInner_ctrl"],
    attrs=["translateY", "translateY"],
    values=[-3.074, -3.074]
)
"""

def find_corrective_on_corrective_delta(
    base_mesh, 
    neutral_mesh, 
    skin_cluster, 
    blendshape_node, 
    target_mesh, 
    controls, 
    attrs, 
    values
    ):

    delta_name = target_mesh.replace("_trgt", "_delta")
    target_name = target_mesh.replace("_trgt", "")

    # Step 2: Turn on skin cluster and turn off blendshape node
    cmds.setAttr(f"{skin_cluster}.envelope", 1)
    cmds.setAttr(f"{blendshape_node}.envelope", 0)

    # Step 3: Set controls to desired delta pose
    for ctrl, attr, val in zip(controls, attrs, values):
        cmds.setAttr(f"{ctrl}.{attr}", val)

    # Step 3 (continued): Find the delta shape and rename it
    delta_mesh = cmds.invertShape(base_mesh, target_mesh)
    delta = cmds.rename(delta_mesh, delta_name)
    delta_shape_node = cmds.listRelatives(delta, shapes=True, fullPath=True)[0]
    cmds.rename(delta_shape_node, f"{delta_name}Shape")

    # Step 4: Turn off skin cluster and turn on blendshape node
    cmds.setAttr(f"{skin_cluster}.envelope", 0)
    cmds.setAttr(f"{blendshape_node}.envelope", 1)

    # Step 5: Create blendshape on neutral with base mesh and delta as targets
    neut_blendshape = cmds.blendShape(base_mesh, delta, neutral_mesh)[0]
    cmds.setAttr(f"{neut_blendshape}.envelope", 1)
    cmds.setAttr(f"{neut_blendshape}.{base_mesh}", -1)
    cmds.setAttr(f"{neut_blendshape}.{delta}", 1)

    # Step 5 (continued): Duplicate the resulting shape
    neutral_delta = cmds.duplicate(neutral_mesh, n=target_name)
    nd_shape_node = cmds.listRelatives(neutral_delta, shapes=True, fullPath=True)[0]
    cmds.rename(nd_shape_node, f"{target_name}Shape")

    # Step 6: Reset the neutral for future use
    cmds.setAttr(f"{neut_blendshape}.envelope", 0)
    cmds.delete(neutral_mesh, constructionHistory=True)

    # Step 7: Turn on skin cluster; blendshape node off
    cmds.setAttr(f"{skin_cluster}.envelope", 1)
    cmds.setAttr(f"{blendshape_node}.envelope", 0)

    # Reset controls
    for ctrl, attr, val in zip(controls, attrs, values):
        cmds.setAttr(f"{ctrl}.{attr}", 0)

    return neutral_delta[0]

# ----------------------------------------------------------------------
"""
Function: add_new_blendshape_target
----------------------------------------------------------------------
Adds a new target shape to a blendShape node, optionally using corrective on corrective deltas.

Parameters:
    base_mesh (str): The mesh that the blendShape affects (the base geometry).
    target_mesh (str): The target mesh representing the shape to add (usually ends with '_trgt').
    skin_cluster (str): The skinCluster node name controlling skin deformation.
    connector (str): The attribute that triggers the blendShape target weight (e.g., a control attribute).
    controls (list of str): List of control objects to set for the corrective pose.
    attrs (list of str): List of attributes on the controls to set.
    values (list of float): List of values to set on the corresponding control attributes.
    neutral_mesh (str, optional): The neutral mesh used for corrective blendShapes (default None).
    blendshape_node (str, optional): The existing blendShape node name. If None, a new blendShape is created.
    corrective_on_corrective_flag (bool, optional): If True, calculates a corrective-on-corrective delta instead of a direct delta.

Returns:
    str: The name of the blendShape node updated or created.

Usage:
    base_mesh = "body_geo"
    target_mesh = "LR_eyebrowInner_down_trgt"
    skin_cluster = "body_sc"
    connector = "LR_eyebrowInnerUpDownComb_mdn.outputX"
    controls = ["R_eyebrowInner_ctrl", "L_eyebrowInner_ctrl"]
    attrs = ["translateY", "translateY"]
    values = [-3.074, -3.074]
    blendshape_node = "body_bs"
    
    blendshape_node = add_new_blendshape_target(
        base_mesh, target_mesh, skin_cluster, connector,
        controls, attrs, values, blendshape_node=blendshape_node,
        corrective_on_corrective_flag=True
    )
"""

def add_new_blendshape_target(
    base_mesh, 
    target_mesh, 
    skin_cluster, 
    connector, 
    controls, 
    attrs, 
    values, 
    neutral_mesh=None, 
    blendshape_node=None, 
    corrective_on_corrective_flag=False
    ):

    target_name = target_mesh.replace("_trgt", "")

    if corrective_on_corrective_flag:
        delta_mesh = find_third_type_corrective_delta(skin_cluster, blendshape_node, target_mesh, controls, attrs, values)
    else:
        # Set controls to desired delta pose
        for ctrl, attr, val in zip(controls, attrs, values):
            cmds.setAttr(f"{ctrl}.{attr}", val)

        cmds.setAttr(f"{blendshape_node}.envelope", 0)

        delta_mesh = cmds.invertShape(base_mesh, target_mesh)
        delta_mesh = cmds.rename(delta_mesh, target_name)

    if blendshape_node:
        new_target_index = find_index_for_next_target_on_blendshape(blendshape_node)
        cmds.blendShape(blendshape_node, edit=True, t=(base_mesh, new_target_index, delta_mesh, 1))
    else:
        blendshape_name = base_mesh.replace("_geo", "_bs")
        blendshape_node = cmds.blendShape(delta_mesh, base_mesh, name=blendshape_name)

    # Connect triggering attribute to blendshape weight
    cmds.connectAttr(connector, f"{blendshape_node}.{target_name}", force=True)

    print(f"Target '{target_name}' added to blendShape '{blendshape_node}' and connected.")

    # Reset control attributes
    for ctrl, attr, val in zip(controls, attrs, values):
        cmds.setAttr(f"{ctrl}.{attr}", 0)

    cmds.setAttr(f"{blendshape_node}.envelope", 1)

    return blendshape_node



### ----------------------------------------------------------------------
"""
Function: mirror_crv_left_to_right
----------------------------------------------------------------------
Mirrors the left half of a curve’s CV positions to the right half by flipping the X coordinate.
Parameters:
    crv (str): The name of the curve to mirror.
Returns:
    None
Usage:
    # Select one or more curves in Maya, then run:
    sel = cmds.ls(selection=True, flatten=True)
    for crv in sel:
        mirror_crv_left_to_right(crv)
"""

def mirror_crv_left_to_right(crv):
    """Mirrors the given curve from left to right by copying left-side CV positions to right-side CVs."""
    if not cmds.objExists(crv):
        cmds.warning(f"Curve {crv} does not exist!")
        return

    # Get number of CVs
    num_cvs = cmds.getAttr(f"{crv}.spans") + cmds.getAttr(f"{crv}.degree")
    if num_cvs % 2 != 0:
        cmds.warning(f"Curve {crv} has an odd number of CVs ({num_cvs}), mirroring may not be symmetric.")
    
    half = num_cvs // 2

    # Store positions of left-side CVs (first half)
    left_cv_positions = []
    for i in range(half):
        pos = cmds.pointPosition(f"{crv}.cv[{i}]", world=True)
        left_cv_positions.append(pos)

    # Right-side CVs indices (second half, reversed order)
    right_cvs = list(range(num_cvs - 1, half - 1, -1))

    # Mirror positions from left to right
    for cv, pos in zip(right_cvs, left_cv_positions):
        x_pos = -pos[0]  # Negate X value for mirroring
        cmds.move(x_pos, pos[1], pos[2], f"{crv}.cv[{cv}]", absolute=True)
    
    print(f"Mirrored {crv} successfully!")


### ----------------------------------------------------------------------
"""
Function: turn_off_blendshapes
--------------------------------------------
Sets all blendshape target weights to 0 (turns them off) for given blendShape nodes.
Parameters:
    blendshape_nodes (list of str): List of blendShape node names.
Returns:
    None
Usage:
    blendshape_nodes = ["face_bs", "body_bs"]
    turn_off_blendshapes(blendshape_nodes)
"""

def turn_off_blendshapes(blendshape_nodes):
    for bs_node in blendshape_nodes:
        if cmds.objExists(bs_node):
            # Get all the weight attributes
            aliases = cmds.aliasAttr(bs_node, q=True)
            if aliases:
                for i in range(0, len(aliases), 2):
                    weight_attr = f"{bs_node}.{aliases[i]}"
                    try:
                        cmds.setAttr(weight_attr, 0)
                    except:
                        print(f"Could not set {weight_attr}")
        else:
            print(f"{bs_node} does not exist.")










def create_delta_crvs(side, x_attrs, y_attrs, corrected_curves, pose_names, ctrl, base_crv):
    delta_crvs = []
    delta_names = []

    for x, y, old_crv, pose in zip(x_attrs, y_attrs, corrected_curves, pose_names):
        cmds.setAttr(f"{ctrl}.translateX", x)
        cmds.setAttr(f"{ctrl}.translateY", y)

        delta_name = f"{side}_lipCorner{crv}Crv_{pose}"
        delta_names.append(delta_name)

        delta_crv = cmds.invertShape(base_crv, old_crv)
        delta_crv = cmds.rename(delta_crv, delta_name)

        delta_crvs.append(delta_crv)

    # Reset translate
    cmds.setAttr(f"{ctrl}.translateX", 0)
    cmds.setAttr(f"{ctrl}.translateY", 0)    

    print("delta curves:", delta_crvs)
    print("delta names:", delta_names)
    return delta_crvs, delta_names




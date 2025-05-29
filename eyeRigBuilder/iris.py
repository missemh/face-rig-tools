import maya.cmds as cmds
import maya.OpenMaya as om
import math

class EyeballRig:
    def __init__(self, iris_edges, pupil_edges, r_eye_flag=True):
        self.iris_edges = iris_edges
        self.pupil_edges = pupil_edges
        self.create_eyeball_rig(r_eye_flag)

    def create_eyeball_rig(self, right_eye_flag):
        self.create_rig_groups()

        if right_eye_flag:
            sides = ["l", "r"]
        else:
            sides = ["l"]

        for side in sides:
            eye_joints = []

            selected_iris_edges = []
            selected_pupil_edges = []
            selected_iris_skin_edges = []
            selected_pupil_skin_edges = []

            rig_grp = cmds.group(empty=True, n=f"{side}_eyeRig_grp")

            if side == "r":
                for iris_main, pupil_main in zip(self.iris_edges, self.pupil_edges):
                    r_iris_main = iris_main.replace("l_", "r_")
                    r_pupil_main = pupil_main.replace("l_", "r_")
                    selected_iris_edges.append(r_iris_main)
                    selected_pupil_edges.append(r_pupil_main)

            elif side == "l":
                for iris_main, pupil_main in zip(self.iris_edges, self.pupil_edges):
                    selected_iris_edges.append(iris_main)
                    selected_pupil_edges.append(pupil_main)

            iris_crv, pupil_crv = self.create_iris_and_pupil_curves(side, selected_iris_edges, selected_pupil_edges)
            center_loc, pupil_loc = self.find_aim_of_the_pupil(side, f"{side}_eye_geo", pupil_crv)

            if side == "l":
                self.create_eyeball_joints(center_loc, jnt_parent=self.skel_grp)
                eye_jnt = self.l_eye_jnt
            if side == "r":
                eye_jnt = self.r_eye_jnt

            aim_jnt, pupil_jnt = self.create_eye_aim_joints(side, pupil_loc, center_loc, eye_jnt)

            curves = [iris_crv, pupil_crv]
            names = ["iris", "pupil"]

            up_obj = self.create_up_locator(side, aim_jnt, iris_crv, rig_grp)

            iris_cv_aim_joints, iris_cv_tip_joints = self.create_joints_for_each_cv_on_curves(side, iris_crv, eye_jnt)
            iris_cv_offsets, iris_cv_offset_drivers = self.create_drivers_for_each_cv_on_curves(side, iris_crv, "iris", rig_grp)

            pupil_cv_aim_joints, pupil_cv_tip_joints = self.create_joints_for_each_cv_on_curves(side, pupil_crv, eye_jnt)
            pupil_cv_offsets, pupil_cv_offset_drivers = self.create_drivers_for_each_cv_on_curves(side, pupil_crv, "pupil", rig_grp)

            self.aim_cv_joints_to_cv_drivers(iris_cv_offset_drivers, iris_cv_aim_joints, iris_cv_tip_joints, up_obj, aim_jnt)
            self.aim_cv_joints_to_cv_drivers(pupil_cv_offset_drivers, pupil_cv_aim_joints, pupil_cv_tip_joints, up_obj, aim_jnt)

            eye_joints.extend(iris_cv_aim_joints + iris_cv_tip_joints + pupil_cv_aim_joints)
            eye_joints.append(eye_jnt)
            eye_joints.append(aim_jnt)

            iris_tips = iris_cv_tip_joints
            pupil_tips = pupil_cv_tip_joints
            pupil_drivers = pupil_cv_offset_drivers
            iris_drivers = iris_cv_offset_drivers
            crv = pupil_crv

            pupil_scale_jnts, pupil_tip_jnts = self.create_pupil_scale(side, iris_tips, pupil_tips, pupil_drivers, iris_drivers, pupil_cv_aim_joints, up_obj, crv)

            eye_joints.extend(pupil_scale_jnts + pupil_tip_jnts)

            skin_cluster = self.bind_eye_geo_to_create_skin_cluster(side, eye_joints, pupil_jnt, f"{side}_eye_geo", f"{side}_pupil_geo")

            self.create_blendshapes(side, pupil_crv)
            self.create_controls(side, iris_crv, pupil_crv, aim_jnt, up_obj, pupil_jnt)

            locs = [center_loc, pupil_loc]
            self.clean_up_outliner(side, locs)


            cmds.parent(rig_grp, self.eye_rig_grp)
            side_to_print = "Left" if side == "l" else "Right"
            print(f"{side_to_print} rig and initial skinning complete.")

        
        cmds.parent(self.eye_rig_grp, self.eye_grp)
        cmds.parent(self.geo_grp, self.eye_grp)
        cmds.parent(self.skel_grp, self.eye_grp)
        cmds.setAttr(f"{self.skel_grp}.visibility", 0)

    def create_rig_groups(self):
        self.eye_grp = cmds.group(empty=True, n="eye_grp")
        self.eye_rig_grp = cmds.group(empty=True, n="rig_grp")
        self.geo_grp = cmds.group(empty=True, n="geo_grp")
        self.skel_grp = cmds.group(empty=True, n="skel_grp")

        cmds.parent("r_eye_geo", self.geo_grp)
        cmds.parent("l_eye_geo", self.geo_grp)
        cmds.parent("r_pupil_geo", self.geo_grp)
        cmds.parent("l_pupil_geo", self.geo_grp)

    def create_iris_and_pupil_curves(self, side, iris_edges, pupil_edges):
        iris_crv = self.create_curve_from_edge(side, "iris", iris_edges)

        cmds.select(clear=True)
        cmds.select(iris_crv)
        cmds.CenterPivot(iris_crv)
        cmds.select(clear=True)

        pupil_crv = self.create_curve_from_edge(side, "pupil", pupil_edges)

        return iris_crv, pupil_crv


    def create_curve_from_edge(self, side, name, edges):
        cmds.select(clear=True)
        cmds.select(edges)
        
        curve_name = f"{side}_{name}_crv"
        curve_from_edge = cmds.polyToCurve(form=1, degree=1, conformToSmoothMeshPreview=0, ch=0)[0]
        curve_from_edge = cmds.rename(curve_from_edge, curve_name)

        return curve_from_edge

    def find_aim_of_the_pupil(self, side, eyeball_geo, pupil_crv):
        # Returns a group based on the eyeball geometry and pupil vertex to position the master controls
        # Find aim of pupil using the eyeball geometry and the vertex

        aim_center_loc = cmds.spaceLocator(name=f"{side}_eyeAim_loc")[0]
        cmds.delete(cmds.parentConstraint(eyeball_geo, aim_center_loc, mo=False))

        pupil_center_loc = cmds.spaceLocator(name=f"{side}_eyePupil_loc")[0]

        cmds.select(clear=True)
        cmds.select(pupil_crv)
        cmds.CenterPivot(pupil_crv)
        cmds.select(clear=True)


        cmds.delete(cmds.parentConstraint(pupil_crv, pupil_center_loc, mo=False))

        cmds.delete(cmds.aimConstraint(pupil_center_loc, aim_center_loc, aimVector=[0, 0, 1], upVector=[0, 1, 0]))

        return aim_center_loc, pupil_center_loc


    def create_eyeball_joints(self, center_loc, jnt_parent=None):
        # Create left and right eye/eyelid joints
        cmds.select(clear=True)
        
        self.l_eye_jnt = cmds.joint(name=f"l_eye_jnt")
        cmds.delete(cmds.parentConstraint(center_loc, self.l_eye_jnt, mo=False))
        self.r_eye_jnt = cmds.mirrorJoint(self.l_eye_jnt, mirrorYZ=True, mirrorBehavior=True, searchReplace=("l_", "r_"))[0]

        # Apply transformations for the left eye joint
        cmds.makeIdentity(self.l_eye_jnt, apply=True, translate=True, rotate=True, scale=True)

        for jnt, side in zip([self.l_eye_jnt, self.r_eye_jnt], ["l_", "r_"]):
            cmds.makeIdentity(jnt, apply=True, translate=True, rotate=True, scale=True)
            self.label_joint(side, jnt)
            if jnt_parent:
                cmds.parent(jnt, jnt_parent)


    def create_eye_aim_joints(self, side, pupil_loc, eye_control, eyeball_jnt):
        # Creates right and left side separately, right side is NOT a mirror of left. Point constraints not parent constraints.
        # Creates joint at center of eye and joint at pupil position
        # These joints are used to create the eye aim

        cmds.select(clear=True)
        aim_jnt = cmds.joint(name=f"{side}_eyeAim_jnt")
        
        cmds.select(clear=True)
        pupil_jnt = cmds.joint(name=f"{side}_eyePupil_jnt")
        cmds.select(clear=True)
        pupil_end_jnt = cmds.joint(name=f"{side}_eyePupilEnd_jnt")

        self.label_joint(side, aim_jnt)
        self.label_joint(side, pupil_jnt)
        self.label_joint(side, pupil_end_jnt)

        cmds.delete(cmds.pointConstraint(eyeball_jnt, aim_jnt, mo=False))
        cmds.delete(cmds.parentConstraint(eyeball_jnt, pupil_jnt, mo=False))
        cmds.delete(cmds.parentConstraint(pupil_loc, pupil_end_jnt, mo=False))
        cmds.delete(cmds.aimConstraint(pupil_end_jnt, pupil_jnt, aimVector=[0, 0, 1], upVector=[0, 1, 0]))

        eyeball_jnt_name = self.isolate_name(eyeball_jnt)
        cmds.parent(pupil_end_jnt, pupil_jnt)
        cmds.parent(pupil_jnt, aim_jnt)
        cmds.parent(aim_jnt, eyeball_jnt_name)

        return aim_jnt, pupil_jnt

    def create_joints_for_each_cv_on_curves(self, side, crv, eye_jnt):
        cv_aim_joints = []
        cv_tip_joints = []
        
        cvs = cmds.ls(f"{crv}.cv[*]", flatten=True)
        for i in range(len(cvs)):
            index_str = str(i).zfill(2)
        
            # Create joint to sit in center of eyeball
            cmds.select(clear=True)
            jnt = cmds.joint(name=crv.replace("_crv", f"{index_str}_jnt"))
            
            # Create tip joint to sit in at cv point on curve
            cmds.select(clear=True)
            jnt_tip = cmds.joint(name=crv.replace("_crv", f"Tip{index_str}_jnt"))
        
            # Position joints
            cmds.delete(cmds.parentConstraint(eye_jnt, jnt, mo=False))
            cv_pos = cmds.xform(cvs[i], query=True, translation=True, worldSpace=True)
            cmds.xform(jnt_tip, translation=cv_pos, worldSpace=True)
        
            cv_tip_joints.append(jnt_tip)
            cv_aim_joints.append(jnt)


        return cv_aim_joints, cv_tip_joints

    def create_drivers_for_each_cv_on_curves(self, side, crv, name, parent_grp):
        cv_offsets = []
        cv_offsets_drivers = []

        grp_name = f"{side}_{name}Driver_grp"

        driver_grp = cmds.group(empty=True, name=grp_name)

        cvs = cmds.ls(f"{crv}.cv[*]", flatten=True)
        for i in range(len(cvs)):
            cmds.select(clear=True)
            index_str = str(i).zfill(2)

            control_name = crv.replace("_crv", f"{index_str}Drv_grp")

            cv_offset  = cmds.group(empty=True, name=control_name)
            cmds.select(clear=True)
            cv_offset_drv  = cmds.group(empty=True, name=control_name.replace("Drv_grp", "_drv"))
            cmds.select(clear=True)
            cmds.parent(cv_offset_drv, cv_offset)
            cmds.parent(cv_offset, driver_grp)

            cv_offsets.append(cv_offset)
            cv_offsets_drivers.append(cv_offset_drv)

            point_on_crv = cmds.createNode("pointOnCurveInfo", name=crv.replace("_crv", f"{index_str}_pci"))
            crv_shape = cmds.listRelatives(crv, children=True, shapes=True)[0]
            cmds.connectAttr(f"{crv_shape}.worldSpace[0]", f"{point_on_crv}.inputCurve")
            cmds.setAttr(f"{point_on_crv}.parameter", i)
            cmds.connectAttr(f"{point_on_crv}.position", f"{cv_offset}.t")

        cmds.parent(driver_grp, parent_grp)

        return cv_offsets, cv_offsets_drivers



    def aim_cv_joints_to_cv_drivers(self, cv_drivers, cv_aim_joints, cv_tip_joints, up_loc, eye_aim_jnt):
        # parent constrains the tip cv joint to the cv offset and deletes it

        for cv_drv, cv_aim_jnt, cv_tip_jnt in zip(cv_drivers, cv_aim_joints, cv_tip_joints):
            cmds.delete(cmds.pointConstraint(cv_drv, cv_tip_jnt, mo=False))
            cmds.delete(cmds.aimConstraint(cv_drv, cv_aim_jnt, aimVector=[0,0,1], upVector=[0,1,0], worldUpType="object", wuo=f"{up_loc}", mo=False))
            
            # Freeze the transformations so there are zero rotations on the joint
            cmds.makeIdentity(cv_aim_jnt, apply=True, translate=True, rotate=True, scale=True)

            # Re-constrain the joint 
            cmds.aimConstraint(
                cv_drv, 
                cv_aim_jnt, 
                aimVector=[0,0,1], 
                upVector=[0,1,0], 
                worldUpType="object", 
                wuo=f"{up_loc}", 
                mo=False, 
                )

            cmds.parent(cv_tip_jnt, cv_aim_jnt)
            cmds.parent(cv_aim_jnt, eye_aim_jnt)


    def create_pupil_scale(self, side, iris_tips, pupil_tips, pupil_drivers, iris_drivers, pupil_aim_joints, up_loc, crv):
        pupil_scale_jnts = []
        pupil_tip_jnts = []

        rig_grp = f"{side}_eyeRig_grp"

        distance_loc_grp = cmds.group(empty=True, n=f"{side}_pupilScaleLoc_grp")

        # Loop through iris and pupil tips
        for index, (iris_jnt, pupil_jnt, pupil_drv, iris_drv, pupil_aim) in enumerate(zip(iris_tips, pupil_tips, pupil_drivers, iris_drivers, pupil_aim_joints)):
            pupil_jnt = cmds.rename(pupil_jnt, pupil_jnt.replace("Tip", "Scale"))
            pupil_scale_jnts.append(pupil_jnt)
            
            # Duplicate iris joints and parent to world
            pupil_tip = cmds.duplicate(iris_jnt, parentOnly=True, name=pupil_jnt.replace("Scale", "Tip"))[0]
            cmds.parent(pupil_tip, world=True)
            pupil_tip_jnts.append(pupil_tip)

            # Aim constrain pupil joints to the duplicated iris joints
            cmds.delete(cmds.aimConstraint(iris_jnt, pupil_jnt, aimVector=(0, 1, 0), upVector=(0, 0, 1), worldUpType="vector", worldUpVector=(0, 0, 1)))
            cmds.makeIdentity(pupil_jnt, apply=True, translate=True, rotate=True, scale=True)
            cmds.aimConstraint(iris_jnt, pupil_jnt, aimVector=(0, 1, 0), upVector=(0, 0, 1), worldUpType="vector", worldUpVector=(0, 0, 1))
            
            # Parent the duplicated iris joint to the corresponding pupil joint
            cmds.parent(pupil_tip, pupil_jnt)
            
            # Create locators to represent the world space position of the iris and pupil joints
            iris_loc = cmds.spaceLocator(name=f"{iris_jnt}_loc")[0]
            pupil_loc = cmds.spaceLocator(name=f"{pupil_jnt}_loc")[0]

            # Optionally use a constraint to keep locators following the joints (without parenting)
            cmds.pointConstraint(iris_jnt, iris_loc, maintainOffset=False)
            cmds.pointConstraint(pupil_drv, pupil_loc, maintainOffset=False)

            # Set locator visibility to 0
            cmds.setAttr(f"{iris_loc}.visibility", 0)
            cmds.setAttr(f"{pupil_loc}.visibility", 0)

            # Create a distanceBetween node to measure the world space distance
            dist_node = cmds.createNode('distanceBetween', name=f"{pupil_jnt}_to_{iris_jnt}_dist")
            
            # Connect the world position of the locators to the distanceBetween node
            cmds.connectAttr(f"{iris_loc}.worldPosition[0]", f"{dist_node}.point1")
            cmds.connectAttr(f"{pupil_loc}.worldPosition[0]", f"{dist_node}.point2")

            # Create a multiplyDivide node to normalize the distance
            mult_div_node = cmds.createNode('multiplyDivide', name=pupil_jnt.replace("_jnt", "Scale_multDiv"))
            
            # Get the initial distance to set as the divisor for normalization
            initial_distance = cmds.getAttr(f"{dist_node}.distance")  # Get the starting distance
            cmds.setAttr(f"{mult_div_node}.operation", 2)  # Set to division operation
            cmds.setAttr(f"{mult_div_node}.input2X", initial_distance)  # Normalize by initial distance

            # Connect the distance output from the distanceBetween node to the multiplyDivide node
            cmds.connectAttr(f"{dist_node}.distance", f"{mult_div_node}.input1X")
            
            # Connect the output of the multiplyDivide node to the scaleY of the pupil joint
            cmds.connectAttr(f"{mult_div_node}.outputX", f"{pupil_jnt}.scaleY")
            
            driver_name = self.isolate_name(pupil_drv)

            cmds.pointConstraint(driver_name, pupil_jnt, mo=True)

            cmds.parent(iris_loc, distance_loc_grp)
            cmds.parent(pupil_loc, distance_loc_grp)

        cmds.parent(distance_loc_grp, rig_grp)

        return pupil_scale_jnts, pupil_tip_jnts
        
    def label_joint(self, side, joint_to_be_labelled):
        # Label the joints according to left and right side to help with skinning process
        # Used when any new joints are created
    
        # Determine the side value based on the side argument
        side_value = 1 if side == "L" else 2
    
        # Define label type
        label_type = 18
    
        # Get the label name by stripping prefix and suffix
        label_name = self.strip_prefix_suffix(joint_to_be_labelled)
    
        # Apply the label attributes to the joint
        cmds.setAttr(f"{joint_to_be_labelled}.side", side_value)
        cmds.setAttr(f"{joint_to_be_labelled}.type", label_type)
        cmds.setAttr(f"{joint_to_be_labelled}.otherType", label_name, type="string")
    
    
    def strip_prefix_suffix(self, name):
        # Split the name into components using underscores
        components = name.split('_')

        # Return the middle part (without the prefix and suffix)
        return components[1] if len(components) > 2 else name
    

    def create_up_locator(self, side, eye_aim_jnt, curve, eye_rig_grp):
        # Create the up loc used for the eye aim constraints

        curve_length = cmds.arclen(curve)
        scale_factor = curve_length / 5

        up_loc = cmds.spaceLocator(name=f"{side}_eyeballUpObject_loc")[0]
        cmds.delete(cmds.parentConstraint(eye_aim_jnt, up_loc, mo=False))
        
        move_distance = abs(scale_factor * 4)
        cmds.move(0,move_distance,0, up_loc, relative=True)
        cmds.parent(up_loc, eye_rig_grp)

        cmds.parentConstraint(eye_aim_jnt, up_loc, mo=True)

        cmds.setAttr(f"{up_loc}.visibility", 0)

        return up_loc

    def isolate_name(self, obj):

        full_path = obj
        name = full_path.split('|')[-1]

        return name


    def bind_eye_geo_to_create_skin_cluster(self, side, eye_joints, pupil_jnt, geo, pupil_geo):
        """Creates a skin cluster for the eye geometry using the given joints."""

        skin_cluster_name = f"{side}_eye_sc"
        skin_cluster = cmds.skinCluster(*eye_joints, geo, name=skin_cluster_name, toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)[0]

        pupil_name = f"{side}_pupil_sc"
        pupil_cluster = cmds.skinCluster(pupil_jnt, pupil_geo, name=pupil_name, toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)[0]

        return skin_cluster

    def create_blendshapes(self, side, pupil_crv):
        blendshape_targets = [f"{side}_heart_crv", f"{side}_oval_crv", f"{side}_star_crv", f"{side}_diamond_crv", f"{side}_clover_crv"]
        blendshape_name = f"{side}_pupilShape_bs"
        pupil_shape_bs = cmds.blendShape(*blendshape_targets, pupil_crv, name=blendshape_name)[0]


    def switch_blendshape_target_on_off(self, target):
        sides = ["l", "r"]

        for side in sides:
            blendshape_name = f"{side}_pupilShape_bs"
            target_name = f"{side}_{target}_crv"
            blendshape_targets = [
                f"{side}_heart_crv", f"{side}_oval_crv", 
                f"{side}_star_crv", f"{side}_diamond_crv", 
                f"{side}_clover_crv"
            ]

            if target == "circle":
                for tgt in blendshape_targets:
                    cmds.setAttr(f"{blendshape_name}.{tgt}", 0)
            else:
                for tgt in blendshape_targets:
                    value = 1 if tgt == target_name else 0  # Turn on the selected target, turn off others
                    cmds.setAttr(f"{blendshape_name}.{tgt}", value)

        print(f"Activated: {target} eyes")


    def create_controls(self, side, iris_crv, pupil_crv, aim_jnt, up_obj, pupil_jnt):

        rig_grp = f"{side}_eyeRig_grp"

        pupil_crv_grp = cmds.group(empty=True, n=f"{side}_pupilCrv_grp")
        pupil_center_grp = cmds.group(empty=True, n=f"{side}_pupilCenter_grp")
        cmds.delete(cmds.parentConstraint(pupil_crv, pupil_crv_grp, mo=False))
        cmds.delete(cmds.parentConstraint(aim_jnt, pupil_center_grp, mo=False))
        cmds.parent(pupil_crv, pupil_crv_grp)
        cmds.parent(pupil_crv_grp, pupil_center_grp)

        # Duplicate the curve
        pupil_ctrl = cmds.duplicate(pupil_crv, n=f"{side}_pupil_ctrl")
        cmds.makeIdentity(pupil_ctrl, apply=True, translate=True, rotate=True, scale=True, normal=False)  # Freeze transforms  
        # Rebuild the curve to be cubic (degree=3) while keeping the original shape
        pupil_ctrl = cmds.rebuildCurve(pupil_ctrl[0], degree=3, spans=10, keepRange=0, rebuildType=0)

        pupil_ctrl_grp = cmds.group(empty=True, n=f"{side}_pupil_grp")
        cmds.delete(cmds.parentConstraint(pupil_ctrl, pupil_ctrl_grp, mo=False))

        cmds.parent(pupil_ctrl, pupil_ctrl_grp)

        # Select the shape node of the iris control
        pupil_ctrl_shape = cmds.listRelatives(pupil_ctrl, shapes=True)[0]
        
        # Enable the override and set the color to pink (13 in Maya's color palette)
        cmds.setAttr(f"{pupil_ctrl_shape}.overrideEnabled", 1)
        cmds.setAttr(f"{pupil_ctrl_shape}.overrideColor", 17)


        iris_crv_grp = cmds.group(empty=True, n=f"{side}_irisCrv_grp")
        iris_center_grp = cmds.group(empty=True, n=f"{side}_irisCenter_grp")
        cmds.delete(cmds.parentConstraint(iris_crv, iris_crv_grp, mo=False))
        cmds.delete(cmds.parentConstraint(aim_jnt, iris_center_grp, mo=False))
        cmds.parent(iris_crv, iris_crv_grp)
        cmds.parent(iris_crv_grp, iris_center_grp)


        iris_ctrl = cmds.duplicate(iris_crv, n=f"{side}_iris_ctrl")
        cmds.makeIdentity(iris_ctrl, apply=True, translate=True, rotate=True, scale=True, normal=False)  # Freeze transforms  
        iris_ctrl = cmds.rebuildCurve(iris_ctrl[0], degree=3, spans=10, keepRange=0, rebuildType=0)
        iris_ctrl_shape = cmds.listRelatives(iris_ctrl, shapes=True)[0]
        # Enable the override and set the color to pink (13 in Maya's color palette)
        cmds.setAttr(f"{iris_ctrl_shape}.overrideEnabled", 1)
        cmds.setAttr(f"{iris_ctrl_shape}.overrideColor",9)

        #cmds.delete(iris_ctrl, constructionHistory=True)  # Delete history  
        iris_ctrl_grp = cmds.group(empty=True, n=f"{side}_iris_grp")
        cmds.delete(cmds.parentConstraint(iris_ctrl, iris_ctrl_grp, mo=False))
        cmds.makeIdentity(iris_ctrl, apply=True, translate=True, rotate=True, scale=True, normal=False)  # Freeze transforms  

        cmds.parent(iris_ctrl, iris_ctrl_grp)
        cmds.delete(cmds.parentConstraint(iris_ctrl, pupil_ctrl_grp, mo=False))
        cmds.parent(pupil_ctrl_grp, iris_ctrl)

        # Move the group 0.5 in local Z
        cmds.move(0,0,0.5, iris_ctrl_grp, relative=True)

        cmds.connectAttr(f"{iris_ctrl[0]}.scaleX", f"{iris_crv}.scaleX")
        cmds.connectAttr(f"{iris_ctrl[0]}.scaleY", f"{iris_crv}.scaleY")
        cmds.connectAttr(f"{iris_ctrl[0]}.scaleZ", f"{iris_crv}.scaleZ")

        #cmds.parentConstraint(iris_ctrl, pupil_jnt, mo=True, sr=["x", "y", "z"])
        #cmds.scaleConstraint(iris_ctrl, pupil_jnt, mo=True)

        cmds.aimConstraint(pupil_ctrl, pupil_jnt, aimVector=(0, 0, 1), upVector=(0, 1, 0), worldUpType="object", worldUpObject=up_obj, mo=True)

        cmds.pointConstraint(pupil_ctrl, pupil_crv_grp, mo=True, skip="z")
        cmds.scaleConstraint(pupil_ctrl, pupil_crv_grp, mo=True)


        # Step 1: PlusMinusAverage node to average the iris control scales
        pma_node = cmds.createNode("plusMinusAverage", n=f"{side}_irisScale_avg")
        cmds.setAttr(f"{pma_node}.operation", 3)  # Set to Average mode

        # Connect the scale X and Y of the iris control to the PMA node
        cmds.connectAttr(f"{iris_ctrl[0]}.scaleX", f"{pma_node}.input1D[0]")
        cmds.connectAttr(f"{iris_ctrl[0]}.scaleY", f"{pma_node}.input1D[1]")

        # Step 2: Condition node to check if PMA output > 1
        condition_node = cmds.createNode("condition", n=f"{side}_irisScale_condition")
        cmds.setAttr(f"{condition_node}.operation", 2)  # 2 = Greater than operation
        cmds.setAttr(f"{condition_node}.secondTerm", 1)  # Compare to 1
        cmds.setAttr(f"{condition_node}.colorIfFalseR", 0)  # If PMA <= 1, set to 0
        # Connect PMA output to condition node
        cmds.connectAttr(f"{pma_node}.output1D", f"{condition_node}.firstTerm")
        cmds.connectAttr(f"{pma_node}.output1D", f"{condition_node}.colorIfTrueR")

        # Step 3: Multiply the result of the condition node by -0.1
        mdn_node = cmds.createNode("multiplyDivide", n=f"{side}_irisScale_multiply")
        cmds.setAttr(f"{mdn_node}.input2X", -0.1)  # Multiply by -0.1

        # Connect the condition output to the multiply node
        cmds.connectAttr(f"{condition_node}.outColorR", f"{mdn_node}.input1X")

        # Step 4: Connect the result of the multiply node to translate Z of the pupil joint
        cmds.connectAttr(f"{mdn_node}.outputX", f"{pupil_jnt}.translateZ")  # Connect to translate Z of the pupil joint


        pupil_scale_mdn = cmds.createNode("multiplyDivide", n=f"{side}_pupilScale_mdn")

        for attr in ["X", "Y"]:
            # Step 2: Create a condition node
            condition_node = cmds.createNode("condition", n=f"{side}_pupilScale_condition_{attr.lower()}")
            cmds.setAttr(f"{condition_node}.operation", 0)  # 0 = Equal to operation
            cmds.setAttr(f"{condition_node}.secondTerm", 1)  # Compare to 1
            cmds.setAttr(f"{condition_node}.colorIfTrueR", 1)  # If true, output 1

            # Connect the multiply divide output to the condition node
            cmds.connectAttr(f"{iris_ctrl[0]}.scale{attr}", f"{condition_node}.firstTerm")
            cmds.connectAttr(f"{iris_ctrl[0]}.scale{attr}", f"{condition_node}.colorIfFalseR")

            # Step 3: Connect the output of condition to a plus-minus-average node to subtract 1
            subtract_mdn = cmds.createNode("plusMinusAverage", n=f"{side}_pupilScale_subtract_{attr.lower()}")
            cmds.setAttr(f"{subtract_mdn}.operation", 2)  # Set to subtract
            cmds.setAttr(f"{subtract_mdn}.input1D[1]", 1)  # Subtract 1

            cmds.connectAttr(f"{condition_node}.outColorR", f"{subtract_mdn}.input1D[0]")  # Output of condition -> input of subtract

            # Step 4: Multiply the result by 0.15
            scale_mdn = cmds.createNode("multiplyDivide", n=f"{side}_pupilScale_adjust_{attr.lower()}")
            cmds.setAttr(f"{scale_mdn}.operation", 1)  # Multiply mode
            cmds.setAttr(f"{scale_mdn}.input2{attr}", 0.05)  # Multiply by 0.15

            cmds.connectAttr(f"{subtract_mdn}.output1D", f"{scale_mdn}.input1{attr}")  # Connect result of subtraction to multiply

            # Step 5: Add 1 back to the scaled result
            add_mdn = cmds.createNode("plusMinusAverage", n=f"{side}_pupilScale_add_{attr.lower()}")
            cmds.setAttr(f"{add_mdn}.operation", 1)  # Add mode
            cmds.setAttr(f"{add_mdn}.input1D[1]", 1)  # Add 1

            cmds.connectAttr(f"{scale_mdn}.output{attr}", f"{add_mdn}.input1D[0]")  # Connect multiplied value to add

            # Step 6: Connect the final result to the joint scale
            cmds.connectAttr(f"{add_mdn}.output1D", f"{pupil_jnt}.scale{attr}")  # Final scale to joint

        # pupil_scale_mdn = cmds.createNode("multiplyDivide", n=f"{side}_pupilScale_mdn")

        # for attr in ["X", "Y", "Z"]:
        #     cmds.setAttr(f"{pupil_scale_mdn}.input2{attr}", 0.9)  # Corrected attribute name
        #     cmds.connectAttr(f"{iris_ctrl[0]}.scale{attr}", f"{pupil_scale_mdn}.input1{attr}")
        #     cmds.connectAttr(f"{pupil_scale_mdn}.output{attr}", f"{pupil_jnt}.scale{attr}")

        cmds.parent(iris_center_grp, rig_grp)
        cmds.parent(pupil_center_grp, rig_grp)
        cmds.parent(iris_ctrl_grp, rig_grp)
        cmds.aimConstraint(iris_ctrl, iris_center_grp, aimVector=(0, 0, 1), upVector=(0, 1, 0), worldUpType="object", worldUpObject=up_obj, mo=True)
        cmds.aimConstraint(iris_ctrl, pupil_center_grp, aimVector=(0, 0, 1), upVector=(0, 1, 0), worldUpType="object", worldUpObject=up_obj, mo=True)

        cmds.setAttr(f"{iris_center_grp}.visibility", 0)
        cmds.setAttr(f"{pupil_center_grp}.visibility", 0)

    def clean_up_outliner(self, side, locs):
        rig_grp = f"{side}_eyeRig_grp"

        for loc in locs:
            cmds.setAttr(f"{loc}.visibility", 0)
            cmds.parent(loc, rig_grp)

    def assign_influence_to_closest_joint(self, vertices, joints, skin_cluster, iris_flag, value):
        """Assigns 100% influence to the closest joint for each vertex in the loop."""
        for vertex in vertices:
            closest_joint = None
            min_distance = float('inf')  # Start with an infinitely large distance
            
            # Get the position of the vertex
            vertex_position = om.MVector(*cmds.xform(vertex, q=True, t=True, ws=True))
            
            # Check distance to each joint
            for jnt in joints:
                jnt_position = om.MVector(*cmds.xform(jnt, q=True, t=True, ws=True))
                
                distance = (vertex_position - jnt_position).length()  # Calculate the distance to the joint
                
                if distance < min_distance:
                    min_distance = distance
                    closest_joint = jnt
                    if iris_flag:
                        closest_joint = closest_joint.replace("Tip", "")
            
            # Assign 100% influence to the closest joint
            cmds.skinPercent(skin_cluster, vertex, transformValue=(closest_joint, value))

    def skin_eye_verts(self, side, face_list, joints_list, iris_flag=False):
        """Skins the donut mesh based on the provided faces, center, and joints."""

        skin_cluster = f"{side}_eye_sc"

        position = cmds.xform(f"{side}_eyePupil_loc", q=True, t=True, ws=True)
        center = om.MVector(position[0], position[1], position[2])

        # Get vertices from the faces
        all_vertices = cmds.polyListComponentConversion(face_list, toVertex=True)
        all_vertices = cmds.ls(all_vertices, flatten=True)  # Flatten the component list

        # Group vertices by their distance to the center (form edge loops)
        min_weight = 0.2
        
        # Group vertices by their distance to the center (forming edge loops)
        distance_groups = {}
        for vertex in all_vertices:
            vertex_position = om.MVector(*cmds.xform(vertex, q=True, t=True, ws=True))
            # Get the distance from the actual center (not origin)
            distance = (vertex_position - center).length()  # Measure distance to the center position
        
            # Group vertices by distance (which corresponds to the edge loop)
            if distance not in distance_groups:
                distance_groups[distance] = []
            distance_groups[distance].append(vertex)
        
        # Sort distances for ordered processing (from inner to outer loops)
        sorted_distances = sorted(distance_groups.keys())
        
        if iris_flag:
            num_groups = len(sorted_distances)
            # First quarter: full influence.
            quarter_size = num_groups // 4
            if quarter_size < 1:
                quarter_size = 1
        
            # The fade zone will run from index `quarter_size` to the final index.
            fade_range = (num_groups - 1) - quarter_size  # Ensure this is at least 1 for proper division
        
            for i, distance in enumerate(sorted_distances):
                if i < quarter_size:
                    # First quarter: assign full weight (1.0)
                    value = 1.0
                else:
                    # Fade from 1.0 to min_weight using cosine interpolation.
                    # t goes from 0 (start of fade) to 1 (last group)
                    t = float(i - quarter_size) / fade_range
                    # Standard cosine interpolation gives a value from 1.0 down to 0.0:
                    cosine_val = 0.5 * (math.cos(math.pi * t) + 1.0)
                    # Remap that range so that the final value is min_weight rather than 0.0.
                    value = min_weight + (1.0 - min_weight) * cosine_val
                self.assign_influence_to_closest_joint(distance_groups[distance], joints_list, skin_cluster, iris_flag, value=value)

        else:
            for distance, vertices in distance_groups.items():
                self.assign_influence_to_closest_joint(vertices, joints_list, skin_cluster, iris_flag, value=1)

    def assign_influence_to_eye_aim(self, side, faces):
        """Assigns all iris vertices to the eye aim joint."""
        aim_jnt = f"{side}_eyeAim_jnt"
        skin_cluster = f"{side}_eye_sc"

        all_vertices = cmds.polyListComponentConversion(faces, toVertex=True)
        all_vertices = cmds.ls(all_vertices, flatten=True)  # Flatten the component list

        for vertex in all_vertices:
            cmds.skinPercent(skin_cluster, vertex, transformValue=(aim_jnt, 1.0))




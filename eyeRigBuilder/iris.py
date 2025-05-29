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



            

# iris_jnt_edges = ['L_eye_geo.e[1057]', 'L_eye_geo.e[1060]', 'L_eye_geo.e[1062]', 'L_eye_geo.e[1064]', 'L_eye_geo.e[1066]', 'L_eye_geo.e[1068]', 'L_eye_geo.e[1070]', 'L_eye_geo.e[1072]', 'L_eye_geo.e[1074]', 'L_eye_geo.e[1076]', 'L_eye_geo.e[1078]', 'L_eye_geo.e[1080]', 'L_eye_geo.e[1082]', 'L_eye_geo.e[1084]', 'L_eye_geo.e[1086]', 'L_eye_geo.e[1088]', 'L_eye_geo.e[1090]', 'L_eye_geo.e[1092]', 'L_eye_geo.e[1094]', 'L_eye_geo.e[1096]', 'L_eye_geo.e[1098]', 'L_eye_geo.e[1100]', 'L_eye_geo.e[1102]', 'L_eye_geo.e[1103]']
# pupil_jnt_edges = ['L_eye_geo.e[1273]', 'L_eye_geo.e[1278]', 'L_eye_geo.e[1282]', 'L_eye_geo.e[1286]', 'L_eye_geo.e[1290]', 'L_eye_geo.e[1294]', 'L_eye_geo.e[1298]', 'L_eye_geo.e[1302]', 'L_eye_geo.e[1306]', 'L_eye_geo.e[1310]', 'L_eye_geo.e[1314]', 'L_eye_geo.e[1318]', 'L_eye_geo.e[1322]', 'L_eye_geo.e[1326]', 'L_eye_geo.e[1330]', 'L_eye_geo.e[1334]', 'L_eye_geo.e[1338]', 'L_eye_geo.e[1342]', 'L_eye_geo.e[1346]', 'L_eye_geo.e[1350]', 'L_eye_geo.e[1354]', 'L_eye_geo.e[1358]', 'L_eye_geo.e[1362]', 'L_eye_geo.e[1366]']


# pupil_faces = ['L_eye_geo.f[576]', 'L_eye_geo.f[577]', 'L_eye_geo.f[578]', 'L_eye_geo.f[579]', 'L_eye_geo.f[580]', 'L_eye_geo.f[581]', 'L_eye_geo.f[582]', 'L_eye_geo.f[583]', 'L_eye_geo.f[584]', 'L_eye_geo.f[585]', 'L_eye_geo.f[586]', 'L_eye_geo.f[587]', 'L_eye_geo.f[588]', 'L_eye_geo.f[589]', 'L_eye_geo.f[590]', 'L_eye_geo.f[591]', 'L_eye_geo.f[592]', 'L_eye_geo.f[593]', 'L_eye_geo.f[594]', 'L_eye_geo.f[595]', 'L_eye_geo.f[596]', 'L_eye_geo.f[597]', 'L_eye_geo.f[598]', 'L_eye_geo.f[599]', 'L_eye_geo.f[600]', 'L_eye_geo.f[601]', 'L_eye_geo.f[602]', 'L_eye_geo.f[603]', 'L_eye_geo.f[604]', 'L_eye_geo.f[605]', 'L_eye_geo.f[606]', 'L_eye_geo.f[607]', 'L_eye_geo.f[608]', 'L_eye_geo.f[609]', 'L_eye_geo.f[610]', 'L_eye_geo.f[611]', 'L_eye_geo.f[612]', 'L_eye_geo.f[613]', 'L_eye_geo.f[614]', 'L_eye_geo.f[615]', 'L_eye_geo.f[616]', 'L_eye_geo.f[617]', 'L_eye_geo.f[618]', 'L_eye_geo.f[619]', 'L_eye_geo.f[620]', 'L_eye_geo.f[621]', 'L_eye_geo.f[622]', 'L_eye_geo.f[623]', 'L_eye_geo.f[624]', 'L_eye_geo.f[625]', 'L_eye_geo.f[626]', 'L_eye_geo.f[627]', 'L_eye_geo.f[628]', 'L_eye_geo.f[629]', 'L_eye_geo.f[630]', 'L_eye_geo.f[631]', 'L_eye_geo.f[632]', 'L_eye_geo.f[633]', 'L_eye_geo.f[634]', 'L_eye_geo.f[635]', 'L_eye_geo.f[636]', 'L_eye_geo.f[637]', 'L_eye_geo.f[638]', 'L_eye_geo.f[639]', 'L_eye_geo.f[640]', 'L_eye_geo.f[641]', 'L_eye_geo.f[642]', 'L_eye_geo.f[643]', 'L_eye_geo.f[644]', 'L_eye_geo.f[645]', 'L_eye_geo.f[646]', 'L_eye_geo.f[647]', 'L_eye_geo.f[648]', 'L_eye_geo.f[649]', 'L_eye_geo.f[650]', 'L_eye_geo.f[651]', 'L_eye_geo.f[652]', 'L_eye_geo.f[653]', 'L_eye_geo.f[654]', 'L_eye_geo.f[655]', 'L_eye_geo.f[656]', 'L_eye_geo.f[657]', 'L_eye_geo.f[658]', 'L_eye_geo.f[659]', 'L_eye_geo.f[660]', 'L_eye_geo.f[661]', 'L_eye_geo.f[662]', 'L_eye_geo.f[663]', 'L_eye_geo.f[664]', 'L_eye_geo.f[665]', 'L_eye_geo.f[666]', 'L_eye_geo.f[667]', 'L_eye_geo.f[668]', 'L_eye_geo.f[669]', 'L_eye_geo.f[670]', 'L_eye_geo.f[671]', 'L_eye_geo.f[672]', 'L_eye_geo.f[673]', 'L_eye_geo.f[674]', 'L_eye_geo.f[675]', 'L_eye_geo.f[676]', 'L_eye_geo.f[677]', 'L_eye_geo.f[678]', 'L_eye_geo.f[679]', 'L_eye_geo.f[680]', 'L_eye_geo.f[681]', 'L_eye_geo.f[682]', 'L_eye_geo.f[683]', 'L_eye_geo.f[684]', 'L_eye_geo.f[685]', 'L_eye_geo.f[686]', 'L_eye_geo.f[687]', 'L_eye_geo.f[688]', 'L_eye_geo.f[689]', 'L_eye_geo.f[690]', 'L_eye_geo.f[691]', 'L_eye_geo.f[692]', 'L_eye_geo.f[693]', 'L_eye_geo.f[694]', 'L_eye_geo.f[695]', 'L_eye_geo.f[696]', 'L_eye_geo.f[697]', 'L_eye_geo.f[698]', 'L_eye_geo.f[699]', 'L_eye_geo.f[700]', 'L_eye_geo.f[701]', 'L_eye_geo.f[702]', 'L_eye_geo.f[703]', 'L_eye_geo.f[704]', 'L_eye_geo.f[705]', 'L_eye_geo.f[706]', 'L_eye_geo.f[707]', 'L_eye_geo.f[708]', 'L_eye_geo.f[709]', 'L_eye_geo.f[710]', 'L_eye_geo.f[711]', 'L_eye_geo.f[712]', 'L_eye_geo.f[713]', 'L_eye_geo.f[714]', 'L_eye_geo.f[715]', 'L_eye_geo.f[716]', 'L_eye_geo.f[717]', 'L_eye_geo.f[718]', 'L_eye_geo.f[719]', 'L_eye_geo.f[720]', 'L_eye_geo.f[721]', 'L_eye_geo.f[722]', 'L_eye_geo.f[723]', 'L_eye_geo.f[724]', 'L_eye_geo.f[725]', 'L_eye_geo.f[726]', 'L_eye_geo.f[727]', 'L_eye_geo.f[728]', 'L_eye_geo.f[729]', 'L_eye_geo.f[730]', 'L_eye_geo.f[731]', 'L_eye_geo.f[732]', 'L_eye_geo.f[733]', 'L_eye_geo.f[734]', 'L_eye_geo.f[735]', 'L_eye_geo.f[736]', 'L_eye_geo.f[737]', 'L_eye_geo.f[738]', 'L_eye_geo.f[739]', 'L_eye_geo.f[740]', 'L_eye_geo.f[741]', 'L_eye_geo.f[742]', 'L_eye_geo.f[743]']
# iris_faces = ['L_eye_geo.f[0]', 'L_eye_geo.f[1]', 'L_eye_geo.f[2]', 'L_eye_geo.f[3]', 'L_eye_geo.f[4]', 'L_eye_geo.f[5]', 'L_eye_geo.f[6]', 'L_eye_geo.f[7]', 'L_eye_geo.f[8]', 'L_eye_geo.f[9]', 'L_eye_geo.f[10]', 'L_eye_geo.f[11]', 'L_eye_geo.f[12]', 'L_eye_geo.f[13]', 'L_eye_geo.f[14]', 'L_eye_geo.f[15]', 'L_eye_geo.f[16]', 'L_eye_geo.f[17]', 'L_eye_geo.f[18]', 'L_eye_geo.f[19]', 'L_eye_geo.f[20]', 'L_eye_geo.f[21]', 'L_eye_geo.f[22]', 'L_eye_geo.f[23]', 'L_eye_geo.f[24]', 'L_eye_geo.f[25]', 'L_eye_geo.f[26]', 'L_eye_geo.f[27]', 'L_eye_geo.f[28]', 'L_eye_geo.f[29]', 'L_eye_geo.f[30]', 'L_eye_geo.f[31]', 'L_eye_geo.f[32]', 'L_eye_geo.f[33]', 'L_eye_geo.f[34]', 'L_eye_geo.f[35]', 'L_eye_geo.f[36]', 'L_eye_geo.f[37]', 'L_eye_geo.f[38]', 'L_eye_geo.f[39]', 'L_eye_geo.f[40]', 'L_eye_geo.f[41]', 'L_eye_geo.f[42]', 'L_eye_geo.f[43]', 'L_eye_geo.f[44]', 'L_eye_geo.f[45]', 'L_eye_geo.f[46]', 'L_eye_geo.f[47]', 'L_eye_geo.f[48]', 'L_eye_geo.f[49]', 'L_eye_geo.f[50]', 'L_eye_geo.f[51]', 'L_eye_geo.f[52]', 'L_eye_geo.f[53]', 'L_eye_geo.f[54]', 'L_eye_geo.f[55]', 'L_eye_geo.f[56]', 'L_eye_geo.f[57]', 'L_eye_geo.f[58]', 'L_eye_geo.f[59]', 'L_eye_geo.f[60]', 'L_eye_geo.f[61]', 'L_eye_geo.f[62]', 'L_eye_geo.f[63]', 'L_eye_geo.f[64]', 'L_eye_geo.f[65]', 'L_eye_geo.f[66]', 'L_eye_geo.f[67]', 'L_eye_geo.f[68]', 'L_eye_geo.f[69]', 'L_eye_geo.f[70]', 'L_eye_geo.f[71]', 'L_eye_geo.f[72]', 'L_eye_geo.f[73]', 'L_eye_geo.f[74]', 'L_eye_geo.f[75]', 'L_eye_geo.f[76]', 'L_eye_geo.f[77]', 'L_eye_geo.f[78]', 'L_eye_geo.f[79]', 'L_eye_geo.f[80]', 'L_eye_geo.f[81]', 'L_eye_geo.f[82]', 'L_eye_geo.f[83]', 'L_eye_geo.f[84]', 'L_eye_geo.f[85]', 'L_eye_geo.f[86]', 'L_eye_geo.f[87]', 'L_eye_geo.f[88]', 'L_eye_geo.f[89]', 'L_eye_geo.f[90]', 'L_eye_geo.f[91]', 'L_eye_geo.f[92]', 'L_eye_geo.f[93]', 'L_eye_geo.f[94]', 'L_eye_geo.f[95]', 'L_eye_geo.f[96]', 'L_eye_geo.f[97]', 'L_eye_geo.f[98]', 'L_eye_geo.f[99]', 'L_eye_geo.f[100]', 'L_eye_geo.f[101]', 'L_eye_geo.f[102]', 'L_eye_geo.f[103]', 'L_eye_geo.f[104]', 'L_eye_geo.f[105]', 'L_eye_geo.f[106]', 'L_eye_geo.f[107]', 'L_eye_geo.f[108]', 'L_eye_geo.f[109]', 'L_eye_geo.f[110]', 'L_eye_geo.f[111]', 'L_eye_geo.f[112]', 'L_eye_geo.f[113]', 'L_eye_geo.f[114]', 'L_eye_geo.f[115]', 'L_eye_geo.f[116]', 'L_eye_geo.f[117]', 'L_eye_geo.f[118]', 'L_eye_geo.f[119]', 'L_eye_geo.f[120]', 'L_eye_geo.f[121]', 'L_eye_geo.f[122]', 'L_eye_geo.f[123]', 'L_eye_geo.f[124]', 'L_eye_geo.f[125]', 'L_eye_geo.f[126]', 'L_eye_geo.f[127]', 'L_eye_geo.f[128]', 'L_eye_geo.f[129]', 'L_eye_geo.f[130]', 'L_eye_geo.f[131]', 'L_eye_geo.f[132]', 'L_eye_geo.f[133]', 'L_eye_geo.f[134]', 'L_eye_geo.f[135]', 'L_eye_geo.f[136]', 'L_eye_geo.f[137]', 'L_eye_geo.f[138]', 'L_eye_geo.f[139]', 'L_eye_geo.f[140]', 'L_eye_geo.f[141]', 'L_eye_geo.f[142]', 'L_eye_geo.f[143]', 'L_eye_geo.f[144]', 'L_eye_geo.f[145]', 'L_eye_geo.f[146]', 'L_eye_geo.f[147]', 'L_eye_geo.f[148]', 'L_eye_geo.f[149]', 'L_eye_geo.f[150]', 'L_eye_geo.f[151]', 'L_eye_geo.f[152]', 'L_eye_geo.f[153]', 'L_eye_geo.f[154]', 'L_eye_geo.f[155]', 'L_eye_geo.f[156]', 'L_eye_geo.f[157]', 'L_eye_geo.f[158]', 'L_eye_geo.f[159]', 'L_eye_geo.f[160]', 'L_eye_geo.f[161]', 'L_eye_geo.f[162]', 'L_eye_geo.f[163]', 'L_eye_geo.f[164]', 'L_eye_geo.f[165]', 'L_eye_geo.f[166]', 'L_eye_geo.f[167]', 'L_eye_geo.f[168]', 'L_eye_geo.f[169]', 'L_eye_geo.f[170]', 'L_eye_geo.f[171]', 'L_eye_geo.f[172]', 'L_eye_geo.f[173]', 'L_eye_geo.f[174]', 'L_eye_geo.f[175]', 'L_eye_geo.f[176]', 'L_eye_geo.f[177]', 'L_eye_geo.f[178]', 'L_eye_geo.f[179]', 'L_eye_geo.f[180]', 'L_eye_geo.f[181]', 'L_eye_geo.f[182]', 'L_eye_geo.f[183]', 'L_eye_geo.f[184]', 'L_eye_geo.f[185]', 'L_eye_geo.f[186]', 'L_eye_geo.f[187]', 'L_eye_geo.f[188]', 'L_eye_geo.f[189]', 'L_eye_geo.f[190]', 'L_eye_geo.f[191]', 'L_eye_geo.f[192]', 'L_eye_geo.f[193]', 'L_eye_geo.f[194]', 'L_eye_geo.f[195]', 'L_eye_geo.f[196]', 'L_eye_geo.f[197]', 'L_eye_geo.f[198]', 'L_eye_geo.f[199]', 'L_eye_geo.f[200]', 'L_eye_geo.f[201]', 'L_eye_geo.f[202]', 'L_eye_geo.f[203]', 'L_eye_geo.f[204]', 'L_eye_geo.f[205]', 'L_eye_geo.f[206]', 'L_eye_geo.f[207]', 'L_eye_geo.f[208]', 'L_eye_geo.f[209]', 'L_eye_geo.f[210]', 'L_eye_geo.f[211]', 'L_eye_geo.f[212]', 'L_eye_geo.f[213]', 'L_eye_geo.f[214]', 'L_eye_geo.f[215]', 'L_eye_geo.f[216]', 'L_eye_geo.f[217]', 'L_eye_geo.f[218]', 'L_eye_geo.f[219]', 'L_eye_geo.f[220]', 'L_eye_geo.f[221]', 'L_eye_geo.f[222]', 'L_eye_geo.f[223]', 'L_eye_geo.f[224]', 'L_eye_geo.f[225]', 'L_eye_geo.f[226]', 'L_eye_geo.f[227]', 'L_eye_geo.f[228]', 'L_eye_geo.f[229]', 'L_eye_geo.f[230]', 'L_eye_geo.f[231]', 'L_eye_geo.f[232]', 'L_eye_geo.f[233]', 'L_eye_geo.f[234]', 'L_eye_geo.f[235]', 'L_eye_geo.f[236]', 'L_eye_geo.f[237]', 'L_eye_geo.f[238]', 'L_eye_geo.f[239]', 'L_eye_geo.f[240]', 'L_eye_geo.f[241]', 'L_eye_geo.f[242]', 'L_eye_geo.f[243]', 'L_eye_geo.f[244]', 'L_eye_geo.f[245]', 'L_eye_geo.f[246]', 'L_eye_geo.f[247]', 'L_eye_geo.f[248]', 'L_eye_geo.f[249]', 'L_eye_geo.f[250]', 'L_eye_geo.f[251]', 'L_eye_geo.f[252]', 'L_eye_geo.f[253]', 'L_eye_geo.f[254]', 'L_eye_geo.f[255]', 'L_eye_geo.f[256]', 'L_eye_geo.f[257]', 'L_eye_geo.f[258]', 'L_eye_geo.f[259]', 'L_eye_geo.f[260]', 'L_eye_geo.f[261]', 'L_eye_geo.f[262]', 'L_eye_geo.f[263]', 'L_eye_geo.f[264]', 'L_eye_geo.f[265]', 'L_eye_geo.f[266]', 'L_eye_geo.f[267]', 'L_eye_geo.f[268]', 'L_eye_geo.f[269]', 'L_eye_geo.f[270]', 'L_eye_geo.f[271]', 'L_eye_geo.f[272]', 'L_eye_geo.f[273]', 'L_eye_geo.f[274]', 'L_eye_geo.f[275]', 'L_eye_geo.f[276]', 'L_eye_geo.f[277]', 'L_eye_geo.f[278]', 'L_eye_geo.f[279]', 'L_eye_geo.f[280]', 'L_eye_geo.f[281]', 'L_eye_geo.f[282]', 'L_eye_geo.f[283]', 'L_eye_geo.f[284]', 'L_eye_geo.f[285]', 'L_eye_geo.f[286]', 'L_eye_geo.f[287]', 'L_eye_geo.f[288]', 'L_eye_geo.f[289]', 'L_eye_geo.f[290]', 'L_eye_geo.f[291]', 'L_eye_geo.f[292]', 'L_eye_geo.f[293]', 'L_eye_geo.f[294]', 'L_eye_geo.f[295]', 'L_eye_geo.f[296]', 'L_eye_geo.f[297]', 'L_eye_geo.f[298]', 'L_eye_geo.f[299]', 'L_eye_geo.f[300]', 'L_eye_geo.f[301]', 'L_eye_geo.f[302]', 'L_eye_geo.f[303]', 'L_eye_geo.f[304]', 'L_eye_geo.f[305]', 'L_eye_geo.f[306]', 'L_eye_geo.f[307]', 'L_eye_geo.f[308]', 'L_eye_geo.f[309]', 'L_eye_geo.f[310]', 'L_eye_geo.f[311]', 'L_eye_geo.f[312]', 'L_eye_geo.f[313]', 'L_eye_geo.f[314]', 'L_eye_geo.f[315]', 'L_eye_geo.f[316]', 'L_eye_geo.f[317]', 'L_eye_geo.f[318]', 'L_eye_geo.f[319]', 'L_eye_geo.f[320]', 'L_eye_geo.f[321]', 'L_eye_geo.f[322]', 'L_eye_geo.f[323]', 'L_eye_geo.f[324]', 'L_eye_geo.f[325]', 'L_eye_geo.f[326]', 'L_eye_geo.f[327]', 'L_eye_geo.f[328]', 'L_eye_geo.f[329]', 'L_eye_geo.f[330]', 'L_eye_geo.f[331]', 'L_eye_geo.f[332]', 'L_eye_geo.f[333]', 'L_eye_geo.f[334]', 'L_eye_geo.f[335]', 'L_eye_geo.f[336]', 'L_eye_geo.f[337]', 'L_eye_geo.f[338]', 'L_eye_geo.f[339]', 'L_eye_geo.f[340]', 'L_eye_geo.f[341]', 'L_eye_geo.f[342]', 'L_eye_geo.f[343]', 'L_eye_geo.f[344]', 'L_eye_geo.f[345]', 'L_eye_geo.f[346]', 'L_eye_geo.f[347]', 'L_eye_geo.f[348]', 'L_eye_geo.f[349]', 'L_eye_geo.f[350]', 'L_eye_geo.f[351]', 'L_eye_geo.f[352]', 'L_eye_geo.f[353]', 'L_eye_geo.f[354]', 'L_eye_geo.f[355]', 'L_eye_geo.f[356]', 'L_eye_geo.f[357]', 'L_eye_geo.f[358]', 'L_eye_geo.f[359]', 'L_eye_geo.f[360]', 'L_eye_geo.f[361]', 'L_eye_geo.f[362]', 'L_eye_geo.f[363]', 'L_eye_geo.f[364]', 'L_eye_geo.f[365]', 'L_eye_geo.f[366]', 'L_eye_geo.f[367]', 'L_eye_geo.f[368]', 'L_eye_geo.f[369]', 'L_eye_geo.f[370]', 'L_eye_geo.f[371]', 'L_eye_geo.f[372]', 'L_eye_geo.f[373]', 'L_eye_geo.f[374]', 'L_eye_geo.f[375]', 'L_eye_geo.f[376]', 'L_eye_geo.f[377]', 'L_eye_geo.f[378]', 'L_eye_geo.f[379]', 'L_eye_geo.f[380]', 'L_eye_geo.f[381]', 'L_eye_geo.f[382]', 'L_eye_geo.f[383]', 'L_eye_geo.f[384]', 'L_eye_geo.f[385]', 'L_eye_geo.f[386]', 'L_eye_geo.f[387]', 'L_eye_geo.f[388]', 'L_eye_geo.f[389]', 'L_eye_geo.f[390]', 'L_eye_geo.f[391]', 'L_eye_geo.f[392]', 'L_eye_geo.f[393]', 'L_eye_geo.f[394]', 'L_eye_geo.f[395]', 'L_eye_geo.f[396]', 'L_eye_geo.f[397]', 'L_eye_geo.f[398]', 'L_eye_geo.f[399]', 'L_eye_geo.f[400]', 'L_eye_geo.f[401]', 'L_eye_geo.f[402]', 'L_eye_geo.f[403]', 'L_eye_geo.f[404]', 'L_eye_geo.f[405]', 'L_eye_geo.f[406]', 'L_eye_geo.f[407]', 'L_eye_geo.f[408]', 'L_eye_geo.f[409]', 'L_eye_geo.f[410]', 'L_eye_geo.f[411]', 'L_eye_geo.f[412]', 'L_eye_geo.f[413]', 'L_eye_geo.f[414]', 'L_eye_geo.f[415]', 'L_eye_geo.f[416]', 'L_eye_geo.f[417]', 'L_eye_geo.f[418]', 'L_eye_geo.f[419]', 'L_eye_geo.f[420]', 'L_eye_geo.f[421]', 'L_eye_geo.f[422]', 'L_eye_geo.f[423]', 'L_eye_geo.f[424]', 'L_eye_geo.f[425]', 'L_eye_geo.f[426]', 'L_eye_geo.f[427]', 'L_eye_geo.f[428]', 'L_eye_geo.f[429]', 'L_eye_geo.f[430]', 'L_eye_geo.f[431]', 'L_eye_geo.f[432]', 'L_eye_geo.f[433]', 'L_eye_geo.f[434]', 'L_eye_geo.f[435]', 'L_eye_geo.f[436]', 'L_eye_geo.f[437]', 'L_eye_geo.f[438]', 'L_eye_geo.f[439]', 'L_eye_geo.f[440]', 'L_eye_geo.f[441]', 'L_eye_geo.f[442]', 'L_eye_geo.f[443]', 'L_eye_geo.f[444]', 'L_eye_geo.f[445]', 'L_eye_geo.f[446]', 'L_eye_geo.f[447]', 'L_eye_geo.f[448]', 'L_eye_geo.f[449]', 'L_eye_geo.f[450]', 'L_eye_geo.f[451]', 'L_eye_geo.f[452]', 'L_eye_geo.f[453]', 'L_eye_geo.f[454]', 'L_eye_geo.f[455]', 'L_eye_geo.f[456]', 'L_eye_geo.f[457]', 'L_eye_geo.f[458]', 'L_eye_geo.f[459]', 'L_eye_geo.f[460]', 'L_eye_geo.f[461]', 'L_eye_geo.f[462]', 'L_eye_geo.f[463]', 'L_eye_geo.f[464]', 'L_eye_geo.f[465]', 'L_eye_geo.f[466]', 'L_eye_geo.f[467]', 'L_eye_geo.f[468]', 'L_eye_geo.f[469]', 'L_eye_geo.f[470]', 'L_eye_geo.f[471]', 'L_eye_geo.f[472]', 'L_eye_geo.f[473]', 'L_eye_geo.f[474]', 'L_eye_geo.f[475]', 'L_eye_geo.f[476]', 'L_eye_geo.f[477]', 'L_eye_geo.f[478]', 'L_eye_geo.f[479]', 'L_eye_geo.f[480]', 'L_eye_geo.f[481]', 'L_eye_geo.f[482]', 'L_eye_geo.f[483]', 'L_eye_geo.f[484]', 'L_eye_geo.f[485]', 'L_eye_geo.f[486]', 'L_eye_geo.f[487]', 'L_eye_geo.f[488]', 'L_eye_geo.f[489]', 'L_eye_geo.f[490]', 'L_eye_geo.f[491]', 'L_eye_geo.f[492]', 'L_eye_geo.f[493]', 'L_eye_geo.f[494]', 'L_eye_geo.f[495]', 'L_eye_geo.f[496]', 'L_eye_geo.f[497]', 'L_eye_geo.f[498]', 'L_eye_geo.f[499]', 'L_eye_geo.f[500]', 'L_eye_geo.f[501]', 'L_eye_geo.f[502]', 'L_eye_geo.f[503]', 'L_eye_geo.f[504]', 'L_eye_geo.f[505]', 'L_eye_geo.f[506]', 'L_eye_geo.f[507]', 'L_eye_geo.f[508]', 'L_eye_geo.f[509]', 'L_eye_geo.f[510]', 'L_eye_geo.f[511]', 'L_eye_geo.f[512]', 'L_eye_geo.f[513]', 'L_eye_geo.f[514]', 'L_eye_geo.f[515]', 'L_eye_geo.f[516]', 'L_eye_geo.f[517]', 'L_eye_geo.f[518]', 'L_eye_geo.f[519]', 'L_eye_geo.f[520]', 'L_eye_geo.f[521]', 'L_eye_geo.f[522]', 'L_eye_geo.f[523]', 'L_eye_geo.f[524]', 'L_eye_geo.f[525]', 'L_eye_geo.f[526]', 'L_eye_geo.f[527]', 'L_eye_geo.f[528]', 'L_eye_geo.f[529]', 'L_eye_geo.f[530]', 'L_eye_geo.f[531]', 'L_eye_geo.f[532]', 'L_eye_geo.f[533]', 'L_eye_geo.f[534]', 'L_eye_geo.f[535]', 'L_eye_geo.f[536]', 'L_eye_geo.f[537]', 'L_eye_geo.f[538]', 'L_eye_geo.f[539]', 'L_eye_geo.f[540]', 'L_eye_geo.f[541]', 'L_eye_geo.f[542]', 'L_eye_geo.f[543]', 'L_eye_geo.f[544]', 'L_eye_geo.f[545]', 'L_eye_geo.f[546]', 'L_eye_geo.f[547]', 'L_eye_geo.f[548]', 'L_eye_geo.f[549]', 'L_eye_geo.f[550]', 'L_eye_geo.f[551]']
# pupil_joints = [f"L_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]  # Pupil joints
# iris_joints = [f"L_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]

# r_pupil_edges = [edge.replace("L_eye_geo", "R_eye_geo") for edge in pupil_edges]
# r_iris_edges  = [edge.replace("L_eye_geo", "R_eye_geo") for edge in iris_edges]
# r_pupil_joints = [f"R_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]  # Pupil joints
# r_iris_joints = [f"R_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]




# eye_rig = EyeballRig(iris_jnt_edges, pupil_jnt_edges)
# eye_rig.assign_influence_to_eye_aim("L", iris_faces)
# eye_rig.assign_influence_to_eye_aim("L", pupil_faces)
# eye_rig.skin_eye_verts("L", iris_faces, iris_joints, iris_flag=True)
# eye_rig.skin_eye_verts("L", pupil_faces, pupil_joints, iris_flag=False)

# def assign_influence_to_closest_joint(vertices, joints, skin_cluster, iris_flag, value):
#     """Assigns 100% influence to the closest joint for each vertex in the loop."""
#     for vertex in vertices:
#         closest_joint = None
#         min_distance = float('inf')  # Start with an infinitely large distance
        
#         # Get the position of the vertex
#         vertex_position = om.MVector(*cmds.xform(vertex, q=True, t=True, ws=True))
        
#         # Check distance to each joint
#         for jnt in joints:
#             jnt_position = om.MVector(*cmds.xform(jnt, q=True, t=True, ws=True))
            
#             distance = (vertex_position - jnt_position).length()  # Calculate the distance to the joint
            
#             if distance < min_distance:
#                 min_distance = distance
#                 closest_joint = jnt
#                 if iris_flag:
#                     closest_joint = closest_joint.replace("Tip", "")
        
#         # Assign 100% influence to the closest joint
#         cmds.skinPercent(skin_cluster, vertex, transformValue=(closest_joint, value))

# def skin_eye_verts(side, face_list, joints_list, iris_flag=False):
#     """Skins the donut mesh based on the provided faces, center, and joints."""

#     skin_cluster = f"{side}_eye_sc"

#     position = cmds.xform(f"{side}_eyePupil_loc", q=True, t=True, ws=True)
#     center = om.MVector(position[0], position[1], position[2])

#     # Get vertices from the faces
#     all_vertices = cmds.polyListComponentConversion(face_list, toVertex=True)
#     all_vertices = cmds.ls(all_vertices, flatten=True)  # Flatten the component list

#     # Group vertices by their distance to the center (form edge loops)
#     min_weight = 0.2
    
#     # Group vertices by their distance to the center (forming edge loops)
#     distance_groups = {}
#     for vertex in all_vertices:
#         vertex_position = om.MVector(*cmds.xform(vertex, q=True, t=True, ws=True))
#         # Get the distance from the actual center (not origin)
#         distance = (vertex_position - center).length()  # Measure distance to the center position
    
#         # Group vertices by distance (which corresponds to the edge loop)
#         if distance not in distance_groups:
#             distance_groups[distance] = []
#         distance_groups[distance].append(vertex)
    
#     # Sort distances for ordered processing (from inner to outer loops)
#     sorted_distances = sorted(distance_groups.keys())
    
#     if iris_flag:
#         num_groups = len(sorted_distances)
#         # First quarter: full influence.
#         quarter_size = num_groups // 4
#         if quarter_size < 1:
#             quarter_size = 1
    
#         # The fade zone will run from index `quarter_size` to the final index.
#         fade_range = (num_groups - 1) - quarter_size  # Ensure this is at least 1 for proper division
    
#         for i, distance in enumerate(sorted_distances):
#             if i < quarter_size:
#                 # First quarter: assign full weight (1.0)
#                 value = 1.0
#             else:
#                 # Fade from 1.0 to min_weight using cosine interpolation.
#                 # t goes from 0 (start of fade) to 1 (last group)
#                 t = float(i - quarter_size) / fade_range
#                 # Standard cosine interpolation gives a value from 1.0 down to 0.0:
#                 cosine_val = 0.5 * (math.cos(math.pi * t) + 1.0)
#                 # Remap that range so that the final value is min_weight rather than 0.0.
#                 value = min_weight + (1.0 - min_weight) * cosine_val
    
#             assign_influence_to_closest_joint(distance_groups[distance], joints_list, skin_cluster, iris_flag, value=value)

#     else:
#         for distance, vertices in distance_groups.items():
#             assign_influence_to_closest_joint(vertices, joints_list, skin_cluster, iris_flag, value=1)

#     if side == "R":
#         side_to_print = "Right"
#     elif side == "L":
#         side_to_print = "Left"

#     print(f"{side_to_print} eye is skinned")

# def assign_influence_to_eye_aim(side, faces):
#     aim_jnt = f"{side}_eyeAim_jnt"
#     skin_cluster = f"{side}_eye_sc"

#     """Assign all iris vertices to the L_eyeAim_jnt."""
#     all_vertices = cmds.polyListComponentConversion(faces, toVertex=True)
#     all_vertices = cmds.ls(all_vertices, flatten=True)  # Flatten the component list

#     for vertex in all_vertices:
#         cmds.skinPercent(skin_cluster, vertex, transformValue=(aim_jnt, 1.0))


# pupil_edges = ['L_eye_geo.e[1105]', 'L_eye_geo.e[1107]', 'L_eye_geo.e[1109]', 'L_eye_geo.e[1111]', 'L_eye_geo.e[1113]', 'L_eye_geo.e[1115]', 'L_eye_geo.e[1117]', 'L_eye_geo.e[1119]', 'L_eye_geo.e[1121]', 'L_eye_geo.e[1123]', 'L_eye_geo.e[1125]', 'L_eye_geo.e[1127]', 'L_eye_geo.e[1129]', 'L_eye_geo.e[1131]', 'L_eye_geo.e[1133]', 'L_eye_geo.e[1135]', 'L_eye_geo.e[1137]', 'L_eye_geo.e[1139]', 'L_eye_geo.e[1141]', 'L_eye_geo.e[1143]', 'L_eye_geo.e[1145]', 'L_eye_geo.e[1147]', 'L_eye_geo.e[1149]', 'L_eye_geo.e[1151]', 'L_eye_geo.e[1152]', 'L_eye_geo.e[1153]', 'L_eye_geo.e[1154]', 'L_eye_geo.e[1155]', 'L_eye_geo.e[1156]', 'L_eye_geo.e[1157]', 'L_eye_geo.e[1158]', 'L_eye_geo.e[1159]', 'L_eye_geo.e[1160]', 'L_eye_geo.e[1161]', 'L_eye_geo.e[1162]', 'L_eye_geo.e[1163]', 'L_eye_geo.e[1164]', 'L_eye_geo.e[1165]', 'L_eye_geo.e[1166]', 'L_eye_geo.e[1167]', 'L_eye_geo.e[1168]', 'L_eye_geo.e[1169]', 'L_eye_geo.e[1170]', 'L_eye_geo.e[1171]', 'L_eye_geo.e[1172]', 'L_eye_geo.e[1173]', 'L_eye_geo.e[1174]', 'L_eye_geo.e[1175]', 'L_eye_geo.e[1176]', 'L_eye_geo.e[1177]', 'L_eye_geo.e[1178]', 'L_eye_geo.e[1179]', 'L_eye_geo.e[1180]', 'L_eye_geo.e[1181]', 'L_eye_geo.e[1182]', 'L_eye_geo.e[1183]', 'L_eye_geo.e[1184]', 'L_eye_geo.e[1185]', 'L_eye_geo.e[1186]', 'L_eye_geo.e[1187]', 'L_eye_geo.e[1188]', 'L_eye_geo.e[1189]', 'L_eye_geo.e[1190]', 'L_eye_geo.e[1191]', 'L_eye_geo.e[1192]', 'L_eye_geo.e[1193]', 'L_eye_geo.e[1194]', 'L_eye_geo.e[1195]', 'L_eye_geo.e[1196]', 'L_eye_geo.e[1197]', 'L_eye_geo.e[1198]', 'L_eye_geo.e[1199]', 'L_eye_geo.e[1200]', 'L_eye_geo.e[1201]', 'L_eye_geo.e[1202]', 'L_eye_geo.e[1203]', 'L_eye_geo.e[1204]', 'L_eye_geo.e[1205]', 'L_eye_geo.e[1206]', 'L_eye_geo.e[1207]', 'L_eye_geo.e[1208]', 'L_eye_geo.e[1209]', 'L_eye_geo.e[1210]', 'L_eye_geo.e[1211]', 'L_eye_geo.e[1212]', 'L_eye_geo.e[1213]', 'L_eye_geo.e[1214]', 'L_eye_geo.e[1215]', 'L_eye_geo.e[1216]', 'L_eye_geo.e[1217]', 'L_eye_geo.e[1218]', 'L_eye_geo.e[1219]', 'L_eye_geo.e[1220]', 'L_eye_geo.e[1221]', 'L_eye_geo.e[1222]', 'L_eye_geo.e[1223]', 'L_eye_geo.e[1224]', 'L_eye_geo.e[1225]', 'L_eye_geo.e[1226]', 'L_eye_geo.e[1227]', 'L_eye_geo.e[1228]', 'L_eye_geo.e[1229]', 'L_eye_geo.e[1230]', 'L_eye_geo.e[1231]', 'L_eye_geo.e[1232]', 'L_eye_geo.e[1233]', 'L_eye_geo.e[1234]', 'L_eye_geo.e[1235]', 'L_eye_geo.e[1236]', 'L_eye_geo.e[1237]', 'L_eye_geo.e[1238]', 'L_eye_geo.e[1239]', 'L_eye_geo.e[1240]', 'L_eye_geo.e[1241]', 'L_eye_geo.e[1242]', 'L_eye_geo.e[1243]', 'L_eye_geo.e[1244]', 'L_eye_geo.e[1245]', 'L_eye_geo.e[1246]', 'L_eye_geo.e[1247]', 'L_eye_geo.e[1248]', 'L_eye_geo.e[1249]', 'L_eye_geo.e[1250]', 'L_eye_geo.e[1251]', 'L_eye_geo.e[1252]', 'L_eye_geo.e[1253]', 'L_eye_geo.e[1254]', 'L_eye_geo.e[1255]', 'L_eye_geo.e[1256]', 'L_eye_geo.e[1257]', 'L_eye_geo.e[1258]', 'L_eye_geo.e[1259]', 'L_eye_geo.e[1260]', 'L_eye_geo.e[1261]', 'L_eye_geo.e[1262]', 'L_eye_geo.e[1263]', 'L_eye_geo.e[1264]', 'L_eye_geo.e[1265]', 'L_eye_geo.e[1266]', 'L_eye_geo.e[1267]', 'L_eye_geo.e[1268]', 'L_eye_geo.e[1269]', 'L_eye_geo.e[1270]', 'L_eye_geo.e[1271]', 'L_eye_geo.e[1272]', 'L_eye_geo.e[1273]', 'L_eye_geo.e[1274]', 'L_eye_geo.e[1275]', 'L_eye_geo.e[1276]', 'L_eye_geo.e[1277]', 'L_eye_geo.e[1278]', 'L_eye_geo.e[1279]', 'L_eye_geo.e[1280]', 'L_eye_geo.e[1281]', 'L_eye_geo.e[1282]', 'L_eye_geo.e[1283]', 'L_eye_geo.e[1284]', 'L_eye_geo.e[1285]', 'L_eye_geo.e[1286]', 'L_eye_geo.e[1287]', 'L_eye_geo.e[1288]', 'L_eye_geo.e[1289]', 'L_eye_geo.e[1290]', 'L_eye_geo.e[1291]', 'L_eye_geo.e[1292]', 'L_eye_geo.e[1293]', 'L_eye_geo.e[1294]', 'L_eye_geo.e[1295]', 'L_eye_geo.e[1296]', 'L_eye_geo.e[1297]', 'L_eye_geo.e[1298]', 'L_eye_geo.e[1299]', 'L_eye_geo.e[1300]', 'L_eye_geo.e[1301]', 'L_eye_geo.e[1302]', 'L_eye_geo.e[1303]', 'L_eye_geo.e[1304]', 'L_eye_geo.e[1305]', 'L_eye_geo.e[1306]', 'L_eye_geo.e[1307]', 'L_eye_geo.e[1308]', 'L_eye_geo.e[1309]', 'L_eye_geo.e[1310]', 'L_eye_geo.e[1311]', 'L_eye_geo.e[1312]', 'L_eye_geo.e[1313]', 'L_eye_geo.e[1314]', 'L_eye_geo.e[1315]', 'L_eye_geo.e[1316]', 'L_eye_geo.e[1317]', 'L_eye_geo.e[1318]', 'L_eye_geo.e[1319]', 'L_eye_geo.e[1320]', 'L_eye_geo.e[1321]', 'L_eye_geo.e[1322]', 'L_eye_geo.e[1323]', 'L_eye_geo.e[1324]', 'L_eye_geo.e[1325]', 'L_eye_geo.e[1326]', 'L_eye_geo.e[1327]', 'L_eye_geo.e[1328]', 'L_eye_geo.e[1329]', 'L_eye_geo.e[1330]', 'L_eye_geo.e[1331]', 'L_eye_geo.e[1332]', 'L_eye_geo.e[1333]', 'L_eye_geo.e[1334]', 'L_eye_geo.e[1335]', 'L_eye_geo.e[1336]', 'L_eye_geo.e[1337]', 'L_eye_geo.e[1338]', 'L_eye_geo.e[1339]', 'L_eye_geo.e[1340]', 'L_eye_geo.e[1341]', 'L_eye_geo.e[1342]', 'L_eye_geo.e[1343]', 'L_eye_geo.e[1344]', 'L_eye_geo.e[1345]', 'L_eye_geo.e[1346]', 'L_eye_geo.e[1347]', 'L_eye_geo.e[1348]', 'L_eye_geo.e[1349]', 'L_eye_geo.e[1350]', 'L_eye_geo.e[1351]', 'L_eye_geo.e[1352]', 'L_eye_geo.e[1353]', 'L_eye_geo.e[1354]', 'L_eye_geo.e[1355]', 'L_eye_geo.e[1356]', 'L_eye_geo.e[1357]', 'L_eye_geo.e[1358]', 'L_eye_geo.e[1359]', 'L_eye_geo.e[1360]', 'L_eye_geo.e[1361]', 'L_eye_geo.e[1362]', 'L_eye_geo.e[1363]', 'L_eye_geo.e[1364]', 'L_eye_geo.e[1365]', 'L_eye_geo.e[1366]', 'L_eye_geo.e[1367]', 'L_eye_geo.e[1368]', 'L_eye_geo.e[1369]', 'L_eye_geo.e[1370]', 'L_eye_geo.e[1371]', 'L_eye_geo.e[1372]', 'L_eye_geo.e[1373]', 'L_eye_geo.e[1374]', 'L_eye_geo.e[1375]', 'L_eye_geo.e[1376]', 'L_eye_geo.e[1377]', 'L_eye_geo.e[1378]', 'L_eye_geo.e[1379]', 'L_eye_geo.e[1380]', 'L_eye_geo.e[1381]', 'L_eye_geo.e[1382]', 'L_eye_geo.e[1383]', 'L_eye_geo.e[1384]', 'L_eye_geo.e[1385]', 'L_eye_geo.e[1386]', 'L_eye_geo.e[1387]', 'L_eye_geo.e[1388]', 'L_eye_geo.e[1389]', 'L_eye_geo.e[1390]', 'L_eye_geo.e[1391]', 'L_eye_geo.e[1392]', 'L_eye_geo.e[1393]', 'L_eye_geo.e[1394]', 'L_eye_geo.e[1395]', 'L_eye_geo.e[1396]', 'L_eye_geo.e[1397]', 'L_eye_geo.e[1398]', 'L_eye_geo.e[1399]', 'L_eye_geo.e[1400]', 'L_eye_geo.e[1401]', 'L_eye_geo.e[1402]', 'L_eye_geo.e[1403]', 'L_eye_geo.e[1404]', 'L_eye_geo.e[1405]', 'L_eye_geo.e[1406]', 'L_eye_geo.e[1407]', 'L_eye_geo.e[1408]', 'L_eye_geo.e[1409]', 'L_eye_geo.e[1410]', 'L_eye_geo.e[1411]', 'L_eye_geo.e[1412]', 'L_eye_geo.e[1413]', 'L_eye_geo.e[1414]', 'L_eye_geo.e[1415]', 'L_eye_geo.e[1416]', 'L_eye_geo.e[1417]', 'L_eye_geo.e[1418]', 'L_eye_geo.e[1419]', 'L_eye_geo.e[1420]', 'L_eye_geo.e[1421]', 'L_eye_geo.e[1422]', 'L_eye_geo.e[1423]', 'L_eye_geo.e[1424]', 'L_eye_geo.e[1425]', 'L_eye_geo.e[1426]', 'L_eye_geo.e[1427]', 'L_eye_geo.e[1428]', 'L_eye_geo.e[1429]', 'L_eye_geo.e[1430]', 'L_eye_geo.e[1431]', 'L_eye_geo.e[1432]', 'L_eye_geo.e[1433]', 'L_eye_geo.e[1434]', 'L_eye_geo.e[1435]', 'L_eye_geo.e[1436]', 'L_eye_geo.e[1437]', 'L_eye_geo.e[1438]', 'L_eye_geo.e[1439]', 'L_eye_geo.e[1440]', 'L_eye_geo.e[1441]', 'L_eye_geo.e[1442]', 'L_eye_geo.e[1443]', 'L_eye_geo.e[1444]', 'L_eye_geo.e[1445]', 'L_eye_geo.e[1446]', 'L_eye_geo.e[1447]', 'L_eye_geo.e[1448]', 'L_eye_geo.e[1449]', 'L_eye_geo.e[1450]', 'L_eye_geo.e[1451]', 'L_eye_geo.e[1452]', 'L_eye_geo.e[1453]', 'L_eye_geo.e[1454]', 'L_eye_geo.e[1455]', 'L_eye_geo.e[1456]', 'L_eye_geo.e[1457]', 'L_eye_geo.e[1458]', 'L_eye_geo.e[1459]', 'L_eye_geo.e[1460]', 'L_eye_geo.e[1461]', 'L_eye_geo.e[1462]', 'L_eye_geo.e[1463]', 'L_eye_geo.e[1464]', 'L_eye_geo.e[1465]', 'L_eye_geo.e[1466]', 'L_eye_geo.e[1467]', 'L_eye_geo.e[1468]', 'L_eye_geo.e[1469]', 'L_eye_geo.e[1470]', 'L_eye_geo.e[1471]', 'L_eye_geo.e[1472]', 'L_eye_geo.e[1473]', 'L_eye_geo.e[1474]', 'L_eye_geo.e[1475]', 'L_eye_geo.e[1476]', 'L_eye_geo.e[1477]', 'L_eye_geo.e[1478]', 'L_eye_geo.e[1479]', 'L_eye_geo.e[1480]', 'L_eye_geo.e[1481]', 'L_eye_geo.e[1482]', 'L_eye_geo.e[1483]', 'L_eye_geo.e[1484]', 'L_eye_geo.e[1485]', 'L_eye_geo.e[1486]', 'L_eye_geo.e[1487]']
# pupil_joints = [f"L_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]  # Pupil joints
# iris_joints = [f"L_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]

# r_pupil_edges = [edge.replace("L_eye_geo", "R_eye_geo") for edge in pupil_edges]
# r_iris_edges  = [edge.replace("L_eye_geo", "R_eye_geo") for edge in iris_edges]
# r_pupil_joints = [f"R_pupilScale{str(i).zfill(2)}_jnt" for i in range(24)]  # Pupil joints
# r_iris_joints = [f"R_irisTip{str(i).zfill(2)}_jnt" for i in range(24)]



# assign_influence_to_eye_aim("L", iris_edges)
# assign_influence_to_eye_aim("L", pupil_edges)

# skin_eye_verts("L", pupil_edges, pupil_joints, iris_flag=False)
# skin_eye_verts("L", iris_edges, iris_joints, iris_flag=True)

# assign_influence_to_eye_aim("R", r_iris_edges)
# assign_influence_to_eye_aim("R", r_pupil_edges)

# skin_eye_verts("R", r_pupil_edges, r_pupil_joints, iris_flag=False)
# skin_eye_verts("R", r_iris_edges, r_iris_joints, iris_flag=True)






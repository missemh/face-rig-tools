import maya.cmds as cmds
import pymel.core as pm
import math
import re
from facialAutoRigger.dictionaries import colors
from facialAutoRigger import utils
from facialAutoRigger.parts import joints
from facialAutoRigger.parts import guides
from facialAutoRigger.parts import controls
from facialAutoRigger.features import eyeAttributes


class Eye():
    def __init__(self, l_upper_edges, l_lower_edges, r_upper_edges, r_lower_edges, joint_parent=None, rig_parent=None):
        self.l_upper_edges = l_upper_edges
        self.l_lower_edges = l_lower_edges
        self.r_upper_edges = r_upper_edges
        self.r_lower_edges = r_lower_edges
        self.rig_parent = rig_parent
        self.lid_names = ["Upper", "Lower"]
        self.control_names = ["Inner", "UpperTweak00", "UpperMid", "UpperTweak01", "Outer", "LowerTweak00", "LowerMid", "LowerTweak01"]
        self.joint_parent = joint_parent
        self.l_pupil_vert = "l_eye_geo.vtx[73]"
        self.r_pupil_vert = "r_eye_geo.vtx[73]"
        self.l_eye_rig = cmds.group(empty=True, name=f"L_eyeRig_grp")
        l_settings_shape = self.create_settings_shape("L", self.l_eye_rig)
        self.create_rig(l_settings_shape)


    def create_rig(self, l_settings_shape):

        # Create curves and wire deformers for left and right sides.
        l_curve_grp, self.l_high_curves, l_low_curves, l_blend_curve, l_driver_curves, l_drivers_bs, l_upper_blink_bs, l_lower_blink_bs = self.create_curves("L", self.l_upper_edges, self.l_lower_edges)
        r_curve_grp, r_high_curves, r_low_curves, r_blend_curve, r_driver_curves, r_drivers_bs, r_upper_blink_bs, r_lower_blink_bs = self.create_curves("R", self.r_upper_edges, self.r_lower_edges)

        
        # Create left controls,
        l_eye_offset, l_eye_ctrl, l_eyelid_offset, l_eyelid_ctrl, l_controls, l_offsets = self.create_left_side_controls("L", self.l_eye_rig, self.l_high_curves, l_settings_shape)
        
        # Duplicate and scale left controls to create right controls.
        self.r_eye_rig, r_settings_shape, r_eye_ctrl, r_eye_offset, r_eyelid_offset, r_eyelid_ctrl, r_offsets, r_controls = self.create_right_side_controls(self.l_eye_rig)
        
        # Create left and right joints to skin to curve
        l_eye_joints, l_upper_joints, l_lower_joints, r_eye_joints, r_upper_joints, r_lower_joints = self.create_joints(l_controls, r_controls, l_eyelid_ctrl, r_eyelid_ctrl)

        # Skin joints to curves. Constrain controls and offsets in hierarchy and to joints.
        self.create_curve_connections("L",l_eye_joints, l_upper_joints, l_lower_joints, l_low_curves, l_controls, l_offsets)
        self.create_curve_connections("R",r_eye_joints, r_upper_joints, r_lower_joints, r_low_curves, r_controls, r_offsets)

        # Connection blendshapes to settings attributes.
        self.create_blendshape_connections("L", l_settings_shape, l_upper_blink_bs, l_lower_blink_bs, l_blend_curve, l_driver_curves, l_drivers_bs)
        self.create_blendshape_connections("R", r_settings_shape, r_upper_blink_bs, r_lower_blink_bs, r_blend_curve, r_driver_curves, r_drivers_bs)

        l_eye_joints, r_eye_joints, l_up_loc, r_up_loc, l_aim_jnt, r_aim_jnt = self.create_eyeball_joints(l_eye_ctrl, l_eyelid_ctrl, r_eye_ctrl, r_eyelid_ctrl)

        l_eyelid_ctrl_grp = self.create_joints_around_eye("L", self.l_high_curves, l_eye_joints[-1], l_eyelid_ctrl, l_up_loc)
        self.create_joints_around_eye("R", r_high_curves, r_eye_joints[-1], r_eyelid_ctrl, r_up_loc, l_eyelid_ctrl_grp)
        
        main_aim_offset = self.create_eye_aim_left_and_right(l_eye_ctrl, r_eye_ctrl, l_settings_shape, r_settings_shape, l_up_loc, r_up_loc, l_aim_jnt, r_aim_jnt)

        eye_rig_grp = cmds.group(empty=True, name=f"eyeRig_grp")
        cmds.parent(main_aim_offset, eye_rig_grp)
        cmds.parent(l_curve_grp, self.l_eye_rig)
        cmds.parent(r_curve_grp, self.r_eye_rig)
        cmds.parent(self.l_eye_rig, eye_rig_grp)
        cmds.parent(self.r_eye_rig, eye_rig_grp)

        if self.rig_parent:
            cmds.parent(eye_rig_grp, self.rig_parent)

        self.create_fleshy_eyes(l_settings_shape, r_settings_shape,l_offsets, r_offsets, l_blend_curve)


    def create_settings_shape(self, side, rig_group):
        settings = controls.SettingsShape(rig_group, f"{side}_eye")
        settings_shape = settings.settings_shape

        cmds.addAttr(settings_shape, ln="blinkHeight", at="float", min=-1, max=1, dv=0, k=True)
        cmds.addAttr(settings_shape, ln="upperBlink", at="double", min=0, max=1, dv=0, k=True)
        cmds.addAttr(settings_shape, ln="lowerBlink", at="double", min=0, max=1, dv=0, k=True)

        return settings_shape


#-------------------------------------------------------------------------------------------------------------------------------------    

class Eye():
    def __init__(self, l_upper_edges, l_lower_edges, r_upper_edges, r_lower_edges, joint_parent=None, rig_parent=None):
        self.l_upper_edges = l_upper_edges
        self.l_lower_edges = l_lower_edges
        self.r_upper_edges = r_upper_edges
        self.r_lower_edges = r_lower_edges

        self.l_eye_rig = cmds.group(empty=True, name=f"L_eyeRig_grp")

        # Build left and right curves using CurveManager
        self.l_curves = CurveManager("L", self.l_upper_edges, self.l_lower_edges).build()
        self.r_curves = CurveManager("R", self.r_upper_edges, self.r_lower_edges).build()


#-------------------------------------------------------------------------------------------------------------------------------------    
# Create eyelid curves from edge selection

class CurveManager:
    def __init__(self, side, upper_edges, lower_edges):
        self.side = side
        self.upper_edges = upper_edges
        self.lower_edges = lower_edges
        self.high_curves = []
        self.low_curves = []
        self.blink_curves = []
        self.base_curves = []
        self.ref_curves = []
        self.blend_curve = None

    def create_curve_group(self):
        return cmds.group(empty=True, name=f"{self.side}_eyeCurve_grp")

    def create_high_curves(self):
        cmds.select(clear=True)
        for name, edges in zip(["Upper", "Lower"], [self.upper_edges, self.lower_edges]):
            cmds.select(edges)
            curve_name = f"{self.side}_eyelid{name}High_crv"
            curve_from_edge = cmds.polyToCurve(form=2, degree=1, conformToSmoothMeshPreview=1, ch=0)[0]
            curve_from_edge = cmds.rename(curve_from_edge, curve_name)
            self.high_res_curves.append(curve_from_edge)
        cmds.select(clear=True)

    def check_and_adjust_curve_direction(self):
        direction_matched = utils.compare_curve_directions(self.high_curves[0], self.high_curves[-1])
        if not direction_matched:
            print("Curves have been adjusted to match direction.")
            self.high_curves = self.adjust_curve_direction(self.high_curves)
        else:
            print("Curves are in the same direction.")

    def adjust_curve_direction(self, curves):
        adjusted_curves = []
        for curve in curves:
            adjusted_curve = cmds.reverseCurve(curve, constructionHistory=False)[0]
            adjusted_curves.append(adjusted_curve)
        return adjusted_curves

    def rebuild_curves_to_create_low_curves(self, span=4):
        for crv in self.high_curves:
            low_curve = cmds.duplicate(crv, name=crv.replace("High_crv", "Low_crv"))[0]
            low_curve = cmds.rebuildCurve(low_curve, ch=0, rpo=True, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=span, d=3, tol=0.01)[0]
            self.low_curves.append(low_curve)

    def create_blend_and_driver_curves(self):
        # Duplicate the lower lid high resolution curve
        self.blend_curve = cmds.duplicate(self.high_res_curves[1], name=self.high_res_curves[1].replace("LowerHigh_crv", "Blend_crv"))[0]

        # Blendshape the high curve in, then delete, so the blend curve is half way between the upper and lower lids
        cmds.blendShape(self.high_res_curves[0], self.blend_curve, name=f"{self.side}_eye_bs")[0]
        cmds.delete(self.blend_curve, constructionHistory=True)

        for crv in self.high_curves:
            blink_curve = cmds.duplicate(crv, name=crv.replace("High_crv", "Blink_crv"))[0]
            ref_curve = cmds.duplicate(crv, name=crv.replace("High_crv", "Driver_crv"))[0]
            base_curve = cmds.duplicate(crv, name=crv.replace("High_crv", "Base_crv"))[0]
            combined_curve = cmds.duplicate(crv, name=crv.replace("High_crv", "Combined_crv"))[0]
            self.blink_curves.append(blink_curve)
            self.ref_curves.append(ref_curve)
            self.base_curves.append(base_curve)
            self.combined_curves.append(combined_curve)

    def create_wires(self):
        for driver, low, name in zip(self.ref_curves, self.low_curves, ["Upper", "Lower"]): 
            cmds.wire(driver, wire=low, name=f"{self.side}_eyelid{name}_wire")

    def build(self):
        curve_group = self.create_curve_group()
        self.create_high_curves()
        self.check_and_adjust_curve_direction()
        self.rebuild_curves_to_create_low_curves()
        self.create_blend_and_driver_curves()
        self.create_wires()
        self.create_blink_blendshapes()

        return {
            "curve_group": curve_group,
            "high_curves": self.high_curves,
            "low_curves": self.low_curves,
            "blink_curves": self.blink_curves,
            "driver_curves": self.driver_curves,
            "blend_curve": self.blend_curve
        }


    def create_blink_blendshapes(self):
        upper_blink_blendshape = cmds.blendShape(self.driver_curves[0], self.blend_curve, self.blink_curves[0], name=f"{self.side}_upperBlink_bs")[0]
        lower_blink_blendshape = cmds.blendShape(self.driver_curves[-1], self.blend_curve, self.blink_curves[-1], name=f"{self.side}_lowerBlink_bs")[0]

#-------------------------------------------------------------------------------------------------------------------------------------    
# Create eyelid controls for the left eye

class EyeControlManager:
    def __init__(self, side, rig_group, high_curves, l_settings_shape):
        self.side = side
        self.rig_group = rig_group
        self.high_curves = high_curves
        self.settings_shape = settings_shape
        self.scale_factor = self.calculate_scale_factor(high_curves)
        self.controls_inst = ControlsBase()
        self.l_eyelid_ctrls = []
    
    def calculate_scale_factor(self, high_curves, num_spans=4):
        curve_length = cmds.arclen(high_curves[0])
        return curve_length / num_spans

    def create_master_controls(self, l_settings_shape):
        center_group = self.find_aim_of_the_pupil()

        scale = self.scale_factor / 4

        # Create master controls
        eye_offset, eye_ctrl  = self.controls_instance.create_control("circle", 13, "L_eyeMaster", scale, position_obj=center_group, orient_flag=True, settings_shape=self.settings_shape)
        eyelid_offset, eyelid_ctrl = self.controls_instance.create_control("circle", 13, "L_eyeMaster", scale*0.5, position_obj=center_group, orient_flag=True, settings_shape=self.settings_shape)

        # Move cvs
        for ctrl in [eye_ctrl, eyelid_ctrl]:
            cvs_master = cmds.ls(f"{ctrl}.cv[*]", flatten=True)
            for cv in cvs_master:
                cmds.move(1, 0, -0.4, cv, relative=True, worldSpace=True)

        # Create hierarchy
        cmds.parent(eyelid_offset, eye_ctrl)
        cmds.parent(eye_offset, rig_group)
        cmds.delete(center_group)

    def find_aim_of_the_pupil(self, left_eyeball_geo)
        # Find aim of pupil
        center_group = cmds.group(empty=True, name="L_eyeCenter_grp")
        aimer_loc = cmds.spaceLocator(name="L_eyePupil_loc")[0]
        cmds.delete(cmds.parentConstraint(left_eyeball_geo, center_group, mo=False))
        pupil_pos = cmds.xform(self.l_pupil_vert, query=True, translation=True, worldSpace=True)
        cmds.xform(aimer_loc, translation=pupil_pos, worldSpace=True)
        cmds.delete(cmds.aimConstraint(aimer_loc, center_group, aimVector=[0, 0, 1], upVector=[0, 1, 0]))
        cmds.delete(aimer_loc)

        return center_group

    def create_eyelid_controls(self):
        self.l_upperlid_controls = []
        self.l_upperlid_offset = []

        scale = self.scale_factor / 6
        inner_loc, outer_loc = place_inner_and_outer_locs(self.l_pupil_vert, self.l_curves.high_curves[-1])

        inner_offet, inner_control = self.controls_inst.create_control("circle", 14, "L_eyeInner", scale, position_obj=inner_loc, orient_flag=True, settings_shape=self.settings_shape)
        outer_offet, outer_control = self.controls_inst.create_control("circle", 14, "L_eyeOuter", scale, position_obj=outer_loc, orient_flag=True, settings_shape=self.settings_shape)

        upper_lid_locs, lower_lid_locs = place_lid_locs(self.l_curves.high_curves)

        for loc in upper_lid_locs:
            offset, control = self.controls_inst.create_control("circle", 14, "L_eyeInner", scale, position_obj=loc, orient_flag=True, settings_shape=self.settings_shape)

        for loc in lower_lid_locs:
            offset, control = self.controls_inst.create_control("circle", 14, "L_eyeInner", scale, position_obj=loc, orient_flag=True, settings_shape=self.settings_shape)
            self.left_offsets.append(offsets)
            self.left_offsets.append(offsets)

        master_scale = self.scale_factor / 4

        inner_master_offset, inner_master_control = self.controls_inst.create_control("square", 20, "L_eyelidInner", master_scale, position_obj=inner_offet, orient_flag=True, settings_shape=self.settings_shape)
        outer_master_offset, outer_master_control = self.controls_inst.create_control("square", 20, "L_eyelidOuter", master_scale, position_obj=outer_offet, orient_flag=True, settings_shape=self.settings_shape)
        upper_master_offset, inner_master_control = self.controls_inst.create_control("square", 20, "L_eyelidUpper", master_scale, position_obj=upper_lid_locs[1], orient_flag=True, settings_shape=self.settings_shape)
        lower_master_offset, inner_master_control = self.controls_inst.create_control("square", 20, "L_eyelidLower", master_scale, position_obj=lower_lid_locs[1], orient_flag=True, settings_shape=self.settings_shape)

        # Clean up scene
        for loc in upper_lid_locs:
            cmds.delete(loc)

        for loc in lower_lid_locs:
            cmds.delete(loc)

        cmds.delete(inner_loc)
        cmds.delete(outer_loc)

        # Move control shapes out from their pivots, to position in front of the eye topology
        for ctrl in l_controls:
            cvs = cmds.ls(f"{ctrl}.cv[*]", flatten=True)
            for cv in cvs:
                cmds.move(0, 0, 0.3, cv, relative=True, objectSpace=True, worldSpaceDistance=True)

        return eye_offset, eye_ctrl, eyelid_offset, eyelid_ctrl, l_controls, l_offsets


    def create_right_side_controls(self, l_rig_group):
        r_eye_rig_group = cmds.duplicate(l_rig_group, name="R_eyeRig_grp", renameChildren=True)[0]

        # Scale the duplicated group to mirror it
        cmds.scale(-1, 1, 1, r_eye_rig_group, relative=True)

        children = cmds.listRelatives(r_eye_rig_group, allDescendents=True) or []

        r_controls = []
        r_offsets = []
        settings_shape_found = False

        # Rename each child with the new prefix
        for child in children:
            child_name = child.split("|")[-1]
            right_name = child_name.replace("L_", "R_")
            pattern = re.compile(r'(?<!0)1')
            new_name = pattern.sub('', right_name)
            cmds.rename(child, new_name)
            if cmds.objectType(new_name) == 'transform':
                if "eyeMaster_grp" in new_name:
                    r_eye_offset = new_name
                if "eyeMaster_ctrl" in new_name:
                    r_eye_ctrl = new_name
                if "eyelidMaster_grp" in new_name:
                    r_eyelid_offset = new_name
                if "eyelidMaster_ctrl" in new_name:
                    r_eyelid_ctrl = new_name
                if "ctrl" in new_name and any(keyword in new_name for keyword in ["Inner", "Upper", "Outer", "Lower"]):
                    r_controls.append(new_name)
                if "grp" in new_name and any(keyword in new_name for keyword in ["Inner", "Upper", "Outer", "Lower"]):
                    r_offsets.append(new_name)
            shapes = cmds.listRelatives(new_name, shapes=True, fullPath=True) or []
            if not settings_shape_found:
                if "locShape" in new_name:
                    r_settings_shape = new_name
                    settings_shape_found = True


        return r_eye_rig_group, r_settings_shape, r_eye_ctrl, r_eye_offset, r_eyelid_offset, r_eyelid_ctrl, r_offsets, r_controls


    def create_joints(self, l_controls, r_controls, l_eyelid_ctrl, r_eyelid_ctrl):
        l_eye_joints = []
        l_upper_skin_joints = []
        l_lower_skin_joints = []

        r_eye_joints = []
        r_upper_skin_joints = []
        r_lower_skin_joints = []

        for index, (l_ctrl, r_ctrl) in enumerate(zip(l_controls, r_controls)):
            cmds.select(clear=True)
            l_jnt = cmds.joint(name=l_ctrl.replace("ctrl", "jnt"))
            cmds.delete(cmds.parentConstraint(l_ctrl, l_jnt, mo=False))
            cmds.makeIdentity(l_jnt, apply=True, translate=True, rotate=True, scale=True)
            cmds.select(clear=True)
            r_jnt = cmds.mirrorJoint(l_jnt, mirrorYZ=True, mirrorBehavior=True, searchReplace=("L_", "R_"))[0]
            cmds.select(clear=True)

            l_eye_joints.append(l_jnt)
            r_eye_joints.append(r_jnt)

            if index == 0:
                l_upper_skin_joints.append(l_jnt)
                l_lower_skin_joints.append(l_jnt)
                r_upper_skin_joints.append(r_jnt)
                r_lower_skin_joints.append(r_jnt)
            elif index == 1 or index == 2 or index == 3:
                l_upper_skin_joints.append(l_jnt)
                r_upper_skin_joints.append(r_jnt)
            elif index == 4:
                l_upper_skin_joints.append(l_jnt)
                l_lower_skin_joints.append(l_jnt)
                r_upper_skin_joints.append(r_jnt)
                r_lower_skin_joints.append(r_jnt)
            elif index == 5 or index == 6 or index == 7:
                l_lower_skin_joints.insert(-1, l_jnt)
                r_lower_skin_joints.insert(-1, r_jnt)


        self.l_offset_jnts = []
        self.r_offset_jnts = []

        for joints, offsets_list in zip([l_eye_joints, r_eye_joints], 
                                        [self.l_offset_jnts, self.r_offset_jnts]):
            for jnt in joints:
                offset_joint = cmds.duplicate(jnt)
                offset_joint = cmds.rename(offset_joint, jnt.replace("_jnt", "Offset_jnt"))  
                cmds.parent(jnt, offset_joint)
                offsets_list.append(offset_joint)

        l_curve_joint_grp = cmds.group(empty=True, name="L_curveJoints_grp")
        r_curve_joint_grp = cmds.group(empty=True, name="R_curveJoints_grp")
        cmds.parent(l_curve_joint_grp, self.l_eye_rig)
        cmds.parent(r_curve_joint_grp, self.r_eye_rig)

        for jnt in  self.l_offset_jnts:
            cmds.parent(jnt, l_curve_joint_grp)

        for jnt in self.r_offset_jnts:
            cmds.parent(jnt, r_curve_joint_grp)


        return l_eye_joints, l_upper_skin_joints, l_lower_skin_joints, r_eye_joints, r_upper_skin_joints, r_lower_skin_joints

    def create_curve_connections(self, side, eye_joints, upper_skin_joints, lower_skin_joints, low_curves, controls, offsets):
        # Skin joints to low res curves
        skin_cluster_upper = cmds.skinCluster(*upper_skin_joints, low_curves[0], name=f"{side}_eyelidUpper_clstr", toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)[0]
        skin_cluster_lower = cmds.skinCluster(*lower_skin_joints, low_curves[1], name=f"{side}_eyelidLower_clstr", toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)[0]

        # Create constraints between the controls and joints
        # for jnt, ctrl in zip(eye_joints, controls):
        #     driver_name = utils.process_name(ctrl)
        #     driven_name = utils.process_name(jnt)
        #     cmds.parentConstraint(ctrl, jnt, mo=True, name=f"{driver_name}_parent_{driven_name}")

        if side == "L":
            for jnt, ctrl in zip(eye_joints, controls):
                for attr in ["translate", "rotate", "scale"]:
                    for axis in ["X", "Y", "Z"]:
                        cmds.connectAttr(f"{ctrl}.{attr}{axis}", f"{jnt}.{attr}{axis}")

        if side == "R":
            for jnt, ctrl in zip(eye_joints, controls):
                neg_value_mdn = cmds.createNode("multiplyDivide", name=ctrl.replace("ctrl", "NegValue_mdn"))
                for attr in ["rotate", "scale"]:
                    for axis in ["X", "Y", "Z"]:
                        cmds.connectAttr(f"{ctrl}.{attr}{axis}", f"{jnt}.{attr}{axis}")
                for axis in ["X", "Y", "Z"]:
                    cmds.setAttr(f"{neg_value_mdn}.input2{axis}", -1)
                    cmds.connectAttr(f"{ctrl}.translate{axis}", f"{neg_value_mdn}.input1{axis}")
                    cmds.connectAttr(f"{neg_value_mdn}.output{axis}", f"{jnt}.translate{axis}")


        # # Create constraints between the controls and tweaks
        # for d1_index, d2_index, dr_index in zip([0,4,0,4], [2,2,6,6], [1,3,5,-1]):
        #     driver_one = utils.process_name(controls[d1_index])
        #     driver_two = utils.process_name(controls[d2_index])
        #     driven_name = utils.process_name(offsets[dr_index])
        #     constraint_name = f"{driver_one}_{driver_two}_parent_{driven_name}"
        #     cmds.parentConstraint(controls[d1_index], controls[d2_index], offsets[dr_index], mo=True, name=constraint_name)


    def create_blendshape_connections(self, side, settings_shape, upper_blink_bs, lower_blink_bs, blend_curve, driver_curves, drivers_bs):
        # Connect blink attributes to blendshapes with reverse nodes
        for index, attr in enumerate(["lowerBlink", "upperBlink"]):
            reverse_node = pm.createNode("reverse", name=f"{side}_eye{attr.capitalize()}_rev")
            cmds.connectAttr(f"{settings_shape}.{attr}", f"{reverse_node}.inputX")
            if index == 0:
                cmds.connectAttr(f"{settings_shape}.{attr}", f"{lower_blink_bs}.{blend_curve[0]}")
                cmds.connectAttr(f"{reverse_node}.outputX", f"{lower_blink_bs}.{driver_curves[1][0]}")
            if index == 1:
                cmds.connectAttr(f"{settings_shape}.{attr}", f"{upper_blink_bs}.{blend_curve[0]}")
                cmds.connectAttr(f"{reverse_node}.outputX", f"{upper_blink_bs}.{driver_curves[0][0]}")

        # Connect blink height attribute to blendshape with remap nodes
        for index, (driver, height) in enumerate(zip(driver_curves, ["upper", "lower"])):
            remape_node = pm.createNode("remapValue", name=f"{side}_eye{height.capitalize()}_rmp")
            cmds.connectAttr(f"{settings_shape}.blinkHeight", f"{remape_node}.inputValue")
            cmds.setAttr(f"{remape_node}.inputMin", -1)
            cmds.connectAttr(f"{remape_node}.outValue", f"{drivers_bs}.{driver[0]}")
            if index == 0:
                cmds.setAttr(f"{remape_node}.outputMin", 0)
                cmds.setAttr(f"{remape_node}.outputMax", 1)
            if index == 1:
                cmds.setAttr(f"{remape_node}.outputMin", 1)
                cmds.setAttr(f"{remape_node}.outputMax", 0)


    def create_eyeball_joints(self, l_eye_ctrl, l_eyelid_ctrl, r_eye_ctrl, r_eyelid_ctrl):
        # Create eye and eyelid joints. Parent to the parent joint if it was given in the arguements.
        l_eyeball_joints = []
        r_eyeball_joints = []

        for name in ["eye", "eyelid"]:
            cmds.select(clear=True)
            l_eye_jnt = cmds.joint(name=f"L_{name}_jnt")
            cmds.delete(cmds.parentConstraint(l_eye_ctrl, l_eye_jnt, mo=False))
            r_eye_jnt = cmds.mirrorJoint(l_eye_jnt, mirrorYZ=True, mirrorBehavior=True, searchReplace=("L", "R"))[0]

            cmds.setAttr(f"{l_eye_jnt}.side", 1)
            cmds.setAttr(f"{r_eye_jnt}.side", 2)
            cmds.setAttr(f"{l_eye_jnt}.type", 18)
            cmds.setAttr(f"{r_eye_jnt}.type", 18)
            label_name = f"{name}_lbl"
            cmds.setAttr(f"{l_eye_jnt}.otherType", label_name, type="string")
            cmds.setAttr(f"{r_eye_jnt}.otherType", label_name, type="string")

            l_eyeball_joints.append(l_eye_jnt)
            r_eyeball_joints.append(r_eye_jnt)
            cmds.select(clear=True)
            cmds.makeIdentity(l_eye_jnt, apply=True, translate=True, rotate=True, scale=True)
            cmds.makeIdentity(r_eye_jnt, apply=True, translate=True, rotate=True, scale=True)

        for l_jnt, l_ctrl in zip(l_eyeball_joints, [l_eye_ctrl, l_eyelid_ctrl]):
            l_driver_ctrl = utils.process_name(l_ctrl)
            l_driven_jnt = utils.process_name(l_jnt)
            cmds.parentConstraint(l_ctrl, l_jnt, mo=False, name=f"{l_driver_ctrl}_parent_{l_driven_jnt}")
            cmds.scaleConstraint(l_ctrl, l_jnt, mo=False, name=f"{l_driver_ctrl}_scale_{l_driven_jnt}")

        for r_jnt, r_ctrl in zip(r_eyeball_joints, [r_eye_ctrl, r_eyelid_ctrl]):
            r_driver_ctrl = utils.process_name(r_ctrl)
            r_driven_jnt = utils.process_name(r_jnt)
            cmds.parentConstraint(r_ctrl, r_jnt, mo=True, name=f"{r_driver_ctrl}_parent_{r_driven_jnt}")
            cmds.scaleConstraint(r_ctrl, r_jnt, mo=True, name=f"{r_driver_ctrl}_scale_{r_driven_jnt}")

        # Create up object
        for side, ctrl in zip(["L", "R"], [l_eye_ctrl, r_eye_ctrl]):
            up_loc = cmds.spaceLocator(name=f"{side}_eyeUpObject_loc")[0]
            cmds.delete(cmds.parentConstraint(ctrl, up_loc, mo=False))
            move_distance = abs(self.scale_factor * 4)
            scale_factor = self.scale_factor
            cmds.scale(scale_factor, scale_factor, scale_factor, up_loc)
            cmds.move(0,move_distance,0, up_loc, relative=True)
            cmds.parent(up_loc, ctrl)
            if side == "L":
                l_up_loc = up_loc
            elif side == "R":
                r_up_loc = up_loc


        l_pupil_pos = cmds.xform(self.l_pupil_vert, query=True, translation=True, worldSpace=True)
        r_pupil_pos = cmds.xform(self.r_pupil_vert, query=True, translation=True, worldSpace=True)

        for index, (side, ctrl, pos, up_obj) in enumerate(zip(["L", "R"], [l_eye_ctrl, r_eye_ctrl], [l_pupil_pos, r_pupil_pos], [l_up_loc, r_up_loc])):
            cmds.select(clear=True)
            jnt = cmds.joint(name=f"{side}_eyeAim_jnt")
            cmds.select(clear=True)
            jnt_tip = cmds.joint(name=f"{side}_eyePupil_jnt")
            cmds.select(clear=True)

            cmds.setAttr(f"{jnt}.side", 1 if side == "L" else 2)
            cmds.setAttr(f"{jnt_tip}.side", 1 if side == "L" else 2)
            cmds.setAttr(f"{jnt}.type", 18)
            cmds.setAttr(f"{jnt_tip}.type", 18)
            jnt_label = utils.strip_suffix_and_prefix(jnt)
            cmds.setAttr(f"{jnt}.otherType", jnt_label, type="string")
            jnt_tip_label = utils.strip_suffix_and_prefix(jnt_tip)
            cmds.setAttr(f"{jnt_tip}.otherType", jnt_tip_label, type="string")

            cmds.delete(cmds.pointConstraint(ctrl, jnt, mo=False))
            cmds.delete(cmds.pointConstraint(jnt, jnt_tip, mo=False))
            jnt_tip_pos = cmds.xform(jnt_tip, query=True, translation=True, worldSpace=True)
            cmds.xform(jnt_tip, translation=(jnt_tip_pos[0], jnt_tip_pos[1], pos[-1]), worldSpace=True)

            cmds.parent(jnt_tip, jnt)
            if index == 0:
                l_aim_jnt = jnt
                cmds.parent(jnt, l_eyeball_joints[0])
            if index == 1:
                r_aim_jnt = jnt
                cmds.parent(jnt, r_eyeball_joints[0])
            cmds.select(clear=True)

        if self.joint_parent:
            cmds.parent(l_eyeball_joints[0], self.joint_parent)
            cmds.parent(r_eyeball_joints[0], self.joint_parent)

        cmds.parent(l_eyeball_joints[-1], l_eyeball_joints[0])
        cmds.parent(r_eyeball_joints[-1], r_eyeball_joints[0])

        return l_eyeball_joints, r_eyeball_joints, l_up_loc, r_up_loc, l_aim_jnt, r_aim_jnt

    def create_joints_around_eye(self, side, high_curves, eyelid_jnt, eyelid_ctrl, up_loc, l_eyelid_ctrl_grp=None):

        if side == "L":
            l_eyelid_ctrl_grp = cmds.group(empty=True, name=f"{side}_eyelidControl_grp")
        if side == "R":
            r_eyelidupper_offsets = []
            r_eyelidupper_controls = []
            r_eyelidlower_offsets = []
            r_eyelidlower_controls = []
            
            r_eyelid_ctrl_grp = cmds.duplicate(l_eyelid_ctrl_grp, name="R_eyelidControl_grp", renameChildren=True)[0]

            cmds.scale(-1, 1, 1, r_eyelid_ctrl_grp, relative=True)
            r_eyelid_children = cmds.listRelatives(r_eyelid_ctrl_grp, allDescendents=True) or []

            new_children_list = []
            for item in r_eyelid_children:
                if "aim" in item:
                    cmds.delete(item)
                elif "scale" in item:
                    cmds.delete(item)
                else:
                    new_children_list.append(item)


            for item in new_children_list:
                if cmds.objExists(item):
                    item_name = item.split("|")[-1]
                    r_item_name = item_name.replace("L_", "R_")
                    pattern = re.compile(r'(?<!0)1$')
                    r_item_name = pattern.sub('', r_item_name)
                    cmds.rename(item, r_item_name)
                    # Identify the type of the child (offset or control) and add it to the respective list
                    if cmds.objectType(r_item_name) == 'transform':
                        if "Upper" in r_item_name and "grp" in r_item_name:
                            r_eyelidupper_offsets.append(r_item_name)
                        if "Upper" in r_item_name and "ctrl" in r_item_name:
                            r_eyelidupper_controls.append(r_item_name)
                        if "Lower" in r_item_name and "grp" in r_item_name:
                            r_eyelidlower_offsets.append(r_item_name)
                        if "Lower" in r_item_name and "ctrl" in r_item_name:
                            r_eyelidlower_controls.append(r_item_name)

            cmds.parent(l_eyelid_ctrl_grp, self.l_eye_rig)
            cmds.parent(r_eyelid_ctrl_grp, self.r_eye_rig)


        for crv in high_curves:
            cvs = cmds.ls(f"{crv}.cv[*]", flatten=True)
            offsets = []
            eyelash_controls = []
            for i in range(len(cvs)):
                cmds.select(clear=True)
                index_str = str(i).zfill(2)
                jnt = cmds.joint(name=crv.replace("High_crv", f"{index_str}_jnt"))
                cmds.select(clear=True)
                jnt_tip = cmds.joint(name=crv.replace("High_crv", f"Tip{index_str}_jnt"))

                cmds.setAttr(f"{jnt}.side", 1 if side == "L" else 2)
                cmds.setAttr(f"{jnt}.type", 18)
                label = utils.strip_suffix_and_prefix(crv)
                label_name = label.replace("High", f"{index_str}_lbl")
                cmds.setAttr(f"{jnt}.otherType", label_name, type="string")

                cmds.delete(cmds.parentConstraint(eyelid_jnt, jnt, mo=False))
                cv_pos = cmds.xform(cvs[i], query=True, translation=True, worldSpace=True)
                cmds.xform(jnt_tip, translation=cv_pos, worldSpace=True)

                if side == "L":
                    control_name = crv.replace("High_crv", f"{index_str}")
                    ctrl_instance = controls.Controls("square", self.scale_factor/12, 13, control_name)
                    ctrl_offset, ctrl = ctrl_instance.create()
                    offsets.append(ctrl_offset)
                    eyelash_controls.append(ctrl)
                    point_on_crv = cmds.createNode("pointOnCurveInfo", name=crv.replace("High_crv", f"{index_str}_pci"))
                    crv_shape = cmds.listRelatives(crv, children=True, shapes=True)[0]
                    cmds.connectAttr(f"{crv_shape}.worldSpace[0]", f"{point_on_crv}.inputCurve")
                    cmds.setAttr(f"{point_on_crv}.parameter", i)
                    cmds.connectAttr(f"{point_on_crv}.position", f"{ctrl_offset}.t")

                if side == "R":
                    if "Upper" in crv:
                        ctrl_offset = r_eyelidupper_offsets[i]
                        ctrl = r_eyelidupper_controls[i]
                        point_on_crv = cmds.createNode("pointOnCurveInfo", name=crv.replace("High_crv", f"{index_str}_pci"))
                        crv_shape = cmds.listRelatives(crv, children=True, shapes=True)[0]
                        mdn = cmds.createNode("multiplyDivide", name=crv.replace("High_crv", f"{index_str}_mdn"))
                        cmds.setAttr(f"{mdn}.input2X", -1)
                        cmds.connectAttr(f"{crv_shape}.worldSpace[0]", f"{point_on_crv}.inputCurve")
                        cmds.setAttr(f"{point_on_crv}.parameter", i)
                        cmds.connectAttr(f"{point_on_crv}.position", f"{mdn}.input1")
                        cmds.connectAttr(f"{mdn}.output", f"{ctrl_offset}.t")

                    if "Lower" in crv:
                        ctrl_offset = r_eyelidlower_offsets[i]
                        ctrl = r_eyelidlower_controls[i]
                        point_on_crv = cmds.createNode("pointOnCurveInfo", name=crv.replace("High_crv", f"{index_str}_pci"))
                        crv_shape = cmds.listRelatives(crv, children=True, shapes=True)[0]
                        mdn = cmds.createNode("multiplyDivide", name=crv.replace("High_crv", f"{index_str}_mdn"))
                        cmds.setAttr(f"{mdn}.input2X", -1)
                        cmds.connectAttr(f"{crv_shape}.worldSpace[0]", f"{point_on_crv}.inputCurve")
                        cmds.setAttr(f"{point_on_crv}.parameter", i)
                        cmds.connectAttr(f"{point_on_crv}.position", f"{mdn}.input1")
                        cmds.connectAttr(f"{mdn}.output", f"{ctrl_offset}.t")

                if i != 0:
                    driver = utils.process_name(ctrl_offset)
                    if side == "L":
                        driven_item = offsets[i-1]
                        driven = utils.process_name(offsets[i-1])
                    if side == "R":
                        if "Upper" in crv:
                            driven_item = r_eyelidupper_offsets[i-1]
                            driven = utils.process_name(r_eyelidupper_offsets[i-1])
                        if "Lower" in crv:
                            driven_item = r_eyelidlower_offsets[i-1]
                            driven = utils.process_name(r_eyelidlower_offsets[i-1])
                    cnst_name = f"{driver}_aim_{driven}"
                    cmds.aimConstraint(ctrl_offset, driven_item, aimVector=[-1,0,0], upVector=[0,1,0], worldUpType="object", wuo=f"{up_loc}", mo=False, name=cnst_name)

                cmds.delete(cmds.parentConstraint(ctrl_offset, jnt_tip, mo=False))

                # Make constraint, delete constraint, freeze transfroms, re-constrain
                ctrl_name = utils.process_name(ctrl)
                jnt_name = utils.process_name(jnt)
                cnst_name_two = f"{ctrl_name}_aim_{jnt_name}"
                cmds.delete(cmds.aimConstraint(ctrl, jnt, aimVector=[0,0,1], upVector=[0,1,0], worldUpType="object", wuo=f"{up_loc}", mo=False, name=cnst_name_two))
                cmds.makeIdentity(jnt, apply=True, translate=True, rotate=True, scale=True)
                cmds.aimConstraint(ctrl, jnt, aimVector=[0,0,1], upVector=[0,1,0], worldUpType="object", wuo=f"{up_loc}", mo=False, name=cnst_name_two)

                # Parent into joint hierarchy
                cmds.parent(jnt_tip, jnt)
                cmds.parent(jnt, eyelid_jnt)

                eyelid_ctrl_name = utils.process_name(eyelid_ctrl)
                jnt_name = utils.process_name(jnt)
                cmds.scaleConstraint(eyelid_ctrl, jnt, mo=True, name=f"{eyelid_ctrl_name}_scale_{jnt_name}")

                if side == "L":
                    # Re-shape the controls using proxy control duplicate
                    ctrl_shape = cmds.listRelatives(ctrl, children=True, shapes=True)[0]
                    duplicate_shape = cmds.duplicate(ctrl_shape)

                    cmds.rotate(0, 90, 0, duplicate_shape, relative=True, objectSpace=True)
                    cmds.scale(1, 0.5, 2, duplicate_shape, relative=True, objectSpace=True)

                    cvs_ctrl = cmds.ls(f"{ctrl_shape}.cv[*]", flatten=True)
                    cvs_duplicate = cmds.ls(f"{duplicate_shape[0]}.cv[*]", flatten=True)

                    for cv_ctrl, cv_dup in zip(cvs_ctrl, cvs_duplicate):
                        pos_dup = cmds.pointPosition(cv_dup, world=True)
                        cmds.move(pos_dup[0], pos_dup[1], pos_dup[2], cv_ctrl, absolute=True, worldSpace=True)

                    cmds.delete(duplicate_shape)

                    cmds.parent(ctrl_offset, l_eyelid_ctrl_grp)
        
        if side == "L":
            return l_eyelid_ctrl_grp
        else:
            return None, None


    def create_eye_aim_left_and_right(self, l_eye_ctrl, r_eye_ctrl, l_settings_shape, r_settings_shape, l_up_loc, r_up_loc, l_aim_jnt, r_aim_jnt):
        main_aim_ctrl_inst = controls.Controls("circle", self.scale_factor, 18, f"eyeAim")
        main_aim_offset, main_aim_ctrl = main_aim_ctrl_inst.create()

        l_aim = eyeAttributes.EyeAim("L", self.l_pupil_vert, l_settings_shape, self.scale_factor, l_eye_ctrl, l_up_loc, l_aim_jnt, l_eye_ctrl, self.l_eye_rig)
        r_aim = eyeAttributes.EyeAim("R", self.r_pupil_vert, r_settings_shape, self.scale_factor, r_eye_ctrl, r_up_loc, r_aim_jnt, l_eye_ctrl, self.r_eye_rig)

        self.l_pupil_ctrl = l_aim.pupil_ctrl
        self.r_pupil_ctrl = r_aim.pupil_ctrl

        cmds.xform(main_aim_offset, translation=(0,l_aim.aim_ctrl_y_pos,l_aim.aim_ctrl_z_pos), worldSpace=True, relative=True)

        for aim_offset in [l_aim.aim_offset, r_aim.aim_offset]:
            main_driver = utils.process_name(main_aim_ctrl)
            aim_driven = utils.process_name(aim_offset)
            cmds.scaleConstraint(main_aim_ctrl, aim_offset,  mo=True, name=f"{main_driver}_scale_{aim_driven}")
            cmds.parentConstraint(main_aim_ctrl, aim_offset, mo=True, name=f"{main_driver}_parent_{aim_driven}")

        return main_aim_offset

    def create_fleshy_eyes(self, l_settings_shape, r_settings_shape, l_offsets, r_offsets, blend_crv):
        cv_positions = []

        cmds.setAttr(f"{l_settings_shape}.upperBlink", 1)
        cmds.setAttr(f"{l_settings_shape}.lowerBlink", 1)
        cmds.setAttr(f"{l_settings_shape}.blinkHeight", -1)

        cv_pos_down = cmds.pointPosition(f"{blend_crv[0]}.cv[7]")
        cv_positions.append(cv_pos_down)

        cmds.setAttr(f"{l_settings_shape}.blinkHeight", 0)
        cv_pos_half = cmds.pointPosition(f"{blend_crv[0]}.cv[7]")
        cv_positions.append(cv_pos_half)

        cmds.setAttr(f"{l_settings_shape}.blinkHeight", 1)
        cv_pos_up = cmds.pointPosition(f"{blend_crv[0]}.cv[7]")
        cv_positions.append(cv_pos_up)

        cmds.setAttr(f"{l_settings_shape}.upperBlink", 0)
        cmds.setAttr(f"{l_settings_shape}.lowerBlink", 0)
        cmds.setAttr(f"{l_settings_shape}.blinkHeight", 0)

        l_pupil_drv_offset, l_pupil_drv = controls.create_driver_grp_and_offset(self.l_pupil_ctrl, "l_eyeFleshyEye")
        driver_name = utils.process_name(self.l_pupil_ctrl)
        driven_name = utils.process_name(l_pupil_drv)
        cmds.delete(cmds.pointConstraint(self.l_pupil_ctrl, l_pupil_drv_offset, mo=False))
        cmds.pointConstraint(self.l_pupil_ctrl, l_pupil_drv_offset, mo=False, name=f"{driver_name}_point_{driven_name}")

        eyeAttributes.FleshyEyes(self.l_eye_lid_ctrls, self.l_offset_jnts, self.r_offset_jnts, l_settings_shape, r_settings_shape, self.scale_factor, l_offsets, r_offsets, l_pupil_drv, self.l_pupil_ctrl, cv_positions)
   
        # cmds.setAttr(f"{l_settings_shape}.upperBlink", 0)
        # cmds.setAttr(f"{l_settings_shape}.lowerBlink", 0)
        # cmds.setAttr(f"{l_settings_shape}.blinkHeight", 0)


#-------------------------------------------------------------------------------------------------------------------------------------    
# Stand alone function to find the mid CV index and the direction of the curve

def find_mid_cv_and_curve_direction(self, curve)
    cvs = cmds.ls(f"{curve}.cv[*]", flatten=True)
    end_index = len(cvs) - 1
    mid_cv = (len(cvs)-1) / 2

    curve_direction = utils.find_curve_direction(curve)

    return mid_cv, curve_direction


#-------------------------------------------------------------------------------------------------------------------------------------    
# Function to position the locators along the upper and lower lids. 
# One mid loc in the centre and two tweak locs

def place_lid_locs(high_curves):
    mid_cv, curve_direction = self.find_mid_cv_and_curve_direction(high_curves[-1])

    upper_lid_locs, lower_lid_locs = self.place_tweak_locs(high_curves, curve_direction)
    self.place_mid_locs(self.high_res_curves, curve_direction, upper_lid_locs, lower_lid_locs, mid_cv)

    return upper_lid_locs, lower_lid_locs


#-------------------------------------------------------------------------------------------------------------------------------------    
# Function to position the locators at each corner of the eyelids

def place_inner_and_outer_locs(pupil_vertex, curve_lower_lid):
    curve_direction = utils.find_curve_direction(curve_lower_lid)

    pupil_pos = cmds.xform(pupil_vertex, query=True, translation=True, worldSpace=True)
    vert_loc = cmds.spaceLocator(name="pupilAimer_loc")[0]
    cmds.xform(vert_loc, translation=pupil_pos, worldSpace=True)

    aimed_at_tangent_locators = []
    placer_locs = []
    aimed_at_loc_locators = []
    helper_components = []

    if curve_direction < 0:
        curve_direction = -1
        inner_point = cmds.pointPosition(f"{curve_lower_lid}.cv[{self.end_index}]", world=True)
        outer_point = cmds.pointPosition(f"{curve_lower_lid}.cv[0]", world=True)
        cv_pivot_inner = 14
        cv_pivot_outer = 0
        
    elif curve_direction > 0:
        curve_direction = 1
        inner_point = cmds.pointPosition(f"{curve_lower_lid}.cv[0]", world=True)
        outer_point = cmds.pointPosition(f"{curve_lower_lid}.cv[{self.end_index}]", world=True)
        cv_pivot_inner = 0
        cv_pivot_outer = 14

    for name, point, pivot in zip(["Inner", "Outer"], [inner_point, outer_point], [cv_pivot_inner, cv_pivot_outer]):
        loc_anchor = cmds.spaceLocator(name=f"L_{name}Anchor_loc")[0]
        cmds.xform(loc_anchor, translation=point, worldSpace=True)
        flat_curve = utils.create_flat_curve_with_same_number_of_cvs(curve_lower_lid)
        flat_curve = cmds.rename(flat_curve, f"L_{name}Flat_crv")
        pivot_position = cmds.pointPosition(f"{flat_curve}.cv[{pivot}]", world=True)
        cmds.xform(flat_curve, rotatePivot=pivot_position, worldSpace=True)
        cmds.delete(cmds.pointConstraint(loc_anchor, flat_curve, mo=False))
        tangent_loc = cmds.spaceLocator(name=f"L_eyelid{name}Tangent_loc")[0]
        cmds.xform(tangent_loc, translation=point, worldSpace=True)
        cmds.delete(cmds.tangentConstraint(flat_curve, tangent_loc, weight=1, aimVector=(curve_direction, 0, 0), upVector=(0, 1, 0), worldUpType="scene"))
        aimed_at_tangent_locators.append(tangent_loc)
        helper_components.extend([loc_anchor, flat_curve])

    cmds.delete(cmds.aimConstraint(vert_loc, aimed_at_tangent_locators[-1], aimed_at_tangent_locators[0], mo=False, weight=1, aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType="scene"))
    cmds.delete(cmds.aimConstraint(vert_loc, aimed_at_tangent_locators[0], aimed_at_tangent_locators[-1], mo=False, weight=1, aimVector=[-1, 0, 0], upVector=[0, 1, 0], worldUpType="scene"))
    
    cmds.delete(vert_loc)

    inner_loc = aimed_at_tangent_locators[0]
    outer_loc = aimed_at_tangent_locators[-1]

    for component in helper_components:
        cmds.delete(component)

    return inner_loc, outer_loc

#-------------------------------------------------------------------------------------------------------------------------------------    
# Creates and positions the tweak locs and returns them

def place_tweak_locs(curves, curve_direction):
    upper_lid_locs = []
    lower_lid_locs = []

    names = ["Tweak00", "Tweak01"]
    
    if curve_direction < 0:
        curve_direction = -1
        paremters = [0.75, 0.25]
        
    elif curve_direction > 0:
        curve_direction = 1
        paremters = [0.25, 0.75]

    for index, (crv, lid) in enumerate(zip(curves, ["Upper", "Lower"])):
        for name, parameter in zip(names, paremters):
            loc = cmds.spaceLocator(name=f"L_{lid}{name}")
            point = cmds.pointOnCurve(crv, pr=parameter, p=True, turnOnPercentage=True)
            cmds.xform(loc, translation=point, worldSpace=True)
            cmds.delete(cmds.tangentConstraint(crv, loc, weight=1, aimVector=(curve_direction, 0, 0), upVector=(0, 1, 0), worldUpType="scene"))
            if index == 0:
                upper_lid_locs.append(loc)
            if index == 1:
                lower_lid_locs.append(loc)

    return upper_lid_locs, lower_lid_locs

#-------------------------------------------------------------------------------------------------------------------------------------    
# Creates and positions the mid locs and returns them

def place_mid_locs(curves, curve_direction, upper_locs, lower_locs, mid_cv):
    mid_locs = []
    
    if curve_direction < 0:
        aim_vector = -1
        
    elif curve_direction > 0:
        aim_vector = 1
    
    for index, (crv, name) in enumerate(zip(curves, ["Upper", "Lower"])):
        mid_loc = cmds.spaceLocator(name=f"L_{name}Mid")
        mid_point = cmds.pointPosition(f"{crv}.cv[{mid_cv}]", world=True)
        cmds.xform(mid_loc, translation=mid_point, worldSpace=True)
        cmds.delete(cmds.tangentConstraint(crv, mid_loc, weight=1, aimVector=(aim_vector, 0, 0), upVector=(0, 1, 0), worldUpType="scene"))
        mid_locs.append(mid_loc)
        if index == 0:
            upper_locs.insert(1, mid_loc)
        if index == 1:
            lower_locs.insert(1, mid_loc)

    cmds.delete(cmds.aimConstraint(mid_locs[0], mid_locs[1], offset=[0, 0, 0], weight=1, aimVector=[0, -(curve_direction), 0], upVector=[0, 0, 1], worldUpType="none", skip=["y"]))
    cmds.delete(cmds.aimConstraint(mid_locs[1], mid_locs[0], offset=[0, 0, 0], weight=1, aimVector=[0, curve_direction, 0], upVector=[0, 0, 1], worldUpType="none", skip=["y"]))

    cmds.delete(cmds.pointConstraint(mid_locs[0], mid_locs[1], skip=["x", "y"]))
    cmds.delete(cmds.geometryConstraint(curves[-1], mid_locs[1]))




if __name__ == "__main__":
    cmds.file(new=True, f=True)
    file_path = "/Users/ericahetherington/Documents/AnimSchool/advanced_rigging/horseFace_mayaProject/scenes/week_2/09_week2_importFileforeEyebrow.ma"

    cmds.file(file_path, 
              i=True, 
              type="mayaAscii", 
              ignoreVersion=True, 
              mergeNamespacesOnClash=False, 
              rpr="09_week2_importFileforeEyebrow", 
              options="v=0;", 
              pr=True, 
              importFrameRate=True, 
              importTimeRange="override", 
              l=False)  # Exclude layers during import

    # pupil_vertex = None

    # joint_parent ="upperFace00_jnt"

    l_upper_edges = ['horse_geo.e[50290]', 'horse_geo.e[50292]', 'horse_geo.e[50294]', 'horse_geo.e[50296]', 'horse_geo.e[50298]', 'horse_geo.e[50300]', 'horse_geo.e[50302]', 'horse_geo.e[50332]', 'horse_geo.e[50334]', 'horse_geo.e[50336]', 'horse_geo.e[50338]', 'horse_geo.e[50340]', 'horse_geo.e[50342]', 'horse_geo.e[50343]']
    l_lower_edges = ['horse_geo.e[50304]', 'horse_geo.e[50306]', 'horse_geo.e[50308]', 'horse_geo.e[50310]', 'horse_geo.e[50312]', 'horse_geo.e[50314]', 'horse_geo.e[50316]', 'horse_geo.e[50318]', 'horse_geo.e[50320]', 'horse_geo.e[50322]', 'horse_geo.e[50324]', 'horse_geo.e[50326]', 'horse_geo.e[50328]', 'horse_geo.e[50330]']

    r_upper_edges = ['horse_geo.e[50346]', 'horse_geo.e[50348]', 'horse_geo.e[50350]', 'horse_geo.e[50352]', 'horse_geo.e[50354]', 'horse_geo.e[50356]', 'horse_geo.e[50358]', 'horse_geo.e[50360]', 'horse_geo.e[50390]', 'horse_geo.e[50392]', 'horse_geo.e[50394]', 'horse_geo.e[50396]', 'horse_geo.e[50398]', 'horse_geo.e[50399]']
    r_lower_edges = ['horse_geo.e[50362]', 'horse_geo.e[50364]', 'horse_geo.e[50366]', 'horse_geo.e[50368]', 'horse_geo.e[50370]', 'horse_geo.e[50372]', 'horse_geo.e[50374]', 'horse_geo.e[50376]', 'horse_geo.e[50378]', 'horse_geo.e[50380]', 'horse_geo.e[50382]', 'horse_geo.e[50384]', 'horse_geo.e[50386]', 'horse_geo.e[50388]']

    eye_inst = Eye(l_upper_edges, l_lower_edges, r_upper_edges, r_lower_edges, joint_parent="upperFace00_jnt", rig_parent="rig_grp")

# cmds.select(l_upper_edges, add=True)

# cmds.select(l_lower_edges, add=True)

# cmds.select(r_upper_edges, add=True)

# cmds.select(r_lower_edges, add=True)

from eyeRigTool.face_rig import FaceRig

import maya.cmds as cmds 
import maya.mel as mel
import maya.api.OpenMaya as om

class EyelidSystem(FaceRig):  
    
    def __init__(self):
        pass
    
    # Beta
    # can be refactor
    # parameter(vertex = selected vertex, center_pos = xform(), aim_vec=(1,0,0), 
    # up_vec=(0,1,0) dir_x = "L/R", dir_y = "up/low",)
    def setup_individual_eyelid(self, vertex, center_pos, tipVertex, aim_vec=(1,0,0), up_vec = (0,1,0),
                     dir_x="L" or "R", dir_y="upper" or "lower"):            
        
        # Function Variable 
        mesh = cmds.polyListComponentConversion(vertex, fv=True)[0]
        center_joints = []
        snap_joints = []
        lowRes_crv_points = []
        eyelid_ctrl = 5
        joint = []
        ctrl_grp = []
        crv_setup = []
        engine_jnt = []
        eyelid_constraint = []
                
        # Create joint
        cntr_joint = self.create_eyelid_joint_from_vertex(vertex, center_pos, dir_x, dir_y)
        center_joints.extend(cntr_joint)
        
        # (Beta)
        # Create Locator from eyeball center pivot 
        if not cmds.objExists("Eye_"+dir_x+"_Up_Loc"):
            eye_aim_up_loc = cmds.spaceLocator(n="Eye_"+dir_x+"_Up_Loc",p=center_pos)[0]
            cmds.xform(cp=1)
            cmds.move(0,10,0,eye_aim_up_loc,r=1,os=1,wd=1)
        
        # Organize System 
        if cmds.objExists("Eyelid_"+dir_x+"_aim_jnt"): 
            lid_setup_grp_name = "Eyelid_"+dir_x+"_aim_jnt"
        else:
            lid_setup_grp_name = cmds.group(n="Eyelid_"+dir_x+"_aim_jnt" , em=1, w=1)
            
        cmds.setAttr("Eyelid_"+dir_x+"_aim_jnt.visibility",0)   # Hide visibility
        
        for i in center_joints:
            cmds.parent(i, lid_setup_grp_name)
            snap_joints.append(cmds.listRelatives(i,c=1)[0])
            
        cmds.xform(lid_setup_grp_name,cp=1)
        
        # Create Engine joints
        for i in snap_joints:
            cmds.select(cl=1)
            jnt = cmds.duplicate(i,n=i.replace("snap","engine"))[0]
            cmds.setAttr(jnt+".segmentScaleCompensate",0)
            cmds.parent(jnt,w=1)
            engine_jnt.append(jnt)
            cmds.pointConstraint(i,jnt,mo=1)
            constraint = cmds.listRelatives(jnt,c=1)
            cmds.parent(constraint,w=1)
            eyelid_constraint.append(constraint)
            
        if not cmds.objExists("Eyelid_"+dir_x+"_Constraint_grp"):
            cmds.group(n="Eyelid_"+dir_x+"_Constraint_grp",em=1,w=1)
        
        for i in eyelid_constraint:
            cmds.parent(i,"Eyelid_"+dir_x+"_Constraint_grp")  
            
        if not cmds.objExists("Eyelid_"+dir_x+"_bindJnt"):
            cmds.group(n="Eyelid_"+dir_x+"_bindJnt",em=1,w=1)
        
        for i in engine_jnt:
            cmds.parent(i,"Eyelid_"+dir_x+"_bindJnt")
            
        # Create Curve
        hiCurve_name = "eyelid_" + dir_x + "_" + dir_y + "_curveSetup_driven" 
        lowCurve_name = "eyelid_" + dir_x + "_" + dir_y + "_curveSetup_driver" 
        lid_locators = self.set_aim_loc(snap_joints,dir_x,"Eye_"+dir_x+"_Up_Loc",aim_vec,up_vec)
        
        lid_locators_pos = self.get_xform_pos(lid_locators)
        
        eyelid_crv_hiRes = self.create_curve_from_pos(hiCurve_name,lid_locators_pos,1,2,self.COLOR_YELLOW)
        crv_setup.append(eyelid_crv_hiRes)
        
        # Curve param drive locator
        self.connect_curve_to_obj(lid_locators,eyelid_crv_hiRes)
        
        # Create low resolution curve 
        max_param = len(lid_locators)-1   # BASED on assumption
        param_value_list = []
        div_count = 0.0
        divisor = eyelid_ctrl - 1 
        
        if max_param<eyelid_ctrl:       # Check low res
            eyelid_ctrl = max_param
            cmds.warning("Eyelid ctrl exceed maximum curve cv, change curve resolution to {0}".format(max_param))
        
        for i in range(eyelid_ctrl):
            divider = div_count/divisor
            param_value_list.append(max_param * divider)
            div_count+=1
    
        for param_value in param_value_list:
            lowRes_crv_points.append(self.get_point_from_param(hiCurve_name,param_value))
        
        eyelid_crv_lowRes = self.create_curve_from_pos(lowCurve_name,lowRes_crv_points,1,2,self.COLOR_RED)
        crv_setup.append(eyelid_crv_lowRes)
    
        # Wire deform from driver to driven
        wire_name = "eyelidCrv_" + dir_x + "_" + dir_y + "_wire"
        wire_node = mel.eval("wire -n {0} -w {1} {2};".format(wire_name,lowCurve_name,hiCurve_name))
        crv_setup.append(eyelid_crv_lowRes+"BaseWire")
        cmds.setAttr(wire_node[0] + ".dropoffDistance[0]", 100)
        
        # Create Main Ctrl Section
        # main ctrl variable
        corner_inner_pos = None
        corner_outer_pos = None
        upper_main_pos = None
        lower_main_pos = None
  
        # Assign all variable      
        if dir_y == "upper":
            upper_main_pos = self.findMiddle(lowRes_crv_points)
            lowRes_crv_points.remove(upper_main_pos)
            
            if len(upper_main_pos) == 2:
                upper_main_pos = self.findMiddle_pos(upper_main_pos[0],upper_main_pos[1])
                lowRes_crv_points.remove(upper_main_pos[0])
                lowRes_crv_points.remove(upper_main_pos[1])
            
            if self.find_inner_or_outer(cmds.xform(tipVertex[0],q=1,ws=1,t=1),
                                        center_pos,dir_x) == "inner":
                corner_inner_pos = cmds.xform(tipVertex[0],q=1,ws=1,t=1)
                corner_outer_pos = cmds.xform(tipVertex[1],q=1,ws=1,t=1)
            else:
                corner_inner_pos = cmds.xform(tipVertex[1],q=1,ws=1,t=1)
                corner_outer_pos = cmds.xform(tipVertex[0],q=1,ws=1,t=1)
                
        
        if dir_y == "lower": 
            lower_main_pos = self.findMiddle(lowRes_crv_points)
            lowRes_crv_points.remove(lower_main_pos)
            
            if len(lower_main_pos) == 2:
                lower_main_pos = self.findMiddle_pos(lower_main_pos[0],lower_main_pos[1])
                lowRes_crv_points.remove(lower_main_pos[0])
                lowRes_crv_points.remove(lower_main_pos[1])
    
            if self.find_inner_or_outer(cmds.xform(tipVertex[0],q=1,ws=1,t=1),
                                        center_pos,dir_x) == "inner":
                corner_inner_pos = cmds.xform(tipVertex[0],q=1,ws=1,t=1)
                corner_outer_pos = cmds.xform(tipVertex[1],q=1,ws=1,t=1)
            else:
                corner_inner_pos = cmds.xform(tipVertex[1],q=1,ws=1,t=1)
                corner_outer_pos = cmds.xform(tipVertex[0],q=1,ws=1,t=1)        
        
        # Dictionary to hold position and name
        main_ctrl_dict = { "eyelidCorner_inner_" + dir_x + "_main_ctrl" : corner_inner_pos,
                    "eyelidCorner_outer_" + dir_x + "_main_ctrl" : corner_outer_pos,
                    "eyelidUpper_" + dir_x + "_main_ctrl" : upper_main_pos,
                    "eyelidLower_" + dir_x + "_main_ctrl" : lower_main_pos,
        }
        
        # Create Control and Joint
        for i in main_ctrl_dict:
            if main_ctrl_dict[i] == None or cmds.objExists(i):
                continue
            
            grp = self.create_ctrl_on_pos(i,main_ctrl_dict[i],color=self.COLOR_RED,width=1.5,shape="circle",scale=0.2)[0]
            ctrlFK = cmds.listRelatives(grp,c=1)[0]
            self.create_extra_group(ctrlFK,"Extra")
            ctrl_grp.append(grp)
            cmds.select(cl=1)
            joint.append(cmds.joint(n=i.replace("ctrl","jnt"),p=main_ctrl_dict[i]))
        
        # Remove used crv points from main ctrl
        del lowRes_crv_points [0]
        del lowRes_crv_points [-1]
        
        # =====================================================================================================================
        upper_inner_pos = None
        upper_outer_pos = None
        lower_inner_pos = None
        lower_outer_pos = None
 
        # Assign all variable      
        if dir_y == "upper":
            if self.find_inner_or_outer(lowRes_crv_points[0],center_pos,dir_x) == "inner":
                upper_inner_pos = lowRes_crv_points[0]
                upper_outer_pos = lowRes_crv_points[1]
            else:
                upper_inner_pos = lowRes_crv_points[1]
                upper_outer_pos = lowRes_crv_points[0]
                
        
        if dir_y == "lower": 
            if self.find_inner_or_outer(lowRes_crv_points[0],center_pos,dir_x) == "inner":
                lower_inner_pos = lowRes_crv_points[0]
                lower_outer_pos = lowRes_crv_points[1]
            else:
                lower_inner_pos = lowRes_crv_points[1]
                lower_outer_pos = lowRes_crv_points[0]  
                    
        # Dictionary to hold position and name
        sec_ctrl_dict = {  "eyelidUpper_inner_" + dir_x + "_sec_ctrl" : upper_inner_pos,
                            "eyelidUpper_outer_" + dir_x + "_sec_ctrl" : upper_outer_pos,
                            "eyelidLower_inner_" + dir_x + "_sec_ctrl" : lower_inner_pos,
                            "eyelidLower_outer_" + dir_x + "_sec_ctrl" : lower_outer_pos,
        }
        
        # Create Control and Joint     
        for i in sec_ctrl_dict:
            if sec_ctrl_dict[i] == None or cmds.objExists(i):
                continue

            grp = self.create_ctrl_on_pos(i,sec_ctrl_dict[i],color=self.COLOR_YELLOW,width=2,scale=0.1)[0]
            ctrlFK = cmds.listRelatives(grp,c=1)[0]
            self.create_extra_group(ctrlFK,"Follow")   
            ctrl_grp.append(grp) 
            cmds.select(cl=1)
            joint.append(cmds.joint(n=i.replace("ctrl","jnt"),p=sec_ctrl_dict[i])) 
            
        return joint, mesh, ctrl_grp, crv_setup
    
    # parameter(joint = all selected joint, mesh, ctrl_grp, crv_setup,center_pos=xform())
    def setup_combined_eyelid(self,joint,mesh,ctrl_grp,crv_setup,center_pos,eye_mesh,mainCV_crv_pos):
        cmds.select(cl=1)
        # Function Variable
        eyelid_ctrl = []
        eyelid_secondary_ctrl = []
        eyelid_main_ctrl = []
        constraint_list = []
        upperCrv_jnt_skin = []
        lowerCrv_jnt_skin = []
        new_crvSetup = []
        eyelid_constraint = []
        
        upper_driver_crv = None
        lower_driver_crv = None
        upper_driven_crv = None
        lower_driven_crv = None
        dir_x = None
        dir_y = None
        
        # Get Driver and Driven crv
        for i in crv_setup:
            if "driver" and "upper" in i:
                if "BaseWire" in i:
                    continue
                upper_driver_crv = i
            if "driver" and "lower" in i:
                if "BaseWire" in i:
                    continue
                lower_driver_crv = i
            if "_lower_curveSetup_driven" in i:
                lower_driven_crv = i
            if "_upper_curveSetup_driven" in i:
                upper_driven_crv = i
        
        # Get upper and inner jnt separately
        for i in joint:
            if "Upper" in i:
                upperCrv_jnt_skin.append(i)
            if "Lower" in i:
                lowerCrv_jnt_skin.append(i)
            if "Corner" in i:
                upperCrv_jnt_skin.append(i)
                lowerCrv_jnt_skin.append(i)
        
        # Bind skin to curve
        if len(upperCrv_jnt_skin) != 2:
            for i in upperCrv_jnt_skin:
                cmds.select(i,add=1)
            cmds.select(upper_driver_crv,add=1)
            cmds.skinCluster(tsb=1,dr=4,bm=0,mi=3)
        
        if len(lowerCrv_jnt_skin) != 2:
            for i in lowerCrv_jnt_skin:
                cmds.select(i,add=1)
            cmds.select(lower_driver_crv,add=1)
            cmds.skinCluster(tsb=1,dr=4,bm=0,mi=3)
        
        # Get ctrl from group
        for i in ctrl_grp:
            lid_ctrl = cmds.listRelatives(i,ad=1)[1]
            eyelid_ctrl.append(lid_ctrl)
            
        # Point constraint
        lidPoint_count = 0
        for i in eyelid_ctrl:
            constraint = cmds.pointConstraint(i,joint[lidPoint_count],mo=1)
            constraint_list.append(constraint)
            lidPoint_count+=1
        
        # Store secondary eyelid ctrl
        for i in eyelid_ctrl:
            if "sec" in i:
                eyelid_secondary_ctrl.append(i)
                
        # Store main eyelid ctrl
        for i in eyelid_ctrl:
            if "main" in i:
                eyelid_main_ctrl.append(i)
                
        # Check what dir_x from name
        if "L" in eyelid_main_ctrl[0]:
            dir_x = "L"
        else:
            dir_x = "R"
            
        # find which secondary
        for i in eyelid_secondary_ctrl:
            
            # Careful this is the most hard coded thing in program
            if "inner" and "Upper" in i:
                dir_y_target = "eyelidUpper_"+dir_x+"_main_ctrl"
                dir_x_target = "eyelidCorner_inner_"+dir_x+"_main_ctrl"
                
            if "outer" and "Upper" in i:
                dir_y_target = "eyelidUpper_"+dir_x+"_main_ctrl"
                dir_x_target = "eyelidCorner_outer_"+dir_x+"_main_ctrl"
                
            if "inner" and "Lower" in i:
                dir_y_target = "eyelidLower_"+dir_x+"_main_ctrl"
                dir_x_target = "eyelidCorner_inner_"+dir_x+"_main_ctrl"  
                
            if "outer" and "Lower" in i:
                dir_y_target = "eyelidLower_"+dir_x+"_main_ctrl"
                dir_x_target = "eyelidCorner_outer_"+dir_x+"_main_ctrl"  
                
            sec_ctrl_attr = self.follow_system(i,dir_y_target,dir_x_target,"translate")  
            cmds.setAttr(sec_ctrl_attr,5)
        
        # duplicate driver curve once, rename and blendshape it
        blink_crv_duplicated = cmds.duplicate(lower_driver_crv)[0]
        blink_crv = blink_crv_duplicated.replace("lower","blink")
        blink_crv = blink_crv.replace("_driver1","")
        
        cmds.rename(blink_crv_duplicated,blink_crv)
        new_crvSetup.append(blink_crv)
        
        blink_BS = self.create_blendshape(blink_crv.replace("curveSetup","BS"),(upper_driver_crv,lower_driver_crv),blink_crv)
        
        # Duplicate all driven_crv and rename
        upper_blink_target_crv_duplicated = cmds.duplicate(upper_driven_crv)[0]
        upper_blink_target_crv = upper_blink_target_crv_duplicated.replace("upper","upBlink")
        upper_blink_target_crv = upper_blink_target_crv.replace("driven1","target")
        cmds.rename(upper_blink_target_crv_duplicated,upper_blink_target_crv)
        new_crvSetup.append(upper_blink_target_crv)
        
        lower_blink_target_crv_duplicated = cmds.duplicate(lower_driven_crv)[0]
        lower_blink_target_crv = lower_blink_target_crv_duplicated.replace("lower","lowBlink")
        lower_blink_target_crv = lower_blink_target_crv.replace("driven1","target")
        cmds.rename(lower_blink_target_crv_duplicated,lower_blink_target_crv)
        new_crvSetup.append(lower_blink_target_crv)
        
        # set blink height and wire accordingly
        # Lower setup
        lower_wire_name = lower_blink_target_crv + "_wire"
        wire_node = mel.eval("wire -n {0} -w {1} {2};".format(lower_wire_name.rpartition("_curveSetup")[0]+"_wire",
        blink_crv,lower_blink_target_crv))
        
        wire_obj = blink_crv.rpartition("blink")[0]+"low"+blink_crv.rpartition("eyelid_"+dir_x+"_")[2] + "BaseWire"
        cmds.rename(blink_crv + "BaseWire",wire_obj)
        
        new_crvSetup.append(wire_obj)
        cmds.setAttr(wire_node[0] + ".dropoffDistance[0]", 100)
        cmds.setAttr(wire_node[0] + ".scale[0]",0)
        
        # Upper setup
        cmds.setAttr(blink_BS+"."+upper_driver_crv,1)
        
        upper_wire_name = upper_blink_target_crv + "_wire"
        wire_node = mel.eval("wire -n {0} -w {1} {2};".format(upper_wire_name.rpartition("_curveSetup")[0]+"_wire",
        blink_crv,upper_blink_target_crv))
        
        wire_obj = blink_crv.rpartition("blink")[0]+"upper"+blink_crv.rpartition("eyelid_"+dir_x+"_")[2] + "BaseWire"
        cmds.rename(blink_crv + "BaseWire",wire_obj)
        
        new_crvSetup.append(wire_obj)
        cmds.setAttr(wire_node[0] + ".dropoffDistance[0]", 100)
        cmds.setAttr(wire_node[0] + ".scale[0]",0)
              
        # Create eyelid curve for eyelid follow by manipulate blink bs and rename the duplicated

        cmds.setAttr(blink_BS+"."+upper_driver_crv,1.5)    
        upperLid_follow_up = cmds.duplicate(upper_blink_target_crv)[0]
        upperLid_follow_up = cmds.rename(upperLid_follow_up,"upperLid_follow_up")
        
        cmds.setAttr(blink_BS+"."+upper_driver_crv,0.3)
        upperLid_follow_down = cmds.duplicate(upper_blink_target_crv)[0]
        upperLid_follow_down = cmds.rename(upperLid_follow_down,"upperLid_follow_down")
        
        cmds.setAttr(blink_BS+"."+upper_driver_crv,0.2)
        lowerLid_follow_up = cmds.duplicate(lower_blink_target_crv)[0]
        lowerLid_follow_up= cmds.rename(lowerLid_follow_up,"lowerLid_follow_up")
        
        cmds.setAttr(eyelid_main_ctrl[-1]+".ty",-0.25)        # index -1 is lower main ctrl(assume method)
        lowerLid_follow_down = cmds.duplicate(lower_driven_crv)[0]
        lowerLid_follow_down = cmds.rename(lowerLid_follow_down,"lowerLid_follow_down")
        cmds.setAttr(eyelid_main_ctrl[-1]+".ty",0)           # Clear attribute
        
        cmds.setAttr(eyelid_main_ctrl[0]+".tx",0.2)
        upperLid_follow_left = cmds.duplicate(upper_driven_crv)[0]
        upperLid_follow_left = cmds.rename(upperLid_follow_left,"upperLid_follow_left")
        
        cmds.setAttr(eyelid_main_ctrl[0]+".tx",-0.2)
        upperLid_follow_right = cmds.duplicate(upper_driven_crv)[0]
        upperLid_follow_right = cmds.rename(upperLid_follow_right,"upperLid_follow_right")
        
        cmds.setAttr(eyelid_main_ctrl[-1]+".tx",0.2)
        lowerLid_follow_left = cmds.duplicate(lower_driven_crv)[0]
        lowerLid_follow_left = cmds.rename(lowerLid_follow_left, "lowerLid_follow_left")
        
        cmds.setAttr(eyelid_main_ctrl[-1]+".tx",-0.2)
        lowerLid_follow_right = cmds.duplicate(lower_driven_crv)[0]
        lowerLid_follow_right = cmds.rename(lowerLid_follow_right,"lowerLid_follow_right")
        
        cmds.setAttr(eyelid_main_ctrl[0]+".tx",0)       # Clear attribute
        cmds.setAttr(eyelid_main_ctrl[-1]+".tx",0)
        
        # create blendshape for eyelid follow
        upper_follow_BS_name = ("eyelid_"+dir_x+"_upper_follow_BS")
        lower_follow_BS_name = ("eyelid_"+dir_x+"_lower_follow_BS")

        eyeLid_Upper_follow_BS = self.create_blendshape(upper_follow_BS_name,(upperLid_follow_up,upperLid_follow_down,
                                                        upperLid_follow_left,upperLid_follow_right),upper_driven_crv)
                                                        
        eyeLid_Lower_follow_BS = self.create_blendshape(lower_follow_BS_name,(lowerLid_follow_up,lowerLid_follow_down,
                                                        lowerLid_follow_left,lowerLid_follow_right),lower_driven_crv)
        
        upper_blink_BS = self.create_blendshape(upper_driven_crv.replace("driven","BS"),upper_blink_target_crv,upper_driven_crv)
        lower_blink_BS = self.create_blendshape(lower_driven_crv.replace("driven","BS"),lower_blink_target_crv,lower_driven_crv)
                                                                                                                
        for i in (upperLid_follow_up,upperLid_follow_down,lowerLid_follow_up,lowerLid_follow_down,
                  upperLid_follow_left,upperLid_follow_right,lowerLid_follow_left,lowerLid_follow_right):   
                    
            cmds.delete(i)                  # Delete bs mesh and cleanup memory
            del i                            
        
        #==================================================================================================================
        # Create Eyeball control and joint then skin it
        eye_ctrl_grp,eye_ctrl = self.create_ctrl_on_pos("eyeball_"+dir_x+"_Ctrl",pos=center_pos,
        color=self.COLOR_CREAM,width=1.7,scale=0.5)
        
        cmds.select(cl=1)
        eye_joint = cmds.joint(n="eyeball_"+dir_x+"_joint",p=center_pos)        
        cmds.parentConstraint(eye_ctrl,eye_joint,mo=1)
        cmds.parent(eye_joint,"Eyelid_"+dir_x+"_bindJnt")
        cmds.select(eye_joint)
        cmds.select(eye_mesh,add=1)
        cmds.skinCluster(tsb=1,dr=4,bm=0,mi=3)
        
        # Move eye cv ctrl and eyelid cv ctrl
        # calculate distance for eye ctrl  (Works if Y is up axis)
        up_eyelid_main_ctrl_dist = cmds.xform("eyelidUpper_"+dir_x+"_main_ctrl",q=1,ws=1,t=1)[2]
        
        for i in range(cmds.getAttr(eye_ctrl+'.spans')+1):
            self.move_cv(eye_ctrl,"z",up_eyelid_main_ctrl_dist+0.25)
            
        for ctrl in eyelid_main_ctrl:
            temp_ctrl_pos = cmds.xform(ctrl,q=1,ws=1,t=1)[2]
            self.move_cv(ctrl,"z",temp_ctrl_pos+0.2)
        
        for ctrl in eyelid_secondary_ctrl:
            temp_ctrl_pos = cmds.xform(ctrl,q=1,ws=1,t=1)[2]
            self.move_cv(ctrl,"z",temp_ctrl_pos+0.2)
        
            
        # Set Driven key eye jnt to follow 
        # For up and down follow
        min_eye_rotX = -25
        max_eye_rotX = 25
        
        eye_jnt_driver_rot_X = ((eye_joint+".rx",0),(eye_joint+".rx",min_eye_rotX),(eye_joint+".rx",max_eye_rotX))
        
        up_Uppercrv_eyelid_follow=((eyeLid_Upper_follow_BS+"."+upperLid_follow_up,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_up,1),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_up,0))
                                  
        up_Lowercrv_eyelid_follow=((eyeLid_Upper_follow_BS+"."+upperLid_follow_down,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_down,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_down,1))
                                  
        down_Uppercrv_eyelid_follow=((eyeLid_Lower_follow_BS+"."+lowerLid_follow_up,0),
                                      (eyeLid_Lower_follow_BS+"."+lowerLid_follow_up,1),
                                      (eyeLid_Lower_follow_BS+"."+lowerLid_follow_up,0))
                                      
        down_Lowercrv_eyelid_follow=((eyeLid_Lower_follow_BS+"."+lowerLid_follow_down,0),
                                      (eyeLid_Lower_follow_BS+"."+lowerLid_follow_down,0),
                                      (eyeLid_Lower_follow_BS+"."+lowerLid_follow_down,1))        
        
        self.set_driven_key(eye_jnt_driver_rot_X,up_Uppercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_X,up_Lowercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_X,down_Uppercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_X,down_Lowercrv_eyelid_follow)
        
        # For left and right follow
        min_eye_rotY = -45
        max_eye_rotY = 45
        
        eye_jnt_driver_rot_Y = ((eye_joint+".ry",0),(eye_joint+".ry",min_eye_rotY),(eye_joint+".ry",max_eye_rotY))
        
        left_Uppercrv_eyelid_follow=((eyeLid_Upper_follow_BS+"."+upperLid_follow_left,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_left,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_left,1))
                                  
        right_Uppercrv_eyelid_follow=((eyeLid_Upper_follow_BS+"."+upperLid_follow_right,0),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_right,1),
                                  (eyeLid_Upper_follow_BS+"."+upperLid_follow_right,0))
                                  
        left_Lowercrv_eyelid_follow=((eyeLid_Lower_follow_BS+"."+lowerLid_follow_left,0),
                                  (eyeLid_Lower_follow_BS+"."+lowerLid_follow_left,0),
                                  (eyeLid_Lower_follow_BS+"."+lowerLid_follow_left,1))
                                  
        right_Lowercrv_eyelid_follow=((eyeLid_Lower_follow_BS+"."+lowerLid_follow_right,0),
                                  (eyeLid_Lower_follow_BS+"."+lowerLid_follow_right,1),
                                  (eyeLid_Lower_follow_BS+"."+lowerLid_follow_right,0))
                                  
        self.set_driven_key(eye_jnt_driver_rot_Y,left_Uppercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_Y,right_Uppercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_Y,left_Lowercrv_eyelid_follow)
        self.set_driven_key(eye_jnt_driver_rot_Y,right_Lowercrv_eyelid_follow)
        
        #===================================================================================================================        
        # Add attr to lid ctrl, connect to corresponding BS
        self.add_attr_separator(eye_ctrl,"FEATURE")
        blink_attr = self.add_attr_float(eye_ctrl,"Blink",0,10)
        eyelid_follow_attr = self.add_attr_float(eye_ctrl,"Eyelid_Follow",0,10)
        blink_height_attr = self.add_attr_float(eye_ctrl,"Blink_Height",0,10)    
        convert_node = self.convert_value(blink_height_attr,blink_BS+"."+upper_driver_crv,0.1)

        self.reverse_value(convert_node+".output",blink_BS+"."+lower_driver_crv)
        self.convert_value(blink_attr,upper_blink_BS+"."+upper_blink_target_crv,0.1)
        self.convert_value(blink_attr,lower_blink_BS+"."+lower_blink_target_crv,0.1)
        
        # Eyelid follow weight to control SDK value
        sdk_node_lidUp_follow_BS = cmds.listConnections(eyeLid_Upper_follow_BS,t="animCurveUU")
        sdk_node_lidLow_follow_BS = cmds.listConnections(eyeLid_Lower_follow_BS,t="animCurveUU")
        
        for i in sdk_node_lidUp_follow_BS:
            cmds.selectKey(i,add=1,k=1,f=(min_eye_rotY,max_eye_rotY))
            cmds.keyTangent(itt="linear",ott="linear")
            convert_node = self.convert_value(eyelid_follow_attr,None,0.1)
            self.blend_weight(i+".output",
                              eyeLid_Upper_follow_BS+"."+i.rpartition(eyeLid_Upper_follow_BS+"_")[2], # Ugly syntax (might fix later)
                              i+"_SDK_BW",
                              convert_node+".output")
            
        for i in sdk_node_lidLow_follow_BS:
            cmds.selectKey(i,add=1,k=1,f=(min_eye_rotY,max_eye_rotY))
            cmds.keyTangent(itt="linear",ott="linear")
            convert_node = self.convert_value(eyelid_follow_attr,None,0.1)
            self.blend_weight(i+".output",
                              eyeLid_Lower_follow_BS+"."+i.rpartition(eyeLid_Lower_follow_BS+"_")[2], # Ugly syntax (might fix later)
                               i+"_SDK_BW",
                              convert_node+".output")
        #def blend_weight(self,source_attr,target_attr,name,weight_attr=None):
            
        # recover attribute to default value
        cmds.setAttr(blink_attr,0)
        cmds.setAttr(eyelid_follow_attr,10)
        cmds.setAttr(blink_height_attr,2)
 
        # CLEANUP  ====================================================================================================
        # Group curve and cleanup outliner
        if not cmds.objExists("Eyelid_"+dir_x+"__Curve_Setup"):
            cmds.group(n="Eyelid_"+dir_x+"__Curve_Setup",em=1,w=1)
            
        for i in crv_setup:
            cmds.parent(i,"Eyelid_"+dir_x+"__Curve_Setup")
            
        for i in new_crvSetup:
            cmds.parent(i,"Eyelid_"+dir_x+"__Curve_Setup")
         
        if not cmds.objExists("EyelidMain_"+dir_x+"_Setup_Joint"): 
            cmds.group(n="EyelidMain_"+dir_x+"_Setup_Joint",em=1,w=1)     
            
        if not cmds.objExists("Eye_"+dir_x+"_Joint_Setup"): 
            cmds.group(n="Eye_"+dir_x+"_Joint_Setup",em=1,w=1)   
            
        cmds.parent("EyelidMain_"+dir_x+"_Setup_Joint","Eye_"+dir_x+"_Joint_Setup")
        
        for i in joint:
            cmds.parent(i,"EyelidMain_"+dir_x+"_Setup_Joint")
            
        if not cmds.objExists(dir_x+"EyeLidCtrl"): 
            cmds.group(n=dir_x+"EyeLidCtrl",w=1,em=1)
        
        for i in ctrl_grp:
            cmds.parent(i,dir_x+"EyeLidCtrl")
            
        # Finalizing cleanup
        if not cmds.objExists("Eyelid_"+dir_x+"_System"):
            cmds.group(n="Eyelid_"+dir_x+"_System",em=1,w=1)
        
        cmds.parent("Eyelid_"+dir_x+"_aim_jnt","Eyelid_"+dir_x+"_System")
        cmds.parent("Eyelid_"+dir_x+"__Curve_Setup","Eyelid_"+dir_x+"_System")
        cmds.parent("Eyelid_"+dir_x+"_loc_aim_grp","Eyelid_"+dir_x+"_System")
        cmds.parent("Eye_"+dir_x+"_Joint_Setup","Eyelid_"+dir_x+"_System")
        cmds.parent("Eye_"+dir_x+"_Up_Loc","Eyelid_"+dir_x+"_System")
            
        # Hide system 
        cmds.setAttr("Eyelid_"+dir_x+"__Curve_Setup.visibility" ,0)
        cmds.setAttr("Eye_"+dir_x+"_Joint_Setup.visibility",0)
        
        # Create master control and setup
        
        mainCV_crv_pos_list = []
        for i in mainCV_crv_pos:
            mainCV_crv_pos_list.append(cmds.xform(i,q=1,ws=1,t=1))
        
        eye_master_ctrl = self.create_curve_from_pos("eyelid_"+dir_x+"_Master_Ctrl",mainCV_crv_pos_list,degree=1,
                                                     width=2.3,color=self.COLOR_CYAN)
        
        degs = cmds.getAttr(eye_master_ctrl+'.degree')
        spans = cmds.getAttr(eye_master_ctrl+'.spans')
        cvs = degs+spans
    
        for i in range(cvs):
            cmds.move(0,0,0.15,eye_master_ctrl+".cv[{0}]".format(i),r=1,os=1,wd=1)
        
        cmds.move(center_pos[0],center_pos[1],center_pos[2],eye_master_ctrl+".scalePivot",eye_master_ctrl+".rotatePivot",a=1)
        
        cmds.parent(eye_ctrl_grp,eye_master_ctrl)
        cmds.parent(dir_x+"EyeLidCtrl",eye_ctrl_grp)
        cmds.parentConstraint(eye_master_ctrl,dir_x+"EyeLidCtrl",mo=1)
        cmds.parentConstraint(eye_master_ctrl,"Eyelid_"+dir_x+"_aim_jnt",mo=1)
        
        cmds.scaleConstraint(eye_master_ctrl,"Eyelid_"+dir_x+"_aim_jnt",mo=1)
        cmds.scaleConstraint(eye_master_ctrl,eye_ctrl_grp,mo=1)
        cmds.scaleConstraint(eye_master_ctrl,eye_joint,mo=1)
        
        constraint = cmds.listRelatives(eye_joint,c=1)
        for i in constraint:
            cmds.parent(i,"Eyelid_"+dir_x+"_Constraint_grp")
        
    # parameter(vertices = cmds.ls(sl=1,fl=1) Flaten!, center = xform(), dir_x = "left/right", dir_y = "up/low")
    def create_eyelid_joint_from_vertex(self, vertex, center, dir_x, dir_y):
        count = 1
        root_joints = []
        
        # Create joint setup according to given vertex 
        for i in vertex:
            cmds.select(cl=1)
            cmds.joint()
            jnt = cmds.rename(cmds.ls(sl=1)[0], "eyelid_"+dir_x+"_"+dir_y+"_snap_jnt"+str(count))
            vertex_pos = cmds.xform(i, q=1, ws=1, t=1)
            cmds.xform(jnt, ws=1, t=vertex_pos)

            cmds.select(cl=1)
            cmds.joint()
            center_jnt = cmds.rename(cmds.ls(sl=1)[0], "eyelid_"+dir_x+"_"+dir_y+"_centerJnt"+str(count))
            cmds.xform(center_jnt, ws=1, t=center)
            cmds.parent(jnt,center_jnt)
            root_joints.append(center_jnt)
            
            # Orient rotation from parent to child joint
            cmds.joint(center_jnt , e=1, zso=1, ch=1, oj ="xyz", sao="yup") 
            count+=1
                        
        return root_joints
        
    # Beta
    # Not yet clean constraint
    # parameter(joints=selected lid jnt(w/o root), dir_x = "left/right", up_obj, 
    # aim_vec = (x, y, z), up_vec = (x, y, z))
    def set_aim_loc(self,joints,dir_x,up_obj,aim_vec,up_vec):
        lid_locator = []
        
        # Beta (unquote below, if head joint available)
        """
        up_vector = cmds.spaceLocator(n = dir_x+"_eyeUpVec_Loc", p = (0,0,0))
        up_vector_grp = cmds.group(n = dir_x+"_eyeUpVec_FollowHead", em=1, w=1)
        """
        
        # Create locator for each joint, and aim constraint
        for i in joints:
            cmds.spaceLocator()
            loc = cmds.rename(cmds.ls(sl=1)[0], i.replace("jnt","Loc"))
            lid_locator.append(loc)
            jnt_pos = cmds.xform(i, q=1, ws=1, t=1)
            cmds.xform(loc, ws=1, t=jnt_pos)
            jnt_parent = cmds.listRelatives(i,p=1)[0]
            
            cmds.aimConstraint(loc, jnt_parent, mo=1, w=1, aim=aim_vec, u=up_vec, wut="object", wuo=up_obj)
        
        # Group all locator and organize
        if cmds.objExists("Eyelid_"+dir_x+"_loc_aim_grp"): 
            loc_group = "Eyelid_"+dir_x+"_loc_aim_grp"
        else:
            loc_group = cmds.group(n="Eyelid_"+dir_x+"_loc_aim_grp",em=1,w=1)
            
        cmds.setAttr("Eyelid_"+dir_x+"_loc_aim_grp.visibility",0)
            
        for i in lid_locator:
            cmds.parent(i,loc_group)
        cmds.xform(loc_group,cp=1)

        return lid_locator
    
    # Beta
    # only connect to translate of target obj
    # parameter(obj = transform node, curve = eyelid setup curve name)
    def connect_curve_to_obj(self,obj,curve):
        for i in obj:
            pos = cmds.xform(i, q=1, ws=1, t=1)
            param = self.get_info_from_crv(curve,pos)[1]    # Get param return -> [1]
            
            # Point on curve info node = PCI
            PCI_name = i.replace("Loc","PCI")
            PCI_node = cmds.createNode("pointOnCurveInfo", n=PCI_name)
            cmds.connectAttr(curve+".worldSpace", PCI_node+".inputCurve")
            cmds.setAttr(PCI_node + ".parameter", param)
            cmds.connectAttr(PCI_node+".position",i+".t")
            
        return PCI_node
            
    # Parameter(crv = curve(transform), point = cv or point in global space)
    def get_info_from_crv(self,crv,pnt):
        point = om.MPoint(pnt[0],pnt[1],pnt[2])
        dag_path = om.MDagPath.getAPathTo(om.MSelectionList().add(crv).getDependNode(0))
        curve = om.MFnNurbsCurve(dag_path)
        closest_pnt,param = curve.closestPoint(point)
        length = curve.findLengthFromParam(param)
        
        return closest_pnt, param, length
    
    def get_point_from_param(self,crv,param):
        dag_path = om.MDagPath.getAPathTo(om.MSelectionList().add(crv).getDependNode(0))
        curve = om.MFnNurbsCurve(dag_path)
        Mpoint = curve.getPointAtParam(param)
        
        x = Mpoint[0]
        y = Mpoint[1]
        z = Mpoint[2]
        point = (x,y,z)
        
        return point
    
    # this only work with default maya axis and might be incorrect if center is 0 on x axis
    # parameter(obj = (x,y,z), center = (x,y,z),dir_x)
    def find_inner_or_outer(self,obj,center,dir_x="L"):
        dir_X_option = ("L","R")
        if dir_x not in dir_X_option:
            cmds.error("Invalid direction type. Expected L or R")
        
        # find distance on y axis
        deviation = center[0] - obj[0]
        
        if dir_x == "L":
            if deviation > 0:
                return "inner"
            elif deviation < 0:
                return "outer"
        
        if dir_x == "R":
            if deviation > 0:
                return "outer"
            elif deviation < 0:
                return "inner"
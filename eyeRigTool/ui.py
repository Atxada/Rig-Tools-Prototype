from eyeRigTool.rig_system import RigSystem
from eyeRigTool.eyelid_system import EyelidSystem

import maya.cmds as cmds 

class UI(RigSystem):
    # DEBUG
    upperLid_vertex = None
    lowerLid_vertex = None
    upperLid_visual_setup = None
    lowerLid_visual_setup = None
    upperLid_tipVertex = None
    lowerLid_tipVertex = None
    eye_mesh_pos = None
    eye_mesh = None
    mainCV_crv_pos = []
    visual_setup = [upperLid_visual_setup, lowerLid_visual_setup,upperLid_vertex,
                    lowerLid_vertex,eye_mesh_pos,eye_mesh,upperLid_tipVertex,
                    lowerLid_tipVertex]
    
    # DEBUG    
    def debug_UI(self,width,height):
    # Check if the window is present
        if cmds.window("DebugUI",ex=1): cmds.deleteUI("DebugUI")

        # Create the window
        window = cmds.window("DebugUI", t="DEBUG", w=200, h =200, mnb=1, mxb=1, cc=self.delete_visual_setup)
        mainLayout = cmds.formLayout(nd=100)

        #All the widget
        # Text

        # TextField
        text_field_1 = cmds.textField("text_field_1",h=25, w=175,fi="",ed=0,bgc=(0.2,0.2,0.2))
        text_field_2 = cmds.textField("text_field_2",h=25, w=175,fi="",ed=0,bgc=(0.2,0.2,0.2))
        text_field_3 = cmds.textField("text_field_3",h=25, w=175,fi="",ed=0,bgc=(0.2,0.2,0.2))
 
        # Button
        generateButton = cmds.button(l="Generate!",c=self.generate_eyelid_setup,h=30,w=100)
        Button_1 = cmds.button(l="Upper Lid Edge",c=self.store_upperLid_vtx,h=25,w=100)
        Button_2 = cmds.button(l="Lower Lid Edge",c=self.store_lowerLid_vtx,h=25,w=100)
        Button_3 = cmds.button(l="Eye Vertices",c=self.store_eye_mesh,h=25,w=100)
        
        # RadioButton
        Direction_Collection = cmds.radioCollection('direction_collection')
        left_rb = cmds.radioButton('left_rb',l = "Left", h =20,cl=Direction_Collection,sl=1)
        right_rb = cmds.radioButton('right_rb',l = "Right", h =20,cl=Direction_Collection)
                
        # CheckBoxes
    
        # adjust layout

        cmds.formLayout (mainLayout,e=1,

        attachForm = [
        (Button_1,"left",10),
        (Button_1,"top",12),
        (Button_2,"left",10),
        (Button_2,"top",42),
        (Button_3,"left",10),
        (Button_3,"top",72),

        (left_rb,"left",70),
        (left_rb,"top",110),
        (right_rb,"left",170),
        (right_rb,"top",110),

        (text_field_1,"top",12),
        (text_field_1,"left",120),
        (text_field_2,"top",42),
        (text_field_2,"left",120),
        (text_field_3,"top",72),
        (text_field_3,"left",120),

        (generateButton,"left",width/2-50),
        (generateButton,"top",140),
        ],
        )
                
        cmds.showWindow(window)
        cmds.window('DebugUI', e=True, wh=(width, height),s=0)
    
    def store_upperLid_vtx(self, *args):        
        # notify user to select edge only
        if cmds.filterExpand(sm=32) == None:
            cmds.warning("please select valid edge loop")
            return
        
        # Update Debug
        if self.upperLid_visual_setup != None:
            try: cmds.delete(self.upperLid_visual_setup)
            except: pass
        
        # get correct vertex list (with edge vertex being first)
        selection = cmds.ls(sl=1,fl=1)
        sel_vertex = cmds.ls(cmds.polyListComponentConversion(selection, toVertex=True),fl=1)
        
        for i in sel_vertex:
            if self.is_vertex_on_edge(i,sel_vertex) == True:
                sel_vertex.remove(i)
                sel_vertex.insert(0,i)
                break
        
        # make vertex ordered, so curve is correct
        ordered_selection = self.order_selection(sel_vertex)
        self.upperLid_vertex = ordered_selection
        cmds.textField("text_field_1",e=1,fi=str(ordered_selection))
        
        # query all vertex and tip vertex
        self.mainCV_crv_pos.append(list(ordered_selection))
        self.upperLid_tipVertex = [ordered_selection[0],ordered_selection[-1]]
        
        # Visual setup
        ordered_selection_pos = self.get_xform_pos(ordered_selection)
        left_rb = cmds.radioButton("left_rb",sl=1,q=1)
        right_rb = cmds.radioButton("right_rb",sl=1,q=1)
        
        if left_rb:
            direction = "L"
        else:
            direction = "R"
        
        if cmds.objExists("DEBUG_CURVE_eyelid_"+direction+"_upper"):
            cmds.delete("DEBUG_CURVE_eyelid_"+direction+"_upper")
            
        debug_crv = self.create_curve_from_pos("DEBUG_CURVE_eyelid_"+direction+"_upper",
        ordered_selection_pos,1,7,self.COLOR_BLACK)
        self.visual_setup.append(debug_crv)
        self.upperLid_visual_setup = debug_crv
        cmds.select(cl=1)

    def store_lowerLid_vtx(self, *args):
        # notify user to select edge only
        if cmds.filterExpand(sm=32) == None:
            cmds.warning("please select valid edge loop")
            return
            
        # Update Debug
        if self.lowerLid_visual_setup != None:
            try: cmds.delete(self.lowerLid_visual_setup)
            except: pass
        
        # get correct vertex list (with edge vertex being first)
        selection = cmds.ls(sl=1,fl=1)
        sel_vertex = cmds.ls(cmds.polyListComponentConversion(selection, toVertex=True),fl=1)
   
        
        for i in sel_vertex:
            if self.is_vertex_on_edge(i,sel_vertex) == True:
                sel_vertex.remove(i)
                sel_vertex.insert(0,i)
                break
        
        # make vertex ordered, so curve is correct
        ordered_selection = self.order_selection(sel_vertex)
        self.lowerLid_vertex = ordered_selection
        cmds.textField("text_field_2",e=1,fi=str(ordered_selection))
        
        # query all vertex and tip vertex
        self.mainCV_crv_pos.append(list(ordered_selection))
        self.lowerLid_tipVertex= [ordered_selection[0],ordered_selection[-1]]
        
        # Visual setup
        ordered_selection_pos = self.get_xform_pos(ordered_selection)
        left_rb = cmds.radioButton("left_rb",sl=1,q=1)
        right_rb = cmds.radioButton("right_rb",sl=1,q=1)
        
        if left_rb:
            direction = "L"
        else:
            direction = "R"
            
        if cmds.objExists("DEBUG_CURVE_eyelid_"+direction+"_lower"):
            cmds.delete("DEBUG_CURVE_eyelid_"+direction+"_lower")
            
        debug_crv = self.create_curve_from_pos("DEBUG_CURVE_eyelid_"+direction+"_lower",
        ordered_selection_pos,1,7,self.COLOR_WHITE)
        
        self.visual_setup.append(debug_crv)
        self.lowerLid_visual_setup = debug_crv
        cmds.select(cl=1)
        
    def store_eye_mesh(self, *args):
        if cmds.filterExpand(sm=31) == None:
            cmds.warning("please select all vertex from one of the eyeball")
            return
        
        # change to face, duplicate eye and center pivot, then delete
        selection = cmds.ls(sl=1,fl=1)
        sel_faces = cmds.ls(cmds.polyListComponentConversion(selection, toFace=True),fl=1)
        eye_mesh = sel_faces[0].rpartition(".f[")[0]
        
        # check if eye skinned
        if self.is_obj_skinned(eye_mesh) == True: 
            cmds.warning("Eye mesh already have skinCluster") 
            return
        
        # Get absolute center by duplicate the eye
        temp_duplicate = cmds.duplicate(eye_mesh)[0]
        
        shape_duplicate = cmds.select(temp_duplicate)          # Get correct shape
        cmds.pickWalk(d="down")
        sel = cmds.ls(sl=1)[0]
        cmds.rename(sel,"temp_atx_Shape")
        
        cmds.polyChipOff(temp_duplicate[:len(sel_faces)], ch=0, kft=1, dup=1, off=0)
        temp_eye_duplicate = cmds.polySeparate(cmds.listRelatives(temp_duplicate,s=1)[0],ch=0,rs=1)[0]
        temp_eye_duplicate = cmds.rename(temp_eye_duplicate,"EYE_PROXY")
        cmds.xform(temp_eye_duplicate,cp=1)
            
        cmds.textField("text_field_3",e=1,fi=eye_mesh)
        self.eye_mesh_pos = cmds.xform(temp_eye_duplicate,q=1,ws=1,sp=1)
        self.eye_mesh = eye_mesh
        cmds.parent(temp_eye_duplicate,w=1)
        cmds.delete(temp_duplicate)
        cmds.delete(temp_eye_duplicate)
        del temp_duplicate
    
    def generate_eyelid_setup(self, *args):
        # Stop the operation if all required field are not filled in
        if self.upperLid_vertex == None or self.lowerLid_vertex == None or self.eye_mesh_pos == None:
            cmds.warning("Some of required fields is not filled in, operation canceled")
            return
            
        # Function variable
        joint_list = []
        mesh_list = []
        ctrl_grp = []
        crv_setup = []
        mainCV_crv_pos_ordered = []
        
        # make correct order for mainCV_crv_pos
        if self.mainCV_crv_pos[0][-1] != self.mainCV_crv_pos[1][0]:
            self.mainCV_crv_pos[1].reverse()
        
        for element in self.mainCV_crv_pos:
            for i in element:
                if i not in mainCV_crv_pos_ordered:
                    mainCV_crv_pos_ordered.append(i)
        
        mainCV_crv_pos_ordered.append(mainCV_crv_pos_ordered[0])   # to close the curve
            
        # Check if curve tip met
        tipVertex = []
        if self.upperLid_tipVertex != None:
            tipVertex.extend(self.upperLid_tipVertex)          
        
        if self.lowerLid_tipVertex != None:
            tipVertex.extend(self.lowerLid_tipVertex)
        
        tipVertex = list(dict.fromkeys(tipVertex))
        
        if len(tipVertex) > 2:
            cmds.error("Both curves are not connected")
        
        left_rb = cmds.radioButton("left_rb",sl=1,q=1)
        right_rb = cmds.radioButton("right_rb",sl=1,q=1)
        
        if left_rb:
            direction = "L"
        else:
            direction = "R"
        
        eyeLid_setup = EyelidSystem()
        
        # Check Duplicate
        obj_to_check = ["Eyeball_"+direction+"_Ctrl_grp","eyelid_"+direction+"_Master_Ctrl_grp",
                        "Eyelid_"+direction+"__Curve_Setup","Eyeball_"+direction+"_joint",
                        "Eyelid_"+direction+"_loc_aim_grp","Eyelid_"+direction+"_aim_jnt",
                        direction+"EyeLidCtrl","Eyelid_"+direction+"_Constraint_grp",
                        "Eyelid_"+direction+"_bindJnt"]
                
        self.check_objExist(obj_to_check)            
                
        if self.upperLid_vertex:
            joint, mesh, grp, crv = eyeLid_setup.setup_individual_eyelid(self.upperLid_vertex,
                                                                                    self.eye_mesh_pos,
                                                                                    tipVertex,
                                                                                    (1,0,0),
                                                                                    (0,1,0),
                                                                                    direction,
                                                                                    "upper")
            joint_list.extend(joint)
            mesh_list.append(mesh)
            ctrl_grp.extend(grp)
            crv_setup.extend(crv)
    
        if self.lowerLid_vertex:
            joint, mesh, grp, crv = eyeLid_setup.setup_individual_eyelid(self.lowerLid_vertex,
                                                                                    self.eye_mesh_pos,
                                                                                    tipVertex,
                                                                                    (1,0,0),
                                                                                    (0,1,0),
                                                                                    direction,
                                                                                    "lower")
            joint_list.extend(joint)
            mesh_list.append(mesh)
            ctrl_grp.extend(grp)
            crv_setup.extend(crv)
        
        # Call setup for combined eyelid
        # refer to first index cause it's the same with second index
        eyeLid_setup.setup_combined_eyelid(joint_list,mesh_list[0],ctrl_grp,crv_setup,self.eye_mesh_pos,
                                            self.eye_mesh,mainCV_crv_pos_ordered) 
        
        # Cleanup
        self.delete_visual_setup()
        cmds.select(cl=1)
        
        
    def delete_visual_setup(self):
        # remove duplicate element in list
        self.visual_setup = list(dict.fromkeys(self.visual_setup))
        #self.proxy_setup = list(dict.fromkeys(self.proxy_setup))
        
        for i in self.visual_setup:
            if i == None:
                continue
            else:
                try: cmds.delete(i)
                except: pass
                
        # Clear list and variable
        self.visual_setup=[]
        self.mainCV_crv_pos = []
        self.upperLid_vertex = None
        self.lowerLid_vertex = None
        self.upperLid_visual_setup = None
        self.lowerLid_visual_setup = None
        self.upperLid_tipVertex = None
        self.lowerLid_tipVertex = None
        self.eye_mesh_pos = None
        self.eye_mesh = None
        
        # just in case there's still leftovers
        ctrl_name_preset = ["DEBUG_CURVE_eyelid_L_upper","DEBUG_CURVE_eyelid_L_lower"]
        
        for i in ctrl_name_preset:
            if cmds.objExists(i):
                cmds.delete(i)
      
        # Empty texxt field to indicate cache are cleaned
        cmds.textField("text_field_1",e=1,fi="") 
        cmds.textField("text_field_2",e=1,fi="") 
        cmds.textField("text_field_3",e=1,fi="") 
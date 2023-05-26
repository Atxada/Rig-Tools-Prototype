#------------------------------------------------------------------------------------------
# RigSystem/Functions
#------------------------------------------------------------------------------------------
import maya.cmds as cmds 
import maya.mel as mel
import maya.api.OpenMaya as om

import os 
import json

class RigSystem():
    
    # current working directory
    #module_path = rig_system.__file__
    module_path = "C:\Users\\atxada\Desktop\Maya Scripts Draft\Storage\Rig Tools\Sources\Private\RigSystem"
    sources_path = module_path.rpartition("Private")[0]
    
    # Color Enum
    COLOR_RED = 13
    COLOR_YELLOW = 17
    COLOR_GREEN = 14
    COLOR_CYAN = 18
    COLOR_BLUE = 6
    COLOR_CREAM = 20
    COLOR_WHITE = 16
    COLOR_BLACK = 1
    
    def  __init__(self):
        pass
    
    # Error (Unusable if obj in world space outliner and already freezed transform)
    # parameter(selection = object, group_name = string)
    def create_extra_group(self, selection, suffix_name):
        cmds.select(selection)
        selection_parent = cmds.pickWalk(d="up")

        if selection_parent[0] == selection: 
            extra_group = cmds.group(n = selection + "_" + suffix_name,w=1,em=1) 
            cmds.matchTransform(extra_group,selection)
            cmds.parent(selection,extra_group)
            return extra_group
        
        else:
            extra_group = cmds.group(n = selection + "_" + suffix_name,w=1,em=1)
            cmds.parent(extra_group,selection_parent)
            self.zero_transform(extra_group)
            cmds.makeIdentity(extra_group)
            cmds.parent(selection,extra_group)
            cmds.select(cl=1)
            return extra_group
        
        print ("Create extra group for {0}".format(selection))
    
    # Beta
    def SystemGroupHierarchy(self, system_group_order):
        if system_group_order == 0:
            system_group_order = "Extra"
        elif system_group_order == 1:
            system_group_order = "Flip"
        elif system_group_order == 2:
            system_group_order = "Global"
        elif system_group_order == 3:
            system_group_order = "Follow"        
        elif system_group_order == 4:
            system_group_order = "Offset"  
        else:
            cmds.error("please specify valid order input")
    
    # this function create extra group for follow so you don't need to
    # parameter(selection=ctrl,follow_target1,follow_target2, 
    # follow_type = "translate"|"rotate"|"translate_and_rotate")
    def follow_system(self,selection,follow_target1,follow_target2,follow_type = "translate_and_rotate"):
        # Beta
        cmds.select(selection)
        
        # Decide follow_type
        if follow_type == "translate_and_rotate":
            attribute_name = "Follow"
            follow_group = self.create_extra_group(selection,attribute_name)
            follow_constraint = cmds.parentConstraint(follow_target2,follow_target1,follow_group,mo=1)[0]
            cmds.setAttr(follow_constraint + ".interpType", 2)
            setrange_name = "_follow_setrange"
            
        elif follow_type == "translate":
            attribute_name = "Follow_Translate"
            follow_group = self.create_extra_group(selection,attribute_name)
            follow_constraint = cmds.parentConstraint(follow_target2,follow_target1,follow_group,
            mo=1,sr=("x","y","z"))[0]
            cmds.setAttr(follow_constraint + ".interpType", 2)
            setrange_name = "_follow_trans_setrange"
            
        else: 
            attribute_name = "Follow_Rotate"
            follow_group = self.create_extra_group(selection,attribute_name)
            follow_constraint = cmds.parentConstraint(follow_target2,follow_target1,follow_group,
            mo=1,st=("x","y","z"))[0]
            cmds.setAttr(follow_constraint + ".interpType", 2)
            setrange_name = "_follow_rot_setrange"
        
        #  Create Follow Attribute
        cmds.addAttr (selection, ln=attribute_name, at="float",dv=0,min=0, max=10)
        cmds.setAttr (selection + ("."+attribute_name),e=1, k=1)

        # connect follow attribute to drive weight constraint
        
        rev_node = cmds.shadingNode("setRange", n=(selection + setrange_name) , au=1 )
        cmds.setAttr(rev_node + ".oldMaxX", 10)
        cmds.setAttr(rev_node + ".oldMaxY", 10)
        cmds.setAttr(rev_node + ".minY", 1)
        cmds.setAttr(rev_node + ".maxX", 1)
        
        cmds.connectAttr(selection+"."+attribute_name, rev_node+".value.valueX")
        cmds.connectAttr(selection+"."+attribute_name, rev_node+".value.valueY")
        cmds.connectAttr(rev_node+".outValue.outValueX",follow_constraint+"."+follow_target1+"W1")
        cmds.connectAttr(rev_node+".outValue.outValueY",follow_constraint+"."+follow_target2+"W0")
        
        cmds.select(cl=1)
        return (selection + "." + attribute_name)
        
    # drivers take list
    # parameter(drivers=[obj_name+attr_name,...], driven = obj_name+attr_name)
    def clamp_multi_input(self,drivers,driven,clamp_min=0,clamp_max=1):
        # check passed argument if it list
        if not isinstance(drivers, list):
            cmds.warning("Only detect one input clamp, skip operation")
            return
            
        # Select all driver first then the driven
        rename_driven = driven.replace(".","_")
        clamp_node_name = rename_driven + "_clamp"
        blendWeight_node_name = rename_driven + "_blendW"
        
        cmds.shadingNode("blendWeighted",n=blendWeight_node_name,au=1)
        cmds.shadingNode("clamp",n=clamp_node_name,au=1)
        
        cmds.setAttr(clamp_node_name + ".minR",clamp_min)
        cmds.setAttr(clamp_node_name + ".maxR",clamp_max)
        
        count = 0
        for i in drivers:
            cmds.connectAttr(i,blendWeight_node_name+".input"+str([count]),f=1)
            count+=1
            
        cmds.connectAttr(blendWeight_node_name+".output",clamp_node_name+".input.inputR",f=1)
        cmds.connectAttr(clamp_node_name+".output.outputR",driven,f=1)
        
        return blendWeight_node_name,clamp_node_name
    
    # parameter(object = selected dag_object)
    def zero_transform(self,object):
        cmds.setAttr(object + ".tx", 0)
        cmds.setAttr(object + ".ty", 0)
        cmds.setAttr(object + ".tz", 0)
        cmds.setAttr(object + ".rx", 0)
        cmds.setAttr(object + ".ry", 0)
        cmds.setAttr(object + ".rz", 0)
    
    # Beta
    # Make sure all argument ordered correctly (top to bottom in hierarchy)!
    # parameter(follow_gr p= list or string, fk_ctrl = list or string, follow_grp_parent = string, 
    # fk_ctrl_parent = list or string, follow_attr = obj_name + attr_name)
    def set_follow_for_fk(self,follow_grp,fk_ctrl,follow_grp_parent,fk_ctrl_parent,follow_attr,max_attr=10):
        offset_fk = []
        offset_follow = []
        constraint_list = []
        count_follow_grp = 0
        count_fk_ctrl = 0
        count_offset_follow = 0
        count_constraint_list = 0
        
        for i in fk_ctrl:
            new_fk_group = self.create_extra_group(i,"connectFollow")
            offset_fk.append(new_fk_group)
            cmds.parent(new_fk_group,fk_ctrl_parent[count_fk_ctrl])
            count_fk_ctrl+=1
            
        for i in follow_grp:
            new_follow_grp = self.create_extra_group(i,"off")
            offset_follow.append(new_follow_grp)
            cmds.parent(new_follow_grp,follow_grp_parent)
            cmds.connectAttr(i+".translate",offset_fk[count_follow_grp]+".translate",f=1)
            cmds.connectAttr(i+".rotate",offset_fk[count_follow_grp]+".rotate",f=1)
            count_follow_grp+=1
        
        # Exclude first offset
        for i in offset_follow[1:]:
            constraint = cmds.parentConstraint(follow_grp[count_offset_follow],fk_ctrl[count_offset_follow],
            i,mo=1)[0]
            cmds.setAttr(constraint + ".interpType", 2)
            constraint_list.append(constraint)
            count_offset_follow+=1
        
        # Switch for follow and fk system
        rename_follow_attr = follow_attr.replace(".","_")
        if cmds.objExists(rename_follow_attr+"_setFK_SR"):
            shading_node = rename_follow_attr + "_setFK_SR"
        else:
            shading_node = cmds.shadingNode("setRange",n=rename_follow_attr+"_setFK_SR",au=1)
            cmds.setAttr(shading_node + ".oldMaxX", max_attr)
            cmds.setAttr(shading_node + ".oldMaxY", max_attr)
            cmds.setAttr(shading_node + ".minY", 1)
            cmds.setAttr(shading_node+ ".maxX", 1)
            cmds.connectAttr(follow_attr, shading_node+".value.valueX")
            cmds.connectAttr(follow_attr, shading_node+".value.valueY")
        
        for i in constraint_list:
            cmds.connectAttr(shading_node+".outValue.outValueX",i+"."+follow_grp[count_constraint_list]+"W0")
            cmds.connectAttr(shading_node+".outValue.outValueY",i+"."+fk_ctrl[count_constraint_list]+"W1")
            count_constraint_list+=1
    
    # HEAVY 
    def are_vertices_connected(self,vertex1, vertex2):
        #basically query all edge that connected to first vertex
        connected_edges = cmds.polyListComponentConversion(vertex1, toEdge=True)
        connected_edges = cmds.filterExpand(connected_edges, sm=32)

        # Check if the second vertex is part of any of the connected edges
        for edge in connected_edges:
            vertices = cmds.polyListComponentConversion(edge, toVertex=True)
            vertices = cmds.filterExpand(vertices, sm=31)
            if vertex2 in vertices:
                return True
            
        return False
        
    # HEAVY 
    # parameter(vertex, all_vertex = list of selected vertex)
    def is_vertex_on_edge(self,vertex, all_vertex):
        connect_count = 0
        
        #basically query all edge that connected to first vertex
        connected_edges = cmds.polyListComponentConversion(vertex, toEdge=True)
        connected_edges = cmds.filterExpand(connected_edges, sm=32)
        cmds.select(cl=1)
        
        # Check if the second vertex is part of any of the connected edges
        for edge in connected_edges:
            vertices = cmds.polyListComponentConversion(edge, toVertex=True)
            vertices = cmds.filterExpand(vertices, sm=31)
            cmds.select(vertices,add=1)
            neighbor_vtx = cmds.ls(sl=1,fl=1)
            
        for vtx in all_vertex:
            if vtx in neighbor_vtx:
                connect_count +=1
                if connect_count == 3:
                    return False
            
        return True

    # Beta(Remember only passing the correct parameter for this to work)
    # Note(this function can remove element in given argument)
    # parameter(selection = vertex selected (cmds.ls(fl=1,os=1))
    def order_selection(self,selection):  
        #print ""
        #print"STARTTTTTTT"
        #print  ""
        selection_initial_length = len(selection)
        connected_vtx=[]
        
        count = 0
        for i in range(len(selection)):
            #print""
            #print "loop number:{0}".format(str(count))
            if len(selection) == 1:
                #print "only one element left in selection, automatically added"
                connected_vtx.append(selection[0])
                selection.remove(selection[0])
                break
            for vtx in selection:
                first_index = selection[0]
                #print""
                #print "current first_index: {0}".format(str(first_index))
                vertex = vtx
                if first_index!=vtx:
                    if self.are_vertices_connected(first_index,vtx):
                        #print "{0} and {1} are connected".format(str(first_index),str(vtx))
                        connected_vtx.append(first_index)
                        #print "APPEND to result! {0}".format(str(first_index))
                        selection.remove(selection[0])
                        selection.remove(vtx)
                        selection.insert(0,vtx)
                    #else:
                        #print "{0} is not connected with {1}".format(first_index,vtx)
                #else:
                    #print "same value detected, {0} with {1} ".format(first_index,vtx)
            count+=1
        
        if len(connected_vtx) != selection_initial_length:
            print connected_vtx
            cmds.warning("some vertices have been excluded, please select clean vertex loop")
    
        return connected_vtx
    
    def do_wire_deform(self, shape, deformCurves, baseCurves):
        count = len(deformCurves)
        wireDef = cmd.wire(shape, wc= count)[0]
        for i in range(count):  
            cmd.connectAttr('%s.worldSpace[0]' % deformCurves[i], '%s.deformedWire[%s]' % (wireDef, i)) 
            cmd.connectAttr('%s.worldSpace[0]' % baseCurves[i], '%s.baseWire[%s]' % (wireDef, i)) 
        cmd.setAttr('%s.rotation' % wireDef, 0)
        
    # Beta
    # parameter(name,vtx=single or multiple xform/(x,y,z),degree,width,color=remember to use enum for easier us)
    def create_curve_from_pos(self,name,pos,degree=1,width=1,color=0):
        curve = cmds.curve(n=name,d=degree,p=pos,k=range(len(pos)))
        cmds.xform(curve,cp=1)
        curveShape = cmds.listRelatives(curve, s=1)[0]
        
        cmds.setAttr(curveShape+".lineWidth",width)
        cmds.setAttr(curveShape+".overrideEnabled",1)
        cmds.setAttr(curveShape+".overrideColor",color)
        
        return curve
    
    # parameter(obj)
    # Note(use translation flag)
    def get_xform_pos(self,obj):
        if isinstance(obj, list):
            obj_xform = []
            
            for i in obj:
                pos = cmds.xform(i, q=1,ws=1,t=1)
                obj_xform.append(pos)
            
            return obj_xform
        else:
            return cmds.xform(obj,q=1,ws=1,t=1)
    
    # Beta 
    # Parameter (name,pos,rot,color,width,shape=ctrl shape you want to create)
    def create_ctrl_on_pos(self,name,pos=(0,0,0),rot=(0,0,0),color=0,width=1,shape="circle",scale=1):
        # Available Ctrl
        """
        -"circle" (default)
        -"arrow_line_cross"
        -"box"
        -"sphere_3D"
        """
        if shape != "circle":
            with open(self.sources_path+"controls.json") as read_file:
                json_file = json.load(read_file)
                
                point = json_file[shape]
                
                if scale != 1:
                    for i in range(len(point)):
                        point[i][0] = point[i][0]*scale
                        point[i][1] = point[i][1]*scale
                        point[i][2] = point[i][2]*scale
                    ctrl = cmds.curve(n=name,d=1,p=point)
                else:    
                    ctrl = cmds.curve(n=name,d=1,p=point)
        else:
            ctrl = cmds.circle(n=name,ch=0)[0]
            if scale!=1:
                for i in range(cmds.getAttr(ctrl+'.spans')):
                    X_CV = cmds.xform(ctrl+".cv[{0}]".format(i),q=1,ws=1,t=1)[0]
                    Y_CV = cmds.xform(ctrl+".cv[{0}]".format(i),q=1,ws=1,t=1)[1]
                    Z_CV = cmds.xform(ctrl+".cv[{0}]".format(i),q=1,ws=1,t=1)[2]
                    cmds.xform(ctrl+".cv[{0}]".format(i),ws=1,t=(X_CV*scale,Y_CV*scale,Z_CV*scale))
            
        group = cmds.group(n=name+"_off",em=1,w=1)
        cmds.parent(ctrl,group)
        
        # Move group on pos and rot
        cmds.xform(group,ws=1,t=pos,ro=rot)
        
        # Change Color if needed
        circleShape = cmds.listRelatives(ctrl, s=1)
        
        for shape in circleShape:
            cmds.setAttr(shape+".lineWidth",width)
            cmds.setAttr(shape+".overrideEnabled",1)
            cmds.setAttr(shape+".overrideColor",color)
        
        return group, ctrl
    
    # source: stackoverflow by Kyle baker 
    def findMiddle(self,input_list):
        middle = float(len(input_list))/2
        if middle % 2 != 0:
            return input_list[int(middle - .5)]         # return element in list
        else:
            return (input_list[int(middle)], input_list[int(middle-1)])     # return tuple between two object
    
    
    # parameter (pos_1 = (x,y,z), pos_2 = (x,y,z))
    def findMiddle_pos(self,pos_1,pos_2):
        center = []

        for i in range(3):
            center.append((pos_1[i]+pos_2[i])/2)
        return center
        
    # parameter (obj to add,name)
    def add_attr_separator(self,obj,name):
        cmds.addAttr(obj, ln=name, at="enum", en="___________:")
        cmds.setAttr(obj+"."+name, e=1, k=0, cb=1)
        
        return obj + "." + name
    
    # you can assign max_value/min_value as false using string
    # parameter (obj to add,name,min_value,max_value)
    def add_attr_float(self,obj,name,min_value,max_value,dv=0):
        if max_value=="False" and min_value=="False":
            cmds.addAttr(obj,ln=name,at="double",dv=dv)
            cmds.setAttr(obj+"."+name,e=1,k=1)       
            return obj + "." + name
            
        elif max_value=="False":
            cmds.addAttr(obj,ln=name,at="double",dv=dv,min=min_value)
            cmds.setAttr(obj+"."+name,e=1,k=1)
            return obj + "." + name
            
        elif min_value=="False":
            cmds.addAttr(obj,ln=name,at="double",dv=dv,max=max_value)
            cmds.setAttr(obj+"."+name,e=1,k=1)
            return obj + "." + name
            
        else:
            cmds.addAttr(obj,ln=name,at="double",dv=dv,max=max_value,min=min_value)
            cmds.setAttr(obj+"."+name,e=1,k=1)
            return obj + "." + name        
    
    # You can pass None to output_attr 
    # parameter (input_attr=name+attr_name,output_attr=name+attr_name,factor=conversion factor)
    def convert_value(self,input_attr,output_attr,factor):
        if output_attr == None:
            node = cmds.shadingNode("unitConversion",au=1,n="UC_"+input_attr.rpartition(".")[2])
        if not output_attr == None:
            node = cmds.shadingNode("unitConversion",au=1,n="UC_"+input_attr.rpartition(".")[2]+"_"+(output_attr.rpartition(".")[2])[:14])
            cmds.connectAttr(node+".output",output_attr,f=1)
        cmds.connectAttr(input_attr,node+".input.",f=1)
        cmds.setAttr(node+".conversionFactor",factor)
        
        return node
    
    # parameter (input_attr,output_attr)
    def reverse_value(self,input_attr,output_attr):
        node = cmds.shadingNode("reverse",au=1,n="Rev_"+input_attr.rpartition(".")[2]+"_"+(output_attr.rpartition(".")[2])[:14])
        cmds.connectAttr(input_attr,node+".inputX",f=1)
        cmds.connectAttr(node+".outputX",output_attr,f=1)
        
        return node
    
    # parameter (name,source=list/single object,target=obj)
    def create_blendshape(self,name,source,target):
        cmds.select(cl=1)
        if isinstance(source, list or tuple):
            for i in source:
                cmds.select(i,add=1)
        else:
            cmds.select(source)
        
        cmds.select(target,add=1)
        return cmds.blendShape(n=name)[0]
    
    # Beta (Unstable)
    # driver attr take 2 level tuple/list and driven also take 2 level tuple
    # parameter (driver_attr=((driver attr name, value),(..)), driven attr=((driven attr name, value),(..))
    def set_driven_key(self,driver_attr,driven_attr):
        for i in range(len(driver_attr)):
            cmds.setAttr(driver_attr[i][0],driver_attr[i][1])
            cmds.setAttr(driven_attr[i][0],driven_attr[i][1])
            cmds.setDrivenKeyframe(driven_attr[i][0],cd=driver_attr[i][0])
            
        # Reset to normal
        cmds.setAttr(driver_attr[0][0],driver_attr[0][1])
    
    # parameter (source_attr = attr_name to connect to input BW, target_attr,name,weight_attr=weight input in BW node)
    def blend_weight(self,source_attr,target_attr,name,weight_attr=None):
        cmds.shadingNode("blendWeighted",n=name,au=1)
        
        source_count = 0
        weight_count = 0
        
        if isinstance(source_attr, list):
            for i in source_attr:
                cmds.connectAttr(i,name+".input"+str[source_count],f=1)
                source_count+=1
        else:
            cmds.connectAttr(source_attr,name+".input[0]",f=1)
        
        if weight_attr != None:
            if isinstance(weight_attr, list):
                for i in weight_attr:
                    cmds.connectAttr(i,name+".weight"+str[weight_count],f=1)
                    weight_count+=1
            else:
                cmds.connectAttr(weight_attr,name+".weight[0]",f=1)
                
        cmds.connectAttr(name+".output",target_attr,f=1)
        
        return name
    
    # Beta(Heavy)(not effective)
    # parameter (obj,axis= x or y or z or (x,y,z) individual, amount = target pos)
    def move_cv(self,obj,axis,amount):
        degs = cmds.getAttr(obj+'.degree')
        spans = cmds.getAttr(obj+'.spans')
        cvs = degs+spans
        
        for i in range(cvs):
            if "x" in axis:
                temp_posY = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[1]
                temp_posZ = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[2]
                temp_posX = cmds.xform(obj+".cv[{0}]".format(i),ws=1,t=(amount,temp_posY,temp_posZ),wd=1)
                temp_posX = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[0]
                
            if "y" in axis:
                temp_posX = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[0]
                temp_posZ = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[2]
                temp_posY = cmds.xform(obj+".cv[{0}]".format(i),ws=1,t=(temp_posX,amount,temp_posZ),wd=1)
                temp_posY = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[1]

            if "z" in axis:
                temp_posX = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[0]
                temp_posY = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[1]
                temp_posZ = cmds.xform(obj+".cv[{0}]".format(i),ws=1,t=(temp_posX,temp_posY,amount),wd=1)
                temp_posZ = cmds.xform(obj+".cv[{0}]".format(i),q=1,ws=1,t=1)[2]
            
    #parameter (obj = can be single or multiple)
    def check_objExist(self,obj):
        if isinstance(obj, list):
            for i in obj:
                if cmds.objExists(i):
                    cmds.error("Duplicated object detected: {0}".format(i))
                    return i
        else:
            if cmds.objExists(obj):
                cmds.error("Duplicated object detected: {0}".format(obj))
                return obj
    
    # source: stackoverflow by theodox
    #parameter (geo)
    def is_obj_skinned(self,geo):
        objHist = cmds.listHistory(geo, pdo=True)
        skinCluster = cmds.ls(objHist, type="skinCluster") or [None]
        cluster = skinCluster[0]
        
        if cluster == None:
            return False
        else:
            return True
        
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
      
class FaceRig(RigSystem):
    
    def __init__(self):
        pass

    # Beta
    # parameter(control = target to be driven by segment joint/list)
    def set_face_segment(self,control):
        for i in control:
            # Create joint based on existing bone face proportion calculation and parent it to control
            pass
 
 # Class notes: tutorial + move and scale whole eye + skin pass + easy user setup to use system  
 # Only work for sphere eye!!!         
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
        
        eye_master_ctrl = self.create_curve_from_pos("eyelid_"+dir_x+"_Master_Ctrl",mainCV_crv_pos_list,
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
        
#argument placeholder
#sel = cmds.ls(fl=1,os=1)
test = EyelidSystem()
test.debug_UI(300,180)
sel = cmds.ls(sl=1,fl=1)
""" Debug Purpose
print str(cmds.ls(sl=1)[0]) + "." + str(cmds.channelBox('mainChannelBox', q=True,selectedMainAttributes=True)[0])
"""

# EXPERIMENT
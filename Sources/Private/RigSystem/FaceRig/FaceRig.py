#------------------------------------------------------------------------------------------
# RigSystem/Functions
#------------------------------------------------------------------------------------------
import maya.cmds as cmds 
import maya.mel as mel
import maya.api.OpenMaya as om

import os 
import json
      
class FaceRig(RigSystem):
    
    def __init__(self):
        pass

    # Beta
    # parameter(control = target to be driven by segment joint/list)
    def set_face_segment(self,control):
        for i in control:
            # Create joint based on existing bone face proportion calculation and parent it to control
            pass

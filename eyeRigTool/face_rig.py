from eyeRigTool.rig_system import RigSystem
      
class FaceRig(RigSystem):
    
    def __init__(self):
        pass

    # Beta
    # parameter(control = target to be driven by segment joint/list)
    def set_face_segment(self,control):
        for i in control:
            # Create joint based on existing bone face proportion calculation and parent it to control
            pass

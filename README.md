## Face Rigging Tools for autodesk maya
### Beta version

**Locate the package folder "eyeRigTool" inside maya environment variable**
>Windows	C:\Users\<Username>\Documents\maya\<version_number> \
>Linux	$HOME/maya/<version_number> \
>macOS	$HOME/Library/Preferences/Autodesk/maya/<version_number> 

Write the following code in the maya script editor\
```
from eyeRigTool import ui
window = ui.UI()
window.debug_UI(300,200)
```

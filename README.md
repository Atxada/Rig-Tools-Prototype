### Face Rigging Tools for autodesk maya (Beta version)

<span style="color:red">
### Face Rigging Tools for autodesk maya (Beta version)
</span>

**Locate the package folder "eyeRigTool" inside maya environment variable**
>Windows	C:\Users\<Username>\Documents\maya\<version_number>\scripts \
>Linux	$HOME/maya/<version_number>/scripts \
>macOS	$HOME/Library/Preferences/Autodesk/maya/<version_number>/scripts 

Write the following code in the maya script editor
```
from eyeRigTool import ui
window = ui.UI()
window.debug_UI(300,200)
```

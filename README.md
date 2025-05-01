# Avatar-XBM-Material-Viewer
A material viewer for James Cameron's Avatar: The Game. Entirely made with AI code. I'm not a coder.

Allows the user to view RGB values, float32 values, integers, etc. Basically see the materials and HEX of what the models use. Stuff like the UV scale, specular power, etc.

This script basically was made mainly for the sole reason of finding the bio/bioluminescent colors of the creatures. Because the game has some materials with "_m" which are mask textures. The bios are also this "_m" masked texture and they need the RGB values to display the correct color for the bio on the creatures, so with this we can properly get all the values for the RGB colors for these creatures. Simply look for the material you want about the creature and look for something like "IlluminationColor1" That should be the Bio color and you should see on the color tab, the RGBA color values easily.

Todo List:

1.Fix RGBA texture viewer

2. Add proper material viewer.

3. Add RGBA texture support. (Currently it has some issue since i didn't tell the AI to add RGBA support.

4. Fix scrolling material list.

5. Fix long freezing/almost crash when loading certain textures.

This script is **SUPER WIP**. Some textures might not display at all, i still need to find the issue/cause of that.

Use:
1. Place the script where you have the xbm files at, it can be in "_materials" or in another folder where you can place xbm files one by one.
1. Simply double click the .py file to turn on the GUI.
3. Locate the folder wherever you extracted the data.pak file to. Essential the root folder where it contains the folder for "graphics" such as "\Data\graphics\_materials"
4. Use the script to view the files/values.
![image](https://github.com/user-attachments/assets/e218d462-7b37-4853-ab49-897b8f6de1bb)
![image](https://github.com/user-attachments/assets/5ddf34de-8eae-470c-b626-52db4cdb9abb)
![image](https://github.com/user-attachments/assets/61993e2a-d127-4a21-a79f-73cf973ec568)
![image](https://github.com/user-attachments/assets/469a7d56-51da-44f6-8223-8572983a4d3a)

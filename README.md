# VACR_Quiz
<h3>https://vacrquiz-pfnbpvqtgumek3nrbfkhql.streamlit.app</h3>
<img src="vacr-quiz.png"></img>
<br><br><br>

<h2>Changelog</h2>
+ Version 2.0 is out!<br>
--> Added category selection in the UI.<br>
--> Added Hotlist Manager Tool.<br>
--> Added Image Manager Tool.<br>
--> Restructured images to the /imgs archive.<br>
--> Restructured hotlists to the /hotlists archive.<br>
--> A few general bugfixes.<br>
--> AI-assistant will be re-implemented in a future release.<br>
+ Version 1.2 build 7: Removed the AI explanations given how now days all their models are payware -.-"<br>
+ Version 1.2 build zero: A few bugfixes, and added AI explanation of wrong answers when you click them at the end of the quiz.<br>
+ Version 1.1 build zero: Ported to streamlit for unified access via any computer and mobile devices. Link: https://vacrquiz-pfnbpvqtgumek3nrbfkhql.streamlit.app/<br>
+ Version 1.0 build zero released for both the VACR and the Hotlist_Manager apps.<br>
<br>
<br>
<h2>VACR Quiz Features</h2>
+ Executable compiled. Version 1.0 build zero released.<br>
+ Randomly picked aircraft models from the hotlist while ensuring every model is iterated at least once before a new pool is generated.<br>
+ Randomly picked aircraft image for that model from the pool of images.<br>
+ Supports the following image formats: ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif".<br>
+ Multiple choices are randomly generated based on the same category of the aircraft presented.<br>
+ Hotlist is selectable from the hotlist database.<br>
+ Difficulty (Speed of image and choice presentation) is selectable.<br>
+ Selectable quantity of aircraft from the hotlist.<br>
+ Selectable multiple choices from 4 to 6.<br>
+ Aircraft images are centered and zoomed to fit the screen in a way that the pixels are soft.<br>
+ At the end of the quiz a rollup of incorrect answers and shown, with the correct answer next to it.<br>
+ Also displays the percentage score at the end.<br>
+ Windows 11 Dark themed.<br>
<br>
<br>
<h2>Hotlist Manager Tool Features</h2>
+ Executable compiled. Version 1.0 build zero released.<br>
+ Import/Export hotlist<br>
+ Add/Remove aircraft<br>
+ Add/Remove aircraft images (up to 26) per each aircraft.<br>
+ Supports the following image formats: ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif".<br>
+ Aircraft images have a thumbnailed preview.<br>
+ Aircraft images can be added by drag & drop.<br>
+ Aircraft image naming conventions are automatically converted.<br>
+ Can edit aircraft name and category.<br>
<br>
<br>
<h2>How to use</h2>
+  Executables located in "dist" folder.<br>
0. There already is a hotlist on file so if you don't want to generate a new one skip to step 10.<br>
1. Open up the hotlist manager tool.<br>
2. Add a new aircraft.<br>
3. Use common nomenclature for naming the aircraft.<br>
4. assign the category of that aircraft.<br>
5. browse the web and download as many images of that aircraft as you want.<br>
6. drag all those images into the list area for the aircraft image (middle pane).<br>
7. Go to step 2 until complete.<br>
8. Export hotlist to the "hotlist" folder.<br>
9. Name your new hotlist.<br>
<br>
10. Open up the VACR quiz app.<br>
11. select your hotlist from the selection field.<br>
12. select how many aircraft you would like to quiz on.<br>
13. select the difficulty.<br>
14. select the amount of multiple choice to be presented for each aircraft.<br>
15. send it.<br>
<br>
<br>
<h2>Known limitations</h2>
+ VACR Quiz does 1 to 50 questions. (TODO: make the default value based on the hotlist entries, max values to 200)<br>
+ Hotlist database is restricted to the "hotlist" folder.<br>
+ Other image types not supported will not work. (TODO: Hotlist Manager tool should auto convert when you add new images _maybe_)<br>
<br>
<br>
<h2>Buglist</h2>
+ The Hotlist_Manager tool creates a copy of the hotlist you import in the "dist" folder, so a user might think they can import and edit and save and it rewrites that hotlist with the changes they made. However, this is not the case. For a user to make changes they would have to import, delete the hotlist they imported from the directory, and then export it as the same name back into that directory. This will be addressed on release 1.1.<br>
<br>
<br>
<h2>Notes</h2>
This is neat little engine. If I generalize the naming conventions of the tools themselves, one could technically use this for ground vehicles, equipment, weapons, etc. Also it works well for throwing some Night Vision and Thermal recognition images.<br>
<br>
<br>
<h2>Developers</h2>
Developer: SGT David "Marty" Martinez <br>
Additional resources, consultation, and verification: SSG Jacob Clark, SSG Dean Evans (Air Defense Artillery Instructors)<br>

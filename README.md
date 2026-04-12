# VACR_Quiz
14P VACR Quiz Project


<h2>VACR Quiz Features</h2>
+ Randomly picked aircraft models from the hotlist while ensuring every model is iterated at least once before a new pool is generated.
+ Randomly picked aircraft image for that model from the pool of images.
+ Supports the following image formats: ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif".
+ Multiple choices are randomly generated based on the same category of the aircraft presented.
+ Hotlist is selectable from the hotlist database.
+ Difficulty (Speed of image and choice presentation) is selectable.
+ Selectable quantity of aircraft from the hotlist.
+ Selectable multiple choices from 4 to 6.
+ Aircraft images are centered and zoomed to fit the screen in a way that the pixels are soft.
+ At the end of the quiz a rollup of incorrect answers and shown, with the correct answer next to it.
+ Also displays the percentage score at the end.
+ Windows 11 Dark themed.
+ Python dependencies included for stand-alone execution.


<h2>Hotlist Manager Tool Features</h2>
+ Import/Export hotlist
+ Add/Remove aircraft
+ Add/Remove aircraft images (up to 26) per each aircraft.
+ Supports the following image formats: ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif".
+ Aircraft images have a thumbnailed preview.
+ Aircraft images can be added by drag & drop.
+ Aircraft image naming conventions are automatically converted.
+ Can edit aircraft name and category.
+ Python dependencies included for stand-alone execution.


<h2>How to use</h2>
1. Open up the hotlist manager tool
2. Add a new aircraft.
3. Use common nomenclature for naming the aircraft.
4. assign the category of that aircraft.
5. browse the web and download as many images of that aircraft as you want.
6. drag all those images into the list area for the aircraft image (middle pane).
7. Go to step 2 until complete.
8. Export hotlist to the "hotlist" folder.
9. Name your new hotlist.

10. Open up the VACR quiz app.
11. select your hotlist from the selection field.
12. select how many aircraft you would like to quiz on.
13. select the difficulty.
14. select the amount of multiple choice to be presented for each aircraft.
15. send it.


<h2>Known limitations</h2>
+ VACR Quiz does 1 to 50 questions. (TODO: make the default value based on the hotlist entries, max values to 200)
+ Hotlist database is restricted to the "hotlist" folder.
+ Other image types not supported will not work. (TODO: Hotlist Manager tool should auto convert when you add new images _maybe_)


<h2>Buglist</h2>
none yet.

<h2>Notes</h2>
This is neat little engine. If I generalize the naming conventions of the tools themselves, one could technically use this for ground vehicles, equipment, weapons, etc. Also it works well for throwing some Night Vision and Thermal recognition images.


Credits:
Coding and initial push: SGT David "Marty" Martinez <br>
Additional resources and consultation: SSG Clark

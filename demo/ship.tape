# vhs tape for the claude-ship /ship demo.
# Render:  vhs demo/ship.tape   ->  produces demo/ship.gif
#
# NOTE: /ship is interactive. Tune the Sleep durations and the approval
# responses (ship / y) to your machine before the final capture.

Output demo/ship.gif

Set FontSize 16
Set Width 1200
Set Height 760
Set Theme "Dracula"
Set Padding 24

Type "claude"
Enter
Sleep 4s

Type `/ship "add a CHANGELOG note for the demo"`
Enter
Sleep 6s

# Approve the plan when /ship shows it.
Type "ship"
Enter
Sleep 8s

# Approve the commit when commit-protocol shows the overview.
Type "y"
Enter
Sleep 5s

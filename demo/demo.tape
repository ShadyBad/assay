# vhs tape — assay self-validation walkthrough.
# Render from the repo root:  vhs demo/demo.tape   ->  demo/assay.gif
#
# This is non-interactive on purpose: it runs the real test + lint suite so the
# GIF shows the plugin validating its own structure, not a staged session.

Output demo/assay.gif

Set FontSize 18
Set Width 1280
Set Height 820
Set Theme "Dracula"
Set Padding 30
Set TypingSpeed 35ms

Type "# assay — a Claude Code plugin that validates its own structure"
Enter
Sleep 1500ms

Type "ls .claude/commands .claude/skills"
Enter
Sleep 2500ms

Type "uv run pytest -q"
Enter
Sleep 4500ms

Type "uv run ruff check ."
Enter
Sleep 3000ms

Type "# 62 structure tests + lint, green. drift fails CI."
Enter
Sleep 2500ms

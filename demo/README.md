# Demo assets

`claude-ship.gif` (shown in the top-level README) is a recorded walkthrough of
the plugin validating its own structure — the real test + lint suite running
green. It is non-interactive on purpose: it demonstrates the repo's rigor
without staging a fake session.

## Recording

Captured with [vhs](https://github.com/charmbracelet/vhs), which renders a
terminal session from a declarative tape file.

```bash
# install vhs (macOS): brew install vhs
vhs demo/demo.tape          # writes demo/claude-ship.gif
```

Run it from the repo root so `uv run pytest` resolves the project. Tune the
`Sleep` durations to your machine's `uv` startup latency before the final
capture.

## A live /ship recording

To add a GIF of the interactive `/ship` pipeline itself, record a real session
with [asciinema](https://asciinema.org/) (which captures interactive input
cleanly) and convert with [agg](https://github.com/asciinema/agg):

```bash
asciinema rec demo/ship.cast   # run /ship inside, then exit
agg demo/ship.cast demo/ship.gif
```

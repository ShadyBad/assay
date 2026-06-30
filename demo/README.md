# Demo assets

This directory holds the recorded demo of `/ship` shown in the top-level README.

## Recording the GIF

The demo is captured with [vhs](https://github.com/charmbracelet/vhs), which
renders a terminal session from a declarative tape file.

```bash
# install vhs (macOS): brew install vhs
vhs demo/ship.tape          # writes demo/ship.gif
```

`ship.tape` is a starting point. Because `/ship` is interactive (it pauses for
plan approval, commit approval, and push), the tape's `Sleep` durations and the
`ship` / `y` responses need tuning to your machine's latency before the capture
looks clean. Record against a throwaway task so the pipeline has something real
to run.

## Alternative: asciinema

For an embeddable, copy-pasteable cast instead of a GIF:

```bash
asciinema rec demo/ship.cast
# run /ship inside the recording, then exit
```

Once `ship.gif` exists, embed it in the top-level README under the Demo section.

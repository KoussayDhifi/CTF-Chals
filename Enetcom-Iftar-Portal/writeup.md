## Intoduction

This medium web exploitation challenge requires an attack chain with two steps

1. Detect LFI
2. Craft JWT Token


## Ivestigation

The website is basically a simple portal that you access by logging in and creating an account if you don't have one.

You have simple inputs only username and password for both pages.

If you are not the admin the website will just show you an interface with a hint indicating that you need to look for a text file using the page variable within the URL like `?page=welcome.txt` and when you navigate there you can see that it shows the content of each file.

## First Chain : LFI

Accessing a file from the file system should hint that it is an LFI vulnerability and from the description you can understand that there are some parts of old infrastructure are still left there you can see what well-known files exist like config files and one of those files are *.evn*.
.
So if you search for `?page=../.env` you can see that the content of the file is a JWT secret `SECRET_JWT=never_gonna_give_you_up` and from there you can get admin access (which is the goal of the challenge) by forgin JWT token.

## Second Chain : Forge admin JWT

If you use burpsuite and intercept the traffic when logging in you can see in the cookies section a field called Authorization that has the structure of : Bearer <token>

![ImageBurpSuite](ImagesWriteup/Pasted%20image.png)

And if you decode this JWT token using for example **jwt.io** you can find that this is the structure of the header is

```js

{
  "alg": "HS256",
  "typ": "JWT"
}

```

and the structure of the payload is

```js
{
  "user": "Name",
  "role": "user",
  "exp": 1769424239
}
```

And with that you can forge a JWT token since you have the JWT secret from the LFI (use jwt.io to forge better)

By just changing the role into the payload into `admin` like this 

```js
{
  "user": "Name",
  "role": "admin",
  "exp": 1769424239
}
```

![ForgeToken](ImagesWriteup/Pasted%20image%20(2).png)

Then After you get your forget JWT token you can use the repeater in burpsuite and change the authorization field JWT token into the new forged-token and with that you get the flag.

![Repeater](ImagesWriteup/Pasted%20image%20(3).png)
![Repeater](ImagesWriteup/Pasted%20image%20(4).png)

And with that you get the flag


## Conclusion

1. Find .env file
2. Craft your JWT token
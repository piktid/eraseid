<p align="center">
  <img src="https://id.piktid.com/logo.svg" alt="EraseID by PiktID logo" width="150">
  </br>
  <h3 align="center"><a href="[https://id.piktid.com](https://id.piktid.com)">EraseID by PiktID</a></h3>
</p>


# EraseID
[![Official Website](https://img.shields.io/badge/Official%20Website-piktid.com-blue?style=flat&logo=world&logoColor=white)](https://piktid.com)
[![Discord Follow](https://dcbadge.vercel.app/api/server/FJU39e9Z4P?style=flat)](https://discord.com/invite/FJU39e9Z4P)

EraseID is an AI face anonymizer. 
It automatically replaces faces in existing images, instead of blurring or pixelating. The aim is to keep the image aesthetics while protecting privacy and complying with the data protection laws.

[![How does EraseID work?](http://i3.ytimg.com/vi/Ts9DqHTwYn0/hqdefault.jpg)](https://www.youtube.com/watch?v=Ts9DqHTwYn0)


## About
EraseID utilizes generative models to intelligently create real-looking synthetic humans that perfectly fit your photos. It can be extremely useful for:

- <ins>Enterprises</ins>: Expand your portfolio and add diversity. Unique high-resolution face replacement and editing. Enhanced variety for stock photos. No model release needed for commercial use.
- <ins>Marketing</ins>: Customize models and fit them to any market. Adapt models for targeted campaigns worldwide. Use photos without model release for commercial purposes. Retarget advertising photos for specific groups. 
- <ins>Graphic designers</ins>: Enhance your creativity with AI-generated faces. Easy face retouching. Unique faces and expressions. Speed up work.
- <ins>Photographers</ins>: Edit models with the help of AI. Diversify the portfolio. Adapt faces to customers’ needs.

## Getting Started
<a target="_blank" href="https://colab.research.google.com/drive/1dAAswUw9M3h8NAcHJ-ty_-WD6jDrSnwD">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

The following instructions suppose you have already installed a recent version of Python. For a general overview, please visit the <a href="https://api.piktid.com/docs">API documentation</a>.
To use any PiktID API, an access token is required. 

> **Step 0** - Register <a href="https://id.piktid.com">here</a>. 10 credits are given for free to all new users.

> **Step 1** - Clone the EraseID library
```bash
# Installation commands
$ git clone https://github.com/piktid/eraseid.git
$ cd eraseid
$ pip install -r requirements.txt
```

> **Step 2** - Export the email and password as environmental variables
```bash
$ export ERASEID_EMAIL={Your email here}
$ export ERASEID_PASSWORD={Your password here}
```

> **Step 3** - You can either provide the URL or the absolute path of the image (containing people). Add the arguments
```python
...
--url 'your-url'
or
--filepath 'mydir/myfile.jpg'
...
```

> **Step 4** - Run the main function
```bash
$ python3 main.py --url 'your-url'
```

Without any additional argument, EraseID only changes the first face it finds in your image, and provides the result asynchronously. 
If you want to change also the hair, change all the faces in the photo and call the server synchronously, use the following command:

```bash
$ python3 main.py --hair --all_faces --sync
```

## Consistent identity (premium feature)
It is now possible to use the same generated identity in multiple photos! 
To save the generated identity into your database, use the command:

```bash
$ python3 main.py --store_identity
```

The identity will be stored as 'pippo'. The name is hard-coded but you can change it.
If you want to reuse 'pippo' in different photos, use the command:

```bash
$ python3 main.py --identity_name 'pippo'
```

Different face enhancers are available, at the moment GFPGAN starts as default.

## Contact
office@piktid.com

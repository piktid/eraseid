<p align="center">
  <img src="https://id.piktid.com/logo.svg" alt="EraseID by PiktID logo" width="150">
  </br>
  <h3 align="center"><a href="[https://studio.piktid.com](https://studio.piktid.com)">EraseID by PiktID</a></h3>
</p>


# EraseID - v3.1.0
[![Official Website](https://img.shields.io/badge/Official%20Website-piktid.com-blue?style=flat&logo=world&logoColor=white)](https://piktid.com)
[![Discord Follow](https://dcbadge.vercel.app/api/server/FJU39e9Z4P?style=flat)](https://discord.com/invite/FJU39e9Z4P)

EraseID is an AI face changer and anonymizer. 
It automatically changes and replaces faces in existing images based on users' inputs, enabling full control of all human identities.

[![How does EraseID work?](http://i3.ytimg.com/vi/REQsqVu-L7I/hqdefault.jpg)](https://www.youtube.com/watch?v=REQsqVu-L7I)


## About
EraseID utilizes generative models to intelligently create real-looking synthetic humans that perfectly fit your photos. It can be extremely useful for:

- <ins>Enterprises</ins>: Expand your portfolio and add diversity. Unique high-resolution face replacement and editing. Enhanced variety for stock photos. No model release needed for commercial use.
- <ins>Marketing</ins>: Customize models and fit them to any market. Adapt models for targeted campaigns worldwide. Use photos without model release for commercial purposes. Retarget advertising photos for specific groups. 
- <ins>Graphic designers</ins>: Enhance your creativity with AI-generated faces. Easy face retouching. Unique faces and expressions. Speed up work.
- <ins>Photographers</ins>: Edit models with the help of AI. Diversify the portfolio. Adapt faces to customers' needs.

## Getting Started - Random identity
[![Colab Notebook](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1dAAswUw9M3h8NAcHJ-ty_-WD6jDrSnwD)


The following instructions suppose you have already installed a recent version of Python. For a general overview, please visit the <a href="https://api.piktid.com/docs">API documentation</a>.
To use any PiktID API, an access token is required. 

> **Step 0** - Register <a href="https://studio.piktid.com">here</a>. 10 credits are given for free to all new users.

> **Step 1** - Clone the EraseID library
```bash
# Installation commands
$ git clone https://github.com/piktid/eraseid.git
$ cd eraseid
```

> **Step 2** - Export the email and password as environmental variables. If you want to authenticate via token, check the colab implementation.
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
If you want to change also the hair and change all the faces in the photo, use the following command:

```bash
$ python3 main.py --hair --all_faces
```

You can fine-tune the generation process using the following parameters:
- `--guidance_scale`: Float value between 1 and 20 that controls the guidance scale
- `--prompt_strength`: Float value between 0 and 1 that controls the diversity of generated faces
- `--var_strength`: Float value between 0 and 1 that controls the creativity of generated faces
- `--controlnet_scale`: Float value between 0 and 2 that controls the conditioning scale
- `--seed`: Integer value for generation seed (default: random between 1 and 1000000)

For example, for a more creative generation, you can use:
```bash
$ python3 main.py --hair --all_faces --prompt_strength 0.8 --var_strength 0.8
```

## Change facial expression
[![Colab Notebook](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1d6YT3pt7M4bacAgy0zdr-qYjS57KymLw?usp=sharing)
[![Notion Guide](https://img.shields.io/badge/Notion-Visit%20Page-blue?style=flat)](https://piktid.notion.site/EraseID-Change-Expression-API-Quick-Start-Guide-18162b3ad01f8012b982f383ee0bc3d1)


It is possible to edit the original identity in your photos! Use keywords to add open closed eyes, add a smile or create a surprised look on all the faces.
Choose the EXPRESSION value from the ones available in `cfe_keywords.py`

```bash
$ python3 main.py --all_faces --change_expression_flag --new_expression EXPRESSION
```

## Consistent identity (swap generated faces)
It is also possible to use the same generated identity in multiple photos! 
To save the generated identity into your database, use the command:

```bash
$ python3 main.py --store_identity
```

The identity will be stored as 'pippo'. The name is hard-coded but you can change it.
If you want to reuse 'pippo' in different photos, use the command:

```bash
$ python3 main.py --identity_name 'pippo'
```

## Consistent identity (swap real faces, see [SwapID](https://github.com/piktid/swapid))
[![Colab Notebook](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1N_PMMvNJV9UnfRP3p8hFBpGMgv_qYXHL?usp=sharing)

It is also possible to use the same real identity from a source image into multiple target photos. We *recommend* to visit [SwapID](https://studio.piktid.com/swap) for this particular use case. Since SwapID utilizes the EraseID infrastructure, the results should be identical.
To use a real identity from a source photo with local path 'mydir/myfile.jpg', use the command:

```bash
$ python3 main.py --filepath 'mydir/myfile.jpg' --identity_filepath 'mydir/myfile.jpg' --identity_name 'myidentityname'
```

The identity will be stored as 'myidentityname' and it will be used as reference input for the target image 'mydir/myfile.jpg'

If you want to swap also the hair and use an identity located at 'mylink/myfile.jpg', use the command
```bash
$ python3 main.py --filepath 'mydir/myfile.jpg' --identity_url 'mylink/myfile.jpg' --identity_name 'myidentityname' --hair
```

It is possible to change the default consistent generation parameters, to do that use the command
```bash
$ python3 main.py --filepath 'mydir/myfile.jpg' --identity_filepath 'mydir/myfile.jpg' --identity_name 'myidentityname' --prompt_strength 0.55 --seed 0
```

## Full-body skin generation
It is now possible to automatically generate coherent full-body skin for the newly generated face! It is particularly useful when generating different ethnicities. 

```bash
$ python3 main.py --skin
```

## Contact
office@piktid.com

import os
import copy
import time
import json
import base64
import requests
from time import sleep
from io import BytesIO
from requests_toolbelt import MultipartEncoder
from PIL import Image, ImageFile, ImageFilter, ImageCms


## -----------READ/WRITE FUNCTIONS------------
def open_image_from_url(url):
    response = requests.get(url, stream=True)
    if not response.ok:
        print(response)

    image = Image.open(BytesIO(response.content))
    return image

def open_image_from_path(path):
    f = open(path, 'rb')
    buffer = BytesIO(f.read())
    image = Image.open(buffer)
    return image

    return BytesIO(response.content)

def im_2_B(image):
    # Convert Image to buffer
    buff = BytesIO()

    if image.mode == 'CMYK':
        image = ImageCms.profileToProfile(image, 'ISOcoated_v2_eci.icc', 'sRGB Color Space Profile.icm', renderingIntent=0, outputMode='RGB')

    image.save(buff, format='PNG',icc_profile=image.info.get('icc_profile'))
    img_str = buff.getvalue()
    return img_str

def im_2_buffer(image):
    # Convert Image to bytes 
    buff = BytesIO()

    if image.mode == 'CMYK':
        image = ImageCms.profileToProfile(image, 'ISOcoated_v2_eci.icc', 'sRGB Color Space Profile.icm', renderingIntent=0, outputMode='RGB')

    image.save(buff, format='PNG',icc_profile=image.info.get('icc_profile'))
    return buff

def b64_2_img(data):
    # Convert Base64 to Image
    buff = BytesIO(base64.b64decode(data))
    return Image.open(buff)
    
def im_2_b64(image):
    # Convert Image 
    buff = BytesIO()
    image.save(buff, format='PNG')
    img_str = base64.b64encode(buff.getvalue()).decode('utf-8')
    return img_str


## -----------PROCESSING FUNCTIONS------------
def start_call(email, password):
    # Get token

    URL_API = 'https://api.piktid.com/api'

    print(f'Logging to: {URL_API}')

    response = requests.post(URL_API+'/tokens', data={}, auth=(email, password))
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token':ACCESS_TOKEN, 'refresh_token':REFRESH_TOKEN, 'url_api':URL_API}


def refresh_call(TOKEN_DICTIONARY):
    # Get token using only access and refresh tokens, no mail and psw
    URL_API = TOKEN_DICTIONARY.get('url_api')
    response = requests.put(URL_API+'/tokens', json=TOKEN_DICTIONARY)
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token':ACCESS_TOKEN, 'refresh_token':REFRESH_TOKEN, 'url_api':URL_API}

# UPLOAD
def upload_and_detect_call(src_img, HAIR_FACTOR, TOKEN_DICTIONARY):
    # upload the image into PiktID's servers
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    src_img_B = im_2_buffer(src_img)

    options = '1'
    m = MultipartEncoder(
    fields={'options': options, 'flag_hair': str(HAIR_FACTOR), 'flag_sync': '1',
            'file': ('file', src_img_B, 'text/plain')}
    )
    
    response = requests.post(URL_API+'/upload', 
                            headers={
                                      'Content-Type': m.content_type,
                                      'Authorization': 'Bearer '+TOKEN},
                            data=m,
                            )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/upload', 
            headers={
                'Content-Type': m.content_type,
                'Authorization': 'Bearer '+TOKEN
            },
            data=m,
        )
    # if no faces, 405 error
    response_json = json.loads(response.text)

    image_address = response_json.get('image_id') # image id
    faces_dict = response_json.get('faces') # faces dictionary
    indices_info = faces_dict.get('coordinates_list')
    selected_faces_list = faces_dict.get('selected_faces') # faces that can be modified
    number_of_faces = faces_dict.get('number_of_faces') # information about the number of faces

    return image_address, indices_info, selected_faces_list

def upload_reference_face_call(src_img, identity_name, TOKEN_DICTIONARY):
    # upload the image into PiktID's servers
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    src_img_B = im_2_buffer(src_img)

    m = MultipartEncoder(
    fields={'identity_name': identity_name, 'file': ('file', src_img_B, 'text/plain')})

    response = requests.post(URL_API+'/upload_identity',
                            headers={"Content-Type": m.content_type,
                                     'Authorization': 'Bearer '+TOKEN},
                            data=m,
                            )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/upload_identity',
                            headers={"Content-Type": m.content_type,
                                     'Authorization': 'Bearer '+TOKEN},
                            data=m,
                            )
    print(response.content)
    response_json = json.loads(response.text)
    return response_json

# SELECT FACES
def selection_call(image_id, selected_faces_list, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/selection',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={'flag_sync':True,'id_image': image_id,'selected_faces':selected_faces_list},
                            #timeout=100,
                            )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/selection',
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'flag_sync':True,'id_image': image_id,'selected_faces':selected_faces_list},
            #timeout=100,
        )
    response_json = json.loads(response.text)
    keywords_list = response_json.get('frontend_prompt')

    return keywords_list

# GET SAVED IDENTITIES
def get_identities_call(TOKEN_DICTIONARY):
    # get the list of identities available in the account
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/get_identities', 
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={})
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/get_identities', 
            headers={'Authorization': 'Bearer '+TOKEN},
            json={}
        )

    response_json = json.loads(response.text)
    identities_list = [d['n'] for d in response_json if 'n' in d]

    return identities_list

# GENERATE NEW FACES
def update_data_generation_call(data, PARAM_DICTIONARY):
    # update the json data first

    GUIDANCE_SCALE = PARAM_DICTIONARY.get('GUIDANCE_SCALE')
    PROMPT_STRENGTH = PARAM_DICTIONARY.get('PROMPT_STRENGTH')
    CONTROLNET_SCALE = PARAM_DICTIONARY.get('CONTROLNET_SCALE')
    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')

    if GUIDANCE_SCALE is not None:
        data.update({'guidance_scale':GUIDANCE_SCALE})
        
    if PROMPT_STRENGTH is not None:
        data.update({'prompt_strength':PROMPT_STRENGTH})

    if CONTROLNET_SCALE is not None:
        data.update({'controlnet_scale':CONTROLNET_SCALE})

    if IDENTITY_NAME is not None:
        extra_data = {'identity_name': IDENTITY_NAME}
        data.update(extra_data)

    return data

def generation_call(image_address, idx_face, prompt, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    SEED = PARAM_DICTIONARY.get('SEED') 

    data = {'id_image': image_address,'id_face': idx_face, 'prompt': prompt, 'seed':SEED}
    data = update_data_generation_call(data, PARAM_DICTIONARY)
    print(f'data to send to generation: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/ask_generate_faces',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json=data,
                            )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/ask_generate_faces',
            headers={'Authorization': 'Bearer '+TOKEN},
            json=data,
        )
    response_json = json.loads(response.text)
    return response_json

# GET NEW FACES
def get_generated_faces(id_image, id_face, TOKEN_DICTIONARY):
    # get list of generated faces - to call after completion of 'generation_call'
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/generated_faces',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={'id_image': id_image, 'id_face': id_face},
    )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/generated_faces',
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'id_image': id_image, 'id_face': id_face},
        )

    response_json = json.loads(response.text)
    return response_json

def get_last_generated_face(list_of_generated_faces, idx_face):
    number_of_generations = len(list_of_generated_faces)
    if (number_of_generations==0):
        return False
    return list_of_generated_faces[number_of_generations-1].get('g')


# SAVE NEW FACES AS NEW IDENTITIES
def set_identity_call(image_address, idx_face, idx_generation, prompt, identity_name, TOKEN_DICTIONARY):
    # save the generated identity in the user profile for future use
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    response = requests.post(URL_API+'/set_identity', 
                        headers={'Authorization': 'Bearer '+TOKEN},
                        json={'id_image': image_address,'id_face': idx_face, 'id_generation': idx_generation, 'prompt': prompt, 'identity_name' : identity_name},
                        )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        # try with new TOKEN
        response = requests.post(URL_API+'/set_identity', 
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'id_image': image_address,'id_face': idx_face, 'id_generation': idx_generation, 'prompt': prompt, 'identity_name' : identity_name},
        )

    response_json = json.loads(response.text)

    return response_json

# PASTE IN THE ORIGINAL IMAGE
def replace_call(image_address, idx_face, idx_generation_to_replace, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    links = []
    for i in idx_generation_to_replace:
        id_generation = i
        flag_reset = 0

        response = requests.post(URL_API+'/pick_face2',
                                headers={'Authorization': 'Bearer '+TOKEN},
                                json={'id_image':image_address, 'id_face':idx_face, 'id_generation':id_generation, 'flag_reset':flag_reset, 'flag_png':1, 'flag_quality':0, 'flag_watermark':0},
                                )
        # if the access token is expired
        if response.status_code == 401:
            TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
            TOKEN = TOKEN_DICTIONARY.get('access_token','')
            # try with new TOKEN
            response = requests.post(URL_API+'/pick_face2',
                headers={'Authorization': 'Bearer '+TOKEN},
                json={'id_image':image_address, 'id_face':idx_face, 'id_generation':id_generation, 'flag_reset':flag_reset, 'flag_png':1, 'flag_quality':0, 'flag_watermark':0},
            )

        response_json = json.loads(response.text)
        links_dict = response_json.get('links')
        links.append(links_dict.get('l'))

    return links

## -----------NOTIFICATIONS FUNCTIONS------------
def get_notification_by_name(name_list, TOKEN_DICTIONARY):
    # name_list='new_generation, progress, error'
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/notification_by_name_json',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={'name_list':name_list},
                            #timeout=100,
                            )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        response = requests.post(URL_API+'/notification_by_name_json',
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'name_list':name_list},
            #timeout=100,
        )

    response_json = json.loads(response.text)
    return response_json.get('notifications_list')

def delete_notification(notification_id, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token','')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    print(f'notification_id: {notification_id}')
    response = requests.delete(URL_API+'/notification/delete_json',
                            headers={'Authorization': 'Bearer '+TOKEN},
                            json={'id':notification_id},
                            #timeout=100,
                            )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token','')
        response = requests.delete(URL_API+'/notification/delete_json',
            headers={'Authorization': 'Bearer '+TOKEN},
            json={'id':notification_id},
            #timeout=100,
        )

    #print(response.text)
    return response.text

def handle_notifications_new_generation(image_id, idx_face, TOKEN_DICTIONARY):
    # check notifications to verify the generation status
    i = 0
    while i<10: # max 10 iterations -> then timeout
        i = i+1
        notifications = get_notification_by_name('new_generation', TOKEN_DICTIONARY)
                
        notifications_to_remove = [n for n in notifications if (n.get('name')=='new_generation' and n.get('data').get('address')==image_id and n.get('data').get('f')==idx_face and n.get('data').get('msg')=='done') and n.get('data').get('g') is not None]

        print(f'notifications_to_remove: {notifications_to_remove}')
        # remove notifications
        result_delete = [delete_notification(n.get('id'), TOKEN_DICTIONARY) for n in notifications_to_remove ]
        #print(result_delete)

        if len(notifications_to_remove)>0:
            print(f'generation for face {idx_face} completed')
            return True, {**notifications_to_remove[0].get('data',{})}

        # check iteration
        if i >= 10:
            print('Timeout. Error in generating faces')
            return False, {}

        # wait
        print('waiting for notification...')
        sleep(60)

    return False, {}

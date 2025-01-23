import json
import requests
from time import sleep
from io import BytesIO


# -----------PROCESSING FUNCTIONS------------
def start_call(email, password):
    # Get token

    URL_API = 'https://api.piktid.com/api'

    print(f'Logging to: {URL_API}')

    response = requests.post(URL_API+'/tokens', data={}, auth=(email, password))
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token': ACCESS_TOKEN, 'refresh_token': REFRESH_TOKEN, 'url_api': URL_API}


def refresh_call(TOKEN_DICTIONARY):
    # Get token using only access and refresh tokens, no mail and psw
    URL_API = TOKEN_DICTIONARY.get('url_api')
    response = requests.put(URL_API+'/tokens', json=TOKEN_DICTIONARY)
    response_json = json.loads(response.text)
    ACCESS_TOKEN = response_json['access_token']
    REFRESH_TOKEN = response_json['refresh_token']

    return {'access_token': ACCESS_TOKEN, 'refresh_token': REFRESH_TOKEN, 'url_api': URL_API}


# UPLOAD
def upload_and_detect_call(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    # upload the image into PiktID's servers
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    input_path = PARAM_DICTIONARY.get('INPUT_PATH')
    if input_path is None:
        input_url = PARAM_DICTIONARY.get('INPUT_URL')
        image_response = requests.get(input_url)
        image_response.raise_for_status()  
        image_file = BytesIO(image_response.content)
        image_file.name = 'input.jpg' 
    else:
        image_file = open(input_path, 'rb')

    OPTIONS_DICT = {}

    FLAG_HAIR = PARAM_DICTIONARY.get('FLAG_HAIR')
    CHANGE_EXPRESSION_FLAG = PARAM_DICTIONARY.get('CHANGE_EXPRESSION_FLAG')
    GENERATION_MODE = 'keep' if CHANGE_EXPRESSION_FLAG else 'random'
    
    OPTIONS_DICT = {**OPTIONS_DICT, 'flag_sync': True, 'flag_hair': FLAG_HAIR, 'mode': GENERATION_MODE}

    response = requests.post(URL_API+'/upload_pro', 
                             headers={'Authorization': 'Bearer '+TOKEN},
                             files={'file': image_file},
                             data={'options': json.dumps(OPTIONS_DICT)},
                             )

    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/upload_pro', 
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 files={'file': image_file},
                                 data={'options': json.dumps(OPTIONS_DICT)},
                                 )
    
    # if no faces, 405 error
    response_json = json.loads(response.text)

    image_address = response_json.get('image_id')  # image id
    faces_dict = response_json.get('faces')  # faces dictionary
    indices_info = faces_dict.get('coordinates_list')
    selected_faces_list = faces_dict.get('selected_faces')  # faces that can be modified
    number_of_faces = faces_dict.get('number_of_faces')  # information about the number of faces

    return image_address, indices_info, selected_faces_list


def upload_reference_face_call(PARAM_DICTIONARY, TOKEN_DICTIONARY):
    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')
    face_full_path = PARAM_DICTIONARY.get('IDENTITY_PATH')
    if face_full_path is None:
        face_url = PARAM_DICTIONARY.get('IDENTITY_URL')
        face_response = requests.get(face_url)
        face_response.raise_for_status()  
        face_file = BytesIO(face_response.content)
        face_file.name = 'face.jpg' 
    else:
        face_file = open(face_full_path, 'rb')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/consistent_identities/upload_face', 
                             headers={'Authorization': 'Bearer '+TOKEN},
                             files={'face': face_file},
                             data={'identity_name': IDENTITY_NAME},
                             )

    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/consistent_identities/upload_face', 
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 files={'face': face_file},
                                 data={'identity_name': IDENTITY_NAME},
                                 )

    response_json = json.loads(response.text)

    return response_json


# SELECT FACES
def selection_call(image_id, selected_faces_list, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/selection',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={'flag_sync': True, 'id_image': image_id, 'selected_faces': selected_faces_list},
                             # timeout=100,
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/selection',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'flag_sync': True, 'id_image': image_id, 'selected_faces': selected_faces_list},
                                 # timeout=100,
                                 )
    response_json = json.loads(response.text)
    keywords_list = response_json.get('frontend_prompt')

    return keywords_list


# GET SAVED IDENTITIES
def get_identities_call(TOKEN_DICTIONARY):
    # get the list of identities available in the account
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/get_identities', 
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={}
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
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

    if GUIDANCE_SCALE is not None:
        data.update({'guidance_scale': GUIDANCE_SCALE})
        
    if PROMPT_STRENGTH is not None:
        data.update({'prompt_strength': PROMPT_STRENGTH})

    if CONTROLNET_SCALE is not None:
        data.update({'controlnet_scale': CONTROLNET_SCALE})

    return data


def update_data_skin_call(data, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    SEED = PARAM_DICTIONARY.get('SEED')

    OPTIONS_DICT = {}
    if SEED is not None:
        OPTIONS_DICT = {**OPTIONS_DICT, 'seed': SEED}

    OPTIONS = json.dumps(OPTIONS_DICT)
    extra_options = {'options': OPTIONS}
    data.update(extra_options)

    return data


def generation_call(image_address, idx_face, prompt, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    SEED = PARAM_DICTIONARY.get('SEED') 

    data = {'id_image': image_address, 'id_face': idx_face, 'prompt': prompt, 'seed': SEED}
    data = update_data_generation_call(data, PARAM_DICTIONARY)
    print(f'data to send to generation: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/ask_generate_faces',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json=data,
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/ask_generate_faces',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json=data,
                                 )
    response_json = json.loads(response.text)
    return response_json


def consistent_generation_call(image_address, idx_face, prompt, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')

    SEED = PARAM_DICTIONARY.get('SEED')
    PROMPT_STRENGTH = PARAM_DICTIONARY.get('PROMPT_STRENGTH')

    OPTIONS_DICT = {}

    if SEED is not None:
        OPTIONS_DICT = {**OPTIONS_DICT, 'seed': SEED}

    if PROMPT_STRENGTH is not None:
        OPTIONS_DICT = {**OPTIONS_DICT, 'prompt_strength': PROMPT_STRENGTH}

    OPTIONS = json.dumps(OPTIONS_DICT)
    extra_options = {'options': OPTIONS}

    data = {'flag_sync': False, 'identity_name': IDENTITY_NAME, 'id_image': image_address, 'id_face': idx_face, 'prompt': prompt}
    data.update(extra_options)
    print(f'data to send to generation: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/consistent_identities/generate',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json=data,
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/consistent_identities/generate',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json=data,
                                 )
    response_json = json.loads(response.text)
    return response_json


def change_expression_call(image_address, idx_face, prompt, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    SEED = PARAM_DICTIONARY.get('SEED')

    data = {'flag_sync': False, 'id_image': image_address, 'id_face': idx_face, 'prompt': prompt, 'seed': SEED}
    # data = update_data_generation_call(data, PARAM_DICTIONARY, TOKEN_DICTIONARY)
    print(f'data to send to cfe: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/ask_new_expression',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json=data,
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/ask_new_expression',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json=data,
                                 )
    # print(response.text)
    response_json = json.loads(response.text)
    return response_json


def change_skin_call(image_address, idx_face, idx_generation, prompt, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    data = {'id_image': image_address, 'id_face': idx_face, 'id_generation': idx_generation, 'prompt': prompt}
    data = update_data_skin_call(data, PARAM_DICTIONARY, TOKEN_DICTIONARY)
    print(f'data to send to skin editing: {data}')

    # start the generation process given the image parameters
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/ask_generate_skin_full_body',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json=data,
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/ask_generate_skin_full_body',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json=data,
                                 )
    response_json = json.loads(response.text)
    return response_json


# GET NEW FACES
def get_generated_faces(id_image, id_face, TOKEN_DICTIONARY):
    # get list of generated faces - to call after completion of 'generation_call'
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/generated_faces',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={'id_image': id_image, 'id_face': id_face},
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/generated_faces',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'id_image': id_image, 'id_face': id_face},
                                 )

    response_json = json.loads(response.text)
    return response_json


def get_last_generated_face(list_of_generated_faces, idx_face):
    number_of_generations = len(list_of_generated_faces)
    if (number_of_generations == 0):
        return False
    return list_of_generated_faces[number_of_generations-1].get('g')


# SAVE NEW FACES AS NEW IDENTITIES
def set_identity_call(image_address, idx_face, idx_generation, prompt, identity_name, TOKEN_DICTIONARY):
    # save the generated identity in the user profile for future use
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/set_identity', 
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={'id_image': image_address, 'id_face': idx_face, 'id_generation': idx_generation, 'prompt': prompt, 'identity_name': identity_name},
                             )
    # if the access token is expired
    if response.status_code == 401:
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        # try with new TOKEN
        response = requests.post(URL_API+'/set_identity', 
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'id_image': image_address, 'id_face': idx_face, 'id_generation': idx_generation, 'prompt': prompt, 'identity_name': identity_name},
                                 )

    response_json = json.loads(response.text)

    return response_json


# PASTE IN THE ORIGINAL IMAGE
def replace_call(image_address, idx_face, idx_generation_to_replace, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    links = []
    for i in idx_generation_to_replace:
        id_generation = i
        flag_reset = 0

        response = requests.post(URL_API+'/pick_face2',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'id_image': image_address, 'id_face': idx_face, 'id_generation': id_generation, 'flag_reset': flag_reset, 'flag_png': 1, 'flag_quality': 0, 'flag_watermark': 0},
                                 )
        # if the access token is expired
        if response.status_code == 401:
            TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
            TOKEN = TOKEN_DICTIONARY.get('access_token', '')
            # try with new TOKEN
            response = requests.post(URL_API+'/pick_face2',
                                     headers={'Authorization': 'Bearer '+TOKEN},
                                     json={'id_image': image_address, 'id_face': idx_face, 'id_generation': id_generation, 'flag_reset': flag_reset, 'flag_png': 1, 'flag_quality': 0, 'flag_watermark': 0},
                                     )

        response_json = json.loads(response.text)
        links_dict = response_json.get('links')
        links.append(links_dict.get('l'))

    return links


# -----------NOTIFICATIONS FUNCTIONS------------
def get_notification_by_name(name_list, TOKEN_DICTIONARY):
    # name_list='new_generation, progress, error'
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    response = requests.post(URL_API+'/notification_by_name_json',
                             headers={'Authorization': 'Bearer '+TOKEN},
                             json={'name_list': name_list},
                             # timeout=100,
                             )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        response = requests.post(URL_API+'/notification_by_name_json',
                                 headers={'Authorization': 'Bearer '+TOKEN},
                                 json={'name_list': name_list},
                                 # timeout=100,
                                 )

    response_json = json.loads(response.text)
    return response_json.get('notifications_list')


def delete_notification(notification_id, TOKEN_DICTIONARY):
    TOKEN = TOKEN_DICTIONARY.get('access_token', '')
    URL_API = TOKEN_DICTIONARY.get('url_api')

    print(f'notification_id: {notification_id}')
    response = requests.delete(URL_API+'/notification/delete_json',
                               headers={'Authorization': 'Bearer '+TOKEN},
                               json={'id': notification_id},
                               # timeout=100,
                               )
    # if the access token is expired
    if response.status_code == 401:
        # try with new TOKEN
        TOKEN_DICTIONARY = refresh_call(TOKEN_DICTIONARY)
        TOKEN = TOKEN_DICTIONARY.get('access_token', '')
        response = requests.delete(URL_API+'/notification/delete_json',
                                   headers={'Authorization': 'Bearer '+TOKEN},
                                   json={'id': notification_id},
                                   # timeout=100,
                                   )

    # print(response.text)
    return response.text


def handle_notifications_new_generation(image_id, idx_face, TOKEN_DICTIONARY):
    # check notifications to verify the generation status
    i = 0
    while i < 60:  # max 60 iterations -> then timeout
        i = i+1
        notifications = get_notification_by_name('new_generation', TOKEN_DICTIONARY)
                
        notifications_to_remove = [n for n in notifications if (n.get('name') == 'new_generation' and n.get('data').get('address') == image_id and n.get('data').get('f') == idx_face and n.get('data').get('msg') == 'done') and n.get('data').get('g') is not None]

        print(f'notifications_to_remove: {notifications_to_remove}')
        # remove notifications
        result_delete = [delete_notification(n.get('id'), TOKEN_DICTIONARY) for n in notifications_to_remove]
        # print(result_delete)

        if len(notifications_to_remove) > 0:
            print(f'generation for face {idx_face} completed')
            return True, {**notifications_to_remove[0].get('data', {})}

        # wait
        print('waiting for notification...')
        sleep(10)

    print('Timeout. Error in generating faces')
    return False, {}


def handle_notifications_new_skin(image_id, idx_face, TOKEN_DICTIONARY):
    # check notifications to verify the generation status
    i = 0
    while i < 20:  # max 20 iterations -> then timeout
        i = i+1
        notifications_list = get_notification_by_name('new_skin', TOKEN_DICTIONARY)
        notifications_to_remove = [n for n in notifications_list if (n.get('name') == 'new_skin' and n.get('data').get('address') == image_id and n.get('data').get('f') == idx_face and n.get('data').get('msg') == 'done')]

        print(f'notifications_to_remove: {notifications_to_remove}')
        # remove notifications
        result_delete = [delete_notification(n.get('id'), TOKEN_DICTIONARY) for n in notifications_to_remove ]
        # print(result_delete)

        if len(notifications_to_remove) > 0:
            print(f'replace for face {idx_face} with full skin completed')
            return True, {**notifications_to_remove[0].get('data', {})}

        # wait
        print('waiting for notification...')
        sleep(30)

    print('Timeout. Error in editing skin')
    return False, {}

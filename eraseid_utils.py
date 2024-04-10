import os
import sys
import json
from io import BytesIO
from random import randint
from PIL import Image, ImageFile, ImageFilter

from keywords import country_list, gender_list, emotion_list, mouth_list, nose_list
from eraseid_api import open_image_from_url, upload_and_detect_call, upload_reference_face_call, selection_call, get_identities_call, generation_call, handle_notifications_new_generation, get_generated_faces, get_last_generated_face, set_identity_call, replace_call

def process_single_image(input_image, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')
    IDENTITY_IMAGE = PARAM_DICTIONARY.get('IDENTITY_IMAGE')

    # upload the source identity (swap feature), if any
    if IDENTITY_IMAGE is not None and IDENTITY_NAME is not None:
        response = upload_reference_face_call(IDENTITY_IMAGE, IDENTITY_NAME, TOKEN_DICTIONARY)
        print(f'Identity: {IDENTITY_NAME} correctly uploaded to PiktID servers')

    CHANGE_ALL_FACES = PARAM_DICTIONARY.get('CHANGE_ALL_FACES')
    HAIR_FACTOR = PARAM_DICTIONARY.get('HAIR_FACTOR')

    # upload
    print('Uploading the image')
    IMAGE_ID, indices_info, selected_faces_list = upload_and_detect_call(input_image, HAIR_FACTOR, TOKEN_DICTIONARY)

    print(f'image id: {IMAGE_ID}')

    PARAM_DICTIONARY = {**PARAM_DICTIONARY,'IMAGE_ID': IMAGE_ID}

    # select the indices of the faces to change
    idx_faces_comma_separated = (','.join(str(x) for x in range(len(indices_info)))) if CHANGE_ALL_FACES else '0' # use '0,1,2' if you want to modify the first 3 faces
    print(f'idx_faces_comma_separated:{idx_faces_comma_separated}')
    
    if CHANGE_ALL_FACES:
        selected_faces_list = [1]*len(selected_faces_list)
        idx_faces = [*range(0,len(selected_faces_list))]

    else:
        idx_faces = []
        for str_int in idx_faces_comma_separated.split(','):
            idx_faces.append(int(str_int))
        for idx_face in idx_faces:
            selected_faces_list[idx_face] = 1

    # update the list of the faces to change
    selected_faces_list_str = (','.join(str(x) for x in selected_faces_list))

    # get the keywords for each face
    print('Selecting the faces')
    KEYWORDS_LIST = selection_call(IMAGE_ID, selected_faces_list_str, TOKEN_DICTIONARY)

    PARAM_DICTIONARY = {**PARAM_DICTIONARY,'KEYWORDS_LIST': KEYWORDS_LIST}

    # IDENTITIES
    # check if the input identity is available from your database
    if IDENTITY_NAME is not None:
        # get available identities, if the call does not work, proceed without that parameter
        try:
            identity_list = get_identities_call(TOKEN_DICTIONARY)
            print(f'List of available identity names:{identity_list}')
            if IDENTITY_NAME not in identity_list:
                # Error, stop the entire process
                print(f'The identity named {IDENTITY_NAME} is not available in your database of identities, generating a random one..')
                IDENTITY_NAME = None
                PARAM_DICTIONARY['IDENTITY_NAME'] = None
        except Exception as inst:
            #print(f'ERROR. {str(type(inst))}, {str(inst.args)}, {str(inst)}')
            print('APIs are probably not updated to the latest version, generating a new identity')
            IDENTITY_NAME = None
            PARAM_DICTIONARY['IDENTITY_NAME'] = None

    # do the generation process
    j = 0
    for idx_face in idx_faces:
        # run the one face process function for each face selected
        try:
            print(f'Running process single face on face:{idx_face}')
            response = process_single_face(idx_face, j, PARAM_DICTIONARY, TOKEN_DICTIONARY)
        except Exception as inst:
            print(f'type:{type(inst)}, args:{inst.args}, {inst}')
            print(f'Error in process_single_face')
        j = j+1

    return True


def process_single_face(idx_face, count, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')
    STORE_IDENTITY_FLAG = PARAM_DICTIONARY.get('STORE_IDENTITY_FLAG')

    KEYWORDS_LIST = PARAM_DICTIONARY.get('KEYWORDS_LIST')

    image_id = PARAM_DICTIONARY.get('IMAGE_ID')

    # add a keyword
    # KEYWORDS_LIST[idx_face]['a'] = {**KEYWORDS_LIST[idx_face]['a'], 'Skin':'highly detailed'}

    keywords_to_send = KEYWORDS_LIST[count]
    keywords_to_send = json.dumps(keywords_to_send.get('a'))

    print('Generating new faces')
    response = generation_call(image_address=image_id, idx_face=idx_face, prompt=keywords_to_send, PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)

    print(f'Generation response:{response}')

    # Asynchronous API call
    response_notifications = handle_notifications_new_generation(image_id, idx_face, TOKEN_DICTIONARY)
    if response_notifications == False:
        # Error
        return False

    list_generated_faces = get_generated_faces(image_id, idx_face, TOKEN_DICTIONARY)

    # select the idx of the generation to replace
    idx_generation_to_replace = [get_last_generated_face(list_generated_faces.get('links'), idx_face)]
    print(f'Replace generation {idx_generation_to_replace}')

    # Store the last generated face as 'pippo'
    if IDENTITY_NAME is None:
        if STORE_IDENTITY_FLAG:
            new_identity_name = 'pippo' # choose your name, call it afterwards
            idx_generation = idx_generation_to_replace[-1]
            # set only the last generated as identity for the future
            response = set_identity_call(image_id, idx_face, idx_generation, keywords_to_send, new_identity_name, TOKEN_DICTIONARY)

    links = replace_call(image_id, idx_face, idx_generation_to_replace, TOKEN_DICTIONARY)

    # download the output from EraseID
    #output_img = open_image_from_url(links[-1])
    print(f'Download the generated image here: {links[-1]}')

    return True



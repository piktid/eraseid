import json

from eraseid_api import upload_and_detect_call, upload_reference_face_call, selection_call, get_identities_call, random_generation_call, consistent_generation_call, change_expression_call, change_skin_call, handle_notifications_new_generation, handle_notifications_new_skin, get_generated_faces, get_last_generated_face, set_identity_call, replace_call
from cfe_keywords import cfe_dict


def find_key_by_value(target_value):
    for key, values in cfe_dict.items():
        if target_value in values:
            return key
    return None


def process_single_image(PARAM_DICTIONARY, TOKEN_DICTIONARY):

    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')
    IDENTITY_PATH = PARAM_DICTIONARY.get('IDENTITY_PATH')
    IDENTITY_URL = PARAM_DICTIONARY.get('IDENTITY_URL')

    # upload the source identity (swap feature), if any
    if IDENTITY_NAME is not None and (IDENTITY_PATH is not None or IDENTITY_URL is not None):
        response = upload_reference_face_call(PARAM_DICTIONARY, TOKEN_DICTIONARY)
        print(f'Identity: {IDENTITY_NAME} correctly uploaded to PiktID servers')

    CHANGE_ALL_FACES = PARAM_DICTIONARY.get('CHANGE_ALL_FACES')

    # upload
    print('Uploading the image')
    IMAGE_ID, indices_info, selected_faces_list = upload_and_detect_call(PARAM_DICTIONARY, TOKEN_DICTIONARY)

    print(f'image id: {IMAGE_ID}')

    PARAM_DICTIONARY = {**PARAM_DICTIONARY, 'IMAGE_ID': IMAGE_ID}

    # select the indices of the faces to change
    idx_faces_comma_separated = (','.join(str(x) for x in range(len(indices_info)))) if CHANGE_ALL_FACES else '0'  # use '0,1,2' if you want to modify the first 3 faces
    print(f'idx_faces_comma_separated:{idx_faces_comma_separated}')
    
    if CHANGE_ALL_FACES:
        selected_faces_list = [1]*len(selected_faces_list)
        idx_faces = [*range(0, len(selected_faces_list))]

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

    PARAM_DICTIONARY = {**PARAM_DICTIONARY, 'KEYWORDS_LIST': KEYWORDS_LIST}

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
            # print(f'ERROR. {str(type(inst))}, {str(inst.args)}, {str(inst)}')
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
            print('Error in process_single_face')
        j = j+1

    return True


def process_single_face(idx_face, count, PARAM_DICTIONARY, TOKEN_DICTIONARY):

    IDENTITY_NAME = PARAM_DICTIONARY.get('IDENTITY_NAME')
    STORE_IDENTITY_FLAG = PARAM_DICTIONARY.get('STORE_IDENTITY_FLAG')

    CHANGE_EXPRESSION_FLAG = PARAM_DICTIONARY.get('CHANGE_EXPRESSION_FLAG')

    CHANGE_SKIN = PARAM_DICTIONARY.get('CHANGE_SKIN')

    KEYWORDS_LIST = PARAM_DICTIONARY.get('KEYWORDS_LIST')

    image_id = PARAM_DICTIONARY.get('IMAGE_ID')

    # add a keyword, check on id.piktid.com all the available keywords
    # KEYWORDS_LIST[count]['a'] = {**KEYWORDS_LIST[count]['a'], 'Skin':'highly detailed'}

    if CHANGE_EXPRESSION_FLAG:
        NEW_EXPRESSION = PARAM_DICTIONARY.get('NEW_EXPRESSION')
        # replace all the found keywords with the ones only for the expression/gaze/eyes
        category = find_key_by_value(NEW_EXPRESSION)
        if category is None:
            print('No keyword corresponds to the entered new expression value, please check cfe_keywords.py')
            return False
        KEYWORDS_LIST[count]['a'] = {category: NEW_EXPRESSION}

    keywords_to_send = KEYWORDS_LIST[count]
    keywords_to_send = json.dumps(keywords_to_send.get('a'))

    if CHANGE_EXPRESSION_FLAG:
        print('Changing facial expressions')
        response = change_expression_call(image_address=image_id, idx_face=idx_face, prompt=keywords_to_send, PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
        print(f'Cfe response:{response}')

    elif IDENTITY_NAME is not None:
        print('Swapping faces')
        response = consistent_generation_call(image_address=image_id, idx_face=idx_face, prompt=keywords_to_send, PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
        print(f'Swap response:{response}')
    else:
        print('Generating new faces')
        response = random_generation_call(image_address=image_id, idx_face=idx_face, prompt=keywords_to_send, PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
        print(f'Generation response:{response}')

    # Asynchronous API call
    response_notifications = handle_notifications_new_generation(image_id, idx_face, TOKEN_DICTIONARY)
    if response_notifications is False:
        # Error
        return False

    list_generated_faces = get_generated_faces(image_id, idx_face, TOKEN_DICTIONARY)

    # select the idx of the generation to replace
    idx_generation_to_replace = [get_last_generated_face(list_generated_faces.get('links'), idx_face)]
    print(f'Replace generation {idx_generation_to_replace}')

    if CHANGE_SKIN:
        for idx_generation in idx_generation_to_replace:
                
            print('Editing the skin')
            response = change_skin_call(image_address=image_id, idx_face=idx_face, idx_generation=idx_generation, prompt=keywords_to_send, PARAM_DICTIONARY=PARAM_DICTIONARY, TOKEN_DICTIONARY=TOKEN_DICTIONARY)
            print(f'Skin editing response:{response}')

            # Asynchronous API call
            response_notifications = handle_notifications_new_skin(image_id, idx_face, TOKEN_DICTIONARY)
            if response_notifications is False:
                # Error
                return False

    # Store the last generated face as 'pippo'
    if IDENTITY_NAME is None:
        if STORE_IDENTITY_FLAG:
            new_identity_name = 'pippo'  # choose your name, call it afterwards
            idx_generation = idx_generation_to_replace[-1]
            # set only the last generated as identity for the future
            response = set_identity_call(image_id, idx_face, idx_generation, keywords_to_send, new_identity_name, TOKEN_DICTIONARY)

    links = replace_call(image_id, idx_face, idx_generation_to_replace, TOKEN_DICTIONARY)

    # download the output from EraseID
    print(f'Download the generated image here: {links[-1]}')

    return True

import os
import sys
import json
from io import BytesIO
from PIL import Image, ImageFile, ImageFilter
import argparse

from eraseid_api import open_image_from_url, open_image_from_path, start_call, upload_and_detect_call, selection_call, get_identities_call, generation_call, handle_notifications_new_generation, get_generated_faces, get_last_generated_face, set_identity_call, replace_call
from keywords import country_list, gender_list, emotion_list, mouth_list, nose_list


if __name__ == '__main__':


    parser = argparse.ArgumentParser()

    parser.add_argument('--hair', help='Change also the hair', action='store_true')
    parser.add_argument('--all_faces', help='Change all the faces in the photo', action='store_true')
    parser.add_argument('--sync', help='Use synchronous calls', action='store_true')
    parser.add_argument('--identity_name', help='Use the face from the stored identities', default=None)
    parser.add_argument('--store_identity', help='Save the generated identity under the name pippo', action='store_true')
    parser.add_argument('--url', help='Image file url', type=str, default='https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1')
    parser.add_argument('--filepath', help='Image file absolute path', type=str, default=None)

    args = parser.parse_args()

    # be sure to export your email and psw as environmental variables
    EMAIL = os.getenv("ERASEID_EMAIL")
    PASSWORD = os.getenv("ERASEID_PASSWORD")

    # Parameters
    CHANGE_HAIR = args.hair # False if only the face is anonymized, True if both face and hair
    CHANGE_ALL_FACES = args.all_faces # False if only a subset of the faces in the image need to be anonymize, True if all the faces
    FLAG_SYNC = args.sync # False if the API call is asynchronous, True otherwise, which means that the program will wait for the server's answer
    IDENTITY_NAME = args.identity_name # Default is None, otherwise a string of a stored name
    STORE_IDENTITY_FLAG = args.store_identity # False if the new identity shall not be saved in the user profile, viceversa True

    # load the image
    URL = args.url 
    IMAGE_PATH = args.filepath
    
    if IMAGE_PATH is not None:
        if os.path.exists(IMAGE_PATH):
            input_img = open_image_from_path(IMAGE_PATH)
            print(f'Using as input image the file located at: {IMAGE_PATH}')
        else:
            print('Wrong filepath, check again')
            sys.exit()
    else:
        try:
            input_img = open_image_from_url(URL)
            print(f'Using as input image the file located at: {URL}')
        except:
            print('Wrong URL, check again')
            sys.exit()

    # log in
    TOKEN = start_call(EMAIL, PASSWORD)
    HAIR_FACTOR = 1 if CHANGE_HAIR else 0

    # upload
    image_id, indices_info, selected_faces_list = upload_and_detect_call(input_img,HAIR_FACTOR,TOKEN)

    # select the indices of the faces to change
    idx_faces_comma_separated = (','.join(str(x) for x in range(len(indices_info)))) if CHANGE_ALL_FACES else '0' # use '0,1,2' if you want to modify the first 3 faces

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
    keywords_list = selection_call(image_id, selected_faces_list_str, TOKEN)

    # KEYWORDS
    # if you want to change the keywords, uncomment the next lines and select the index of the face and read the keywords
    """
    idx_face = 0
    try:
        keywords = keywords_list[idx_faces.index(idx_face)].get('a')
        print(f'Keywords of the face n-th {idx_face}: {keywords}')
    except:
        print(f'An error occured. Most likely, you typed in an idx_face that was not selected for modification. Choices allowed are among: {idx_faces}')

    keywords_list[idx_face]['a'] = {'Age': 60, 'Country': 'Italy', 'Emotion':'happy', 'Gender':'female'}
    """
    # -------------------------

    # IDENTITIES
    # check if the input identity is available from your database
    if IDENTITY_NAME is not None:
        # get available identities, if the call does not work, proceed without that parameter
        try:
            identity_list = get_identities_call(TOKEN)
            print(f'List of available identity names:{identity_list}')
            if IDENTITY_NAME not in identity_list:
                # Error, stop the entire process
                print(f'The identity named {IDENTITY_NAME} is not available in your database of identities, generating a random one..')
                IDENTITY_NAME = None
        except Exception as inst:
            #print(f'ERROR. {str(type(inst))}, {str(inst.args)}, {str(inst)}')
            print('APIs are probably not updated to the latest version, generating a new identity')
            IDENTITY_NAME = None

    # do the generation process
    j = 0
    for idx_face in idx_faces:

        # generate each face sequentially
        keywords_to_send = keywords_list[j]
        keywords_to_send = json.dumps(keywords_to_send.get('a'))

        response = generation_call(image_id, idx_face, keywords_to_send, IDENTITY_NAME, TOKEN, FLAG_SYNC)

        if FLAG_SYNC:
            # Synchronous API call
            a = (response.get('links')).get('list')
            b = a[0].get('g')
            # select the idx of the generation to replace
            idx_generation_to_replace = [b]

        else:
            # Asynchronous API call
            response_notifications = handle_notifications_new_generation(image_id, idx_face, TOKEN)
            if response_notifications == False:
                # Error
                break

            list_generated_faces = get_generated_faces(image_id, idx_face, TOKEN)

            # select the idx of the generation to replace
            idx_generation_to_replace = [get_last_generated_face(list_generated_faces.get('links'), idx_face)]
            print(f'Replace generation {idx_generation_to_replace}')

        # Store the last generated face as 'pippo'
        if IDENTITY_NAME is None:
            if STORE_IDENTITY_FLAG:
                new_identity_name = 'pippo' # choose your name, call it afterwards
                idx_generation = idx_generation_to_replace[-1]
                # set only the last generated as identity for the future
                response = set_identity_call(image_id, idx_face, idx_generation, keywords_to_send, new_identity_name, TOKEN)

        links = replace_call(image_id, idx_face, idx_generation_to_replace, TOKEN)
        j = j+1

    # download the output from EraseID
    output_img = open_image_from_url(links[-1])
    print(f'Download the generated image here: {links[-1]}')


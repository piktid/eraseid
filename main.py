import os
import requests
import json
from io import BytesIO
from PIL import Image, ImageFile, ImageFilter
import argparse

from eraseid_api import start_call, upload_and_detect_call, selection_call, generation_call, handle_notifications_new_generation, get_generated_faces, get_last_generated_face, replace_call
from keywords import country_list, gender_list, emotion_list, mouth_list, nose_list


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--hair', help='Change also the hair', action='store_true')
    parser.add_argument('--all_faces', help='Change all the faces in the photo', action='store_true')
    parser.add_argument('--sync', help='Use synchronous calls', action='store_true')

    args = parser.parse_args()

    # be sure to export your email and psw as environmental variables
    EMAIL = os.getenv("ERASEID_EMAIL")
    PASSWORD = os.getenv("ERASEID_PASSWORD")

    # Parameters
    CHANGE_HAIR = args.hair # False if only the face is anonymized, True if both face and hair
    CHANGE_ALL_FACES = args.all_faces # False if only a subset of the faces in the image need to be anonymize, True if all the faces
    FLAG_SYNC = args.sync # False if the API call is asynchronous, True otherwise, which means that the program will wait for the server's answer

    ## START
    # insert the URL of the image to anonymize
    # photo of a girl
    url = 'https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1'
    # photo with 3 persons
    #url = 'https://images.pexels.com/photos/8790786/pexels-photo-8790786.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1'
    input_img = Image.open(BytesIO(requests.get(url,stream=False).content))

    # start the call
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

    # do the generation process
    j = 0
    for idx_face in idx_faces:

        # generate each face sequentially
        keywords_to_send = keywords_list[j]
        keywords_to_send = json.dumps(keywords_to_send.get('a'))

        response = generation_call(image_id, idx_face, keywords_to_send, TOKEN, FLAG_SYNC)

        if FLAG_SYNC:
            # Syncronous API call
            a = (response.get('links')).get('list')
            b = a[0].get('g')
            # select the idx of the generation to replace
            idx_generation_to_replace = [b]

        else:
            # Asyncronous API call
            response_notifications = handle_notifications_new_generation(image_id, idx_face, TOKEN)
            if response_notifications == False:
                # Error
                break

            list_generated_faces = get_generated_faces(image_id, idx_face, TOKEN)

            # select the idx of the generation to replace
            idx_generation_to_replace = [get_last_generated_face(list_generated_faces.get('links'), idx_face)]
            print(f'Replace generation {idx_generation_to_replace}')

        links = replace_call(image_id, idx_face, idx_generation_to_replace, TOKEN)
        j = j+1

    # download the output from EraseID
    output_img = Image.open(requests.get(links[-1],stream=True).raw)
    print(f'Download the generated image here: {links[-1]}')


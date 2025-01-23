import os
import sys
import argparse
from random import randint

from eraseid_utils import process_single_image
from eraseid_api import start_call


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('--hair', help='Change also the hair', action='store_true')
    parser.add_argument('--all_faces', help='Change all the faces in the photo', action='store_true')
    parser.add_argument('--url', help='Image file url', type=str, default='https://images.piktid.com/frontend/studio/eraseid/free-photo-of-a-woman.webp')
    parser.add_argument('--filepath', help='Input image file absolute path', type=str, default=None)

    # Consistent identity parameters
    parser.add_argument('--identity_filepath', help='Input identity file absolute path', type=str, default=None)
    parser.add_argument('--identity_url', help='Input identity url, use only if no identity path was given', type=str, default=None)
    parser.add_argument('--identity_name', help='Use the face from the stored identities', default=None)
    parser.add_argument('--store_identity', help='Save the generated identity under the name pippo', action='store_true')

    # Change expression parameters
    parser.add_argument('--change_expression_flag', help='Change only the facial expression', action='store_true')
    parser.add_argument('--new_expression', help='Desired facial expression', type=str, default='happy')

    # Random generation parameters
    parser.add_argument('--guidance_scale', help='Guidance scale', type=str, default=None)
    parser.add_argument('--prompt_strength', help='Description strength', type=str, default=None)
    parser.add_argument('--controlnet_scale', help='Conditioning scale', type=str, default=None)
    parser.add_argument('--seed', help='Generation seed', type=int, default=randint(0, 1000000))

    # Skin parameters
    parser.add_argument('--skin', help='Change also the skin', action='store_true')

    args = parser.parse_args()

    # be sure to export your email and psw as environmental variables
    EMAIL = os.getenv("ERASEID_EMAIL")
    PASSWORD = os.getenv("ERASEID_PASSWORD")

    # Parameters
    FLAG_HAIR = args.hair  # False if only the face is modified, True if both face and hair
    CHANGE_ALL_FACES = args.all_faces  # False if only a subset of the faces in the image need to be anonymize, True if all the faces

    # Consistent identity parameters
    IDENTITY_PATH = args.identity_filepath
    IDENTITY_URL = args.identity_url
    IDENTITY_NAME = args.identity_name  # Default is None, otherwise a string of a stored name
    STORE_IDENTITY_FLAG = args.store_identity  # False if the new identity shall not be saved in the user profile, viceversa True

    # Change expression parameters
    CHANGE_EXPRESSION_FLAG = args.change_expression_flag
    NEW_EXPRESSION = args.new_expression

    # Generation parameters
    GUIDANCE_SCALE = args.guidance_scale
    PROMPT_STRENGTH = args.prompt_strength
    CONTROLNET_SCALE = args.controlnet_scale
    SEED = args.seed

    # Skin parameters
    CHANGE_SKIN = args.skin  # True if also the skin is anonymized

    # Image parameters
    INPUT_URL = args.url 
    INPUT_PATH = args.filepath

    if INPUT_PATH is not None:
        if os.path.exists(INPUT_PATH):
            print(f'Using as input image the file located at: {INPUT_PATH}')
        else:
            print('Wrong filepath, check again')
            sys.exit()
    else:
        print('Input filepath not assigned, trying with URL..')
        if INPUT_URL is not None:
            print(f'Using the input image located at: {INPUT_URL}')
        else:
            print('Wrong input url, check again, exiting..')
            sys.exit()

    if IDENTITY_PATH is not None:
        if os.path.exists(IDENTITY_PATH):
            print(f'Using the input identity file located at: {IDENTITY_PATH}')
        else:
            print('Wrong identity path, check again')
    else:
        print('Identity path not assigned, check again')
        if IDENTITY_URL is not None:
            print(f'Using the input identity located at: {IDENTITY_URL}')
        else:
            print('Wrong identity url, check again')

    # log in
    TOKEN_DICTIONARY = start_call(EMAIL, PASSWORD)

    # we recommend including the hair when changing expression!
    # FLAG_HAIR = True if CHANGE_EXPRESSION_FLAG else FLAG_HAIR

    PARAM_DICTIONARY = {
            'INPUT_PATH': INPUT_PATH,
            'INPUT_URL': INPUT_URL,
            'FLAG_HAIR': FLAG_HAIR,
            'CHANGE_ALL_FACES': CHANGE_ALL_FACES,
            'IDENTITY_PATH': IDENTITY_PATH,
            'IDENTITY_URL': IDENTITY_URL,
            'IDENTITY_NAME': IDENTITY_NAME,
            'STORE_IDENTITY_FLAG': STORE_IDENTITY_FLAG,
            'SEED': SEED,
            'GUIDANCE_SCALE': GUIDANCE_SCALE,
            'PROMPT_STRENGTH': PROMPT_STRENGTH,
            'CONTROLNET_SCALE': CONTROLNET_SCALE,
            'CHANGE_EXPRESSION_FLAG': CHANGE_EXPRESSION_FLAG,
            'NEW_EXPRESSION': NEW_EXPRESSION,
            'CHANGE_SKIN': CHANGE_SKIN,
        }

    response = process_single_image(PARAM_DICTIONARY, TOKEN_DICTIONARY)

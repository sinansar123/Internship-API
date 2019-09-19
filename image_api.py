from flask import Flask, Response, make_response,request
#from flask_restful import reqparse
import json
import urllib.request
import cv2
from PIL import Image,ImageEnhance
import numpy as np
import os
import pyimgur
import uuid
#from Pillow import Image

app = Flask(__name__)

@app.route('/')
def api_root():
    response =make_response('Available requests are: /resize, /blur, /adjust.')
    response.status_code = 200
    return response


@app.route('/resize',  methods=["POST"])
def resize():
    body = request.get_json()



    if 'url' not in body:
        response = make_response('missing url')
        response.status_code = 400
    elif 'dimensions' not in body:
        response= make_response('Missing Dimensions')
        response.status_code = 400
    elif ('width') not in body['dimensions'] and ('height') not in body['dimensions']:
            response = make_response('missing width and height')
            response.status_code = 400
    elif 'width' not in body['dimensions']:
            response = make_response('missing width')
            response.status_code = 400
    elif 'height' not in body['dimensions']:
            response = make_response('missing height')
            response.status_code = 400
    else:
        url = body['url']
        save_name = str(uuid.uuid3(uuid.NAMESPACE_URL, url)) + ('.jpg')
        urllib.request.urlretrieve(url, save_name)
        img = cv2.imread(save_name)

        try:
            resized = cv2.resize(img, (body['dimensions']['width'], body['dimensions']['height']))
        except:
            response = make_response('Bad Request:Url does not link to an Image')
            response.status_code = 400
            return response

        os.remove(save_name)
        cv2.imwrite(save_name, resized)



        # push new file to imgur, get an URL
        # delete resized which has the name 'name' now

        response = make_response('ok')
        response.status_code = 200

        CLIENT_ID = "296a4e28342d492"
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(save_name)

        os.remove(save_name)
        uploaded_url = uploaded_image.link
        d = {'data': {
            'url': uploaded_url
        }
        }
        response.set_data(json.dumps(d))

    return response



#to do: use opencv to get a blur filter
@app.route('/blur' ,methods=["POST"])
def blur():
    body = request.get_json()

    if 'url' not in body:
        response = make_response('Bad Request:Missing URL')
        response.status_code = 400
    else:
        url = body['url']

        #A solution to check if the url contains an image using MIME type, it is commented out since checking whether image processing operations work or not is a better solution.
        """""
        MIME_check = urllib.request.urlopen(url)
        http_message = MIME_check.info()
        full = http_message.get_content_type()  # 'text/plain'
        main = http_message.get_content_maintype()
        print(main)
        print(full)

        
        
        if  (main == 'image'):
        """

        save_name = str(uuid.uuid3(uuid.NAMESPACE_URL,url)) + ('.jpg')
        urllib.request.urlretrieve(url, save_name)
        img = cv2.imread(save_name)


        try:
            blurred = cv2.blur(img, (5, 5))
        except:
            response = make_response('Bad Request:Url does not link to an Image')
            response.status_code = 400
            return response

        os.remove(save_name)
        cv2.imwrite(save_name, blurred)



        response = make_response("ok")
        response.status_code = 200

        CLIENT_ID = "296a4e28342d492"
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(save_name)

        uploaded_url = uploaded_image.link
        os.remove(save_name)
        d = {'data': {
        'url': uploaded_url
            }
        }
        response.set_data(json.dumps(d))

        """""
        else:
            response = make_response('Bad Request:Url has invalid MIME Type')
            response.status_code = 400
        """
    return response


#a small funtion to use in /adjust. it removes % signs from values and turns them to int
def perc_reader(string):
    new_str = ''
    for i in range(len(string)-1):
            new_str = new_str + string[i]
    coef_int = int(new_str)/100
    return coef_int



#multiple enhancers have to be usable -->parse them from request.
@app.route('/adjust', methods=["POST"])
def adjust():
    body = request.get_json() #body is parsed to a dictionary

    """""
    if no enhancers are provided or there isn't a url in the request body, a bad request response is returned 
    explaining the problem briefly. 
    
    setting enhancements at 100% returns the exact image. Setting them higher or lower will manipulate the 
    image accordingly.
    """""
    if 'url'  not in body:
        response = make_response('Bad Request:Missing URL')
        response.status_code = 400
    elif 'enhancers' not in body:
        response = make_response('Bad Request:No enhancers provided.')
        response.status_code = 400
    elif bool(body['enhancers']) == False:
        response = make_response('Bad Request: No enhancers provided.')
        response.status_code = 400
    else:
        url= body['url']
        save_name = str(uuid.uuid3(uuid.NAMESPACE_URL, url)) + ('.jpg')
        name =  str(uuid.uuid3(uuid.NAMESPACE_URL, url))

        urllib.request.urlretrieve(url, save_name)
        i = 0
        #use i to track file names. After each enhancement a new file (version) is created and the old one gets deleted.
        if 'colorBalance' in body['enhancers']:
            i= i+1
            color_coef = perc_reader(body['enhancers']['colorBalance'])
            try:
                img = Image.open(save_name)
                enhancer = ImageEnhance.Color(img)
                old_name = save_name
                save_name = name + str(i) + ('.jpg')
                enhancer.enhance(color_coef).save(save_name)
                os.remove(old_name)
            except:
                response = make_response('Bad Request:Url does not link to an Image')
                response.status_code = 400
                return response

        if 'brightness' in body['enhancers']:
            i = i+1
            bright_coef = perc_reader(body['enhancers']['brightness'])
            try:
                img = Image.open(save_name)
                enhancer = ImageEnhance.Brightness(img)
                old_name = save_name
                save_name = name + str(i) + ('.jpg')
                enhancer.enhance(bright_coef).save(save_name)
                os.remove(old_name)
            except:
                response = make_response('Bad Request:Url does not link to an Image')
                response.status_code = 400
                return response

        if 'contrast' in body['enhancers']:
            i = i + 1
            contrast_coef = perc_reader(body['enhancers']['contrast'])

            try:
                img = Image.open(save_name)
                enhancer = ImageEnhance.Contrast(img)
                old_name = save_name
                save_name = name + str(i) + ('.jpg')
                enhancer.enhance(contrast_coef).save(save_name)
                os.remove(old_name)
            except:
                response = make_response('Bad Request:Url does not link to an Image')
                response.status_code = 400
                return response

        if 'sharpness' in body['enhancers']:
            i = i + 1
            sharp_coef = perc_reader(body['enhancers']['sharpness'])

            try:
                img = Image.open(save_name)
                enhancer = ImageEnhance.Sharpness(img)
                old_name = save_name
                save_name = name + str(i) + ('.jpg')
                enhancer.enhance(sharp_coef).save(save_name)
                os.remove(old_name)
            except:
                response = make_response('Bad Request:Url does not link to an Image')
                response.status_code = 400
                return response

        response = make_response("ok")
        response.status_code = 200

        CLIENT_ID = "296a4e28342d492"
        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(save_name)

        os.remove(save_name)
        uploaded_url = uploaded_image.link
        d = {'data': {
            'url': uploaded_url
            }
        }
        response.set_data(json.dumps(d))
    return response

#save images to server. Treat them as localfiles and create urls as paths. Hehe .. Nope. Just upload to imgur, provide a link.

if __name__ == '__main__':
    app.run(host='0.0.0.0')

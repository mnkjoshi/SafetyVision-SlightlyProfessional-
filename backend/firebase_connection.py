from json import JSONEncoder
import firebase_admin
from firebase_admin import db,storage
import numpy as np
import geocoder

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def e(data, shift):
    out = ""
    for char in list(data):
        if not char.isalpha():
            out += char
        else:
            out += chr((ord(char) - 97 + shift) % 26 + 97)
    return out


def d(data, shift):
    out = ""
    for char in list(data):
        if not char.isalpha():
            out += char
        else:
            out += chr((ord(char) - 97 - shift) % 26 + 97)
    return out


class firebase_connection:
    def __init__(self):
        self.__cred_obj = firebase_admin.credentials.Certificate('safetyvision-huh.json')
        self.__default_app = firebase_admin.initialize_app(self.__cred_obj, {
            'databaseURL': 'https://safetyvision-huh-default-rtdb.firebaseio.com/',
            'storageBucket': 'safetyvision-huh.appspot.com'
        })
        self.__ref = db.reference('/')
        self.__sh = 4781

    def save_image(self, image, weapon_type=None, time=None, date=None, location=None):
        """
        :param image: This is the image np object
        :param weapon_type: This is the weapontype as a string
        :param time: This is the time as a string
        :param date: This is the date as a string
        :param location: This is the string object
        :return: None
        """
        bucket = storage.bucket()
        blob = bucket.blob(image)
        blob.upload_from_filename(image)

        # Opt : if you want to make public access from the URL
        blob.make_public()

        childref = self.__ref.child('images')
        g = geocoder.ip('me')
        image_json = {
            'image':  blob.public_url,
            'time': time,
            'date': date,
            'location': g.latlng,
            'weapon_type': weapon_type,
            'new': 1
        }
        # encoded_image_json = json.dumps(image_json, cls=NumpyArrayEncoder)
        childref.push(image_json)

    def get_new_data(self):
        childref = self.__ref.child('images')
        snapshot = childref.order_by_child('new').equal_to(1).get()
        # Set all new to 0 and convert image
        for k, v in snapshot.items():
            keychildref = childref.child(k)
            v['new'] = 0
            keychildref.update(v)
            snapshot[k]['image'] = eval('np.array(' + v['image'] + ')')

        return snapshot

    def user_auth(self, username, password):
        childref = self.__ref.child('users')
        
        # Get the user password 
        snapshot = childref.child(username).get()
        if snapshot is None:
            return False,None  # User doesnt exist
        if password == d(snapshot,self.__sh):
            return True,'cp'  # Correct password
        elif snapshot:
            return False,'ip'  # Incorrect password

    def create_user(self, username, password):
        """
        Function to create user
        :param username: string
        :param password: string
        :return: True if successful else false
        """
        childref = self.__ref.child('users')
        if not childref.child(username).get():
            childref.child(username).set(e(password, self.__sh))
            return True
        return False
    
    def add_email(self,email):
        childref = self.__ref.child('emails')
        snapshot = childref.get()
        if snapshot is None:
            childref.set([email])
        else:
            if email not in snapshot:
                snapshot.append(email)
            childref.set(snapshot)

    def get_emails(self):
        childref = self.__ref.child('emails')
        snapshot = childref.get()

        return snapshot

if __name__ == '__main__':
    fc = firebase_connection()

    # Test to add image
    # for i in range(5):
    #     fc.save_image(image=np.array([[1.02,2,3,4],[1,2,4,5]]))

    # Test to get new data
    # print(fc.get_new_data())

    # Test to create user
    # print(fc.create_user('hd', 'hd'))
    
    # Test to auth user
    # print(fc.user_auth('hd','hd'))
    
    # Test to add email
    # fc.add_email('hd1@hd.com')

    # # Test to get emails
    # print(fc.get_emails())
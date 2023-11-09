import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage




#import all photos , once we have the Images we're going to encode one by one and store in the list

#importing the mode Images into list
folderPath = 'Images'
PathList = os.listdir(folderPath)  # it will provide list of all files in directory
imgList = []
# print(PathList)
#import id's as well
studentsIds = []
for path in PathList:
    imgList.append(cv2.imread(os.path.join(folderPath,path)))
    #removing .jpg
    studentsIds.append(os.path.splitext(path)[0])
    # print(path)
    # print(os.path.splitext(path)[0]) #to get first element use 0 because not interested in extensions
    # down, it will create a folder called Images and in that folder it will all Images not need to add manually into database firebase
    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)
#print(studentsIds) #imported only first data without extension
# print(len(imgModeList)) #--> to check whether we imported all files or not

#we're going to loop through all Images and encode every single image
# Note: openCV uses --> BGR, face-recognition uses --> RGB , so covert according to library
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB) # conversion of bgr to rgb
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList
print("Encoding Started..")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentsIds]

# print(encodeListKnown)
print("Encoding Completed")

# next step is to save this in a pickle file so we can use it in later in webcam
# when we're saving we need save two things 1. encoding, 2. names (ids)

# Generating pickle file
file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Saved")


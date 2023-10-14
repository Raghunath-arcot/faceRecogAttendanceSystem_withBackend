import os
import pickle
import cv2
import face_recognition
import cvzone
import numpy as np
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "https://realtimefaceattendance-e49f5-default-rtdb.firebaseio.com/",
    'storageBucket': "realtimefaceattendance-e49f5.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBg = cv2.imread('Resources/background.png')

#importing the mode Images into list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)  # it will provide list of all files in directory
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath,path)))
# print(len(imgModeList)) #--> to check whether we imported all files or not

# load the encoding file
print("Loading Encode file....")
file = open("EncodeFile.p",'rb') # for permission rb
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentsIds = encodeListKnownWithIds
# print(studentsIds)
print("Encode file Loaded")

modeType = 0
# once the face is detected only one we can download the information , we can't download all time we run it's inefficient so use counter
counter = 0
id = -1 # 0 is also an id so -1
imgStudent = []

while True:
    success, img = cap.read()

    # making our image a bit smaller because it's taking lot of computation time
    imgS = cv2.resize(img, (0,0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB) # conversion is important

    # encoding in current frame
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)     # previous encoding of known faces and we have new encodings and compare

    imgBg[162:162 + 480, 55:55 + 640] = img # overlaying webcam image in graphics
    imgBg[44:44 + 633, 808:808 + 414] = imgModeList[modeType]


    if faceCurFrame:

    # loop through all these encoding and one by one comparing whether they match or not

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            # print("matches", matches)
            # print("faceDis",faceDis) #matching distance, lower the dis better mathces

            matchIndex = np.argmin(faceDis)
            # print("Match Index", matchIndex) # gives index of zero value

            if matches[matchIndex]:
                # print("Known Face Detected")
                # print(studentsIds[matchIndex])
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4 # at up we reduced by 4 so here we multiplied by 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBg = cvzone.cornerRect(imgBg, bbox, rt = 0) # bbox = bounding box
                id = studentsIds[matchIndex]
                if counter == 0:
                    # just says loading because it is lagging to overcome this use asynchronous functions
                    cvzone.putTextRect(imgBg,"Loading..", (275, 400))
                    cv2.imshow("Face Attendance", imgBg)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1
        if counter!=0:
            if counter == 1:
                #get the data
                #download data and show it
                studentsInfo = db.reference(f'Students/{id}').get()
                print(studentsInfo)
                #get the image from the storage
                blob = bucket.get_blob(f'Images/{id}.jpg')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
                # Update data of attendance
                #Note Note_---> 30 sec for just reference because 45min a period interval of time might not be possible for testing my project
                # if students time was more then 30 sec from previos attendance then mark attendance
                datetimeObject = datetime.strptime(studentsInfo['Last-attendance-time'],
                                                  "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)
                if secondsElapsed > 30: #this for 30 sec (in real time use accordingly like 30 min)
                    ref = db.reference(f'Students/{id}')
                    studentsInfo['Total-attendance'] += 1
                    #update in server database
                    ref.child('Total-attendance').set(studentsInfo['Total-attendance']) #we need to update total_attendancw with the value  studentsInfo['total_attendance']
                    ref.child('Last-attendance-time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) #updating last attendance time as well
                else:
                    modeType = 3
                    counter = 0
                    imgBg[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if modeType != 3:

                if 10<counter<20:
                    modeType = 2 #we change modetype then update the image
                imgBg[44:44 + 633, 808:808 + 414] = imgModeList[modeType]


                if counter <= 10:
                    cv2.putText(imgBg, str(studentsInfo['Total-attendance']), (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                    cv2.putText(imgBg, str(studentsInfo['Department']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)
                    cv2.putText(imgBg, str(studentsInfo['id']), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.4, (0, 0, 0), 1)
                    cv2.putText(imgBg, str(studentsInfo['Section']), (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (20, 20, 20), 1)
                    cv2.putText(imgBg, str(studentsInfo['Batch']), (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (20, 20, 20), 1)
                    cv2.putText(imgBg, str(studentsInfo['Academic Year']), (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.4, (20, 20, 20), 1)

                    (w, h), _ = cv2.getTextSize(studentsInfo['Name'],cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w)//2
                    cv2.putText(imgBg, str(studentsInfo['Name']), (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)  # here name varies big or small length so we need to center it

                    imgBg[175:175+216, 909:909+216] = imgStudent


                counter+=1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentsInfo = []
                    imgBg[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    #cv2.imshow("Webcam", img)
    cv2.imshow("Face Attendance", imgBg)
    cv2.waitKey(1)


# to remove the lags use Asynchorous functions
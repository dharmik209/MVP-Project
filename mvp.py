#To add new user :
  python3 add_user.py


#To Recognize user :
  python3 recognize.py


#To Recognize until KeyboardInterrupt (ctrl + c) by the user:
  python3 recognize_until_keyboard_Interrupt.py


#To delete an existing user :
  python3 delete_user.py


#Import the dependencies
 import tensorflow as tf
 import numpy as np
 import os
 import glob
 import pickle
 import cv2
 import time
 from numpy import genfromtxt

 from keras import backend as K
 from keras.models import load_model
 K.set_image_data_format('channels_first')
 np.set_printoptions(threshold=np.nan)


 import pyaudio
 from IPython.display import Audio, display, clear_output
 import wave
 from scipy.io.wavfile import read
 from sklearn.mixture import GMM 
 import warnings
 warnings.filterwarnings("ignore")

 from sklearn import preprocessing
 # for converting audio to mfcc
 import python_speech_features as mfcc


#Facial Encodings
#provides 128 dim embeddings for face
def img_to_encoding(img):
   img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
   
   #converting img format to channel first
   img = np.around(np.transpose(img, (2,0,1))/255.0, decimals=12)

   x_train = np.array([img])

   #facial embedding from trained model
   embedding = model.predict_on_batch(x_train)
   return embedding 


#Triplet Loss
def triplet_loss(y_true, y_pred, alpha = 0.2):
    anchor, positive, negative = y_pred[0], y_pred[1], y_pred[2]
    
    # triplet loss formula 
    pos_dist = tf.reduce_sum( tf.square(tf.subtract(y_pred[0], y_pred[1])) )
    neg_dist = tf.reduce_sum( tf.square(tf.subtract(y_pred[0], y_pred[2])) )
    basic_loss = pos_dist - neg_dist + alpha
    
    loss = tf.maximum(basic_loss, 0.0)
   
    return loss

# load the model
model = load_model('facenet_model/model.h5', custom_objects={'triplet_loss': triplet_loss})


#MFCC features and Extract delta of the feature vector
def calculate_delta(array):
    rows,cols = array.shape
    deltas = np.zeros((rows,20))
    N = 2
    for i in range(rows):
        index = []
        j = 1
        while j <= N:
            if i-j < 0:
                first = 0
            else:
                first = i-j
            if i+j > rows -1:
                second = rows -1
            else:
                second = i+j
            index.append((second,first))
            j+=1
        deltas[i] = ( array[index[0][0]]-array[index[0][1]] + (2 * (array[index[1][0]]-array[index[1][1]])) ) / 10
    return deltas

#convert audio to mfcc features
def extract_features(audio,rate):    
    mfcc_feat = mfcc.mfcc(audio,rate, 0.025, 0.01,20,appendEnergy = True, nfft=1103)
    mfcc_feat = preprocessing.scale(mfcc_feat)
    delta = calculate_delta(mfcc_feat)

    #combining both mfcc features and delta
    combined = np.hstack((mfcc_feat,delta)) 
    return combined


#Adding a New User's Face
def add_user():
    
    name = input("Enter Name:")
     # check for existing database
    if os.path.exists('./face_database/embeddings.pickle'):
        with open('./face_database/embeddings.pickle', 'rb') as database:
            db = pickle.load(database)   
            
            if name in db:
                print("Name Already Exists! Try Another Name...")
                return
    else:
        #if database not exists than creating new database
        db = {}
    
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    #detecting only frontal face using haarcascade
    face_cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_default.xml')
    
    i = 3
    face_found = False
    
    while True:            
        _, frame = cap.read()
        frame = cv2.flip(frame, 1, 0)
            
        #time.sleep(1.0)
        cv2.putText(frame, 'Keep Your Face infront of Camera', (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (255, 255, 255), 2)
        
        cv2.putText(frame, 'Starting', (260, 270), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (255, 255, 255), 2)
        
        cv2.putText(frame, str(i), (290, 330), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.3, (255, 255, 255), 3)

        i-=1
                   
        cv2.imshow('frame', frame)
        cv2.waitKey(1000)
        
        if i < 0:
            break
            
    start_time = time.time()        
    img_path = './saved_image/1.jpg'

    ## Face recognition 
    while True:
        curr_time = time.time()
        
        _, frame = cap.read()
        frame = cv2.flip(frame, 1, 0)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        face = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(face) == 1:
            for(x, y, w, h) in face:
                roi = frame[y-10:y+h+10, x-10:x+w+10]

                fh, fw = roi.shape[:2]

                #make sure the face roi is of required height and width
                if fh < 20 and fw < 20:
                    continue

                face_found = True
                #cv2.imwrite(img_path, roi)

                cv2.rectangle(frame, (x-10,y-10), (x+w+10, y+h+10), (255, 200, 200), 2)

         
        if curr_time - start_time >= 3:
            break
            
        cv2.imshow('frame', frame)
        cv2.waitKey(1)
            
    cap.release()        
    cv2.destroyAllWindows()

    
    if face_found:
        img = cv2.resize(roi, (96, 96))

        db[name] = img_to_encoding(img)

        with open('./face_database/embeddings.pickle', "wb") as database:
            pickle.dump(db, database, protocol=pickle.HIGHEST_PROTOCOL)
    
    elif len(face) > 1:
        print("More than one faces found. Try again...")
        return
    
    else:
        print('There was no face found in the frame. Try again...')
        return


#Adding a New User's voice
 #Voice authentication
  FORMAT = pyaudio.paInt16
  CHANNELS = 2
  RATE = 44100
  CHUNK = 1024
  RECORD_SECONDS = 3
  
  source = "./voice_database/" + name
  
 
  os.mkdir(source)

  for i in range(3):
      audio = pyaudio.PyAudio()

      if i == 0:
          j = 3
          while j>=0:
              time.sleep(1.0)
              print("Speak your name in {} seconds".format(j))
              clear_output(wait=True)

              j-=1

      elif i ==1:
          print("Speak your name one more time")
          time.sleep(0.5)

      else:
          print("Speak your name one last time")
          time.sleep(0.5)

      # start Recording
      stream = audio.open(format=FORMAT, channels=CHANNELS,
                  rate=RATE, input=True,
                  frames_per_buffer=CHUNK)

      print("recording...")
      frames = []

      for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
          data = stream.read(CHUNK)
          frames.append(data)

      # stop Recording
      stream.stop_stream()
      stream.close()
      audio.terminate()
      
      # saving wav file of speaker
      waveFile = wave.open(source + '/' + str((i+1)) + '.wav', 'wb')
      waveFile.setnchannels(CHANNELS)
      waveFile.setsampwidth(audio.get_sample_size(FORMAT))
      waveFile.setframerate(RATE)
      waveFile.writeframes(b''.join(frames))
      waveFile.close()
      print("Done")

  dest =  "./gmm_models/"
  count = 1

  for path in os.listdir(source):
      path = os.path.join(source, path)

      features = np.array([])
      
      # reading audio files of speaker
      (sr, audio) = read(path)
      
      # extract 40 dimensional MFCC & delta MFCC features
      vector   = extract_features(audio,sr)

      if features.size == 0:
          features = vector
      else:
          features = np.vstack((features, vector))
          
      # when features of 3 files of speaker are concatenated, then do model training
      if count == 3:    
          gmm = GMM(n_components = 16, n_iter = 200, covariance_type='diag',n_init = 3)
          gmm.fit(features)

          # saving the trained gaussian model
          pickle.dump(gmm, open(dest + name + '.gmm', 'wb'))
          print(name + ' added successfully') 
          
          features = np.asarray(())
          count = 0
      count = count + 1

if __name__ == '__main__':
  add_user()


#/Voice Authentication
def recognize():
   # Voice Authentication
   FORMAT = pyaudio.paInt16
   CHANNELS = 2
   RATE = 44100
   CHUNK = 1024
   RECORD_SECONDS = 3
   FILENAME = "./test.wav"

   audio = pyaudio.PyAudio()
  
   # start Recording
   stream = audio.open(format=FORMAT, channels=CHANNELS,
                   rate=RATE, input=True,
                   frames_per_buffer=CHUNK)

   print("recording...")
   frames = []

   for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
       data = stream.read(CHUNK)
       frames.append(data)
   print("finished recording")


   # stop Recording
   stream.stop_stream()
   stream.close()
   audio.terminate()

   # saving wav file 
   waveFile = wave.open(FILENAME, 'wb')
   waveFile.setnchannels(CHANNELS)
   waveFile.setsampwidth(audio.get_sample_size(FORMAT))
   waveFile.setframerate(RATE)
   waveFile.writeframes(b''.join(frames))
   waveFile.close()

   modelpath = "./gmm_models/"

   gmm_files = [os.path.join(modelpath,fname) for fname in 
               os.listdir(modelpath) if fname.endswith('.gmm')]

   models    = [pickle.load(open(fname,'rb')) for fname in gmm_files]

   speakers   = [fname.split("/")[-1].split(".gmm")[0] for fname 
               in gmm_files]
 
   #read test file
   sr,audio = read(FILENAME)
   
   # extract mfcc features
   vector = extract_features(audio,sr)
   log_likelihood = np.zeros(len(models)) 

   #checking with each model one by one
   for i in range(len(models)):
       gmm = models[i]         
       scores = np.array(gmm.score(vector))
       log_likelihood[i] = scores.sum()

   pred = np.argmax(log_likelihood)
   identity = speakers[pred]
  
   # if voice not recognized than terminate the process
   if identity == 'unknown':
           print("Not Recognized! Try again...")
           return
   
   print( "Recognized as - ", identity)


#Face Recognition
   # face recognition
   print("Keep Your face infront of the camera")
   cap = cv2.VideoCapture(0)
   cap.set(3, 640)
   cap.set(4, 480)

   cascade = cv2.CascadeClassifier('./haarcascades/haarcascade_frontalface_default.xml')
   
   #loading the database 
   database = pickle.load(open('face_database/embeddings.pickle', "rb"))
   
   time.sleep(1.0)
   
   start_time = time.time()
   
   while True:
       curr_time = time.time()
           
       _, frame = cap.read()
       frame = cv2.flip(frame, 1, 0)
       gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

       face = cascade.detectMultiScale(gray, 1.3, 5)
        
       name = 'unknown'
       
       
       if len(face) == 1:

           for (x, y, w, h) in face:
               roi = frame[y-10:y+h+10, x-10:x+w+10]
           
               fh, fw = roi.shape[:2]
               min_dist = 100
               
               #make sure the face is of required height and width
               if fh < 20 and fh < 20:
                   continue

               
               #resizing image as required by the model
               img = cv2.resize(roi, (96, 96))

               #128 d encodings from pre-trained model
               encoding = img_to_encoding(img)
               
               # loop over all the recorded encodings in database 
               for knownName in database:
                   # find the similarity between the input encodings and recorded encodings in database using L2 norm
                   dist = np.linalg.norm(np.subtract(database[knownName], encoding) )
                   # check if minimum distance or not
                   if dist < min_dist:
                       min_dist = dist
                       name = knownName

           # if min dist is less then threshold value and face and voice matched than unlock the door
           if min_dist < 0.4 and name == identity:
               print ("Door Unlocked! Welcome " + str(name))
               break

       #open the cam for 3 seconds
       if curr_time - start_time >= 3:
           break    

       cv2.waitKey(1)
       cv2.imshow('frame', frame)
       
   cap.release()
   cv2.destroyAllWindows()
  
   if len(face) == 0:
       print('There was no face found in the frame. Try again...')
       
   elif len(face) > 1:
       print("More than one faces found. Try again...")
       
   elif min_dist > 0.5 or name != identity:
       print("Not Recognized! Try again...")
  
       
if __name__ == '__main__':
   recognize()

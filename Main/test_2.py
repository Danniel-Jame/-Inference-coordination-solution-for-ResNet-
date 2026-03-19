from matplotlib import pyplot as plt
import re
# USAGE
# python recognize_faces_image.py --encodings encodings.pickle --image examples/example_01.png 

# import the necessary packages
import face_recognition
import pickle
import cv2
from imutils import paths # to get paths
import os
import numpy
import time
import pandas as pd
from frontend2 import frontend_queue
from frontend2 import update_image, update_progress_bar
import threading
from frontend2 import start_frontend


# for cross-functions
from cv2 import dnn_superres
from matplotlib import pyplot as plt
from PIL import Image
import warnings

def show_image(title, img):
      show = img[:,:,::-1] # needed to reverse colour properly. select all the elements on the first axis, all the elements on the seconds, and then the reverse of the elements on the third axis.
      plt.imshow(show)
      plt.title(title)
      plt.show()

def optimizeImage(imagePath, modelPath):
    # Create an SR object
    sr = dnn_superres.DnnSuperResImpl_create()
    
    # Get model name, get text between '/' & '_'
    modelName = modelPath.split('/')[1].split('_')[0].lower()

    # Get scale
    scale = int(modelPath.split('/')[1].split('_')[1].split('.')[0][1])

    # Display the name and scale
    # print("Model name: "+ modelName)
    # print("Model scale: " + str(modelScale))

    # Read image
    image = cv2.imread(imagePath)
    
    # Read the desired model
    sr.readModel(modelPath)

    # Set the desired model and scale to get correct pre- and post-processing
    sr.setModel(modelName, scale)

    # Upscale the image
    result = sr.upsample(image)

    # Save the image (optional)
    #cv2.imwrite("./examples/upscaled-fsrcnn_x4.jpg", result)
    
    return result

## for use in bicubic START
def scaleImage(imagePath, factor, algorithm):
    # Read image
    image = Image.open(imagePath)
    imgSize = (image.width * factor, image.height * factor)

    # Upscale the image
    result = image.resize(imgSize, algorithm)

    return result

# for non-opencv use
def display_image(title, img):
      plt.imshow(img)
      plt.title(title)
      plt.show()
## for use in bicubic END

def send_to_frontend(image_rgb, boxes, names, text_info):
    update_image(image_rgb, boxes, names, text_info)


# detection_mode: # variable for setting detection method, either: 'scale', 'ai', or anything else for 'direct'
def recognize_face(detection_mode):
    # benchmark time
    start_time = time.time()
    # variables for detection accuracy
    identify_correct = 0
    identify_wrong = 0
    identify_none = 0

    # Load the model
    # load the known faces and embeddings
    print("[INFO] loading encodings...")
    clf = pickle.loads(open(args["encodings"], "rb").read())
    
    # fig, (ax_img, ax_text) = plt.subplots(1, 2, figsize=(7, 5))
    # fig.canvas.manager.set_window_title("Thông tin nhận diện khuôn mặt")  # đặt tên cửa sổ
    # ax_img.axis("off")
    # ax_text.axis("off")
    # ax_img.set_title("Ảnh khuôn mặt", fontsize=12)
    # text_obj = ax_text.text(0.05, 0.8, "", fontsize=12, verticalalignment='top', wrap=True)

    # plt.ion()  # bật chế độ interactive
    # plt.show()

    for imagePath in imagePaths:
        progress = int((imagePaths.index(imagePath) + 1) / len(imagePaths) * 100)
        update_progress_bar(progress)

        if (detection_mode == "scale"):
            pil_img = scaleImage(imagePath, 4, Image.BICUBIC)
            image = cv2.cvtColor(numpy.array(pil_img), cv2.COLOR_RGB2BGR)
            # print("scaling")
        elif (detection_mode == "ai"):
            image = optimizeImage(imagePath, "models/EDSR_x4.pb")
            # print("ai")
        else:
            pil_img = scaleImage(imagePath, 4, Image.NEAREST)
            image = cv2.cvtColor(numpy.array(pil_img), cv2.COLOR_RGB2BGR)
            # print("direct")
            
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # detect the (x, y)-coordinates of the bounding boxes corresponding
        # to each face in the input image, then compute the facial embeddings
        # for each face
        print("[INFO] recognizing faces in ", imagePath)
        boxes = face_recognition.face_locations(rgb, model=args["detection_method"])
        encodings = face_recognition.face_encodings(rgb, boxes)
        # initialize the list of names for each face detected
        names = []
        for encoding in encodings:
            try:
                predicted = clf.predict([encoding])[0]
            except:
                predicted = "Unknown"
            names.append(predicted)

        
        # for encoding in encodings:
        #     name = "Unknown"
        #     name = clf.predict([encoding])[0]
        #     names.append(name)

        # loop over the recognized faces
        # for ((top, right, bottom, left), name) in zip(boxes, names):
        #     # draw the predicted face name on the image
        #     cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 1)
        #     y = top - 15 if top - 15 > 15 else top + 15
        #     print(name)
        #     cv2.putText(image, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


        correctName = [imagePath.split(os.path.sep)[1]] # 0 is root directory, 1 is subfolder (name), 2 is image name
        if names == correctName:
            print("Correct face recognized")
            identify_correct += 1
        else:
            print("Folder name is: ", correctName, ". However, face detected is:", names)
            if names: #implicit booliness
                identify_wrong += 1
            else:
                identify_none += 1
        
        
        image = cv2.imread(imagePath)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # === Lấy thông tin từ đường dẫn ===
        folder_name = os.path.basename(os.path.dirname(imagePath))
        parts = folder_name.split('_')
        name       = parts[0] if len(parts) > 0 else ""
        birth_year = parts[1] if len(parts) > 1 else ""
        id_code    = parts[2] if len(parts) > 2 else ""
        address    = parts[3] if len(parts) > 3 else ""

        text_info = f"Tên: {name}\nĐịa chỉ: {birth_year}\nNăm sinh: {id_code}\nMã định danh: {address}"

        # === Cập nhật ảnh và thông tin trên figure có sẵn ===
        send_to_frontend(image_rgb, boxes, names, text_info)
        time.sleep(3)

        # === Dừng chờ người dùng nhấn Enter ===
        # input("Nhấn Enter để xem ảnh tiếp theo...")


    totalPictures = len(imagePaths)
    if (totalPictures > 0):
        print("Summary")
        print("==========================")
        print("Total pictures", totalPictures)
        print("Faces identified correctly: ", identify_correct)
        print("Faces identified wrongly: ", identify_wrong)
        print("Faces not identified: ", identify_none)
        print("Absolute Accuracy (correct / [correct + incorrect + not detected]) * 100%: ")
        print(round(identify_correct / (identify_correct + identify_wrong + identify_none), 2) * 100, "%")
        print("Detection Accuracy [(correct + incorrect) / total] * 100%: ")
        print(round(((identify_correct + identify_wrong) / totalPictures) * 100, 2), "%")
        print("END, time taken: ", round((time.time() - start_time), 2), "seconds")
        print("Avg. secs. per picture: ", round((time.time() - start_time) / totalPictures, 2), "seconds")
        print("==========================")
    else:
        print("[INFO] No detections made. No pictures found.")
    
args = {}
args["encodings"] = r"C:\Users\Nam Nguyen Thanh\Downloads\blockdrop-simulation\blockdrop-simulation\models sr\svm-face.pickle"
args["dataset"] = r"C:\Users\Nam Nguyen Thanh\Downloads\blockdrop-simulation\blockdrop-simulation\dataset\test"
# args["dataset"] = "./dataset/test"
args["detection_method"] = "hog"
imagePaths = list(paths.list_images(args["dataset"]))
# print(imagePaths)
print("Arguments set!")

print("Face identification: Direct without any image enhancement")
print("=========================================================")

if __name__ == "__main__":
    print("Đang khởi động frontend…")

    # Khởi chạy GUI trong thread riêng
    gui_thread = threading.Thread(target=start_frontend, daemon=True)
    gui_thread.start()

    print("Backend đang chạy…")
    recognize_face("scale")
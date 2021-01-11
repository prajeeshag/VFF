
import cv2
import sys
import numpy as np


def faceCrop(imagePath):

    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faceCascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(30, 30)
    )

    height, width = image.shape[:2]

    for (x, y, w, h) in faces:
        x0 = int((2*x+w)*0.5)
        y0 = int((2*y+h)*0.5)
        w0 = np.amin(np.array([x0, y0, width-x0, height-y0]))
        x1 = x0-w0
        y1 = y0-w0
        w1 = int(w0*2)
        h1 = w1
        return x1, y1, w1, h1

    return None, None, None, None


if __name__ == "__main__":
    imagePath = sys.argv[1]
    x1, y1, w1, h1 = faceCrop(imagePath)
    if x1 is None:
        print('Could not find faces')
        sys.exit()

    image = cv2.imread(imagePath)
    cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
    status = cv2.imwrite('faces_detected.jpg', image)

import numpy as np
import cv2
import os

# Process image of pdf pages using opencv library (Computer Vision)

def find_images(file_name, dirname):
    print("Processing " + file_name)
    im = cv2.imread(file_name)
    im_original = im.copy()
    
    bg_color = [255, 255, 255]
    
    # Convert image to grayscale and then convert into a binary image
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    imblur = cv2.GaussianBlur(imgray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(imblur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C ,cv2.THRESH_BINARY_INV,11,2)

    # Find all the contours of our binary image
    im2,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    
    # Loop through each contour and check if it is small enough to be texts
    # If we determine it is text, then fill a white rectangle to remove text
    for cnt in contours:
        [x,y,w,h] = cv2.boundingRect(cnt)
        if w < 33 or h < 33:
            rect = cv2.minAreaRect(cnt)
            box = np.int0(cv2.boxPoints(rect))
            cv2.drawContours(im,[box],0,bg_color,-1)
    
    # Makes a second contour pass-through to find the images
    
    # Convert image to grayscale and then convert into a binary image
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    imblur = cv2.GaussianBlur(imgray, (5,5), 0)
    thresh = cv2.adaptiveThreshold(imblur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
    
    # Find all the contours of our binary image
    im2,contours,hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    
    # Loop through each contour and check if it is big enough to be a figure
    rectList = []
    imheight, imwidth, imchannel = im_original.shape
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if w > 33 and h > 33:
            rect = [x, y, x+w, y+h]
            rectList.append(rect)
    rectList = np.asarray(rectList)
    
    # Inflate the rectangles to cover the figures
    for i in range(0, rectList.shape[0]):
        rect = rectList[i,:]
        rectList[i,:] = inflate(rect, im_original.copy())
    
    # Correct for overlapping contour lines by merging them together
    i = 0; j = 0
    while i < rectList.shape[0]:
        while j < rectList.shape[0]:
            if i != j:
                rect1 = rectList[i,:]
                rect2 = rectList[j,:]
                if intersection(rect1, rect2):
                    rectList[i,:] = union(rect1, rect2)
                    rectList = np.delete(rectList, j, 0)
                    if (i > j): i -= 1
                    j = -1
            j += 1
        i += 1
        j = 0
    
    # Crop the image given rectangle covering the figure
    for i in range(0, rectList.shape[0]):
        [x1, y1, x2, y2]  = rectList[i,:]
        roi = im_original[y1:y2, x1:x2]
        [roi_width, roi_height, roi_channel] = roi.shape
        padding_h = round(0.05 * roi_height + 33)
        padding_w = round(0.05 * roi_width + 33)
        roi = cv2.copyMakeBorder(roi, padding_h, padding_h, padding_w, padding_w, cv2.BORDER_CONSTANT, value=bg_color)
        output = file_name[0:-4] + '-image-%i.png' %(i+1)
        cv2.imwrite(os.path.join(dirname, output), roi)
    
    # Output the results found in the page
    print("%i figure(s) founds." % rectList.shape[0])

# Create a rectangle that contains a and b inside
def union(a,b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))

# Return true if the area of intersection between a and b is greater than a threshold
def intersection(a,b,th=0):
    overlapx = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    overlapy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    overlaparea = overlapx * overlapy
    return overlaparea > th

# Expand the given rectangle by a given amount in all four faces
def inflate(rect, image):
    amnt = 3
    thresh = 230
    imheight, imwidth, imchannel = image.shape
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    (x1, y1, x2, y2) = rect
    
    sides = 1
    while sides:
        sides = 0
        left = image[y1:y2, (x1-amnt):(x1)]
        top = image[(y1-amnt):(y1), x1:x2]
        right = image[y1:y2, (x2):(x2+amnt)]
        bottom = image[(y2):(y2+amnt), x1:x2]
        
        if (left<thresh).any() and x1 > 0:
            x1 = max(0,x1-amnt)
            sides = sides + 1
        if (top<thresh).any() and y1 > 0:
            y1 = max(0, y1-amnt)
            sides = sides + 1
        if (right<thresh).any() and x2 < imwidth:
            x2 = min(x2+amnt, imwidth)
            sides = sides + 1
        if (bottom<thresh).any() and y2 < imheight:
            y2 = min(y2+amnt, imheight)
            sides = sides + 1
    return [x1, y1, x2, y2]

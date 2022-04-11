import cv2
import numpy as np
  
path = "gfg.jpeg"
  
image = cv2.imread(path)
  
window_name = 'Image'
  
pts = np.array([[25, 70], [25, 160], 
                [110, 200], [200, 160], 
                [200, 70], [110, 20]],
               np.int32)
  
pts = pts.reshape((-1, 1, 2))
  
isClosed = True
color = (255, 0, 0)
  
thickness = 2
  
image = cv2.polylines(image, [pts], isClosed, color, thickness)
  
while(1):
    cv2.imshow('image', image)
    if cv2.waitKey(20) & 0xFF == 27:
        break
          
cv2.destroyAllWindows()
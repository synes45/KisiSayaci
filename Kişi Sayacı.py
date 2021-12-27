##Kişi sayacı
##from picamera.array import PiRGBArray
##from picamera import PiCamera
import numpy as np
import cv2 as cv
import Kişi
import time

try:
    log = open('log.txt',"w")
except:
    print("Kayıt dosyası açılamıyor")

#Giriş ve çıkış sayaçları
cnt_up   = 0
cnt_down = 0

#Video kaynağı
#cap = cv.VideoCapture(0)
cap = cv.VideoCapture('Test Files/TestVideo.avi')
#camera = PiCamera()
##camera.resolution = (160,120)
##camera.framerate = 5
##rawCapture = PiRGBArray(camera, size=(160,120))
##time.sleep(0.1)

#Video Özellikleri
##cap.set(3,160) #Width
##cap.set(4,120) #Height

#Yakalama özelliklerini konsola yazdırma
for i in range(19):
    print( i, cap.get(i))

h = 480
w = 640
frameArea = h*w
areaTH = frameArea/250
print( 'Alan Eşiği', areaTH)

#Giriş / çıkış hatları
line_up = int(2*(h/5))
line_down   = int(3*(h/5))

up_limit =   int(1*(h/5))
down_limit = int(4*(h/5))

print( "Kırmızı Çizgi y:",str(line_down))
print( "Mavi Çizgi y:", str(line_up))
line_down_color = (255,0,0)
line_up_color = (0,0,255)
pt1 =  [0, line_down];
pt2 =  [w, line_down];
pts_L1 = np.array([pt1,pt2], np.int32)
pts_L1 = pts_L1.reshape((-1,1,2))
pt3 =  [0, line_up];
pt4 =  [w, line_up];
pts_L2 = np.array([pt3,pt4], np.int32)
pts_L2 = pts_L2.reshape((-1,1,2))

pt5 =  [0, up_limit];
pt6 =  [w, up_limit];
pts_L3 = np.array([pt5,pt6], np.int32)
pts_L3 = pts_L3.reshape((-1,1,2))
pt7 =  [0, down_limit];
pt8 =  [w, down_limit];
pts_L4 = np.array([pt7,pt8], np.int32)
pts_L4 = pts_L4.reshape((-1,1,2))

#Kişi azaltıcı
fgbg = cv.createBackgroundSubtractorMOG2(detectShadows = True)

#Yapı bilimsel filtreler için yapılandırma elemanları
kernelOp = np.ones((3,3),np.uint8)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((11,11),np.uint8)

#Değişkenler
font = cv.FONT_HERSHEY_SIMPLEX
persons = []
max_p_age = 5
pid = 1

while(cap.isOpened()):
##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    #Video kaynağından bir görsel okuma
    ret, frame = cap.read()
##    frame = image.array

    for i in persons:
        i.age_one()
    #########################
    #       ÖN İŞLEME       #
    #########################
    
    #Arka plan çıkarma
    fgmask = fgbg.apply(frame)
    fgmask2 = fgbg.apply(frame)

    #Gölgeleri kaldırmak için ikilileştirme (gri renk)
    try:
        ret,imBin= cv.threshold(fgmask,200,255,cv.THRESH_BINARY)
        ret,imBin2 = cv.threshold(fgmask2,200,255,cv.THRESH_BINARY)
        #Gürültüyü gidermek için açma (aşınma-> genişletme).
        mask = cv.morphologyEx(imBin, cv.MORPH_OPEN, kernelOp)
        mask2 = cv.morphologyEx(imBin2, cv.MORPH_OPEN, kernelOp)
        #Beyaz bölgeleri birleştirmek için kapatma (genişletme -> aşındırma).
        mask =  cv.morphologyEx(mask , cv.MORPH_CLOSE, kernelCl)
        mask2 = cv.morphologyEx(mask2, cv.MORPH_CLOSE, kernelCl)
    except:
        print('SONUÇ')
        print( 'GİREN:',cnt_up)
        print ('ÇIKAN:',cnt_down)
        break
    #################
    #   KONTURLAR   #
    #################
    
    # RETR_EXTERNAL yalnızca aşırı dış alanları döndürür. Tüm çocuk konturları geride bırakılır.
    contours0, hierarchy = cv.findContours(mask2,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    for cnt in contours0:
        area = cv.contourArea(cnt)
        if area > areaTH:
            #################
            #     İzleme    #
            #################
            
            #Geriye çok kişili, ekran çıktıları ve girdileri için koşullar eklemek kalıyor.
            
            M = cv.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv.boundingRect(cnt)

            new = True
            if cy in range(up_limit,down_limit):
                for i in persons:
                    if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                        # nesne daha önce tespit edilmiş olana yakın
                        new = False
                        i.updateCoords(cx,cy)   #nesnedeki koordinatları günceller ve yaşı sıfırlar
                        if i.going_UP(line_down,line_up) == True:
                            cnt_up += 1;
                            print( "ID:",i.getId(),' girdi ',time.strftime("%c"))
                            log.write("ID: "+str(i.getId())+' girdi ' + time.strftime("%c") + '\n')
                        elif i.going_DOWN(line_down,line_up) == True:
                            cnt_down += 1;
                            print( "ID:",i.getId(),' cikti ',time.strftime("%c"))
                            log.write("ID: " + str(i.getId()) + ' cikti ' + time.strftime("%c") + '\n')
                        break
                    if i.getState() == '1':
                        if i.getDir() == ' cikti' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == ' girdi' and i.getY() < up_limit:
                            i.setDone()
                    if i.timedOut():
                        #i'yi kişi listesinden çıkar
                        index = persons.index(i)
                        persons.pop(index)
                        del i     #hafızayı temizleme
                if new == True:
                    p = Kişi.MyPerson(pid,cx,cy, max_p_age)
                    persons.append(p)
                    pid += 1     
            #################
            #   ÇİZİMLER    #
            #################
            cv.circle(frame,(cx,cy), 5, (0,0,255), -1)
            img = cv.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)            
            #cv.drawContours(frame, cnt, -1, (0,255,0), 3)
            
    #contours0'da cnt için SON
            
    #########################
    #    ÇİZİM PARÇALARI    #
    #########################
    for i in persons:
##        if len(i.getTracks()) >= 2:
##            pts = np.array(i.getTracks(), np.int32)
##            pts = pts.reshape((-1,1,2))
##            frame = cv.polylines(frame,[pts],False,i.getRGB())
##        if i.getId() == 9:
##            print str(i.getX()), ',', str(i.getY())
        cv.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3,i.getRGB(),1,cv.LINE_AA)
        
    #################
    #   GÖRÜNTÜLER  #
    #################
    str_up = 'GIREN: '+ str(cnt_up)
    str_down = 'CIKAN: '+ str(cnt_down)
    frame = cv.polylines(frame,[pts_L1],False,line_down_color,thickness=2)
    frame = cv.polylines(frame,[pts_L2],False,line_up_color,thickness=2)
    frame = cv.polylines(frame,[pts_L3],False,(255,255,255),thickness=1)
    frame = cv.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)
    cv.putText(frame, str_up ,(10,40),font,0.5,(255,255,255),2,cv.LINE_AA)
    cv.putText(frame, str_up ,(10,40),font,0.5,(0,0,255),1,cv.LINE_AA)
    cv.putText(frame, str_down ,(10,90),font,0.5,(255,255,255),2,cv.LINE_AA)
    cv.putText(frame, str_down ,(10,90),font,0.5,(255,0,0),1,cv.LINE_AA)

    cv.imshow('Goruntu',frame)
    cv.imshow('Kalip',mask)    
    

##    rawCapture.truncate(0)
    #çıkmak için ESC'ye basın
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break
#SON while(cap.isOpened())
    
#################
#   TEMİZLEME   #
#################
log.flush()
log.close()
cap.release()
cv.destroyAllWindows()

#coding=utf-8
import cv2
import numpy as np
import mvsdk
import platform
import time
import cv2.aruco as aruco
import imutils
import winsound
from playsound import playsound

from pickle import FRAME
from matplotlib import image
from tkinter import N
from csv import DictWriter
import datetime
import csv






class Camera(object):
  def __init__(self, DevInfo):
    super(Camera, self).__init__()
    self.DevInfo = DevInfo
    self.hCamera = 0
    self.cap = None
    self.pFrameBuffer = 0

  def open(self):
    if self.hCamera > 0:
      return True

    # 打开相机
    hCamera = 0
    try:
      hCamera = mvsdk.CameraInit(self.DevInfo, -1, -1)
    except mvsdk.CameraException as e:
      print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
      return False

    # 获取相机特性描述
    cap = mvsdk.CameraGetCapability(hCamera)

    # 判断是黑白相机还是彩色相机
    monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

    # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
    if monoCamera:
      mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)
    else:
      mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_BGR8)

    # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
    FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)

    # 分配RGB buffer，用来存放ISP输出的图像
    # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
    pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

    # 相机模式切换成连续采集
    mvsdk.CameraSetTriggerMode(hCamera, 0)

    # 手动曝光，曝光时间30ms
    mvsdk.CameraSetAeState(hCamera, 0)
    mvsdk.CameraSetExposureTime(hCamera, 30 * 1000)

    # 让SDK内部取图线程开始工作
    mvsdk.CameraPlay(hCamera)

    self.hCamera = hCamera
    self.pFrameBuffer = pFrameBuffer
    self.cap = cap
    return True

  def close(self):
    if self.hCamera > 0:
      mvsdk.CameraUnInit(self.hCamera)
      self.hCamera = 0

    mvsdk.CameraAlignFree(self.pFrameBuffer)
    self.pFrameBuffer = 0

  def grab(self):
    # 从相机取一帧图片
    hCamera = self.hCamera
    pFrameBuffer = self.pFrameBuffer
    try:
      pRawData, FrameHead = mvsdk.CameraGetImageBuffer(hCamera, 200)
      mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
      mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

      # windows下取到的图像数据是上下颠倒的，以BMP格式存放。转换成opencv则需要上下翻转成正的
      # linux下直接输出正的，不需要上下翻转
      if platform.system() == "Windows":
        mvsdk.CameraFlipFrameBuffer(pFrameBuffer, FrameHead, 1)
      
      # 此时图片已经存储在pFrameBuffer中，对于彩色相机pFrameBuffer=RGB数据，黑白相机pFrameBuffer=8位灰度数据
      # 把pFrameBuffer转换成opencv的图像格式以进行后续算法处理
      frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
      frame = np.frombuffer(frame_data, dtype=np.uint8)
      frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )
      return frame
    except mvsdk.CameraException as e:
      if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
        print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message) )
      return None


def nothing(a):
    pass
cv2.namedWindow('ALARMA', cv2.WINDOW_NORMAL )
cv2.resizeWindow('ALARMA', 1280 , 800)
cv2.createTrackbar('DER AMPL','ALARMA',0,500,nothing)
cv2.createTrackbar('DER REDU','ALARMA',0,500,nothing)
cv2.createTrackbar('IZQ AMPL','ALARMA',0,400,nothing)
cv2.createTrackbar('IZQ REDU','ALARMA',0,400,nothing)
#cv2.createTrackbar('SS','Ajuste color',0,255,nothing)
#cv2.createTrackbar('VV','Ajuste color',0,255,nothing)
#cv2.createTrackbar('DST','Ajuste color',-50,150,nothing)

def TratamientoImagen(foto,corners_int,h1,s1,v1,hh1,ss1,vv1,ajuste,t,f,g,z,r,t4):


    

    #momentos de imagen
    perimetro_aruco = cv2.arcLength(corners_int[0], True)
    #print(perimetro_aruco)
    lado_aruco=perimetro_aruco/4
    #print(lado_aruco)
    proporcion_cm = (perimetro_aruco/20)
    peri = np.int0(proporcion_cm)
    #print(proporcion_cm)
                

    if foto is not None:
      puntos = []
      
      
      imagen_HSV = cv2.cvtColor(foto, cv2.COLOR_BGR2HSV)
      glassBajo = np.array([h1, s1, v1], np.uint8)
      glassAlto = np.array([hh1, ss1, vv1], np.uint8)
      maskglass = cv2.inRange(imagen_HSV, glassBajo, glassAlto)
      #cv2.imshow("maskglass", maskglass)
          
      
      cnts = cv2.findContours(maskglass, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
      cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:1]
      
      
      
      for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(foto, (x, y), (x+w, y+h), (255, 0, 0), 2)
        puntos.append([x, y, w, h])
        
      
      
      x1, y1, w1, h1 = puntos[0]

      x2=t
      y2=f
      w2=g
      h2=z

      y3=y2-30

     # playsound(C:\Users\Administrator\Documents\15_11_2023\sonido.mp3
        
      
      if x1 < x2: #### derecho
        distancia_pixeles = abs(x2 - (x1+w1))
        distancia_cm = (distancia_pixeles*ajuste)/30.26   ###ojo en la formula de distancia_cm el valor de 30 es el lado del aruco  
        cv2.putText(foto, "{:.2f} cm".format(distancia_cm), (x1+w1+distancia_pixeles//2, y3-30), 2, 0.8, (0,0,255), 1, cv2.LINE_AA)
        cv2.line(foto,(x1+w1,y3-20),(x2, y3-20),(0, 0, 255),2)#horizontal
        cv2.line(foto,(x1+w1,y3-30),(x1+w1, y3-10),(0, 0, 255),2)#dere
        cv2.line(foto,(x2,y3-30),(x2, y3-10),(0, 0, 255),2)#izq
        #print(x1)

        # lineas para generar alarma
        cv2.line(foto,((r+70),300-20),((t4+70), 300-20),(0,255,0),1)#horizontal
        cv2.line(foto,((r+70),300-30),((r+70), 300-10),(0,255,0),1)#dere
        cv2.line(foto,((t4+70),300-30),((t4+70), 300-10),(0,255,0),1)#izq
        distancia_pixeles1 = abs((t4+70) - (r+70))
        distancia_cm1 = (distancia_pixeles1*ajuste)/30.26 ###ojo en la formula de distancia_cm el valor de 30 es el lado del aruco
        #print(distancia_cm1)
        cv2.putText(foto, "{:.2f} cm".format(distancia_cm1), (r+70+distancia_pixeles1//2, 356-30), 2, 0.8, (0,0,255), 1, cv2.LINE_AA)


        
        if (w1+68) > r:
          #print("alarma")
          cv2.putText(foto, 'Ampliacion', (40,470),1,2,
                  (0,255,0),2)
          frecuencia=440
          duracion_milisegundos=5*8
          winsound.Beep(frecuencia,duracion_milisegundos)

        elif (w1+68) < t4:
          #print("alarma")
          cv2.putText(foto, 'Reduccion', (40,470),1,2,
                  (0,255,0),2)        
          frecuencia=440
          duracion_milisegundos=5*8
          winsound.Beep(frecuencia,duracion_milisegundos)
        
       
        
        
      else:     #### izquierdo
        distancia_pixeles = abs(x1 - (x2+w2))
        distancia_cm = (distancia_pixeles*ajuste)/30  ###ojo en la formula de distancia_cm el valor de 30 es el lado del aruco
        cv2.putText(foto, "{:.2f} cm".format(distancia_cm), (x2+w2+distancia_pixeles//2, y2-30), 2, 0.8, (0,0,255), 1, cv2.LINE_AA)
        cv2.line(foto,(x2+w2,y2-20),(x1, y2-20),(0, 0, 255),2)#horizontal
        cv2.line(foto,(x2+w2,y2-30),(x2+w2, y2-10),(0, 0, 255),2)#izq
        cv2.line(foto,(x1,y2-30),(x1, y2-10),(0, 0, 255),2)#dere


        #print(x1)
        # lineas para generar alarma
        cv2.line(foto,((r+94),300-20),((t4+94), 300-20),(0,255,0),1)#horizontal
        cv2.line(foto,((r+94),300-30),((r+94), 300-10),(0,255,0),1)#dere
        cv2.line(foto,((t4+94),300-30),((t4+94), 300-10),(0,255,0),1)#izq
        distancia_pixeles2 = abs((r+86) - (t4+86))
        distancia_cm2 = (distancia_pixeles2*ajuste)/30 ###ojo en la formula de distancia_cm el valor de 30 es el lado del aruco
        #print(t4)
        cv2.putText(foto, "{:.2f} cm".format(distancia_cm2), (r+86+distancia_pixeles2//2, 356-30), 2, 0.8, (0,0,255), 1, cv2.LINE_AA)

        if (x1-95) > r:
          #print("alarma")
          #playsound(cancion)
          cv2.putText(foto, 'Reduccion', (40,470),1,2,
                  (0,255,0),2)
          frecuencia=440
          duracion_milisegundos=5*8
          winsound.Beep(frecuencia,duracion_milisegundos)            

        if (x1-95) < t4:
          #print("alarma")
          cv2.putText(foto, 'Ampliacion', (40,470),1,2,
                  (0,255,0),2)          
          frecuencia=440
          duracion_milisegundos=5*8
          winsound.Beep(frecuencia,duracion_milisegundos)          
          

      
      maskglass = cv2.cvtColor(maskglass, cv2.COLOR_GRAY2BGR)
      maskglass = imutils.resize(maskglass,height=(maskglass.shape[0] // 2))
      
      
      concat_v = cv2.vconcat([maskglass,maskglass])
      concat_h = cv2.hconcat([foto, concat_v])
      
      cv2.putText(concat_h, 'medida', (10,20),1,1.5,
              (0,255,0),2)
      cv2.putText(concat_h, 'maskReferencia', (650,20),1,1.5,
              (0,255,0),2)
      cv2.putText(concat_h, 'maskglass', (650,260),1,1.5,
              (0,255,0),2)
      
      #cv2.imshow('concat_h',concat_h)

    return foto , distancia_cm
#############
def almacenamiento(izquierda3 , derecha3 , ancho_bruto):
        
  fechaActual = datetime.datetime.now()
  rounded_fechaActual= fechaActual.replace(microsecond=0)
  headersCSV = ['Fecha  &  Hora','Lado Izquierdo','Lado derecho', 'Ancho Bruto']      
  dict={'Fecha  &  Hora':     rounded_fechaActual     ,'Lado Izquierdo':  izquierda3    ,'Lado derecho':   derecha3 ,'Ancho Bruto':  ancho_bruto }
    
  with open('base.csv', 'a', newline='') as f_object:
      
    dictwriter_object = DictWriter(f_object, fieldnames=headersCSV)
    dictwriter_object.writerow(dict)
    f_object.close()
############################



##############################
def main_loop():
  # 枚举相机
  DevList = ["169.254.172.241","169.254.72.240"]
  DevList = mvsdk.CameraEnumerateDevice()
  nDev = len(DevList)
  if nDev < 1:
    print("No camera was found!")
    return

  for i, DevInfo in enumerate(DevList):
    print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))

  cams = []
  cam = Camera(DevList[0])
  if cam.open():
    cams.append(cam)

  cams1 = []
  cam1 = Camera(DevList[1])
  if cam1.open():
    cams1.append(cam)



  tiempo_anterior=time.time()
        

  while (cv2.waitKey(1) & 0xFF) != ord('q'):
  
    h = cv2.getTrackbarPos('DER AMPL','ALARMA')
    s = cv2.getTrackbarPos('DER REDU','ALARMA')
    v = cv2.getTrackbarPos('IZQ REDU','ALARMA')
    hh = cv2.getTrackbarPos('IZQ AMPL','ALARMA')


######################################################  Lado Derecho
    frame = cam.grab()
    frame = cv2.resize(frame, (640,480), interpolation = cv2.INTER_LINEAR)
    #cv2.imshow("{} Press q to end".format(cam.DevInfo.GetFriendlyName()), frame)
    cv2.imwrite('captura.jpg', frame)

    cap= cv2.VideoCapture('captura.jpg')
    aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_100)
    ret, foto = cap.read()
    #cv2.imshow("Video1", foto)

    parameters = aruco.DetectorParameters_create()
    corners, ids , rejectedImgPoints = cv2.aruco.detectMarkers(foto, aruco_dict, parameters=parameters)
    corners_int = np.int0(corners)
    foto = aruco.drawDetectedMarkers(foto, corners)

    # Evita que mi programa pare por que no ve el perimetro del aruco
    if (ids == None).any():
      continue

   

  ##############################################

    mostrar,distancia_ld = TratamientoImagen (foto,corners_int,0,0,100,179,100,255,4.8,599,228,28,138,h,s)
    

#####################################################   Lado Izquierdo
    frame1 = cam1.grab()
    frame1 = cv2.resize(frame1, (640,480), interpolation = cv2.INTER_LINEAR)
    #cv2.imshow("{} Press q to end".format(cam.DevInfo.GetFriendlyName()), frame)
    cv2.imwrite('captura1.jpg', frame1)

    cap1= cv2.VideoCapture('captura1.jpg')
    aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_100)
    ret1, foto1 = cap1.read()
    #cv2.imshow("Video1", foto1)

    parameters1 = aruco.DetectorParameters_create()
    #corners1, ids1 , rejectedImgPoints = cv2.aruco.detectMarkers(foto1, aruco_dict, parameters=parameters1, cameraMatrix=matrix_LI , distCoeff=dist_LI)
    corners1, ids1 , rejectedImgPoints = cv2.aruco.detectMarkers(foto1, aruco_dict, parameters=parameters1)
    corners_int1 = np.int0(corners1)
    foto1 = aruco.drawDetectedMarkers(foto1, corners1)

    # Evita que mi programa pare por que no ve el perimetro del aruco
    if (ids1 == None).any():
      continue
         

  ##############################################
    mostrar1,distancia_li  = TratamientoImagen (foto1,corners_int1,0,0,100,179,100,255,4.86,41,184,32,65,v,hh)
    #cv2.imshow('concat_h1',mostrar1)

#######################

    ancho_bruto=4401-((distancia_li*10)+(distancia_ld*10))
    #print(ancho_bruto)
    #time.sleep(0.4)

#/////////////////////////////////////////////////////////////////////////////////////Arreglo para guardar seg a seg

    izq3 = round(distancia_li,2)
    der3 = round(distancia_ld,2)
    anch_bru = round(ancho_bruto,2)

    tiempo_actual=time.time()
    if tiempo_actual-tiempo_anterior>=1:
            almacenamiento(izq3,der3,anch_bru)
            tiempo_anterior=tiempo_actual
              



#/////////////////////////////////////////////////////////////////////////////////////



#######################
  

    concat_f = cv2.hconcat([mostrar1, mostrar])

                
    
    
    #cv2.putText(concat_f, "{:.2f} cm".format(ancho_bruto), (x2+w2+distancia_pixeles//2, y2-30), 2, 0.8, (0,0,255), 1, cv2.LINE_AA)
    cv2.putText(concat_f, "{:.2f} mm".format(ancho_bruto), (400,440),1,5.5, 
            (0,255,0),2)
    cv2.putText(concat_f, "{:.2f} mm".format(distancia_li*10), (190,50),1,3.7, 
            (0,255,0),2)
    cv2.putText(concat_f, "{:.2f} mm".format(distancia_ld*10), (850,50),1,3.7, 
            (0,255,0),2)

    cv2.putText(concat_f, 'ANCHO BRUTO', (560,370),1,1.5,
              (0,245,0),2)
    cv2.putText(concat_f, 'Lado Izquierdo', (50,80),1,1.5,
              (0,255,0),2)
    cv2.putText(concat_f, 'Lado Derecho', (1050,80),1,1.5,
              (0,255,0),2)

    cv2.putText(concat_f, 'PROYECTO CENTRADO DE HOJA EN CORTE', (940,470),1,1,
              (0,255,0),2)

    #cv2.imshow('concat_h1',concat_f)
    cv2.imshow('ALARMA', concat_f )
 


    


def main():
  try:
    
    main_loop()
    
    
  finally:
    cv2.destroyAllWindows()

main()



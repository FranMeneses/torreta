from __future__ import print_function
from imutils.video import VideoStream
import argparse
import imutils
import time
import cv2
import os
import RPi.GPIO as GPIO

#define los puertos GPIOs para los servos
panServo = 27
tiltServo = 17
triggerServo = 22

#funcion que posiciona los servos
def positionServo (servo, angle):
    os.system("python angleServoCtrl.py " + str(servo) + " " + str(angle))
    print("[INFO] Positioning servo at GPIO {0} to {1} degrees\n".format(servo, angle))
    

#posiciona los servos para centrar la imagen
def mapServoPosition (x, y):
    global panAngle
    global tiltAngle
    global trigAngle
    if (x < 220):
        panAngle += 5
        if panAngle > 140:
            panAngle = 140
        positionServo (panServo, panAngle)
 
    if (x > 280):
        panAngle -= 5
        if panAngle < 40:
            panAngle = 40
        positionServo (panServo, panAngle)

    if (y < 160):
        tiltAngle += 5
        if tiltAngle > 100:
            tiltAngle = 100
        positionServo (tiltServo, tiltAngle)
 
    if (y > 210):
        tiltAngle -= 5
        if tiltAngle < 80:
            tiltAngle = 80
        positionServo (tiltServo, tiltAngle)

	#si el servo esta centrado se acciona el servo gatillo
    if (x >= 220 and x <= 280):
        if (y>=160 and y<=210):
            trigAngle = 80
            positionServo (triggerServo, trigAngle)
            trigAngle = 170
            positionServo (triggerServo, trigAngle)

#inicializa el video stream y espera a que la camara caliente
print("[INFO] esperando que la camara caliente...")
vs = VideoStream(0).start()
time.sleep(2.0)

#define los valores minimos y maximos del objeto para ser trackeados en HSV
colorLower = (24, 100, 100)
colorUpper = (44, 255, 255)

#Inicializa los angulos de los servos
global panAngle
panAngle = 90
global tiltAngle
tiltAngle = 90
global trigAngle
trigAngle = 175

#posiciona Pan/Tilt/Trigger servos en su posicion inicial
positionServo (panServo, panAngle)
positionServo (tiltServo, tiltAngle)
positionServo (triggerServo, trigAngle)

#loop sobre los frames del video stream
while True:
	#toma el siguiente frame del video stream, invierte el angulo en 180 y convierte el color a HSV
	frame = vs.read()
	frame = imutils.resize(frame, width=500)
	frame = imutils.rotate(frame, angle=180)
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	#construye una mascara para el color del objeto
	mask = cv2.inRange(hsv, colorLower, colorUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	#encuentra los contornos de la mascara e inicializa el centro del objeto
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if imutils.convenience.is_cv4() else cnts[1]
	center = None

	if len(cnts) > 0:
		#encuentra el contorno mas largo en la mascara y luego lo encapsula en el circulo mas chico posible
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

		if radius > 10:
			#dibuja el circulo en el frame
			cv2.circle(frame, (int(x), int(y)), int(radius),
				(0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
			
			#posiciona el servo al centro del circulo
			mapServoPosition(int(x), int(y))

	cv2.imshow("Frame", frame)
	
	#espera para salir
	key = cv2.waitKey(1) & 0xFF
	if key == 27:
            break

print("\n [INFO] Saliendo del Programa \n")
positionServo (panServo, 90)
positionServo (tiltServo, 150)
positionServo (triggerServo, 175)
GPIO.cleanup()
cv2.destroyAllWindows()
vs.stop()
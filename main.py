import cv2
import mediapipe as mp
import numpy as np

# Load images for each gesture 
img_point = cv2.imread("Smart.png")         
img_thumb = cv2.imread("Smirks.jpg")          
img_mouth = cv2.imread("Surprised.png")      
img_finger_mouth = cv2.imread("Confused.png")   
img_default = np.zeros((480, 640, 3), np.uint8)

# Setup MediaPipe
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_mesh
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
face_mesh = mp_face.FaceMesh(min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_result = hands.process(rgb)
    face_result = face_mesh.process(rgb)

    gesture_detected = "none"
    selected_img = img_default.copy()

    # HAND DETECTION
    if hand_result.multi_hand_landmarks and hand_result.multi_handedness:
        for hand_landmarks, handedness in zip(hand_result.multi_hand_landmarks, hand_result.multi_handedness):
            lm = hand_landmarks.landmark
            hand_label = handedness.classification[0].label  

            wrist = lm[0]
            thumb_tip = lm[4]
            thumb_ip = lm[3]
            thumb_mcp = lm[2]
            index_tip = lm[8]
            index_mcp = lm[5]

            # Thumb extension + folded fingers check
            thumb_extended = abs(thumb_tip.x - thumb_mcp.x) > 0.05
            fingers_folded = (
                lm[8].y > lm[6].y and  # index folded
                lm[12].y > lm[10].y and
                lm[16].y > lm[14].y and
                lm[20].y > lm[18].y
            )

            # GESTURE LOGIC
            # Pointed Up
            if (lm[8].y < lm[6].y and lm[12].y > lm[10].y and
                lm[16].y > lm[14].y and lm[20].y > lm[18].y):
                gesture_detected = "smart"
                selected_img = img_point

            # Left hand thumb pointing left
            elif hand_label == "Left" and thumb_tip.x < wrist.x and thumb_extended and fingers_folded:
                gesture_detected = "LOL"
                selected_img = img_thumb

            # Finger in mouth detection
            if face_result.multi_face_landmarks:
                for face_landmarks in face_result.multi_face_landmarks:
                    mouth_upper = face_landmarks.landmark[13]
                    mouth_lower = face_landmarks.landmark[14]
                    mx = int(((mouth_upper.x + mouth_lower.x) / 2) * w)
                    my = int(((mouth_upper.y + mouth_lower.y) / 2) * h)
                    ix, iy = int(index_tip.x * w), int(index_tip.y * h)

                    if abs(ix - mx) < 30 and abs(iy - my) < 30:
                        gesture_detected = "confused"
                        selected_img = img_finger_mouth

    # FACE DETECTION
    if face_result.multi_face_landmarks:
        for face_landmarks in face_result.multi_face_landmarks:
            upper_lip = face_landmarks.landmark[13]
            lower_lip = face_landmarks.landmark[14]

            # Open mouth detection
            distance = abs(lower_lip.y - upper_lip.y)
            if distance > 0.01:
                gesture_detected = "surprised"
                selected_img = img_mouth


    # DISPLAY
    selected_img = cv2.resize(selected_img, (w, h))
    combined = np.hstack((frame, selected_img))
    cv2.putText(combined, f"Gesture: {gesture_detected}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)

    cv2.imshow("Gesture & Expression Recognition", combined)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

import cv2
import mediapipe as mp

# --------------------------------------------------
# MediaPipe setup
# --------------------------------------------------

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="models/pose_landmarker_full.task"
    ),
    running_mode=RunningMode.VIDEO
)

# --------------------------------------------------
# Pose landmark connections
# --------------------------------------------------

connections = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),

    (9, 10),

    (11, 12),

    (11, 13), (13, 15),
    (15, 17), (15, 19), (15, 21),

    (12, 14), (14, 16),
    (16, 18), (16, 20), (16, 22),

    (11, 23),
    (12, 24),

    (23, 24),

    (23, 25), (25, 27),
    (27, 29), (27, 31),

    (24, 26), (26, 28),
    (28, 30), (28, 32)
]

# --------------------------------------------------
# Open camera
# --------------------------------------------------

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open camera.")
    exit()

print("Camera started.")
print("Press Q to quit.")

# --------------------------------------------------
# Start Pose Landmarker
# --------------------------------------------------

with PoseLandmarker.create_from_options(options) as landmarker:

    frame_number = 0

    while True:

        success, frame = camera.read()

        if not success:
            print("ERROR: Could not read camera frame.")
            break

        # Flip image horizontally
        frame = cv2.flip(frame, 1)

        # Convert BGR → RGB
        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # Create MediaPipe image
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        # Timestamp
        timestamp_ms = frame_number * 33
        frame_number += 1

        # Detect pose
        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        # --------------------------------------------------
        # Draw landmarks
        # --------------------------------------------------

        if result.pose_landmarks:

            landmarks = result.pose_landmarks[0]

            # Draw points
            for landmark in landmarks:

                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])

                cv2.circle(
                    frame,
                    (x, y),
                    4,
                    (0, 255, 0),
                    -1
                )

            # Draw connections
            for start, end in connections:

                x1 = int(
                    landmarks[start].x *
                    frame.shape[1]
                )

                y1 = int(
                    landmarks[start].y *
                    frame.shape[0]
                )

                x2 = int(
                    landmarks[end].x *
                    frame.shape[1]
                )

                y2 = int(
                    landmarks[end].y *
                    frame.shape[0]
                )

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 255, 255),
                    2
                )

            cv2.putText(
                frame,
                "POSE DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "NO POSE DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        # Display
        cv2.imshow(
            "AI Study Bot - Pose Detection",
            frame
        )

        # Q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

camera.release()
cv2.destroyAllWindows()

print("Program stopped.")
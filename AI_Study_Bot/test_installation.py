import cv2
import mediapipe as mp
import math
import time


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/pose_landmarker_full.task"

CAMERA_ID = 0

# ------------------------------------------------------------
# Calibration angle
# ------------------------------------------------------------

# When you press P while intentionally bending forward,
# the system treats that posture as this angle.
#
# Example:
# Upright = 0 degrees
# Poor posture reference = 20 degrees
#
CALIBRATION_POOR_ANGLE = 20.0


# ------------------------------------------------------------
# Warning settings
# ------------------------------------------------------------

# Poor posture must remain detected for this duration
# before a warning is shown.
POOR_POSTURE_TIME = 3.0


# ------------------------------------------------------------
# Smoothing
# ------------------------------------------------------------

SMOOTHING_FRAMES = 10


# ------------------------------------------------------------
# Posture thresholds
# ------------------------------------------------------------

# Percentage of the calibrated poor-posture zoom level
# at which we enter the POOR state.
#
# Example:
# Poor calibration zoom = 1.15
# 80% of the change = 1.12 approximately
#
POOR_THRESHOLD_PERCENT = 0.80


# Percentage of the poor-posture change at which we
# return to GOOD.
GOOD_THRESHOLD_PERCENT = 0.55


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

BaseOptions = mp.tasks.BaseOptions

PoseLandmarker = mp.tasks.vision.PoseLandmarker

PoseLandmarkerOptions = (
    mp.tasks.vision.PoseLandmarkerOptions
)

RunningMode = mp.tasks.vision.RunningMode


options = PoseLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=RunningMode.VIDEO
)


# ============================================================
# POSE CONNECTIONS
# ============================================================

connections = [

    # Face
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 7),

    (0, 4),
    (4, 5),
    (5, 6),
    (6, 8),

    # Mouth
    (9, 10),

    # Shoulders
    (11, 12),

    # Left arm
    (11, 13),
    (13, 15),
    (15, 17),
    (15, 19),
    (15, 21),

    # Right arm
    (12, 14),
    (14, 16),
    (16, 18),
    (16, 20),
    (16, 22),

    # Torso - only visible part
    (11, 23),
    (12, 24),
    (23, 24)
]


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(CAMERA_ID)

if not camera.isOpened():

    print("ERROR: Could not open camera.")
    print("Try changing CAMERA_ID from 0 to 1.")

    exit()


print()
print("==============================================")
print("       AI STUDY BOT - POSTURE AI")
print("==============================================")
print()
print("CONTROLS")
print("----------------------------------------------")
print("C = Calibrate upright posture")
print("P = Calibrate poor posture reference")
print("R = Reset calibration")
print("Q = Quit")
print("----------------------------------------------")
print()


# ============================================================
# VARIABLES
# ============================================================

frame_number = 0


# ------------------------------------------------------------
# Baseline measurements
# ------------------------------------------------------------

baseline_shoulder_width = None

baseline_face_width = None

baseline_scale = None


# ------------------------------------------------------------
# Poor posture reference
# ------------------------------------------------------------

poor_reference_scale = None

poor_reference_zoom_change = None


# ------------------------------------------------------------
# Current measurements
# ------------------------------------------------------------

current_scale = None

current_zoom_ratio = None

current_zoom_change = None

estimated_angle = 0.0


# ------------------------------------------------------------
# Posture state
# ------------------------------------------------------------

posture = "NOT CALIBRATED"

poor_posture_start = None

warning = False


# ------------------------------------------------------------
# Smoothing history
# ------------------------------------------------------------

scale_history = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def average(values):

    if len(values) == 0:

        return 0.0

    return sum(values) / len(values)


def smooth_value(history, value):

    history.append(value)

    if len(history) > SMOOTHING_FRAMES:

        history.pop(0)

    return average(history)


def distance(x1, y1, x2, y2):

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


# ============================================================
# START MEDIAPIPE
# ============================================================

with PoseLandmarker.create_from_options(options) as landmarker:

    while True:

        # ====================================================
        # READ CAMERA FRAME
        # ====================================================

        success, frame = camera.read()

        if not success:

            print("ERROR: Could not read camera frame.")

            break


        # ====================================================
        # MIRROR CAMERA
        # ====================================================

        frame = cv2.flip(frame, 1)


        frame_height, frame_width = frame.shape[:2]


        # ====================================================
        # BGR → RGB
        # ====================================================

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        # ====================================================
        # CREATE MEDIAPIPE IMAGE
        # ====================================================

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )


        # ====================================================
        # TIMESTAMP
        # ====================================================

        timestamp_ms = frame_number * 33

        frame_number += 1


        # ====================================================
        # POSE DETECTION
        # ====================================================

        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )


        # ====================================================
        # PERSON DETECTED
        # ====================================================

        if result.pose_landmarks:

            landmarks = result.pose_landmarks[0]


            # ------------------------------------------------
            # IMPORTANT LANDMARKS
            # ------------------------------------------------

            nose = landmarks[0]

            left_ear = landmarks[7]

            right_ear = landmarks[8]

            left_shoulder = landmarks[11]

            right_shoulder = landmarks[12]


            # ------------------------------------------------
            # CHECK VISIBILITY
            # ------------------------------------------------

            required_landmarks = [

                nose,
                left_ear,
                right_ear,
                left_shoulder,
                right_shoulder
            ]


            visible = all(
                landmark.visibility > 0.5
                for landmark in required_landmarks
            )


            if visible:

                # =================================================
                # FACE WIDTH
                # =================================================

                face_width = distance(

                    left_ear.x,
                    left_ear.y,

                    right_ear.x,
                    right_ear.y
                )


                # =================================================
                # SHOULDER WIDTH
                # =================================================

                shoulder_width = distance(

                    left_shoulder.x,
                    left_shoulder.y,

                    right_shoulder.x,
                    right_shoulder.y
                )


                # =================================================
                # VALID MEASUREMENTS
                # =================================================

                if (
                    face_width > 0.001
                    and
                    shoulder_width > 0.001
                ):

                    # =================================================
                    # COMBINED SCALE
                    # =================================================
                    #
                    # We use both face width and shoulder width.
                    #
                    # This makes the measurement more stable.
                    #
                    # Face contributes 40%
                    # Shoulders contribute 60%
                    #

                    if baseline_face_width is not None:

                        face_scale = (
                            face_width /
                            baseline_face_width
                        )

                    else:

                        face_scale = 1.0


                    if baseline_shoulder_width is not None:

                        shoulder_scale = (
                            shoulder_width /
                            baseline_shoulder_width
                        )

                    else:

                        shoulder_scale = 1.0


                    # ------------------------------------------------
                    # Current combined scale
                    # ------------------------------------------------

                    if (
                        baseline_face_width is not None
                        and
                        baseline_shoulder_width is not None
                    ):

                        current_scale = (

                            0.40 *
                            face_scale

                            +

                            0.60 *
                            shoulder_scale
                        )


                        # ------------------------------------------------
                        # Smooth scale
                        # ------------------------------------------------

                        current_scale = smooth_value(
                            scale_history,
                            current_scale
                        )


                        current_zoom_ratio = (
                            current_scale
                        )


                        # =================================================
                        # ZOOM CHANGE
                        # =================================================

                        current_zoom_change = (
                            current_zoom_ratio - 1.0
                        )


                        # =================================================
                        # ESTIMATED ANGLE
                        # =================================================

                        if (
                            poor_reference_zoom_change
                            is not None
                            and
                            poor_reference_zoom_change > 0.001
                        ):

                            # --------------------------------------------
                            # How much of the calibrated poor-posture
                            # zoom change has occurred?
                            # --------------------------------------------

                            progress = (
                                current_zoom_change /
                                poor_reference_zoom_change
                            )


                            # Limit to 0–1.5
                            progress = max(
                                0.0,
                                min(
                                    progress,
                                    1.5
                                )
                            )


                            # --------------------------------------------
                            # Convert to estimated angle
                            # --------------------------------------------

                            estimated_angle = (

                                progress *
                                CALIBRATION_POOR_ANGLE
                            )


                        else:

                            estimated_angle = 0.0


                        # =================================================
                        # POSTURE CLASSIFICATION
                        # =================================================

                        if poor_reference_zoom_change is not None:

                            # ------------------------------------------------
                            # Current progress toward poor reference
                            # ------------------------------------------------

                            progress = (

                                current_zoom_change /
                                poor_reference_zoom_change
                            )


                            # ------------------------------------------------
                            # Enter POOR
                            # ------------------------------------------------

                            if posture == "GOOD":

                                if (
                                    progress >=
                                    POOR_THRESHOLD_PERCENT
                                ):

                                    posture = "POOR"

                                    poor_posture_start = (
                                        time.time()
                                    )


                            # ------------------------------------------------
                            # Return GOOD
                            # ------------------------------------------------

                            elif posture == "POOR":

                                if (
                                    progress <
                                    GOOD_THRESHOLD_PERCENT
                                ):

                                    posture = "GOOD"

                                    poor_posture_start = None

                                    warning = False


                            # ------------------------------------------------
                            # POOR POSTURE TIMER
                            # ------------------------------------------------

                            if posture == "POOR":

                                if (
                                    poor_posture_start
                                    is None
                                ):

                                    poor_posture_start = (
                                        time.time()
                                    )


                                poor_duration = (
                                    time.time()
                                    -
                                    poor_posture_start
                                )


                                if (
                                    poor_duration
                                    >=
                                    POOR_POSTURE_TIME
                                ):

                                    warning = True

                                else:

                                    warning = False


                            else:

                                poor_duration = 0.0

                                warning = False


                    # =================================================
                    # DRAW LANDMARKS
                    # =================================================

                    for landmark in landmarks:

                        x = int(
                            landmark.x *
                            frame_width
                        )

                        y = int(
                            landmark.y *
                            frame_height
                        )


                        cv2.circle(
                            frame,
                            (x, y),
                            4,
                            (0, 255, 0),
                            -1
                        )


                    # =================================================
                    # DRAW CONNECTIONS
                    # =================================================

                    for start, end in connections:

                        x1 = int(
                            landmarks[start].x *
                            frame_width
                        )

                        y1 = int(
                            landmarks[start].y *
                            frame_height
                        )

                        x2 = int(
                            landmarks[end].x *
                            frame_width
                        )

                        y2 = int(
                            landmarks[end].y *
                            frame_height
                        )


                        cv2.line(
                            frame,
                            (x1, y1),
                            (x2, y2),
                            (255, 255, 255),
                            2
                        )


                    # =================================================
                    # DISPLAY PERSON STATUS
                    # =================================================

                    cv2.putText(
                        frame,
                        "PERSON DETECTED",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.75,
                        (0, 255, 0),
                        2
                    )


                    # =================================================
                    # DISPLAY ZOOM RATIO
                    # =================================================

                    if current_zoom_ratio is not None:

                        cv2.putText(
                            frame,
                            f"Zoom Ratio: "
                            f"{current_zoom_ratio:.3f}",
                            (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (255, 255, 255),
                            2
                        )


                    # =================================================
                    # DISPLAY ZOOM CHANGE
                    # =================================================

                    if current_zoom_change is not None:

                        zoom_percent = (
                            current_zoom_change *
                            100
                        )


                        cv2.putText(
                            frame,
                            f"Zoom Change: "
                            f"{zoom_percent:+.1f}%",
                            (20, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (255, 255, 255),
                            2
                        )


                    # =================================================
                    # DISPLAY ESTIMATED ANGLE
                    # =================================================

                    cv2.putText(
                        frame,
                        f"Estimated Lean: "
                        f"{estimated_angle:.1f} deg",
                        (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2
                    )


                    # =================================================
                    # DISPLAY POSTURE
                    # =================================================

                    if posture == "GOOD":

                        posture_color = (
                            0,
                            255,
                            0
                        )

                    elif posture == "POOR":

                        posture_color = (
                            0,
                            0,
                            255
                        )

                    else:

                        posture_color = (
                            0,
                            165,
                            255
                        )


                    cv2.putText(
                        frame,
                        f"Posture: {posture}",
                        (20, 165),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.85,
                        posture_color,
                        2
                    )


                    # =================================================
                    # POOR POSTURE TIMER
                    # =================================================

                    if posture == "POOR":

                        cv2.putText(
                            frame,
                            f"Poor posture: "
                            f"{poor_duration:.1f} sec",
                            (20, 200),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 165, 255),
                            2
                        )


                    # =================================================
                    # WARNING
                    # =================================================

                    if warning:

                        cv2.putText(
                            frame,
                            "PLEASE SIT UPRIGHT!",
                            (20, 240),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (0, 0, 255),
                            3
                        )


                    # =================================================
                    # CALIBRATION STATUS
                    # =================================================

                    if baseline_scale is None:

                        cv2.putText(
                            frame,
                            "Press C - Calibrate UPRIGHT",
                            (20, 280),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 165, 255),
                            2
                        )

                    elif poor_reference_scale is None:

                        cv2.putText(
                            frame,
                            "Press P - Calibrate POOR POSTURE",
                            (20, 280),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 165, 255),
                            2
                        )

                    else:

                        cv2.putText(
                            frame,
                            "Calibration: READY",
                            (20, 280),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 255, 0),
                            2
                        )


                # =================================================
                # LANDMARKS UNCLEAR
                # =================================================

                else:

                    posture = "LANDMARKS UNCLEAR"

                    poor_posture_start = None

                    warning = False


                    cv2.putText(
                        frame,
                        "MOVE INTO CAMERA VIEW",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2
                    )


        # ====================================================
        # NO PERSON DETECTED
        # ====================================================

        else:

            posture = "NO PERSON"

            poor_posture_start = None

            warning = False


            cv2.putText(
                frame,
                "NO PERSON DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.imshow(
            "AI Study Bot - Calibrated Front Posture",
            frame
        )


        # ====================================================
        # KEYBOARD INPUT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        # ====================================================
        # C = UPRIGHT CALIBRATION
        # ====================================================

        if key == ord("c"):

            if result.pose_landmarks:

                landmarks = result.pose_landmarks[0]


                left_ear = landmarks[7]

                right_ear = landmarks[8]

                left_shoulder = landmarks[11]

                right_shoulder = landmarks[12]


                # ------------------------------------------------
                # Measure face width
                # ------------------------------------------------

                face_width = distance(

                    left_ear.x,
                    left_ear.y,

                    right_ear.x,
                    right_ear.y
                )


                # ------------------------------------------------
                # Measure shoulder width
                # ------------------------------------------------

                shoulder_width = distance(

                    left_shoulder.x,
                    left_shoulder.y,

                    right_shoulder.x,
                    right_shoulder.y
                )


                if (
                    face_width > 0.001
                    and
                    shoulder_width > 0.001
                ):

                    baseline_face_width = (
                        face_width
                    )

                    baseline_shoulder_width = (
                        shoulder_width
                    )


                    baseline_scale = 1.0


                    # Reset smoothing
                    scale_history.clear()


                    # Reset posture
                    posture = "GOOD"

                    poor_posture_start = None

                    warning = False


                    print()
                    print(
                        "================================"
                    )
                    print(
                        "UPRIGHT CALIBRATION COMPLETE"
                    )
                    print(
                        "================================"
                    )

                    print(
                        f"Baseline face width: "
                        f"{baseline_face_width:.4f}"
                    )

                    print(
                        f"Baseline shoulder width: "
                        f"{baseline_shoulder_width:.4f}"
                    )

                    print()
                    print(
                        "Now sit in your intentionally"
                    )

                    print(
                        "POOR POSTURE and press P."
                    )

                    print()


        # ====================================================
        # P = POOR POSTURE CALIBRATION
        # ====================================================

        if key == ord("p"):

            if (
                baseline_face_width is not None
                and
                baseline_shoulder_width is not None
                and
                result.pose_landmarks
            ):

                landmarks = result.pose_landmarks[0]


                left_ear = landmarks[7]

                right_ear = landmarks[8]

                left_shoulder = landmarks[11]

                right_shoulder = landmarks[12]


                # ------------------------------------------------
                # Current face width
                # ------------------------------------------------

                face_width = distance(

                    left_ear.x,
                    left_ear.y,

                    right_ear.x,
                    right_ear.y
                )


                # ------------------------------------------------
                # Current shoulder width
                # ------------------------------------------------

                shoulder_width = distance(

                    left_shoulder.x,
                    left_shoulder.y,

                    right_shoulder.x,
                    right_shoulder.y
                )


                if (
                    face_width > 0.001
                    and
                    shoulder_width > 0.001
                ):

                    # ------------------------------------------------
                    # Calculate scale relative to upright
                    # ------------------------------------------------

                    face_scale = (
                        face_width /
                        baseline_face_width
                    )


                    shoulder_scale = (
                        shoulder_width /
                        baseline_shoulder_width
                    )


                    poor_reference_scale = (

                        0.40 *
                        face_scale

                        +

                        0.60 *
                        shoulder_scale
                    )


                    poor_reference_zoom_change = (

                        poor_reference_scale -
                        1.0
                    )


                    # ------------------------------------------------
                    # Validate calibration
                    # ------------------------------------------------

                    if (
                        poor_reference_zoom_change
                        <= 0.01
                    ):

                        print()
                        print(
                            "WARNING:"
                        )

                        print(
                            "Poor posture reference"
                        )

                        print(
                            "did not show enough zoom change."
                        )

                        print(
                            "Lean forward more and"
                        )

                        print(
                            "press P again."
                        )

                        print()

                        poor_reference_scale = None

                        poor_reference_zoom_change = None

                    else:

                        posture = "GOOD"

                        poor_posture_start = None

                        warning = False


                        print()
                        print(
                            "================================"
                        )

                        print(
                            "POOR POSTURE CALIBRATION COMPLETE"
                        )

                        print(
                            "================================"
                        )

                        print(
                            f"Poor reference scale: "
                            f"{poor_reference_scale:.3f}"
                        )

                        print(
                            f"Poor reference zoom: "
                            f"{poor_reference_zoom_change * 100:.1f}%"
                        )

                        print(
                            f"Calibration angle: "
                            f"{CALIBRATION_POOR_ANGLE:.1f} deg"
                        )

                        print()

                        print(
                            "POSTURE AI READY"
                        )

                        print()


        # ====================================================
        # R = RESET
        # ====================================================

        if key == ord("r"):

            baseline_face_width = None

            baseline_shoulder_width = None

            baseline_scale = None

            poor_reference_scale = None

            poor_reference_zoom_change = None

            current_scale = None

            current_zoom_ratio = None

            current_zoom_change = None

            estimated_angle = 0.0

            posture = "NOT CALIBRATED"

            poor_posture_start = None

            warning = False

            scale_history.clear()


            print()
            print(
                "Calibration reset."
            )

            print(
                "Press C to calibrate upright posture."
            )

            print()


        # ====================================================
        # Q = QUIT
        # ====================================================

        if key == ord("q"):

            break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()


print()
print("==============================================")
print("Posture detection stopped.")
print("==============================================")
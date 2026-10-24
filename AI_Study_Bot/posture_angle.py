import cv2
import mediapipe as mp
import math
import time
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urlencode


# ============================================================
# ESP32 WIRELESS CONFIGURATION
# ============================================================

# IMPORTANT:
# Replace this with the IP shown by the ESP32 Serial Monitor.
#


ESP32_IP = "10.74.166.123"

ESP32_UPDATE_INTERVAL = 0.10

ESP32_TIMEOUT = 0.8

last_esp32_update = 0.0

esp32_connection_status = "NOT CONNECTED"

last_sent_state = None
last_sent_remaining = None


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/pose_landmarker_full.task"

CAMERA_ID = 0


# ============================================================
# POSTURE CALIBRATION
# ============================================================

CALIBRATION_POOR_ANGLE = 20.0


# ============================================================
# BUFFER / WARNING
# ============================================================

POOR_POSTURE_TIME = 3.0


# ============================================================
# POSTURE STATE THRESHOLDS
# ============================================================

POOR_THRESHOLD_PERCENT = 0.80

GOOD_THRESHOLD_PERCENT = 0.55


# ============================================================
# SMOOTHING
# ============================================================

SMOOTHING_FRAMES = 10


# ============================================================
# DISPLAY
# ============================================================

WINDOW_NAME = "AI Study Bot - Posture Detection"


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
# POSE LANDMARK CONNECTIONS
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

    # Visible torso
    (11, 23),
    (12, 24),
    (23, 24)
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def distance(x1, y1, x2, y2):

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


def average(values):

    if not values:
        return 0.0

    return sum(values) / len(values)


def smooth_value(history, value):

    history.append(value)

    if len(history) > SMOOTHING_FRAMES:
        history.pop(0)

    return average(history)


def format_time(timestamp):

    if timestamp is None:
        return "--:--:--"

    return datetime.fromtimestamp(
        timestamp
    ).strftime("%H:%M:%S")


def format_duration(seconds):

    if seconds is None:
        return "00:00:00"

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (seconds % 3600) // 60

    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================
# ESP32 URL
# ============================================================

def esp32_url(path, params=None):

    if params:
        return (
            f"http://{ESP32_IP}{path}?"
            f"{urlencode(params)}"
        )

    return f"http://{ESP32_IP}{path}"


# ============================================================
# ESP32 HTTP REQUEST
# ============================================================

def esp32_request(path, params=None):

    global esp32_connection_status

    if (
        not ESP32_IP
        or ESP32_IP == "YOUR_ESP32_IP"
    ):
        esp32_connection_status = "NO IP"

        return False


    try:

        url = esp32_url(
            path,
            params
        )


        request = urllib.request.Request(
            url,
            method="GET"
        )


        with urllib.request.urlopen(
            request,
            timeout=ESP32_TIMEOUT
        ) as response:

            response.read()


        esp32_connection_status = "CONNECTED"

        return True


    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError
    ):

        esp32_connection_status = "DISCONNECTED"

        return False


# ============================================================
# ESP32 PING TEST
# ============================================================

def test_esp32_connection():

    print()
    print("====================================================")
    print("Testing ESP32 wireless connection...")
    print("====================================================")


    success = esp32_request(
        "/ping"
    )


    if success:

        print(
            "ESP32 CONNECTION: CONNECTED"
        )

        print(
            f"ESP32 IP: {ESP32_IP}"
        )

    else:

        print(
            "ESP32 CONNECTION: FAILED"
        )

        print(
            f"ESP32 IP: {ESP32_IP}"
        )

        print(
            "Check that laptop and ESP32 are on the same Wi-Fi."
        )


    print("====================================================")
    print()


# ============================================================
# SEND POSTURE TO ESP32
# ============================================================

def send_posture_to_esp32(
    posture_state,
    remaining=0.0,
    force=False
):

    global last_esp32_update
    global last_sent_state
    global last_sent_remaining


    now = time.time()


    # --------------------------------------------------------
    # Prevent excessive requests
    # --------------------------------------------------------

    if (
        not force
        and now - last_esp32_update
        < ESP32_UPDATE_INTERVAL
    ):
        return


    # --------------------------------------------------------
    # Don't repeatedly send identical GOOD/BAD states
    # --------------------------------------------------------
    #
    # BUFFER is different because remaining time changes.

    if posture_state != "BUFFER":

        if (
            not force
            and posture_state == last_sent_state
        ):

            return


    else:

        if (
            not force
            and last_sent_state == "BUFFER"
            and last_sent_remaining is not None
            and abs(
                remaining -
                last_sent_remaining
            ) < 0.05
        ):

            return


    remaining = max(
        0.0,
        float(remaining)
    )


    success = esp32_request(
        "/state",
        {
            "status": posture_state,
            "remaining": f"{remaining:.2f}"
        }
    )


    last_esp32_update = now


    if success:

        last_sent_state = posture_state

        last_sent_remaining = remaining


        if posture_state == "BUFFER":

            print(
                f"ESP32 -> BUFFER | "
                f"{remaining:.1f}s"
            )

        else:

            print(
                f"ESP32 -> {posture_state}"
            )


# ============================================================
# SEND SESSION SUMMARY TO ESP32
# ============================================================

def send_session_summary_to_esp32():

    if session_start_time is None:
        return


    start_text = format_time(
        session_start_time
    )


    end_text = format_time(
        session_end_time
    )


    if (
        session_end_time is not None
    ):

        duration_seconds = (
            session_end_time -
            session_start_time
        )

    else:

        duration_seconds = 0


    duration_text = format_duration(
        duration_seconds
    )


    print()
    print(
        "Sending session summary to ESP32..."
    )


    success = esp32_request(
        "/session_end",
        {
            "badEvents":
                str(bad_posture_events),

            "alerts":
                str(confirmed_bad_alerts),

            "start":
                start_text,

            "end":
                end_text,

            "duration":
                duration_text
        }
    )


    if success:

        print(
            "Session summary sent to ESP32."
        )

    else:

        print(
            "WARNING: Could not send session summary to ESP32."
        )


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(
    CAMERA_ID
)


if not camera.isOpened():

    print()
    print(
        "ERROR: Could not open camera."
    )

    print(
        "Try changing CAMERA_ID from 0 to 1."
    )

    print()

    exit()


# ============================================================
# START MESSAGE
# ============================================================

print()
print(
    "===================================================="
)
print(
    "             AI STUDY BOT"
)
print(
    "          POSTURE DETECTION SYSTEM"
)
print(
    "===================================================="
)
print()

print(
    "ESP32 WIRELESS"
)

print(
    "----------------------------------------------------"
)

print(
    f"ESP32 IP: {ESP32_IP}"
)

print(
    f"Update interval: {ESP32_UPDATE_INTERVAL}s"
)

print()

print(
    "CONTROLS"
)

print(
    "----------------------------------------------------"
)

print(
    "C = Calibrate UPRIGHT posture"
)

print(
    "P = Calibrate POOR posture + START session"
)

print(
    "R = Reset calibration"
)

print(
    "Q = End session and display statistics"
)

print(
    "----------------------------------------------------"
)

print()

print(
    "IMPORTANT:"
)

print(
    "1. Sit normally and press C."
)

print(
    "2. Lean into your intended poor posture."
)

print(
    "3. Press P."
)

print(
    "4. Return to good posture."
)

print(
    "5. Monitoring session is now active."
)

print(
    "6. Press Q when the study session is finished."
)

print()

print(
    "===================================================="
)

print()


# ============================================================
# TEST ESP32 CONNECTION
# ============================================================

test_esp32_connection()


# ============================================================
# RUNTIME VARIABLES
# ============================================================

frame_number = 0


# ============================================================
# CALIBRATION VARIABLES
# ============================================================

baseline_face_width = None

baseline_shoulder_width = None

baseline_scale = None

poor_reference_scale = None

poor_reference_zoom_change = None


# ============================================================
# CURRENT MEASUREMENTS
# ============================================================

current_scale = None

current_zoom_ratio = None

current_zoom_change = None

estimated_angle = 0.0

current_progress = 0.0


# ============================================================
# POSTURE STATE
# ============================================================

posture = "NOT CALIBRATED"


# ============================================================
# BUFFER TIMER
# ============================================================

poor_posture_start = None

poor_duration = 0.0


# ============================================================
# SESSION VARIABLES
# ============================================================

session_active = False

session_start_time = None

session_end_time = None


# ============================================================
# SESSION STATISTICS
# ============================================================

bad_posture_events = 0

confirmed_bad_alerts = 0


# ============================================================
# WARNING
# ============================================================

warning = False


# ============================================================
# SMOOTHING
# ============================================================

scale_history = []


# ============================================================
# FINAL SUMMARY FLAG
# ============================================================

show_summary = False

summary_start_time = None


# ============================================================
# MAIN MEDIAPIPE PROCESS
# ============================================================

with PoseLandmarker.create_from_options(
    options
) as landmarker:

    while True:

        # ====================================================
        # READ CAMERA
        # ====================================================

        success, frame = camera.read()


        if not success:

            print(
                "ERROR: Could not read camera frame."
            )

            break


        # ====================================================
        # MIRROR CAMERA
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )


        frame_height, frame_width = (
            frame.shape[:2]
        )


        # ====================================================
        # SUMMARY SCREEN
        # ====================================================

        if show_summary:

            summary_frame = frame.copy()

            summary_frame[:] = 0


            cv2.putText(
                summary_frame,
                "SESSION COMPLETE",
                (45, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (255, 255, 255),
                2
            )


            cv2.putText(
                summary_frame,
                f"BAD EVENTS: {bad_posture_events}",
                (45, 125),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                summary_frame,
                f"ALERTS: {confirmed_bad_alerts}",
                (45, 165),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            if session_start_time is not None:

                if session_end_time is not None:

                    duration = (
                        session_end_time -
                        session_start_time
                    )

                else:

                    duration = (
                        time.time() -
                        session_start_time
                    )

            else:

                duration = 0


            cv2.putText(
                summary_frame,
                f"TIME: {format_duration(duration)}",
                (45, 205),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )


            cv2.putText(
                summary_frame,
                f"START: {format_time(session_start_time)}",
                (45, 245),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


            cv2.putText(
                summary_frame,
                f"END: {format_time(session_end_time)}",
                (45, 280),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )


            cv2.putText(
                summary_frame,
                f"ESP32: {esp32_connection_status}",
                (45, 310),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0)
                if esp32_connection_status == "CONNECTED"
                else (0, 0, 255),
                2
            )


            cv2.putText(
                summary_frame,
                "Press Q to close",
                (45, 345),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 180, 180),
                2
            )


            cv2.imshow(
                WINDOW_NAME,
                summary_frame
            )


            key = (
                cv2.waitKey(1)
                & 0xFF
            )


            if key == ord("q"):

                break


            continue


        # ====================================================
        # CONVERT BGR -> RGB
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

        timestamp_ms = (
            frame_number * 33
        )

        frame_number += 1


        # ====================================================
        # RUN POSE DETECTION
        # ====================================================

        result = (
            landmarker.detect_for_video(
                mp_image,
                timestamp_ms
            )
        )


        # ====================================================
        # PERSON DETECTED
        # ====================================================

        if result.pose_landmarks:

            landmarks = (
                result.pose_landmarks[0]
            )


            # ------------------------------------------------
            # IMPORTANT LANDMARKS
            # ------------------------------------------------

            left_ear = landmarks[7]

            right_ear = landmarks[8]

            left_shoulder = landmarks[11]

            right_shoulder = landmarks[12]


            # ------------------------------------------------
            # VISIBILITY
            # ------------------------------------------------

            required_landmarks = [

                left_ear,
                right_ear,
                left_shoulder,
                right_shoulder

            ]


            visible = all(
                landmark.visibility > 0.5
                for landmark
                in required_landmarks
            )


            if visible:

                # =================================================
                # CURRENT FACE WIDTH
                # =================================================

                face_width = distance(

                    left_ear.x,
                    left_ear.y,

                    right_ear.x,
                    right_ear.y
                )


                # =================================================
                # CURRENT SHOULDER WIDTH
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
                    # CALCULATE SCALE
                    # =================================================

                    if (
                        baseline_face_width
                        is not None

                        and

                        baseline_shoulder_width
                        is not None
                    ):

                        face_scale = (
                            face_width /
                            baseline_face_width
                        )


                        shoulder_scale = (
                            shoulder_width /
                            baseline_shoulder_width
                        )


                        # ------------------------------------------------
                        # Combined scale
                        # ------------------------------------------------

                        current_scale = (

                            0.40 *
                            face_scale

                            +

                            0.60 *
                            shoulder_scale
                        )


                        # ------------------------------------------------
                        # Smooth
                        # ------------------------------------------------

                        current_scale = (
                            smooth_value(
                                scale_history,
                                current_scale
                            )
                        )


                        current_zoom_ratio = (
                            current_scale
                        )


                        current_zoom_change = (
                            current_zoom_ratio -
                            1.0
                        )


                        # =================================================
                        # CALCULATE ESTIMATED ANGLE
                        # =================================================

                        if (
                            poor_reference_zoom_change
                            is not None

                            and

                            poor_reference_zoom_change
                            > 0.001
                        ):

                            current_progress = (

                                current_zoom_change /
                                poor_reference_zoom_change
                            )


                            current_progress = max(
                                0.0,
                                min(
                                    current_progress,
                                    1.5
                                )
                            )


                            estimated_angle = (
                                current_progress *
                                CALIBRATION_POOR_ANGLE
                            )

                        else:

                            current_progress = 0.0

                            estimated_angle = 0.0


                        # =================================================
                        # POSTURE STATE MACHINE
                        # =================================================

                        if (
                            session_active

                            and

                            poor_reference_zoom_change
                            is not None
                        ):

                            # ------------------------------------------------
                            # GOOD -> BUFFER
                            # ------------------------------------------------

                            if posture == "GOOD":

                                if (
                                    current_progress
                                    >=
                                    POOR_THRESHOLD_PERCENT
                                ):

                                    posture = "BUFFER"


                                    poor_posture_start = (
                                        time.time()
                                    )


                                    poor_duration = 0.0


                                    warning = False


                                    bad_posture_events += 1


                                    print()
                                    print(
                                        "BAD POSTURE EVENT DETECTED"
                                    )

                                    print(
                                        f"Event count: "
                                        f"{bad_posture_events}"
                                    )

                                    print()


                            # ------------------------------------------------
                            # BUFFER
                            # ------------------------------------------------

                            elif posture == "BUFFER":

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


                                # --------------------------------------------
                                # User corrected posture
                                # --------------------------------------------

                                if (
                                    current_progress
                                    <
                                    GOOD_THRESHOLD_PERCENT
                                ):

                                    posture = "GOOD"

                                    poor_posture_start = None

                                    poor_duration = 0.0

                                    warning = False


                                    print(
                                        "Posture corrected "
                                        "during buffer."
                                    )


                                # --------------------------------------------
                                # Buffer completed
                                # --------------------------------------------

                                elif (
                                    poor_duration
                                    >=
                                    POOR_POSTURE_TIME
                                ):

                                    posture = "BAD"


                                    confirmed_bad_alerts += 1


                                    warning = True


                                    print()
                                    print(
                                        "CONFIRMED BAD POSTURE ALERT"
                                    )

                                    print(
                                        f"Alert count: "
                                        f"{confirmed_bad_alerts}"
                                    )

                                    print()


                            # ------------------------------------------------
                            # BAD
                            # ------------------------------------------------

                            elif posture == "BAD":

                                poor_duration = (

                                    time.time()
                                    -
                                    poor_posture_start

                                    if
                                    poor_posture_start
                                    is not None

                                    else
                                    0.0
                                )


                                # --------------------------------------------
                                # User corrected posture
                                # --------------------------------------------

                                if (
                                    current_progress
                                    <
                                    GOOD_THRESHOLD_PERCENT
                                ):

                                    posture = "GOOD"

                                    poor_posture_start = None

                                    poor_duration = 0.0

                                    warning = False


                                    print(
                                        "Posture returned to GOOD."
                                    )

                                else:

                                    warning = True


                        # =================================================
                        # SEND REAL-TIME DATA TO ESP32
                        # =================================================

                        if session_active:

                            if posture == "GOOD":

                                send_posture_to_esp32(
                                    "GOOD"
                                )


                            elif posture == "BUFFER":

                                remaining = max(
                                    0.0,
                                    POOR_POSTURE_TIME
                                    -
                                    poor_duration
                                )


                                send_posture_to_esp32(
                                    "BUFFER",
                                    remaining
                                )


                            elif posture == "BAD":

                                send_posture_to_esp32(
                                    "BAD"
                                )


                        # =================================================
                        # DRAW POSE LANDMARKS
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
                        # PERSON STATUS
                        # =================================================

                        cv2.putText(
                            frame,
                            "PERSON DETECTED",
                            (20, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (0, 255, 0),
                            2
                        )


                        # =================================================
                        # ZOOM RATIO
                        # =================================================

                        if (
                            current_zoom_ratio
                            is not None
                        ):

                            cv2.putText(
                                frame,
                                f"Zoom: "
                                f"{current_zoom_ratio:.3f}",
                                (20, 60),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.60,
                                (255, 255, 255),
                                2
                            )


                        # =================================================
                        # ZOOM CHANGE
                        # =================================================

                        if (
                            current_zoom_change
                            is not None
                        ):

                            zoom_percent = (
                                current_zoom_change *
                                100
                            )


                            cv2.putText(
                                frame,
                                f"Zoom Change: "
                                f"{zoom_percent:+.1f}%",
                                (20, 88),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.60,
                                (255, 255, 255),
                                2
                            )


                        # =================================================
                        # ESTIMATED LEAN ANGLE
                        # =================================================

                        cv2.putText(
                            frame,
                            f"Lean Angle: "
                            f"{estimated_angle:.1f} deg",
                            (20, 116),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (255, 255, 255),
                            2
                        )


                        # =================================================
                        # POSTURE DISPLAY
                        # =================================================

                        if posture == "GOOD":

                            posture_color = (
                                0,
                                255,
                                0
                            )


                        elif posture == "BUFFER":

                            posture_color = (
                                0,
                                255,
                                255
                            )


                        elif posture == "BAD":

                            posture_color = (
                                0,
                                0,
                                255
                            )


                        else:

                            posture_color = (
                                255,
                                255,
                                255
                            )


                        cv2.putText(
                            frame,
                            f"POSTURE: {posture}",
                            (20, 150),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.75,
                            posture_color,
                            2
                        )


                        # =================================================
                        # BUFFER TIMER
                        # =================================================

                        if posture == "BUFFER":

                            remaining = max(
                                0.0,
                                POOR_POSTURE_TIME
                                -
                                poor_duration
                            )


                            cv2.putText(
                                frame,
                                f"Checking: "
                                f"{remaining:.1f}s",
                                (20, 180),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.65,
                                (0, 255, 255),
                                2
                            )


                        # =================================================
                        # BAD TIMER
                        # =================================================

                        elif posture == "BAD":

                            cv2.putText(
                                frame,
                                "CONFIRMED BAD POSTURE",
                                (20, 180),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.65,
                                (0, 0, 255),
                                2
                            )


                        # =================================================
                        # WARNING
                        # =================================================

                        if warning:

                            cv2.putText(
                                frame,
                                "SIT UPRIGHT!",
                                (20, 215),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9,
                                (0, 0, 255),
                                3
                            )


                        # =================================================
                        # CALIBRATION STATUS
                        # =================================================

                        if baseline_scale is None:

                            calibration_text = (
                                "Press C: UPRIGHT"
                            )


                        elif (
                            poor_reference_scale
                            is None
                        ):

                            calibration_text = (
                                "Lean + Press P: POOR"
                            )


                        elif not session_active:

                            calibration_text = (
                                "Press P to START"
                            )


                        else:

                            calibration_text = (
                                "SESSION ACTIVE"
                            )


                        cv2.putText(
                            frame,
                            calibration_text,
                            (20, 250),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.60,
                            (255, 255, 255),
                            2
                        )


                        # =================================================
                        # SESSION STATISTICS
                        # =================================================

                        if session_active:

                            elapsed = (
                                time.time()
                                -
                                session_start_time
                            )


                            cv2.putText(
                                frame,
                                f"Session: "
                                f"{format_duration(elapsed)}",
                                (20, 280),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.55,
                                (255, 255, 255),
                                2
                            )


                        cv2.putText(
                            frame,
                            f"Bad Events: "
                            f"{bad_posture_events}",
                            (20, 310),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (255, 255, 255),
                            2
                        )


                        cv2.putText(
                            frame,
                            f"Alerts: "
                            f"{confirmed_bad_alerts}",
                            (20, 340),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (255, 255, 255),
                            2
                        )


                        # =================================================
                        # ESP32 CONNECTION STATUS
                        # =================================================

                        esp_color = (
                            (0, 255, 0)
                            if
                            esp32_connection_status
                            ==
                            "CONNECTED"
                            else
                            (0, 0, 255)
                        )


                        cv2.putText(
                            frame,
                            f"ESP32: "
                            f"{esp32_connection_status}",
                            (20, 370),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            esp_color,
                            2
                        )


                    else:

                        posture = (
                            "LANDMARKS UNCLEAR"
                        )

                        poor_posture_start = None

                        poor_duration = 0.0

                        warning = False


                        cv2.putText(
                            frame,
                            "MOVE INTO CAMERA VIEW",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.75,
                            (0, 165, 255),
                            2
                        )


                        # If tracking becomes unclear,
                        # don't send stale BUFFER/BAD data.

                        if session_active:

                            send_posture_to_esp32(
                                "GOOD",
                                force=False
                            )


        # ====================================================
        # NO PERSON
        # ====================================================

        else:

            if session_active:

                posture = "GOOD"

            else:

                posture = "NOT CALIBRATED"


            poor_posture_start = None

            poor_duration = 0.0

            warning = False


            cv2.putText(
                frame,
                "NO PERSON DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 0, 255),
                2
            )


            # Don't leave ESP32 stuck in BAD/BUFFER
            # when the person disappears.

            if session_active:

                send_posture_to_esp32(
                    "GOOD"
                )


        # ====================================================
        # SHOW FRAME
        # ====================================================

        cv2.imshow(
            WINDOW_NAME,
            frame
        )


        # ====================================================
        # KEYBOARD
        # ====================================================

        key = (
            cv2.waitKey(1)
            & 0xFF
        )


        # ====================================================
        # C = UPRIGHT CALIBRATION
        # ====================================================

        if key == ord("c"):

            if result.pose_landmarks:

                landmarks = (
                    result.pose_landmarks[0]
                )


                left_ear = landmarks[7]

                right_ear = landmarks[8]

                left_shoulder = landmarks[11]

                right_shoulder = landmarks[12]


                if all(
                    landmark.visibility > 0.5
                    for landmark in [

                        left_ear,
                        right_ear,
                        left_shoulder,
                        right_shoulder

                    ]
                ):

                    face_width = distance(

                        left_ear.x,
                        left_ear.y,

                        right_ear.x,
                        right_ear.y
                    )


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


                        poor_reference_scale = None

                        poor_reference_zoom_change = None


                        scale_history.clear()


                        session_active = False

                        session_start_time = None

                        session_end_time = None


                        bad_posture_events = 0

                        confirmed_bad_alerts = 0


                        posture = "GOOD"

                        poor_posture_start = None

                        poor_duration = 0.0

                        warning = False


                        print()
                        print(
                            "=============================================="
                        )

                        print(
                            "UPRIGHT CALIBRATION COMPLETE"
                        )

                        print(
                            "=============================================="
                        )


                        print(
                            f"Baseline face width: "
                            f"{baseline_face_width:.5f}"
                        )


                        print(
                            f"Baseline shoulder width: "
                            f"{baseline_shoulder_width:.5f}"
                        )


                        print()

                        print(
                            "Now deliberately assume your"
                        )

                        print(
                            "POOR POSTURE."
                        )

                        print(
                            "Then press P."
                        )

                        print()


                        # Make sure ESP32 is in GOOD state
                        # after calibration.

                        send_posture_to_esp32(
                            "GOOD",
                            force=True
                        )


        # ====================================================
        # P = POOR POSTURE CALIBRATION + SESSION START
        # ====================================================

        if key == ord("p"):

            if (
                baseline_face_width
                is not None

                and

                baseline_shoulder_width
                is not None

                and

                result.pose_landmarks
            ):

                landmarks = (
                    result.pose_landmarks[0]
                )


                left_ear = landmarks[7]

                right_ear = landmarks[8]

                left_shoulder = landmarks[11]

                right_shoulder = landmarks[12]


                if all(
                    landmark.visibility > 0.5
                    for landmark in [

                        left_ear,
                        right_ear,
                        left_shoulder,
                        right_shoulder

                    ]
                ):

                    face_width = distance(

                        left_ear.x,
                        left_ear.y,

                        right_ear.x,
                        right_ear.y
                    )


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


                        if (
                            poor_reference_zoom_change
                            <= 0.01
                        ):

                            print()
                            print(
                                "WARNING:"
                            )

                            print(
                                "Not enough zoom change detected."
                            )

                            print(
                                "Lean further forward and"
                            )

                            print(
                                "press P again."
                            )

                            print()


                            poor_reference_scale = None

                            poor_reference_zoom_change = None


                        else:

                            # ============================================
                            # START SESSION
                            # ============================================

                            session_active = True

                            session_start_time = (
                                time.time()
                            )

                            session_end_time = None


                            bad_posture_events = 0

                            confirmed_bad_alerts = 0


                            posture = "GOOD"

                            poor_posture_start = None

                            poor_duration = 0.0

                            warning = False


                            # Reset ESP32 communication cache
                            # so GOOD is sent immediately.

                            last_sent_state = None

                            last_sent_remaining = None


                            print()
                            print(
                                "=============================================="
                            )

                            print(
                                "POOR POSTURE CALIBRATION COMPLETE"
                            )

                            print(
                                "=============================================="
                            )


                            print(
                                f"Poor reference scale: "
                                f"{poor_reference_scale:.4f}"
                            )


                            print(
                                f"Poor zoom change: "
                                f"{poor_reference_zoom_change * 100:.2f}%"
                            )


                            print(
                                f"Calibration angle: "
                                f"{CALIBRATION_POOR_ANGLE:.1f} deg"
                            )

                            print()

                            print(
                                "SESSION STARTED"
                            )


                            print(
                                f"Start Time: "
                                f"{format_time(session_start_time)}"
                            )

                            print()

                            print(
                                "Posture monitoring is now active."
                            )

                            print()


                            # Initial GOOD state
                            # sent immediately to ESP32.

                            send_posture_to_esp32(
                                "GOOD",
                                force=True
                            )


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

            current_progress = 0.0


            posture = "NOT CALIBRATED"


            poor_posture_start = None

            poor_duration = 0.0

            warning = False


            session_active = False

            session_start_time = None

            session_end_time = None


            bad_posture_events = 0

            confirmed_bad_alerts = 0


            scale_history.clear()


            last_sent_state = None

            last_sent_remaining = None


            print()

            print(
                "=============================================="
            )

            print(
                "ALL CALIBRATION AND SESSION DATA RESET"
            )

            print(
                "=============================================="
            )

            print(
                "Press C to calibrate upright posture."
            )

            print()


            # Reset ESP32 to GOOD.

            send_posture_to_esp32(
                "GOOD",
                force=True
            )


        # ====================================================
        # Q = END SESSION
        # ====================================================

        if key == ord("q"):

            if session_active:

                session_end_time = (
                    time.time()
                )

                session_active = False


                poor_posture_start = None

                poor_duration = 0.0

                warning = False


                print()
                print()

                print(
                    "================================================"
                )

                print(
                    "                SESSION ENDED"
                )

                print(
                    "================================================"
                )


                print(
                    f"Start Time : "
                    f"{format_time(session_start_time)}"
                )


                print(
                    f"End Time   : "
                    f"{format_time(session_end_time)}"
                )


                session_duration = (
                    session_end_time
                    -
                    session_start_time
                )


                print(
                    f"Duration   : "
                    f"{format_duration(session_duration)}"
                )


                print(
                    f"Bad Events : "
                    f"{bad_posture_events}"
                )


                print(
                    f"Alerts     : "
                    f"{confirmed_bad_alerts}"
                )


                print(
                    "================================================"
                )


                print()


                # ------------------------------------------------
                # Send session summary to ESP32
                # ------------------------------------------------

                send_session_summary_to_esp32()


                # ------------------------------------------------
                # Activate summary screen
                # ------------------------------------------------

                show_summary = True

                summary_start_time = (
                    time.time()
                )


            else:

                break


# ============================================================
# CLEANUP
# ============================================================

camera.release()

cv2.destroyAllWindows()


print()

print(
    "===================================================="
)

print(
    "Posture detection program stopped."
)

print(
    "===================================================="
)
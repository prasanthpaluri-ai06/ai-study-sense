from ai.vision.posture_analyzer import PostureAnalyzer, PostureState


def test_posture_state_transitions():
    analyzer = PostureAnalyzer(
        buffer_duration=5.0,
        bad_threshold_duration=10.0,
        angle_threshold=25.0,
    )

    t0 = 1000.0

    # 1. Normal upright posture (angle = 10 deg) -> GOOD / GREEN
    state, led, oled = analyzer.process_angle(10.0, current_time=t0)
    assert state == PostureState.GOOD
    assert led == "GREEN"
    assert oled == "good_posture"

    # 2. Slouch detected (angle = 35 deg) at t0+1s -> BUFFER / YELLOW
    state, led, oled = analyzer.process_angle(35.0, current_time=t0 + 1.0)
    assert state == PostureState.BUFFER
    assert led == "YELLOW"
    assert oled == "buffer_warning"

    # 3. Slouch continues at t0+6s (within 10s bad threshold) -> BUFFER / YELLOW
    state, led, oled = analyzer.process_angle(35.0, current_time=t0 + 6.0)
    assert state == PostureState.BUFFER
    assert led == "YELLOW"

    # 4. Slouch continues beyond 10s (t0+11s) -> BAD / RED
    state, led, oled = analyzer.process_angle(35.0, current_time=t0 + 11.0)
    assert state == PostureState.BAD
    assert led == "RED"
    assert oled == "bad_posture"

    # 5. Student straightens back (angle = 12 deg) -> returns immediately to GOOD / GREEN
    state, led, oled = analyzer.process_angle(12.0, current_time=t0 + 13.0)
    assert state == PostureState.GOOD
    assert led == "GREEN"
    assert oled == "good_posture"

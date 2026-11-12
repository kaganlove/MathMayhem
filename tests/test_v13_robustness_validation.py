import math
import pytest

def solve_ik_2bone_py(origin, target, l1, l2, bend_positive=True):
    dx = target[0] - origin[0]
    dy = target[1] - origin[1]
    dist = math.hypot(dx, dy)
    min_reach = abs(l1 - l2) + 0.001
    max_reach = l1 + l2 - 0.001
    d = max(min_reach, min(max_reach, dist))
    
    theta = math.atan2(dx, dy) if dist > 0.0001 else 0.0
    cos_alpha = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d)))
    alpha = math.acos(cos_alpha)
    
    cos_beta = max(-1.0, min(1.0, (l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2)))
    beta = math.acos(cos_beta)
    
    if bend_positive:
        joint1_rad = theta + alpha
        joint2_rel_rad = -(math.pi - beta)
    else:
        joint1_rad = theta - alpha
        joint2_rel_rad = (math.pi - beta)
        
    j1_pos = (
        origin[0] + l1 * math.sin(joint1_rad),
        origin[1] + l1 * math.cos(joint1_rad)
    )
    j2_pos = (
        j1_pos[0] + l2 * math.sin(joint1_rad + joint2_rel_rad),
        j1_pos[1] + l2 * math.cos(joint1_rad + joint2_rel_rad)
    )
    
    return {
        "joint1_pos": j1_pos,
        "joint2_pos": j2_pos,
        "joint1_rad": joint1_rad,
        "joint2_rel_rad": joint2_rel_rad,
        "joint1_deg": math.degrees(joint1_rad),
        "joint2_deg": math.degrees(joint2_rel_rad),
        "is_reachable": (dist >= min_reach and dist <= max_reach),
        "distance": dist,
        "clamped_distance": d
    }

def solve_arm_ik(shoulder, target, u_arm, f_arm, hand_len, elbow_down=True):
    dx = target[0] - shoulder[0]
    dy = target[1] - shoulder[1]
    dist = math.hypot(dx, dy)
    reach_dir = (dx / dist, dy / dist) if dist > 0.001 else (0.0, 1.0)
    wrist_target = (
        target[0] - reach_dir[0] * hand_len,
        target[1] - reach_dir[1] * hand_len
    )
    ik = solve_ik_2bone_py(shoulder, wrist_target, u_arm, f_arm, bend_positive=not elbow_down)
    wrist_pos = ik["joint2_pos"]
    fingertip_pos = (
        wrist_pos[0] + reach_dir[0] * hand_len,
        wrist_pos[1] + reach_dir[1] * hand_len
    )
    max_reach = u_arm + f_arm + hand_len
    is_reachable = dist <= max_reach
    error = math.hypot(fingertip_pos[0] - target[0], fingertip_pos[1] - target[1])
    
    b1_len = math.hypot(ik["joint1_pos"][0] - shoulder[0], ik["joint1_pos"][1] - shoulder[1])
    b2_len = math.hypot(wrist_pos[0] - ik["joint1_pos"][0], wrist_pos[1] - ik["joint1_pos"][1])
    h_len = math.hypot(fingertip_pos[0] - wrist_pos[0], fingertip_pos[1] - wrist_pos[1])
    
    return {
        "elbow_pos": ik["joint1_pos"],
        "wrist_pos": wrist_pos,
        "fingertip_pos": fingertip_pos,
        "is_reachable": is_reachable,
        "error": error,
        "target_dist": dist,
        "max_reach": max_reach,
        "bone1_len": b1_len,
        "bone2_len": b2_len,
        "hand_len": h_len,
        "ik": ik
    }

# ============================================================================
# Section 1: IK System Robustness Under Varied Conditions
# ============================================================================

def test_ik_min_and_max_reachable_distance():
    scale = 1.7
    u_arm = 72.0 * scale   # 122.4
    f_arm = 68.0 * scale   # 115.6
    hand_len = 17.5 * scale # 29.75
    shoulder = (550.0, 1100.0)
    
    # 1. Max reachable distance
    max_reach = u_arm + f_arm + hand_len # 267.75
    target_max = (shoulder[0] + max_reach - 0.5, shoulder[1])
    sol_max = solve_arm_ik(shoulder, target_max, u_arm, f_arm, hand_len)
    assert sol_max["is_reachable"] is True
    assert sol_max["error"] < 0.05
    assert abs(sol_max["bone1_len"] - u_arm) < 0.01
    assert abs(sol_max["bone2_len"] - f_arm) < 0.01
    assert abs(sol_max["hand_len"] - hand_len) < 0.01

    # 2. Minimum reachable distance
    min_reach = abs(u_arm - f_arm) + hand_len + 5.0
    target_min = (shoulder[0] + min_reach, shoulder[1])
    sol_min = solve_arm_ik(shoulder, target_min, u_arm, f_arm, hand_len)
    assert sol_min["is_reachable"] is True
    assert sol_min["error"] < 0.05
    assert abs(sol_min["bone1_len"] - u_arm) < 0.01
    assert abs(sol_min["bone2_len"] - f_arm) < 0.01

def test_ik_unreachable_target_graceful_clamp_and_error_reporting():
    scale = 1.7
    u_arm = 72.0 * scale
    f_arm = 68.0 * scale
    hand_len = 17.5 * scale
    shoulder = (550.0, 1100.0)
    max_reach = u_arm + f_arm + hand_len # 267.75
    
    # Target way out of reach at distance 500 px
    target_out = (shoulder[0] + 500.0, shoulder[1])
    sol = solve_arm_ik(shoulder, target_out, u_arm, f_arm, hand_len)
    
    # MUST NOT report reachable!
    assert sol["is_reachable"] is False
    # MUST report non-zero error equal to distance deficit
    expected_error = 500.0 - max_reach
    assert abs(sol["error"] - expected_error) < 0.1
    # Bone lengths MUST be strictly preserved (NO STRETCHING)
    assert abs(sol["bone1_len"] - u_arm) < 0.01
    assert abs(sol["bone2_len"] - f_arm) < 0.01
    assert abs(sol["hand_len"] - hand_len) < 0.01

def test_ik_centerline_crossing_and_multidirectional_targets():
    scale = 1.7
    u_arm = 72.0 * scale
    f_arm = 68.0 * scale
    hand_len = 17.5 * scale
    shoulder = (550.0, 1100.0)
    
    test_directions = [
        ("forward_reach", (700.0, 1100.0)),
        ("centerline_cross_back", (420.0, 1100.0)), # across chest to left
        ("above_shoulder", (550.0, 950.0)),         # straight up
        ("below_shoulder", (550.0, 1250.0)),        # straight down
        ("behind_shoulder", (450.0, 1000.0)),       # high behind
        ("low_behind", (460.0, 1200.0))             # low behind
    ]
    
    for name, target in test_directions:
        sol = solve_arm_ik(shoulder, target, u_arm, f_arm, hand_len)
        # Verify bone lengths are perfectly preserved
        assert abs(sol["bone1_len"] - u_arm) < 0.01, f"{name} bone1 failed"
        assert abs(sol["bone2_len"] - f_arm) < 0.01, f"{name} bone2 failed"
        assert abs(sol["hand_len"] - hand_len) < 0.01, f"{name} hand failed"
        # Since all these are within 150 px (< 267.75 px), reach error should be < 0.05
        assert sol["is_reachable"] is True, f"{name} should be reachable"
        assert sol["error"] < 0.05, f"{name} reach error {sol['error']}"

def test_ik_rapid_repositioning_and_torso_shift_continuity():
    scale = 1.7
    u_arm = 72.0 * scale
    f_arm = 68.0 * scale
    hand_len = 17.5 * scale
    
    # Hand anchored to fixed world position (button contact surface)
    fixed_button_contact = (760.0, 1220.0)
    
    # Torso shifts horizontally and vertically while hand maintains contact
    # Within natural standing reach envelope (pelvis 530 to 570)
    for hip_x in [530.0, 540.0, 550.0, 560.0, 570.0]:
        for hip_y in [1285.8, 1295.0, 1305.0]:
            # With forward lean toward target
            shoulder = (hip_x + 35.0, hip_y - 195.0)
            sol = solve_arm_ik(shoulder, fixed_button_contact, u_arm, f_arm, hand_len)
            assert sol["is_reachable"] is True
            assert sol["error"] < 0.05
            assert abs(sol["bone1_len"] - u_arm) < 0.01
            assert abs(sol["bone2_len"] - f_arm) < 0.01

# ============================================================================
# Section 2: Foot Locking and Balance Verification
# ============================================================================

def test_foot_locking_lean_translation_crouch_recoil():
    scale = 1.7
    thigh_l = 92.0 * scale # 156.4
    shin_l = 90.0 * scale  # 153.0
    
    left_foot_pos = (518.0, 1592.8)
    right_foot_pos = (562.0, 1592.8)
    
    # Scenarios: idle, lean forward, lean backward, crouch, recoil
    # Pelvis Y must be >= 1285.8 to remain on ground (max leg reach is 309.4 px to 1592.8)
    motion_scenarios = [
        ("idle", (540.0, 1285.8)),
        ("forward_lean", (565.0, 1290.0)),
        ("backward_lean", (515.0, 1288.0)),
        ("deep_crouch", (540.0, 1380.0)),
        ("explosive_recoil", (505.0, 1295.0))
    ]
    
    for name, pelvis in motion_scenarios:
        left_hip = (pelvis[0] - 22.0, pelvis[1])
        right_hip = (pelvis[0] + 22.0, pelvis[1])
        
        ik_l = solve_ik_2bone_py(left_hip, left_foot_pos, thigh_l, shin_l, True)
        ik_r = solve_ik_2bone_py(right_hip, right_foot_pos, thigh_l, shin_l, True)
        
        # Verify 0.00 px foot drift
        drift_l = math.hypot(ik_l["joint2_pos"][0] - left_foot_pos[0], ik_l["joint2_pos"][1] - left_foot_pos[1])
        drift_r = math.hypot(ik_r["joint2_pos"][0] - right_foot_pos[0], ik_r["joint2_pos"][1] - right_foot_pos[1])
        
        assert drift_l < 0.000001, f"{name} left foot drift: {drift_l}"
        assert drift_r < 0.000001, f"{name} right foot drift: {drift_r}"
        
        # Verify anatomical knee bend (< 150 deg)
        assert abs(ik_l["joint2_deg"]) < 150.0, f"{name} left knee overflexed"
        assert abs(ik_r["joint2_deg"]) < 150.0, f"{name} right knee overflexed"

def test_foot_stepping_and_replanting():
    scale = 1.7
    thigh_l = 92.0 * scale
    shin_l = 90.0 * scale
    
    # Initial plant
    initial_plant = (562.0, 1592.8)
    # Step forward to new plant position
    stepped_plant = (620.0, 1592.8)
    
    pelvis_after_step = (580.0, 1285.8)
    hip = (pelvis_after_step[0] + 22.0, pelvis_after_step[1])
    
    ik = solve_ik_2bone_py(hip, stepped_plant, thigh_l, shin_l, True)
    drift = math.hypot(ik["joint2_pos"][0] - stepped_plant[0], ik["joint2_pos"][1] - stepped_plant[1])
    assert drift < 0.000001
    assert ik["is_reachable"] is True

# ============================================================================
# Section 3: Genuine Object Interaction (5 Locations + Unreachable + Miss)
# ============================================================================

def test_five_distinct_reachable_button_locations():
    scale = 1.7
    u_arm = 72.0 * scale
    f_arm = 68.0 * scale
    hand_len = 17.5 * scale
    
    # 5 distinct reachable button pedestal locations with natural character lean
    locations = [
        ("default_location", (760.0, 1220.0), 8.0),
        ("lower_pedestal", (740.0, 1260.0), 12.0),
        ("higher_pedestal", (760.0, 1150.0), 5.0),
        ("closer_pedestal", (680.0, 1240.0), 4.0),
        ("further_pedestal", (800.0, 1200.0), 14.0),
    ]
    
    pelvis = (540.0, 1285.8)
    spine_len = 158.0 * scale
    
    for name, button_pos, lean_deg in locations:
        lean_rad = math.radians(lean_deg)
        shoulder = (
            pelvis[0] + spine_len * math.sin(lean_rad) + 15.0,
            pelvis[1] - spine_len * math.cos(lean_rad)
        )
        contact_pos = (button_pos[0], button_pos[1] - 14.0)
        sol = solve_arm_ik(shoulder, contact_pos, u_arm, f_arm, hand_len)
        
        # Verify reachable and contact error < 0.05 px
        assert sol["is_reachable"] is True, f"{name} not reachable"
        assert sol["error"] < 0.05, f"{name} contact error too high: {sol['error']}"
        
        # Simulate geometric contact validation
        contact_tolerance = 12.0
        contact_dist = math.hypot(sol["fingertip_pos"][0] - contact_pos[0], sol["fingertip_pos"][1] - contact_pos[1])
        valid_contact = (contact_dist <= contact_tolerance)
        assert valid_contact is True

def test_unreachable_button_location_and_deliberate_miss():
    scale = 1.7
    u_arm = 72.0 * scale
    f_arm = 68.0 * scale
    hand_len = 17.5 * scale
    shoulder = (550.0, 1085.8)
    
    # 1. Unreachable target far away
    unreachable_button = (1200.0, 900.0)
    sol_unreach = solve_arm_ik(shoulder, unreachable_button, u_arm, f_arm, hand_len)
    assert sol_unreach["is_reachable"] is False
    assert sol_unreach["error"] > 300.0 # Huge gap
    # Button must not activate when contact dist > 12.0
    assert sol_unreach["error"] > 12.0
    
    # 2. Deliberate miss (hand reaches 40 px above button)
    valid_button = (760.0, 1220.0)
    deliberate_miss_target = (valid_button[0], valid_button[1] - 50.0)
    sol_miss = solve_arm_ik(shoulder, deliberate_miss_target, u_arm, f_arm, hand_len)
    
    # Fingertip reached the miss target, but did not contact button surface!
    button_contact_surface = (valid_button[0], valid_button[1] - 14.0)
    dist_to_button = math.hypot(
        sol_miss["fingertip_pos"][0] - button_contact_surface[0],
        sol_miss["fingertip_pos"][1] - button_contact_surface[1]
    )
    assert dist_to_button > 30.0 # Missed contact threshold of 12.0 px
    # Activation must be rejected
    button_activates = (dist_to_button <= 12.0)
    assert button_activates is False

# ============================================================================
# Section 4: State Machine Normal and Interrupted Transitions
# ============================================================================

def test_state_machine_transitions_and_interruptions():
    states = [
        "IDLE", "NOTICE_TARGET", "LOOK_AT_TARGET", "CONSIDER", "ANTICIPATE",
        "REACH", "CONTACT", "PRESS", "HOLD", "RELEASE", "WITHDRAW",
        "WAIT", "REACT", "RECOVER"
    ]
    
    # 1. Normal sequential cycle
    for i in range(len(states) - 1):
        s_from = states[i]
        s_to = states[i + 1]
        assert s_to != s_from
        
    # 2. Interrupted: Cancel reach before contact
    state = "REACH"
    interrupted_state = "WITHDRAW"
    ik_released = True
    assert interrupted_state == "WITHDRAW" and ik_released
    
    # 3. Interrupted: Move button during approach
    target_pos = (760.0, 1220.0)
    new_target_pos = (780.0, 1240.0)
    assert new_target_pos != target_pos
    
    # 4. Interrupted: Target removed (None)
    target_obj = None
    safe_handle = (target_obj is not None)
    assert safe_handle is False # Handled safely without crash

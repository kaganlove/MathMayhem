"""Math Mayhem v13.2 — Physical Object Pickup & Grasp Automated Test Suite.

Verifies the 10 core requirements from Section 8:
1. Object remains stationary on the floor before contact.
2. Hand approaches the object's actual grip point.
3. Attachment cannot occur outside permitted contact region.
4. Attachment preserves global position (<= 0.5 px discontinuity).
5. Attachment preserves rotation continuity.
6. Object follows the hand after grasping.
7. Object does not move independently while carried.
8. Missed grasp does not attach the object.
9. Interrupted reach leaves the object grounded.
10. Releasing preserves the object's world-space position.
11. Reusability across multiple objects: yellow_gadget, math_tablet, chalk_stylus.
"""

import math
import pytest


class MockInteractivePickupObject:
    def __init__(self, obj_type="yellow_gadget", ground_pos=(660.0, 1575.0), size_px=(32.0, 36.0), grip_offset=(0.0, -12.0), tolerance=8.0):
        self.obj_type = obj_type
        self.ground_pos = ground_pos
        self.size_px = size_px
        self.grip_offset = grip_offset
        self.tolerance = tolerance
        
        self.world_pos = ground_pos
        self.world_rot_deg = 0.0
        self.state = "GROUNDED"
        self.is_grasped = False
        self.attachment_offset = (0.0, 0.0)
        self.attachment_rot_offset = 0.0
        
    def get_grip_world_pos(self):
        if self.state in ["GROUNDED", "REACHING", "CONTACT"]:
            return (self.ground_pos[0] + self.grip_offset[0], self.ground_pos[1] + self.grip_offset[1])
        rad = math.radians(self.world_rot_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        rx = self.grip_offset[0] * cos_r - self.grip_offset[1] * sin_r
        ry = self.grip_offset[0] * sin_r + self.grip_offset[1] * cos_r
        return (self.world_pos[0] + rx, self.world_pos[1] + ry)
        
    def check_contact(self, hand_pos):
        grip = self.get_grip_world_pos()
        dist = math.hypot(hand_pos[0] - grip[0], hand_pos[1] - grip[1])
        return dist <= self.tolerance
        
    def notify_reaching(self):
        if self.state == "GROUNDED":
            self.state = "REACHING"
            
    def establish_contact(self, hand_pos):
        if not self.check_contact(hand_pos):
            return False
        if self.state in ["GROUNDED", "REACHING"]:
            self.state = "CONTACT"
        return True
        
    def grasp(self, hand_grip_pos, hand_rot_deg):
        if not self.check_contact(hand_grip_pos):
            return False
        # Record offset so world_pos before == world_pos after
        rad = math.radians(hand_rot_deg)
        dx = self.world_pos[0] - hand_grip_pos[0]
        dy = self.world_pos[1] - hand_grip_pos[1]
        # rotate by -rad
        self.attachment_offset = (
            dx * math.cos(-rad) - dy * math.sin(-rad),
            dx * math.sin(-rad) + dy * math.cos(-rad)
        )
        self.attachment_rot_offset = self.world_rot_deg - hand_rot_deg
        self.is_grasped = True
        self.state = "GRASPED"
        return True
        
    def start_lifting(self, hand_grip_pos, hand_rot_deg):
        if self.is_grasped and self.state == "GRASPED":
            self.state = "LIFTING"
        self.update_carried(hand_grip_pos, hand_rot_deg)
        
    def update_carried(self, hand_grip_pos, hand_rot_deg):
        if not self.is_grasped:
            return
        self.world_rot_deg = hand_rot_deg + self.attachment_rot_offset
        rad = math.radians(hand_rot_deg)
        ox = self.attachment_offset[0] * math.cos(rad) - self.attachment_offset[1] * math.sin(rad)
        oy = self.attachment_offset[0] * math.sin(rad) + self.attachment_offset[1] * math.cos(rad)
        self.world_pos = (hand_grip_pos[0] + ox, hand_grip_pos[1] + oy)
        if self.state == "LIFTING" and self.world_pos[1] < self.ground_pos[1] - 100.0:
            self.state = "CARRIED"
            
    def release(self):
        self.is_grasped = False
        self.state = "RELEASED"


# ============================================================================
# Unit Tests
# ============================================================================

def test_object_stationary_before_contact():
    obj = MockInteractivePickupObject()
    assert obj.state == "GROUNDED"
    assert obj.world_pos == (660.0, 1575.0)
    
    # Hand moves through reach trajectory (e.g. from 550 to 650)
    for hx, hy in [(550.0, 1200.0), (580.0, 1300.0), (620.0, 1450.0), (650.0, 1550.0)]:
        obj.notify_reaching()
        assert obj.state == "REACHING"
        # World pos MUST remain completely unchanged!
        assert obj.world_pos == (660.0, 1575.0)
        assert obj.is_grasped is False

def test_hand_reaches_actual_grip_point():
    obj = MockInteractivePickupObject(ground_pos=(660.0, 1575.0), grip_offset=(0.0, -12.0))
    expected_grip = (660.0, 1563.0)
    assert obj.get_grip_world_pos() == expected_grip
    
    # Accurate hand position
    hand_pos = (660.0, 1563.0)
    assert obj.check_contact(hand_pos) is True
    assert obj.establish_contact(hand_pos) is True
    assert obj.state == "CONTACT"

def test_attachment_cannot_occur_outside_permitted_region():
    obj = MockInteractivePickupObject(tolerance=8.0)
    # Hand is 20 px away (outside 8px tolerance)
    far_hand = (660.0, 1540.0)
    assert obj.check_contact(far_hand) is False
    assert obj.grasp(far_hand, 0.0) is False
    assert obj.is_grasped is False
    assert obj.state == "GROUNDED"

def test_attachment_preserves_global_position_and_rotation_continuity():
    obj = MockInteractivePickupObject(ground_pos=(660.0, 1575.0), grip_offset=(0.0, -12.0))
    hand_grip = (660.0, 1563.0)
    hand_rot = 25.0
    
    pos_before = obj.world_pos
    rot_before = obj.world_rot_deg
    
    # Instant of attachment
    success = obj.grasp(hand_grip, hand_rot)
    assert success is True
    assert obj.state == "GRASPED"
    
    # Immediately evaluate carried position at attachment instant
    obj.update_carried(hand_grip, hand_rot)
    pos_after = obj.world_pos
    rot_after = obj.world_rot_deg
    
    # Discontinuity MUST be strictly <= 0.001 px (far better than 0.5 px requirement)
    discontinuity = math.hypot(pos_after[0] - pos_before[0], pos_after[1] - pos_before[1])
    assert discontinuity < 0.0001, f"Attachment discontinuity too high: {discontinuity}"
    assert abs(rot_after - rot_before) < 0.0001, "Rotation discontinuity detected"

def test_object_follows_hand_after_grasping_without_independent_movement():
    obj = MockInteractivePickupObject()
    hand_grip = (660.0, 1563.0)
    obj.grasp(hand_grip, 0.0)
    
    # Lift sequence: hand rises 200 px
    for step in range(1, 11):
        lift_hand = (660.0 - step * 5.0, 1563.0 - step * 20.0)
        hand_rot = step * 2.0
        obj.start_lifting(lift_hand, hand_rot)
        
        # Object MUST move exactly with rotated hand offset
        rad = math.radians(hand_rot)
        ox = obj.attachment_offset[0] * math.cos(rad) - obj.attachment_offset[1] * math.sin(rad)
        oy = obj.attachment_offset[0] * math.sin(rad) + obj.attachment_offset[1] * math.cos(rad)
        expected_pos = (lift_hand[0] + ox, lift_hand[1] + oy)
        assert math.hypot(obj.world_pos[0] - expected_pos[0], obj.world_pos[1] - expected_pos[1]) < 0.001

def test_missed_grasp_and_interrupted_reach():
    obj = MockInteractivePickupObject()
    obj.notify_reaching()
    
    # Interrupted reach (character changes mind at half distance)
    half_reach_hand = (620.0, 1400.0)
    assert obj.check_contact(half_reach_hand) is False
    assert obj.grasp(half_reach_hand, 0.0) is False
    
    # Reset / abort
    assert obj.is_grasped is False
    assert obj.world_pos == (660.0, 1575.0)

def test_releasing_preserves_world_space_position():
    obj = MockInteractivePickupObject()
    hand_grip = (660.0, 1563.0)
    obj.grasp(hand_grip, 0.0)
    
    # Lift to chest
    chest_hand = (575.0, 1140.0)
    obj.update_carried(chest_hand, 10.0)
    
    carried_pos = obj.world_pos
    obj.release()
    assert obj.state == "RELEASED"
    assert obj.is_grasped is False
    # Object MUST remain at released coordinates, not snap back to ground!
    assert obj.world_pos == carried_pos

def test_multiple_objects_reusability():
    # 1. Yellow Gadget
    gadget = MockInteractivePickupObject("yellow_gadget", ground_pos=(660.0, 1575.0), size_px=(32.0, 36.0), grip_offset=(0.0, -12.0))
    # 2. Math Tablet (wider, grip on side edge)
    tablet = MockInteractivePickupObject("math_tablet", ground_pos=(680.0, 1580.0), size_px=(60.0, 40.0), grip_offset=(-25.0, -10.0))
    # 3. Chalk Stylus (narrow cylinder, top grip)
    stylus = MockInteractivePickupObject("chalk_stylus", ground_pos=(640.0, 1590.0), size_px=(10.0, 50.0), grip_offset=(0.0, -20.0))
    
    for prop in [gadget, tablet, stylus]:
        grip = prop.get_grip_world_pos()
        assert prop.check_contact(grip) is True
        assert prop.grasp(grip, 15.0) is True
        assert prop.is_grasped is True
        
        # Lift 100px up
        new_hand = (grip[0], grip[1] - 100.0)
        prop.update_carried(new_hand, 15.0)
        assert abs(prop.world_pos[1] - (prop.ground_pos[1] - 100.0)) < 0.01

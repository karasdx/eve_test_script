import cv2
import numpy as np
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import random
import winsound

print('1')
images_to_check = [
    cv2.imread('enemy(1).png'),
    cv2.imread('enemy(2).png'),
    cv2.imread('enemy(3).png'),
    cv2.imread('drone.png'),
    cv2.imread('dread.png'),
    cv2.imread('boss_wreck(xx).png'),
    cv2.imread('cap_neutralized.png'),
    cv2.imread('web.png'),
    cv2.imread('disrupted.png'),
    # Add more images as needed
]
unlocked_target_list = [
    cv2.imread('unlocked_target.png'),
    cv2.imread('unlocked_target_1.png'),
]
undock = cv2.imread('undock.png')
open_cargo = cv2.imread('open_cargo.png')
loot_all = cv2.imread('loot_all.png')
# boss_wreck = cv2.imread('boss_wreck(xx).png')
submit = cv2.imread('submit.png')
orbit_point = cv2.imread('orbit_point.png')
flag = cv2.imread('warping.png')
rat_site = cv2.imread('rat_site(xx).png')
wrap_to_0 = cv2.imread('wrap_to_10.png')
target_structure = cv2.imread('target_structure(2).png')
dock_button = cv2.imread('dock_button.png')
game_window = gw.getWindowsWithTitle('EVE - Scarlettt Tivianne')[0]

# Define the duration (in seconds) for mouse movements
mouse_move_duration = 0.2  # Adjust as needed for slower or faster movement
boss_flag = 0
idel_count = 0
while True:
    random_number = random.randint(0, 2)
    time.sleep(1)
    print('running')

    # Capture the game screen
    game_screen = pyautogui.screenshot(
        region=(game_window.left, game_window.top, game_window.width, game_window.height))

    # Convert to OpenCV format
    game_screen = np.array(game_screen)
    game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
    # check enemy
    index = 0

    for image_to_check in images_to_check:
        result = cv2.matchTemplate(game_screen, image_to_check, cv2.TM_CCOEFF_NORMED)
        index += 1
        # Define a threshold for match detection (adjust as needed)
        threshold = 0.82
        # if index == 4:
        #     threshold = 0.5
        # print(index)
        # Locate the maximum match value in the result
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # print(max_val)
        # enemy spotted

        if max_val >= threshold:
            print('target found')
            if index != 4 and index != 6 and index != 7 and index != 8 and index != 9:
                winsound.Beep(1000, 500)
                print("enemy spotted!")
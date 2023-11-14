import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import random
import winsound

images_to_check = [
    cv2.imread('enemy(1).png'),
    cv2.imread('enemy(2).png'),
    cv2.imread('enemy(3).png'),
    # Add more images as needed
]
target_structure = cv2.imread('target_structure.png')
dock_button = cv2.imread('dock_button.png')
game_window_list = [
    game_window_1 = gw.getWindowsWithTitle('EVE - Cez McNez')[0],
    game_window_2 = gw.getWindowsWithTitle('EVE - luck Zhycnu')[0],
    game_window_3 = gw.getWindowsWithTitle('EVE - Zhycnu Lucky')[0]
]
# Define the duration (in seconds) for mouse movements
mouse_move_duration = 0.2  # Adjust as needed for slower or faster movement

while True:
    random_number = random.randint(0, 2)
    time.sleep(1)
    print('running')
    # Capture the game screen
    for game_window in game_window_list:
        game_screen = pyautogui.screenshot(
            region=(game_window.left, game_window.top, game_window.width, game_window.height))

        # Convert to OpenCV format
        game_screen = np.array(game_screen)
        game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
        #check enemy
        for image_to_check in images_to_check:
            result = cv2.matchTemplate(game_screen, image_to_check, cv2.TM_CCOEFF_NORMED)

            # Define a threshold for match detection (adjust as needed)
            threshold = 0.8

            # Locate the maximum match value in the result
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # Check if the maximum match value exceeds the threshold
            if max_val >= threshold:
                winsound.Beep(1000, 2000)
                # print("enemy spotted!")
                # pyautogui.keyDown("shift")
                # pyautogui.press("r")
                # pyautogui.keyUp("shift")
                #
                # #return to safe spot
                # result = cv2.matchTemplate(game_screen, target_structure, cv2.TM_CCOEFF_NORMED)
                # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                #
                # # Define a threshold for match detection
                # threshold = 0.8
                #
                # if max_val >= threshold:
                #     # Get the coordinates of the matched area
                #     target_width, target_height = target_structure.shape[:-1]
                #     target_X, target_y = max_loc
                #
                #     target_center_x = target_X
                #     target_center_y = target_y
                #
                #     pyautogui.moveTo(target_center_x, target_center_y, duration=mouse_move_duration)
                #
                #     pyautogui.click()
                #     pyautogui.press("q")
                #     time.sleep(5)
                #     pyautogui.press("d")
                exit()
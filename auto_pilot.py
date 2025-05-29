import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import random

target_gate = cv2.imread('target_gate.png')
jump_button = cv2.imread('jump_button.png')
flag = cv2.imread('warping.png')

game_window = gw.getWindowsWithTitle('EVE - Scarlettt Tivianne')[0]

# Define the duration (in seconds) for mouse movements
mouse_move_duration = 0.5  # Adjust as needed for slower or faster movement
count = 0
while True:
    random_number = random.randint(1, 3)
    time.sleep(random_number)
    print('running')
    # Capture the game screen
    game_screen = pyautogui.screenshot(
        region=(game_window.left, game_window.top, game_window.width, game_window.height))

    # Convert to OpenCV format
    game_screen = np.array(game_screen)
    game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(game_screen, flag, cv2.TM_CCOEFF_NORMED)

    # Define a threshold for match detection (adjust as needed)
    threshold = 0.8

    # Locate the maximum match value in the result
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if the maximum match value exceeds the threshold
    if max_val >= threshold:
        print("warping!")

    else:
        time.sleep(15)
        # Search for the target image within the game screen
        game_screen = pyautogui.screenshot(
            region=(game_window.left, game_window.top, game_window.width, game_window.height))

        game_screen = np.array(game_screen)
        game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(game_screen, target_gate, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Define a threshold for match detection
        threshold = 0.7

        if max_val >= threshold:
            count = 0
            # Get the coordinates of the matched area
            target_width, target_height = target_gate.shape[:-1]
            target_x, target_y = max_loc

            # Calculate the center of the matched area
            target_center_x = target_x + target_width // 2
            target_center_y = target_y + target_height // 2

            # Simulate a right-click at the center of the matched area with slower mouse movement
            pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                             duration=mouse_move_duration)
            pyautogui.click()
            pyautogui.press("q")
            time.sleep(1)
            pyautogui.press("f2")
            pyautogui.press("f1")
            time.sleep(8)
            pyautogui.press("f1")
            pyautogui.press("d")
        else:
            count += 1
            if count > 10:
                print('end point reached')
                pyautogui.keyDown("ctrl")
                pyautogui.press("s")
                pyautogui.keyUp("ctrl")
                exit()

import cv2
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
    # Add more images as needed
]
orbit_point = cv2.imread('orbit_point.png')
flag = cv2.imread('warping.png')
rat_site = cv2.imread('rat_site.png')
wrap_to_0 = cv2.imread('wrap_to_0.png')
target_structure = cv2.imread('target_structure.png')
dock_button = cv2.imread('dock_button.png')
game_window = gw.getWindowsWithTitle('EVE - Boah Tsasa')[0]

# Define the duration (in seconds) for mouse movements
mouse_move_duration = 0.2  # Adjust as needed for slower or faster movement

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
    #check enemy
    index = 0
    for image_to_check in images_to_check:
        result = cv2.matchTemplate(game_screen, image_to_check, cv2.TM_CCOEFF_NORMED)
        index += 1
        # Define a threshold for match detection (adjust as needed)
        threshold = 0.8
        # if index == 4:
        #     threshold = 0.5
        print(index)
        # Locate the maximum match value in the result
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print(max_val)
        # enemy spotted

        if max_val >= threshold:
            print('target found')
            if index !=4:
                winsound.Beep(1000, 200)
                print("enemy spotted!")
                pyautogui.keyDown("shift")
                pyautogui.press("r")
                pyautogui.keyUp("shift")
                # Capture the game screen

                #return to safe spot
                result = cv2.matchTemplate(game_screen, target_structure, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Define a threshold for match detection
                threshold = 0.8

                if max_val >= threshold:
                    # Get the coordinates of the matched area
                    target_width, target_height = target_structure.shape[:-1]
                    target_X, target_y = max_loc

                    target_center_x = target_X
                    target_center_y = target_y

                    pyautogui.moveTo(target_center_x, target_center_y, duration=mouse_move_duration)

                    pyautogui.click()
                    pyautogui.press("q")
                    time.sleep(5)
                    pyautogui.press("d")
                    exit()
            #change site
            else:
                if idel_count > 20:
                    idel_count = 0
                    print("auto rat done!")
                    pyautogui.keyDown("shift")
                    pyautogui.press("r")
                    pyautogui.keyUp("shift")
                    # Capture the game screen
                    game_screen = pyautogui.screenshot(
                        region=(game_window.left, game_window.top, game_window.width, game_window.height))

                    # Convert to OpenCV format
                    game_screen = np.array(game_screen)
                    game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                    result = cv2.matchTemplate(game_screen, rat_site, cv2.TM_CCOEFF_NORMED)

                    threshold = 0.7

                    # Locate the maximum match value in the result
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    if max_val >= threshold:
                        # Get the coordinates of the matched area
                        target_width, target_height = target_structure.shape[:-1]
                        target_X, target_y = max_loc

                        target_center_x = target_X
                        target_center_y = target_y

                        pyautogui.moveTo(target_center_x, target_center_y, duration=mouse_move_duration)

                        pyautogui.rightClick()

                        # Capture the game screen
                        game_screen = pyautogui.screenshot(
                            region=(game_window.left, game_window.top, game_window.width, game_window.height))

                        # Convert to OpenCV format
                        game_screen = np.array(game_screen)
                        game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                        #wrap to rat site
                        result = cv2.matchTemplate(game_screen, wrap_to_0, cv2.TM_CCOEFF_NORMED)

                        threshold = 0.7

                        # Locate the maximum match value in the result
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)


                        if max_val >= threshold:
                            # Get the coordinates of the matched area
                            target_width, target_height = target_structure.shape[:-1]
                            target_X, target_y = max_loc

                            target_center_x = target_X
                            target_center_y = target_y

                            pyautogui.moveTo(target_center_x, target_center_y, duration=mouse_move_duration)

                            pyautogui.click()
                            time.sleep(8)
                            #check if wrap done
                            wrap_flag = True
                            while wrap_flag == True:
                                time.sleep(1)
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
                                    wrap_flag = False
                                    print('new rat site reach!')
                            pyautogui.keyDown("shift")
                            time.sleep(1)
                            pyautogui.press("f")
                            time.sleep(1)
                            pyautogui.keyUp("shift")
                            time.sleep(1)
                            #start orbiting
                            result = cv2.matchTemplate(game_screen, orbit_point, cv2.TM_CCOEFF_NORMED)

                            threshold = 0.7

                            # Locate the maximum match value in the result
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                            if max_val >= threshold:
                                # Get the coordinates of the matched area
                                target_width, target_height = target_structure.shape[:-1]
                                target_X, target_y = max_loc

                                target_center_x = target_X
                                target_center_y = target_y

                                pyautogui.moveTo(target_center_x, target_center_y, duration=mouse_move_duration)

                                pyautogui.click()
                                pyautogui.press("w")
                                time.sleep(1)
                                pyautogui.press("f1")
                else:
                    idel_count += 1
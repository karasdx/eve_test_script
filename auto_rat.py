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
    cv2.imread('boss_wreck.png'),
    cv2.imread('cap_neutralized.png'),
    cv2.imread('web.png'),
    cv2.imread('disrupted.png'),
    # Add more images as needed
]
unlocked_target_list = [
    cv2.imread('unlocked_target.png'),
    cv2.imread('unlocked_target_1.png'),
    cv2.imread('unlocked_target_2.png'),
]
undock = cv2.imread('undock.png')
open_cargo = cv2.imread('open_cargo.png')
loot_all = cv2.imread('loot_all.png')
# boss_wreck = cv2.imread('boss_wreck(xx).png')
submit = cv2.imread('submit.png')
orbit_point = cv2.imread('orbit_point_new.png')
flag = cv2.imread('warping.png')
rat_site = cv2.imread('rat_site.png')
wrap_to_0 = cv2.imread('wrap_to_10.png')
target_structure = cv2.imread('target_structure(2).png')
dock_button = cv2.imread('dock_button.png')
game_window = gw.getWindowsWithTitle('EVE - Surt Boe Agalder')[0]

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
                winsound.Beep(1000, 200)
                print("enemy spotted!")
                print(index)
                print(max_val)
                pyautogui.moveTo(game_window.left, game_window.top,
                                 duration=mouse_move_duration)

                pyautogui.click()
                pyautogui.keyDown("shift")
                pyautogui.press("r")
                pyautogui.keyUp("shift")
                # Capture the game screen

                # return to safe spot
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

                    pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                     duration=mouse_move_duration)

                    pyautogui.click()
                    pyautogui.press("f1")
                    pyautogui.press("q")
                    time.sleep(12)
                    pyautogui.press("d")
                    # exit()
                    time.sleep(300)

                    # Capture the game screen
                    game_screen = pyautogui.screenshot(
                        region=(game_window.left, game_window.top, game_window.width, game_window.height))

                    # Convert to OpenCV format
                    game_screen = np.array(game_screen)
                    game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                    result = cv2.matchTemplate(game_screen, undock, cv2.TM_CCOEFF_NORMED)
                    threshold = 0.7

                    # Locate the maximum match value in the result
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    if max_val >= threshold:
                        # Get the coordinates of the matched area
                        target_width, target_height = undock.shape[:-1]
                        target_X, target_y = max_loc

                        target_center_x = target_X
                        target_center_y = target_y

                        pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                         duration=mouse_move_duration)

                        pyautogui.click()
                        print("try to undock")

                        time.sleep(14)
                        pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                         duration=mouse_move_duration)

                        pyautogui.click()
                        pyautogui.keyDown("ctrl")
                        pyautogui.press("space")
                        pyautogui.keyUp("ctrl")
                        pyautogui.keyDown("shift")
                        pyautogui.press("f")
                        pyautogui.keyUp("shift")
                        pyautogui.press("f2")
                        pyautogui.press("f3")
                        pyautogui.press("f4")
                        idel_count = 55
            #web / neutralized
            elif index == 7 or index == 8 or index == 9:
                print(index)
                game_screen = pyautogui.screenshot(
                    region=(game_window.left, game_window.top, game_window.width, game_window.height))
                # Convert to OpenCV format
                game_screen = np.array(game_screen)
                game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)

                #
                pyautogui.moveTo(game_window.left, game_window.top,
                                 duration=mouse_move_duration)

                pyautogui.click()
                result = cv2.matchTemplate(game_screen, image_to_check, cv2.TM_CCOEFF_NORMED)
                threshold = 0.7

                # Locate the maximum match value in the result
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val >= threshold:
                    # Get the coordinates of the matched area
                    target_width, target_height = image_to_check.shape[:-1]
                    target_X, target_y = max_loc

                    target_center_x = target_X + target_width / 2
                    target_center_y = target_y + target_height / 2

                    pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                     duration=mouse_move_duration)

                    pyautogui.keyDown("ctrl")
                    pyautogui.click()
                    pyautogui.keyUp("ctrl")

                    time.sleep(10)
                    pyautogui.press("f")
                    print('drone engage locked target')

            elif index == 6:
                if boss_flag == 0:
                    boss_flag = 1
                    print('boss wreck found')
                    pyautogui.moveTo(game_window.left, game_window.top,
                                     duration=mouse_move_duration)

                    pyautogui.click()
                    pyautogui.keyDown("ctrl")
                    pyautogui.press("b")
                    pyautogui.keyUp("ctrl")
                    pyautogui.press("enter")
            # change site
            else:
                if idel_count > 40:
                    boss_flag = 0
                    print('drone idle')
                    # Capture the game screen
                    game_screen = pyautogui.screenshot(
                        region=(game_window.left, game_window.top, game_window.width, game_window.height))
                    # Convert to OpenCV format
                    game_screen = np.array(game_screen)
                    game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                    unlocked_target_flag = 0
                    for unlocked_target in unlocked_target_list:
                        result = cv2.matchTemplate(game_screen, unlocked_target, cv2.TM_CCOEFF_NORMED)
                        threshold = 0.7

                        # Locate the maximum match value in the result
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        if max_val >= threshold:
                            # Get the coordinates of the matched area
                            target_width, target_height = unlocked_target.shape[:-1]
                            target_X, target_y = max_loc

                            target_center_x = target_X + target_width / 2
                            target_center_y = target_y + target_height / 2

                            pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                             duration=mouse_move_duration)

                            pyautogui.keyDown("ctrl")
                            pyautogui.click()
                            pyautogui.keyUp("ctrl")

                            time.sleep(10)
                            pyautogui.press("f")
                            print('drone engage locked target')
                            idel_count = 0
                            unlocked_target_flag = 1

                    if unlocked_target_flag == 0:
                        idel_count = 0
                        print("auto rat done!")
                        pyautogui.moveTo(game_window.left, game_window.top,
                                         duration=mouse_move_duration)

                        pyautogui.click()
                        pyautogui.keyDown("shift")
                        pyautogui.press("r")
                        pyautogui.keyUp("shift")

                        # Capture the game screen
                        game_screen = pyautogui.screenshot(
                            region=(game_window.left, game_window.top, game_window.width, game_window.height))

                        # Convert to OpenCV format
                        game_screen = np.array(game_screen)
                        game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)

                        # loot boss

                        # result = cv2.matchTemplate(game_screen, submit, cv2.TM_CCOEFF_NORMED)
                        # threshold = 0.55
                        #
                        # # Locate the maximum match value in the result
                        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        # print(max_val)
                        # if max_val >= threshold:
                        #
                        #     print('save location')
                        #     # Get the coordinates of the matched area
                        #     target_width, target_height = target_structure.shape[:-1]
                        #     target_X, target_y = max_loc
                        #
                        #     target_center_x = target_X
                        #     target_center_y = target_y
                        #
                        #     pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top, duration=mouse_move_duration)
                        #
                        #     pyautogui.click()
                        #     time.sleep(50)

                        # take the loot
                        # result = cv2.matchTemplate(game_screen, loot_all, cv2.TM_CCOEFF_NORMED)
                        # threshold = 0.7
                        #
                        # # Locate the maximum match value in the result
                        # min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        # if max_val >= threshold:
                        #     # Get the coordinates of the matched area
                        #     target_width, target_height = target_structure.shape[:-1]
                        #     target_X, target_y = max_loc
                        #
                        #     target_center_x = target_X
                        #     target_center_y = target_y
                        #
                        #     pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top, duration=mouse_move_duration)
                        #
                        #     pyautogui.click()

                        # change rat site
                        print('changing rat site')
                        result = cv2.matchTemplate(game_screen, rat_site, cv2.TM_CCOEFF_NORMED)
                        threshold = 0.8

                        # Locate the maximum match value in the result
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        if max_val >= threshold:
                            # Get the coordinates of the matched area
                            target_width, target_height = target_structure.shape[:-1]
                            target_X, target_y = max_loc

                            target_center_x = target_X
                            target_center_y = target_y

                            pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                             duration=mouse_move_duration)

                            pyautogui.rightClick()
                            # Capture the game screen
                            game_screen = pyautogui.screenshot(
                                region=(game_window.left, game_window.top, game_window.width, game_window.height))

                            # Convert to OpenCV format
                            game_screen = np.array(game_screen)
                            game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                            # wrap to rat site
                            result = cv2.matchTemplate(game_screen, wrap_to_0, cv2.TM_CCOEFF_NORMED)

                            threshold = 0.65

                            # Locate the maximum match value in the result
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                            if max_val >= threshold:
                                # Get the coordinates of the matched area
                                target_width, target_height = target_structure.shape[:-1]
                                target_X, target_y = max_loc

                                target_center_x = target_X
                                target_center_y = target_y

                                pyautogui.moveTo(target_center_x + game_window.left, target_center_y + game_window.top,
                                                 duration=mouse_move_duration)
                                time.sleep(15)
                                pyautogui.click()
                                time.sleep(10)
                                # check if wrap done
                                wrap_flag = True
                                while wrap_flag == True:
                                    time.sleep(5)
                                    # Capture the game screen
                                    game_screen = pyautogui.screenshot(
                                        region=(
                                        game_window.left, game_window.top, game_window.width, game_window.height))

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

                                # start orbiting
                                result = cv2.matchTemplate(game_screen, orbit_point, cv2.TM_CCOEFF_NORMED)

                                threshold = 0.85

                                # Locate the maximum match value in the result
                                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                                if max_val >= threshold:
                                    print("start orbiting")
                                    # Get the coordinates of the matched area
                                    target_width, target_height = target_structure.shape[:-1]
                                    target_X, target_y = max_loc

                                    target_center_x = target_X + target_width / 2
                                    target_center_y = target_y + target_height / 2

                                    pyautogui.moveTo(target_center_x + game_window.left,
                                                     target_center_y + game_window.top, duration=mouse_move_duration)

                                    pyautogui.click()
                                    pyautogui.press("w")
                                    pyautogui.press("f1")
                                    pyautogui.keyDown("shift")
                                    pyautogui.press("f")
                                    pyautogui.keyUp("shift")
                                else:
                                    # return to safe spot
                                    print('fail to orbit,return to station')
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

                                        pyautogui.moveTo(target_center_x + game_window.left,
                                                         target_center_y + game_window.top,
                                                         duration=mouse_move_duration)

                                        pyautogui.click()
                                        pyautogui.press("q")
                                        time.sleep(13)
                                        pyautogui.press("d")
                                        # exit()
                                        time.sleep(60)

                                        # Capture the game screen
                                        game_screen = pyautogui.screenshot(
                                            region=(
                                            game_window.left, game_window.top, game_window.width, game_window.height))

                                        # Convert to OpenCV format
                                        game_screen = np.array(game_screen)
                                        game_screen = cv2.cvtColor(game_screen, cv2.COLOR_RGB2BGR)
                                        result = cv2.matchTemplate(game_screen, undock, cv2.TM_CCOEFF_NORMED)
                                        threshold = 0.7

                                        # Locate the maximum match value in the result
                                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                                        if max_val >= threshold:
                                            # Get the coordinates of the matched area
                                            target_width, target_height = target_structure.shape[:-1]
                                            target_X, target_y = max_loc

                                            target_center_x = target_X
                                            target_center_y = target_y

                                            pyautogui.moveTo(target_center_x + game_window.left,
                                                             target_center_y + game_window.top,
                                                             duration=mouse_move_duration)

                                            pyautogui.click()
                                            print("try to undock")

                                            time.sleep(20)
                                            pyautogui.moveTo(target_center_x + game_window.left,
                                                             target_center_y + game_window.top,
                                                             duration=mouse_move_duration)

                                            pyautogui.click()
                                            pyautogui.keyDown("ctrl")
                                            pyautogui.press("space")
                                            pyautogui.keyUp("ctrl")
                                            pyautogui.keyDown("shift")
                                            pyautogui.press("f")
                                            pyautogui.keyUp("shift")
                                            pyautogui.press("f2")
                                            pyautogui.press("f3")
                                            pyautogui.press("f4")
                                            idel_count = 35
                            else:
                                print("fail to change site.")
                                time.sleep(5)
                                pyautogui.keyDown("shift")
                                pyautogui.press("r")
                                pyautogui.keyUp("shift")
                        else:
                            print("fail to find a new site")

                else:
                    idel_count += 1
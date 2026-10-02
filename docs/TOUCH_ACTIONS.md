# Touch actions

Landscape touch actions in `android/host/app/src/main/java/ui/activity/TouchControls.java`.
They inject the OpenMW 0.51 default bindings only. Physics, gait, and the run control are unchanged.

The closed overlay is a move stick and four buttons. Thirteen controls are not drawn at once. MORE opens a two-column tray and CLOSE hides it again. The phone shots of 0.10 showed the old thirteen buttons covering the journal, the inventory, and the right-hand look surface.

## Closed overlay

The left 40% of the screen is the move stick when the finger is not on a button. The rest of the empty screen looks: a drag there calls `SDLActivity.sendRelativeMouseMotion`. The hint "Drag empty space to look" sits above the stick. The engine name label stays at the top center.

The right edge holds four squares, bottom to top: USE, JUMP, ATK, MORE. USE holds Space (`A_Activate`). JUMP holds E (`A_Jump`). ATK holds `SDL_BUTTON_LEFT` (`A_Use`) and is highlighted while that button is down. MORE toggles the tray and reads CLOSE while the tray is open. USE sits 13% of the screen height above the bottom edge so the engine compass stays visible. That gap is only a layout choice.

Each square's edge is 10.5% of the shorter screen side, capped at 14% of the height, and then raised to 48px if that is still smaller. The gap is at least 6px and otherwise 16% of the edge. `tests/test_touch_layout.py` checks this cluster on 1920×1080, 2400×1080, 1280×720, and 960×540.

## Tray

MORE opens ten squares in two columns, row-major from the top: RUN, SNEAK, WEAPON, MAGIC, INV, JOURNAL, WAIT, POV, MENU, EXIT. The bottom row lines up with USE. The columns sit to the left of the four primary buttons.

RUN toggles a hold of Left Shift (`A_Run`). It starts on. The label reads WALK while running and RUN while walking. SNEAK toggles a hold of Left Ctrl (`A_Sneak`). The label stays SNEAK and the square is highlighted while sneak is on. This is not the engine `toggleSneak` setting. RUN and SNEAK leave the tray open.

Every other tray control, and USE, JUMP, and ATK, close the tray on the press. EXIT still calls `release()` and finishes the activity. MENU is Escape and does not replace EXIT.

| Control | OpenMW action | SDL binding | Gesture |
| --- | --- | --- | --- |
| USE | `A_Activate` | Space | Hold. Primary, bottom. |
| JUMP | `A_Jump` | E | Hold. Primary. |
| ATK | `A_Use` (10) | `SDL_BUTTON_LEFT` (1) | Hold. Highlighted while held. |
| MORE | none | none | Toggles the tray. |
| RUN | `A_Run` (17) | Left Shift | Toggle. Label WALK while running. |
| SNEAK | `A_Sneak` (24) | Left Ctrl | Toggle hold. Highlighted while on. |
| WEAPON | `A_ToggleWeapon` (28) | F | Tap. |
| MAGIC | `A_ToggleSpell` (29) | R | Tap. |
| INV | `A_Inventory` (3) | `SDL_BUTTON_RIGHT` (3) | Tap. |
| MENU | `A_GameMenu` (0) | Escape | Tap. |
| JOURNAL | `A_Journal` (14) | J | Tap. |
| WAIT | `A_Rest` (13) | T | Tap. |
| POV | `A_TogglePOV` (30) | Tab | Tap. Holding it keeps Tab down, which OpenMW uses for the temporary preview camera. |
| EXIT | none | none | Finishes the activity. |

`A_AutoMove` (Q) has no overlay button. OpenMW fires the menu and stance actions on the press. Attack stays active only while left mouse is down.

## Pointer and focus

Mouse buttons use `org.libsdl.app.SDLActivity.sendMouseButton(int state, int button)`: state `1` presses and `0` releases. The button argument is the SDL id, `SDL_BUTTON_LEFT` (1) or `SDL_BUTTON_RIGHT` (3). `onNativeMouse` is not used; that call also injects pointer motion and tracks one Android button-state mask. The finger that pressed a key or a mouse button is the only one that can release it. Buttons are hit-tested before the stick and the look surface, so a tray square does not also look.

`release()` drops held keys, Shift, Ctrl, and mouse buttons. It does not clear the run, sneak, or tray state. `onPause` already calls it. `syncRun()` sends the Shift and Ctrl holds again when the window focus returns. `GameActivity` calls both.

# Touch actions

Landscape touch actions in `android/host/app/src/main/java/ui/activity/TouchControls.java`.
They inject the OpenMW 0.51 default bindings only. Physics, gait, and the run control are unchanged.

USE, JUMP, EXIT, and run stay where they were. USE holds Space (`A_Activate`). JUMP holds E (`A_Jump`). EXIT finishes the activity. Run toggles a hold of Left Shift (`A_Run`), starts on, and shows WALK while running and RUN while walking. `A_AutoMove` (Q) has no overlay button.

Mouse buttons use `org.libsdl.app.SDLActivity.sendMouseButton(int state, int button)`: state `1` presses and `0` releases. The button argument is the SDL id, `SDL_BUTTON_LEFT` (1) or `SDL_BUTTON_RIGHT` (3). `onNativeMouse` is not used; that call also injects pointer motion and tracks one Android button-state mask. The finger that pressed a mouse button is the only one that can release it. Keys use the same one-owner rule. `release()` drops held keys and mouse buttons; `onPause` already calls it. Run and sneak holds are sent again from `syncRun()` when the window focus returns.

Buttons are hit-tested before the move stick (left 40%) and look (everything else), so a tap on a button does not also look. Every new key button is the same size as USE: 10.5% of width by 11% of height. ATK is wider and as tall as the JUMP+USE stack. USE, JUMP, and ATK sit 13% of the screen height above the bottom edge so the engine minimap is not covered. The look hint is above the move stick, not at the top center, because the engine name label occupies that spot. The new cluster is below RUN and EXIT and does not cover the stick. Nothing from the list below was dropped.

Upper row, left to right: POV, MAGIC, WAIT, MENU. Lower row, left to right: JOURNAL, WEAPON, SNEAK, INV. ATK sits under WEAPON and SNEAK, immediately left of JUMP and USE.

| Control | OpenMW action | SDL binding | Gesture |
| --- | --- | --- | --- |
| ATK | `A_Use` (10) | `SDL_BUTTON_LEFT` (1) | Hold while the finger is down. Highlighted while held. |
| SNEAK | `A_Sneak` (24) | `SDL_SCANCODE_LCTRL` | Toggle. Holds Left Ctrl while on, same pattern as run. Label stays SNEAK and the button is highlighted while on. This is not the engine `toggleSneak` setting. |
| WEAPON | `A_ToggleWeapon` (28) | `SDL_SCANCODE_F` | Tap. Key down on finger down, up on finger up. |
| MAGIC | `A_ToggleSpell` (29) | `SDL_SCANCODE_R` | Tap. Key down on finger down, up on finger up. |
| INV | `A_Inventory` (3) | `SDL_BUTTON_RIGHT` (3) | Tap. Button down on finger down, up on finger up. |
| MENU | `A_GameMenu` (0) | `SDL_SCANCODE_ESCAPE` | Tap. Key down on finger down, up on finger up. Does not replace EXIT. |
| JOURNAL | `A_Journal` (14) | `SDL_SCANCODE_J` | Tap. Key down on finger down, up on finger up. |
| WAIT | `A_Rest` (13) | `SDL_SCANCODE_T` | Tap. Key down on finger down, up on finger up. |
| POV | `A_TogglePOV` (30) | `SDL_SCANCODE_TAB` | Tap. Key down on finger down, up on finger up. Holding it keeps Tab down, which OpenMW uses for the temporary preview camera. |

OpenMW fires these menu and stance actions on the press. Attack stays active only while left mouse is down.

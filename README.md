Puppetstrings


Plug in Controller
- In the 3d viewport N panel, press the "Enable Controller" it should say "Controller Running"

Start Button: Start the play control
Back Button:
    When Playing, stops playback
    When Stopped, goes to start frame

Arm recording without punch to record at all times.

Create markers in the timeline and choose them for punch points, pre-roll is optional
When punch is enabled (click the arm circle next to punch in) it will always record in punch area.
When no punch points are selected, recording will happen at all frames.

Prevent Looping Animation: When the playback gets to the final frame, playback is cancelled rather than looping

Auto-Simplify: Enable/Disable the render settings "simplify" panel on recording or recording/playback.

Controller FPS: How often the controller is polled

Keyframe Interval: How often to record keyframes

Smoothing ms: Length of Time for Smoothing Calculation on Axis & Trigger Controls

Debounce Time ms: Length of time to prevent jittery button presses

Mapping Set: A grouping of key mappings, you will need at least one, if it is unchecked the mapping has no effect on the recording

Button Mappings: A specific key mapping. if it is unchecked the mapping has no effect on the recording
    Checkbox: Enable this mapping for processing
    Eye: Show or hide mapping details
    Button: Axes or Button to map to
    Object: Object to get mapping for
    Mapping Type: What kind of property is being mapped
        Location / Rotation / Scale: An Axis to Map is Offered
        Shape Key: A listing of shape keys on the object is offered
        Modifier/Data Path: These are still in development for ease of use
    Operation:
        Direct Value: Take the value directly from the controller
        Curve: Map the controller value to a curve. Use the curve tools to extend the clipping
        Inverted Button: rather than 0=Off 1=On, it is 1=Off, 0=On
        Inverted Axis: rather than -1 to 1 it is 1 to -1
        Assignment Expression: using the word 'value' write an expression starting with "=" in valid python
            e.g.     = value * 2
        Easing: An easing method to be applied at the controller level before value is returned to the script


TODO:
    Make a way to set smoothing per button

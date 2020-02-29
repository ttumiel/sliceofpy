G2{units}
G90                     ;absolute positioning
M82                     ;set extruder to absolute mode
M107                    ;start with the fan off
G28 X0 Y0               ;move X/Y to min endstops
G28 Z0                  ;move Z to min endstops
M140 S{bed_temperature}             ; start heating the bed to 50 degrees Celsius
M190 S{bed_temperature}             ; wait until the bed reaches 50 degrees before continuing
M104 S{temperature}             ;start heating T0 to 190 degrees Celsius
M109 S{temperature}             ;wait for T0 to reach 190 degrees before continuing with any other commands
G1 Z15.0 F{feedrate}            ;move the platform down 15mm
G92 E0                  ;zero the extruded length
G1 F200 E6              ;extrude 6 mm of feed stock
G92 E0                  ;zero the extruded length again
G1 F{feedrate}                  ;set feedrate
M117 Printing...        ;Put printing message on LCD screen

import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/gantry_lattepanda/Ryan_ws/gantry_lidars/install/gantry_lidars'

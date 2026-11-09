import numpy as np
END = 17.2                     # new total duration (s)
A_NEW = [0, 2.67, 6.502, 8.406, 9.206, 10.333, 13.514, 16.181]   # song beats
A_SRC = [0, 2.733, 6.3, 8.2, 9.0, 11.0, 14.167, 16.834]          # footage events
def src_of_new(t): return float(np.interp(t, A_NEW, A_SRC)) if t <= A_NEW[-1] else A_SRC[-1]
def old_of_src(s):
    if s < 9: return s
    if s < 10.2: return 9 + (s - 9) / 2
    return s - 0.6
def old_of_new(t):
    if t > A_NEW[-1]: return old_of_src(A_SRC[-1]) + (t - A_NEW[-1])
    return old_of_src(src_of_new(t))
def new_of_old(o):
    s_end_old = old_of_src(A_SRC[-1])
    if o > s_end_old: return A_NEW[-1] + (o - s_end_old)
    s = o if o < 9 else (9 + (o - 9) * 2 if o < 9.6 else o + 0.6)
    return float(np.interp(s, A_SRC, A_NEW))
OLD_END = old_of_new(END)
# text start overrides, in NEW (song) time, snapped to beats / 8ths / 16ths
OVR = {'h1': 0.14, 'h2': 0.766, 'h3': 1.08, 'b1': 1.393, 'b2': 2.02,
       'r2': 2.67, 'r1': 2.98, 'r3': 3.297, 'f1': 10.65, 'f2': 10.96,
       'l1': 12.237, 'l2': 12.396, 'l3': 12.555, 'l4': 12.714,
       'k1': 14.141, 'k2': 14.466, 'k3': 14.791, 'k4': 15.116, 'k5': 15.441, 'k6': 15.755}
OUT_OVR = {'h1': 1.36, 'h2': 1.36, 'h3': 1.36, 'b1': 2.55, 'b2': 2.55}
BEAT_PUNCH = [3.947, 5.224, 9.033, 11.61, 14.141, 14.791, 15.441, 16.068, 16.695]  # downbeats/beats -> small zoom bump

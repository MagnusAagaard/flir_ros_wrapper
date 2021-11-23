import numpy as np

def convert16bit_to_8bit(arr):
    '''
    Returns numpy array with dtype np.uint8, slicing np.uint16 values into two values.
    '''
    a = arr.flatten()
    converted_arr = np.zeros((a.shape[0]*2), dtype=np.uint8)
    for i, x in enumerate(a):
        msb = (x >> 8) & 0xff
        lsb = x & 0xff
        converted_arr[i*2] = msb
        converted_arr[i*2+1] = lsb
    return converted_arr
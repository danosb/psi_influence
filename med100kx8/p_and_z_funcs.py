import math


# Returns the trial_p value from the normalized weighted surprival value (nwsv) from 21 sub-trials with n = 31; The input range is -1 to +1 and the default output range is approximately: 0.0001 < p < 0.9999.
def trialp_from_nwsv(nwsv, influence_type):

    if nwsv < -0.95:
        x = -0.95
    elif nwsv > 0.95:
        x = 0.95
    else:
        x = nwsv

    x = -abs(nwsv)
    xx = 1.3671649364575*x \
    + 0.043433149991109*x**2 \
    - 2.16454907883120*x**3 \
    - 1.16398609859974*x**4 \
    - 15.9478516592348*x**5 \
    - 86.4404062808434*x**6 \
    - 201.9161410163*x**7 \
    - 265.2908149166*x**8 \
    - 205.91445301453*x**9 \
    - 88.495808283824*x**10 \
    - 16.271768076703*x**11 \

    if nwsv < 0:
        trial_p = 0.5 + xx
    if nwsv > 0:
        trial_p = 0.5 - xx

    if influence_type == 'Produce more 1s':
        trial_p = 1 - trial_p

    if nwsv < 0 and influence_type == 'Alternate between producing more 0s and more 1s':
        trial_p = 2 * trial_p
    if nwsv > 0 and influence_type == 'Alternate between producing more 0s and more 1s':    
        trial_p = 2 * (1 - trial_p)

    return trial_p


# Accepts trial_p (the cumulative uniform distribution value) and returns the corresponding z-score
def invnorm(trial_p):
    trial_z = 0

    p0 = -0.322232431088
    p1 = -1.0
    p2 = -0.342242088547
    p3 = -0.0204231210245
    p4 = -0.453642210148e-4
    q0 = 0.099348462606
    q1 = 0.588581570495
    q2 = 0.531103462366
    q3 = 0.10353775285
    q4 = 0.38560700634e-2

    if trial_p < 0.5:
        pp = trial_p
    else:
        pp = 1.0 - trial_p

    y = math.sqrt(math.log(1 / (pp ** 2)))
 
    trial_z = y + ((((y * p4 + p3) * y + p2) * y + p1) * y + p0) / ((((y * q4 + q3) * y + q2) * y + q1) * y + q0)

    if trial_p < 0.5:
        trial_z = -trial_z
    
    return trial_z


# Accepts window_z, returns cumulative normal distribution p value for window (window_p). Accuracy better than 1% to z=±7.5; .05% to z=±4.
def cdf(window_z):
    c1 = 2.506628275
    c2 = 0.31938153
    c3 = -0.356563782
    c4 = 1.781477937
    c5 = -1.821255978
    c6 = 1.330274429
    c7 = 0.2316419

    if window_z >= 0:
        w = 1
    else:
        w = -1

    t = 1.0 + c7 * w * window_z
    y = 1.0 / t
    window_p = 0.5 + w * (0.5 - (c2 + (c6 + c5 * t + c4 * t ** 2 + c3 * t ** 3) / t ** 4) / (c1 * math.exp(0.5 * window_z ** 2) * t))
    
    # If the window_p value is less than 0.5, double the p value and that is the windowp value for a result of -1
    # If the window_p value is greater than (or =) 0.5, the windowp value is 2(1-p) for a result of +1.
    if window_p < 0.5:
        window_p = window_p * 2
    else:
        window_p = 2 * (1 - window_p)

    return window_p
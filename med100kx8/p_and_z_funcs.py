import math


# Returns the trial_p value from the normalized weighted surprival value (nwsv) from 21 sub-trials with n = 31; The input range is -1 to +1 and the default output range is approximately: 0.0001 < p < 0.9999.
# Note, this is a two-tailed test, meaning if the nwsv is negative, take the p returned by the function above. If the nwsv is positive, the actual p value is 1-p returned by the function. If you were using the trial by itself, each of the p values would be doubled for the two-tailed statistic. For combining into a windowp, take the p values returned by the function without subtracting from 1 or doubling them.
def trialp_from_nwsv(nwsv):
    if nwsv < -0.916:
        x = -0.916
    elif nwsv > 0.916:
        x = 0.916
    else:
        x = nwsv

    trial_p = (
        0.4999447235559293
        + 1.2528465672038636 * x
        + 0.0023748498254079604 * x ** 2
        - 1.8238870199248776 * x ** 3
        - 0.01775000187777237 * x ** 4
        + 1.9836743245635038 * x ** 5
        + 0.05445147471824477 * x ** 6
        - 1.3540283379808826 * x ** 7
        - 0.08206132973167951 * x ** 8
        + 0.5389043846181366 * x ** 9
        + 0.060502652558113074 * x ** 10
        - 0.09752931591747523 * x ** 11
        - 0.01746939645456147 * x ** 12
    )

    # Open question if doing two-tailed:
    # "two-tailed test, meaning if the nwtv is negative, take the p returned by the function above. If the nwtv is positive, the actual p value is 1-p returned by the function. If you were using the trial by itself (which I know is not your plan), each of the p values would be doubled for the two-tailed statistic. For combining into a windowp, take the p values returned by the function without subtracting from 1 or doubling them.
    # .. so we perform operations or we don't?

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
    
    # Uncomment if two-tailed
    # If the window_p value is less than 0.5, double the p value and that is the windowp value for a result of -1
    # If the window_p value is greater than (or =) 0.5, the windowp value is 2(1-p) for a result of +1.
    # if window_p < 0.5:
    #     window_p = window_p * 2
    # else:
    # window_p = 2 * (1 - window_p)

    return window_p
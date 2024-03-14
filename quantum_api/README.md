Uses an API to obtain quantum random numbers. As with other programs in this folder group, these random numbers are then used to evaluate the effect of intention on influencing their outcomes. The goal is to use intention to make the numbers less random, and to be able to measure and portay the effects of this influence using computer code.

For this subfolder we do not use a hardware-based random number generator (RNG) but instead use an API provided by [Australian National University Quantum Numbers (AQN)](https://quantumnumbers.anu.edu.au/). The random numbers are generated in real-time in our lab by measuring the quantum fluctuations of the vacuum. The vacuum is described very differently in quantum physics and classical physics. In classical physics, a vacuum is considered as a space that is empty, devoid of matter or photons. Quantum physics however says that same space resembles a sea of virtual particles continuoisly appearing and disappearing. This is a prediction of quantum mechanics and can be measured and even sometimes utilised, such as in this service. By carefully measuring these vacuum fluctuations, we are able to generate ultra-high bandwidth random numbers. 

There are two files in this folder:

In **main2.py** there are two different sets of numbers obtained from the quantum API here; 1) Those obtained a head of time and the results are observed. 2) Those obtained in real-time during a trial. The idea here is to enable replication of Helmut Schmidt's successful experiment in which he concluded that both real-time and unobserved results could still be influenced, while observed results could not.

A series of images is shown to the user in sequence during the experiment. The image instructs the user to try to influence the numbers to do one of three things:
  1. Influence the results to have more positive numbers
  2. Influence the results to have more negative numbers
  3. Do nothing - attempt to exert no influence.

A short amount of time elapses while the image is displayed on the screen and then a sound is played for the user to indicate whether the outcome (more positive or more negative) matched the instruction. (e.g. if the image instructs more positive numbers, and more positive numbers were produced for that trial, then a confirmatory DING is played, rather than a negatory BUZZ).

The user does not know if given image is pulling numbers from the quantum API in real-time or whether the trial is using pre-observed numbers. Therefore, they do not actually know if a given image/trial is theoretically open to influence (thus negating potential bias in which the participant may not try to influence results in the same way if they know a particular result has already been observed).

All data and results are stored to a local database. At the end, the user is presented with an overall outcome showing the probability of randomness for each set of numbers (pre-observed and real-time).
In theory, we'd expect the real-time number set to be open to influence while the pre-observed group is not.

**main3.py** uses a basically similar approach as described above, but it uses only text rather than images, and also it only suggests to influence in one direction (rather than having varying instructions to influence in positive/negative directions).


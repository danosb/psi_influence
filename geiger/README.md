This code is written to use the [RNG-01A Random Number Generator](https://www.imagesco.com/psi/random-number-generator.html). As with other programs in this folder group, these random numbers are then used to evaluate the effect of intention on influencing their outcomes. The goal is to use intention to make the numbers less random, and to be able to measure and portay the effects of this influence using computer code.

The RNG-01 Random Number Generator is a lab quality instrument. It uses the immutable randomness of radioactivity decay to generate random numbers. Quantum mechanics states that the nuclear decay of atoms, are fundamentally random and cannot be predicted. Our device has a mini-Geiger counter that detects background radiation. The detection of a radioactive particle being a random event use to initiate the generation of a random number. The output of the built-in Geiger counter is monitored by a PIC microcontroller. The PIC microcontroller is rotating numbers inside a register at approximately 1,000,000 numbers a second. When a radioactive particle (Random Event) is detected the microcontroller stops the rotation of numbers, reads the current number in the register and produces a random number. 

The Random Number Generator (RNG-01A) will produce approximately one to three random numbers every minute from background radiation. However, a small piece of Uranium can be purchased online completely legaly (at least in the US) placed next to the RNG, significantly increasing the frequently of numbers produced due to increased radioactive decay (take basic safety precuations here, of course).

In this folder there are two files:

* **rng_influence_geiger_realtime_only.py** -  Uses Geiger-generated numbers generated in real-time. All results are combined into a single probability that probability controls a line chart and also the pitch of an audio tone, giving real-time feedback. The line, and the audio tone, go up or down in real-time based on calculated probability of results being random. If you are influencing the results with your intention, you'd expect to see/hear the line and the audio tone both rise.

* **rng_influence_geiger.py** - This is a more sophisticated version of the above. Rather than only capturing and reacting to data in real-time, it captures three different sets of results:
  1. **Pre-run data - Unobserved** - Numbers are captured from the RNG and stored, the results are stored in a local database but NOT observed.
  2. **Pre-run data - Observed** - Numbers are captured from the RNG and stored, the results are stored in a local database and ARE observed..=
  3. **Real-time data** - Numbers are captured in real-time.
 
Then, all three sets of data are combined to create the line-chart and audio tones presented to the user - one set occuring in real-time is mixed with the other two (one observed and one unobserved) that were captured ahead of time.

The idea here is to enable replication of [Helmut Schmidt's successful experiment](https://www.fourmilab.ch/rpkp/retro.html) in which he concluded that both real-time and unobserved results could still be influenced, while observed results could not.

Since all three sets are combined into the same output when shown to the user, this is effectively a blind study that prevents the user from having knowledge about which individual results belong to which set (thus negating potential bias in which the participant may not try to influence results in the same way if they know a particular result has already been observed).




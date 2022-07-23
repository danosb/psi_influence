# quantum_influence
An experiment to measure impact of intention on quantum random numbers

## Summary

Previous experiments, mostly done by Helmut Schmidt in the 70s and 80s, suggest that prior to being observed random numbers can be influenced by intention. Once the random numbers have been observed they no longer appear to be open to influence. This is important because it is the strongest evidence indicating that the observer plays an active role in the quantum mechanical process of collapsing a wave-function from all probable outcomes (existing in a superposition) into a single actual outcome (eigenstate). While an area of active debate with no direct experimental evidence, such a suggestion is in stark contrast to the commonly accepted viewpoint amongst quantum physcists, who assert that the observer plays no role and instead the act of measurement itself, or more specifcailly interaction with a measuring device, is what causes wave-function collapse.

This debate is incredibly important because it deals with the point at which our world stops being a cloud of possibilities and becomes an actual physical thing. It's a core question underpinning our understanding of reality, and likely represents the missing link between what are currently our two completely different and allegedly unrelated sets of physics (quantum vs classical). 

As such, I believe this experiment is the strongest indicator we have to point us towards the role played by consciousness in formation of our physical world, a connection most commonly believed to not exist. 


## Experiment Details

A number of variations on Helmmut Schmidt's original experiments can be seen here: https://www.fourmilab.ch/rpkp/.

Here, we aim to improve on these experiments by using quantum random numbers to drive all aspects of the experiment.

To retreive these quantum random numbers we'll use an API offered by Australian National University Quantum Numbers (AQN) https://quantumnumbers.anu.edu.au/.

Each experimental trial consists of multiple runs, and each run includes four distinct sets of quantum nummbers. For each of the four sets we'll use sets of 1000 integers between 0 and 255. We will then sum all numbers in each set. The four sets in each runs are used in the following manner:

Set 1: Determines whether a dummy set (Set #3) or real set (Set #4) gets displayed to user prior to trial.
  - To do so we'll sum the 1000 numbers in Set 1 and do modulo 7. If modulo 7 is less than 5 then the preview will show dummy numbers (Set #3), else show the real results (Set $4), which will occur 2/7 of the time. If real numbers are previewed prior to the actual trial then we expect the numbers to NOT be open to intentional influence. We want to test this condition.

Set 2: Determines which action to direct the user to take during the actual trial. 
  - Again, we will sum and take modulo 7 on Set 2.
		- If <3 then direct user to influence sum to be positive (green)
		- If >3 then direct user to influence sum to be negative (red)
		- If =3 then direct user to exert no influence

Set 3: Is a dummy set that is not used during the experiment.
  - Set 3 is often displayed during the preview phase, as dictated by Set 1. We don't want the user to know whether they are previewing real or dummy results, so we'll show Set 3 rather than showing nothing.

Set 4: Is the set that is always shown to the user during the actual experiment trials. 
  - Depending on Set 1, Set 4 may or may not have been exposed in the preview.

## Experiment Experience

First the user is flahsed a number of images and instructed that these not need be remembered, just observed.

Next, the runs will be begin. For each run we will sum up 1000 random numbers. The user is instructed to do one of the following:
1. Influence the sum to be positive
2. Influence the sum to be negative
3. Make no attempt to influence

After each run a sound will play indicating whether the user was successful.

All data is logged for later analysis.


## Setup

Setup is very straightforward. First you'll need to update the API key in line 82 of main.py. These are available at https://quantumnumbers.anu.edu.au/api-key. They provide 100 free calls per month. From there simply install any required packages, download included assets (e.g. images, sound), and run the Python file.

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

Each experimental trial consists of multiple runs, and each run includes two distinct sets of quantum nummbers. The two sets in each run are used in the following manner:

Set 1: Determines which of the six groups set #2 will fall into. We have six possible groups.
  - Unobserved, influence to even
  - Unobserved, influence to odd
  - Unobserved, no influence
  - Observed, influence to even
  - Observed, influence to odd
  - Observed, no influence
  
  - To do so we'll get a set of 1002 randomm numbers, sum them, and take modulo 6. 
  - 

Set 2: Is the set of numbers that may be influenced.

  - We'll get a set of 1000 random numbers, sum them, and take modulo 2 to determine whether the sum is even or odd.

In the event that Set #1 dictates we NOT show results during the preview (in other words, results are Unobserved), then we will use a psuedo-random number generator to show dummy results so that the user cannot tell whether real or fake results are being shown.


## Experiment Experience

First the user is flahsed a number of images and instructed that these not need be remembered, just observed.

Next, the runs will be begin. For each run we will sum up 1000 random numbers. The user is instructed to do one of the following:
1. Influence the sum to be positive
2. Influence the sum to be negative
3. Make no attempt to influence

After each run a sound will play indicating whether the user was successful.

Stats are displayed at the end.


## Setup

Setup is very straightforward. First you'll need to update the API key in line 82 of main.py. These are available at https://quantumnumbers.anu.edu.au/api-key. They provide 100 free calls per month. From there simply install any required packages, download included assets (e.g. images, sound), and run the Python file.

## 1
I will present a paper review today. The paper, published in 2016, reports the first direct observation of gravitational waves.

## 2
Let me start with the background. Gravitational waves were predicted by Einstein in 1916 as a consequence of general relativity. They are transverse waves: a strain of spacetime that travels at the speed of light. They are produced when the mass distribution, or more precisely the quadrupole moment, changes in time.

The figure on the right is a sketch of how particles placed on a ring move when a gravitational wave passes. The ring stretches horizontally and squeezes vertically, and half a period later it does the opposite. This stretching is extremely small, and Einstein himself understood that the amplitude would be tiny.

Observations of a binary pulsar had shown indirectly that gravitational waves exist, but until this paper nobody had captured the waves themselves.

※ (Source) The paper's Introduction.

## 3
That indirect evidence came from a binary pulsar. A pulsar is a neutron star that emits radio pulses at very regular intervals. Let us go through the labels on the left from the top. First, Hulse and Taylor discovered a binary pulsar called PSR B1913+16. Later, Taylor and Weisberg observed that this system was losing energy. The paper says this demonstrated the existence of gravitational waves.

The figure on the right is a rough sketch of the idea. The pulsar is red, the companion is blue, and the dashed outer circle is the earlier orbit. As the two stars orbit and lose energy, the orbit slowly shrinks. Note, however, that this did not catch the gravitational waves directly; it showed their existence indirectly.

The paper also says that observing the amplitude and phase of the waves directly would allow new tests of general relativity in strong gravitational fields.

So can we catch the wave itself? As we will see, the change a gravitational wave reaching Earth makes in a 4 km arm is far smaller than the size of a proton. Can such a tiny motion be picked out from the noise on the ground? This paper is the answer to that question.

※ (Supplement, not from the paper) The figure is a schematic for explanation; the paper gives no numbers for the orbit size or how fast it shrinks.

## 4
This is the paper I will present. It comes from the LIGO and Virgo collaborations, and its title is "Observation of Gravitational Waves from a Binary Black Hole Merger."

※ The paper is published under CC BY 3.0, and its figures are used here with the source shown.

## 5
So how do we catch the wave itself? The detector built for this is Advanced LIGO. It is an improved Michelson interferometer with 4 km arms.

When a gravitational wave passes, one arm gets longer and the other gets shorter. The difference in arm length, delta L, equals the strain h of the wave times the arm length L. We read this difference as the phase difference between the two beams of light that come back.

There are two detectors, at Hanford and at Livingston, 10 milliseconds apart at the speed of light. Watching with two distant detectors lets us separate the signal from noise that occurs only at one site, and the difference in arrival time also tells us about the direction of the source.

※ (About the figure) The figure on the right is drawn after the paper's Fig. 3 and leaves out parts such as the cavities discussed on the next two slides. "Photodetector" corresponds to the photodetector in the paper's figure.

## 6
But here is the first obstacle. The change in arm length caused by a gravitational wave is far smaller than a proton. A basic Michelson interferometer cannot read such a difference. So three improvements are added.

The first is a cavity in each arm. Light bounces back and forth between two mirrors, which makes the effect of the gravitational wave on the phase of the light 300 times larger. The second is the power-recycling mirror on the input side. It stores the light, so that the 20 watts from the laser becomes 700 watts at the beam splitter and 100 kilowatts inside each arm. The third is the signal-recycling mirror on the output side, which widens the bandwidth of the arm cavities.

The figure on the right shows how the light power builds up. It uses the paper's values as they are.

As the "Aim" label at the lower left says, all of these are meant to suppress the high-frequency noise we will see on the next slide, the photon shot noise. The stronger the light, the larger the change in the light caused by the phase shift from a gravitational wave.

※ (Source) The paper's Sec. III. The figure is our own, drawn with the paper's numbers.

## 7
Next is noise. The figure on the right shows the detector noise at each frequency; it is the right part of the paper's Fig. 3. Lower means more sensitive. Red is H1, that is Hanford, and blue is L1, Livingston.

The source of noise depends on the frequency. At high frequencies, above 150 hertz, photon shot noise dominates, that is, fluctuations in the number of light particles. This is what the cavities and recycling on the previous slide reduce, by making the light stronger and turning the signal into a larger change in the light. At low frequencies the problem is ground vibration. The mirrors hang from four-stage pendulums mounted on active isolation platforms, which together give more than ten orders of magnitude of isolation above 10 hertz. At intermediate frequencies the thermal noise of the mirrors matters, so low-loss materials are used. The mirrors are 40 kilogram pieces of fused silica, and the fibers that hold them are also fused silica. The mirrors sit in ultra-high vacuum.

As a result, the most sensitive band is 100 to 300 hertz, and the detectors are three to five times more sensitive to strain than the first-generation LIGO. This signal ran from 35 to 250 hertz, around this band.

※ (Source) The paper's Sec. III and Fig. 3(b). The thin spikes in the figure are instrumental lines, such as the power-line frequency and vibrations of the suspension fibers, not signals.

## 8
Now the results. On September 14, 2015, the two detectors caught signals of the same shape. Livingston saw it first, and Hanford 6.9 milliseconds later. The two sites are 10 milliseconds apart at the speed of light, so a gravitational wave traveling at that speed should arrive within this range.

In the figure below, the left panel is Hanford and the right panel is Livingston. In the right panel, the Hanford signal has been shifted in time, inverted, and overlaid, and you can see that the two signals match well.

The peak strain was 10 to the minus 21. Multiplied by the 4 km arm, the change in length is about 10 to the minus 18 meters, far smaller than a proton. The combined signal-to-noise ratio of the two detectors is 24, meaning the signal is about 24 times stronger than the noise.

※ (Presenter's supplement, not a claim of the paper) The length change is a rough estimate from ΔL = hL. The comparison with a proton is a common rule of thumb.

## 9
The next figure shows the same signal as a time-frequency map. The horizontal axis is time, the vertical axis is frequency, and brighter colors mean a stronger signal. The left panel is Hanford and the right panel is Livingston.

In both detectors, the bright part runs from lower left to upper right; in other words, the frequency rises with time. As the paper's abstract says, it goes from 35 hertz up to 250 hertz. The amplitude is largest near 150 hertz. On the next slide I will explain how this rise determines the masses of the objects.

※ (Source) The lower row of the paper's Fig. 1.

## 10
So where did this signal come from? Looking at the waveform, there are about eight cycles in roughly 0.2 seconds, and the oscillation gets faster and larger. Over this time the frequency rises from 35 to 150 hertz, where the amplitude peaks.

This kind of rise is explained as two objects approaching each other while emitting gravitational waves. At low frequencies, how fast this happens is set by a quantity called the chirp mass. Reading the frequency and its rate of change from the figure gives about 30 times the mass of the Sun. From this, the total mass of the two objects is at least 70 solar masses. M-sun is the mass of the Sun.

The top of the figure on the right is the reconstructed waveform, which agrees well with numerical relativity calculations. The bottom shows the effective separation and relative velocity of the two objects. The velocity is an effective value that the paper derives from the post-Newtonian parameter v over c; reading the figure, it exceeds half the speed of light just before the merger. What this slide shows is only that two objects orbited each other and merged. That they are black holes comes on the next slide.

※ (Source) The paper's Sec. II and Fig. 2. "At least 70" is in the detector frame; the masses in the final table (Table I) are in the source frame.

## 11
What are these two objects? The paper narrows it down by size.

If the total mass is at least 70 solar masses, the sum of the two Schwarzschild radii, that is, the size of black holes of those masses, is at least 210 kilometers. On the other hand, the gravitational-wave frequency is around 150 hertz, so the orbital frequency is half of that, 75 hertz. To orbit at this frequency, treating them as point masses, the centers can be only about 350 kilometers apart. The figure on the right draws these sizes and the separation to scale, for the equal-mass case.

So could they be other objects? That is what the two questions on the left are about. A pair of neutron stars is compact, but not heavy enough. A neutron star is at most a few solar masses, so two of them cannot reach 70 solar masses. A neutron star and a black hole, for the same chirp mass, would have a much larger total mass and would merge at a much lower frequency. So the argument is that the only objects that can get this close at this frequency without touching are, in the paper's words, black holes, "among known objects."

※ (Source) The paper's Sec. II. The circle sizes in the figure are an example that divides the 210 km sum of radii equally between equal masses; it is not a figure from the paper.

## 12
But here comes the second obstacle, a doubt: maybe the noise in the two detectors just happened to line up into the same shape. How often do you think such a coincidence would occur? The difficulty in checking this is that we cannot shield the detectors from gravitational waves and measure the noise alone. So the time-shift method is used.

A real gravitational wave appears in both detectors within 10 milliseconds. So we shift the data of one detector by much more than 10 milliseconds and pair it with the other. Then real signals no longer line up, and only chance coincidences between noise remain. The figure on the right is a sketch of this. Changing the shift each time, the paper's binary search repeated this about 10 million times. From 16 days of data, this gives a background equivalent to 608,000 years.

※ (Source) The paper's Sec. V B. The figure is a sketch of the idea; the waveforms and noise are examples.

※ (Source) The paper's Sec. V: the shifted pairs also include cases where a real signal overlaps by chance with noise in the other detector, so the background is not strictly "noise only" and is overestimated. The significance estimate is correspondingly conservative.

## 13
The answer is less than once in 200,000 years. In the figure on the right, the black line is the background built from time shifts, and the orange dots are the events in the actual data. The point in the red circle is GW150914, with a detection statistic of 23.6. The false alarm rate is how often noise alone produces an event this strong. Because GW150914 is louder than every background event, only an upper limit can be set on its false alarm rate: less than once in 203,000 years. Over the 16 days of observation, the probability that noise alone produces an event this strong, the false alarm probability, is below 2×10⁻⁷. Translated into a normal distribution, this is as rare as landing more than 5.1 sigma from the mean, so we say at least 5.1 sigma.

The paper also detected the event in a separate search that does not assume a waveform. There, the detection statistic is 20.0, and the false alarm rate is less than once in 22,500 years, or 4.6 sigma.

The purple line in the figure is the background rebuilt after accepting GW150914 as a real signal and removing it; it is used to assess the second and later candidates. According to the paper, the second loudest event has a false alarm rate of once in 2.3 years. The red circle was added by the presenter.

※ (Source) The paper's Sec. V A and B and Fig. 4. 5.1σ is the bound combining the three search classes (Sec. V).

## 14
Finally, what we learned. The table gives the median estimates and their 90% ranges. Before the merger, the black holes were 36 and 29 solar masses, and after it, 62. The difference, about 3 solar masses, was radiated as gravitational waves. The distance is 410 megaparsecs, about 1.3 billion light years; note that the range is wide. The masses in the table are in the source frame. z is the redshift, the factor by which the expansion of the universe stretches the wave. So the masses in the detector frame are larger by (1+z) ≈ 1.09, and 65 × 1.09 ≈ 71, which matches the "at least 70" from before.

As the "Significance" label on the right says, this paper is both the first direct observation of gravitational waves and the first observation of a binary black hole merger. The three tests of general relativity also showed no inconsistency. With Virgo and KAGRA joining, the position of sources will be determined much more precisely.

The answer to our first question, whether a motion smaller than a proton can be picked out from the noise, is yes, it was. The light and the pendulums read the tiny motion, and the time shifts cleared the doubt that it was a chance coincidence.

That is all. Thank you for your attention.

※ (Source) The numbers are from the paper's Table I and text. All are medians with 90% credible intervals.

## 15
These are answers to questions that may come up after the talk.
The first is whether the noise in the two detectors just lined up by chance. The paper made pairs with one detector's time shifted by a large amount and counted the coincidences that occur from noise alone. Compared with that background, a signal as strong as GW150914 occurs by chance less than once in 203,000 years, corresponding to at least 5.1σ. Going back to slide 13, you can see in the background distribution that this signal stands alone.
The second is whether it could be a pair of neutron stars. The 150 Hz gravitational wave corresponds to a 75 Hz orbit, from which the separation of the two objects is estimated at about 350 km. Only neutron stars or black holes are small enough to orbit this close, but two neutron stars do not have enough mass. Going back to slide 11, you can follow the reasoning that compares the separation with the sum of the Schwarzschild radii.

## 16
The third is what the 6.9 ms delay between the two detectors means. Light takes 10 ms to travel between them, so 6.9 ms is shorter, consistent with one wave passing through the two detectors in turn. The delay alone does not prove it is the same signal, though; the matching waveforms are used together with it. Going back to slide 8, you can see the figure with H1 inverted, shifted, and overlaid on L1.
The fourth is how much energy was released. Before the merger the two objects had 36 and 29 solar masses, and after it 62, so about 3 solar masses were radiated as gravitational waves. In energy, that is 3.0 M⊙c², with a range of ±0.5. Going back to slide 14, you can see the values from the paper's Table I.

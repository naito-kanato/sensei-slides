## 1
<!-- 表紙の枚 -->

Today I will present a paper review on the first observation of gravitational waves. The paper, published in 2016, reports a signal that two detectors caught from a pair of black holes merging far away.

I will start with the background, then show how the detector works, and then go through the main results one by one.

## 2
Let me start with the basic idea behind this paper: gravitational waves. In 1916, the year after the field equations of general relativity were finalized, Einstein predicted that these waves should exist. He found wave solutions in the weak-field version of his equations.

Please look at the figure below. The circle is a ring of free test particles. When a wave passes through the page, the ring is stretched horizontally and squeezed vertically, and half a cycle later the pattern is reversed. So the wave does not push things around. It changes distances in space itself.

According to the paper, these are transverse waves of spatial strain that travel at the speed of light. They are generated when the mass quadrupole moment of the source changes in time. For now, you can think of the quadrupole moment simply as how the mass is distributed.

One point that is easy to miss: Einstein himself understood that the amplitudes would be remarkably small. In fact, people debated whether the waves were physically real at all, until the Chapel Hill conference in 1957.

※ (Not from the source) The ring sketch is my own drawing of the stretch pattern; it is not a figure from the paper.

So if the waves are this small, how did anyone know they were real? That is the next slide.

## 3
Let's look more closely at one part of that story: how we knew these waves were real before this paper.

Look at the figure on the right. It shows the orbit of the binary pulsar PSR B1913+16. The dashed line is the older orbit, and the solid line is the orbit later, slowly shrinking. The sketch has no numbers. It only shows the idea.

Hulse and Taylor discovered this system in 1975. Later, in 1982, Taylor and Weisberg observed its energy loss, and this demonstrated that gravitational waves exist. But notice the red words on the slide: only indirectly. Nobody had seen the wave itself.

※ (Not from the source) A pulsar is a neutron star that sends out very regular radio pulses, so it works like a precise clock.

The paper says that direct observations of the amplitude and phase of the waves would open up new tests of general relativity, especially in the dynamic strong-field regime. That is the goal.

So here is the question for today. Remember the remarkably small amplitude from the last slide. How can a stretch this tiny be caught on Earth, and told apart from noise? Please keep this question in mind, because the rest of the talk answers it step by step.

First, let's look at the instrument that makes this possible.

## 4
<!-- 表紙の枚 ／ ノートへ：Published 11 Feb 2016; over 1000 authors -->

Before we go into the instrument, here is the paper I am presenting. Its title is "Observation of Gravitational Waves from a Binary Black Hole Merger," by the LIGO Scientific Collaboration and the Virgo Collaboration, in Physical Review Letters, volume 116.

It was published on February 11, 2016, and the author list has more than one thousand names. The event itself is called GW150914, after the date it was seen, September 14, 2015.

※ The paper is published under CC BY 3.0, and its figures are used here with the source shown.

## 5
So, to catch that tiny stretch, we use a laser interferometer: the Advanced LIGO detector.

Look at the figure on the right. It is drawn after Fig. 3 of the paper and is not to scale. Laser light hits the beam splitter, which sends it down two perpendicular arms, each 4 km long. At the end of each arm is a mirror, a free-hanging test mass. The light comes back, recombines at the beam splitter, and goes to the photodetector.

When a wave passes, it stretches one arm and shrinks the other, and half a cycle later this reverses. The detector measures the difference, delta L of t, which is delta L x minus delta L y, and that equals h of t times L. Here h is the strain, the fractional stretch delta L over L, with no unit. L is the arm length, 4 km.

This length difference changes the phase difference between the two light fields returning to the beam splitter. So the photodetector gives an optical signal proportional to the strain h.

A common misunderstanding is that the wave pushes the mirrors. It does not. The mirrors are only markers. What changes is the distance between them, the space itself.

So how big is this length change in practice? Next, let's put in the numbers.

## 6
But here is the wall. Let's put real numbers into delta L equals h times L.

Look at the ruler below. It is on a log scale, so equal distances mean equal factors. At the right end is the 4 km arm. Much further to the left is the width of a proton, about 1.7 times ten to the minus fifteen meters. And further left still is the change we actually need to measure.

The strain of the event in this paper peaked at 1.0 times ten to the minus twenty-one. Here I use this later measured peak value as the target size. Multiply it by the 4 km arm, and delta L is only about 4 times ten to the minus eighteen meters. That is roughly one four-hundredth of a proton.

※ (Not from the source) The proton width of about 1.7×10⁻¹⁵ m is based on CODATA 2018, and the 4×10⁻¹⁸ m and the 1/400 ratio are my own rough estimates.

This is why detection took so long. Weber started with resonant mass detectors in the 1960s. Then the initial interferometers, such as initial LIGO, Virgo, GEO 600 and TAMA 300, made joint observations from 2002 through 2011, but they only set upper limits.

One thing to be careful about: h is not a length. It is a fractional stretch, so the length change grows with the arm length.

So how can a detector read a change this small? Next, let's see how LIGO boosts its light.

## 7
So we use two tricks to boost the light inside the detector.

Look at the figure on the left. It is a schematic I drew after the optical layout in Fig. 3 of the paper, keeping only the parts we need today. Follow the red light from the laser: 20 W goes in, it is 700 W at the beam splitter, and 100 kW in each 4 km arm, between its two test masses. The thicker the red line, the more light. The black box at the bottom is the photodetector, as on slide 5.

First, each arm is a resonant optical cavity, formed by its two test mass mirrors. The light bounces back and forth between them, and this multiplies the effect of a gravitational wave on the light phase by a factor of 300.

Second, a partially transmissive power-recycling mirror at the input sends the returning light back in. So 20 W of laser input becomes 700 W at the beam splitter, and then 100 kW circulating in each arm cavity.

Why do we want so much light? These techniques maximize the conversion of strain into optical signal, and so they minimize the impact of photon shot noise, the main noise at high frequencies. Shot noise is the fluctuation in the number of photons. With more photons, this fluctuation is smaller relative to the signal, so a smaller delta L can be read.

※ (Not from the source) For N photons, the relative fluctuation scales as one over the square root of N.

There is also a signal-recycling mirror at the output, which broadens the bandwidth of the arm cavities. The laser is a 1064 nm Nd:YAG laser, and the signal is extracted with a homodyne readout.

※ (Not from the source) Bandwidth here means the range of signal frequencies the cavities can respond to.

But shot noise is only one kind of noise. Next, let's see where the total noise is lowest.

## 8
Another key property of the detector is where its noise is lowest.

Look at the figure on the right, taken from Fig. 3(b) of the paper. The horizontal axis is frequency, and the vertical axis is the instrument noise, expressed as equivalent strain. Lower means quieter. The two curves are H1 at Hanford, in red, and L1 at Livingston, in blue. The shaded band shows where the signal lies, 35 to 250 Hz, which we will see on slide 10.

Above 150 Hz, the limit is photon shot noise, the noise we fought with more light on the last slide. At low frequencies, ground motion dominates. Each test mass hangs as the final stage of a quadruple pendulum, on an active seismic isolation platform. Together they give more than 10 orders of magnitude of isolation from ground motion above 10 Hz. In between, thermal noise matters, so the mirrors are 40 kg fused silica, hung on fused silica fibers.

※ (Not from the source) Each pendulum stage filters out ground motion above its own resonance, so stacking four stages multiplies the effect.

Be careful with the narrow spikes. They are not signals. They are calibration lines, 60 Hz power grid harmonics, and vibrational modes of the suspension fibers. Also, the arm beams run in tubes kept below 1 μPa.

As a result, the most sensitive band is 100 to 300 Hz, where the detectors are 3 to 5 times more sensitive to strain than initial LIGO.

Next, let's see what the two detectors actually recorded.

## 9
Next, with the detectors ready, a signal arrived. On September 14, 2015, at 09:50:45 UTC, both LIGO sites recorded the event called GW150914.

Look at the figure below. It is the top row of Fig. 1, with the time axis from the bottom of the same figure. The horizontal axis is time in seconds. The left panel is the strain at Hanford, H1, and the right panel is Livingston, L1. The vertical axis is strain in units of 10 to the minus 21. In the right panel, blue is L1 and orange is the shifted, inverted H1. The wave reached L1 first and arrived at H1 6.9 ms later. That fits within the 10 ms it takes light to travel between the two sites, so a real wave crossing the Earth could do this.

In the right panel, the H1 data are also drawn shifted by 6.9 ms and inverted. The inversion is needed because the two detectors face in different directions. After this shift, the two traces overlap.

Why do two sites matter? The paper uses widely separated detectors to tell gravitational waves apart from local instrumental and environmental noise. A truck near Hanford does not shake Livingston. So the same shape at both sites points to a common source.

The peak strain was 1.0 times ten to the minus twenty-one, and the combined signal-to-noise ratio, or SNR, was 24.

※ (Not from the source) The truck example is my own illustration of local noise.

As a side note, the first alert came from a low-latency search within three minutes, and Virgo was being upgraded at the time, so only the two LIGO detectors were observing.

Now let's look more closely at how the frequency of this signal changed.

## 10
Let's look more closely at one part of Fig. 1: the bottom row, which shows how the frequency of the signal changed over time.

Look at the figure on the left. This is the time-frequency map for H1; L1 shows the same track. The horizontal axis is time, the vertical axis is frequency, and the color shows the signal power. Follow the bright track. It bends upward from left to right.

According to the paper, over 0.2 s the signal increases in frequency and amplitude in about 8 cycles, from 35 to 150 Hz, where the amplitude reaches its maximum. Looking at the whole signal, the abstract says it sweeps from 35 up to 250 Hz.

This rising tone is called a chirp. ※ (Not from the source) The name comes from the sound: if you play the signal as audio, it sounds like a bird's chirp.

What does this mean? The paper says the most plausible explanation is the inspiral of two orbiting masses due to gravitational-wave emission. The gravitational-wave frequency is twice the orbital frequency. As the pair loses energy to gravitational waves, the orbit shrinks, so the objects go around faster, and the frequency rises.

A point that is easy to get wrong: the frequency rising does not mean the source is coming closer. It is the orbit itself that speeds up.

※ (Not from the source) The statement that energy loss makes the orbit shrink and speed up is my simplified explanation.

Next, let's see what this chirp rate tells us about the mass.

## 11
From this rising chirp, we can say how heavy the source must be. The speed of the frequency sweep on the previous slide is the key.

Look at the figure on the right, the same H1 map as before. Read two things from the bright track. I marked them in white. One is the frequency f at a given moment. The other is its slope, ḟ, which tells you how fast the frequency is climbing.

The paper plugs these two into the chirp-mass formula. I keep the formula off the slide. In words, the chirp mass is m₁ m₂ to the three-fifths, over m₁ plus m₂ to the one-fifth. The paper sets this equal to c cubed over G, times five over ninety-six, pi to the minus eight-thirds, f to the minus eleven-thirds, and ḟ, all raised to the three-fifths. The chirp mass is a particular combination of the two masses, m₁ and m₂, and at low frequencies it alone controls how the chirp evolves. From f and ḟ in Fig. 1, the authors get a chirp mass of about 30 solar masses. That implies a total mass of at least 70 solar masses in the detector frame.

A common slip is to read 30 as the total mass. It is not. The chirp mass fixes only one combination, so many pairs of m₁ and m₂ share it. Among them, the total is smallest when the two masses are equal.
※ (Presenter's own calculation) With equal masses, M = 4^(3/5) ℳ ≈ 2.3 ℳ ≈ 70 solar masses, which is where the lower bound comes from.
Also, "detector frame" means the masses as we see them; Table I says to multiply source-frame masses by one plus z, where z is the redshift, to convert.

As a side check, the numerical-relativity waveform and the model-free reconstruction overlap by 94% in the second row of Fig. 1, and Fig. 2 shows the relative speed rising above half the speed of light near merger.

So, what kind of object can pack 70 solar masses into such a tight orbit?

## 12
Why must these two objects be black holes, and not something else?

Look at the figure on the right. It is a scale drawing. The two filled circles are the horizons of two equal masses. The red arrow between their centers is about 350 kilometers, and the arrow on top is the sum of their radii, at least 210 kilometers. The point is that both bodies must fit inside that 350-kilometer gap without touching. The blue arcs show the two bodies going around each other, 75 times a second.

Here is the reasoning in the paper. The gravitational-wave frequency peaks at 150 hertz, so the orbital frequency is half of that, 75 hertz. Two equal Newtonian point masses orbiting at 75 hertz would be only about 350 kilometers apart. Now, the total mass is at least 70 solar masses, so the summed Schwarzschild radii, 2GM over c squared, are at least 210 kilometers. That is about 3 kilometers per solar mass.
※ (Presenter's own calculation) 210 km divided by 70 solar masses gives the 3 km per solar mass.
So each body must be close to its own Schwarzschild size. That is extremely compact.

Then the paper checks the other candidates one by one. Two neutron stars are compact enough, but they do not have the required mass.
※ (Not from the source) Neutron stars are thought to be at most about 2 to 3 solar masses, so two of them cannot reach 70.
A neutron star with a black hole, with this chirp mass, would need a very large total mass, and so would merge at a much lower frequency. That leaves black holes as the only known objects compact enough. The decay after the peak also fits a black hole settling into a final Kerr state.

But wait. Could the whole signal simply be a chance coincidence of noise?

## 13
Here a question comes up. Isn't this just two noise bumps that happened to line up by chance?

To answer that, we need to know how often noise alone makes an event this strong. That is the background. But there are two problems. The detector noise is non-Gaussian and nonstationary, so we cannot just compute a rate from a sigma; we have to measure it from the data. And we cannot shield a detector from gravitational waves to record a clean, signal-free stretch.

The trick is the time shift, shown in the figure on the right. The top trace is Hanford, the bottom is Livingston. Slide the Livingston data by an offset much larger than the 10-millisecond travel time between the sites. Then search for coincidences again. A real signal can no longer line up, so whatever coincidences remain are made by noise alone.

Each shift gives a new noise-only version of the 16 days of data, taken from September 12 to October 20, 2015. For the binary coalescence search, repeating this about ten million times gives a background equivalent to 608,000 years.

One point is easy to misread. A real signal in one detector can line up with shifted noise in the other and leak into the background. This makes the background too large, so the significance comes out conservative, not inflated. Separately, the environmental sensors found no disturbance that could account for the signal, including a search for correlated disturbances between the two sites, in Section IV.

So, against 608,000 years of noise, how rare is GW150914?

## 14
From the time-shifted background on the last slide, we can now say how rare GW150914 really is.

Look at the histogram on the left. It is the right panel of Figure 4, the binary coalescence search. The horizontal axis is ρ̂c, the SNR combined from both sites and down-weighted when the data look like a glitch. It is the same idea as the SNR of 24 on slide 9. The black line is the noise background, the orange markers are the real candidates, and the scale on top converts the axis to sigma. The red circle, which I added, is GW150914. The purple line is the background with GW150914 removed. The long black tail to the right is GW150914 itself leaking into the background, the conservative bias from the last slide.

GW150914 sits at ρ̂c equal to 23.6, to the right of every background event. Noise alone would produce something this loud less than once in 203,000 years. That is a false alarm probability below 2 times 10 to the minus 7, or 5.1 sigma. The generic search, which uses no waveform model, also finds it, at less than 1 in 22,500 years, or 4.6 sigma.

Two points are easy to get wrong. First, 203,000 years is an upper bound. No background event was louder, so the paper can only say "less than". Second, 5.1 sigma does not mean the noise is Gaussian. The probability is counted from data, and sigma is just a Gaussian-equivalent way to express it.

So the answer to our question is this. The two LIGO detectors recorded the same chirp 6.9 milliseconds apart, and noise alone would mimic it less than once in 203,000 years, which is 5.1 sigma.

Then, what exactly was the source?

## 15
From this significance, we can say the signal is real, so now we can ask what made it.

Look at the three cards. The first card is the mass. Two black holes of 36 and 29 solar masses merged into one of 62 solar masses. The final black hole is lighter than the two it came from.

These masses come from fits with general-relativity waveform models, listed in Table I, in the source frame. Multiplying 36 plus 29 by 1 plus z, which is 1.09, gives about 71 solar masses in the detector frame. That agrees with the lower bound of 70 from the chirp mass on slide 11.
※ (Presenter's own calculation) 65 times 1.09 is about 71.
The second card is the energy. The paper estimates that 3.0 plus or minus 0.5 solar masses times c squared was radiated as gravitational waves, with a peak luminosity of 3.6 times 10 to the 56 erg per second. The third card is the distance. The source is about 410 megaparsecs away, at redshift 0.09, with a 90% range of plus 160 and minus 180. That is about 1.3 billion light-years.
※ (Presenter's conversion) 1 megaparsec is about 3.26 million light-years, so 410 Mpc is about 1.3 billion light-years.

Be careful with the missing mass. Each mass is a median with a 90% range of about plus or minus 4 to 5, so just subtracting 65 minus 62 is not precise. Use the paper's estimate of 3.0 instead. Not on the slide: the paper also ran three tests of general relativity and found no deviation. One test bounds the graviton Compton wavelength above 10 to the 13 kilometers.
The paper notes this can be read as a bound on the graviton mass, below 1.2 times 10 to the minus 22 eV over c squared.

So, back to our question: how can such a tiny stretch be caught and told apart from noise? Two detectors saw the same chirp, and a large time-shifted background showed noise can't explain it. This is the first direct detection of gravitational waves and the first binary black hole merger seen. At design sensitivity, the SNR would be 3 times higher, and Virgo, KAGRA, and a possible LIGO detector in India will join the network.

## 16
Q1. Why is the H1 trace inverted before it is overlaid on L1? The two detectors point their arms in different directions, as shown in the inset of Figure 3. Because of this, the same wave shows up with the opposite sign in the two detectors. So the paper flips H1 and shifts it by 6.9 milliseconds just for a visual comparison. For details, go back to slide 9, where you can see the flipped and shifted H1 trace lying right on top of L1.

Q2. Could an earthquake or a local disturbance have caused it? Each site has an array of environmental sensors, such as seismometers, microphones, and magnetometers. None of them recorded anything that evolved in time and frequency like GW150914. All environmental fluctuations in that second could explain at most 6% of its strain, and a special search found no correlated disturbances between the two sites. For details, go back to slide 9, where you can see the same waveform at Hanford and Livingston, 6.9 milliseconds apart, within the travel time between the sites.

## 17
Q3. What does 5.1 sigma mean here? It is a false alarm probability below 2 times 10 to the minus 7, written as the tail of a Gaussian beyond 5.1 sigma. The detector noise itself is not Gaussian, so the probability is not computed from a sigma. It is counted from the time-shifted background. For details, go back to slide 14, where you can see GW150914 to the right of every background event, with the sigma scale on top.

Q4. Where in the sky was the source? Only the two LIGO detectors were observing, so the position comes mainly from the difference in arrival times. That gives an area of about 600 square degrees, as a 90% credible region. Advanced Virgo, KAGRA, and a possible third LIGO detector in India will extend the network and improve the position. For details, go back to slide 15, where you can see the distance of about 410 megaparsecs, the other half of where the source is.


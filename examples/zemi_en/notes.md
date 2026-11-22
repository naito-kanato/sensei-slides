## 1
<!-- 表紙の枚 -->

Good afternoon. Today I will present the paper "Observation of Gravitational Waves from a Binary Black Hole Merger," published by the LIGO and Virgo collaborations in Physical Review Letters in 2016.

This is the paper that reported the first gravitational-wave signal, GW150914. I will start with the background, then explain how the detector works, then look at the signal and its source, and finally show how the team made sure it was not noise.

## 2
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ ノートへ：Einstein knew the amplitude would be tiny; the reality of GWs was debated until 1957; pulsar = neutron star sending regular radio pulses; quadrupole moment = how the mass distribution changes -->

Let me begin with the background. In 1916, general relativity predicted gravitational waves: transverse waves of strain, which means space itself stretches and squeezes, moving at the speed of light.

Look at the figure on the right. Each dot is a mass floating freely, and the shape of the ring shows the stretch at that moment, for a wave passing straight into the screen. At a quarter period the ring is stretched sideways and squeezed vertically. Half a period later, it is the other way round. The stretch is greatly exaggerated here.

For almost a century the only evidence was indirect. The binary pulsar PSR B1913+16 is a neutron star that sends regular radio pulses while orbiting a companion. Its orbit loses energy and shrinks, because gravitational waves carry the energy away. Einstein himself knew the amplitude would be tiny, and whether the waves were even real was debated until 1957.

You can think of ripples on a pond. The difference is that here the ripple is in distance itself: nothing pushes the dots, the space between them changes.

So here is a question for you. If such a wave passes a 4 km ruler, how far does the ruler stretch? Please keep your guess in mind.

※ (Figure) The ring is schematic and the stretch is exaggerated; the wave travels perpendicular to the page.

## 3
<!-- 表紙の枚 -->

This is the paper I am presenting today. The authors are B. P. Abbott and the rest of the LIGO Scientific Collaboration and the Virgo Collaboration, and it appeared in Physical Review Letters, volume 116, article 061102, in 2016.

The paper is open access under CC BY 3.0, so the figures I show are cropped from it with credit. I will cover the main results, Sections II to VI. One change from the paper's order: I start with the detector, Section III, and then go to the observation, Section II, so that you know how the signal is measured before we look at it.

※ Source: CC BY 3.0, DOI 10.1103/PhysRevLett.116.061102.

## 4
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（手段）（1文目でこの語のつながりを言う） ／ ノートへ：Test masses are free-hanging mirrors; the wave changes the distance between them; like the ring on slide 2, when the x arm stretches the y arm shrinks, so the difference of the two arms catches it; two sites: Hanford (H1) and Livingston (L1) -->

So how do you measure a stretch of space? The answer is to use an interferometer as a ruler.

The drawing on the right is a simplified version of Fig. 3 in the paper, not to scale. Light from the laser is split at the beam splitter and sent down two perpendicular arms, each 4 km long. At the ends hang mirrors called test masses. They hang freely, just like the floating dots on the previous slide. The red line is the light path, and the dashed outlines show one arm getting longer while the other gets shorter.

The paper writes this as the equation on the left. The difference of the two arm changes, delta L x minus delta L y, equals h times L. Here h is the strain, the fractional stretch with no unit, and L is the arm length, 4 km. This difference shifts the phase of the light coming back to the beam splitter, and the photodetector reads it out.

Why take the difference? Remember the ring: when the x direction stretches, the y direction shrinks, so the difference catches both. It is like two runners on perpendicular tracks whose finish times split apart when one track gets longer and the other shorter. The difference is that here the change is far smaller than an atom.

LIGO has two of these, at Hanford, called H1, and Livingston, called L1. So how small is the change?

## 5
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：しかし（壁）（1文目でこの語のつながりを言う） ／ ノートへ：Answer to the slide-2 guess; 10⁻²¹ is the peak strain later measured (1.0×10⁻²¹); proton size (charge radius 0.84 fm) is outside the paper; earlier resonant bars (1960s) and initial interferometers (2002–2011) gave only upper limits -->

But here we hit a wall. Let me answer the guess from slide 2.

The signal we will see later has a peak strain of about ten to the minus 21. Multiply that by the 4 km arm, and the change in length is only about 4 times ten to the minus 18 meters. That is the big number on the slide. A proton is about 1.7 femtometers across, so this stretch is about one four-hundredth of a proton.

This is why earlier detectors failed. Resonant bars in the 1960s and the first interferometers, from 2002 to 2011, gave only upper limits. They never saw a signal.

So the question for the rest of this talk is the one in red at the bottom: how can a stretch this tiny be caught on Earth, and be told apart from noise?

It is easy to think that the problem is simply the length of the ruler. A longer arm does help, but 4 km is already the size of a small town. The real problem is reading such a small change against all the shaking and noise around it.

The next two slides show how LIGO does this, starting with light.

※ (Not from the source) Proton size: charge radius 0.84 fm (CODATA 2018), so about 1.7 fm across. 4×10⁻¹⁸ m and 1/400 are the presenter's estimate.

## 6
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（手段）（1文目でこの語のつながりを言う） ／ ノートへ：5,000 = 100 kW / 20 W (presenter's arithmetic); purpose: more light ⇒ smaller relative shot noise; shot noise = the fluctuation in the number of photons, about √N for N photons, so the relative fluctuation falls as the light grows; 1064 nm laser -->

So the first tool is light: more light makes a sharper ruler.

Look at the flow on the right. The laser puts in 20 watts. A partly transmitting power-recycling mirror at the input sends light that is heading back toward the laser into the arms again, so 700 watts reach the beam splitter. Inside each arm, the light bounces between the two test masses and builds up to 100 kilowatts. That is 5,000 times the input.

The bouncing does a second job. Each trip down the arm adds the phase shift again, so the arm cavity multiplies the effect of the wave on the light phase by about 300.

Why does more light help? At high frequencies the main noise is shot noise. Light arrives as photons, and the number of photons fluctuates by about the square root of N for N photons. So the relative fluctuation becomes smaller as the light grows.

It is like measuring rainfall by counting drops in a bucket. In a light drizzle, a few extra drops make a big error, but in a downpour the same random scatter is a tiny fraction. Unlike rain, the light here comes from a stable 1064 nm laser, so the only randomness left is the photon count itself.

But light helps only at high frequency. What about the rest of the band?

※ (Not from the source) 5,000 = 100 kW / 20 W is the presenter's arithmetic.

## 7
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（並べる）（1文目でこの語のつながりを言う） ／ ノートへ：Reading Fig. 3(b): vertical axis = noise in each frequency band, as strain (unit 1/√Hz); lower = smaller stretches can be read; a pendulum barely follows ground shaking faster than its own swing, and four stages multiply the effect; most sensitive band 100–300 Hz, 3–5× better than initial LIGO; arm tubes below 1 μPa; calibration within 10% in amplitude -->

And the noise is different in each frequency band, so each band needs its own fix.

The figure on the left is Fig. 3(b) of the paper. The horizontal axis is frequency. The vertical axis is the noise in each frequency band, written as strain, in units of one over root hertz. Lower means smaller stretches can be read. Red is Hanford and blue is Livingston; you can ignore the narrow spikes for now. The most sensitive band is about 100 to 300 Hz, three to five times better than initial LIGO.

The three cases on the right go through the bands. Above 150 Hz, photon shot noise dominates, and the extra light from the previous slide pushes it down. In the middle band, thermal noise: the test masses are heavy, 40 kg fused-silica mirrors, so they jiggle less. At low frequency, seismic noise: each mirror hangs as the last stage of a quadruple pendulum on an active isolation platform.

Why does a pendulum help? A pendulum barely follows ground shaking that is faster than its own swing, and four stages multiply the effect. In total, ground motion is cut by more than ten orders of magnitude above 10 Hz.

Two more details: the arm tubes are kept below one micropascal, and the calibration is good to within 10 percent in amplitude. With this detector running, a signal arrived.

## 8
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（次へ）（1文目でこの語のつながりを言う） ／ ノートへ：H1 is inverted because the two detectors face differently; 35–350 Hz bandpass for display; only the two LIGO detectors were observing -->

And then, on 14 September 2015, at 09:50:45 UTC, both LIGO detectors recorded a signal. It is called GW150914, after the date.

The figure at the bottom is the top row of Fig. 1. The vertical axis is strain in units of ten to the minus 21, and time is in seconds after 09:50:45. The left panel is Hanford, H1, in red. The right panel is Livingston, L1, in dark blue, with the Hanford data laid on top in light red. That Hanford trace is shifted in time and flipped upside down, because the two detectors face in different directions. After that, the two wiggles match closely.

The signal reached Livingston first, and Hanford 6.9 milliseconds later. Light needs up to 10 milliseconds to travel between the sites, so a single wave could have passed both. A delay longer than that would have pointed to two unrelated events.

The peak strain was 1.0 times ten to the minus 21. The combined signal-to-noise ratio was 24, which means the signal was 24 times the typical noise. For display, the data were filtered to 35 to 350 Hz. Only these two LIGO detectors were observing at the time.

Next, let us see how the frequency changed during those wiggles.

## 9
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（詳しく）（1文目でこの語のつながりを言う） ／ ノートへ：Reading the map: horizontal = time, vertical = frequency, brightness = signal strength; 'chirp': this rising sweep sounds like a bird's chirp as audio; the whole signal spans 35–250 Hz (abstract) -->

Let us look at the same signal in more detail, as a time-frequency map.

The figure at the bottom is the bottom row of Fig. 1, Hanford on the left and Livingston on the right. The horizontal axis is time, the vertical axis is frequency, and brightness is signal strength. You can see a bright track rising from the lower left to the upper right.

Over about 0.2 seconds, the signal goes from 35 to 150 Hz in about eight cycles, and the amplitude peaks at 150 Hz. The whole signal spans 35 to 250 Hz. Importantly, the same rising track appears in both detectors.

This rising sweep is called a chirp, because played as audio it sounds like a bird's chirp. The reading on the right explains why it rises. Two masses spiral in as they lose energy to gravitational waves, so they orbit faster and faster, and both the frequency and the amplitude go up.

One point is easy to get backward: losing energy makes the orbit faster, not slower. As the masses fall closer together they speed up, a bit like water spinning faster near a drain. Unlike the water, nothing pulls them in except the energy carried off by the waves.

So the shape of this chirp is a clue. How fast it rises tells us how heavy the pair is.

## 10
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（帰結）（1文目でこの語のつながりを言う） ／ ノートへ：Chirp mass = the one mass combination that sets how fast the chirp rises: heavier pairs radiate more strongly and sweep faster; for a given total M, ℳ is largest at m₁ = m₂ (ℳ ≈ 0.435M), so ℳ ≃ 30 M⊙ needs M ≈ 70 M⊙ or more (presenter's arithmetic); Fig. 2 bottom: R_S = Schwarzschild radius 2GM/c² (horizon size); speed above 0.5c near merger -->

So the rate of the rise lets us weigh the pair.

On the left is Fig. 2 of the paper. The top panel is the full waveform, with pictures of the black hole horizons from numerical relativity: inspiral, merger, and ringdown. Below this panel, the paper also plots the separation of the two bodies in Schwarzschild radii and their speed, which goes above 0.5 c near the merger. The Schwarzschild radius, R S, is 2 G M over c squared; it is the size of the horizon.

On the right is the equation for the chirp mass, script M. It is the one combination of the two masses that sets how fast the chirp rises: heavier pairs radiate more strongly and sweep faster. The right-hand side needs only f, the observed frequency, and f dot, its rate of change, both read from the data in Fig. 1.

From the data, the chirp mass is about 30 solar masses. For a given total mass, the chirp mass is largest when the two masses are equal, at about 0.435 of the total. So 30 solar masses needs a total of about 70 solar masses or more.

Seventy solar masses, orbiting fast enough to give these frequencies. What kind of objects can do that?

※ (Not from the source) ≳70 M⊙ from ℳ ≈ 0.435M at m₁ = m₂ is the presenter's arithmetic.

## 11
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（問い）（1文目でこの語のつながりを言う） ／ ノートへ：Heaviest well-measured neutron star: PSR J0740+6620, 2.08 ± 0.07 M⊙ (Fonseca et al., ApJL 915, L12, 2021; outside the paper), so two cannot reach 70 M⊙; orbit 75 Hz = half the 150 Hz GW frequency; equal point masses; R_S = 2GM/c² (slide 10), so 70 M⊙ gives about 210 km, and 350 km is under twice that: only black holes are that compact; NS + BH with this chirp mass would need a very large total mass, and a bigger pair touches at a wider, slower orbit, so it would merge at a lower frequency -->

That leads to the next question: what objects could these be? The figure on the left answers it with a scale drawing.

It is drawn to scale, with the bar at the top showing 100 km. The blue circles are the horizon sizes, and the distance between their centers is the separation at a 75 Hz orbit. The orbit is 75 Hz because the gravitational-wave frequency, 150 Hz at the peak, is twice the orbital frequency.

On the right we check three candidates. Two neutron stars? Each is at most about 2 solar masses; the heaviest well-measured one is 2.08. So two of them cannot reach 70. A neutron star and a black hole? With this chirp mass the total mass would be very large, and a bigger pair touches at a wider, slower orbit, so it would merge at a much lower frequency. Two black holes? Kepler's law for equal point masses puts them only 350 km apart. The Schwarzschild radius is about 3 km per solar mass, so 70 solar masses gives radii that add up to about 210 km.

350 km is less than twice 210 km, so the pair is extremely compact, and only black holes are that compact.

So the source looks like two black holes. But can we trust that the signal is real at all?

※ (Not from the source) Heaviest well-measured neutron star: PSR J0740+6620, 2.08 ± 0.07 M⊙ (Fonseca et al., ApJL 915, L12, 2021).
※ (Figure) Equal masses; each horizon radius is about 105 km, half of 210 km.

## 12
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：しかし（疑い）（1文目でこの語のつながりを言う） ／ ノートへ：Glitch = a short burst of noise from the instrument; non-Gaussian = big bursts come far more often than a normal distribution predicts, so σ cannot be computed from a formula and chance must be counted; no correlated transients between sites; sensors: seismometers, microphones, magnetometers, radio receivers, cosmic-ray detector; ~10⁵ channels; detectors cannot be shielded from GWs -->

But wait. Could this signal be fake? The data contain glitches, so we have to doubt it.

A glitch is a short burst of noise from the instrument. LIGO noise is also non-Gaussian, which means big bursts come far more often than a normal distribution predicts. So we cannot compute the sigma from a formula; the chance has to be counted.

The two questions at the top are the two doubts. First, a local disturbance. The sites are watched by about a hundred thousand channels: seismometers, microphones, magnetometers, radio receivers, and a cosmic-ray detector. Every disturbance they saw was under 6 percent of the signal's strain, too small to make it, and there were no correlated transients between the sites. You cannot shield a detector from gravitational waves, so these sensors are the check.

The comparison at the bottom shows what to look for. A gravitational wave has the same shape at both sites, arrives no more than 10 ms apart, and leaves the sensors quiet. Noise has different shapes, any offset in time, and the sensors see it.

The second doubt is a chance coincidence: two unrelated glitches that happen to line up. That cannot be ruled out by sensors; it must be counted, which is the next slide.

## 13
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（手段）（1文目でこの語のつながりを言う） ／ ノートへ：Nothing is invented: real noise is re-paired in time; each shift adds another 16 days of noise-only coincidences, so ~10⁷ shifts × 16 days add up to 608,000 years; 16 days: 12 Sep – 20 Oct 2015; numbers are for the binary coalescence search; a real signal in the background makes the false alarm rate an overestimate -->

So how do you count chance? You manufacture a background.

The figure on the left shows the idea. The rows are the two detectors. In the original data at the top, a real signal, in red, lines up in H1 and L1. At the bottom, the L1 data are slid in time by an offset much larger than 10 ms. Now the real signal no longer lines up, so any coincidence that is left must come from noise alone.

The steps are on the right. First, shift one site by much more than 10 ms, beyond the light travel time, so no real wave can line up. Second, count the coincidences again. Third, repeat about ten million times. Each shift adds another 16 days of noise-only coincidences, from the observing period of 12 September to 20 October 2015. So ten million shifts of 16 days add up to 608,000 years of noise.

Nothing is invented here; it is real noise, only re-paired in time. Think of shuffling two decks of cards against each other to see how often pairs match by luck. Unlike the cards, the real signal is still inside the data, which makes the noise look stronger, so the method is conservative.

These numbers are for the binary coalescence search. So how did GW150914 compare with this background?

## 14
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：だから（帰結）（1文目でこの語のつながりを言う） ／ ノートへ：Reading Fig. 4: horizontal = loudness score, vertical = number of events, lines = time-shifted background, red circle = GW150914; false alarm rate = how often noise alone makes an event this strong; 203,000 is an upper bound set by the background length; it is below 608,000 because the search sorts events into classes, and counting the chance in any class (trials factor) lowers the bound; 16 days ÷ 203,000 years ≈ 2×10⁻⁷ = chance that noise did it during the run ↔ 5.1σ Gaussian tail; values in データ1 -->

Here is the result: no background event beat it.

The figure on the left is the right panel of Fig. 4, from the binary coalescence search. The horizontal axis is the loudness score, and the vertical axis is the number of events, on a log scale. The black line is the time-shifted background, the orange squares are the real events, and GW150914 is the one circled in red, far to the right.

This search fits merger waveforms, called templates. Its loudness score for GW150914 was 23.6, beyond every background event. So the false alarm rate, meaning how often noise alone makes an event this strong, is less than once per 203,000 years. That is 5.1 sigma.

Note that 203,000 years is an upper bound set by the length of the background. It is below 608,000 because the search sorts events into classes, and counting the chance in any class, the trials factor, lowers the bound. Sixteen days divided by 203,000 years is about two times ten to the minus 7: the chance that noise did this during the run, which matches a 5.1 sigma Gaussian tail.

The generic transient search, which uses no waveform model, also found it, at less than once per 22,500 years, 4.6 sigma. Two independent searches both detect it. So the answer to our question: the same chirp at two sites, and not noise.

## 15
<!-- 目安 462字前後（導入・図の読み方・根拠・例か間違いやすい所・次へのつなぎ） ／ 前の枚から：そして（次へ）（1文目でこの語のつながりを言う） ／ ノートへ：Masses as at the source; read at Earth, cosmic expansion (z = 0.09) stretches the wave and masses look about 1.09× heavier, so slide 10's ≳70 M⊙ is about 65 = 36 + 29 here; 90% intervals ±4–5 M⊙; distance 410 Mpc (z = 0.09); peak luminosity 3.6×10⁵⁶ erg/s; graviton mass < 1.2×10⁻²² eV/c²; final spin 0.67; sky area ~600 deg² -->

And with the signal confirmed, the full waveform tells us about the source.

The bar chart on the left shows the masses from Table I of the paper. Before the merger, the two black holes had 36 and 29 solar masses. After the merger, one black hole of 62 solar masses remained; that is the highlighted bar.

Now the arithmetic: 36 plus 29 is 65, but the final mass is only 62. The missing mass left as gravitational waves; the paper estimates 3.0 plus or minus 0.5 solar masses times c squared. The peak luminosity was 3.6 times ten to the 56 erg per second. These values come from Bayesian fits of general-relativity waveforms.

One point may confuse you. On slide 10 the total was 70 or more, but here it is 65. These masses are at the source. Read at Earth, cosmic expansion at redshift 0.09 stretches the wave, so the masses look about 1.09 times heavier. The distance is 410 megaparsecs. Each mass also has a 90 percent range of about plus or minus 4 to 5 solar masses.

Finally, the team ran three tests of general relativity and found no deviation. For example, the graviton mass must be below 1.2 times ten to the minus 22 eV over c squared. The final black hole has a spin of 0.67.

Let me now summarize.

## 16
<!-- まとめの枚 ／ ノートへ：Full answer: first direct GW detection and first binary black hole merger〔VIII. Conclusion〕; outlook: design sensitivity gives 3× SNR; Virgo, KAGRA, LIGO-India improve sky position〔VII. Outlook〕 -->

Let me go back to the question from slide 5: how can a stretch smaller than a proton be caught on Earth, and told apart from noise?

The flow at the top retraces the story. The stretch is tiny, about 4 times ten to the minus 18 meters. Strong light, 100 kilowatts in each arm, and quiet mirrors on quadruple pendulums made it readable. The same chirp appeared at both sites, 6.9 ms apart. And 608,000 years of time-shifted background showed it was not chance, at 5.1 sigma.

The three points below are what I would like you to take home. How do you catch it? Strong light and quiet mirrors. Could it be noise? Less than once per 203,000 years. What was the source? Merging black holes.

So this paper reports both the first direct detection of gravitational waves and the first observation of a binary black hole merger. Looking ahead, reaching the design sensitivity will give about three times the signal-to-noise ratio, and adding Virgo, KAGRA, and LIGO-India will locate sources in the sky much better.

Thank you for your attention.

## 17
<!-- 想定質問の枚 -->

These are questions I expect.

If someone asks whether noise in the two detectors could have lined up by chance, I will go back to slide 14. The time-shifted background is equivalent to 608,000 years, and noise this strong appears less than once in 203,000 years, which is 5.1 sigma.

If someone asks whether an earthquake or a power-line disturbance could have caused it, I will go back to slide 12. The site sensors found every fluctuation under 6 percent of the strain amplitude, and no disturbance correlated between the two sites.

## 18
<!-- 想定質問の枚 -->

Two more expected questions.

If someone asks what the 6.9 ms delay means, I will go back to the figure from slide 8. It is shorter than the 10 ms light travel time between the sites, so one wave could have passed both.

If someone asks where in the sky the source was, I will go back to slide 15. With only two detectors, the position is set mainly by the arrival times, so it is spread over about 600 square degrees for the 90 percent region. Virgo and KAGRA will narrow it.

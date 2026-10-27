---
layout: post
title: "MRPM 2026"
date: 2026-10-24
---

Oh, wow! You made it this far. Congrats. You can find the poster itself and the references I used below.
Now, let me tell you what the main idea of this work is in informal tone.
We are generally very interested in application of the second moment (M2), that we are obtaining by integration from the NMR spectral line. Usually, scientist will do the fitting, and calculate the M2 from there. What is the problem in our opinion?

Fitting requires a model (in the worst case scenario, it requires also the correct initial parameters). It is all nice, when you have a task to study the materials, you have SAXS, NMR, DSC on your hands, plenty of time, and some knowledge about fitting procedure. Imagine, if you do not have all of this -- and this is exactly where many industry clients are. Another option is if you want to do the routine measurements in vast quantities: such as temperature measurements. Fitting procedure will take you substantial amount of time, no doubt.

OK, let's assume I have convinced you. So what with the second moment? Well, it is known to be dependent on crystallinity, and many other properties, that influence the dipolar coupling. We can measure it's temperature dependence for couple of convenient polymers, and this leads us to the first two graphs. Basically, as the temperature increases, the molecular motions in the polymer gradually unfreeze and activate -- The M2 decreases. What happens next is that we are arriving at some kind of a plateau (of even splash-increase), and this is the temperature region, where the effective proton–proton dipolar interactions remain approximately constant. This means that the molecular motions responsible for averaging these interactions are not changing significantly on the NMR timescale.
Further heating produces little additional reduction in M2, until another motional process becomes effective.

OK, we can actually connect these changes with what we see in the T1: there we see alpha-beta-gamma processes, and these are overlapping with the M2 temperature dependence. I think it's cool.

Next? We can use it in the Spin Diffusion experiment. Instead of doing multicomponent complex fitting of the NMR line (spectral or decay) we can take the M2 of the signal filtered in the Double-Quantum experiment. Let's say, when we are filtering the signal at ~60us, the contribution from the rigid signal becomes neglectable. And we can say that the M2 at 60us DQ filtering time corresponds solely to the amorphous part. Well, now we just need to use it in the corresponding formula, and this is how we get the dimensions of the amorphous part of the material.

Thank you for your attention, and have a nice conference :)

# Poster

[![MRPM 2026 Poster]({{ '/assets/mrpm2026/poster_preview.png' | relative_url }})]({{ '/assets/mrpm2026/poster.pdf' | relative_url }})

[Download the poster (PDF)]({{ '/assets/mrpm2026/poster.pdf' | relative_url }})

# References

1. **Grunin, Leonid; Ivanova, Maria; Schiraya, Veronika; Grunina, Tatiana**
   *Time-Domain NMR Techniques in Cellulose Structure Analysis*
   Applied Magnetic Resonance **54** (2023), 929--955
   .

2. **Hedesiu, Cristian; Demco, Dan E.; Kleppinger, Ralph; Buda, Alina Adams; Blümich, Bernhard; Remerie, Klaas; Litvinov, Victor M.**
   *The effect of temperature and annealing on the phase composition, molecular mobility and the thickness of domains in high-density polyethylene*
   Polymer **48** (2007), 763--777
   .

3. **Litvinov, Victor M.; Penning, Jan Paul**
   *Phase Composition and Molecular Mobility in Nylon 6 Fibers as Studied by Proton NMR Transverse Magnetization Relaxation*
   Macromolecular Chemistry and Physics **205** (2004), 1721--1734
   .

4. **Litvinov, Victor; Men, Yongfeng**
   *Time-domain NMR in polyolefin research*
   Polymer **256** (2022), 
   .

5. **Lange, Frank; Schwenke, Konrad; Kurakazu, Manami; Akagi, Yuki; Chung, Ung-il; Lang, Michael; Sommer, Jens-Uwe; Sakai, Takamasa; Saalwächter, Kay**
   *Connectivity and Structural Defects in Model Hydrogels: A Combined Proton NMR and Monte Carlo Simulation Study*
   Macromolecules **44** (2011), 9666--9674
   .

6. **Demco, Dan E.; Johansson, Anna; Tegenfeldt, Jörgen**
   *Proton spin diffusion for spatial heterogeneity and morphology investigations of polymers*
   Solid State Nuclear Magnetic Resonance **4** (1995), 13--38
   .

7. **Eckman, R. R.; Henrichs, P. M.; Peacock, A. J.**
   *Study of Polyethylene by Solid State NMR Relaxation and Spin Diffusion*
   Macromolecules **30** (1997), 2474--2481
   .

8. **Bonk, Fábio A.; Caldarelli, Stefano; Phan, Trang; Bertin, Denis; Deazevedo, Eduardo R.; Mantovani, Gerson Luiz; Bonagamba, Tito J.; Plivelic, Tomás S.; Torriani, Iris L.**
   *Investigation by combined solid-state NMR and SAXS methods of the morphology and domain size in polystyrene-b-polyethylene oxide-b-polystyrene triblock copolymers*
   Journal of Polymer Science Part B: Polymer Physics **48** (2009), 55--64
   .

9. **Schmidt-Rohr, K.; Spiess, H. W.**
   *Chain diffusion between crystalline and amorphous regions in polyethylene detected by 2D exchange carbon-13 NMR*
   Macromolecules **24** (1991), 5288--5293
   .

10. **Idiyatullin, D. Sh.; Khozina, E. V.; Smirnov, V. S.**
   *Studies of domain morphology in segmented polyurethanes by pulsed NMR*
   Solid State Nuclear Magnetic Resonance **7** (1996), 17--26
   .

11. **Qin, Yanan; Qiao, Yongna; Chassé, Walter; Litvinov, Victor; Men, Yongfeng**
   *Crystallinity of polyolefins with large side groups by low-field 1H NMR T2 relaxometry: Isotactic Polybutene-1 with form II and I crystals*
   Solid State Nuclear Magnetic Resonance **105** (2020), 
   .

12. **Androsch, René; Di Lorenzo, Maria Laura; Schick, Christoph; Wunderlich, Bernhard**
   *Mesophases in polyethylene, polypropylene, and poly(1-butene)*
   Polymer **51** (2010), 4639--4662
   .

13. **Di Girolamo, Rocco; Cicolella, Alessandra; Talarico, Giovanni; Scoti, Miriam; De Stefano, Fabio; Giordano, Angelo; Malafronte, Anna; De Rosa, Claudio**
   *Structure and Morphology of Crystalline Syndiotactic Polypropylene-Polyethylene Block Copolymers*
   Polymers **14** (2022), 
   .

14. **Yamamoto, Katsuhiro; Kato, Kazumichi; Sugino, Yusuke; Hara, Shigeo; Miwa, Yohei; Sakaguchi, Masato; Shimada, Shigetaka**
   *ESR Study on Segmental Motion of Polyethylene in Amorphous Region, Dependent on Crystallinity, Molecular Weight, and Labeled Site*
   Macromolecules **38** (2005), 4737--4743
   .

15. **Crist, Buckley; Peterlin, A.**
   *Spin-Lattice Relaxation in Linear Polyethylene*
   Journal of Polymer Science Part A-2: Polymer Physics **7** (1969), 1165--1186
   .

16. **Crist, Buckley; Peterlin, A.**
   *Spin-lattice relaxation in branched polyethylene*
   Journal of Macromolecular Science, Part B: Physics **4** (1970), 791--810
   .

17. **Głowinkowski, S.; Makrocka-Rydzyk, M.; Wanke, S.; Jurga, S.**
   *Molecular dynamics in polyethylene and ethylene-1-butene copolymer investigated by NMR methods*
   European Polymer Journal **38** (2002), 961--969
   .

18. **Trappeniers, N. J.; Gerritsma, C. J.; Oosting, P. H.**
   *The measurement of nuclear magnetic relaxation time T1 in polymers by means of spin echo technique*
   Physica **30** (1964), 997--1017
   .

19. **Slichter, W. P.**
   *NMR Studies of Multiple Relaxations in Polymers*
   Journal of Polymer Science Part C: Polymer Symposia **14** (1966), 33--48
   .

20. **Anderson, J. E.; Slichter, W. P.**
   *Nuclear Spin Relaxation in Solid n-Alkanes*
   Journal of Physical Chemistry **69** (1965), 3099--3104
   .

21. **Moraes, Tiago B.; Von Atzingen, Gustavo V.; Mazzero, Larissa P.; Mendes, William S.; Zacharias, Marina B.; Cardinali, Marcelo C. B.**
   *An open-access WebApp for inverse Laplace transform analysis of time-domain nuclear magnetic resonance signals*
   Magnetic Resonance **7** (2026), 39--51
   .

22. **Saalwächter, Kay**
   *Proton multiple-quantum NMR for the study of chain dynamics and structural constraints in polymeric soft materials*
   Progress in Nuclear Magnetic Resonance Spectroscopy **51** (2007), 1--35
   .

23. **Chassé, Walter; López Valentín, Juan; Genesky, Geoffrey D.; Cohen, Claude; Saalwächter, Kay**
   *Precise dipolar coupling constant distribution analysis in proton multiple-quantum NMR of elastomers*
   Journal of Chemical Physics **134** (2011), 
   .

24. **Goldman, M.; Shen, L.**
   *Spin-Spin Relaxation in LaF3*
   Physical Review **144** (1966), 321--331
   .

25. **Saalwächter, Kay**
   *Detection of Heterogeneities in Dry and Swollen Polymer Networks by Proton Low-Field NMR Spectroscopy*
   Journal of the American Chemical Society **125** (2003), 14684--14685
   .


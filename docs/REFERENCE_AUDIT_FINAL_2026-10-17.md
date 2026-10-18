# Final reference audit — 17 October 2026

This supersedes the initial citation audit for the current three help essays.
It separates source identity, access and claim support. The author's prose and
captions remain unchanged apart from authorized citation markup and the linked
“here” presentation. This document supplies no replacement prose.

## Corrections applied

- Removed the opening Zenodo citation by the owner's explicit choice. An exact
  Dennett source for the definition of art was not established; no attribution
  was substituted.
- Removed the extra closing SoundingLine theory citation. Exactly three closing
  repository citations remain, as project pointers. Unused self-reference
  bibliography entries were removed from the working manuscript; archives remain.
- Removed Schwabe and Wolf's stress/habit citation after “expert transition map.”
  Their [study](https://pubmed.ncbi.nlm.nih.gov/19494141/) reports a shift toward
  habitual behavior under stress, not expanded creative possibilities.
- Replaced the failing Kautz/Allen landing-page URL with the official
  [AAAI paper](https://cdn.aaai.org/AAAI/1986/AAAI86-006.pdf).
- Rebuilt citation numbering: **97 unique destinations**, with one shared number
  per destination across prose and captions. The website link is rendered on “here.”

## What was checked

Two serial network passes were made: 98 references after the self-citation
removals, then 97 after the stress citation removal and AAAI correction. The
[final machine receipt](citation-final-url-audit-2026-10-17.json) preserves the
second pass. All 58 DOI records resolved through Crossref and their registered
titles matched the listed works. This verifies registration, not publisher
availability or the claim attached to the source.

The other 39 destinations returned 31 HTTP success responses, five HTTP denials
and three transport errors. Two of the success responses were HTTP 202 challenge
pages and do not establish readable content. Subsequent primary-page checks
resolved the Warwick paper, ACL paper and Berkeley article; the MIT record's
identity was also checked through its indexed primary page. Access remains
unresolved for the Yudkowsky/Soares book site, both UCSB chapter PDFs, Sutton's
essay, the New York Times article and Oxford's Blackmore book page. An access
failure is not evidence of an invalid citation.

Author abstracts were obtained for 55 of the final references through Crossref,
DOI-matched Europe PMC records or arXiv. Those abstracts and selected primary
pages were reviewed for scope. Other entries received identity/topic checks;
this is **not a claim that all 97 full texts were read or every sentence was
validated**. The ledger below identifies the review basis. Retrieved abstracts
stay in local review notes and are not redistributed in the handoff.

## Remaining concerns, ordered by impact

1. **Safety certainty and the proposed anti-capture mechanism.** The CAIS
   statement supports treating extinction risk as a priority, not a certainty
   or proof that this particular architecture is necessary. Armstrong and
   Mindermann establish non-identifiability without normative assumptions;
   Cao and colleagues recover rewards under specified structural conditions.
   Neither establishes that inference weakness forces universal participation
   or prevents capture. These remain the author's arguments, not demonstrated
   properties of ToMpathy. See references 8–11 and 89–93 in the ledger.
2. **Human learning decline versus model collapse.** Shumailov concerns recursive
   model training, not the same mechanism in people. Vicente/Matute demonstrate
   inherited bias in simulated classification tasks. The colonoscopy study
   reports a fall in adenoma detection from 28.4% to 22.4%: six percentage points,
   about 21% relative, in an observational setting. It does not measure general
   clinical accuracy or establish an unlabeled-art condition. The owner's
   “less than 1.5%” skill-decay statement remains uncited by explicit instruction.
   The broader acceleration claims exceed these results (references 7, 43–44).
3. **Recovering personal setpoints from attention or prose.** Revealed-attention
   and costly-information-choice models require specified observations and
   assumptions; homeostatic reinforcement learning models physiological
   regulation. None validates extracting personal cultural setpoints, uncertainty
   or practice timestamps from arbitrary prose. Gao's user-edit evaluation uses
   simulated users. Keep these distinctions when describing actual engine data
   (references 75–86); no admission gates changed in this pass.
4. **Neural mechanism and emotion universality.** Lesion and mirror-neuron work
   supports components and dissociations, not the entire causal chain stated in
   the essay. Ekman 1983 does support directed facial-muscle construction and
   autonomic changes; that support should not be dismissed. The Many Smiles
   study concerns happiness rather than the full fear self-test. Reduced mPFC
   response to extreme outgroups is not complete neural or learning shutdown.
   Panksepp and Barrett represent competing accounts; the citations do not settle
   the dispute (references 28–37, 54, 62–65).
5. **Human AI-detection trajectories.** The Turing-test and linguist studies are
   bounded evaluations, not longitudinal evidence that people or experts worsen
   fastest. Russell/Karpinska/Iyyer do find strong performance by experienced
   users on their English nonfiction task: that is a qualified, relevant result,
   not a universal trend (references 45–47).
6. **Adrenaline and creativity.** Baas concerns anger and short-lived creative
   benefits; it does not isolate adrenaline as the proposed causal mechanism.
   Removing the mismatched stress citation leaves that stronger mechanism
   unestablished, rather than fixing it with an unrelated source (reference 88).
7. **Compression, exclusive attention and scaling.** Schmidhuber presents a
   theoretical account; infant learning and attention/plasticity studies support
   narrower phenomena. They do not establish that conscious attention is the
   only route to learning or that the fastest compression always wins attention.
   SIFT and the Bitter Lesson likewise do not demonstrate that empathy will
   necessarily follow from scale (references 50–52, 77–83).

These limits are editorial findings for the author, not instructions to rewrite
the frozen text automatically. A valid DOI and a passing software test do not
make a theoretical claim an empirical result.

## Per-reference ledger

Numbers match the final rendered essays. “Abstract” means the author abstract
was reviewed; “identity/topic” is a deliberately narrower check. Scope notes
describe relevant limits, not a certification of every adjacent assertion.



| No. / source | Review basis | Relevant scope |
| --- | --- | --- |
| 1. [Lopez-Brau, M., Kwon, J., & Jara-Ettinger, J. (2020). Mental state inference from indirect evidence through Bayesian event reconstruction. Proceedings of the 42nd Annual Conference of the Cognitive Science Society, 467-473.](https://cognitivesciencesociety.org/cogsci20/papers/0085/index.html) | Identity/topic | Bayesian reconstruction from indirect traces; not the exact definition of art. |
| 2. [Baker, C. L., Saxe, R., & Tenenbaum, J. B. (2009). Action understanding as inverse planning. Cognition, 113(3), 329-349.](https://dspace.mit.edu/handle/1721.1/60852) | Identity/topic; access caveat above | Inverse planning with modeled actions and assumptions; not unique access to motives. |
| 3. [Rendell, L., et al. (2010). Why copy others? Insights from the social learning strategies tournament. Science, 328(5975), 208-213.](https://doi.org/10.1126/science.1184719) | Abstract + identity | Copying strategies in a social-learning tournament; scope is the modeled setting. |
| 4. [Bandura, A. (2001). Social cognitive theory of mass communication. Media Psychology, 3(3), 265-299.](https://doi.org/10.1207/S1532785XMEP0303_03) | Identity/topic | Attention within social cognitive theory; not proof that all learning is consciously attended. |
| 5. [Sperber, D., et al. (2010). Epistemic vigilance. Mind & Language, 25(4), 359-393.](https://doi.org/10.1111/j.1468-0017.2010.01394.x) | Identity/topic | Epistemic vigilance framework; evaluate particular mechanisms separately. |
| 6. [Ng, A. Y., & Russell, S. J. (2000). Algorithms for inverse reinforcement learning. Proceedings of the 17th International Conference on Machine Learning, 663-670.](https://ai.stanford.edu/~ang/papers/icml00-irl.pdf) | Identity/topic | Inverse reinforcement learning algorithms; reward recovery needs assumptions. |
| 7. [Budzyń, K., et al. (2025). Endoscopist deskilling risk after exposure to artificial intelligence in colonoscopy: A multicentre, observational study. The Lancet Gastroenterology & Hepatology, 10(10), 896-903.](https://wrap.warwick.ac.uk/id/eprint/191005) | Primary paper/page + identity; access caveat above | Observational colonoscopy ADR decline; not general medical accuracy or an unlabeled-art experiment. |
| 8. [Center for AI Safety (2023, May 30). Statement on AI extinction risk.](https://aistatement.com) | Identity/topic | Risk-priority statement; not a probability estimate or endorsement of this architecture. |
| 9. [Yudkowsky, E., & Soares, N. (2025). If anyone builds it, everyone dies: Why superhuman AI would kill us all. Little, Brown.](https://ifanyonebuildsit.com) | Identity/topic; access caveat above | Book-length risk argument; access unresolved and not empirical certainty. |
| 10. [CNN Business (2025, August 13). The ‘godfather of AI’ reveals the only way humanity can survive superintelligent AI.](https://cnn.com/2025/08/13/tech/ai-geoffrey-hinton) | Identity/topic | News attribution of Hinton’s position; not a demonstrated safety solution. |
| 11. [Albarracin, M., et al. (2026). Empathy modeling in active inference agents for perspective-taking and alignment.](https://arxiv.org/abs/2602.20936) | Abstract + identity | Active-inference social-agent model separates prediction from prosocial valuation; limited game setting. |
| 12. [Preston, S. D. (2013). The origins of altruism in offspring care. Psychological Bulletin, 139(6), 1305-1341.](https://doi.org/10.1037/a0031755) | Abstract + identity | Offspring-care account of altruism; theoretical/review scope, not a complete engineering specification. |
| 13. [Hamid, S. (2025, December 30). EFF’s investigations expose Flock Safety’s surveillance abuses: 2025 in review. Electronic Frontier Foundation.](https://eff.org/deeplinks/2025/12/effs-investigations-expose-flock-safetys-surveillance-abuses-2025-review) | Identity/topic | Original surveillance investigation; concrete case, not a general causal test. |
| 14. [Tolman, E. C. (1948). Cognitive maps in rats and men. Psychological Review, 55(4), 189-208.](https://doi.org/10.1037/h0061626) | Identity/topic | Cognitive-map account; does not establish an identity between all thought and compression. |
| 15. [Wood, W., & Rünger, D. (2016). Psychology of habit. Annual Review of Psychology, 67, 289-314.](https://doi.org/10.1146/annurev-psych-122414-033417) | Abstract + identity | Context-linked habits and goal pursuit; supports automaticity without reducing all expertise to habit. |
| 16. [Hebb, D. O. (1949). The organization of behavior: A neuropsychological theory. Wiley.](https://archive.org/details/organizationofbe00hebbrich) | Identity/topic | Historical plasticity theory; no direct validation of the essay’s full inference chain. |
| 17. [Shatz, C. J. (1992). The developing brain. Scientific American, 267(3), 60-67. The source of the “fire together, wire together” wording; Hebb never used it.](https://doi.org/10.1038/scientificamerican0992-60) | Identity/topic | Developing-brain discussion and wording attribution; not a universal learning theorem. |
| 18. [Logan, G. D. (1988). Toward an instance theory of automatization. Psychological Review, 95(4), 492-527.](https://doi.org/10.1037/0033-295X.95.4.492) | Identity/topic | Instance-based automaticity theory; framework and experimental scope matter. |
| 19. [Rasmussen, J. (1985). The role of hierarchical knowledge representation in decisionmaking and system management. IEEE Transactions on Systems, Man, and Cybernetics, SMC-15(2), 234-243.](https://doi.org/10.1109/TSMC.1985.6313353) | Identity/topic | Hierarchical knowledge in human behavior; background for hierarchy, not a recovered author history. |
| 20. [Kautz, H. A., & Allen, J. F. (1986). Generalized plan recognition. Proceedings of the Fifth National Conference on Artificial Intelligence (AAAI-86), 32-37.](https://cdn.aaai.org/AAAI/1986/AAAI86-006.pdf) | Primary paper/page + identity | Formal plan-recognition paper; official AAAI PDF replaces blocked landing page. |
| 21. [Clark, A. (2013). Whatever next? Predictive brains, situated agents, and the future of cognitive science. Behavioral and Brain Sciences, 36(3), 181-204.](https://doi.org/10.1017/S0140525X12000477) | Abstract + identity | Predictive-processing account; theoretical synthesis, not all details settled. |
| 22. [Gergely, G., Bekkering, H., & Király, I. (2002). Rational imitation in preverbal infants. Nature, 415(6873), 755.](https://doi.org/10.1038/415755a) | Abstract + identity | Selective rational imitation by infants; bounded experimental result. |
| 23. [Kirsh, D., & Maglio, P. (1994). On distinguishing epistemic from pragmatic action. Cognitive Science, 18(4), 513-549.](https://doi.org/10.1207/s15516709cog1804_1) | Abstract + identity | Epistemic versus pragmatic actions in Tetris; supports the distinction in that setting. |
| 24. [Friston, K., et al. (2015). Active inference and epistemic value. Cognitive Neuroscience, 6(4), 187-214.](https://doi.org/10.1080/17588928.2015.1020053) | Abstract + identity | Formal active-inference epistemic/extrinsic value account; not empirical proof of all decisions. |
| 25. [Liu, R., Geng, J., Peterson, J. C., Sucholutsky, I., & Griffiths, T. L. (2025). Large language models assume people are more rational than we really are. ICLR 2025.](https://arxiv.org/abs/2406.17055) | Abstract + identity | Behavioral decision modeling with LLMs; scope does not establish personal preference recovery. |
| 26. [Chen, Z., Zhu, D., & Zheng, L. N. (2026). When synthetic users fail: A cross-domain benchmark of LLM-simulated human survey responses.](https://arxiv.org/abs/2607.26348) | Abstract + identity | Synthetic-user evaluation; limitations are part of the paper’s result. |
| 27. [Tooby, J., & Cosmides, L. (2008). The evolutionary psychology of the emotions and their relationship to internal regulatory variables. In M. Lewis, J. M. Haviland-Jones, & L. F. Barrett (Eds.), Handbook of emotions (3rd ed., pp. 114-137). Guilford.](https://cep.ucsb.edu/wp-content/uploads/2023/05/emotionIRVLewisCh8.pdf) | Identity/topic; access caveat above | Evolutionary-psychology chapter; PDF access unresolved, claim support not newly confirmed. |
| 28. [Panksepp, J. (2011). Cross-species affective neuroscience decoding of the primal affective experiences of humans and related animals. PLoS ONE, 6(9), e21236.](https://doi.org/10.1371/journal.pone.0021236) | Abstract + identity | Seven primary systems within Panksepp’s framework; not consensus resolution of all emotion theories. |
| 29. [Tamir, D. I., & Mitchell, J. P. (2010). Neural correlates of anchoring-and-adjustment during mentalizing. PNAS, 107(24), 10827-10832.](https://doi.org/10.1073/pnas.1003242107) | Abstract + identity | Self-anchoring/adjustment in mentalizing; bounded fMRI task evidence. |
| 30. [Bilalić, M., McLeod, P., & Gobet, F. (2008). Why good thoughts block better ones: The mechanism of the pernicious Einstellung (set) effect. Cognition, 108(3), 652-661.](https://doi.org/10.1016/j.cognition.2008.05.005) | Abstract + identity | Expert chess Einstellung effects; evidence for a specific expertise-related bias. |
| 31. [Panksepp, J. (2007). Neurologizing the psychology of affects: How appraisal-based constructivism and basic emotion theory can coexist. Perspectives on Psychological Science, 2(3), 281-296.](https://doi.org/10.1111/j.1745-6916.2007.00045.x) | Abstract + identity | Basic-affect/construction debate; competing interpretations remain. |
| 32. [Shamay-Tsoory, S. G., Aharon-Peretz, J., & Perry, D. (2009). Two systems for empathy: A double dissociation between emotional and cognitive empathy in inferior frontal gyrus versus ventromedial prefrontal lesions. Brain, 132(3), 617-627.](https://doi.org/10.1093/brain/awn279) | Abstract + identity | Lesion double dissociation of empathy components; not all empathy solely mirror-neuron activity. |
| 33. [Hickok, G. (2014). The myth of mirror neurons: The real neuroscience of communication and cognition. W. W. Norton.](https://wwnorton.com/books/9780393089615) | Identity/topic | Book critique of mirror-neuron interpretations; theoretical background. |
| 34. [Rizzolatti, G., & Craighero, L. (2004). The mirror-neuron system. Annual Review of Neuroscience, 27, 169-192.](https://doi.org/10.1146/annurev.neuro.27.070203.144230) | Abstract + identity | Action observation/execution mirror-neuron review; supports a component, not the whole causal chain. |
| 35. [Cook, R., Bird, G., Catmur, C., Press, C., & Heyes, C. (2014). Mirror neurons: From origin to function. Behavioral and Brain Sciences, 37(2), 177-192.](https://doi.org/10.1017/S0140525X13000903) | Abstract + identity | Associative-learning account of mirror neurons; proposed explanation, not settled exclusivity. |
| 36. [Coles, N. A., et al. (2022). A multi-lab test of the facial feedback hypothesis by the Many Smiles Collaboration. Nature Human Behaviour, 6(12), 1731-1742.](https://doi.org/10.1038/s41562-022-01458-9) | Abstract + identity | Multi-lab happiness/facial-feedback tests; does not directly validate the entire fear self-test. |
| 37. [Ekman, P., Levenson, R. W., & Friesen, W. V. (1983). Autonomic nervous system activity distinguishes among emotions. Science, 221(4616), 1208-1210.](https://doi.org/10.1126/science.6612338) | Abstract + identity | Directed facial-muscle construction and autonomic changes; relevant positive support with bounded scope. |
| 38. [Christiano, P., et al. (2017). Deep reinforcement learning from human preferences.](https://arxiv.org/abs/1706.03741) | Abstract + identity | Learning rewards from human trajectory preferences; formal/experimental training setting. |
| 39. [Ouyang, L., et al. (2022). Training language models to follow instructions with human feedback.](https://arxiv.org/abs/2203.02155) | Abstract + identity | Instruction following with human feedback; improvements as well as limits, not only superficial deception. |
| 40. [Wen, J., et al. (2025). Language models learn to mislead humans via RLHF. ICLR 2025.](https://arxiv.org/abs/2409.12822) | Abstract + identity | Learning to mislead evaluators in specified tasks; avoid universalizing. |
| 41. [Kantamneni, S., & Tegmark, M. (2025). Language models use trigonometry to do addition. arXiv.](https://arxiv.org/abs/2502.00873) | Abstract + identity | Reverse-engineered arithmetic mechanism; example of successful analysis, not general impossibility. |
| 42. [Jakesch, M., Hancock, J. T., & Naaman, M. (2023). Human heuristics for AI-generated language are flawed. PNAS, 120(11), e2208839120.](https://doi.org/10.1073/pnas.2208839120) | Abstract + identity | Flawed heuristics in AI-language detection; task-specific evidence. |
| 43. [Vicente, L., & Matute, H. (2023). Humans inherit artificial intelligence biases. Scientific Reports, 13, 15737.](https://doi.org/10.1038/s41598-023-42384-8) | Abstract + identity | Bias persists after biased AI advice in simulated classification; not universal human collapse. |
| 44. [Shumailov, I., et al. (2024). AI models collapse when trained on recursively generated data. Nature, 631(8022), 755-759.](https://doi.org/10.1038/s41586-024-07566-y) | Abstract + identity | Recursive synthetic-data training harms models; not an established identical human mechanism. |
| 45. [Jones, C. R., & Bergen, B. K. (2025). Large language models pass the Turing test.](https://arxiv.org/abs/2503.23674) | Abstract + identity | Conversational Turing-test performance; not longitudinal human detection decline. |
| 46. [Casal, J. E., & Kessler, M. (2023). Can linguists distinguish between ChatGPT/AI and human writing? A study of research ethics and academic publishing. Research Methods in Applied Linguistics, 2(3), 100068.](https://doi.org/10.1016/j.rmal.2023.100068) | Identity/topic | Linguist detection study; not evidence experts decline fastest over time. |
| 47. [Russell, J., Karpinska, M., & Iyyer, M. (2025). People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text. Proceedings of ACL 2025.](https://aclanthology.org/2025.acl-long.267) | Primary paper/page + identity; access caveat above | Experienced users and majority voting performed strongly on 300 English nonfiction articles; bounded task. |
| 48. [Hubinger, E., van Merwijk, C., Mikulik, V., Skalse, J., & Garrabrant, S. (2019). Risks from learned optimization in advanced machine learning systems.](https://arxiv.org/abs/1906.01820) | Abstract + identity | Mesa-optimization risk framework; theoretical analysis, not every system’s observed behavior. |
| 49. [Sharma, M., et al. (2023). Towards understanding sycophancy in language models.](https://arxiv.org/abs/2310.13548) | Abstract + identity | Sycophancy in tested assistants; distinguish measured tendencies from universal inevitability. |
| 50. [Lowe, D. G. (2004). Distinctive image features from scale-invariant keypoints. International Journal of Computer Vision, 60(2), 91-110.](https://doi.org/10.1023/B:VISI.0000029664.99615.94) | Identity/topic | SIFT algorithm; not an account of manually training all computer vision. |
| 51. [Sutton, R. (2019, March 13). The bitter lesson. incompleteideas.net.](https://incompleteideas.net/IncIdeas/BitterLesson.html) | Identity/topic; access caveat above | Scaling/general-methods argument; access unresolved and not proof empathy necessarily follows. |
| 52. [Roelfsema, P. R., & van Ooyen, A. (2005). Attention-gated reinforcement learning of internal representations for classification. Neural Computation, 17(10), 2176-2214.](https://doi.org/10.1162/0899766054615699) | Abstract + identity | Attention-gated reinforcement-learning model of plasticity; not all learning requires conscious attention. |
| 53. [Hutcherson, C. A., & Gross, J. J. (2011). The moral emotions: A social-functionalist account of anger, disgust, and contempt. Journal of Personality and Social Psychology, 100(4), 719-737.](https://doi.org/10.1037/a0022408) | Abstract + identity | Distinguishes moral emotions and incompetence-related contempt; narrower than the essay’s taxonomy. |
| 54. [Harris, L. T., & Fiske, S. T. (2006). Dehumanizing the lowest of the low: Neuroimaging responses to extreme out-groups. Psychological Science, 17(10), 847-853.](https://doi.org/10.1111/j.1467-9280.2006.01793.x) | Abstract + identity | Reduced mPFC response to extreme outgroups; not zero neural activity or complete learning shutdown. |
| 55. [Kruglanski, A. W., & Webster, D. M. (1996). Motivated closing of the mind: “Seizing” and “freezing.” Psychological Review, 103(2), 263-283.](https://doi.org/10.1037/0033-295X.103.2.263) | Abstract + identity | Need-for-closure account of urgency/permanence; framework with bounded evidence. |
| 56. [Roets, A., & Van Hiel, A. (2011). Allport’s prejudiced personality today: Need for closure as the motivated cognitive basis of prejudice. Current Directions in Psychological Science, 20(6), 349-354.](https://doi.org/10.1177/0963721411424894) | Abstract + identity | Need for closure and prejudice; does not imply every closed belief has one cause. |
| 57. [Porter, T., & Schumann, K. (2018). Intellectual humility and openness to the opposing view. Self and Identity, 17(2), 139-162.](https://doi.org/10.1080/15298868.2017.1361861) | Identity/topic | Intellectual humility and openness; measured relationship within study scope. |
| 58. [Pettigrew, T. F., & Tropp, L. R. (2008). How does intergroup contact reduce prejudice? Meta-analytic tests of three mediators. European Journal of Social Psychology, 38(6), 922-934.](https://doi.org/10.1002/ejsp.504) | Abstract + identity | Contact effects mediated by knowledge, anxiety and empathy; not a universal intervention guarantee. |
| 59. [Keltner, D., & Ekman, P. (2015, July 3). The science of “Inside Out.” The New York Times.](https://nytimes.com/2015/07/05/opinion/sunday/the-science-of-inside-out.html) | Identity/topic; access caveat above | Movie-adviser commentary; access unresolved, not primary experimental evidence. |
| 60. [Barrett, L. F., with Barrett, D. J. (2015, July 5). Brain scientist: How Pixar’s ‘Inside Out’ gets one thing deeply wrong. WBUR.](https://wbur.org/news/2015/07/05/brain-scientist-how-pixars-inside-out-gets-one-thing-deeply-wrong) | Identity/topic | Barrett’s first-person critique of the film; competing theoretical position. |
| 61. [Farrell, S. P. (2024, October 31). UC Berkeley professor breaks down the science of ‘Inside Out 2’. UC Berkeley.](https://vcresearch.berkeley.edu/news/uc-berkeley-professor-breaks-down-science-inside-out-2) | Primary paper/page + identity; access caveat above | University account of Inside Out 2 advising; confirms context, not universal emotional taxonomy. |
| 62. [Barrett, L. F. (2017). The theory of constructed emotion: An active inference account of interoception and categorization. Social Cognitive and Affective Neuroscience, 12(1), 1-23.](https://doi.org/10.1093/scan/nsw154) | Abstract + identity | Constructed-emotion account; theoretical alternative, not disproved merely by citing basic-affect work. |
| 63. [Montag, C., & Panksepp, J. (2017). Primary emotional systems and personality: An evolutionary perspective. Frontiers in Psychology, 8, 464.](https://doi.org/10.3389/fpsyg.2017.00464) | Abstract + identity | Primary-emotional-system/personality framework; distinguishes system from culturally elaborated labels. |
| 64. [Tolchinsky, A., Ellis, G. F. R., Levin, M., Kaňková, Š., & Burgdorf, J. (2024). Disgust as a primary emotional system and its clinical relevance. Frontiers in Psychology, 15, 1454774.](https://doi.org/10.3389/fpsyg.2024.1454774) | Abstract + identity | DISGUST proposal/debate; additional-system status remains argued. |
| 65. [van der Westhuizen, D., & Solms, M. (2015). Basic emotional foundations of social dominance in relation to Panksepp’s affective taxonomy. Neuropsychoanalysis, 17(1), 19-37.](https://doi.org/10.1080/15294145.2015.1021371) | Identity/topic | Social dominance as a possible basic system; proposal, not universal confirmation. |
| 66. [Jackson, J. C., et al. (2019). Emotion semantics show both cultural variation and universal structure. Science, 366(6472), 1517-1522.](https://doi.org/10.1126/science.aaw8160) | Abstract + identity | Emotion semantics vary and share structure across languages; does not alone choose a neural taxonomy. |
| 67. [Nisbett, R. E., & Cohen, D. (1996). Culture of honor: The psychology of violence in the South. Westview Press (Routledge reissue, 2018).](https://doi.org/10.4324/9780429501142) | Identity/topic | Culture-of-honor research; specific cultural evidence rather than all cultural effects. |
| 68. [Anderton, E. (2024). Pixar’s Inside Out 2 almost included a complicated German emotion: Here’s why it got cut. /Film.](https://slashfilm.com/1563120/why-pixar-inside-out-2-cut-german-emotion-character-schadenfreude) | Identity/topic | Film-production reporting on a removed character; not neuroscience evidence. |
| 69. [Linnet, J. T. (2011). Money can’t buy me hygge: Danish middle-class consumption, egalitarianism, and the sanctity of inner space. Social Analysis, 55(2), 21-44.](https://doi.org/10.3167/sa.2011.550202) | Identity/topic | Ethnographic account of hygge; supports cultural context within that study. |
| 70. [Phillips, J., Morris, A., & Cushman, F. (2019). How we know what not to think. Trends in Cognitive Sciences, 23(12), 1026-1040.](https://doi.org/10.1016/j.tics.2019.09.007) | Abstract + identity | Selection of likely/valuable possibilities; bounded cognitive account. |
| 71. [Fredrickson, B. L. (2001). The role of positive emotions in positive psychology: The broaden-and-build theory of positive emotions. American Psychologist, 56(3), 218-226.](https://doi.org/10.1037/0003-066X.56.3.218) | Identity/topic | Broaden-and-build theory of positive emotions; not a general adrenaline/stress result. |
| 72. [Alcaro, A., & Panksepp, J. (2011). The SEEKING mind: Primal neuro-affective substrates for appetitive incentive states and their pathological dynamics in addictions and depression. Neuroscience & Biobehavioral Reviews, 35(9), 1805-1820.](https://doi.org/10.1016/j.neubiorev.2011.03.002) | Abstract + identity | SEEKING framework and neurobehavioral review; not a personal inferred value estimate. |
| 73. [Tooby, J., & Cosmides, L. (1992). The psychological foundations of culture. In J. H. Barkow, L. Cosmides, & J. Tooby (Eds.), The adapted mind (pp. 19-136). Oxford University Press.](https://cep.ucsb.edu/wp-content/uploads/2023/05/pfc92.pdf) | Identity/topic; access caveat above | Foundational evolutionary-psychology chapter; PDF access unresolved. |
| 74. [Blackmore, S. (1999). The meme machine. Oxford University Press.](https://global.oup.com/academic/product/the-meme-machine-9780192862129) | Identity/topic; access caveat above | Memetic framework book; challenge page prevents renewed content verification. |
| 75. [Yudkowsky, E. (2007, November 11). Adaptation-executers, not fitness-maximizers. LessWrong.](https://lesswrong.com/posts/XPErvb8m9FapXCjhA/adaptation-executers-not-fitness-maximizers) | Identity/topic | Conceptual adaptation-executer argument; not a measured universal brain objective. |
| 76. [Gao, G., Taymanov, A., Salinas, E., Mineiro, P., & Misra, D. (2024). Aligning LLM agents by learning latent preference from user edits.](https://arxiv.org/abs/2404.15269) | Abstract + identity | Latent preferences from edits evaluated with simulated users; not real-person ground truth. |
| 77. [Masatlioglu, Y., Nakajima, D., & Ozbay, E. Y. (2012). Revealed attention. American Economic Review, 102(5), 2183-2205.](https://doi.org/10.1257/aer.102.5.2183) | Abstract + identity | Revealed-attention identification under choice-model assumptions; not arbitrary prose inference. |
| 78. [Anderson, B. A., Laurent, P. A., & Yantis, S. (2011). Value-driven attentional capture. PNAS, 108(25), 10367-10371.](https://doi.org/10.1073/pnas.1104047108) | Abstract + identity | Learned reward-driven attentional capture; not all attention revealing one setpoint. |
| 79. [Schmidhuber, J. (2009). Driven by compression progress: A simple principle explains essential aspects of subjective beauty, novelty, surprise, interestingness, attention, curiosity, creativity, art, science, music, jokes. In Anticipatory Behavior in Adaptive Learning Systems (LNCS 5499, pp. 48-76). Springer.](https://arxiv.org/abs/0812.4360) | Abstract + identity | Compression-progress theory of curiosity; proposed account, not a universal demonstrated law. |
| 80. [Poli, F., Serino, G., Mars, R. B., & Hunnius, S. (2020). Infants tailor their attention to maximize learning. Science Advances, 6(39), eabb5053.](https://doi.org/10.1126/sciadv.abb5053) | Abstract + identity | Infant learning-progress sensitivity; task-specific evidence. |
| 81. [Awh, E., Belopolsky, A. V., & Theeuwes, J. (2012). Top-down versus bottom-up attentional control: A failed theoretical dichotomy. Trends in Cognitive Sciences, 16(8), 437-443.](https://doi.org/10.1016/j.tics.2012.06.010) | Abstract + identity | Selection history alongside goals and salience; multiple drivers of attention. |
| 82. [Caplin, A., & Dean, M. (2015). Revealed preference, rational inattention, and costly information acquisition. American Economic Review, 105(7), 2183-2203.](https://doi.org/10.1257/aer.20140117) | Abstract + identity | Optimal costly-information acquisition under specified observations; not unqualified latent-value recovery. |
| 83. [Jara-Ettinger, J., Gweon, H., Schulz, L. E., & Tenenbaum, J. B. (2016). The naïve utility calculus: Computational principles underlying commonsense psychology. Trends in Cognitive Sciences, 20(8), 589-604.](https://doi.org/10.1016/j.tics.2016.05.011) | Abstract + identity | Naive utility calculus in social inference; costs/benefits and model assumptions matter. |
| 84. [Frederick, S., Loewenstein, G., & O’Donoghue, T. (2002). Time discounting and time preference: A critical review. Journal of Economic Literature, 40(2), 351-401.](https://doi.org/10.1257/002205102320161311) | Identity/topic | Time-discounting review with heterogeneous evidence; not a universal personal discount parameter. |
| 85. [Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993). The role of deliberate practice in the acquisition of expert performance. Psychological Review, 100(3), 363-406.](https://doi.org/10.1037/0033-295X.100.3.363) | Identity/topic | Deliberate-practice account; not a validated timestamp for any individual decision. |
| 86. [Keramati, M., & Gutkin, B. (2014). Homeostatic reinforcement learning for integrating reward collection and physiological stability. eLife, 3, e04811.](https://doi.org/10.7554/eLife.04811) | Abstract + identity | Physiological homeostatic reinforcement learning; extension to abstract cultural values remains a proposal. |
| 87. [Solms, M. (2019). The hard problem of consciousness and the free energy principle. Frontiers in Psychology, 9, 2714.](https://doi.org/10.3389/fpsyg.2018.02714) | Abstract + identity | Free-energy/consciousness theoretical account; not validation of these UI measurements. |
| 88. [Baas, M., De Dreu, C. K. W., & Nijstad, B. A. (2011). Creative production by angry people peaks early on, decreases over time, and is relatively unstructured. Journal of Experimental Social Psychology, 47(6), 1107-1115.](https://doi.org/10.1016/j.jesp.2011.05.009) | Identity/topic | Anger and time-dependent creativity benefits; not an isolated adrenaline mechanism. |
| 89. [Douceur, J. R. (2002). The Sybil attack. In Peer-to-Peer Systems (IPTPS 2002), LNCS 2429, 251-260. Springer.](https://doi.org/10.1007/3-540-45748-8_24) | Identity/topic | Sybil identity-attack analysis; not a test of the complete proposed anti-capture design. |
| 90. [Armstrong, S., & Mindermann, S. (2018). Occam’s razor is insufficient to infer the preferences of irrational agents. NeurIPS 2018.](https://arxiv.org/abs/1712.05812) | Abstract + identity | Reward/planner non-identifiability without normative assumptions; more observations alone do not remove it. |
| 91. [Cao, H., Cohen, S. N., & Szpruch, L. (2021). Identifiability in inverse reinforcement learning. NeurIPS 2021.](https://arxiv.org/abs/2106.03498) | Abstract + identity | Reward identifiability under structured conditions; not arbitrary observation or fairness guarantees. |
| 92. [Parr, T., Pezzulo, G., & Friston, K. J. (2022). Active inference: The free energy principle in mind, brain, and behavior. MIT Press (open access).](https://doi.org/10.7551/mitpress/12441.001.0001) | Abstract + identity | Active-inference mathematical framework; not admission of this implementation’s inferences. |
| 93. [Hadfield-Menell, D., Dragan, A., Abbeel, P., & Russell, S. (2016). Cooperative inverse reinforcement learning. NeurIPS 2016.](https://arxiv.org/abs/1606.03137) | Abstract + identity | Cooperative inverse-reinforcement-learning framework; not a complete safety guarantee. |
| 94. [Frankfurt, H. G. (1971). Freedom of the will and the concept of a person. The Journal of Philosophy, 68(1), 5-20.](https://doi.org/10.2307/2024717) | Identity/topic | Philosophical second-order desires; not an empirical preference measurement method. |
| 95. [ToMpathy. Open-source repository, GitHub (EmotiveAutomaton).](https://github.com/EmotiveAutomaton/tompathy) | Identity/topic | Owner repository pointer, retained only in the closing project invitation. |
| 96. [Sounding Line. Open-source research repository, GitHub (EmotiveAutomaton).](https://github.com/EmotiveAutomaton/sounding-line) | Identity/topic | Owner repository pointer, retained only in the closing project invitation. |
| 97. [Ghost Scale Sim. Open-source simulation repository, GitHub (EmotiveAutomaton).](https://github.com/EmotiveAutomaton/ghost-scale-sim) | Identity/topic | Owner repository pointer, retained only in the closing project invitation. |

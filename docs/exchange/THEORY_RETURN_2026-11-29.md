Nov 27 at 09:20 PT, Spark is running Q27 (13,580/43,021), the workstation GPU is running G12 (12,560/43,021), and the card queue is running TP70 grouping block 26 of 40. The workstation can read both held corpora. The last Spark check found no in-place route to the talk pages or recalled stories.

# Two-day engine return · November 27–29

## Against, and clear

Worry’s within-author slope exceeded the 99.5th percentile of both control families. Four isotropic and three rotated heads equaled or exceeded it, so the prediction that none would do so failed. In a separate repeatability test, the difference between worry and median tag repeat was smaller than predicted, at percentile 0.8 of rotated sets. In the whole-author blog return, curiosity’s correlation with competence fell below 0.30 between authors and was positive within authors. Both of those predictions missed.

## Registered predictions

The table covers 35 registered predictions. TP62 met both directional criteria on the fixed texts, including after assigned stems were excluded. The whole-writer sampling interval is unavailable. TP61 still has outstanding components. [TP78 family table](result-sheets/TP78.md)

## Readouts

| Card | Recorded state | Sheet or registered protocol |
|---|---|---|
| TP71 · Display and exports | Landed. Acceptance is shown beside Respect. Wanting and amusement are the reader labels. SHAME carries its scope flag. The Meaning row is hidden. | [TP71 change list](result-sheets/TP71.md) |
| TP61 · Random-head controls | Worry minus median tag repeat was 0.218, below the 0.229–0.299 rotated band. The word-specific estimates fell inside the rotated band for all eight words. Three met the 200-author minimum. Worry’s slope of 0.12711 exceeded both 99.5th percentiles, and seven of 7,600 individual heads reached it. | [TP61](result-sheets/TP61.md) |
| TP62 · Content and style | Trained word accuracy was 35.21%, above every rotated set. Writer accuracy was 1.76%, below the rotated median of 2.43%. Both findings persisted after removing assigned stems. | [TP62](result-sheets/TP62.md) |
| TP70 · Blind grouping | Running on 24,850 chat texts and 5,426 usable blog author means. Each control repeats the comparison in 100 whole-writer or whole-author resamples. | [TP70](result-sheets/TP70.md) |
| TP64 · Channel checks | The three source tables and research SHAME rescore are registered behind TP70. | [TP64](result-sheets/TP64.md) |
| TP65 · Coming or landed | The original within-report comparison and its two writer-rating fields are registered. Further sources depend on Q29–Q31. | [TP65](result-sheets/TP65.md) |
| TP77 · Reader agreement | Original sentence comparisons precede new marks. The standing-mark comparison needs matched B and W responses. | [TP77](result-sheets/TP77.md) |
| TP63 · Outside scores | The event header contains all ten inventory items. The held essay header has empathy and distress and contains no trait columns. The essay arm is unavailable. | Section 4 |
| TP68 · Embarrassment | Registered on the original sources. | Section 4 |
| TP69 · Competence and Respect | Registered on the saved profiles. | Section 4 |
| TP66 · Order during loss | The short arm precedes the blog and story arms. | Section 4 |
| TP67 · Whose rise | The first comparison uses saved inputs. The three-way comparison needs Q27. | Section 4 |
| TP72 · Sealed bundle v2 | Pending its place in the section 6 queue, two invented-data rehearsals and a verified manifest. Sounding Line retains the TP58 rehearsal bundle. | Section 4 |
| TP73 · Whole authors | Q24 returned 2,993 whole authors. The registered competence arm is complete. Its curiosity contrasts miss both bars. Other arms remain open. | [TP73](result-sheets/TP73.md) |
| TP74 · Earned standing | Depends on Q27 and the agreement of the relevant fields. | Section 4 |
| TP75 · Worry and time direction | Depends on Q31’s blog sentence sample. | Section 4 |
| TP76 · Long recalled stories | The V3 header is readable on the workstation. Spark cannot read the table at its held location. No story has entered this job. | Section 4 |
| TP78 · Family table | Open. Includes registered predictions with no measurement yet. | [TP78](result-sheets/TP78.md) |
| TP79 · Anger answered by rank | The workstation opened the held archive directory and its member index. Q33 needs Spark access in place. | Section 4 |

## GPU jobs

Pilot times are wall seconds after loading. Observed totals include job startup and release where available. A projection uses the first 100 texts and is a sizing measurement.

| Job | Packet hours | First 100 seconds | Projected hours | Observed status or hours |
|---|---:|---:|---:|---|
| Q26 · Throughput | <1 | 53.01 serial, 52.98 at two, 53.28 at four | 0.088 for 600 at the serial pilot rate | Completed in 0.093 hours. Serial retained. |
| Q34 · Worry | <1 | 0.422 | 0.068 | Completed in 0.0062 hours after the import repair. |
| Q27 · Standing | 10.8 | 53.74 | 6.42 | Running serially. |
| Q28 · Event features | 2.0 | — | — | Registered behind Q27. |
| Q32 · Third reader and rewordings | 2.0 | — | — | Registered behind Q28. The extended memory rule applies only to C on this job. |
| Q29 · Sentences | 3.0 | — | — | Both machines verified the same 17,755 held-out forum sentences and 21,247 ISEAR sentences. Spark’s native listener is waiting for Q32’s release. |
| Q31 · Blog loss and timing | 9.8 | — | — | Roster preparation ranks posts with at least six windows by mean SADNESS. A separate seeded sample takes 20 openings from each of 500 authors with at least 80 posts. Sizing awaits the actual sentence census and timed pilot. |
| Q30 · Long stories | 9.9 | — | — | In-place Spark source unavailable. |
| Q33 · Talk pages | First 1,000 to size | — | — | In-place Spark source unavailable. |
| G12 · Standing | 4–6 | 66.58 | 7.96 | Running. |
| G14 · Event features | <1 | — | — | Follows G12. |
| G13 · Sentence and loss comparisons | First 100 to size | — | — | The workstation’s sentence listener is waiting for G14’s release. The other comparisons depend on their own inputs. |
| G15 · Workstation filler | Up to 21.6 | — | — | Whole-author selection and exact G11 reuse required. |
| Q24b · Spark filler | Time remaining | — | — | Native dispatcher verified at offset 207,795. Parked while Q27 owns the GPU. |

**Q26.** The three widths completed the same 200 texts at 112.59, 112.58 and 113.47 texts per minute. All 173 valid serial answers matched literally at both higher widths. The other 27 violated the earned-rise field rule. A width needed 200 valid matches and higher throughput. Further concurrency work would require a separately approved server trial or a separately registered prompt; neither change was made. [Verified Q26 aggregate](../../engine/validation/readers-q26-throughput-2026-11.json)

**Q34.** The original process stopped before scoring because its interpreter could not import SciPy. The retry used the earlier offline dependency directory and the identical frozen worker and inputs. It returned 6,600 event scores, 5,014 Q11 sentence scores and 46,543 Q12 sentence scores. All 591 returned artifacts and the GPU release were verified. Source receipt `d1194417e2159f036f5856889427106c0f8aa4d4f6782dcfb8be68d53167da5c`.

**TP77.** Whose doing, change in standing, visibility and earned rise are being measured independently by B and W. Their validity counts and Q26’s repeated B answers do not measure cross-reader agreement. New marks await their field-specific kappa checks.

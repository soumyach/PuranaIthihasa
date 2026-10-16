# Ganapatya research checkpoint

This is a verified seed graph, not a claim of complete Gaṇeśa/Mudgala extraction. JSON is `gp.json`; exact witnesses, chapter/verse locators, evidence and resumable tasks are stored there. Source-scoped IDs deliberately keep the Gaṇeśa Purāṇa, embedded Gītā witness and Mudgala identities separate.

## Discovery and reading

Three source records: Gaṇeśa Purāṇa, Mudgala Purāṇa, and Gaṇeśa Gītā as an embedded text with a separately encoded witness. Sixteen witness records include twelve Sanskrit digital witnesses, the Wisdomlib abridgment, an Archive scan landing page, a commercial Bailey publication and a publisher description.

The [Wisdomlib Gaṇeśa Purāṇa](https://www.wisdomlib.org/hinduism/book/the-ganesha-purana) is explicitly **abridged** and indexes only introduction plus chapters 1–10. It cannot support complete-corpus extraction.

[Sanskrit Upāsanā](https://sanskritdocuments.org/doc_purana/gaNeshapurANam1.html) has 92 chapters and [Krīḍā](https://sanskritdocuments.org/doc_purana/gaNeshapurANam2.html) has 155 in the examined digital witnesses. All 247 chapter titles are inventoried, preserving the text's spelling and possible typographical errors. Index readings are not narrative readings. Upāsanā 46 indexes the Sahasranāma; the Krīḍā index labels 138–148 as Gītā sections.

The full nine-khaṇḍa Mudgala range inventory is verified against each terminal colophon:

| Khaṇḍa | Name | Chapters |
|---|---|---:|
| 1 | Vakratuṇḍacarita | 54 |
| 2 | Ekadantacarita | 74 |
| 3 | Mahodaracarita | 51 |
| 4 | Gajānanacarita | 52 |
| 5 | Lambodaracarita | 45 |
| 6 | Vikaṭacarita | 45 |
| 7 | Vighnarājacarita | 16 |
| 8 | Dhūmravarṇacarita | 50 |
| 9 | Yogacarita | 41 |

The sum is 428, independently stated in 9.41.58 alongside nine khaṇḍas. The **ninth Yogacarita must not be omitted** by reducing Mudgala to eight incarnation books. All individual Mudgala chapter titles still need indexing; chapter-number ranges are recorded now. [Purāṇa directory](https://sanskritdocuments.org/purana/) provides verified links to all nine files and scan candidates.

[Standalone Gaṇeśa Gītā](https://sanskritdocuments.org/doc_giitaa/ganeshagita.html) indexes eleven chapters and 414 verses. Its 1.1–6 frame was directly read and extracted: Vyāsa/Sūta transmission and Gajānana teaching Vareṇya. Chapter headings and wording differ from the embedded index; automatic equivalence remains inappropriate until collation.

## Narrative extraction

Zero whole chapters are marked exhaustively extracted. Two Sanskrit Mudgala chapters (1.23–24) were read in full but have selective narrative extraction. Two small, explicitly bounded Gaṇeśa Purāṇa hearing arcs are complete:

- Krīḍā 155.24–32: a speech-impaired sage hears Brahmā reciting to Lomaśa, gains speech, becomes a reciter, obtains descendants and reaches Gaṇeśa’s abode. Four source-ordered events.
- Krīḍā 155.33–45ab: Saṃvaraṇa’s unsuccessful prior efforts, hearing from the sage, rewards, offspring, devotion and final state; his sister repeats the hearing and reaches her final outcome. Three events. The boundary ends after the sister’s final abode in the first half of verse 45; the Sagara example begins in verse 45cd.

Mudgala 1.23–24 has five events covering Matsara’s origin, Earth’s nurture, initiation, marriage, Śukra’s instruction, austerity, Śiva’s full compound boon, named sons and departure from Earth after demon advice. The **Matsara–Vakratuṇḍa opponent arc remains PARTIAL**: army, conquests, manifestation, battles, surrender and final outcome still require reading. Every festival attendee and hymn epithet/iconographic detail has not been converted into entities, so these chapters remain partly extracted.

Matsara’s boon distinguishes motive, worshipped deity, five-syllable instruction, Pāśupata initiation, thousand divine years without food, request, blanket grant, protection domain, duration and later effects. Counter and activation trigger remain null. Counter is unexamined; trigger is unstated in the read grant. Earth is foster mother; Indra is the seed-origin father. Madakarā, Durbuddhi, Sundarapriya and Viṣayapriya have separate supported family edges. Demon remarks about Jalandhara remain reported speech, not an objectively asserted cross-text victory.

## Counts and verification

35 entities, 22 assertions, 22 relationships, 1 compound boon, 12 events, 3 story spines (2 complete bounded examples, 1 partial wider arc), 12 passage records and 17 evidence records. The passages include metadata excerpts; passage completeness never implies full-chapter completeness.

Local checks passed for unique IDs, source/witness/passage/evidence links, relationship endpoints, boon participants and field evidence, event participants and powers, and story sequence order. `gp_validation.json` records the check. VERIFIED means checked against the accessible digital witness; Sanskrit expert review and print collation remain pending.

## Open discrepancies and gaps

- [AITM 74 publisher description](https://www.motilalbanarsidass.com/en-us/products/the-ganesa-purana-pt-1-upasana-khanda-aitm-vol-74-ancient-indian-tradition-and-mythology) says Gītā chapters 139–150; SD index says 138–148. This is a verified locator discrepancy, not a proven manuscript variant.
- [Publisher corpus description](https://www.motilalbanarsidass.com/products/the-ganesa-purana) gives 4093 + 6986 verses; SD terminal colophons give 4096 + 7021. Do not silently reconcile or infer missing verses.
- Base print editions of SD transcriptions remain unidentified. Footers identify Manish Gavkar (GP), Yash Khasbage (Mudgala), and Sunder Hattangadi (Gītā), not a critical edition.
- SD files permit personal study/research but restrict promotional/commercial copying or reposting without permission. Automated bulk extraction permission is NOT_ESTABLISHED. No full text dumps retained.
- Full Upāsanā/Krīḍā narrative reading, full Mudgala, full Gītā extraction, every individual Mudgala chapter title and actual print scan collation remain open.
- Other-Purāṇa Gaṇeśa passages and Mahābhārata scribe-recension distinctions are queued. No remembered epic account was inserted.
- A Viśvāmitra encounter/boon excerpt at Mudgala 1.54.14–32 was directly read through the browser but not extracted in this checkpoint; do not count it as graph coverage.

The ten queue items preserve these tasks. Wider complete 18-Mahāpurāṇa/Upapurāṇa/epic expansion is deferred per the user's instruction; relevant passages named in the initial mission remain in current scope.

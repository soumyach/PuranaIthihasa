# Khatakshetra Autonomous Book Factory — PR11

## Result

PR11 executed the exact authorized DM04 private visual pilot and stopped after two host-tool image operations. Both real PNGs were preserved and hash-bound to their requests and exact PR7 reference inputs. A separate image-capable reviewer inspected the original pixels and returned `FIX` for page 1 and `ESCALATE` for page 4. Neither image is eligible for page composition, so no preview page or PDF was created.

The durable campaign state is:

`REVIEWED_FIX_REQUIRED_CAMPAIGN_COMPLETE_NO_RETRY`

No retry, full-book production, publication, deployment, push or merge occurred.

## 1. Baseline, branch and authorization

- Baseline commit: `4c28c2524838582eb471cf9f620655805ac6bc72`.
- Branch: `feature/book-factory-controlled-visual-pilot-pr11`.
- Campaign subject: `5a5b7c2a606f47a9b72ef001f19ef9c8736f4b328d2434dae08c5d0b08c061d7`.
- Approval: `approval-9ac3c1c3bc2a352021552a8d`, exact-hash, non-inheritable, private/internal visual testing only.
- Maximum operations: two total and one per selected page.
- PR6 attempt counters remained exhausted and were not reset.

## 2. Actual operations and files

| Page | Operation | Request hash | Exact PNG | SHA-256 | Size |
| --- | --- | --- | --- | --- | --- |
| `page-27d143ae995bf60742b65c5b` | edit | `cf5610b02700837ef6bee853d645df6b66f1743c28e2ac8de581f401345c81e5` | `books/DM04/production-pilot/images/page-27d143ae995bf60742b65c5b/v0001.png` | `5a8d154988f7f9b67ff927ab8b3d4e8b9fe96e6d7a0c99be4d3da9ef6fbdecf7` | 1086 × 1448 |
| `page-5316f7271234e4ab31991528` | generation | `7e24e70043a86cf13a3be457c4c1c095fa2821d852c2e82ff970fafea6f065f3` | `books/DM04/production-pilot/images/page-5316f7271234e4ab31991528/v0001.png` | `cfac6ab6666e84fcd79d1fccd1aa5273adf4e28185d823cd92847131b7802819` | 1086 × 1448 |

Both images pass PNG CRC and pixel-stream validation. There were no retries, variants or additional image operations.

## 3. Reference-image receipts

Page 1 submitted four ordered image inputs:

1. Edit target, rejected PR6 source only: `578e0fcdb4dcf016b7b85a50736e498859528560f569885ddf0f8060003f32fc`.
2. Reference A, series identity, `kgs-satya-p01.png`: `15c2cfaf37a379c8042105051ac432e3aba5ccc0594eef43dc95d157cee53a1b`.
3. Reference B, comic composition, `kgs-dm08-p09.png`: `26f5a3d7fdc9c9432f0a793c6b50711a2bb4b1157cde79a7534c542a6c9bfa2d`.
4. Reference D, forest environment, `kgs-satya-p02.png`: `a0fa07b60d1b8b128b541300f3fb5e26358863e3153c719e2d0aacb0fd7858dd`.

Page 4 submitted two ordered image inputs:

1. Reference A, series identity, `kgs-satya-p01.png`: `15c2cfaf37a379c8042105051ac432e3aba5ccc0594eef43dc95d157cee53a1b`.
2. Reference B, manifestation composition, `kgs-dm08-p12.png`: `d46f264508cf0283e56f14d1a02b6d66b37a49b8e2e66c7b3f31f16764fadfe4`.

Reference C did not exist as a human-approved DM04 exact character asset. Page 4 also had no human-approved exact Reference D setting image. Neither was invented. The immutable image receipt hashes are `b666dd73ae79b3f5017107518b5f21ee86a2ba0e8b61fd5818fc58e1baba6900` and `a71161c00cb5b3b83154117035fecb8e0a5e7c8a1a9b76848d7cb8d4d43c9e12`.

## 4. Independent actual-pixel review

Reviewer `/root/pr11_visual_reviewer` was separate from producer `/root`, image-capable, and inspected the two PNGs and relevant PR7 references at actual reading size.

### Page 1 — `FIX`

The scene strongly passes source fidelity, cultural authenticity, character continuity, narrative clarity, artistic quality and reference alignment. It contains the correct three unarmed characters, natural speaker/listener behavior and no prohibited benchmark story transfer.

Blocking issues:

- It is one full-bleed scene, not the locked two-panel clean-art unit.
- Tree and hut detail occupy the required narration and Medhas-dialogue safe regions.

Review hash: `29605df38b5d27ed16cadde25db723731b5ae1f07c28ed9c863a9dee54fca7c4`.

### Page 4 — `ESCALATE`

The scene has polished devotional-storybook rendering, a clear central Devi, no weapon, gift, lion, mount, chariot, battlefield, Kali content or benchmark story transfer.

Blocking issues:

- The one-to-one named donor-to-body-region radiance map is not auditable from the pixels.
- Repeated donor identities and sacred attributes require qualified religious-iconography review.
- Prohibited halo-like disks appear behind donors.
- Floating palace architecture conflicts with the locked abstract manifestation space.
- The upper narration region is occupied.

Review hash: `c6bc6f6c6dd3a64bed96be6cb2b60f66602562f2b5e968860ecee54972a923e2`.

The factory persisted non-executable, page-local correction requests. They explicitly authorize no retry, leave zero campaign operations, preserve the other page and keep PR6 counters unchanged.

## 5. Composition and PDF gates

Both images are preview-ineligible because their independent reviews are non-PASS. PR8 composition was therefore not invoked. No page preview and no PDF proof were created. The PDF state remains `NOT_CREATED_ART_AND_REVIEW_GATES_BLOCKED`.

## 6. Billing and allowance observations

- Tool: built-in `image_gen.imagegen` through the Codex host session.
- API key supplied: no.
- External provider authorization requested: no.
- Paid billing requested by the tool: no.
- Automatic credit purchase requested: no.
- Purchased-credit balance before, between and after operations: absent / `0`.
- Weekly Codex usage displayed before, between and after operations: `0%`.
- Ordinary usage remained allowed; spend control was not reached.
- Separately billed provider calls recorded: zero.
- Incremental USD cost: `UNKNOWN_NOT_EXPOSED`.

The factory intentionally records the direct monetary amount as unknown rather than asserting USD 0.00. The observable evidence supports included-allowance-first execution with no credit or external-billing prompt, but the host image interface does not expose a per-operation price or a positive zero-spend guarantee.

## 7. Durable controls added

Factory `0.11.0` adds CLI-controlled imports for exact production images and receipts, independent actual-pixel review requests and responses, page-local no-retry correction requests, cost-unknown accounting, exact prompt/reference binding, the two-operation ceiling, reviewer independence and fail-closed composition/PDF gates.

## 8. Remaining blockers

1. Page 1 requires a newly authorized two-panel recomposition with protected lettering regions.
2. Page 4 requires qualified religious-iconography input, a human-approved donor identity map, explicit donor-to-body routing, removal of halo disks and palace architecture, and a protected narration zone.
3. The current campaign has no remaining image operations; any correction requires separate authorization.
4. Human visual-style approval is absent.
5. Publication rights, full-arc source/theological review, font licensing and print/export-profile blockers remain open.

DM08 and the source graph remain unchanged. No next book was started.

## 9. Verification

- PR10 + PR11 targeted tests: 32/32 pass.
- Complete Book Factory Python suite: 183/183 pass.
- `python -m book_factory validate`: pass.
- Book Factory boundary checks: pass; source graph clean and registered reference hashes valid.
- `git diff --check`: pass.

The default system Python lacks Pillow, so the bare `./factory validate` entrypoint reports that optional runtime dependency. The same factory command passed with the repository's bundled Codex Python runtime, which supplies the documented workspace dependencies.

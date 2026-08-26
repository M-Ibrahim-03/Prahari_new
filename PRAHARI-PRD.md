# PRAHARI
# Product Requirements Document

### प्रहरी — *The Sentinel*
### Predictive Crop Health Intelligence for Indian Smallholders

**Version 2.0 · Master PRD · Team Paradox · PS 302**

---

## HOW TO READ THIS DOCUMENT

This is the **single source of truth** for PRAHARI. Everything anyone needs — a developer, a designer, a judge, an ML engineer, a domain scientist, a new team member joining tomorrow — is in this one file. There are no companion documents. Nothing is assumed from prior conversations.

**If you have 5 minutes:** read §1 (Vision), §5 (Product Principles), then jump to **PART VII — The Plain-Language Summary** at the very end.

**If you are building:** read PART II (Product), PART III (Experience), PART IV (Technology) in order. Every feature has requirements, edge cases, and acceptance criteria.

**If you are challenging it:** read PART V (Rigour). It contains the validation methodology, the honest limitations, and the list of claims we have not yet verified.

**Notation used throughout:**

| Tag | Meaning |
|---|---|
| 🔴 | **Load-bearing.** Get this wrong and something important breaks. |
| ⚠️ | A trap that has silently broken real implementations. |
| 💡 | A design insight — the *why* behind a decision. |
| `[VERIFY]` | A factual claim we have not yet independently confirmed. Listed in §43. |
| `[HUMAN]` | Work no amount of code or AI can do. A person must do it. |
| `[P0]` `[P1]` `[P2]` | Priority. P0 = the product does not exist without it. |

---

# ═══════════════════════════════════════
# PART I — STRATEGY
# ═══════════════════════════════════════

# 1. VISION & POSITIONING

## 1.1 The one sentence

> **PRAHARI tells a smallholder farmer what is about to go wrong on their own field — in the next 7 days, with the exact hours to act, spoken aloud in their own language, at zero cost.**

Four things have to be true at once for that sentence to hold, and they are the four hard problems of this project:

1. **"their own field"** — the farmer must be able to point at their land and have the system understand it (§7).
2. **"about to go wrong"** — a forecast, computed from published agro-meteorological science plus satellite observation (§8, §9).
3. **"the exact hours to act"** — a specific spray window, not a risk level (§13).
4. **"spoken aloud in their own language"** — voice-first delivery that works with no internet (§14).

## 1.2 What PRAHARI is

PRAHARI is a **predictive crop health intelligence platform**. It combines published agro-meteorological science, satellite earth observation, machine learning, and a grounded AI agronomist to answer four questions for an individual smallholder field:

1. **What is coming?** — Disease and pest pressure forecast 7 days ahead, at field resolution.
2. **When exactly do I act?** — A specific window of hours when spraying will work, accounting for rain, wind, and temperature.
3. **Why should I believe you?** — Every prediction traces to a published model, with a public accuracy record.
4. **What do I do, in my language, out loud?** — Voice-first advisory in the farmer's own language, that works with no internet.

It is **not** a diagnosis app, a marketplace, a chatbot, or a dashboard. It is an early-warning service with an agronomist attached.

## 1.3 Where PRAHARI acts on the timeline

A crop disease has a life cycle, and there are several legitimate places to intervene in it. PRAHARI chooses one specific window and builds everything around it: **the days before infection occurs.**

```
        ┌─────────────────────────────────────────────────────────┐
        │              THE INTERVENTION TIMELINE                  │
        └─────────────────────────────────────────────────────────┘

  T-7d        T-3d        T-0          T+3d        T+7d       T+21d
   │           │           │            │           │           │
   │           │      infection     first       lesions      yield
   │           │       occurs      symptom     spreading      loss
   │           │           │        visible        │        realised
   │           │           │            │           │           │
   ▼           ▼           ▼            ▼           ▼           ▼
 ┌────────────────────┐   │   ┌──────────────────────┐   ┌──────────────┐
 │  PREVENTION WINDOW │   │   │  DETECTION WINDOW    │   │  RECOVERY /  │
 │  ← PRAHARI         │   │   │                      │   │  INSURANCE   │
 │                    │   │   │  Diagnosis, ID of    │   │              │
 │  Forecast risk.    │   │   │  what is present,    │   │  Loss        │
 │  Protectant spray  │   │   │  curative treatment, │   │  assessment, │
 │  is already on the │   │   │  containment.        │   │  claims.     │
 │  leaf when spores  │   │   │                      │   │              │
 │  arrive.           │   │   │  Genuinely useful —   │   │  Also        │
 │                    │   │   │  and a valuable      │   │  necessary.  │
 │  Cheapest, most    │   │   │  ground-truth        │   │              │
 │  effective, and    │   │   │  signal for us       │   │              │
 │  the least served. │   │   │  (§12, §16).         │   │              │
 └────────────────────┘   │   └──────────────────────┘   └──────────────┘
```

💡 **Why this window:** for a **polycyclic** pathogen — one that completes multiple infection cycles in a season — each cycle multiplies the inoculum load. Acting one cycle earlier is not a linear improvement; it is a compounding one. And the chemistry is different: **protectant** fungicides applied to a healthy leaf are cheaper and more effective than **curative** treatment of established infection.

The prevention window is also the least served, for a simple and non-judgemental reason: **acting before symptoms requires a forecast, and a forecast requires infrastructure** — gridded weather, a validated model, and a delivery channel to a specific field. Detection only requires a camera. Prevention is the harder engineering problem, which is why there is room to build here.

🔴 **The other windows are not competitors — they are inputs.** Detection produces the ground truth that validates and corrects our forecasts (§16, §26.5). A farmer who photographs a confirmed lesion is doing something genuinely valuable for the model. The architecture treats detection as a **partner capability**, and §12 builds it in for exactly that reason.

## 1.4 Goals

| ID | Goal | Measured by |
|---|---|---|
| **G1** | Warn a farmer 48–120 hours before conditions favour infection | Mean lead time on validated outbreak events |
| **G2** | Convert warnings into actions, not anxiety | % of alerts that include a valid spray window |
| **G3** | Make every prediction traceable and every claim checkable | Public accuracy page + tamper-evident alert ledger |
| **G4** | Work for a farmer who cannot read, has 2G, and shares a phone | Voice completion rate; offline session share |
| **G5** | Let a farmer identify their own field in under 60 seconds | Onboarding completion rate; field-mapping success rate |
| **G6** | Cover multiple crops, diseases, and pests — a platform, not a demo | Number of validated crop×pathogen models live |
| **G7** | Amplify the existing extension system, not replace it | Officer console adoption; officer-logged outbreaks |
| **G8** | Operate at near-zero marginal cost | Infrastructure cost per farmer per season |

## 1.5 Explicit anti-goals

State these clearly. Scope discipline is a feature, and a reviewer who sees an undisciplined scope discounts everything else.

| We are **not** building | Why not |
|---|---|
| A photo-diagnosis product | Different window on the timeline (§1.3), and well served already. Vision exists here as *confirmation* and *ground-truth collection* — a supporting role, deliberately (§12). |
| A general-purpose farming chatbot | An ungrounded LLM that invents agronomic numbers is dangerous regardless of who builds it. Our LLM is tightly constrained (§27). |
| A marketplace or input-sales business | Would create an incentive to over-recommend spraying. Structurally incompatible with the product's purpose. |
| A hardware / IoT / sensor network | Per-field capital cost is the constraint for a 1.2 ha holding. Sensor-based advisory is genuinely more accurate; it simply serves a different farm size (§4.1). |
| A yield predictor | Different problem, different validation burden. Flagged as future scope. |
| An insurance product | Though the risk surface is legitimate underwriting infrastructure (§38.5). |
| A pesticide prescription service | 🔴 Recommending a specific product and dose is a licensed advisory act. We give *timing*; a KVK officer or licensed dealer gives *product*. See §39.2. |

## 1.6 Success metrics

**Tier 1 — Scientific credibility.** *These are non-negotiable and published regardless of outcome.*

| Metric | Target | Note |
|---|---|---|
| Probability of Detection (POD) | ≥ 0.75 | The farmer-protective metric |
| False Alarm Ratio (FAR) | ≤ 0.40 | 🔴 Deliberately permissive — see §38.2 |
| Critical Success Index (CSI) | ≥ 0.50 | Balanced measure |
| Mean lead time | ≥ 48 h | Below this the forecast is not actionable |
| **Expected farmer cost** | **minimised** | 🔴 Ranks *above* CSI. See §35.4. |

**Tier 2 — Delivery reality.**

| Metric | Target |
|---|---|
| Field-mapping completion in onboarding | ≥ 80% |
| Voice advisory listen-through rate | ≥ 60% |
| Advisory → action reported | ≥ 30% |
| Sessions served fully offline | ≥ 25% |
| Officer-logged outbreak reports per month | growing |

**Tier 3 — Engineering.**

| Metric | Target |
|---|---|
| Forecast freshness | < 12 h |
| Field-detail screen load, 3G | < 2.5 s |
| Weather API calls per district-night | ≤ 5 |
| Marginal infrastructure cost per farmer-season | ≈ ₹0 |

**Metrics we deliberately reject:**

- ❌ **"Model accuracy: 94%"** — meaningless without a base rate. If 95% of cell-days have no outbreak, predicting "never" scores 95%. We publish contingency tables, not accuracy percentages.
- ❌ **Daily active users** — a farmer who opens the app twice a season and prevents a crop loss is a total success. Engagement is the wrong loss function for a warning system. We measure *warnings acted upon*.
- ❌ **Number of features shipped** — see §1.5.

---

# 2. THE PROBLEM

## 2.1 The loss

Crop losses to pests and diseases in India are large and, critically, **largely preventable with correct timing**. Late blight alone can destroy **40–70% of a potato crop** in an uncontrolled epidemic year. Wheat rusts, rice blast, and cotton pink bollworm each cause comparable regional devastation in bad years.

⚠️ **A number to get right:** the commonly-quoted "15–25% of Indian crop production is lost" figure refers to **pests + weeds + diseases combined**. Quoting it as a disease-only figure is an error a domain expert catches instantly, and it undermines otherwise-sound work. `[VERIFY]` — cite the specific source when using any loss figure.

## 2.2 The science is solved. The last mile is not.

This is the actual gap PRAHARI addresses, and it is important to state it accurately: **the forecasting science is decades old, thoroughly validated, and not ours.** We did not discover anything. What we are building is the delivery layer that connects it to one specific hectare.

| Existing work | What it provides | The remaining last-mile gap |
|---|---|---|
| Smith Period (1956), Hutton Criteria, Wallin DSV (1962), BLITECAST (1975) | The validated science PRAHARI runs on. Everything in §8 is theirs. | Published as research, not as a delivery channel to an individual field. |
| ICAR-CPRI late-blight forecasting (JHULSACAST / INDO-BLIGHTCAST family) | Real, rigorous, India-specific validation and decades of refinement. The gold standard we want to be measured against. `[VERIFY]` current scope. | Designed to inform institutions and regions. Reaching an individual non-literate farmer by voice, nightly, is a different engineering problem. |
| IMD Gramin Krishi Mausam Sewa agromet advisories | Official, trusted, nationwide, and free. Genuine public infrastructure. | District granularity (~4,000 km²), twice weekly, necessarily generic across crops within a district. |
| VDIFN (Univ. of Wisconsin) | Gridded disease-severity mapping, operationally proven at scale. | Built for a different farm structure — larger holdings, literate desktop users, reliable connectivity. |
| Photo-diagnosis products | Strong image classification and wide reach; they solve the detection window well (§1.3). | Operate after symptoms appear, by design. Complementary rather than overlapping. |

💡 **So the gap is not scientific — it is a last-mile delivery gap.** The models work. The remaining problem is connecting them to a specific 1-hectare parcel, in the farmer's language, by voice, in time to act, at a cost of zero. That is a product and infrastructure problem, and it is the one PRAHARI takes on.

## 2.3 The four barriers that have kept this gap open

**Barrier 1 — Resolution.** Disease risk varies over hundreds of metres. A low-lying shaded corner stays wet six hours longer than the field 400 m uphill. District-level advisories cannot express this, so farmers correctly learn to ignore them.

**Barrier 2 — Identification.** 🔴 **This is the barrier everyone underestimates, and the one that has most shaped this PRD.** Even a perfect field-level forecast is useless if the farmer cannot tell which prediction is *theirs*. An abstract grid map, a district choropleth, or a list of village names does not let a farmer with 1.2 hectares in three non-contiguous parcels identify their own land. **A forecast the farmer cannot locate themselves in is not a product.** §20 exists entirely to solve this.

**Barrier 3 — Literacy and language.** A written advisory in English, or even in formal Hindi, excludes a large share of the intended users. Text is a delivery failure mode, not a delivery channel.

**Barrier 4 — Actionability.** "High disease risk" is an alert. Alerts create anxiety and get ignored. **"Spray Tuesday between 6 and 9 in the morning, because it rains at 2 in the afternoon and a late spray washes off and wastes ₹800"** is an instruction. Instructions get followed.

## 2.4 Why now

- **Free hourly weather forecasting at fine resolution** is now available keylessly and globally (Open-Meteo, ECMWF/GFS-derived).
- **Free satellite earth observation** at 10 m resolution and 5-day revisit (Sentinel-2) with free planetary-scale compute (Google Earth Engine).
- **Free multilingual AI**: Bhashini (MeitY) for Indic speech and translation; free-tier LLM APIs; small open models fine-tunable on free GPU.
- **On-device inference** is now practical on ₹8,000 Android phones via ONNX Runtime Web / TFLite.
- **Smartphone penetration in rural India** has crossed the threshold where a voice-first PWA reaches a meaningful population — and where it does not, the same engine drives IVR and SMS.

Each of these became free and viable within the last few years. The product was not buildable at zero cost before.

---

# 3. WHO IT IS FOR

## 3.1 Primary beneficiary — Sunita Devi

**38 · Farrukhabad district, Uttar Pradesh · 1.2 hectares potato across 3 parcels**

Sunita has grown potato for fourteen years. She reads Hindi slowly and prefers to listen. The phone is a ₹7,000 Android, shared with her husband and son; she has it in her hands for perhaps ninety minutes a day. Data is a ₹199 monthly pack that runs out. Her three parcels are not adjacent — one is near the canal, one behind the school, one on higher ground toward the next village.

Her crop is worth roughly **₹80,000** in a good year. A bad blight year takes half of it. She has borrowed against this crop.

**What she does today:** sprays on a calendar her father used, or when a neighbour sprays, or when she sees spots. She has never had information specific to her own field.

**What she needs:** to be told, out loud, in Hindi, "your canal field needs spraying Tuesday morning" — and to be able to tell *which field* that means.

**What breaks her:** anything requiring reading; anything requiring more than three taps; anything that needs a live connection; a map she cannot locate herself on; being told to spray when she doesn't need to, twice, after which she stops listening forever.

🔴 **She is the design constraint.** Every screen is tested against her. If she cannot use it, it does not ship, regardless of how good it looks in a demo.

## 3.2 The amplifier — Dr. Arun Kale

**44 · Subject Matter Specialist (Plant Protection), Krishi Vigyan Kendra · ~40 villages · M.Sc. Plant Pathology**

Arun is responsible for more farmers than he can physically visit. He drives to villages on a rotation, arriving after problems start. He writes advisories that reach a fraction of his farmers.

**He knows the Smith Period. He will check the model.** He will ask which criterion is used, whether the temperature is the daily mean or the mean during the humid spell, and how false alarms were handled. If the answers are good, he becomes the product's most powerful distribution channel. If they are evasive, he dismisses it in one conversation and tells his colleagues.

**What he needs:** a triage screen answering *"which of my 40 villages need me this week"*; the underlying rule trace so he can sanity-check a prediction; the ability to log an outbreak he has personally seen; bulk advisory dispatch; a PDF bulletin he can print.

💡 **Arun is the institutional wedge.** One convinced KVK officer reaches thousands of farmers with credibility no app can manufacture. Designing *for* the extension system rather than around it is the single highest-leverage distribution decision in this product.

## 3.3 The gatekeeper — Dr. Priya Menon

**ICAR scientist · evaluates agri-tech claims**

Priya has seen many dashboards. She is not impressed by maps. She checks, in this order:

1. Is the Wallin table correct, including boundaries?
2. Is RH honestly described as a **proxy** for leaf wetness, or is leaf-wetness sensing being implied?
3. Was the ground truth **frozen before** parameter tuning, and can that be proven?
4. Were **negative cases** scored, or only the outbreaks?
5. Is the resolution claim honest — is 1 km a *presentation* resolution or a *sensing* resolution?
6. Does the ML layer make claims the data cannot support?

**She is not the enemy. She is the standard.** Every rigour section in PART V exists because of her. If the product survives Priya, it survives anyone.

## 3.4 The multiplier — Ravi Kumar

**31 · Farmer Producer Organisation coordinator · ~400 member farmers**

Ravi coordinates bulk input purchase and shared equipment. Two of his villages own one tractor-mounted sprayer between them.

**What he unlocks:** the **village collective spray window**. Individual optimal windows scatter across three days; a synchronised village-wide window is epidemiologically superior — spraying half a village leaves an inoculum reservoir that reinfects the sprayed half. It is also logistically necessary when one sprayer serves forty fields.

**What he needs:** a village-level window, a member roster with field locations, and bulk-purchase timing so fungicide arrives *before* the window, not during it.

## 3.5 Secondary users

| User | Need |
|---|---|
| **Village Level Entrepreneur / agri-input dealer** | Helps farmers map fields during onboarding; sees aggregate village demand timing |
| **State agriculture department** | District-level risk timeline for advisory planning |
| **Crop insurer / underwriter** | Historical validated risk surface (§38.5) |
| **Agricultural researcher** | Open validation data, model registry, reproducible artefacts |

---

# 4. THE LANDSCAPE AND WHERE PRAHARI FITS

## 4.0 The rule for this whole section

> 🔴 **PRAHARI is defined by what it builds, not by what anyone else lacks.**
>
> Everything listed below is real work by capable people solving real problems, usually under constraints we do not have. Several of these systems are **strictly better than PRAHARI at what they were built for.** A sensor in a field measures leaf wetness directly; we can only infer it. A national institute has ground-truth records we will never assemble. An image classifier trained on millions of labelled photographs will out-diagnose our 4 MB on-device model every time.
>
> The honest framing is **positional, not comparative**: this is the specific combination of constraints PRAHARI chose to serve — a 1.2 ha fragmented holding, a non-literate user, a shared ₹7,000 phone, intermittent 2G, and ₹0 of budget on either side. That combination is what shaped every decision in this document. Other systems chose different constraints and built accordingly.

## 4.1 The landscape

| System / category | What it is genuinely good at | The constraint set PRAHARI chose instead |
|---|---|---|
| **Photo-diagnosis products** | Excellent image classification at scale, huge labelled datasets, wide farmer adoption. They solve the detection window well. | The prevention window (§1.3) — which needs a forecast rather than a camera. We use vision as a *supporting* signal (§12) and would rather integrate with strong classifiers than duplicate them. |
| **IMD GKMS agromet advisory** | Official, nationwide, trusted, free public infrastructure. Broader reach than PRAHARI will have for years. | Field-level granularity and per-pathogen specificity, at the cost of covering far fewer districts. PRAHARI is a **downscaling and delivery layer**, and would ideally consume IMD data rather than parallel it. |
| **ICAR-CPRI late-blight forecasting** | Decades of India-specific validation, real ground truth, institutional authority. Scientifically ahead of us and likely to remain so. | Individual-farmer voice delivery at field resolution. See §4.2 — this is a **validation partner**, and being measured against it is the outcome we want. |
| **VDIFN (Univ. of Wisconsin)** | Gridded disease-severity mapping, operationally proven. **Our existence proof** that gridded DSV works in production. | Smallholder constraints: voice-first, offline-first, fragmented parcels, no desktop. Different users, same underlying science. |
| **Sensor-based advisory (in-field IoT)** | Direct measurement of leaf wetness and microclimate. **More accurate than any inference-based approach, including ours.** | Zero per-field capital cost, which is the binding constraint at 1.2 ha. If sensor economics reach smallholders, that is better for farmers than PRAHARI is — and we would happily ingest their data. |
| **Satellite advisory platforms (enterprise agri-tech)** | Sophisticated remote sensing and agronomy, serving lenders, insurers, and agribusiness at scale. `[VERIFY]` current consumer offerings. | Farmer-direct and free, which requires a fundamentally different cost structure — hence every architectural choice in §25. |
| **Government portals (Kisan Suvidha and similar)** | Authoritative aggregation of schemes, prices, and official data. | A predictive layer with a specific recommended action and a spray window. Complementary; not the same job. |

💡 **Read that table again as a build list, not a scoreboard.** Four of the seven rows are things PRAHARI should eventually *consume or partner with*: IMD as a weather source, CPRI as a validator, sensor networks as ground truth, image classifiers as a confirmation upgrade. The architecture in PART IV is deliberately built with adapter boundaries so any of them can be plugged in (§29.7).

## 4.2 🔴 The rule about prior art

> **Never claim to beat a national research institute.** Not because it is impolite, but because it is unprovable with our validation data and it is the fastest way to lose the one audience whose endorsement actually matters.
>
> **The frame that works, and happens to be true:**
>
> *"None of the science here is ours. The models are from 1956, 1962, and 1975, and Indian institutions have refined them for decades with ground truth we do not have. What we built is the last mile — field resolution instead of district, nightly instead of twice weekly, voice instead of text, a specific spray window instead of a risk level, and zero cost. We would like to be validated against CPRI's system. If our forecast disagrees with theirs, the correct assumption is that we are wrong, and we would like to know why."*

That framing turns the strongest available challenge into a collaboration request — and it is also the intellectually correct position to hold.

## 4.3 What PRAHARI contributes that is its own

1. **Field-level identification** (§20). No competitor solves "which prediction is mine" for a smallholder with fragmented parcels. This is a hard UX problem, not a hard tech problem, which is exactly why it is unsolved.
2. **Physics-first, ML-corrected architecture** (§26.5). Deterministic published models produce the prediction; ML corrects systematic bias against observed outbreaks. This is defensible in a way that a pure black-box model never is — and it degrades gracefully when training data is thin.
3. **The grounded AI agronomist** (§27). The LLM never invents a number. It only explains, translates, and speaks facts the deterministic engine produced. This is the difference between a useful assistant and a liability.
4. **The public tamper-evident alert ledger** (§36). The only accuracy claim in this category a sceptic can independently verify in their own browser.
5. **Economic calibration** (§38.2). A miss costs roughly 80× a false alarm, so we accept more false alarms *deliberately and explain why*. Competitors optimise statistics; we optimise the farmer's expected loss.
6. **Zero marginal cost as an architectural property** (§38.4), not a temporary subsidy.

---

# 5. PRODUCT PRINCIPLES

These are decision rules. When two options conflict, the principle decides.

## 🔴 P1 — Your field, not a grid

> **The farmer sees their own field on satellite imagery with landmarks they recognise. The computational grid is invisible to them, forever.**

The 1 km cell is an implementation detail of the physics. It is not a user-facing concept. A farmer never sees a grid, a cell ID, a choropleth, or a district-wide colour wash. They see an outline around *their* land on a photograph of *their* village, with the canal and the school visible.

This principle drove: satellite-first basemap, the three-method field-mapping flow, landmark overlays, field-centric navigation, and the removal of every grid artefact from the farmer app. §20 implements it.

## 🔴 P2 — Instruction, not alert

> Never ship "risk is high". Always ship "spray Tuesday 6–9 AM, because rain at 2 PM will wash it off."

An alert transfers anxiety. An instruction transfers capability. Every risk state in the product must resolve to a concrete recommended action, including the action *"do nothing, and here is why that is safe."*

## 🔴 P3 — The engine is deterministic; the AI explains it

> Published science computes the numbers. Machine learning corrects them against observation. The LLM only *verbalises* them.

The LLM has no authority to produce a risk value, a threshold, a date, or a dose. It receives structured facts and renders them conversationally in the farmer's language. This boundary is enforced in code (§27.4), not by prompt instruction.

💡 This is the entire anti-slop architecture. An LLM that can invent an agronomic number will, eventually, invent a wrong one, and a farmer will act on it.

## 🔴 P4 — Voice is the product; the screen is the accessory

Design the audio advisory first, then build a screen around it. If the product works with the screen switched off, it works for the person who needs it most.

## 🔴 P5 — Honesty over polish

Show data age. Show confidence. Show what we do not know. Publish accuracy including bad numbers. A product that refuses to look confident when it is not is the only kind a plant pathologist will ever trust — and it is the only kind that survives a farmer's second false alarm.

## 🔴 P6 — Offline is the default assumption

Assume no connection. Everything critical — current advisory, field boundaries, voice audio, last forecast — must work in airplane mode. Connectivity is an enhancement that delivers fresh data, not a precondition for the product functioning.

## 🔴 P7 — Amplify the extension system

Every capability should make a KVK officer more effective, not route around them. Product choice, dosage, and anything with liability goes through a qualified human. This is both ethically correct (§39.2) and the fastest real distribution path.

## 🔴 P8 — Zero marginal cost by design

Every architectural choice is checked against "does this still cost nothing at 100× the users?" Free tiers are used within their terms; the design assumes no credit card exists.

---

# ═══════════════════════════════════════
# PART II — PRODUCT
# ═══════════════════════════════════════

# 6. FEATURE ARCHITECTURE — THE TWELVE PILLARS

```
┌───────────────────────────────────────────────────────────────────────┐
│                          PRAHARI PLATFORM                             │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  FOUNDATION LAYER — how the farmer exists in the system               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ①  FIELD IDENTITY & MAPPING              [P0] §7                │  │
│  │     Satellite-first field capture · ML boundary snapping ·       │  │
│  │     landmark anchoring · multi-parcel management                 │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  INTELLIGENCE LAYER — what the system knows                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ②  DISEASE & PEST FORECAST ENGINE        [P0] §8                │  │
│  │ ③  SATELLITE CROP INTELLIGENCE           [P1] §9                │  │
│  │ ④  EPIDEMIC SPREAD SIMULATION            [P1] §10               │  │
│  │ ⑤  GROUNDED AI AGRONOMIST                [P1] §11               │  │
│  │ ⑥  VISION CONFIRMATION                   [P2] §12               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ACTION LAYER — what the farmer does                                  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ⑦  SPRAY WINDOW & OPERATIONS PLANNER     [P0] §13               │  │
│  │ ⑧  VOICE & MULTILINGUAL DELIVERY         [P0] §14               │  │
│  │ ⑨  FIELD OPERATIONS RECORD               [P1] §15               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  NETWORK LAYER — how it compounds                                     │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ⑩  COMMUNITY OUTBREAK NETWORK            [P1] §16               │  │
│  │ ⑪  EXTENSION OFFICER CONSOLE             [P1] §17               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  TRUST LAYER — why anyone believes it                                 │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ ⑫  TRANSPARENCY & VALIDATION             [P0] §18               │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## 6.1 Dependency order

Pillars must be built in dependency order, not priority order. **① Field Identity is the hard prerequisite for everything** — without a field polygon, there is nothing to forecast *for*.

```
①  Field Identity  ──┬──▶ ②  Forecast Engine ──┬──▶ ⑦  Spray Planner ──▶ ⑧  Voice
                     │                          │
                     ├──▶ ③  Satellite Intel ───┤
                     │         │                │
                     │         └────────────────┼──▶ ④  Spread Simulation
                     │                          │
                     ├──▶ ⑥  Vision ────────────┼──▶ ⑩  Community Network
                     │                          │              │
                     │                          └──▶ ⑤  AI Agronomist
                     │                                         │
                     └──▶ ⑨  Field Ops Record ─────────────────┘
                                    │
                     ⑪  Officer Console ◀────────┘
                                    │
                     ⑫  Transparency ◀───────── (consumes everything)
```

## 6.2 What ships in the Minimum Credible Product

A product that does less than this is not credible; a product that does more before validating this is over-extended.

| Pillar | MCP scope |
|---|---|
| ① Field Identity | Satellite capture + tap-to-snap + manual corner adjust + GPS locate + multi-parcel |
| ② Forecast Engine | 2 crops × 3 pathogens, physics models, 7-day horizon, field-level aggregation |
| ⑦ Spray Planner | Window detection with rain/wind/temp gates + village collective window |
| ⑧ Voice | Hindi + one regional language, pre-generated, offline-capable |
| ⑫ Transparency | Public accuracy page + alert ledger + limitations page |

Everything else is sequenced in §40.

---

# 7. PILLAR ① — FIELD IDENTITY & MAPPING `[P0]`

> **This pillar exists because of the single sharpest critique of the original design: a farmer looking at a grid map cannot tell which square is their field.** Solving this is not a UI refinement. It is the foundation of the product.

## 7.1 The problem in detail

A smallholder in the Indo-Gangetic plain typically holds **1–2 hectares split across 2–5 non-adjacent parcels**, often unfenced, bounded by informal bunds, with no cadastral reference the farmer knows by number. Field boundaries are known socially and visually: *"the one past Ram's tubewell"*, *"the low one near the canal"*.

Therefore:
- ❌ A district choropleth is unusable — no reference to *my* land.
- ❌ A 1 km grid is unusable — a 1 km cell contains dozens of farmers' parcels.
- ❌ A vector/abstract basemap is unusable — nothing on it corresponds to what the farmer sees when standing in the field.
- ❌ Asking for a survey number is unusable — often unknown, frequently disputed, and a literacy barrier.
- ✅ **Satellite imagery is usable.** Field parcels, bunds, canals, tracks, ponds, and building clusters are directly recognisable from an aerial view. This is well established in participatory mapping practice.

## 7.2 The solution — three capture methods

Different farmers succeed with different methods. Offer all three; let the farmer pick.

### Method A — Tap on satellite imagery *(primary, ~70% expected)*

```
STEP 1  App requests location → centres satellite imagery on GPS fix
        at ~18–19 zoom (≈40–80 m across the screen)

STEP 2  Landmark overlay renders on top of imagery:
        village name · roads · canals · water bodies · settlement outline
        (from OpenStreetMap — see §29.6)

        Voice prompt (Hindi): "Yeh aapka gaon hai. Apne khet par ungli rakhein."
                              ("This is your village. Touch your field.")

STEP 3  Farmer taps inside their parcel

STEP 4  🔴 ML BOUNDARY SNAP (§26.2)
        A segmentation model proposes the parcel polygon containing that point.
        Rendered as a bright outline with 6–10 draggable vertex handles.

        Voice: "Kya yeh aapka khet hai?"  ("Is this your field?")
        [ Haan, sahi hai ]  [ Thoda badlein ]  [ Nahi, dobara ]

STEP 5  Manual correction — drag any vertex; add a vertex by long-pressing an edge;
        pinch-zoom for precision. Live area readout in BOTH hectares and
        the locally-used unit (bigha / acre / guntha — §7.6)

STEP 6  Confirm → crop selection → sowing date (or auto-detect §26.4)
        → name the field in the farmer's own words
```

💡 **Why the ML snap matters:** manually tracing a polygon on a phone with a fingertip is slow and frustrating, and farmers abandon it. Snapping to a *proposed* boundary that only needs adjusting converts a 4-minute task into a 30-second one. When the model fails, the flow degrades to plain manual drawing — never to a dead end.

### Method B — Walk the boundary *(highest accuracy, ~15%)*

For a farmer physically standing in their field.

```
STEP 1  "Apne khet ke kone par khade hon, phir shuru karein."
        ("Stand at a corner of your field, then start.")
STEP 2  [ Shuru karein ] → continuous GPS track recording
        Live: distance walked · elapsed time · a growing polygon on satellite
        Voice cue every 50 m: "Chalte rahein." ("Keep walking.")
STEP 3  Auto-close when the track returns within 15 m of the start
STEP 4  Douglas-Peucker simplification (5 m tolerance) → clean polygon
STEP 5  Confirm on satellite imagery
```

**Requirements:** works fully offline (GPS needs no data connection); survives screen lock and app backgrounding; warns if GPS accuracy exceeds 15 m; discards points with accuracy > 30 m; allows pause/resume; hard cap 30 minutes.

⚠️ **The trap:** naïvely recording every GPS point produces a jagged 400-vertex polygon that is both wrong and huge. Simplify before storing, and always show the simplified result for confirmation.

### Method C — Assisted mapping *(the reach mechanism, ~15%)*

The farmer who cannot complete either method — no smartphone, no confidence, poor eyesight — is mapped **by another person**: a KVK officer, a Village Level Entrepreneur, an FPO coordinator, or a family member.

```
Officer console → "Map a farmer's field"
  → search/create farmer by name + village + hashed phone
  → map the field using Method A or B
  → farmer receives a confirmation call/SMS with a spoken description:
    "Aapka khet naher ke paas, 2 bigha, aloo — sahi hai?"
```

🔴 **This method is what makes the product reachable rather than merely available.** Designing only for the self-service farmer excludes exactly the population with the most to lose. A farmer with no smartphone still receives IVR and SMS advisories for a field someone else mapped.

## 7.3 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1.1 | Satellite imagery basemap at zoom ≥ 18 for the covered area | P0 |
| FR-1.2 | GPS locate with a visible accuracy radius | P0 |
| FR-1.3 | Landmark overlay: village name, roads, canals, water, settlements | P0 |
| FR-1.4 | Tap-to-snap ML boundary proposal | P0 |
| FR-1.5 | Manual vertex add / drag / delete with pinch-zoom precision | P0 |
| FR-1.6 | Walk-the-boundary GPS trace with simplification | P1 |
| FR-1.7 | Assisted mapping via the officer console | P1 |
| FR-1.8 | Multi-parcel: unlimited fields per farmer, each independently named | P0 |
| FR-1.9 | Farmer-chosen field names in the local language, including voice-dictated | P0 |
| FR-1.10 | Area shown in hectares **and** the local unit | P0 |
| FR-1.11 | Crop + variety + sowing date per field per season | P0 |
| FR-1.12 | Edit or delete a field boundary at any time | P0 |
| FR-1.13 | Season rollover: retain the boundary, prompt for the new crop | P1 |
| FR-1.14 | Field boundaries cached offline and fully usable with no connection | P0 |
| FR-1.15 | Optional auto-detected sowing date from satellite (§26.4) | P2 |
| FR-1.16 | Optional auto-detected crop type from satellite (§26.3), farmer-confirmed | P2 |

## 7.4 Validation rules

| Rule | Behaviour on violation |
|---|---|
| Polygon must be simple (non-self-intersecting) | Auto-repair; if unrepairable, ask the farmer to redraw |
| Area between 0.02 ha and 50 ha | Warn, allow override — some holdings are genuinely tiny or large |
| Must lie inside a covered district | Explain coverage, offer notify-me. **Never a dead end.** |
| Vertex count ≤ 50 after simplification | Simplify further |
| ⚠️ Overlap > 60% with an existing field of the *same* farmer | Warn: "Is this the same field as *Nadi wala khet*?" |
| Overlap with a *different* farmer's field | 🔴 Allow silently. Shared/leased/disputed land is normal; adjudicating ownership is not this product's business and attempting it creates real harm. |

## 7.5 Edge cases

| Case | Handling |
|---|---|
| GPS unavailable (indoors, poor sky view) | Fall back to village search → satellite view of that village |
| Satellite imagery stale (shows a previous crop pattern) | Show the imagery date; boundaries are usually stable even when crops change |
| Farmer's field is smaller than one satellite pixel cluster | Manual drawing at maximum zoom; accept small polygons |
| Cloud-obscured imagery in the basemap tile | Basemap imagery is composited and generally cloud-free; if not, offer Method B |
| Farmer taps a road or a pond | Snap model returns a non-field class → "That looks like a road. Try again inside your field." |
| Leased land changing between seasons | Fields are per-season objects; a boundary can be retained or released at rollover |
| Two farmers map the same parcel | Both allowed (see §7.4). Advisories go to both. |
| Very long thin parcel (common near canals) | Snap model handles elongated geometry; area check must not reject high aspect ratios |

## 7.6 Local area units `[HUMAN]`

Area must be shown in the unit the farmer actually thinks in. Bigha in particular **varies by region and even by district** and cannot be hardcoded to a single value.

```yaml
# config/area_units.yaml — must be verified per district with local input
units:
  hectare: { factor_sqm: 10000, label_hi: "हेक्टेयर" }
  acre:    { factor_sqm: 4046.86, label_hi: "एकड़" }
  bigha_up_west: { factor_sqm: 2529, label_hi: "बीघा", note: "[VERIFY] per district" }
  bigha_wb:      { factor_sqm: 1337.8, label_hi: "বিঘা", note: "[VERIFY]" }
  guntha:        { factor_sqm: 101.17, label_hi: "गुंठा" }
```

🔴 `[HUMAN]` — Each district's bigha value must be confirmed with a local officer before launch in that district. Getting this wrong makes every area readout wrong and destroys credibility in the first thirty seconds.

## 7.7 Acceptance criteria

- [ ] A farmer with no prior app experience maps a field in **under 90 seconds** using Method A
- [ ] The ML snap proposes a usable boundary (≤ 3 vertex corrections needed) in **≥ 70%** of attempts
- [ ] Walk-the-boundary produces an area within **±10%** of the tap-and-snap area for the same parcel
- [ ] All three methods work with the phone in airplane mode after the first imagery cache
- [ ] Field names accept Devanagari and other Indic scripts, and voice dictation
- [ ] Area displays correctly in the district's local unit
- [ ] Deleting a field removes it completely with a confirmation step

---

# 8. PILLAR ② — DISEASE & PEST FORECAST ENGINE `[P0]`

> The scientific core. Everything else is delivery, and none of it matters if this is wrong.

## 8.1 What it produces

For every mapped field, for each of the next 7 days, for each active crop×pathogen model:

- A **risk band** — safe / watch / act — with a numeric score
- The **rule trace** that produced it, in three depths (farmer / officer / scientist)
- A **confidence value** reflecting how much the underlying weather interpolation can be trusted
- A **recommended action**, always including "do nothing, safely"

## 8.2 Architecture — the computational grid the farmer never sees

```
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1 — WEATHER NODE LATTICE                                   │
│  ~36 points at ~0.1° spacing covering the district,              │
│  fetched in ONE multi-coordinate API call                        │
│                                                                  │
│    ●     ●     ●     ●     ●     ●                              │
│    ●     ●     ●     ●     ●     ●     ← hourly temp, RH,       │
│    ●     ●     ●     ●     ●     ●       rain, wind, dewpoint    │
│    ●     ●     ●     ●     ●     ●       for 8 days ahead        │
│    ●     ●     ●     ●     ●     ●                              │
│    ●     ●     ●     ●     ●     ●                              │
└──────────────────────────────────────────────────────────────────┘
                              ▼  bilinear interpolation
                                 + elevation lapse correction
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2 — 1 km COMPUTATIONAL GRID (~3,600 cells/district)        │
│  Internal only. Never rendered to a farmer.                     │
│  Each cell gets a full hourly weather series.                    │
└──────────────────────────────────────────────────────────────────┘
                              ▼  run every active model
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3 — PER-CELL RISK per pathogen per day                     │
│  Hutton / Smith / Wallin DSV / degree-day accumulation           │
│  + ML bias correction (§26.5)                                    │
│  + spatial spread contribution (§10)                            │
└──────────────────────────────────────────────────────────────────┘
                              ▼  area-weighted aggregation
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4 — FIELD-LEVEL RISK  ← 🔴 THE ONLY THING THE FARMER SEES │
│  Each field polygon intersects 1..n cells.                      │
│  Field risk = area-weighted worst-case across intersected cells. │
│  Field confidence = min(cell confidences) — honesty over         │
│  optimism when cells disagree.                                   │
└──────────────────────────────────────────────────────────────────┘
```

💡 **Step 4 is the reconciliation of P1 (Your field, not a grid) with the physics.** The grid is real and necessary; it is simply not the farmer's mental model. We compute on cells and *speak* in fields.

🔴 **Aggregation is worst-case, not mean.** If 20% of a field falls in a high-risk cell, the field is high risk. A farmer sprays a whole field, not 80% of it — and the cost asymmetry (§38.2) makes under-warning far more expensive than over-warning.

## 8.3 🔴 The weather node lattice — the decision that makes zero cost possible

**The naïve approach:** one API call per 1 km cell = ~3,600 calls per district per night. This violates every free tier, invites rate-limiting, and produces partial data when throttled.

**The PRAHARI approach:** fetch ~36 nodes at ~0.1° (~11 km) spacing in **one or two multi-coordinate calls**, then interpolate to the 1 km grid.

```python
# adapters/weather.py  — IMPURE (all I/O lives here)

def build_node_lattice(bbox, spacing_deg=0.1):
    """Nodes covering bbox with a one-node margin so every interior
    cell is surrounded on all four sides — no extrapolation at edges."""

def fetch_nodes(nodes, variables, forecast_days=8, past_days=2):
    """ONE HTTP call per <=100 nodes. Returns raw hourly series per node."""
```

**Interpolation, with one critical asymmetry:**

```python
# engine/interpolate.py — PURE (no network, no clock, no files)

def bilinear(values_at_4_nodes, frac_x, frac_y) -> float: ...

def temp_with_lapse(node_temp_c, node_elev_m, cell_elev_m,
                    lapse_c_per_km=6.5) -> float:
    """Environmental lapse rate correction. Cell 200 m higher ≈ 1.3 °C cooler."""
    return node_temp_c - lapse_c_per_km * (cell_elev_m - node_elev_m) / 1000.0
```

> 🔴 **⚠️ DO NOT lapse-correct relative humidity.** RH is not a linear function of elevation. Interpolate **temperature** and **dew point** — both of which do behave approximately linearly — then *recompute* RH from the corrected pair using the Magnus formula. Applying a lapse rate directly to RH is physically meaningless and silently corrupts every downstream disease calculation. This is the single most common error in downscaled agro-meteorology.

```python
def rh_from_temp_and_dewpoint(temp_c: float, dewpoint_c: float) -> float:
    """Magnus formula. Recompute RH after lapse-correcting BOTH inputs."""
    a, b = 17.625, 243.04
    num = math.exp(a * dewpoint_c / (b + dewpoint_c))
    den = math.exp(a * temp_c / (b + temp_c))
    return max(0.0, min(100.0, 100.0 * num / den))
```

## 8.4 The pathogen model library

🔴 **All science lives in data files, never in `if` statements.** A challenged parameter must be a one-line edit that re-runs the entire test suite, not a code change.

### 8.4.1 Moisture-driven fungal & oomycete models

**Potato/tomato late blight — *Phytophthora infestans*** `[P0]`

⚠️ *An oomycete, not a fungus.* Calling it a fungus in front of a plant pathologist is an immediate credibility loss.

```
HUTTON CRITERIA  ← PRAHARI's headline rule
  A day QUALIFIES when:  daily minimum temperature ≥ 10 °C
                    AND  ≥ 6 hours with RH ≥ 90%
  CRITERION MET when 2 CONSECUTIVE qualifying days occur.

SMITH PERIOD (1956)  ← legacy comparison, switchable
  Identical, but ≥ 11 hours instead of ≥ 6.
```

Hutton is the default because the 6-hour threshold is **more sensitive** — it triggers earlier and misses fewer real outbreaks. Given the ~80:1 cost asymmetry (§38.2), buying sensitivity with false alarms is the economically correct trade, and we make it deliberately and say so.

**Wallin Disease Severity Value (1962)** — graded severity accumulation:

```
Inputs (both easy to get wrong — see §8.6):
  · mean temperature DURING the humid spell   (not the daily mean)
  · hours with RH ≥ 90% WITHIN that spell     (not the daily total)

Temp band        Wet-hour breakpoints → DSV
7.2–11.6 °C      15h→0  18h→1  21h→2  24h→3
11.7–15.0 °C     12h→0  15h→1  18h→2  21h→3  24h→4
15.1–26.6 °C      9h→0  12h→1  15h→2  18h→3  24h→4

Accumulate daily DSV; spray indicated near 15–18 accumulated.
```

🔴 `[VERIFY]` — **the highest-priority verification item in the project.** Confirm the exact Wallin band boundaries and breakpoints against a primary source. Listed in §43.

**Additional moisture-driven models** (each `[P1]`/`[P2]`, same data-driven structure):

| Crop | Disease | Pathogen | Driver | Priority |
|---|---|---|---|---|
| Potato, tomato | Late blight | *P. infestans* (oomycete) | RH ≥ 90% duration + temp | P0 |
| Potato, tomato | Early blight | *Alternaria solani* | Wet hours + warmer temps; older leaves | P1 |
| Wheat | Yellow (stripe) rust | *P. striiformis* | Cool + humid; 10–15 °C optimum | P1 |
| Wheat | Brown (leaf) rust | *P. triticina* | Warmer than yellow rust; 15–22 °C | P2 |
| Rice | Blast | *M. oryzae* | Night RH + leaf wetness + N status | P1 |
| Rice | Bacterial leaf blight | *X. oryzae* | Rain + wind injury + standing water | P2 |
| Grape | Downy mildew | *P. viticola* | The "3-10 rule": 10 mm rain, 10 °C, 10 cm shoots | P2 |
| Onion | Purple blotch | *Alternaria porri* | Leaf wetness duration | P2 |
| Chilli | Anthracnose | *Colletotrichum* | Rain splash + high RH | P2 |
| Mustard | White rust | *A. candida* | Cool humid nights | P2 |

### 8.4.2 Temperature-driven pest models `[P1]`

💡 **Adding pests roughly doubles the product's value with a small marginal engineering cost**, because insect development is governed by *thermal accumulation*, which is even more forecastable than moisture.

```
GROWING DEGREE DAYS (GDD)
  daily_gdd = max(0, ((T_max + T_min) / 2) - T_base)
  Accumulate from a biofix event (first trap catch, sowing, or emergence).
  Each pest has published thresholds where a life stage is reached.
```

| Crop | Pest | T_base | Trigger | Priority |
|---|---|---|---|---|
| Cotton | Pink bollworm | ~12 °C `[VERIFY]` | GDD from squaring → generation peaks | P1 |
| Maize | Fall armyworm | ~10 °C `[VERIFY]` | GDD from detection → larval instars | P1 |
| Rice | Yellow stem borer | ~10 °C `[VERIFY]` | GDD from transplant → moth emergence | P2 |
| Multiple | Aphids | ~4 °C `[VERIFY]` | GDD + mild-humid windows → population build | P2 |
| Multiple | Whitefly | ~11 °C `[VERIFY]` | GDD + dry-warm windows | P2 |

🔴 All `T_base` and threshold values are `[VERIFY]` against ICAR/state package-of-practices documents before any pest model goes live. **A pest model with a guessed base temperature is worse than no pest model**, because it will be confidently wrong on a predictable schedule.

### 8.4.3 The model definition file

```yaml
# config/models.yaml — the entire scientific configuration of the product
models:
  potato_late_blight_hutton:
    version: "2.0.0"
    crop: potato
    pathogen: "Phytophthora infestans"
    pathogen_kind: oomycete          # 🔴 NOT fungus
    model_family: moisture_criterion
    criterion: hutton
    params:
      rh_threshold: 90.0
      min_wet_hours: 6               # Hutton=6, Smith=11
      min_temp_c: 10.0
      consecutive_days: 2            # 🔴 CONSECUTIVE, not total
    severity:
      method: wallin_dsv
      spray_threshold_dsv: 18
      amber_threshold_dsv: 12
      dsv_table:                     # [VERIFY] — §43 item 1
        - { t_min: 7.2,  t_max: 11.6, breaks: [[15,0],[18,1],[21,2],[24,3]] }
        - { t_min: 11.7, t_max: 15.0, breaks: [[12,0],[15,1],[18,2],[21,3],[24,4]] }
        - { t_min: 15.1, t_max: 26.6, breaks: [[9,0],[12,1],[15,2],[18,3],[24,4]] }
    susceptible_stages: [tuber_initiation, tuber_bulking]
    citation: "Hutton criteria; Wallin (1962); Smith (1956); BLITECAST (Krause et al. 1975)"
    ml_correction: potato_lb_residual_v1   # §26.5, optional

  cotton_pink_bollworm:
    version: "1.0.0"
    crop: cotton
    pest: "Pectinophora gossypiella"
    model_family: degree_day
    params:
      t_base_c: 12.0                 # [VERIFY]
      biofix: squaring_stage
      generation_gdd: 550            # [VERIFY]
      alert_gdd_fraction: 0.85       # warn before the peak, not at it
    citation: "[VERIFY] ICAR-CICR package of practices"
```

## 8.5 Growth-stage gating `[P1]`

A model should only fire when the crop is actually susceptible. Late blight risk on a potato field two weeks after sowing is a false alarm by construction — there is not enough canopy to matter.

```
Growth stage from:  sowing date (farmer-entered)
                    → thermal time accumulation (GDD from sowing)
                    → satellite NDVI curve confirmation (§26.4)

Model fires only if current_stage ∈ model.susceptible_stages
```

💡 This is one of the cheapest available reductions in false alarm rate, and it costs one field in the data model.

## 8.6 🔴 The four classic silent bugs

Each has broken real published implementations. **None of them crash. All of them produce plausible output.** Every one requires a permanent regression test.

| # | The bug | Why it is wrong | Required test |
|---|---|---|---|
| **1** | `>` instead of `>=` on the RH threshold | The rule says "≥ 90%". Exactly 90.0 must count. | `hours_rh_at_or_above([90.0, 90.0, 89.9]) == 2` |
| **2** | Using the **daily mean** temperature for Wallin | The rule specifies the mean **during the humid spell**. A cold afternoon drags the daily mean into a different DSV band. | A case where daily mean and spell mean differ by > 2 °C must produce different DSVs |
| **3** | Counting **total** hours RH ≥ 90% in the day | The rule counts hours **within the qualifying spell**. Two separate 4-hour spells are not one 8-hour spell. | A fragmented-spell input must NOT qualify |
| **4** | **"2 days in the window"** instead of **"2 consecutive days"** | A completely different scientific claim. `sum(flags) >= 2` looks entirely reasonable. | 🔴 `criterion_met([True, False, True]) == False` |

> 🔴 **Bug 4 is the single most important test in PRAHARI.** Roughly nine of ten machine-generated implementations get it wrong, because *counting* is the obvious reading and *adjacency* is the correct one. This one assertion protects the scientific core of the entire product.

```python
# tests/test_rules.py — the four tests that must never be deleted
def test_boundary_is_inclusive():
    assert hours_rh_at_or_above([90.0, 90.0, 89.9]) == 2

def test_wallin_uses_spell_mean_not_daily_mean():
    # 6h humid spell at 20°C, cold 18h at 8°C → daily mean 11°C, spell mean 20°C
    assert wallin_dsv(mean_wet_temp=20.0, wet_hours=12) == 1
    assert wallin_dsv(mean_wet_temp=11.0, wet_hours=12) == 0

def test_fragmented_spells_do_not_combine():
    rh = [95]*4 + [70]*4 + [95]*4 + [70]*12     # 8 total wet hours, max spell 4h
    assert longest_wet_spell_hours(rh, 90.0) == 4

def test_consecutive_not_total():
    assert criterion_met([True, False, True]) is False    # 🔴 THE test
    assert criterion_met([True, True, False]) is True
```

## 8.7 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-2.1 | Node lattice fetch in ≤ 2 API calls per district | P0 |
| FR-2.2 | Bilinear interpolation with temp+dewpoint lapse correction, RH recomputed | P0 |
| FR-2.3 | Hutton and Smith criteria, switchable by config | P0 |
| FR-2.4 | Wallin DSV with rolling accumulation | P0 |
| FR-2.5 | Degree-day pest models | P1 |
| FR-2.6 | 7-day forward horizon, daily granularity | P0 |
| FR-2.7 | Field-level worst-case area-weighted aggregation | P0 |
| FR-2.8 | Confidence from inter-node disagreement | P0 |
| FR-2.9 | Growth-stage gating | P1 |
| FR-2.10 | ML residual correction layer, optional per model | P2 |
| FR-2.11 | Model version + engine commit stamped on every output | P0 |
| FR-2.12 | Deterministic: identical inputs always produce identical outputs | P0 |
| FR-2.13 | Multiple simultaneous models per field, each reported separately | P1 |
| FR-2.14 | Graceful degradation to cached weather on fetch failure | P0 |

## 8.8 Acceptance criteria

- [ ] All four silent-bug tests pass, and are wired into CI
- [ ] Full engine test suite runs in **under 2 seconds with no network access**
- [ ] Identical inputs produce byte-identical outputs across runs (determinism)
- [ ] A district night completes in ≤ 2 API calls to the weather provider
- [ ] Every risk output carries model id, model version, and engine commit SHA
- [ ] Changing a `models.yaml` value changes results with **zero code edits**
- [ ] Field risk equals the worst intersected cell, verified on a hand-computed case
- [ ] RH is never lapse-corrected directly anywhere in the codebase (enforced by a lint test)

---

# 9. PILLAR ③ — SATELLITE CROP INTELLIGENCE `[P1]`

> Satellite data is not decoration here. It answers three questions the weather models cannot: **what is actually growing in this field, how healthy is it, and what growth stage is it in.**

## 9.1 Why satellite matters to a disease forecast

The weather engine (§8) knows the atmosphere. It knows nothing about the plant. But disease risk is a function of the **disease triangle** — host, pathogen, and environment — and satellite observation is the only free way to see the *host* vertex at field scale.

```
                    THE DISEASE TRIANGLE

                          HOST
                     (the crop itself)
                            ▲
                            │  ← 🔴 SATELLITE sees this vertex
                            │     crop type · growth stage ·
                            │     canopy density · vigour · stress
                           ╱ ╲
                          ╱   ╲
                         ╱     ╲
                        ╱       ╲
              PATHOGEN ◀─────────▶ ENVIRONMENT
           (inoculum present)     (temp · humidity · rain)
                   ▲                      ▲
                   │                      │
        §10 spread model +       §8 weather engine
        §16 community reports    (the forecastable vertex)
```

💡 **This is the argument that makes the whole product scientifically coherent.** Environment is the only vertex that varies daily and can be forecast — which is why it is the primary driver. But a forecast that ignores host status produces false alarms on bare fields and on crops that are not even susceptible. Satellite closes that gap for free.

Four concrete uses:

| Use | What it prevents or enables |
|---|---|
| **Crop type classification** (§26.3) | Running a potato model on a wheat field — a guaranteed false alarm |
| **Sowing date / phenology** (§26.4) | Firing susceptibility warnings before the canopy exists |
| **Canopy vigour & anomaly** | Flagging a field that is already declining — early problem signal |
| **Water stress** | Irrigation advisory, and stress-driven disease susceptibility |

## 9.2 Data sources

| Source | Resolution | Revisit | Cost | Purpose |
|---|---|---|---|---|
| **Sentinel-2 L2A** (Copernicus) | 10 m (B2/3/4/8), 20 m (B5–7, 8A, 11/12) | ~5 days | Free | NDVI, NDRE, NDWI, crop type, phenology |
| **Sentinel-1 GRD** (SAR) | 10 m | ~6–12 days | Free | 🔴 **Cloud-independent** — critical during monsoon |
| **Landsat 8/9** | 30 m optical, 100 m thermal | ~16 days | Free | Land surface temperature |
| **MODIS / VIIRS** | 250 m–1 km | Daily | Free | Daily coarse LST and vegetation continuity |
| **Bhuvan (ISRO)** | Varies | Varies | Free | Indian thematic layers, land use `[VERIFY]` API terms |
| **Google Earth Engine** | — | — | Free for research/non-commercial `[VERIFY]` | 🔴 **Planetary-scale compute without owning servers** |
| **Satellite basemap tiles** | Sub-metre in many areas | Composited | Free tier | 🔴 The imagery the farmer recognises their field on (§7) |

🔴 **Google Earth Engine is the single biggest unlock in this pillar.** Computing a multi-year NDVI time series for 3,600 cells locally means downloading terabytes. In GEE the computation runs where the data lives and returns a few kilobytes of numbers. `[VERIFY]` — confirm current terms for our specific use before relying on it in production; have a Copernicus Data Space / STAC fallback path (§29.4).

## 9.3 Spectral indices

```python
# engine/indices.py — PURE

def ndvi(nir, red):    return (nir - red) / (nir + red + 1e-10)   # vigour, canopy
def ndre(nir, rededge): return (nir - rededge) / (nir + rededge + 1e-10)  # N status, early stress
def ndwi(nir, swir):   return (nir - swir) / (nir + swir + 1e-10) # moisture
def evi(nir, red, blue):
    return 2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1.0)     # saturates less at high LAI
```

Band mapping for Sentinel-2: `red = B4`, `nir = B8`, `rededge = B5`, `swir = B11`, `blue = B2`.

## 9.4 ⚠️ The three satellite processing traps

**Trap 1 — the reflectance offset.** 🔴 Sentinel-2 L2A products from **processing baseline 04.00 onwards carry `BOA_ADD_OFFSET = −1000`.** The conversion is:

```python
reflectance = (digital_number + BOA_ADD_OFFSET) / 10000.0
```

Skipping the offset does not crash anything and does not look obviously wrong. It shifts **every NDVI value and every anomaly** by a consistent amount, quietly invalidating comparisons between older and newer scenes. Read the offset from the scene metadata; never hardcode it.

**Trap 2 — cloud masking.** Use the Scene Classification Layer (`SCL`) and discard pixels in classes **{0 no-data, 1 saturated, 3 cloud shadow, 8 cloud medium-prob, 9 cloud high-prob, 10 thin cirrus}**. A field averaged over unmasked cloud returns a low NDVI that looks exactly like crop failure.

**Trap 3 — partial coverage.** A field polygon may be 40% cloud-masked. Reporting the mean of the remaining 60% as the field's NDVI is misleading. Rule: **require ≥ 60% valid pixels, otherwise return `null` and say "no clear satellite view since <date>"** rather than a number.

```python
def field_index_summary(pixels, scl, min_valid_fraction=0.6):
    valid = mask_invalid(scl, drop={0,1,3,8,9,10})
    if valid.mean() < min_valid_fraction:
        return None            # 🔴 honest null beats a plausible wrong number
    return {"mean": ..., "p10": ..., "p90": ..., "valid_fraction": valid.mean()}
```

## 9.5 In-field variability — a genuinely new capability

At 10 m resolution a 1.2 ha field contains roughly 120 pixels. That is enough to see **within-field variation**, which is information the farmer has never had before.

```
   Field: "Naher wala khet"    NDVI, 10 m pixels

   ┌───────────────────────────┐
   │ ▓▓▓▓▒▒▒▒░░░░░░▒▒▒▒▓▓▓▓▓▓ │   ▓ 0.70+  healthy
   │ ▓▓▓▒▒░░░░░░░░░░░▒▒▓▓▓▓▓▓ │   ▒ 0.50   moderate
   │ ▓▓▒▒░░░░░░░░░░░░░▒▒▓▓▓▓▓ │   ░ 0.35   weak ← the low corner
   │ ▓▓▓▒▒░░░░░░░░░░▒▒▒▓▓▓▓▓▓ │
   │ ▓▓▓▓▒▒▒░░░░░▒▒▒▒▓▓▓▓▓▓▓▓ │   ← canal side
   └───────────────────────────┘

   Advisory: "The canal-side corner of your field is weaker than
              the rest. That part stays wet longer and gets sick
              first. Check it first when you walk the field."
```

💡 **This is where satellite data stops being a dashboard feature and becomes advice.** "Your northwest corner is the weak spot" is actionable, memorable, and verifiable by the farmer walking twenty metres — which means it also builds trust in everything else the app says.

## 9.6 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-3.1 | Satellite imagery basemap for field identification | P0 |
| FR-3.2 | Field-level NDVI from the most recent clear Sentinel-2 pass | P1 |
| FR-3.3 | Correct `BOA_ADD_OFFSET` handling read from metadata | P1 |
| FR-3.4 | SCL cloud masking with a validity-fraction gate | P1 |
| FR-3.5 | NDVI anomaly vs the field's own history and vs village median | P1 |
| FR-3.6 | Within-field variability map at 10 m | P2 |
| FR-3.7 | Crop-type classification, farmer-confirmed (§26.3) | P2 |
| FR-3.8 | Sowing-date detection from the NDVI curve (§26.4) | P2 |
| FR-3.9 | Sentinel-1 SAR fallback during persistent monsoon cloud | P2 |
| FR-3.10 | Honest "no clear view since <date>" state | P1 |
| FR-3.11 | Satellite outputs never block the disease forecast | P0 |

🔴 **FR-3.11 is the important one.** Satellite enrichment is valuable but optional. If the satellite pipeline fails entirely, the forecast must still ship. The dependency runs one way only.

## 9.7 Acceptance criteria

- [ ] NDVI computed for a known field matches an independent GEE/QGIS computation to within 0.02
- [ ] A scene with the offset applied and one without produce measurably different NDVI (proving the offset is live)
- [ ] A cloudy field returns `null` and a human-readable explanation, never a number
- [ ] Within-field map renders in under 1 s on a mid-range Android device
- [ ] Complete satellite pipeline failure leaves the disease forecast unaffected

---

# 10. PILLAR ④ — EPIDEMIC SPREAD SIMULATION `[P1]`

> The forecast in §8 answers *"will conditions favour infection on my field?"*. This pillar answers the harder and more interesting question: **"the disease has been confirmed 3 km away — when does it reach me?"**

## 10.1 What it is

A spatial epidemic simulation over the 1 km grid. Confirmed outbreak reports (§16) become **inoculum sources**. Wind, distance, and local environmental suitability determine how spore pressure propagates outward over the next 7 days.

```
   DAY 0 — one confirmed outbreak            DAY 3 — with wind from NW
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │ · · · · · · · · · · · · · │             │ · · · · · · · · · · · · · │
   │ · · · · · · · · · · · · · │    wind     │ · · · · · · · · · · · · · │
   │ · · · ● · · · · · · · · · │    ↘↘↘      │ · · ▒▓█▓▒ · · · · · · · · │
   │ · · · · · · · · · · · · · │             │ · · ·▒▓▓▓▒▒· · · · · · · · │
   │ · · · · · · · · · · · · · │             │ · · · ·▒▒▒▒▒· · · · · · · │
   │ · · · · · · · · · · · · · │             │ · · · · ·▒▒· · · · · · · · │
   └───────────────────────────┘             └───────────────────────────┘
     ● confirmed outbreak                      █ high  ▓ moderate  ▒ elevated
                                               (asymmetric — stretched downwind)
```

## 10.2 The model

A **wind-weighted anisotropic dispersal kernel** combined with local suitability. Deliberately simple, because the input data does not justify anything more sophisticated.

```python
# engine/spread.py — PURE

def dispersal_weight(distance_km, bearing_deg, wind_dir_deg, wind_speed_ms,
                     half_distance_km=2.0, anisotropy=3.0):
    """
    Spore pressure contribution from one source to one target cell.

    · Isotropic base: exponential decay with distance
    · Anisotropic stretch: elongated downwind, compressed upwind
    · Wind speed scales the stretch — calm air gives a near-circular kernel
    """
    base = math.exp(-math.log(2) * distance_km / half_distance_km)
    angle_off = abs(((bearing_deg - wind_dir_deg + 180) % 360) - 180)  # 0=downwind
    alignment = math.cos(math.radians(angle_off))                       # +1 .. -1
    stretch = 1.0 + (anisotropy - 1.0) * min(wind_speed_ms / 5.0, 1.0) * alignment
    return base * max(stretch, 0.15)      # never exactly zero upwind

def spore_pressure(cell, sources, wind_series, decay_per_day=0.7):
    """Sum contributions from all active sources, ageing older reports."""
    total = 0.0
    for s in sources:
        age_factor = decay_per_day ** s.age_days
        total += s.severity * age_factor * dispersal_weight(...)
    return min(total, 1.0)

def combined_risk(env_risk, spore_pressure, w_env=0.65, w_inoc=0.35):
    """🔴 MULTIPLICATIVE, not additive — the disease triangle requires BOTH.
    Favourable weather with zero inoculum nearby is genuinely lower risk."""
    return (env_risk ** w_env) * (max(spore_pressure, 0.05) ** w_inoc)
```

🔴 **`combined_risk` is multiplicative and that is a scientific commitment, not a style choice.** Additive combination would let high spore pressure alone produce a red band on a dry sunny week — which is wrong. The disease triangle requires host *and* pathogen *and* environment simultaneously. The `max(spore_pressure, 0.05)` floor represents unobserved background inoculum: we never assume a region is genuinely spore-free, because our reporting coverage is incomplete.

## 10.3 Honest limitations `[P0]`

This is the pillar most likely to be over-claimed, so the limitations are specified as strictly as the model.

| Limitation | How the product handles it |
|---|---|
| Report coverage is sparse and biased toward engaged farmers | Never present absence of reports as absence of disease. Copy says *"no reports nearby"* — never *"no disease nearby"*. |
| Spore dispersal physics is far more complex than an exponential kernel | Presented as a **plausibility surface**, never a physical simulation. UI label: *"Likely spread direction"*. |
| Wind at 10 m is not wind in the canopy | Documented in the limitations page (§18.4) |
| Long-distance dispersal events exist and are unmodelled | Environment-driven risk (§8) is never suppressed by low spore pressure — the multiplicative floor guarantees this |
| Unconfirmed reports could be wrong or malicious | Only **verified** reports become sources (§16.4). Two independent confirmations, or one officer confirmation. |

🔴 **The rule:** the spread layer may **raise** attention. It may never be the sole reason a farmer is told they are safe. Environmental risk always has the floor.

## 10.4 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-4.1 | Verified outbreak reports become dated inoculum sources | P1 |
| FR-4.2 | Wind-weighted anisotropic dispersal over the 1 km grid | P1 |
| FR-4.3 | Source severity decays with report age | P1 |
| FR-4.4 | Multiplicative combination with environmental risk | P1 |
| FR-4.5 | 7-day animated spread visualisation (officer console + optional farmer view) | P2 |
| FR-4.6 | "Nearest confirmed report: 3.2 km, 4 days ago, downwind" on the field screen | P1 |
| FR-4.7 | Explicit copy distinguishing "no reports" from "no disease" | P0 |
| FR-4.8 | Spread layer can never reduce risk below the environmental floor | P0 |

## 10.5 Acceptance criteria

- [ ] A single source with 5 m/s NW wind produces a visibly asymmetric, downwind-stretched surface
- [ ] Zero sources anywhere leaves environmental risk completely unchanged
- [ ] High spore pressure during dry, unfavourable weather does **not** produce an act-band
- [ ] Report age decay is verifiable in the artefact output
- [ ] No UI string anywhere implies certified absence of disease

---

# 11. PILLAR ⑤ — GROUNDED AI AGRONOMIST `[P1]`

> **The feature most likely to be built badly, and the one with the most upside if built correctly.**

## 11.1 The problem with the obvious version

The obvious implementation is a chat box wired to an LLM with a prompt saying *"you are a helpful agricultural assistant."* That produces a system that will, when asked "how much mancozeb for one bigha", answer with a confident, specific, plausible number — which may be wrong, and which a farmer will act on. That is not a feature; it is a liability with a nice interface.

## 11.2 🔴 The architecture: the LLM is a translator, not an oracle

```
┌──────────────────────────────────────────────────────────────────────┐
│  WHAT THE LLM MAY DO                │  WHAT THE LLM MAY NEVER DO     │
├─────────────────────────────────────┼────────────────────────────────┤
│  ✅ Explain a number the engine     │  ❌ Produce a risk value       │
│     already computed                │  ❌ Produce a date or hour     │
│  ✅ Translate advisory text into    │  ❌ Produce a dose or product  │
│     any supported language          │     name                       │
│  ✅ Rewrite formal text into        │  ❌ Compute anything           │
│     simple spoken language          │  ❌ Recall agronomic facts     │
│  ✅ Answer questions using RETRIEVED│     from its own training      │
│     passages, with citation         │  ❌ Answer when retrieval      │
│  ✅ Say "I don't know — ask your    │     returns nothing            │
│     KVK officer"                    │                                │
└──────────────────────────────────────────────────────────────────────┘
```

💡 **The design insight:** the LLM's genuine, irreplaceable strength here is **language**, not knowledge. Turning `{band: "act", dsv: 19, spray_start: "Tue 06:00"}` into fluent, warm, dialect-appropriate spoken Bhojpuri is something no template system can do well and no rule engine can do at all. Knowledge comes from the retrieval corpus and the deterministic engine. **Separating those two roles is the whole design.**

## 11.3 The three modes

### Mode A — Advisory verbalisation `[P1]`

Runs in the nightly job, not at request time.

```
INPUT (structured, from the deterministic engine — no free text)
{
  "field_name": "नहर वाला खेत",
  "crop": "potato", "stage": "tuber_bulking",
  "band": "act", "model": "potato_late_blight_hutton",
  "reason_codes": ["RH90_8H", "TMIN_12C", "CONSECUTIVE_2D"],
  "spray_window": {"start": "2026-01-16T06:00+05:30", "end": "...T09:00+05:30"},
  "spray_blocked_after": "rain 14:00", "nearest_report_km": 3.2,
  "language": "hi", "register": "spoken_simple"
}

SYSTEM PROMPT (abridged — full version in §27.3)
  You render agricultural advisories into spoken language.
  You are given FACTS. You may ONLY restate the facts given.
  · Never introduce a number not present in the input.
  · Never name a pesticide product or a dose.
  · Never mention a date or time not present in the input.
  · Target: 45 words. Grade-5 reading level. Warm, direct, no hedging.
  · Output ONLY the advisory text.

OUTPUT
  "नमस्ते। आपके नहर वाले खेत में आलू की झुलसा बीमारी का खतरा है।
   पिछली दो रातें आठ घंटे तक बहुत नमी रही, और तापमान बारह डिग्री रहा।
   मंगलवार सुबह छह से नौ बजे के बीच दवा छिड़कें। दोपहर दो बजे बारिश
   आएगी, उसके बाद छिड़काव बेकार जाएगा।"

  → then §27.5 VALIDATION GATE, then TTS (§14)
```

🔴 **Every LLM output passes a programmatic validation gate before a farmer ever hears it (§27.5).** If it fails, the system falls back to a deterministic template. The LLM improves quality; it never gates delivery.

### Mode B — Grounded question answering `[P1]`

Farmer asks a question by voice. Retrieval-augmented, cited, and willing to refuse.

```
"मेरे आलू के पत्ते पीले क्यों हो रहे हैं?"
  → Bhashini ASR → Hindi text
  → embed → vector search over the curated corpus (§11.4)
  → retrieve top 5 passages + inject the farmer's live field context
  → LLM answers using ONLY those passages
  → cite: "स्रोत: ICAR आलू पैकेज ऑफ प्रैक्टिसेज, पृष्ठ 34"
  → TTS → spoken answer

If retrieval confidence < threshold:
  → "यह मुझे ठीक से नहीं पता। अपने KVK अधिकारी से पूछें।"
     + one-tap "Ask Dr. Kale" → routes to the officer console
```

🔴 **Refusal is a first-class feature, and the escalation path is what makes it acceptable.** "I don't know, ask your officer" is a correct and useful answer. An invented answer is neither. Routing the unanswered question to a real human turns a dead end into the product's most valuable data — a queue of real farmer questions that shows exactly where the corpus needs expanding.

### Mode C — Officer drafting assistant `[P2]`

For Dr. Kale, not for farmers. Different risk profile — the output is reviewed by a qualified human before dispatch.

```
Officer: "Draft a Hindi advisory for 12 villages in the act band,
          potato late blight, mention resistance rotation."
  → LLM drafts → officer EDITS → officer APPROVES → dispatch
  → 🔴 Nothing is sent without explicit officer approval.
```

## 11.4 The retrieval corpus `[HUMAN]`

🔴 **This is the highest-value manual work in the entire project, and it cannot be automated or generated.**

| Source | Content | Volume |
|---|---|---|
| ICAR crop package-of-practices | Authoritative crop management, per crop | ~50 docs |
| State agriculture department advisories | Regionally specific guidance | ~100 docs |
| KVK bulletins | Local, seasonal, practical | ~200 docs |
| Model source papers | Smith, Wallin, Hutton, BLITECAST | ~15 papers |
| FRAC resistance-management guidance | Fungicide group rotation rules | ~10 docs |
| PRAHARI's own documentation | How to read a band, what confidence means | ~20 pages |

```
Pipeline:  PDF → text extraction → 500-token chunks, 100-token overlap
           → sentence-transformer embeddings (multilingual, free, local)
           → vector store (pgvector on Postgres — no separate service)
           → 🔴 EVERY chunk carries: source · page · publication date · language
```

⚠️ **Never embed a document you cannot cite.** An uncited passage in the corpus becomes an uncitable claim in an answer, which is functionally identical to hallucination with extra steps.

## 11.5 Model choice

| Layer | Choice | Why | Cost |
|---|---|---|---|
| **Advisory verbalisation** | Gemini Flash (free tier, Google AI Studio) | Strong Indic languages, generous free quota, no card required | ₹0 `[VERIFY]` current quotas |
| **Question answering** | Same, with RAG | Consistency across modes | ₹0 |
| **Embeddings** | `sentence-transformers` multilingual, run locally | No API cost, no rate limit, no data leaves our infra | ₹0 |
| **Fallback / offline** | Fine-tuned Gemma (2B/4B) via LoRA (§26.7) | Runs on free GPU; removes third-party dependency | ₹0 |
| **Provider abstraction** | 🔴 One `LLMProvider` interface | Swap Gemini ↔ Claude ↔ local without touching product code | — |

🔴 **The provider abstraction is mandatory, not optional.** Free tiers change terms. A single interface with three implementations means a quota change is a config edit, not a rewrite.

```python
# adapters/llm/base.py
class LLMProvider(Protocol):
    def generate(self, system: str, user: str, max_tokens: int,
                 temperature: float) -> LLMResult: ...

# adapters/llm/gemini.py     — primary, free tier
# adapters/llm/local_gemma.py — fine-tuned fallback, self-hosted
# adapters/llm/template.py    — 🔴 deterministic, ALWAYS available, zero-dependency
```

## 11.6 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-5.1 | LLM verbalises advisories in the nightly job, never per-request | P1 |
| FR-5.2 | Output validation gate rejects invented numbers, dates, and product names | P0 |
| FR-5.3 | Deterministic template fallback on any LLM failure or gate rejection | P0 |
| FR-5.4 | Voice question answering with retrieval grounding | P1 |
| FR-5.5 | Every answer cites source, page, and date | P1 |
| FR-5.6 | Explicit refusal + officer escalation below a retrieval-confidence threshold | P0 |
| FR-5.7 | Live field context injected into every answer | P1 |
| FR-5.8 | Officer drafting assistant with mandatory human approval | P2 |
| FR-5.9 | Provider abstraction with ≥ 2 working implementations | P1 |
| FR-5.10 | All prompts and outputs logged for audit | P1 |
| FR-5.11 | Unanswered questions queued for corpus expansion | P2 |
| FR-5.12 | Hard rate limiting to stay inside the free tier | P0 |

## 11.7 Acceptance criteria

- [ ] An adversarial input attempting to elicit a dose recommendation is refused
- [ ] An LLM output containing a fabricated date is caught by the gate and replaced by the template
- [ ] Killing the LLM provider entirely still delivers every advisory (via templates)
- [ ] Every QA answer displays a citation
- [ ] An out-of-corpus question produces refusal + a working escalation link
- [ ] Daily LLM call volume stays inside the free tier at 10× current user count
- [ ] 🔴 A `[HUMAN]` review of 100 sampled outputs finds **zero** invented agronomic facts

---

# 12. PILLAR ⑥ — VISION CONFIRMATION `[P2]`

> Deliberately scoped as a **supporting** capability. Its primary product value is not diagnosis — it is **ground truth** (§26.5, §35).

## 12.1 The role

```
       ┌──────────────────────────────────────────────────────┐
       │  A farmer photographs a leaf                         │
       └──────────────────────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
  FOR THE FARMER           🔴 FOR THE SYSTEM
  "Does this look like     A dated, geolocated
   what was forecast?"     observation that
                           validates or refutes
  Confirmation of a        a specific prediction.
  warning already given.
                           This is what makes the
                           forecast measurable at all.
```

💡 **The reframe that makes this pillar worth building:** every other product treats the photograph as the output. Here it is the **input to a learning loop**. A farmer confirming "yes, spots appeared" three days after an act-band warning is one row of validation data that no amount of engineering can synthesise — and validation data is the scarcest resource in the entire project (§35.2).

## 12.2 Two-tier inference

```
TIER 1 — ON-DEVICE  (always available, offline, private, instant)
  MobileNetV3-Small, fine-tuned → ONNX opset 13 → int8 → ~4 MB
  Runs via onnxruntime-web. Image NEVER leaves the phone.
  ├── confidence ≥ 0.80 → show result + "matches your forecast" / "differs"
  └── confidence <  0.80 → offer Tier 2

TIER 2 — CLOUD  (optional, explicit consent, needs connection)
  Vision-capable LLM (Gemini free tier) for out-of-distribution images
  🔴 REQUIRES an explicit tap: "Send this photo for a closer look?"
  Never automatic. Never silent.
```

🔴 **The consent gate is non-negotiable.** A photograph of someone's field is their data. Uploading it without an explicit, per-image tap is a privacy violation regardless of what a terms-of-service page says.

## 12.3 Training `[P1]`

| Aspect | Specification |
|---|---|
| Base | MobileNetV3-Small (ImageNet pretrained) |
| Datasets | PlantVillage (clean lab images) + PlantDoc (field images) + our own collected field images |
| ⚠️ Critical | **PlantVillage alone will not generalise.** Uniform backgrounds and studio lighting; models trained on it collapse on a real phone photo in harsh field light. Field-condition data is mandatory. |
| Augmentation | Rotation, brightness/contrast jitter, motion blur, JPEG artefacts, partial occlusion, **hard shadow simulation** |
| Compute | Kaggle free GPU (~30 h/week) or Colab free tier |
| Export | PyTorch → ONNX opset 13 → dynamic int8 quantisation |
| Target | ≤ 5 MB, ≤ 400 ms inference on a mid-range Android device |
| 🔴 Held-out test | **Field photographs only.** Lab-image accuracy is a vanity metric here. |

## 12.4 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-6.1 | On-device inference, fully offline | P2 |
| FR-6.2 | Model bundle ≤ 5 MB, lazy-loaded on first use only | P2 |
| FR-6.3 | Confidence displayed; low confidence stated plainly | P2 |
| FR-6.4 | 🔴 Result explicitly compared against the active forecast | P2 |
| FR-6.5 | Optional cloud escalation behind explicit per-image consent | P2 |
| FR-6.6 | Scan result contributes to the ground-truth store | P1 |
| FR-6.7 | 🔴 Stored scans keep **cell reference only** — never raw GPS, never the image | P0 |
| FR-6.8 | Never presented as a diagnosis; always as a confirmation signal | P0 |
| FR-6.9 | Multi-photo capture guidance (whole plant, leaf top, leaf underside) | P2 |
| FR-6.10 | Optional farmer donation of an image to the training set, opt-in | P2 |

## 12.5 Acceptance criteria

- [ ] Airplane-mode scan completes end to end
- [ ] Bundle download does not occur until the scan feature is first opened
- [ ] Cloud upload is impossible without an explicit tap, verified by network inspection
- [ ] Stored records contain no lat/lon and no image bytes
- [ ] Held-out **field-image** accuracy is reported, not lab-image accuracy
- [ ] A confirmed scan measurably updates the validation dataset

---

# 13. PILLAR ⑦ — SPRAY WINDOW & OPERATIONS PLANNER `[P0]`

> The pillar that implements **P2 — instruction, not alert**. This is the difference between information and capability.

## 13.1 Why a risk band alone fails

A farmer told "high risk" faces four unanswered questions: spray today or tomorrow? morning or evening? it might rain — is it worth it? the sprayer is with my neighbour until Wednesday — is that too late?

Answering those converts a warning into an action. Not answering them means the warning is usually ignored, and correctly so.

## 13.2 The window algorithm

```python
# engine/spray.py — PURE

@dataclass(frozen=True)
class SprayGate:
    """Each gate is an independent veto with a farmer-readable reason."""
    name: str; reason_code: str; reason_hi: str

GATES = (
  SprayGate("no_rain_during",   "RAIN_NOW",   "छिड़काव के समय बारिश"),
  SprayGate("dry_after_hours",  "RAIN_AFTER", "छिड़काव के बाद बारिश — दवा धुल जाएगी"),
  SprayGate("wind_below_max",   "WIND_HIGH",  "तेज़ हवा — दवा उड़ जाएगी"),
  SprayGate("wind_above_min",   "WIND_CALM",  "हवा बिल्कुल नहीं — दवा ठीक से नहीं फैलेगी"),
  SprayGate("temp_in_range",    "TEMP_HIGH",  "बहुत गर्मी — दवा जल्दी सूख जाएगी"),
  SprayGate("daylight_hours",   "DARK",       "अंधेरा"),
  SprayGate("before_risk_onset","TOO_LATE",   "बीमारी शुरू होने से पहले छिड़कें"),
)

PARAMS = {
  "rain_free_hours_after": 4.0,   # rainfastness period [VERIFY per product class]
  "max_rain_mm_during":    0.2,
  "wind_max_ms":           4.0,   # ~14 km/h — drift threshold
  "wind_min_ms":           0.5,   # avoid inversion conditions
  "temp_max_c":           33.0,
  "min_window_hours":      2.0,
  "daylight_start":        6, "daylight_end": 18,
}

def find_windows(hourly, risk_onset_hour, params=PARAMS):
    """
    Score every candidate hour, keep runs of >= min_window_hours,
    return windows RANKED by quality, each with its blocking reasons.
    🔴 Windows must complete BEFORE risk onset — a protectant applied
       after infection begins has lost most of its value.
    """
```

🔴 **`before_risk_onset` is the gate that makes PRAHARI a *forecast* product rather than a weather app.** A perfect spraying day that falls after the infection event is not a usable window. Ordering matters.

## 13.3 What the farmer sees

```
┌─────────────────────────────────────────────────────┐
│  छिड़काव का समय                                     │
│                                                     │
│  मंगलवार सुबह ६ – ९ बजे              ★★★★☆         │
│  ─────────────────────────────────                  │
│                                                     │
│   Mon        TUE        Wed        Thu              │
│  ░░░░░░░  ▓▓███▓▓░░░  ░░░░░░░░  ▒▒▒▒▒▒            │
│           ↑                                         │
│           best                                      │
│                                                     │
│  ⚠️  दोपहर २ बजे बारिश — उससे पहले छिड़कें         │
│  ✓  हवा हल्की                                       │
│  ✓  बीमारी शुरू होने से पहले                       │
│                                                     │
│  [ 🔊 सुनें ]   [ याद दिलाएं ]   [ हो गया ]        │
└─────────────────────────────────────────────────────┘
```

Copy discipline: no product name, no dose, no chemical. **Timing only.** Product choice routes to the officer or dealer (§39.2).

## 13.4 🔴 The village collective window `[P1]`

The epidemiologically and logistically correct unit of action is often the **village, not the field**.

```
Individual optimal windows across 40 fields in Rampur:
   Mon 07–10  ██                     3 fields
   Tue 06–09  ██████████████████    28 fields   ← collective window
   Tue 15–17  ███                    6 fields
   Wed 06–08  ██                     3 fields

Collective recommendation: TUESDAY 06:00–09:00
  · 28 of 40 fields at their individual optimum
  · 12 fields slightly sub-optimal but still within acceptable gates
  · One shared sprayer can cover the village in the window
  · 🔴 No unsprayed reservoir left to reinfect the sprayed fields
```

💡 **The epidemiological argument is the strong one.** Spraying half a village and leaving the other half untreated creates an inoculum reservoir that reinfects the treated fields within one cycle. Synchronisation is not a convenience — it materially changes the outcome. This is also exactly what Ravi (§3.4) needs to schedule one sprayer across forty fields.

Constraint: the collective window is only recommended when **≥ 60% of fields** can be served without violating any hard gate. Otherwise the app reports two staggered windows rather than forcing a bad compromise.

## 13.5 Resistance management `[P2]`

Repeated use of the same fungicide mode of action drives resistance. FRAC codes group products by mode of action, and rotation rules are published and purely rule-based — a good fit for deterministic logic.

```
Spray history for this field this season:
  Dec 12 — FRAC M03 (multi-site)      ✓
  Dec 26 — FRAC 4    (single-site)    ✓
  Jan 08 — FRAC 4    (single-site)    ⚠️  second consecutive FRAC 4

Advisory: "पिछली दो बार एक ही तरह की दवा इस्तेमाल हुई।
           इस बार अलग तरह की दवा के बारे में अधिकारी से पूछें।"
          ("The last two sprays used the same type of medicine.
            Ask your officer about a different type this time.")
```

🔴 **Note the copy carefully: it flags a pattern and routes to a human.** It does not name a replacement product. That boundary is what keeps this feature legal and safe (§39.2).

## 13.6 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-7.1 | Hourly window scoring with all seven gates | P0 |
| FR-7.2 | Ranked windows, each with blocking reasons | P0 |
| FR-7.3 | Windows must complete before forecast risk onset | P0 |
| FR-7.4 | Human-readable reason for every blocked period | P0 |
| FR-7.5 | Village collective window with a 60% coverage rule | P1 |
| FR-7.6 | "No suitable window in 7 days" state with an explanation | P0 |
| FR-7.7 | Reminder scheduling — local notification, works offline | P1 |
| FR-7.8 | "Done" logging feeding the operations record (§15) | P1 |
| FR-7.9 | FRAC rotation flag from spray history | P2 |
| FR-7.10 | 🔴 Never name a product or specify a dose | P0 |
| FR-7.11 | Window text pre-rendered into voice audio (§14) | P0 |

## 13.7 Acceptance criteria

- [ ] Rain 2 h after a candidate window blocks that window with the `RAIN_AFTER` reason
- [ ] A window that would end after risk onset is excluded
- [ ] "No window available" renders as a helpful explanation, never a blank screen
- [ ] The collective window is suppressed when coverage falls below 60%
- [ ] No UI string, template, or LLM output contains a pesticide product name — enforced by an automated string test
- [ ] Reminders fire correctly in airplane mode

---

# 14. PILLAR ⑧ — VOICE & MULTILINGUAL DELIVERY `[P0]`

> Implements **P4 — voice is the product, the screen is the accessory.**

## 14.1 The requirement

Sunita (§3.1) reads slowly and prefers to listen. Designing text-first and adding audio later produces audio that sounds like read-aloud text — stilted, over-long, and skipped. Designing audio-first produces both a good advisory and a screen that mirrors it.

**Test:** switch the screen off. If the product still works, it works for the person who needs it most.

## 14.2 🔴 The pre-generation law

> **All advisory audio is generated in the nightly job. Never at request time. Never per farmer.**

```
❌ WRONG                              ✅ RIGHT
farmer opens app                      nightly job:
  → request TTS                         · compute advisories
  → wait 2–4 s on 2G                    · group by (text_hash, language)
  → often fails on poor network         · generate audio ONCE per unique text
  → cost scales with users              · store as static files
                                        · farmer streams or plays cached
                                      cost scales with DISTINCT MESSAGES
```

💡 **The economics of this are decisive.** 50,000 farmers in a district collapse into perhaps 40 distinct advisory messages per night — a handful of bands × languages × window texts. Pre-generation makes audio cost effectively independent of user count, which is what makes §8 of the product principles (zero marginal cost) survive scale. It is also **faster and more reliable**, because playing a cached file beats a live API call on 2G every time.

**Regeneration rule:** hash the advisory text. Regenerate only when the hash changes. Unchanged text reuses yesterday's file.

## 14.3 Language stack

| Layer | Primary | Fallback | Cost |
|---|---|---|---|
| **TTS** | Bhashini / ULCA (MeitY) — Indian government Indic TTS | `edge-tts` (free, no key) → recorded human audio for critical messages | ₹0 `[VERIFY]` access flow |
| **ASR** (for voice questions) | Bhashini ASR | Fine-tuned Whisper-small (§26.8) | ₹0 |
| **Translation** | Bhashini NMT | LLM translation with the §27.5 gate | ₹0 |
| **UI strings** | Human-translated, reviewed | — | `[HUMAN]` |

🔴 **UI strings and safety-critical copy are human-translated and human-reviewed, never machine-translated.** A mistranslated spray instruction is a real-world harm. `[HUMAN]`

## 14.4 Language coverage

| Phase | Languages |
|---|---|
| Launch | Hindi, English |
| Next | Marathi, Bengali, Telugu, Tamil |
| Then | Punjabi, Gujarati, Kannada, Odia, Malayalam, Assamese |
| Aspiration | Major dialects — Bhojpuri, Awadhi, Marwari — where TTS support allows |

⚠️ **Dialect matters more than the language list suggests.** Formal Hindi TTS is understood in Farrukhabad but is not how people speak. Where Bhashini offers dialect voices, use them. Where it does not, keep vocabulary simple and sentences short — this improves comprehension in every dialect simultaneously.

## 14.5 Advisory script structure

A fixed four-part structure, 40–50 words, ~20 seconds. Structure aids comprehension and lets the farmer predict what comes next.

```
1. WHICH FIELD   "आपके नहर वाले खेत में..."          ← 🔴 always first
2. WHAT          "...आलू की झुलसा बीमारी का खतरा है।"
3. WHY (brief)   "पिछली दो रातें आठ घंटे नमी रही।"
4. WHEN TO ACT   "मंगलवार सुबह छह से नौ बजे छिड़कें।"
```

🔴 **The field name comes first, always.** For a farmer with three parcels, "which field" is the most important word in the message. Leading with the disease name forces them to hold the alarm in memory while waiting for the location.

## 14.6 Multi-channel delivery

A smartphone PWA reaches a large population but not all of it. The same engine output drives four channels.

| Channel | Reach | Notes |
|---|---|---|
| **PWA (in-app)** | Smartphone owners | Full experience; offline-capable |
| **WhatsApp** | Very wide in rural India | Text + voice note. Free tier for service messages `[VERIFY]` limits |
| **SMS** | Universal | 160-char text summary — the honest floor |
| **IVR outbound call** | 🔴 **Feature-phone owners — the highest-need group** | Same pre-generated audio played over a call. Requires a telephony partner; `[VERIFY]` free/subsidised routes such as government or CSC channels |

💡 **IVR is where the product reaches the people who need it most.** A farmer with a ₹1,200 feature phone and no data plan is precisely the farmer with the least access to advisory services and the most to lose. Because audio is already pre-generated (§14.2), IVR requires no new content pipeline — only a dialer. That is a deliberate architectural payoff.

## 14.7 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-8.1 | All advisory audio pre-generated nightly | P0 |
| FR-8.2 | Regeneration only on text-hash change | P0 |
| FR-8.3 | Audio cached on device; offline playback | P0 |
| FR-8.4 | Prominent play control on every advisory surface | P0 |
| FR-8.5 | Field name spoken first | P0 |
| FR-8.6 | Voice-guided onboarding, including field mapping (§7) | P0 |
| FR-8.7 | Voice input for field names and questions | P1 |
| FR-8.8 | Language switch at any time, taking effect immediately | P0 |
| FR-8.9 | Text always available alongside audio | P0 |
| FR-8.10 | Speed control (0.75× / 1× / 1.25×) | P2 |
| FR-8.11 | SMS fallback within 160 characters | P1 |
| FR-8.12 | WhatsApp delivery with voice note | P1 |
| FR-8.13 | IVR-compatible audio format and duration | P2 |
| FR-8.14 | TTS failure degrades to text + a recorded generic band message | P0 |

## 14.8 Acceptance criteria

- [ ] A complete advisory is understood by a non-literate test user with the screen covered `[HUMAN]`
- [ ] Audio plays in airplane mode after one online session
- [ ] Unchanged advisory text triggers zero TTS calls on the second night
- [ ] Distinct-audio-file count per district-night is under 60 regardless of user count
- [ ] Total TTS API calls scale with distinct messages, not users — verified in job logs
- [ ] Every advisory audio clip is under 30 seconds
- [ ] Complete TTS provider outage still delivers text plus a generic recorded band message

---

# 15. PILLAR ⑨ — FIELD OPERATIONS RECORD `[P1]`

> The unglamorous pillar that makes everything else measurable — and quietly delivers the most durable value to the farmer.

## 15.1 Why it earns its place

Three distinct payoffs from one simple feature:

1. **For the farmer** — a season record they have never had. What was sprayed, when, what it cost, what the weather was doing. This is the basis of every improvement they can make next season.
2. **For the model** — 🔴 spray events are *confounders*. A field that was sprayed and did not get sick is not evidence the forecast was wrong. Without spray records, validation (§35) is fundamentally broken.
3. **For institutions** — a real, honest record of input use at village scale, which currently does not exist anywhere.

💡 **Point 2 is the one people miss, and it is the important one.** An early-warning system that works *causes the outcomes it predicted not to happen*. Without knowing who acted on a warning, you cannot distinguish "the forecast was wrong" from "the forecast worked." Spray records are not a nice-to-have; they are the instrument that makes the product's own accuracy knowable.

## 15.2 Logging design

Logging must take **under 10 seconds** or it will not happen.

```
┌─────────────────────────────────────────────────────┐
│  छिड़काव दर्ज करें                                   │
│                                                     │
│  खेत:     [ नहर वाला खेत      ▾ ]                  │
│  कब:      [ आज ]  [ कल ]  [ चुनें ]                │
│  दवा का प्रकार:                                     │
│     ○ बहु-स्थल (मल्टी-साइट)                        │
│     ○ एकल-स्थल (सिस्टेमिक)                         │
│     ○ पता नहीं                    ← 🔴 always valid  │
│  खर्च (वैकल्पिक):  [ ₹___ ]                        │
│                                                     │
│  [ 🎤 बोलकर बताएं ]          [ दर्ज करें ]          │
└─────────────────────────────────────────────────────┘
```

🔴 **"Don't know" must always be a valid answer.** A required field the farmer cannot answer causes them to abandon the form or enter something false. Both outcomes are worse than a recorded "unknown". We ask for the FRAC *class* rather than the product name — that is enough for rotation advice (§13.5), and it is a question farmers can actually answer.

## 15.3 What is tracked

| Event | Fields |
|---|---|
| **Spray** | field, date, FRAC class or unknown, cost (optional), area covered |
| **Irrigation** | field, date, method, duration (optional) |
| **Observation** | field, date, what was seen, optional photo (§12) |
| **Sowing / harvest** | field, date, variety, yield (optional) |
| **Advisory receipt** | 🔴 auto-logged — which advisory, when delivered, when opened, when played |

## 15.4 The season summary

At season end, a single shareable page:

```
┌────────────────────────────────────────────────────┐
│  आलू का मौसम २०२५–२६ · नहर वाला खेत                │
│                                                    │
│  चेतावनी मिली         ४ बार                        │
│  छिड़काव किया         ३ बार                         │
│  कुल खर्च             ₹२,४००                        │
│                                                    │
│  ⚠️  एक चेतावनी पर छिड़काव नहीं हुआ (१४ जनवरी)      │
│                                                    │
│  पिछले साल के मुकाबले: १ छिड़काव कम                 │
│                                                    │
│  [ 📄 PDF ]   [ 🔊 सुनें ]   [ अधिकारी को भेजें ]   │
└────────────────────────────────────────────────────┘
```

⚠️ **Show the missed warning.** Hiding it would be flattering and dishonest. A farmer who sees "you did not act on one warning" learns something real, and a product that reports its own unheeded advice is one that can be trusted about the advice that was heeded (P5).

## 15.5 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-9.1 | Spray logging in under 10 seconds, ≤ 4 taps | P1 |
| FR-9.2 | "Don't know" valid for every optional attribute | P1 |
| FR-9.3 | Fully offline logging with background sync | P1 |
| FR-9.4 | Voice logging | P2 |
| FR-9.5 | Auto-logged advisory delivery, open, and play events | P1 |
| FR-9.6 | Season summary, printable and shareable | P1 |
| FR-9.7 | Year-over-year comparison once history exists | P2 |
| FR-9.8 | 🔴 Spray records used as confounders in validation (§35) | P0 |
| FR-9.9 | Farmer can export or delete their entire record | P0 |
| FR-9.10 | Officer can view records for consenting farmers only | P1 |

## 15.6 Acceptance criteria

- [ ] Median logging time under 10 s in a `[HUMAN]` usability test
- [ ] Offline log entries sync correctly and idempotently on reconnect
- [ ] Season summary renders correctly with zero logged events (empty state)
- [ ] Validation pipeline demonstrably excludes sprayed fields from outbreak scoring
- [ ] Data export produces complete, readable output; deletion is genuinely complete

---

# 16. PILLAR ⑩ — COMMUNITY OUTBREAK NETWORK `[P1]`

> The pillar that compounds. Every other feature is static value; this one improves with each user.

## 16.1 The loop

```
   ┌──────────────────────────────────────────────────────────┐
   │                                                          │
   │   Farmer confirms an outbreak                            │
   │              │                                           │
   │              ▼                                           │
   │   Verification (§16.4) — 2 independent reports            │
   │   OR 1 officer confirmation                              │
   │              │                                           │
   │              ▼                                           │
   │   ①  Becomes an inoculum source → spread model (§10)      │
   │   ②  Becomes ground truth → validation (§35)              │
   │   ③  Becomes training data → ML correction (§26.5)        │
   │              │                                           │
   │              ▼                                           │
   │   Neighbouring farmers get an earlier, better warning     │
   │              │                                           │
   │              ▼                                           │
   │   Trust increases → more farmers report ──────────────────┘
   │
   └──────────────────────────────────────────────────────────┘
```

💡 **This is the only part of PRAHARI that gets structurally better with scale**, and it is what turns a forecasting tool into a network. Ten farmers reporting in a district is noise; two thousand is a real-time epidemiological sensing layer that no amount of satellite or weather data can substitute for. It is also the mechanism by which the product earns the right to make spread claims (§10).

## 16.2 🔴 Privacy architecture

Outbreak reporting means asking farmers to disclose that their crop is diseased. That is **commercially and socially sensitive information** — it affects land value, lease negotiations, and social standing. Getting this wrong does real harm and destroys reporting immediately.

```
┌────────────────────────────────────────────────────────────────┐
│  WHAT IS STORED                 │  WHAT IS NEVER STORED        │
├─────────────────────────────────┼──────────────────────────────┤
│  · 1 km cell reference          │  ❌ Farmer name              │
│  · Date                         │  ❌ Exact GPS coordinates    │
│  · Crop + suspected pathogen    │  ❌ Field polygon            │
│  · Severity bucket (low/med/hi) │  ❌ Phone number (hash only) │
│  · Anonymous device hash        │  ❌ The photograph itself    │
│  · Officer-verified flag        │                              │
└────────────────────────────────────────────────────────────────┘
```

🔴 **k-anonymity is enforced in the database schema, not in application code.**

```sql
CREATE VIEW cell_observations_public AS
SELECT cell_id,
       COUNT(*)                                        AS report_count,
       MODE() WITHIN GROUP (ORDER BY suspected_pathogen) AS common_report,
       MAX(report_date)                                AS latest_report
FROM outbreak_report
WHERE verified = true
GROUP BY cell_id
HAVING COUNT(DISTINCT device_hash) >= 5;   -- 🔴 k=5 IN THE SCHEMA
```

💡 **Why the schema and not the code:** application-layer privacy is one forgotten `WHERE` clause away from a leak. A view that structurally cannot return a group smaller than 5 distinct reporters cannot leak, no matter what query a future developer writes against it. Enforcement belongs at the layer that cannot be bypassed by accident.

⚠️ **Small-village edge case:** in a village with 6 farmers, k=5 means almost nothing is ever shown. Correct handling is to **aggregate upward to a 5×5 km block** rather than lower k. Never lower k to make a feature work.

## 16.3 What farmers see

Never a list of who is sick. Aggregate, directional, and actionable:

```
┌──────────────────────────────────────────────────────┐
│  आपके आस-पास                                         │
│                                                      │
│  🔴 ३.२ किमी दूर झुलसा की पुष्टि                     │
│      ४ दिन पहले · अधिकारी ने जांचा                   │
│      हवा उस तरफ से आ रही है  ↖                       │
│                                                      │
│  आपके गाँव में इस हफ्ते ७ किसानों को चेतावनी          │
│                                                      │
│  ℹ️  यहाँ रिपोर्ट न होने का मतलब बीमारी न होना       │
│      नहीं है।                                        │
│      ("No reports here does not mean no disease.")   │
└──────────────────────────────────────────────────────┘
```

🔴 **That last line is mandatory on every community surface.** Our reporting coverage is sparse and biased. Allowing a farmer to read silence as safety is the most likely way this feature causes harm.

## 16.4 Verification ladder

| Level | Requirement | Weight in the spread model |
|---|---|---|
| **Unverified** | 1 farmer report | 0 — visible to officers only, never used |
| **Corroborated** | 2+ independent reports, same cell, within 5 days | 0.6 |
| **Officer-verified** | 1 KVK officer confirmation | 1.0 |
| **Lab-confirmed** | Laboratory diagnosis | 1.0 + marked as ground truth for validation |

🔴 **Only corroborated and above enter the spread model.** A single unverified report is not evidence, and treating it as such makes the system trivially manipulable — by a mistaken farmer or a malicious one.

## 16.5 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-10.1 | Outbreak reporting in ≤ 5 taps, with voice option | P1 |
| FR-10.2 | Optional photo, processed on-device, image never stored | P1 |
| FR-10.3 | 🔴 Cell-level storage only; no coordinates, no name | P0 |
| FR-10.4 | Four-level verification ladder | P1 |
| FR-10.5 | k≥5 anonymity enforced in the schema | P0 |
| FR-10.6 | Upward spatial aggregation for sparse areas — never lower k | P0 |
| FR-10.7 | Directional nearby-report display with distance and age | P1 |
| FR-10.8 | 🔴 "No reports ≠ no disease" copy on every community surface | P0 |
| FR-10.9 | Verified reports feed the spread model (§10) | P1 |
| FR-10.10 | 🔴 Reports feed the append-only validation ledger (§36) | P0 |
| FR-10.11 | Officer verification queue | P1 |
| FR-10.12 | Report withdrawal by the reporting farmer | P0 |
| FR-10.13 | Rate limiting and abuse detection | P1 |

## 16.6 Acceptance criteria

- [ ] Direct query attempts cannot retrieve a report attributable to an individual
- [ ] The public view returns nothing for a cell with 4 distinct reporters
- [ ] A 4-reporter cell aggregates upward to a block instead of lowering k
- [ ] An unverified report has zero effect on any forecast
- [ ] The disclaimer copy is present on every community screen — verified by an automated test
- [ ] A withdrawn report is removed from the spread model on the next run
- [ ] Reports become append-only ledger entries (§36)

---

# 17. PILLAR ⑪ — EXTENSION OFFICER CONSOLE `[P1]`

> Implements **P7 — amplify the extension system.** Built for Dr. Kale (§3.2), who reaches more farmers in one week than the app will in six months.

## 17.1 The core screen — weekly triage

Arun's actual question is not "what is the risk map". It is **"which of my 40 villages do I visit this week, and in what order?"**

```
┌───────────────────────────────────────────────────────────────────────┐
│  फर्रुखाबाद KVK · सप्ताह २ · आलू                    [ नक्शा ] [ सूची ] │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  प्राथमिकता  गाँव        खेत   जोखिम  छिड़काव खिड़की  रिपोर्ट  कार्रवाई │
│  ─────────────────────────────────────────────────────────────────── │
│  🔴 १        रामपुर       ४२    उच्च   मंगल ६–९      २ ✓     [जाएं]  │
│  🔴 २        नगला         ३८    उच्च   मंगल ६–९      १       [जाएं]  │
│  🟠 ३        भोजपुर       ५१    मध्यम  बुध ७–१०      ०       [भेजें] │
│  🟠 ४        कायमगंज      २९    मध्यम  बुध ७–१०      ०       [भेजें] │
│  🟢 ५        मोहम्मदाबाद   ३३    कम     —             ०       —      │
│  ...                                                                  │
│                                                                       │
│  [ ⚡ शीर्ष ४ गाँवों को सलाह भेजें ]   [ 📄 साप्ताहिक बुलेटिन PDF ]    │
└───────────────────────────────────────────────────────────────────────┘
```

🔴 **Ranked and actionable, not a visualisation.** Sort key: risk band, then field count (impact), then unverified report count (needs eyes), then days since last visit. Every row has one primary action.

## 17.2 Capabilities

| Capability | Description | Priority |
|---|---|---|
| **Weekly triage** | Ranked village list with one action per row | P1 |
| **Model trace** | 🔴 Full rule trace for any cell — the numbers, the thresholds, the intermediate values | P1 |
| **Bulk advisory** | Send to selected villages, LLM-drafted, officer-edited, officer-approved | P1 |
| **Verification queue** | Confirm or reject farmer outbreak reports | P1 |
| **Assisted field mapping** | Map fields for farmers who cannot (§7.2 Method C) | P1 |
| **Farmer roster** | Consenting farmers, fields, contact, advisory history | P1 |
| **Spread animation** | 7-day spread simulation playback (§10) | P2 |
| **Weekly bulletin** | Printable PDF for noticeboards and WhatsApp groups | P1 |
| **Offline field mode** | Full offline operation during village visits, syncing later | P1 |
| **Feedback loop** | 🔴 "The forecast was wrong here, and this is why" — routed to the model team | P1 |

## 17.3 🔴 The model trace — the credibility feature

This single screen determines whether Arun trusts the product or dismisses it.

```
┌────────────────────────────────────────────────────────────────┐
│  रामपुर · कोशिका FRK-R014-C022 · १४ जनवरी २०२६                 │
│  मॉडल: potato_late_blight_hutton v2.0.0                        │
│  इंजन: a3f9c21 · डेटा: Open-Meteo, ०२:१४ बजे लाया गया           │
├────────────────────────────────────────────────────────────────┤
│  HUTTON CRITERIA                                               │
│                                                                │
│  १३ जनवरी   न्यूनतम तापमान  ११.८ °C   ≥ १० °C  ✓              │
│             नमी ≥ ९०% घंटे    ७ घं.    ≥ ६ घं.  ✓  → योग्य     │
│  १४ जनवरी   न्यूनतम तापमान  १२.४ °C   ≥ १० °C  ✓              │
│             नमी ≥ ९०% घंटे    ८ घं.    ≥ ६ घं.  ✓  → योग्य     │
│                                                                │
│  लगातार २ योग्य दिन → 🔴 मापदंड पूरा                            │
│                                                                │
│  WALLIN DSV                                                    │
│  नम अवधि का औसत तापमान  १४.१ °C  → बैंड ११.७–१५.० °C          │
│  उस अवधि में नम घंटे      ८ घं.    → DSV आज = ३                │
│  ७ दिन का संचित DSV      १९       → सीमा १८ से अधिक ✓          │
│                                                                │
│  भरोसा: ०.८२ (उच्च) — ४ मौसम बिंदुओं में अंतर कम               │
│  स्थानिक योगदान: ०.१४ (३.२ किमी दूर पुष्ट रिपोर्ट)             │
│                                                                │
│  [ 📋 गणना डाउनलोड करें ]   [ ⚠️ यह गलत है ]                   │
└────────────────────────────────────────────────────────────────┘
```

💡 **Note what this screen does: it shows the intermediate values, including the ones that could reveal a bug.** Mean-temp-during-spell is displayed separately from anything else precisely because that is where implementations go wrong (§8.6, bug 2). An officer with an M.Sc. in Plant Pathology can read this screen and catch our errors — and the "यह गलत है" (this is wrong) button makes doing so a one-tap contribution rather than a phone call nobody makes.

## 17.4 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-11.1 | Ranked weekly triage across the officer's villages | P1 |
| FR-11.2 | Full model trace with all intermediate values | P1 |
| FR-11.3 | Bulk advisory with mandatory officer approval | P1 |
| FR-11.4 | Outbreak verification queue | P1 |
| FR-11.5 | Assisted field mapping | P1 |
| FR-11.6 | Printable weekly bulletin PDF | P1 |
| FR-11.7 | Offline-capable field mode with sync | P1 |
| FR-11.8 | "This forecast is wrong" reporting with structured reason capture | P1 |
| FR-11.9 | Desktop-optimised, but functional on a tablet | P1 |
| FR-11.10 | Role-based access — officers see only their assigned villages | P1 |
| FR-11.11 | Farmer data visible only with recorded consent | P0 |
| FR-11.12 | Calculation export as CSV/JSON for independent verification | P1 |

## 17.5 Acceptance criteria

- [ ] `[HUMAN]` A plant pathologist reads the trace screen and can independently reproduce the verdict
- [ ] Mean-temp-during-spell is displayed as a distinct labelled value
- [ ] No advisory can be dispatched without an explicit approval action
- [ ] The console operates offline for a full village visit and syncs cleanly
- [ ] An officer cannot access a village outside their assignment
- [ ] Exported calculations reproduce the stated result when recomputed independently

---

# 18. PILLAR ⑫ — TRANSPARENCY & VALIDATION `[P0]`

> Implements **P5 — honesty over polish.** This pillar is the reason a scientist would take the rest seriously.

## 18.1 The public accuracy page

Publicly accessible, no login, updated automatically.

```
┌───────────────────────────────────────────────────────────────────┐
│  PRAHARI · सटीकता · Accuracy                                      │
│  Model: potato_late_blight_hutton v2.0.0                          │
│  Season 2025–26 · Farrukhabad · 3,612 cells × 118 days            │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│                        OBSERVED                                   │
│                   outbreak    no outbreak                         │
│  PREDICTED  act  │    47    │     71     │  118                   │
│             safe │    14    │   4,893    │  4,907                 │
│                  │    61    │   4,964    │  5,025                 │
│                                                                   │
│  POD  (hit rate)              0.77   ← farmers warned             │
│  FAR  (false alarm ratio)     0.60   ← ⚠️ high, and DELIBERATE    │
│  CSI  (critical success)      0.36                                │
│  Mean lead time              62 h                                 │
│                                                                   │
│  🔴 Expected farmer cost with PRAHARI:   ₹6,15,150                │
│     Expected farmer cost with calendar                            │
│     spraying (the status quo):           ₹9,84,000                │
│     Expected cost doing nothing:        ₹24,40,000                │
│                                                                   │
│  Why we accept a 0.60 false alarm ratio →  §38.2                  │
│                                                                   │
│  [ Download full dataset (CSV) ]   [ Methodology ]   [ Limitations ]│
└───────────────────────────────────────────────────────────────────┘
```

🔴 **Publishing FAR = 0.60 is the single most credibility-building decision available to this project.** It is a bad-looking number. Showing it, next to the economic argument for why it is nonetheless the correct trade-off, demonstrates that we understand our own model better than a polished 94% would. Anyone can hide a false alarm rate; only someone who has actually done the analysis can defend one.

⚠️ Numbers shown are illustrative of the format. Real values are published once real validation exists (§35), whatever they turn out to be.

## 18.2 The alert ledger

Every alert ever sent, in a public hash-chained log.

```python
# Each entry chains to the previous — tampering with any record
# invalidates every subsequent hash.
{
  "seq": 14027,
  "timestamp": "2026-01-14T02:14:07+05:30",
  "cell_id": "FRK-R014-C022",
  "model": "potato_late_blight_hutton@2.0.0",
  "engine_sha": "a3f9c21",
  "band": "act",
  "inputs_digest": "sha256:7f3a...",
  "prev_hash": "sha256:9c1e...",
  "hash": "sha256:4b8d..."
}

def compute_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
```

**Four independent integrity layers:**

| Layer | What it prevents |
|---|---|
| The hash chain | Silent editing of a past prediction |
| Git commit history | Backdating the file itself |
| CI verification on every push | An unnoticed broken chain |
| 🔴 **Client-side `ChainVerifier`** | Having to trust *us* — the sceptic recomputes the chain in their own browser |

💡 **The fourth layer is the whole point.** "Trust our accuracy page" is a request. "Here is a button that recomputes our entire history in your browser and tells you if we lied" is a proof. It costs about eighty lines of TypeScript, and it is the most persuasive thing in the product.

## 18.3 The methodology page

Public, plain-language, and specific:

- Where weather data comes from, and its native resolution
- 🔴 That RH is a **proxy** for leaf wetness, not a measurement of it
- That the 1 km grid is a **presentation and computation** resolution, downscaled from ~11 km native — not a sensing resolution
- Exactly how ground truth was collected and when it was frozen
- That negative cases are scored, not just outbreaks
- Every model's citation and parameter values
- The ML correction layer's training data, size, and limits

## 18.4 The limitations page

🔴 **A first-class product surface, linked from the footer of every screen.**

| Limitation | Stated plainly |
|---|---|
| RH is not leaf wetness | "We estimate how long leaves stay wet from humidity. We do not measure it. A sensor in your field would be more accurate." |
| Interpolated weather | "Weather comes from points ~11 km apart. We estimate the values in between, correcting for hill height. Fields in unusual spots — deep hollows, near large water bodies — may differ." |
| Sparse ground truth | "Our accuracy is measured against a limited number of confirmed outbreaks. It will improve as more are reported." |
| Spread is a plausibility surface | "Spread direction is an estimate based on wind and distance. It is not a measurement of where spores actually are." |
| Variety resistance not modelled | "Some potato varieties resist blight better. We do not yet account for variety." |
| Model coverage is finite | "We only forecast the crops and diseases listed. Silence about a disease means we do not model it, not that it is absent." |
| Not a substitute for a person | "PRAHARI helps you decide when to act. It does not replace your KVK officer or your own eyes." |

## 18.5 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-12.1 | Public accuracy page with the full contingency table | P0 |
| FR-12.2 | 🔴 POD, FAR, CSI, lead time published even when unflattering | P0 |
| FR-12.3 | Expected-farmer-cost comparison against calendar spraying and doing nothing | P0 |
| FR-12.4 | Public hash-chained alert ledger | P0 |
| FR-12.5 | Client-side chain verification in the browser | P1 |
| FR-12.6 | CI fails the build on a broken chain | P0 |
| FR-12.7 | Methodology page, plain language | P0 |
| FR-12.8 | Limitations page, linked from every screen footer | P0 |
| FR-12.9 | Full validation dataset downloadable as CSV | P1 |
| FR-12.10 | Model registry with versions, parameters, and citations | P0 |
| FR-12.11 | Every forecast output stamped with model version and engine SHA | P0 |

## 18.6 Acceptance criteria

- [ ] The accuracy page renders correctly with zero validation data (honest empty state)
- [ ] Manually altering one ledger record causes client-side verification to fail
- [ ] CI rejects a push containing a broken chain
- [ ] Every screen has a reachable link to the limitations page
- [ ] The downloadable dataset reproduces the published metrics when recomputed
- [ ] Every artefact carries model version and engine commit SHA

---

# ═══════════════════════════════════════
# PART III — EXPERIENCE
# ═══════════════════════════════════════

# 19. INFORMATION ARCHITECTURE & SCREEN INVENTORY

## 19.1 Three distinct applications

PRAHARI is not one app. It is three surfaces with different users, different devices, and different design languages.

| Surface | User | Device | Design language |
|---|---|---|---|
| **Farmer app** | Sunita (§3.1) | Mid-range Android, portrait, sunlight | Light, high contrast, huge touch targets, voice-first |
| **Officer console** | Arun (§3.2) | Desktop + tablet, offline in the field | Dense, dark, information-rich, keyboard-driven |
| **Public trust site** | Priya (§3.3), press, judges | Any browser | Documentary, typographic, no login |

## 19.2 Farmer app — full navigation map

```
                          ┌────────────────┐
                          │  FIRST LAUNCH  │
                          └────────┬───────┘
                                   ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  ONBOARDING  (§20)                                               │
  │  01 Language pick ▸ 02 Voice welcome ▸ 03 Location permission     │
  │  ▸ 04 FIELD MAPPING ▸ 05 Crop & sowing ▸ 06 Name the field       │
  │  ▸ 07 Alert preferences ▸ 08 Done                                │
  └──────────────────────────────┬───────────────────────────────────┘
                                 ▼
  ╔══════════════════════════════════════════════════════════════════╗
  ║  ①  आज  ·  TODAY            (home — the default landing)         ║
  ║      Per-field status cards · today's action · play advisory      ║
  ╚══════════════════════════════════════════════════════════════════╝
     │
     ├─▶ ②  खेत  ·  FIELD DETAIL          ← tap a field card
     │      ├─▶ ②a  7-day forecast timeline
     │      ├─▶ ②b  Why this warning (3-depth disclosure, §21.4)
     │      ├─▶ ②c  Field health / satellite (§9)
     │      ├─▶ ②d  In-field variability map (§9.5)
     │      └─▶ ②e  Field settings — crop, boundary edit, name, delete
     │
     ├─▶ ③  नक्शा  ·  MY MAP               ← 🔴 satellite, MY fields
     │      ├─▶ ③a  Neighbourhood risk view
     │      ├─▶ ③b  Spread animation (§10)
     │      └─▶ ③c  Add another field (→ §20 mapping flow)
     │
     ├─▶ ④  छिड़काव  ·  SPRAY PLAN         (§13)
     │      ├─▶ ④a  Window detail + why blocked
     │      ├─▶ ④b  Village collective window
     │      └─▶ ④c  Set reminder
     │
     ├─▶ ⑤  पूछें  ·  ASK                  (§11 — voice-first)
     │      ├─▶ ⑤a  Voice question
     │      ├─▶ ⑤b  Answer + citation
     │      ├─▶ ⑤c  Common questions
     │      └─▶ ⑤d  Ask my officer (escalation)
     │
     ├─▶ ⑥  जांच  ·  SCAN                  (§12)
     │      ├─▶ ⑥a  Capture guidance
     │      ├─▶ ⑥b  Result vs forecast comparison
     │      └─▶ ⑥c  Report as outbreak (→ ⑧)
     │
     ├─▶ ⑦  मेरा रिकॉर्ड  ·  MY RECORD     (§15)
     │      ├─▶ ⑦a  Log a spray / irrigation / observation
     │      ├─▶ ⑦b  Season timeline
     │      └─▶ ⑦c  Season summary + PDF
     │
     ├─▶ ⑧  आस-पास  ·  NEARBY             (§16)
     │      ├─▶ ⑧a  Nearby verified reports
     │      ├─▶ ⑧b  Report an outbreak
     │      └─▶ ⑧c  Village activity summary
     │
     ├─▶ ⑨  सीखें  ·  LEARN
     │      ├─▶ ⑨a  Disease library — symptoms, life cycle, prevention
     │      ├─▶ ⑨b  How to read a warning
     │      ├─▶ ⑨c  How to spray properly
     │      └─▶ ⑨d  What PRAHARI cannot do (§18.4)
     │
     ├─▶ ⑩  सूचनाएं  ·  ALERTS
     │      └─▶ ⑩a  Full advisory history with delivery status
     │
     └─▶ ⑪  सेटिंग्स  ·  SETTINGS
            ├─▶ ⑪a  Language & voice
            ├─▶ ⑪b  My fields (list, add, edit, delete)
            ├─▶ ⑪c  Alert channels & quiet hours
            ├─▶ ⑪d  Data & privacy — export, delete, consent
            ├─▶ ⑪e  Offline data — download district pack
            └─▶ ⑪f  About, accuracy, limitations
```

**Bottom navigation (5 items, the maximum that stays tappable):**

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│   🏠         🗺️         💊         🎤         ☰       │
│  आज        नक्शा     छिड़काव      पूछें      और      │
│ TODAY      MAP       SPRAY       ASK       MORE      │
└───────────────────────────────────────────────────────┘
```

Everything else lives under **MORE**. Scan, Record, Nearby, Learn, Alerts, Settings.

## 19.3 Officer console — navigation map

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  SIDEBAR                    │  MAIN                             │
  ├─────────────────────────────┼───────────────────────────────────┤
  │  ▸ Weekly triage      (§17) │  Ranked village table / map       │
  │  ▸ Risk map                 │  District grid, all horizons      │
  │  ▸ Spread simulation  (§10) │  7-day animated playback          │
  │  ▸ Verification queue (§16) │  Pending farmer reports           │
  │  ▸ Advisories               │  Compose · draft · approve · send  │
  │  ▸ Farmers & fields         │  Roster · assisted mapping (§7.2C) │
  │  ▸ Model trace        (§17.3)│ Full calculation for any cell     │
  │  ▸ Accuracy           (§18) │  Live validation metrics          │
  │  ▸ Bulletin                 │  Weekly PDF generator             │
  │  ▸ Feedback                 │  "Forecast was wrong here" queue  │
  └─────────────────────────────┴───────────────────────────────────┘
```

## 19.4 Public trust site

```
  /                    Landing — what PRAHARI is, in one screen
  /accuracy            §18.1 — live contingency table
  /ledger              §18.2 — the alert ledger + browser verifier
  /methodology         §18.3 — how it works, honestly
  /limitations         §18.4 — 🔴 what it cannot do
  /models              Model registry — versions, parameters, citations
  /data                Downloadable validation datasets
  /api                 Public read-only artefact endpoints (§29.7)
```

## 19.5 🔴 Why this is not a one-screen app — and how it stays simple anyway

Eleven farmer screens is a real application, and that is deliberate: a farmer needs to see a forecast, understand why, plan a spray, ask a question, keep a record, and check their neighbourhood. Collapsing that into one card serves the demo, not the user.

But size and complexity are different problems. Three rules keep an eleven-screen app usable by Sunita:

| Rule | Effect |
|---|---|
| **The first screen answers everything urgent** | TODAY (①) contains the complete answer to "what do I do today". The other ten screens are for depth, not for the daily task. A farmer who only ever opens ① is fully served. |
| **Five items in the navigation bar, everything else under MORE** | Depth exists but does not compete for attention. Discovery is progressive. |
| **Every screen has exactly one primary action** | Not a menu of options. One large, obvious next step, with the rest secondary. |

💡 **The distinction that matters: depth on demand, not depth up front.** The app is large because farming is complicated. The *first screen* is small because a farmer standing in a field at 6 a.m. needs one instruction, not eleven features.

---

# 20. 🔴 ONBOARDING & FIELD MAPPING — THE FLAGSHIP FLOW

> **This is the most important flow in the product.** Everything in §8–§18 depends on a field polygon existing. If a farmer abandons here, nothing else in this document ever runs for them.

## 20.1 Design constraints

| Constraint | Consequence |
|---|---|
| The user may not read | Every step has a voice prompt. Nothing depends on reading. |
| The user has never mapped anything | No jargon: no "polygon", no "boundary", no "GPS". |
| The user's patience is ~90 seconds | Maximum 8 steps, each obviously progressing. |
| The user may fail | 🔴 Every step has a fallback. **Never a dead end.** |
| The user may be on 2G | Imagery tiles for one village pre-cached aggressively. |
| The user may be helped by someone else | The whole flow works in assisted mode (§7.2 Method C). |

## 20.2 The flow, screen by screen

### Screen 01 — Language

```
┌─────────────────────────────────────┐
│                                     │
│         🌾  PRAHARI                 │
│                                     │
│   अपनी भाषा चुनें                    │
│   Choose your language              │
│                                     │
│   ┌─────────────┐ ┌─────────────┐  │
│   │   हिंदी      │ │   English   │  │
│   └─────────────┘ └─────────────┘  │
│   ┌─────────────┐ ┌─────────────┐  │
│   │   मराठी      │ │   বাংলা      │  │
│   └─────────────┘ └─────────────┘  │
│                                     │
│   🔊 Each button speaks its own      │
│      name when tapped               │
└─────────────────────────────────────┘
```

🔴 **Language is the very first question, before anything else.** Asking anything else first means asking it in a language the user may not read.

### Screen 02 — Voice welcome

```
🔊 "नमस्ते। मैं प्रहरी हूँ। मैं आपको बताऊंगा कि आपकी फसल में
    बीमारी कब आ सकती है — उससे पहले। शुरू करने के लिए मुझे
    आपका खेत ढूंढ़ना होगा।"

   ("Hello. I am Prahari. I will tell you when disease may come
     to your crop — before it does. To begin, I need to find
     your field.")

              [ ▶  ठीक है, चलें ]
```

⚠️ **No account. No phone number. No OTP. Not yet.** Asking for identity before delivering any value is where onboarding funnels die. Phone number is requested at Screen 07, *after* the farmer has seen their field on the map — at which point they understand what they are signing up for.

### Screen 03 — Location permission, with the reason first

```
🔊 "मुझे आपके फ़ोन की जगह देखनी होगी, ताकि मैं आपका गाँव
    दिखा सकूँ। आपका खेत कहाँ है, यह किसी को नहीं बताया जाएगा।"

   ("I need to see your phone's location so I can show your
     village. Where your field is will not be told to anyone.")

    [ ठीक है ]        [ नहीं, गाँव का नाम लिखूंगा ]
                       ("No, I'll type my village name")
```

🔴 **The reason precedes the request, and the privacy promise is in the same breath.** A bare system permission dialog with no explanation is denied by most users, and denial here is a hard stop unless the manual fallback exists.

### Screen 04 — 🔴 FIELD MAPPING — the critical screen

```
┌───────────────────────────────────────────────────────────┐
│  ◀   अपना खेत ढूंढें                          🔊 सुनें     │
├───────────────────────────────────────────────────────────┤
│                                                           │
│    ░░░▓▓▓░░░  SATELLITE IMAGERY  ░░░▓▓▓▓░░░░              │
│   ░░▓▓███▓▓░░░░  (real aerial photo)  ░░▓▓██▓░░           │
│   ░▓▓█████▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓███▓░            │
│   ░▓███████▓▓░░  ═══════════════  ░░░▓█████▓░            │
│   ░▓▓█████▓▓░░  ← नहर (canal) ──  ░░░▓████▓░░            │
│   ░░▓▓███▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓██▓░░             │
│   ░░░▓▓▓░░░░   ▪ स्कूल      🕌 मंदिर   ░░▓▓░░░            │
│   ░░░░░░░░░  ═══ मुख्य सड़क ═══════════  ░░░░            │
│                                                           │
│                    ⊙  ← आप यहाँ हैं                       │
│                       (you are here, ±8 m)                │
│                                                           │
│              📍  रामपुर                                    │
│                                                           │
├───────────────────────────────────────────────────────────┤
│  🔊 "यह आपका गाँव है। अपने खेत पर ऊँगली रखें।"            │
│     ("This is your village. Touch your field.")           │
│                                                           │
│  [ 🚶 खेत के चारों ओर चलूंगा ]   [ ❓ मदद चाहिए ]         │
│    (walk the boundary)            (need help)             │
└───────────────────────────────────────────────────────────┘
```

**The five things on this screen that make it work:**

| Element | Why it is essential |
|---|---|
| 🔴 **Real satellite imagery** | The farmer recognises their own land. This is the entire solution to the identification problem (§2.3, Barrier 2). A vector map shows nothing they know. |
| 🔴 **Landmark overlay** | Canal, road, school, temple, pond — from OpenStreetMap. These are how a farmer actually navigates: *"my field is past the school, before the canal."* |
| 🔴 **"You are here" marker with accuracy ring** | Direct answer to *"the farmer can't even see himself."* The farmer's own position, on the photograph, with honest uncertainty shown. |
| **Village name label** | Confirms the map is centred on the right place before any tapping. |
| **Two escape hatches** | Walk-the-boundary and ask-for-help. Neither method A failing nor confusion is a dead end. |

### Screen 05 — Boundary confirmation after the ML snap

```
┌───────────────────────────────────────────────────────────┐
│  ◀   क्या यह आपका खेत है?                     🔊 सुनें     │
├───────────────────────────────────────────────────────────┤
│                                                           │
│   ░░░▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░            │
│   ░░▓▓▓╔═══════════════════════╗▓▓░░░░░░░░░░░            │
│   ░▓▓▓▓║ ◆                   ◆ ║▓▓▓░░░░░░░░░░            │
│   ░▓▓▓▓║      YOUR FIELD       ║▓▓▓░░  ═════ नहर          │
│   ░▓▓▓▓║   (bright outline,    ║▓▓▓░░░░░░░░░░            │
│   ░░▓▓▓║    draggable ◆ dots)  ║▓▓░░░░░░░░░░░            │
│   ░░░▓▓║ ◆                   ◆ ║░░░░░░░░░░░░░            │
│   ░░░░░╚═══════════════════════╝░░░░░░░░░░░░░            │
│                                                           │
│              क्षेत्र:  १.२ हेक्टेयर  ≈  ४.७ बीघा           │
│                                                           │
├───────────────────────────────────────────────────────────┤
│  🔊 "क्या यह सही है? कोना खींचकर बदल सकते हैं।"           │
│     ("Is this right? You can drag a corner to change it.")│
│                                                           │
│   [ ✓ हाँ, सही है ]  [ ✎ बदलें ]  [ ✗ दोबारा ]           │
└───────────────────────────────────────────────────────────┘
```

🔴 **Area shown in hectares AND the local unit (§7.6).** "1.2 hectares" means little to a farmer who thinks in bigha. Showing both is a one-line change that transforms whether the confirmation is meaningful — and it lets the farmer catch a wrong boundary instantly, because they know their own field is about 4½ bigha.

### Screen 06 — Crop and sowing date

```
🔊 "इस खेत में क्या बोया है?"     ("What is planted in this field?")

  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
  │  🥔     │ │  🌾     │ │  🍅     │ │  🌱     │
  │  आलू    │ │  गेहूँ   │ │ टमाटर   │ │  अन्य   │
  └─────────┘ └─────────┘ └─────────┘ └─────────┘

  Large picture buttons — 🔴 no reading required.

🔊 "कब बोया था?"                  ("When did you sow it?")

  [ इस हफ्ते ]  [ पिछले महीने ]  [ २ महीने पहले ]  [ तारीख चुनें ]
   this week      last month      2 months ago      pick a date

  💡 Relative options first. A farmer remembers "about a month
     ago" far more reliably than a calendar date. If satellite
     phenology (§26.4) is available, it PRE-FILLS this — and the
     farmer only confirms.
```

### Screen 07 — Name the field

```
🔊 "इस खेत को क्या नाम दें? जैसे 'नहर वाला खेत'।"
   ("What name for this field? Like 'the canal field'.")

  ┌─────────────────────────────────┐
  │  नहर वाला खेत                    │  ← text or 🎤 voice
  └─────────────────────────────────┘

  Suggestions generated from the landmark overlay:
  [ नहर वाला खेत ]  [ स्कूल के पीछे ]  [ बड़ा खेत ]
   canal field       behind the school    big field
```

🔴 **Farmer-chosen names in the farmer's own words.** "Field 1" and "Plot A" are useless to someone with three parcels. "नहर वाला खेत" is instantly unambiguous — and it is what the voice advisory will say first (§14.5), which is what makes the advisory locatable.

💡 **The landmark-derived suggestions are the small detail that makes this feel intelligent.** We already fetched the canal and the school to render the map; using them to propose names costs nothing and produces exactly the phrase the farmer would have chosen.

### Screen 08 — Alerts, then done

```
🔊 "मैं आपको कैसे बताऊं?"          ("How should I tell you?")

  ☑ इस ऐप में                        (in this app)
  ☑ फ़ोन कॉल से                       (by phone call — IVR)
  ☐ WhatsApp पर
  ☐ SMS से

  फ़ोन नंबर:  [ __________ ]   ← 🔴 asked ONLY now, after value shown

  शांत समय:  रात ९ बजे से सुबह ६ बजे तक
             (quiet hours — no calls at night)

  [ ✓ हो गया ]

  → lands on TODAY (①) with the field card already populated
    → 🔊 first advisory plays automatically
```

## 20.3 Failure paths — every one has an exit

| Failure | Recovery |
|---|---|
| GPS denied | Village name search → satellite view of that village |
| GPS inaccurate (> 50 m) | Show accuracy honestly; ask the farmer to confirm the village |
| ML snap returns nothing | Fall back to plain manual drawing at the tap point |
| ML snap returns a wrong shape | Drag vertices; or "दोबारा" to retry; or switch to manual |
| Farmer taps a road/pond | "यह सड़क लगती है — खेत के अंदर छुएं" and retry |
| Imagery will not load (no data) | Cached tiles if present; otherwise offer walk-the-boundary, which needs no data |
| Farmer gives up | 🔴 "मदद चाहिए" → generates a request the local officer/VLE sees in the console (§7.2 C) |
| Field outside covered districts | Explain coverage honestly, offer notify-me, keep the mapped boundary for later |

🔴 **The last row matters more than it looks.** An out-of-coverage farmer who is turned away is lost permanently. One who is told "we do not cover your district yet, but we saved your field and will call you when we do" is a future user *and* a data point in coverage prioritisation.

## 20.4 Adding more fields later

Sunita has three parcels. She will not map all three on day one — she will map one, see whether the product is any good, then map the others.

```
TODAY screen, below the field cards:

  ┌─────────────────────────────────────────┐
  │  ➕  दूसरा खेत जोड़ें                     │
  │      Add another field                  │
  │                                         │
  │  आपके पास और खेत हैं?                    │
  │  ("Do you have more fields?")           │
  └─────────────────────────────────────────┘
       → re-enters §20.2 from Screen 04
```

💡 **Designing for incremental mapping is a retention decision, not a convenience.** Demanding all fields up front raises the cost of trying the product; allowing one field lowers it to almost nothing, and the second field gets mapped after the first advisory proves useful.

## 20.5 Acceptance criteria

- [ ] `[HUMAN]` A farmer with no app experience completes Screens 01–08 in under 90 seconds
- [ ] Every screen's voice prompt plays automatically and can be replayed
- [ ] No screen requires reading to complete
- [ ] No phone number is requested before Screen 08
- [ ] Every failure path in §20.3 is reachable and exits somewhere useful
- [ ] Adding a second field takes fewer than 60 seconds
- [ ] The whole flow completes in assisted mode from the officer console
- [ ] Field name accepts Devanagari and voice dictation

---

# 21. UX SPECIFICATION — KEY SCREENS

## 21.1 ① TODAY — the home screen

```
┌───────────────────────────────────────────────────────┐
│  प्रहरी                              🔔      हिंदी ▾   │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │  🔴  नहर वाला खेत                    आलू        │ │
│  │                                                 │ │
│  │      झुलसा का खतरा                              │ │
│  │      Blight risk                                │ │
│  │                                                 │ │
│  │      💊 मंगलवार सुबह ६–९ बजे छिड़कें             │ │
│  │                                                 │ │
│  │      ┌──────────────────────────────────────┐   │ │
│  │      │  🔊  सुनें  ·  २० सेकंड              │   │ │
│  │      └──────────────────────────────────────┘   │ │
│  │                                                 │ │
│  │      क्यों? →                     भरोसा: उच्च   │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │  🟢  स्कूल के पीछे                    आलू       │ │
│  │      कोई खतरा नहीं · अगले ७ दिन                 │ │
│  │      🔊 सुनें                          क्यों? → │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │  ➕  दूसरा खेत जोड़ें                            │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ─────────────────────────────────────────────────── │
│  ℹ️  ३.२ किमी दूर झुलसा की पुष्टि · हवा उस तरफ से ↖   │
│  ─────────────────────────────────────────────────── │
│  डेटा: आज सुबह २:१४ बजे                              │
├───────────────────────────────────────────────────────┤
│   🏠 आज    🗺️ नक्शा   💊 छिड़काव   🎤 पूछें   ☰ और    │
└───────────────────────────────────────────────────────┘
```

**Rules:**
- 🔴 Fields sorted by risk, worst first. Sunita sees the problem before she sees anything else.
- 🔴 Every card resolves to an action, including "no risk" (P2).
- The play button is the largest interactive element on the card.
- Data age always visible (P5). Stale data is stated, never hidden.
- One card per field. Three parcels = three cards. No aggregation, no "average risk" — a meaningless number.

## 21.2 ③ MY MAP — 🔴 satellite, and my fields on it

```
┌───────────────────────────────────────────────────────┐
│  ◀  मेरे खेत                    [उपग्रह] [सादा]  ⊙   │
├───────────────────────────────────────────────────────┤
│  ░░▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░         │
│  ░▓▓▓╔═══════════╗▓░░░░░░░░░░░░░░░░░░░░░░░░░         │
│  ░▓▓▓║ 🔴        ║▓▓░░  ═══════════ नहर ═══════       │
│  ░▓▓▓║ नहर वाला  ║▓▓▓░░░░░░░░░░░░░░░░░░░░░░         │
│  ░░▓▓╚═══════════╝▓░░░░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░  ⊙ आप  ░░░░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░░░░░░░░░░░░░▪ स्कूल ░░░░░░░░░░░░         │
│  ░░░░░░░░░░╔════════╗░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░░║ 🟢     ║░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░░║स्कूल के║░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░░║ पीछे   ║░░░░░░░░░░░░░░░░░░░░░         │
│  ░░░░░░░░░░╚════════╝░░░░░░░░░░░░░░░░░░░░░         │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ○ मेरे खेत   ○ आस-पास का खतरा   ○ फैलाव        │ │
│  │   my fields    nearby risk        spread        │ │
│  └─────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

**🔴 The non-negotiable rules for this screen — this is where P1 is enforced:**

| Rule | Reason |
|---|---|
| **Satellite imagery is the default basemap** | Recognisability. This is the whole point. |
| **The farmer's own fields are the only labelled polygons** | Their land, named in their words. |
| **"You are here" is always available (⊙ button)** | Direct fix for the original critique. |
| **Landmarks always rendered** | Orientation. |
| 🔴 **NO grid. NO cell boundaries. NO district choropleth. Ever.** | The grid is an implementation detail (§8.2). Rendering it re-creates the exact problem this design exists to solve. |
| **"Nearby risk" renders as soft blurred gradients** | Honest about uncertainty; visually distinct from the crisp field outlines, so a farmer never confuses a modelled surface with their own boundary. |
| **Other farmers' field boundaries are never shown** | Privacy (§16.2). |

## 21.3 Risk vocabulary — three bands, not five

| Band | Colour | Hindi | English | Meaning | Action |
|---|---|---|---|---|---|
| 🟢 | Green | **सुरक्षित** | Safe | No action needed | "Nothing to do. Keep watching." |
| 🟠 | Amber | **ध्यान दें** | Watch | Conditions building | "Get medicine ready. Check your field." |
| 🔴 | Red | **छिड़काव करें** | Act | Criterion met | "Spray in the window shown." |

🔴 **Three bands, chosen deliberately.** Five bands invite the question "what is the difference between level 2 and level 3?", which has no good answer for a farmer and no decision attached to it. Three bands map exactly onto three actions: do nothing / prepare / act. **A band with no distinct action attached should not exist.**

⚠️ **Colour is never the only signal.** Every band carries an icon and a text label — for colour-blind users and for direct sunlight where colour discrimination degrades (§24).

## 21.4 ②b WHY — three-depth progressive disclosure

One screen must satisfy a farmer, an officer, and a scientist without patronising any of them.

```
DEPTH 1 — DEFAULT (farmer)
┌─────────────────────────────────────────────────┐
│  क्यों?                                          │
│                                                 │
│  🌡️  पिछली दो रातें बहुत नमी रही                │
│      (the last two nights were very humid)      │
│                                                 │
│  💧  आठ घंटे तक पत्ते गीले रहे                   │
│      (leaves stayed wet for eight hours)        │
│                                                 │
│  🦠  यही मौसम झुलसा फैलाता है                    │
│      (this weather spreads blight)              │
│                                                 │
│              [ और जानें ▾ ]                     │
└─────────────────────────────────────────────────┘

DEPTH 2 — EXPANDED (officer / curious farmer)
┌─────────────────────────────────────────────────┐
│  १३ जनवरी   न्यू. तापमान ११.८°C ≥ १०°C  ✓      │
│             नमी ≥९०%    ७ घंटे  ≥ ६ घं.  ✓     │
│  १४ जनवरी   न्यू. तापमान १२.४°C ≥ १०°C  ✓      │
│             नमी ≥९०%    ८ घंटे  ≥ ६ घं.  ✓     │
│                                                 │
│  लगातार २ दिन → मापदंड पूरा                     │
│  DSV आज: ३ · ७ दिन का संचय: १९ (सीमा १८)       │
│                                                 │
│  भरोसा ०.८२ · मॉडल Hutton v2.0.0                │
│              [ वैज्ञानिक विवरण ▾ ]              │
└─────────────────────────────────────────────────┘

DEPTH 3 — SCIENTIFIC (Priya)
  Full node lattice values · interpolation weights ·
  lapse correction applied · mean-temp-during-spell ·
  spell boundaries · DSV table row used ·
  ML correction delta · spatial contribution ·
  model citation · engine SHA · data fetch timestamp ·
  [ Download calculation JSON ]
```

💡 **Depth 1 does not contain a single number, and Depth 3 contains nothing but numbers.** The same underlying facts, rendered for three completely different readers. A farmer is never shown a threshold; a scientist is never shown an emoji. This is what makes one product serve §3.1 and §3.3 simultaneously.

## 21.5 The five states every data surface must define

Most products define one. Defining all five is the difference between a demo and a product.

| State | Requirement |
|---|---|
| **Loading** | Skeleton matching the final layout — never a spinner over a blank screen |
| **Empty** | Explains why it is empty and what to do: "No fields yet. Add your first field." |
| **Error** | Plain-language cause + a retry action + an offline fallback |
| **🔴 Stale** | Data age stated prominently. **Never silently show old data as current (P5).** |
| **Success** | The normal case |

🔴 **The stale state is the one that matters most.** A cached forecast displayed as if fresh is the failure mode that causes a farmer to spray on three-day-old information. Every surface showing model output must render its data age.

---

# 22. VISUAL DESIGN SYSTEM

## 22.1 Two purposeful themes

| Theme | Default on | Why |
|---|---|---|
| **Field Mode** (light, very high contrast) | Mobile / farmer app | 🔴 Sunita stands in direct sunlight. Dark themes are unreadable outdoors on a mid-range LCD. |
| **Analyst Mode** (dark, dense) | Desktop / officer console | Long indoor sessions, dense data, better for extended screen time. |

🔴 **Risk colours are identical in both themes.** A band must never look different depending on theme or device — that would make the product's central vocabulary unstable.

## 22.2 Design tokens

```css
:root {
  /* ── RISK — 🔴 IDENTICAL ACROSS THEMES, NEVER OVERRIDDEN ── */
  --risk-safe:   #16A34A;
  --risk-watch:  #F59E0B;
  --risk-act:    #DC2626;

  /* 🔴 Text ON risk colours — contrast-checked, not eyeballed */
  --on-risk-safe:  #FFFFFF;   /* 4.6:1  AA  */
  --on-risk-watch: #0F172A;   /* 7.4:1  AAA — 🔴 DARK text on amber */
  --on-risk-act:   #FFFFFF;   /* 5.9:1  AA  */

  /* ── FIELD MODE (light) ── */
  --bg:            #FFFFFF;
  --surface:       #F8FAFC;
  --surface-raised:#FFFFFF;
  --text:          #0F172A;
  --text-muted:    #475569;
  --border:        #CBD5E1;
  --border-strong: #2D3B58;
  --brand:         #15803D;

  /* ── TYPE — large, because outdoors and older eyes ── */
  --font-sans: 'Noto Sans', 'Noto Sans Devanagari', system-ui, sans-serif;
  --text-xs: 0.875rem;  /* 14px — 🔴 the SMALLEST size allowed anywhere */
  --text-sm: 1rem;      /* 16px */
  --text-base: 1.125rem;/* 18px — body default */
  --text-lg: 1.375rem;  /* 22px */
  --text-xl: 1.75rem;   /* 28px */
  --text-2xl: 2.25rem;  /* 36px — band labels */

  /* ── SPACE — 4px base ── */
  --s-1: 0.25rem; --s-2: 0.5rem;  --s-3: 0.75rem;
  --s-4: 1rem;    --s-6: 1.5rem;  --s-8: 2rem;  --s-12: 3rem;

  /* ── TOUCH — 🔴 minimum 56px, not 44px ── */
  --touch-min: 3.5rem;      /* 56px — farmers, gloves, sunlight, motion */
  --touch-primary: 4.5rem;  /* 72px — play button, primary actions */

  --radius: 0.75rem;
  --radius-lg: 1rem;
}

[data-theme="analyst"] {
  --bg:            #0B1220;
  --surface:       #111A2E;
  --surface-raised:#18233D;
  --text:          #E8EDF7;
  --text-muted:    #94A3B8;
  --border:        #263352;
  --border-strong: #3E4E76;
  --brand:         #22C55E;
  /* risk tokens deliberately NOT redefined */
}
```

🔴 **`--on-risk-watch: #0F172A` — dark text on amber, never white.** White on amber measures roughly 2.1:1 and fails accessibility badly. This is the single most common contrast error in risk-colour interfaces, and it appears specifically on the band a farmer most needs to read while preparing.

🔴 **`--touch-min: 56px`, not the conventional 44px.** The user may be wearing gloves, standing in a field, in bright sunlight, possibly moving. Standard touch targets are calibrated for an office chair.

## 22.3 Band mapping — one source of truth

```typescript
// src/lib/bandToSemantic.ts
// 🔴 The ONLY place a band maps to a colour, icon, or label.
// Anything hardcoding "#DC2626" or "red" elsewhere is a bug.

export type Band = 'safe' | 'watch' | 'act';

export const BAND = {
  safe:  { color: 'var(--risk-safe)',  on: 'var(--on-risk-safe)',
           icon: 'shield-check', hi: 'सुरक्षित',    en: 'Safe',
           action_hi: 'कुछ नहीं करना है' },
  watch: { color: 'var(--risk-watch)', on: 'var(--on-risk-watch)',
           icon: 'alert-triangle', hi: 'ध्यान दें', en: 'Watch',
           action_hi: 'दवा तैयार रखें' },
  act:   { color: 'var(--risk-act)',   on: 'var(--on-risk-act)',
           icon: 'alert-octagon', hi: 'छिड़काव करें', en: 'Act',
           action_hi: 'बताए समय पर छिड़काव करें' },
} as const;
```

💡 **Why this file is load-bearing:** a band appears on cards, maps, timelines, notifications, PDFs, and the officer console. Any one of those hardcoding a colour creates a drift where the same risk looks different in two places — which quietly destroys the reliability of the product's core vocabulary. One file, imported everywhere, makes drift impossible.

---

# 23. VOICE & LANGUAGE UX

## 23.1 The audio-first design method

1. **Write the spoken script first**, in the target language, out loud.
2. Time it. **Over 30 seconds means rewrite, not trim.**
3. Read it to someone unfamiliar with the product. If they cannot repeat the action back, rewrite.
4. *Then* design the screen as a visual mirror of the audio.

⚠️ **Reading the screen aloud produces bad audio.** Text is scannable and can be re-read; audio is linear and cannot. Different medium, different writing.

## 23.2 Copy rules

| Rule | ❌ Don't | ✅ Do |
|---|---|---|
| Field name first | "Blight risk is high in..." | "आपके नहर वाले खेत में..." |
| Specific times | "spray soon" | "मंगलवार सुबह छह से नौ बजे" |
| Everyday words | "आपेक्षिक आर्द्रता" (relative humidity) | "नमी" (moisture) |
| Short sentences | one 30-word sentence | four 8-word sentences |
| No jargon | "DSV 19 exceeds threshold" | "पिछली दो रातें नमी बहुत रही" |
| No product names | "छिड़कें मैंकोज़ेब" | "छिड़काव करें" + "अधिकारी से दवा पूछें" |
| Honest uncertainty | "definitely will get blight" | "खतरा है" (there is a risk) |

## 23.3 Voice interaction

| Interaction | Design |
|---|---|
| **Play advisory** | Largest button on the card. Duration shown. Resumes if interrupted. |
| **Replay** | Always available. Farmers replay often; never hide it. |
| **Voice question** | Hold to speak, release to send. Waveform feedback while recording. |
| **Voice field naming** | Dictate, see the transcription, confirm or retry. |
| **Read-aloud everything** | Any text block has a 🔊 control. No exceptions. |

---

# 24. ACCESSIBILITY

## 24.1 Why this is a functional requirement, not compliance

The primary user has limited literacy, is often over 40 with age-related presbyopia, uses the phone in direct sunlight, and may have hands that are wet, muddy, or gloved. Accessibility here is not an edge case being accommodated — **it is the median case being designed for.**

## 24.2 Requirements

| Requirement | Specification |
|---|---|
| **Contrast** | WCAG AA minimum; AAA for all risk bands and primary actions |
| 🔴 **Never colour alone** | Every band = colour + icon + text label |
| **Touch targets** | ≥ 56 px, ≥ 72 px for primary actions |
| **Text size** | 18 px body minimum; scales with OS font size up to 200% without layout breaking |
| **Screen reader** | Full ARIA labelling; tested with TalkBack in Hindi |
| **Keyboard** | Full navigation in the officer console |
| **Motion** | `prefers-reduced-motion` respected; no essential information conveyed only by animation |
| **Language** | `lang` attribute set correctly for every text node so screen readers pronounce Devanagari properly |
| **Icons** | Never icon-only for a critical action — always paired with a text label |
| **Errors** | Text + icon + colour; never colour alone |
| **Sunlight** | 🔴 Field Mode tested on a mid-range LCD in direct sun `[HUMAN]` |

## 24.3 Testing checklist

- [ ] Every risk band distinguishable in greyscale
- [ ] Every interactive element ≥ 56 px
- [ ] Full flow completed with TalkBack in Hindi `[HUMAN]`
- [ ] 200% OS font size breaks no layout
- [ ] Full flow completed one-handed with a thumb only
- [ ] Field Mode readable outdoors at noon `[HUMAN]`
- [ ] Full onboarding completed with the screen never read `[HUMAN]`
- [ ] Simulated deuteranopia / protanopia review of all band surfaces

---

# ═══════════════════════════════════════
# PART IV — TECHNOLOGY
# ═══════════════════════════════════════

# 25. SYSTEM ARCHITECTURE

## 25.1 The whole system on one page

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FREE PUBLIC DATA SOURCES                                               │
│  Open-Meteo (weather) · Sentinel-2/1 (satellite) · OpenStreetMap        │
│  (landmarks) · SRTM (elevation) · Agmarknet (prices) · IMD              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ⏰ NIGHTLY PIPELINE  —  GitHub Actions cron  "30 20 * * *" = 02:00 IST │
│                                                                         │
│   ① fetch weather (1–2 API calls)   ② interpolate to 1 km grid          │
│   ③ run disease + pest models       ④ ML residual correction            │
│   ⑤ spatial spread simulation       ⑥ aggregate cells → FIELDS          │
│   ⑦ spray window solving            ⑧ LLM verbalisation + gate          │
│   ⑨ TTS pre-generation (hash-keyed) ⑩ write artefacts + ledger entry     │
│                                                                         │
│  🔴 "The server" is a scheduled job. There is no always-on backend.     │
└────────────┬───────────────────────────────────┬────────────────────────┘
             ▼                                   ▼
┌────────────────────────────┐    ┌──────────────────────────────────────┐
│  STATIC ARTEFACTS          │    │  SUPABASE (Postgres + PostGIS)       │
│  (committed to repo / CDN) │    │  fields · subscribers · reports ·    │
│                            │    │  spray logs · ledger · pgvector      │
│  risk/{district}/{day}.json│    │  🔴 Row-Level Security enforced      │
│  audio/{hash}.mp3          │    └──────────────────────────────────────┘
│  tiles/ · ledger.jsonl     │                    │
└────────────┬───────────────┘                    │
             ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  CLIENTS                                                                │
│  Farmer PWA (React+Vite, offline-first) · Officer console ·             │
│  Public trust site · WhatsApp / SMS / IVR out-channels                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 25.2 🔴 The four architectural decisions that make ₹0 possible

| # | Decision | What it replaces | Saving |
|---|---|---|---|
| **1** | **Scheduled job, not a server** | An always-on API backend | The single largest cost line, eliminated |
| **2** | **Static artefacts, not query-time compute** | Per-request database reads and model runs | Reads become CDN hits; compute is O(districts), not O(users) |
| **3** | **Node lattice, not per-cell fetch** (§8.3) | ~3,600 weather calls/district/night | 99.9% fewer API calls — stays inside free tiers |
| **4** | **Pre-generated audio, hash-keyed** (§14.2) | Per-farmer TTS at request time | Cost scales with *distinct messages* (~40/night), not users |

💡 **These four compound.** Together they mean 50,000 farmers cost approximately the same to serve as 50 — which is what makes "free forever" an architectural property rather than a subsidy that runs out.

## 25.3 🔴 The purity boundary — the highest-leverage code decision

```
engine/     PURE. Numbers in, numbers out.
            ❌ no network  ❌ no filesystem  ❌ no clock
            ❌ no randomness  ❌ no environment variables
            ✅ testable in milliseconds, offline, deterministically

adapters/   ALL I/O. Weather, satellite, LLM, TTS, database.
            One module per external system, behind an interface.

pipeline/   Orchestration. Calls adapters, feeds engine, writes artefacts.
```

Enforced by a test that walks the AST of every `engine/` module:

```python
# tests/test_purity.py — 🔴 fails the build on violation
FORBIDDEN = {"requests", "httpx", "urllib", "open", "random",
             "subprocess", "socket", "boto3", "supabase"}
FORBIDDEN_CALLS = {"datetime.now", "time.time", "os.environ", "os.getenv"}

def test_engine_is_pure():
    for path in Path("engine").rglob("*.py"):
        tree = ast.parse(path.read_text())
        # assert no forbidden import or call appears anywhere in the tree
```

💡 **Why this is worth a whole test file:** the scientific core becomes testable without a network, reproducible forever, and reviewable by a scientist who does not read infrastructure code. It also means the four silent-bug tests (§8.6) run in milliseconds, so nobody is tempted to skip them.

## 25.4 Repository layout

```
prahari/
├── engine/              # 🔴 PURE — the science
│   ├── interpolate.py   # bilinear + lapse + Magnus RH
│   ├── rules.py         # Hutton / Smith / consecutive-day logic
│   ├── wallin.py        # DSV table lookup
│   ├── degree_day.py    # pest GDD accumulation
│   ├── spread.py        # anisotropic dispersal kernel
│   ├── spray.py         # window gates and scoring
│   ├── indices.py       # NDVI / NDRE / NDWI / EVI
│   ├── aggregate.py     # cells → fields, worst-case weighting
│   └── confidence.py    # inter-node disagreement
├── adapters/            # ALL I/O
│   ├── weather.py  satellite.py  osm.py  elevation.py
│   ├── llm/{base,gemini,local_gemma,template}.py
│   ├── tts/{base,bhashini,edge}.py
│   └── db.py
├── pipeline/
│   ├── nightly.py       # the orchestrator
│   ├── validate.py      # LLM output gate (§27.5)
│   ├── ledger.py        # hash chain
│   └── config/{models,districts,area_units,copy}.yaml
├── ml/                  # training, notebooks, export
│   ├── segmentation/ crop_type/ phenology/ residual/ vision/ speech/
│   └── export_onnx.py
├── web/                 # farmer PWA (React + Vite + TS)
├── console/             # officer console
├── site/                # public trust site
├── artefacts/           # generated JSON/GeoJSON/audio — committed
├── tests/               # 🔴 test_purity, test_rules, test_gate...
└── .github/workflows/nightly.yml
```

---

# 26. 🔴 THE NINE MACHINE-LEARNING MODELS

> The PPT promised ML. This is what that means concretely: nine models, each with a defined job, free training compute, and an honest fallback when it fails.

## 26.1 Overview

| # | Model | Job | Base | Training | Runs |
|---|---|---|---|---|---|
| 1 | **Field segmentation** | Propose a field boundary from a tap | SAM-derived / U-Net | Kaggle GPU | On-device + server |
| 2 | **Crop-type classifier** | What crop is growing here | 1D-CNN / LightGBM on S2 time series | Kaggle GPU | Server |
| 3 | **Phenology detector** | Sowing date + growth stage | Curve fitting + GBM | Kaggle GPU | Server |
| 4 | **Risk residual corrector** | Correct physics bias vs observation | Gradient boosting | Kaggle GPU | Server |
| 5 | **Weather downscaler** | Improve 11 km → 1 km interpolation | GBM on terrain features | Kaggle GPU | Server |
| 6 | **Leaf/pest vision** | Confirm a suspected disease | MobileNetV3-Small | Kaggle GPU | 🔴 On-device |
| 7 | **Grounded LLM** | Verbalise + answer questions | Gemini free tier / Gemma LoRA | Free tier / Kaggle | Server |
| 8 | **Indic ASR** | Understand voice questions | Bhashini / Whisper-small LoRA | Kaggle GPU | Server |
| 9 | **Embedding model** | Retrieval for RAG | Multilingual sentence-transformer | Off the shelf | Server (local) |

🔴 **Every one has a deterministic fallback.** If a model is unavailable, untrained, or low-confidence, the product degrades to a rule or a template — it never fails and never guesses.

## 26.2 Model 1 — Field boundary segmentation `[P0]`

**The model that makes §20 work.** Farmer taps a point; model returns the parcel polygon containing it.

```
Input:   satellite tile (RGB+NIR if available) + tap point
Output:  polygon + confidence

Approach A (preferred): promptable segmentation (SAM-family), point-prompted,
          distilled to a small student model for on-device use
Approach B (fallback):  U-Net boundary detection → watershed → polygon
Approach C (always):    manual drawing — 🔴 never a dead end

Training: public field-boundary datasets + hand-labelled Indian parcels [HUMAN]
Target:   ≥70% of proposals need ≤3 vertex corrections
Fallback: confidence <0.5 → skip the proposal, open manual drawing silently
```

⚠️ Indian smallholder parcels are small, irregular, and often unfenced — harder than the European/US farmland these models are usually trained on. **Expect to need local labelled data.** `[HUMAN]`

## 26.3 Model 2 — Crop-type classification `[P2]`

Prevents running a potato model on a wheat field — a guaranteed false alarm.

```
Input:   Sentinel-2 NDVI/NDRE/NDWI time series over the season + Sentinel-1 VH/VV
Output:  crop class + confidence
Model:   1D-CNN over the temporal signature, or LightGBM on curve features
         (peak NDVI, days-to-peak, green-up rate, senescence rate, season length)
🔴 Used only to PRE-FILL and to flag mismatch. The farmer's answer always wins.
Copy on mismatch: "Satellite suggests wheat here. Is this field wheat?"
```

## 26.4 Model 3 — Phenology / sowing date `[P2]`

```
NDVI curve → detect green-up inflection → back-calculate sowing date
Combined with thermal time (GDD from sowing) → current growth stage
→ feeds growth-stage gating (§8.5), the cheapest false-alarm reduction available
Fallback: farmer-entered sowing date, always authoritative
```

## 26.5 🔴 Model 4 — Risk residual correction — the scientifically interesting one

**The core idea:** do not replace the published physics. **Learn where it is systematically wrong.**

```
   physics_risk  ──────────────────────────────┐
   (Hutton/Wallin — auditable, citable)        │
                                                ▼
   terrain, aspect, proximity-to-water,   ┌───────────┐
   canopy density, historical bias,  ────▶│ GBM model │──▶ correction δ
   node disagreement, season stage        └───────────┘    (bounded ±0.25)
                                                ▼
   final_risk = clamp(physics_risk + δ, 0, 1)
```

| Property | Value |
|---|---|
| Target | Residual between physics prediction and observed outbreak |
| Features | Terrain, aspect, TWI, distance to water, NDVI, node disagreement, DOY, stage |
| 🔴 Correction bound | **±0.25 maximum.** ML adjusts; it never overrides. |
| 🔴 Band-flip rule | A correction may never move safe → act on its own. Only physics can. |
| Fallback | Untrained or low-confidence → δ = 0, pure physics |
| Explainability | SHAP values shown in the officer trace (§17.3) |

💡 **Why this architecture instead of an end-to-end ML model:** with sparse ground truth, an end-to-end model overfits and cannot be defended to a scientist. Physics-first means the product works on day one with zero training data, is fully citable, and *improves* as observations accumulate — without ever becoming a black box. The physics is the floor; ML is the polish.

## 26.6 Model 5 — Weather downscaling `[P2]`

Learns the correction between interpolated 11 km values and any available point observations (IMD AWS, KVK stations), using terrain features. Bounded, with a fallback to plain bilinear + lapse (§8.3).

## 26.7 Model 7 — Fine-tuned Gemma via LoRA `[P2]`

Removes third-party dependency for advisory verbalisation.

```
Base:      Gemma 2B/4B instruct (open weights)
Method:    LoRA (r=16), 4-bit quantised training
Data:      5,000+ (structured facts → approved advisory text) pairs,
           generated from templates + LLM, 🔴 human-reviewed [HUMAN]
Compute:   Kaggle free GPU (~30 h/week) — fits comfortably
Output:    GGUF quantised, self-hosted
Purpose:   Free-tier independence + full data control
```

## 26.8 Model 8 — Indic ASR `[P2]`

Whisper-small + LoRA on Indian agricultural vocabulary — crop names, disease names, local units, dialect terms that generic ASR mangles. Fallback: Bhashini ASR, then a "type your question" input.

## 26.9 🔴 The rules that keep ML honest

| Rule | Reason |
|---|---|
| Every model has a deterministic fallback | ML unavailability must never be user-visible as failure |
| ML corrections are bounded | An unbounded correction is an unbounded liability |
| Physics alone decides safe → act band flips | Keeps the product defensible to a pathologist |
| Model version stamped on every output | Reproducibility |
| Held-out test sets are real-world, never lab | Lab accuracy is a vanity metric (§12.3) |
| Training data provenance documented | Priya (§3.3) will ask |
| No model trained on data we cannot cite | Same reason as §11.4 |

---

# 27. THE LLM SAFETY LAYER

## 27.1 Why this section exists

An LLM given agronomic authority will eventually produce a confident wrong dose, and a farmer will act on it. Every control below exists to make that structurally impossible rather than unlikely.

## 27.2 The boundary in code

```python
# pipeline/verbalise.py
def verbalise(facts: AdvisoryFacts, lang: str) -> str:
    """🔴 facts is a FROZEN dataclass. The LLM sees ONLY these fields.
    It has no tools, no retrieval beyond the corpus, no engine access."""
    raw = llm.generate(system=SYSTEM_PROMPT, user=facts.to_json(),
                       max_tokens=200, temperature=0.3)
    ok, reason = validate_output(raw.text, facts, lang)   # §27.5
    if not ok:
        log_gate_rejection(reason, facts, raw.text)
        return render_template(facts, lang)                # 🔴 always works
    return raw.text
```

## 27.3 The system prompt

```
You convert agricultural advisory FACTS into natural spoken language.

ABSOLUTE RULES
1. Use ONLY the facts given. Introduce nothing.
2. Never state a number that is not in the input.
3. Never name a pesticide, fungicide, brand, or chemical.
4. Never state a dose, quantity, or concentration.
5. Never mention a date or time not in the input.
6. Never predict an outcome ("your crop will be destroyed").
7. If a fact is missing, omit it. Do not infer it.

STYLE
· Target 45 words. Never exceed 60.
· Grade-5 reading level. Short sentences.
· Warm and direct. No hedging, no jargon, no greetings beyond one.
· 🔴 Name the field FIRST.
· Output ONLY the advisory text. No preamble, no explanation.
```

## 27.4 What the LLM cannot reach

| Blocked | How |
|---|---|
| The engine | Never called from LLM context; no tool access |
| The database | No credentials in the LLM process |
| Product catalogues | Not in the corpus at all |
| Dose tables | Not in the corpus at all |
| Its own training knowledge | Prompt rule 1 + the output gate |

🔴 **Product names and dose tables are absent from the retrieval corpus by design.** The model cannot cite what it was never given. This is stronger than any instruction.

## 27.5 🔴 The output validation gate

```python
def validate_output(text: str, facts: AdvisoryFacts, lang: str):
    # 1. Every number in the output must exist in the facts
    for n in extract_numbers(text):
        if n not in facts.allowed_numbers():
            return False, f"invented number: {n}"
    # 2. Banned vocabulary — pesticide names, chemical groups, dose units
    for term in BANNED_TERMS[lang]:
        if term in text.lower():
            return False, f"banned term: {term}"
    # 3. Length and language
    if len(text.split()) > 60:            return False, "too long"
    if not is_expected_script(text, lang):return False, "wrong script"
    # 4. Dates/times must match the facts
    if extract_times(text) - facts.allowed_times():
        return False, "invented time"
    return True, "ok"
```

**Rejection rate is a monitored metric.** A rising rate means the model, the prompt, or the fact schema has drifted — an early warning, not just a safety net.

---

# 28. THE NIGHTLY PIPELINE

## 28.1 The job

```yaml
# .github/workflows/nightly.yml
on:
  schedule:
    - cron: "30 20 * * *"     # 20:30 UTC = 02:00 IST 🔴 comment the offset
  workflow_dispatch:           # manual re-run
jobs:
  forecast:
    timeout-minutes: 45
    strategy:
      matrix: { district: [farrukhabad, ...] }   # parallel, isolated failures
```

🔴 **02:00 IST is deliberate:** after the day's weather model runs are published, and early enough that advisories are ready before farmers wake.

## 28.2 Stages and failure policy

| # | Stage | On failure |
|---|---|---|
| 1 | Fetch weather | 🔴 **FAIL LOUDLY** — retry ×3, then alert; use cached + mark stale |
| 2 | Interpolate | FAIL LOUDLY — a bug, not a transient |
| 3 | Run models | FAIL LOUDLY |
| 4 | ML correction | Degrade silently — δ = 0 |
| 5 | Satellite enrichment | Degrade silently — omit NDVI |
| 6 | Spread simulation | Degrade silently — omit spatial term |
| 7 | Aggregate to fields | FAIL LOUDLY |
| 8 | Spray windows | FAIL LOUDLY |
| 9 | LLM verbalisation | Degrade silently — template fallback |
| 10 | TTS | Degrade silently — text only + generic recorded clip |
| 11 | Write artefacts + ledger | FAIL LOUDLY |
| 12 | Dispatch alerts | Retry with idempotency keys |

🔴 **The principle: the core forecast path fails loudly; enrichment degrades silently.** A farmer must never receive a *wrong* advisory because something broke — but they should still receive a *simpler* one when an optional layer is down.

## 28.3 The degradation ladder

| Level | Condition | Behaviour |
|---|---|---|
| L0 | All systems normal | Full experience |
| L1 | Satellite unavailable | Forecast without NDVI; UI notes it |
| L2 | ML models unavailable | Pure physics; officer trace shows δ=0 |
| L3 | Spread data sparse | Environmental risk only |
| L4 | LLM unavailable | Template advisories — 🔴 indistinguishable in quality of *content* |
| L5 | TTS unavailable | Text + generic recorded band clip |
| L6 | Weather partially fetched | Interpolate from available nodes; confidence drops; shown |
| L7 | 🔴 **Weather fetch fully failed** | **Show yesterday's forecast, prominently labelled stale, with its age** |
| L8 | Database unreachable | Static artefacts still serve; writes queue locally |
| L9 | Client offline | Full cached experience; sync on reconnect |
| L10 | Alert dispatch failed | Retry with idempotency; in-app still current |
| L11 | Job did not run at all | Client detects staleness from artefact timestamp and says so |
| L12 | Catastrophic | Static page: "PRAHARI is not updating. Contact your KVK officer." |

🔴 **L7 is the thesis of this ladder.** A stale forecast shown *without saying so* is the failure that makes a farmer spray on three-day-old information. Showing it *with* its age is honest and still useful. Hiding staleness is the one unacceptable option.

---

# 29. DATA SOURCES & API CONTRACTS

## 29.1 Complete source table

| Source | Use | Key needed | Cost | Limits |
|---|---|---|---|---|
| **Open-Meteo Forecast** | Hourly weather, 16 days | ❌ None | Free | ~10k calls/day non-commercial `[VERIFY]` |
| **Open-Meteo Archive (ERA5)** | Historical for hindcasting | ❌ None | Free | Same |
| **Sentinel-2 L2A** (STAC/AWS) | NDVI, crop type, phenology | ❌ None | Free | Open data |
| **Sentinel-1 GRD** | Cloud-free SAR | ❌ None | Free | Open data |
| **Google Earth Engine** | Large-scale satellite compute | ✅ Account | Free non-commercial `[VERIFY]` | Quota-based |
| **MapTiler** | Satellite basemap tiles | ✅ Key | Free tier | ~100k tiles/mo `[VERIFY]` |
| **OpenStreetMap / Overpass** | Landmarks — canals, roads, schools | ❌ None | Free | 🔴 Fetch ONCE, commit |
| **SRTM / OpenTopography** | Elevation for lapse correction | ✅ Key (free) | Free | 🔴 Fetch ONCE, commit |
| **Bhashini / ULCA** | Indic TTS, ASR, translation | ✅ Registration | Free (govt) | `[VERIFY]` access flow |
| **edge-tts** | TTS fallback | ❌ None | Free | Unofficial |
| **Gemini API (AI Studio)** | LLM verbalisation + QA | ✅ Key, no card | Free tier | `[VERIFY]` current quota |
| **Agmarknet / data.gov.in** | Mandi prices | ✅ Key (free) | Free | `[VERIFY]` resource id |
| **Supabase** | Postgres + PostGIS + pgvector + auth | ✅ Account | Free tier | 500 MB DB `[VERIFY]` |
| **GitHub Actions** | The scheduler / "server" | ✅ Account | Free | 2,000 min/mo private; unlimited public |
| **Vercel / GitHub Pages** | Hosting + CDN | ✅ Account | Free tier | Generous |
| **Kaggle / Colab** | Free GPU for training | ✅ Account | Free | ~30 h/wk GPU |

🔴 **No credit card is required anywhere in this stack.**

## 29.2 ⚠️ Open-Meteo gotchas

```python
# 🔴 THREE traps that silently corrupt everything downstream

# 1. Single coordinate → OBJECT.  Multiple coordinates → ARRAY.
#    Code written against one shape breaks silently on the other.
resp = get(url, params={"latitude": lats, "longitude": lons, ...})
blocks = resp if isinstance(resp, list) else [resp]

# 2. past_days SHIFTS THE ARRAY ORIGIN.
#    With past_days=2, index 0 is TWO DAYS AGO, not today.
#    🔴 Always locate "now" by parsing the time array. Never assume index 0.

# 3. Returned coordinates are SNAPPED to the model grid.
#    Verify the returned lat/lon against what you requested, or your
#    lattice geometry silently drifts from your interpolation weights.
assert abs(block["latitude"] - requested_lat) < 0.15
```

Variables requested: `temperature_2m, relative_humidity_2m, dew_point_2m, precipitation, wind_speed_10m, wind_direction_10m, cloud_cover, et0_fao_evapotranspiration`.

## 29.3 ⚠️ Sentinel-2 gotchas

Covered in §9.4: the `BOA_ADD_OFFSET = −1000` correction, SCL cloud masking `{0,1,3,8,9,10}`, and the ≥60% valid-pixel rule. All three fail *silently* if skipped.

## 29.4 Fetch-once data

🔴 **Landmarks (Overpass) and elevation (SRTM) are fetched once per district and committed to the repository.** They do not change. Fetching them nightly wastes quota, risks rate limits, and adds a nightly failure mode for data that is effectively static.

## 29.5 The artefact contract — PRAHARI's real API

```jsonc
{
  "type": "FeatureCollection",
  "prahari": {
    "schema_version": "2.0.0",
    "run_id": "2026-01-14T02:14:07+05:30",
    "district": "farrukhabad", "horizon": "today",
    "model": { "id": "potato_late_blight_hutton", "version": "2.0.0",
               "engine_git_sha": "a3f9c21" },
    "data_status": "fresh",          // fresh | stale | degraded
    "degradation": [],               // e.g. ["no_satellite","no_llm"]
    "node_count": 36, "cell_count": 3612,
    "counts": { "safe": 2891, "watch": 549, "act": 172 }
  },
  "features": [{
    "type": "Feature",
    "geometry": { "type": "Polygon", "coordinates": [[...]] },
    "properties": {
      "cell_id": "FRK-R014-C022",
      "band": "act", "risk": 0.91,
      "physics_risk": 0.86, "ml_delta": 0.05, "spatial_contribution": 0.14,
      "dsv_today": 3, "dsv_accum_7d": 19, "criterion_met": true,
      "wet_hours": 8, "min_temp_c": 12.4, "mean_wet_temp_c": 14.1,
      "confidence": 0.82, "confidence_label": "high",
      "spray_start_hour": 30, "spray_end_hour": 33, "spray_quality": 0.88,
      "spray_text_hi": "मंगलवार सुबह ६ से ९ बजे",
      "spray_blocked_by": ["RAIN_AFTER"],
      "et0_mm": 2.4, "ndvi": 0.62, "ndvi_anomaly": -0.08,
      "audio_key": "act_now_hi_7f3a"
    }
  }]
}
```

🔴 **`mean_wet_temp_c` is exposed deliberately** — it is the value that reveals silent bug 2 (§8.6) to any reviewer who checks.

## 29.6 Payload budget

Naive district GeoJSON ≈ 8 MB. Unusable on 2G.

| Technique | Saving |
|---|---|
| Round coordinates to 4 decimals (~11 m) | −45% |
| Drop null properties | −12% |
| Quantise floats to 2 decimals | −8% |
| `turf.dissolve` same-band neighbours at build time | −35% |
| Brotli compression | −70% of the remainder |
| **Result** | **≈ 140 KB per horizon** |

🔴 Farmers fetch only **their own fields'** advisories — a few KB. Full district artefacts are for the officer console.

## 29.7 Adapter interfaces

Every external system sits behind an interface with ≥2 implementations, so a provider change is a config edit:

```python
class WeatherProvider(Protocol): ...   # open_meteo | imd | cached
class SatelliteProvider(Protocol): ... # stac_aws | gee | cached
class LLMProvider(Protocol): ...       # gemini | local_gemma | template
class TTSProvider(Protocol): ...       # bhashini | edge_tts | recorded
```

---

# 30. DATA MODEL

```sql
-- ── GEOGRAPHY ────────────────────────────────────────────────
CREATE TABLE district (
  code TEXT PRIMARY KEY, name TEXT NOT NULL, state TEXT NOT NULL,
  geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
  utm_epsg INT NOT NULL,          -- 🔴 metric CRS for the grid
  area_unit_key TEXT NOT NULL,    -- §7.6 local unit
  active BOOLEAN DEFAULT false
);

CREATE TABLE cell (
  cell_id TEXT PRIMARY KEY,       -- 🔴 'FRK-R014-C022' encodes row/col
  district_code TEXT REFERENCES district(code),
  geom GEOMETRY(Polygon, 4326) NOT NULL,
  centroid GEOGRAPHY(Point, 4326) NOT NULL,
  elevation_m REAL, slope_deg REAL, aspect_deg REAL,
  dist_to_water_m REAL
);
-- 🔴 cell_id encodes row/col so it is STABLE ACROSS REGRIDDING.
--    A sequential id would renumber on any grid change and silently
--    invalidate every historical ledger entry.

CREATE TABLE weather_node (
  node_id TEXT PRIMARY KEY, district_code TEXT, lat REAL, lon REAL,
  elevation_m REAL
);
CREATE TABLE cell_node_weight (          -- precomputed bilinear weights
  cell_id TEXT REFERENCES cell(cell_id),
  node_id TEXT REFERENCES weather_node(node_id),
  weight REAL NOT NULL, PRIMARY KEY (cell_id, node_id)
);
-- 💡 Turns nightly interpolation into a weighted sum. No geometry at runtime.

-- ── FARMER & FIELD ───────────────────────────────────────────
CREATE TABLE farmer (
  id UUID PRIMARY KEY, phone_hash TEXT UNIQUE,  -- 🔴 SHA-256, never raw
  language TEXT DEFAULT 'hi', district_code TEXT,
  consent_share_officer BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE field (
  id UUID PRIMARY KEY, farmer_id UUID REFERENCES farmer(id) ON DELETE CASCADE,
  name TEXT NOT NULL,                    -- 🔴 farmer's own words
  geom GEOMETRY(Polygon, 4326) NOT NULL,
  area_ha REAL NOT NULL,
  capture_method TEXT,                   -- tap_snap | walk | assisted | manual
  centroid_cell_id TEXT REFERENCES cell(cell_id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON field USING GIST (geom);

CREATE TABLE field_season (
  id UUID PRIMARY KEY, field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  season TEXT, crop TEXT, variety TEXT,
  sowing_date DATE, sowing_source TEXT,  -- farmer | satellite | inferred
  active BOOLEAN DEFAULT true
);

CREATE TABLE field_cell (                -- field ↔ cell intersection weights
  field_id UUID, cell_id TEXT, area_fraction REAL,
  PRIMARY KEY (field_id, cell_id)
);

-- ── SCIENCE ──────────────────────────────────────────────────
CREATE TABLE pathogen_model (
  id TEXT PRIMARY KEY, version TEXT NOT NULL, crop TEXT,
  pathogen TEXT, pathogen_kind TEXT,     -- 🔴 'oomycete' ≠ 'fungus'
  model_family TEXT, params JSONB, dsv_table JSONB,
  citation TEXT NOT NULL,                -- 🔴 NOT NULL — no uncited model
  active BOOLEAN DEFAULT true
);

CREATE TABLE cell_risk (
  cell_id TEXT, model_id TEXT, run_date DATE, horizon_day INT,
  band TEXT, risk REAL, physics_risk REAL, ml_delta REAL,
  spatial_contribution REAL, confidence REAL, detail JSONB,
  engine_sha TEXT NOT NULL,
  PRIMARY KEY (cell_id, model_id, run_date, horizon_day)
);
CREATE INDEX ON cell_risk (run_date, band) WHERE band IN ('watch','act');

-- ── OBSERVATION & OPERATIONS ─────────────────────────────────
CREATE TABLE outbreak_report (
  id UUID PRIMARY KEY,
  cell_id TEXT NOT NULL,        -- 🔴 CELL ONLY — never lat/lon, never polygon
  device_hash TEXT NOT NULL, report_date DATE NOT NULL,
  crop TEXT, suspected_pathogen TEXT, severity TEXT,
  verification_level TEXT DEFAULT 'unverified',
  verified_by UUID, withdrawn BOOLEAN DEFAULT false
);

CREATE TABLE spray_log (
  id UUID PRIMARY KEY, field_id UUID REFERENCES field(id) ON DELETE CASCADE,
  spray_date DATE NOT NULL, frac_class TEXT, cost_rs INT,
  logged_at TIMESTAMPTZ DEFAULT now()
);
-- 🔴 Load-bearing for validation (§35): a sprayed field that stayed
--    healthy is NOT evidence the forecast was wrong.

CREATE TABLE alert_log (
  id UUID PRIMARY KEY, farmer_id UUID, field_id UUID,
  channel TEXT, sent_at TIMESTAMPTZ, opened_at TIMESTAMPTZ,
  played_at TIMESTAMPTZ,
  idempotency_key TEXT UNIQUE NOT NULL    -- 🔴 prevents duplicate sends
);

-- ── INTEGRITY ────────────────────────────────────────────────
CREATE TABLE ledger (
  seq BIGSERIAL PRIMARY KEY, payload JSONB NOT NULL,
  prev_hash TEXT NOT NULL, hash TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE RULE ledger_no_update AS ON UPDATE TO ledger DO INSTEAD NOTHING;
CREATE RULE ledger_no_delete AS ON DELETE TO ledger DO INSTEAD NOTHING;
-- 🔴 Append-only enforced by the DATABASE, not by policy.

-- ── PRIVACY ──────────────────────────────────────────────────
CREATE VIEW cell_observations_public AS
SELECT cell_id, COUNT(*) AS report_count,
       MODE() WITHIN GROUP (ORDER BY suspected_pathogen) AS common_report,
       MAX(report_date) AS latest_report
FROM outbreak_report WHERE verification_level <> 'unverified' AND NOT withdrawn
GROUP BY cell_id
HAVING COUNT(DISTINCT device_hash) >= 5;    -- 🔴 k-anonymity IN THE SCHEMA
```

**Row-Level Security:** a farmer reads only their own rows; an officer reads only assigned villages, and only for consenting farmers.

---

# 31. FRONTEND ARCHITECTURE

| Layer | Choice | Why |
|---|---|---|
| Framework | React 18 + Vite + TypeScript (strict) | Fast builds, huge ecosystem, strict types catch schema drift |
| PWA | `vite-plugin-pwa` + Workbox | Installable, offline-first (P6) |
| Map | MapLibre GL JS + MapTiler satellite | Open, free, vector + raster, good mobile performance |
| Geometry | Turf.js | Area, intersection, simplification, dissolve |
| Styling | Tailwind + shadcn/ui | Token-driven (§22.2), fast, accessible primitives |
| Server state | TanStack Query | Cache, retry, background refresh, offline semantics |
| UI state | Zustand | Minimal, no boilerplate |
| Storage | IndexedDB (Dexie) | Fields, advisories, audio, queued writes |
| Charts | Recharts | Forecast timelines |
| ML runtime | onnxruntime-web | On-device vision + segmentation |
| i18n | `i18next` | 🔴 Zero hardcoded strings |

## 31.1 Offline strategy (P6)

```
CACHE-FIRST      app shell · fonts · icons · ML model bundles
STALE-WHILE-     advisory artefacts · audio files
  REVALIDATE     (show cached immediately, refresh in background)
NETWORK-FIRST    officer console live queries
QUEUE + SYNC     spray logs · outbreak reports · field edits
                 → 🔴 idempotency keys, so a replayed queue never duplicates
```

**Airplane-mode acceptance:** open app → see all fields → read/play current advisory → view spray window → log a spray → scan a leaf → all must work.

---

# 32. PERFORMANCE

| Metric | Target | Method |
|---|---|---|
| First contentful paint (3G) | < 1.8 s | Route splitting, inlined critical CSS |
| TODAY screen interactive (3G) | < 2.5 s | Cached artefacts, deferred map |
| Map first render | < 1.5 s | Raster satellite tiles, lazy vector layers |
| Field detail | < 1.0 s | Prefetch on card render |
| On-device inference | < 400 ms | int8 ONNX, ≤5 MB |
| Advisory payload per farmer | < 20 KB | Per-field slicing (§29.6) |
| District artefact | < 150 KB | §29.6 pipeline |
| Nightly job per district | < 20 min | Parallel matrix |
| Weather calls per district-night | ≤ 2 | §8.3 lattice |
| Lighthouse PWA | ≥ 90 | CI-enforced |

🔴 **Test on a real ₹8,000 Android device on throttled 3G, not a desktop simulator.** `[HUMAN]`

---

# 33. SECURITY & PRIVACY

## 33.1 Data minimisation

| We collect | We never collect |
|---|---|
| Field polygon (farmer's own) | Aadhaar, land records, survey numbers |
| Hashed phone (SHA-256) | Raw phone in the analytics path |
| Crop, sowing date | Income, caste, household composition |
| Cell-level reports | Report-level GPS |
| Advisory delivery events | Contacts, SMS, call logs |

## 33.2 Controls

| Area | Control |
|---|---|
| Secrets | GitHub Secrets / Vercel env; 🔴 never committed; `.env` gitignored |
| Client keys | Only public-scoped keys (MapTiler with domain restriction) reach the browser |
| Database | Row-Level Security on every table |
| Reports | k≥5 anonymity in the schema (§16.2) |
| Ledger | Append-only via SQL rules (§30) |
| Images | 🔴 Never stored; on-device inference by default; cloud only on explicit per-image consent |
| Transport | HTTPS everywhere |
| Farmer rights | Full export; full delete; consent revocable at any time |
| Officer access | Role-scoped, consent-gated, audit-logged |

## 33.3 Threat notes

| Threat | Mitigation |
|---|---|
| False outbreak reports | Verification ladder (§16.4); unverified reports have zero weight |
| Report flooding | Rate limits per device hash; anomaly detection |
| Re-identification from reports | Cell-level storage + k≥5 + upward aggregation |
| Prompt injection via a farmer question | Output gate (§27.5) applies to every LLM output |
| Ledger tampering | Hash chain + git history + CI + client-side verification |
| Free-tier key abuse | Server-side only for keyed APIs; strict rate limiting |

---

# ═══════════════════════════════════════
# PART V — RIGOUR
# ═══════════════════════════════════════

# 34. SCIENTIFIC FOUNDATION

## 34.1 The model registry

| Model | Origin | Year | What we use it for |
|---|---|---|---|
| **Smith Period** | Smith, L.P. | 1956 | Legacy comparison band (11 h threshold) |
| **Hutton Criteria** | Derived from Smith | modern | 🔴 Headline rule (6 h threshold) |
| **Wallin DSV** | Wallin, J.R. | 1962 | Graded severity accumulation |
| **BLITECAST** | Krause, Massie & Hyre | 1975 | The operational lineage we sit in |
| **FAO-56 ET₀** | Allen et al. | 1998 | Reference evapotranspiration |
| **Growing Degree Days** | Standard entomology | — | Pest development timing |
| **Magnus formula** | Standard meteorology | — | RH from temp + dew point (§8.3) |
| **Environmental lapse rate** | Standard meteorology | — | 6.5 °C/km elevation correction |

🔴 **Every model in production carries a `citation` field that is `NOT NULL` in the database (§30).** An uncited model cannot be inserted.

## 34.2 The disease triangle argument

Restated because it is the intellectual foundation of the product (§9.1): disease requires host **and** pathogen **and** environment simultaneously. Environment is the only vertex that varies daily and can be forecast — which is why it drives the model. Host status comes from satellite (§9). Pathogen presence comes from community reports (§16). Combination is multiplicative (§10.2), never additive.

## 34.3 🔴 Honest statements about our own science

| Claim we do NOT make | What is actually true |
|---|---|
| "We measure leaf wetness" | We estimate wet duration from **relative humidity as a proxy**. A sensor would be more accurate. |
| "1 km sensing resolution" | 1 km is a **computation and presentation** resolution, downscaled from ~11 km native weather. |
| "We predict disease" | We predict **environmental conducive­ness to infection**. Disease also needs inoculum and a susceptible host. |
| "94% accurate" | Meaningless without a base rate. We publish contingency tables (§18.1). |
| "Better than ICAR" | Unprovable with our data, and not our claim (§4.2). |
| "Our ML model learns disease" | Our ML model learns **residual bias in a physics model** (§26.5), bounded to ±0.25. |

---

# 35. VALIDATION METHODOLOGY

## 35.1 The three validation tiers

| Tier | Method | What it proves |
|---|---|---|
| **1 — Hindcast** | Replay ERA5 historical weather through the engine against documented past outbreak years | The model reproduces known events |
| **2 — Prospective** | Run live, log every prediction to the ledger *before* the outcome is known, score afterwards | 🔴 The only tier that cannot be gamed |
| **3 — Cross-reference** | Compare against institutional forecasts where available | Independent sanity check |

## 35.2 🔴 The frozen-ground-truth protocol

The single most important methodological commitment in the project.

```
1. Collect outbreak observations (officer-verified, lab-confirmed, historical records)
2. 🔴 COMMIT the ground-truth file to git. Record the commit SHA.
3. ONLY THEN tune any parameter or train any ML model.
4. Every published metric cites the ground_truth_commit it was scored against.
5. If ground truth is later extended, the OLD metrics stay published alongside.
```

💡 **Why this matters more than any accuracy number:** tuning against data you have already seen produces impressive metrics that mean nothing. A git SHA is a timestamp nobody can forge. Publishing "scored against ground truth commit `4f9a21c`, frozen before tuning" is a claim Priya (§3.3) can verify herself — and it is the difference between validation and self-congratulation.

## 35.3 🔴 Scoring rules

| Rule | Why |
|---|---|
| **Score negative cases** | Only scoring outbreaks makes any always-on model look perfect |
| **Exclude sprayed fields from miss counting** | A sprayed healthy field is not a forecast failure (§15.1) |
| **Report lead time distribution, not just the mean** | A mean of 62 h hides a bimodal distribution |
| **Score per crop×pathogen, never pooled** | Pooling hides a model that fails on one crop |
| **Publish confidence intervals** | 47 events is a small sample; say so |
| **Never re-score with a changed model without re-labelling the version** | Version drift invalidates comparison |

## 35.4 🔴 Economic calibration — why FAR 0.60 is correct

```python
COST_FALSE_ALARM_RS = 650      # one unnecessary spray per acre [VERIFY]
COST_MISS_RS        = 40_000   # crop loss per acre from missed blight [VERIFY]
# Ratio ≈ 62:1 — a miss is ~62× more expensive than a false alarm

def expected_farmer_cost(hits, false_alarms, misses, correct_negatives):
    return false_alarms * COST_FALSE_ALARM_RS + misses * COST_MISS_RS

# Model A — permissive:  FAR 0.60, POD 0.77  →  ₹6,15,150
# Model B — "tidier":    FAR 0.15, POD 0.50  →  ₹12,66,050
# 🔴 The statistically prettier model costs farmers ~2× more.
```

💡 **This is the argument that reframes the entire accuracy conversation.** A reviewer who sees FAR 0.60 will object. The response is not a defence of the number — it is a demonstration that we optimised the objective that actually matters to a farmer with a ₹80,000 crop, and that the "better-looking" model is the one that hurts them. We publish both columns side by side (§18.1) so nobody has to take our word for it.

⚠️ Both cost constants are `[VERIFY]` — they must be grounded in real local input costs and real loss data, per district and per crop. The *argument* holds at any ratio well above 1:1; the *specific numbers* must be sourced.

## 35.5 Per-model acceptance gates

🔴 **A model does not go live until it passes.**

- [ ] Hindcast reproduces ≥ 70% of documented outbreak events in the test years
- [ ] Prospective POD ≥ 0.70 over a full season
- [ ] Expected farmer cost beats calendar spraying by ≥ 25%
- [ ] Ground truth frozen and committed before any tuning
- [ ] Negative cases scored and published
- [ ] `[HUMAN]` A plant pathologist reviews the trace screen and signs off

---

# 36. TRUST & INTEGRITY

Covered operationally in §18.2. The four layers, restated as a design commitment:

| Layer | Prevents | Verifiable by |
|---|---|---|
| Hash chain | Editing a past prediction | Anyone |
| Git history | Backdating the file | Anyone with the repo |
| CI chain check | An unnoticed break | Automatic, every push |
| 🔴 Client-side `ChainVerifier` | Having to trust us at all | 🔴 The sceptic, in their own browser |

```typescript
// site/src/ChainVerifier.ts — ~80 lines that replace a trust request with a proof
export async function verifyChain(url: string): Promise<VerifyResult> {
  const lines = (await (await fetch(url)).text()).trim().split('\n');
  let prev = GENESIS_HASH;
  for (const [i, line] of lines.entries()) {
    const rec = JSON.parse(line);
    if (rec.prev_hash !== prev) return { ok: false, brokenAt: i };
    const { hash, ...body } = rec;
    if (await sha256(canonicalJSON(body)) !== hash) return { ok: false, brokenAt: i };
    prev = hash;
  }
  return { ok: true, count: lines.length };
}
```

---

# 37. FAILURE MODES

The degradation ladder L0–L12 is specified in §28.3. Additional product-level failure modes:

| Failure | Consequence | Mitigation |
|---|---|---|
| Two false alarms for one farmer | 🔴 **Permanent loss of trust — the worst outcome in the product** | Growth-stage gating (§8.5), confidence display, honest explanation when a warning did not materialise |
| A missed outbreak | Crop loss; reputational damage | Permissive calibration (§35.4); publish the miss |
| Farmer sprays at the wrong time | Wasted money, resistance pressure | Explicit windows with blocking reasons (§13) |
| LLM produces a wrong fact | Potential harm | Output gate + template fallback (§27.5) |
| Field mapped in the wrong place | Wrong forecast delivered | Confirmation step with area in local units (§20.2 Screen 05); editable at any time |
| Officer disagrees with a forecast | Credibility loss with the key channel | "This is wrong" button (§17.3) routes structured feedback to the model team |
| A free tier changes terms | Service interruption | Adapter interfaces with ≥2 implementations (§29.7) |
| Coverage gap turns a farmer away | Permanent user loss | Save the boundary, notify on coverage (§20.3) |

## 37.1 🔴 The false-alarm recovery protocol

When a warning does not materialise, say so **before** the farmer notices:

```
🔊 "पिछले हफ्ते हमने आपको चेतावनी दी थी। बीमारी नहीं आई।
    मौसम बदल गया — बारिश जल्दी रुक गई। यह अच्छी खबर है।
    हम आपको बताते रहेंगे।"

   ("Last week we warned you. The disease did not come.
     The weather changed — the rain stopped early. That is good news.
     We will keep telling you.")
```

💡 **Getting ahead of the disappointment is what preserves the channel.** A farmer who works out on their own that the app was wrong stops listening. A farmer who is told, with the reason, learns that the system is a forecast rather than a prophecy — and forecasts are allowed to be wrong sometimes.

---

# 38. ECONOMICS

## 38.1 Farmer-side economics

| Item | Value |
|---|---|
| Potato crop value, 1.2 ha | ~₹80,000 `[VERIFY]` |
| Uncontrolled blight loss | 40–70% of crop |
| One preventive spray, per acre | ~₹650 `[VERIFY]` |
| Calendar spraying, full season | 6–8 sprays |
| PRAHARI-guided spraying | 3–4 targeted sprays |
| **Expected saving** | **Fewer sprays *and* lower loss risk** |

## 38.2 The asymmetry

A miss costs roughly **62×** a false alarm. Therefore the correct operating point is deliberately permissive, and we publish the reasoning next to the number (§18.1, §35.4). This is the product's central analytical claim.

## 38.3 Operating cost

| Line | Cost |
|---|---|
| Weather API | ₹0 (keyless, within limits) |
| Satellite data | ₹0 (open data) |
| Satellite compute | ₹0 (GEE free tier) |
| Basemap tiles | ₹0 (free tier) |
| Compute / "server" | ₹0 (GitHub Actions cron) |
| Database | ₹0 (Supabase free tier) |
| Hosting + CDN | ₹0 (Vercel / Pages free tier) |
| LLM | ₹0 (Gemini free tier) |
| TTS / ASR | ₹0 (Bhashini) |
| ML training | ₹0 (Kaggle / Colab free GPU) |
| **Total** | **₹0** |

⚠️ **The honest caveat:** IVR telephony and WhatsApp beyond the free service-message tier are the two lines that eventually cost money. Both are flagged as partnership or grant items, not as free-forever claims.

## 38.4 Why cost stays flat with scale

The four decisions in §25.2 mean per-district cost, not per-user cost. Doubling users changes nothing; adding a district adds one matrix entry to a cron job.

## 38.5 Longer-term value beyond the farmer

| Stakeholder | Value |
|---|---|
| State agriculture departments | District risk timelines for advisory planning |
| Crop insurers | A historical validated risk surface for underwriting `[VERIFY]` regulatory position |
| Researchers | Open validation datasets and reproducible model artefacts |
| FPOs | Collective spray scheduling and input-purchase timing (§13.4) |

🔴 **None of these are monetised at the expense of the farmer, and none involve selling farmer data.** Aggregate risk surfaces are derived from public weather and satellite data, not from farmer records.

---

# 39. ETHICS, LIABILITY & RESPONSIBLE DEPLOYMENT

## 39.1 The core ethical tension

A wrong forecast has a real cost to a real person with a borrowed-against crop. This is not a recommendation engine where a bad suggestion wastes thirty seconds.

**Our responses:** publish accuracy honestly including bad numbers (§18.1); show confidence and data age on every surface (§21.5); optimise the farmer's expected cost rather than a statistic (§35.4); route product and dose decisions to a qualified human (§39.2); and get ahead of every false alarm with an explanation (§37.1).

## 39.2 🔴 The advisory boundary

| PRAHARI provides | A qualified human provides |
|---|---|
| Risk forecast | Diagnosis |
| Timing — the spray window | Product selection |
| Weather reasoning | Dose and concentration |
| A resistance-pattern flag | The replacement product |
| "Ask your officer" escalation | The actual prescription |

**Recommending a specific pesticide and dose is a licensed advisory act.** The product is designed so that it structurally cannot do so: no product names in the corpus (§27.4), no dose tables anywhere, a banned-term gate on every LLM output (§27.5), and an automated string test that fails the build if a pesticide name appears in any UI string, template, or copy file (§13.7).

## 39.3 Other commitments

| Area | Commitment |
|---|---|
| **Resistance & environment** | We reduce spray count by targeting timing; we flag repeated modes of action (§13.5). We never recommend a spray the model does not justify. |
| **Equity** | Assisted mapping (§7.2 C) and IVR (§14.6) exist so the product reaches farmers without smartphones — the highest-need group. |
| **Consent** | Officer visibility requires recorded farmer consent, revocable at any time. |
| **Data dignity** | Outbreak reports are commercially sensitive; k≥5 in the schema (§16.2). Images never stored. |
| **Institutional respect** | Position as amplifier and validation partner, never replacement (§4.2, P7). |
| **No dark patterns** | No engagement optimisation. A farmer who opens the app twice a season and prevents a loss is a complete success (§1.6). |

---

# ═══════════════════════════════════════
# PART VI — EXECUTION
# ═══════════════════════════════════════

# 40. PHASED ROADMAP

🔴 **Phases are capability gates, not calendar dates.** A phase is complete when its acceptance criteria pass — not when a week ends. Phase N+1 does not begin until Phase N's gate is met.

## Phase 0 — Foundation
**Gate:** the engine is provably correct and provably pure.

- Repository skeleton with the `engine/` `adapters/` `pipeline/` split (§25.3)
- `tests/test_purity.py` passing and wired into CI
- 🔴 All four silent-bug tests (§8.6) passing
- `models.yaml` with potato late blight (Hutton + Wallin)
- Weather adapter with the three Open-Meteo gotchas handled (§29.2)
- Interpolation with lapse correction and Magnus RH recomputation
- One district: grid built, nodes placed, weights precomputed, elevation and landmarks fetched and committed

**Gate criteria:** engine suite runs offline in < 2 s; determinism verified; `criterion_met([True, False, True]) is False`.

## Phase 1 — The forecast exists
**Gate:** a correct risk artefact is produced nightly, unattended.

- Nightly GitHub Actions job end to end (§28)
- Cell risk → artefact JSON with the full contract (§29.5)
- Payload budget met (< 150 KB per horizon)
- Ledger writing with hash chain + CI verification
- Public accuracy page scaffold with honest empty state
- Degradation ladder L0–L7 implemented

**Gate criteria:** seven consecutive unattended nightly runs; chain verifies; artefact size within budget.

## Phase 2 — 🔴 The farmer can find their field
**Gate:** a real farmer maps a real field unaided. **This is the highest-risk gate in the project.**

- Satellite basemap + landmark overlay + GPS locate (§20.2 Screen 04)
- Field segmentation model 1 trained and deployed (§26.2)
- Tap-to-snap with manual vertex correction
- Walk-the-boundary capture
- Full onboarding Screens 01–08
- Area in hectares + local unit, verified per district `[HUMAN]`
- Field ↔ cell intersection and worst-case aggregation (§8.2 Step 4)

**Gate criteria:** `[HUMAN]` 10 of 12 test farmers complete mapping unaided in < 90 s; snap needs ≤ 3 corrections in ≥ 70% of attempts.

## Phase 3 — The advisory reaches them
**Gate:** a non-literate farmer receives, understands, and can act on an advisory.

- TODAY screen with per-field cards (§21.1)
- Spray window engine with all seven gates (§13.2)
- Pre-generated TTS, hash-keyed (§14.2)
- Three-depth Why panel (§21.4)
- Offline-first PWA with full airplane-mode capability
- SMS + WhatsApp channels

**Gate criteria:** `[HUMAN]` non-literate test user completes the task with the screen covered; airplane-mode acceptance list passes.

## Phase 4 — The extension system is amplified
**Gate:** a real KVK officer uses it in their weekly routine.

- Officer console: weekly triage, model trace, bulk advisory with approval
- Assisted field mapping (§7.2 C)
- Verification queue
- Weekly bulletin PDF
- Offline field mode with sync
- "This forecast is wrong" feedback loop

**Gate criteria:** `[HUMAN]` a plant pathologist reads the trace screen and independently reproduces the verdict; one officer uses the console for four consecutive weeks.

## Phase 5 — Intelligence layers
**Gate:** each layer improves outcomes without ever blocking the forecast.

- Satellite pipeline: NDVI, anomaly, within-field variability (§9)
- Crop-type and phenology models (§26.3, §26.4)
- Growth-stage gating live
- Grounded AI agronomist: verbalisation + RAG QA + output gate (§11, §27)
- Community outbreak network with k≥5 privacy (§16)
- Spread simulation (§10)

**Gate criteria:** every layer independently disableable with the forecast unaffected; 100 sampled LLM outputs contain zero invented facts `[HUMAN]`.

## Phase 6 — Validated and honest
**Gate:** the accuracy page contains real numbers, whatever they are.

- Hindcast against documented outbreak years
- Ground truth frozen and committed **before** any tuning (§35.2)
- Prospective season scored, negative cases included
- ML residual corrector trained and bounded (§26.5)
- Public accuracy page live with the real contingency table
- Client-side chain verifier live

**Gate criteria:** published metrics cite a `ground_truth_commit` that predates all tuning commits; per-model acceptance gates (§35.5) passed.

## Phase 7 — Breadth
**Gate:** each new model passes §35.5 before going live.

- Additional crop×pathogen models (§8.4.1)
- Degree-day pest models (§8.4.2)
- Additional languages (§14.4)
- Additional districts
- Vision confirmation (§12)
- IVR channel
- Fine-tuned Gemma for free-tier independence (§26.7)

🔴 **The rule for Phase 7: breadth is added one validated model at a time.** Shipping ten unvalidated models is worse than shipping one validated one — it converts a credible product into an unfalsifiable one.

---

# 41. TEAM & OWNERSHIP

Four people. Each area needs one owner who is accountable for its acceptance criteria.

| Area | Scope |
|---|---|
| **Engine & science** | `engine/`, `models.yaml`, the four silent-bug tests, validation, the officer trace screen |
| **Pipeline & data** | Adapters, nightly job, artefacts, ledger, database, degradation ladder |
| **Farmer experience** | Onboarding + field mapping (§20 — the highest-risk area), TODAY, map, spray, voice |
| **ML & intelligence** | Nine models (§26), LLM safety layer (§27), satellite pipeline (§28) |

**Shared, non-delegable:** the officer console and the public trust site are built by whoever owns the underlying data, because both are windows onto it.

🔴 **The `[HUMAN]` work is the schedule risk, not the code.** Bigha values per district, the retrieval corpus, human-reviewed translations, farmer usability testing, pathologist sign-off, and ground-truth collection cannot be accelerated by writing more code, and every phase gate depends on some of it. Start each phase's `[HUMAN]` work at the *beginning* of the previous phase.

---

# 42. RISK REGISTER

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| 1 | 🔴 **Farmers cannot map their fields** | Fatal — nothing else runs | Medium | Three capture methods, ML snap, assisted mapping, Phase 2 gate is a real-user test |
| 2 | 🔴 **Wallin table values are wrong** | Severe — invalidates the core model | Medium | `[VERIFY]` item 1, primary-source check before Phase 6 |
| 3 | Ground truth too sparse to validate | Severe — no defensible accuracy claim | High | Hindcast against historical records; community network (§16) as the long-term source; publish confidence intervals |
| 4 | A free tier changes terms | High | Medium | Adapter interfaces with ≥2 implementations (§29.7) |
| 5 | Two false alarms lose a farmer permanently | High | Medium | Growth-stage gating, confidence display, §37.1 recovery protocol |
| 6 | LLM produces a harmful output | Severe | Low | Output gate, banned corpus content, template fallback, string test in CI |
| 7 | Field segmentation fails on Indian parcels | High | Medium | Manual drawing always available; local labelled data `[HUMAN]` |
| 8 | Officers reject it as another dashboard | High | Medium | Built *for* Arun's actual question (§17.1); model trace for credibility |
| 9 | Team lacks depth in a required area | Medium | Medium | One owner per area (§41); adapter boundaries keep areas independent |
| 10 | Pest model base temperatures wrong | Medium | Medium | Every value `[VERIFY]` before that model goes live; §35.5 gate |
| 11 | IVR has no free route | Medium | High | Flagged honestly as a partnership item, not a free-forever claim |
| 12 | Scope grows faster than validation | High | 🔴 High | Phase 7 rule: one validated model at a time |

---

# 43. `[VERIFY]` — CLAIMS NOT YET CONFIRMED

🔴 **This list is a deliverable.** Presenting unverified numbers as settled is the fastest way to lose a domain reviewer. Every item below must be resolved against a primary source, and the list stays in the document with resolutions recorded.

| # | Claim | Priority | How to resolve |
|---|---|---|---|
| 1 | 🔴 **Wallin (1962) DSV band boundaries and breakpoints** | **Highest** | Primary paper or an authoritative extension publication |
| 2 | JHULSACAST / INDO-BLIGHTCAST current resolution, coverage, and delivery | High | ICAR-CPRI publications; direct contact |
| 3 | Pest `T_base` and GDD thresholds for every §8.4.2 model | High | ICAR / state package-of-practices |
| 4 | Open-Meteo non-commercial terms and actual rate limits | High | Provider terms page |
| 5 | Gemini API free-tier quotas (RPM / RPD / TPM) | High | Google AI Studio documentation |
| 6 | Bhashini / ULCA access flow and pipeline identifiers | High | Bhashini developer portal |
| 7 | Cost constants: ₹650 per spray, ₹40,000 per-acre loss | High | Local input prices; state loss assessments |
| 8 | Bigha conversion per target district | High | 🔴 `[HUMAN]` local officer confirmation |
| 9 | Google Earth Engine terms for our specific use | Medium | GEE terms of service |
| 10 | Satellite basemap tile ToS for the free tier we use | Medium | Provider terms |
| 11 | Agmarknet `data.gov.in` resource identifier | Medium | data.gov.in catalogue |
| 12 | Fungicide rainfastness window (the 4-hour assumption) | Medium | Product-class literature |
| 13 | ⚠️ **The "15–25% crop loss" figure is pests + weeds + diseases COMBINED** | Medium | Never quote as disease-only (§2.1) |
| 14 | Supabase free-tier limits at our data volume | Low | Provider pricing page |
| 15 | WhatsApp Cloud API free service-conversation tier | Low | Meta developer documentation |
| 16 | Potato crop value per hectare in target districts | Low | Agmarknet + local data |

---

# 44. GLOSSARY

| Term | Meaning |
|---|---|
| **Band** | Risk level shown to a farmer: safe / watch / act (§21.3) |
| **BOA_ADD_OFFSET** | Sentinel-2 reflectance offset, −1000 for baseline 04.00+ (§9.4) |
| **Cell** | 1 km computational grid square. 🔴 Never shown to a farmer (P1) |
| **CSI** | Critical Success Index — hits / (hits + misses + false alarms) |
| **DSV** | Disease Severity Value — Wallin's daily 0–4 severity score |
| **FAR** | False Alarm Ratio — false alarms / total predicted events |
| **Field** | A farmer's actual mapped parcel. 🔴 The only spatial unit farmers see |
| **FRAC code** | Fungicide Resistance Action Committee mode-of-action group |
| **GDD** | Growing Degree Days — accumulated thermal time (§8.4.2) |
| **Hutton Criteria** | 2 consecutive days: Tmin ≥ 10 °C and ≥ 6 h RH ≥ 90% |
| **Hindcast** | Replaying historical weather through the model to test it |
| **k-anonymity** | Privacy guarantee: no group smaller than k is exposed (§16.2) |
| **KVK** | Krishi Vigyan Kendra — district agricultural extension centre |
| **Lapse rate** | Temperature change with elevation, ~6.5 °C/km |
| **NDVI** | (NIR − Red)/(NIR + Red) — vegetation vigour index |
| **Node lattice** | ~36 weather sample points per district (§8.3) |
| **Oomycete** | 🔴 *Phytophthora* is an oomycete, **not a fungus** |
| **POD** | Probability of Detection — hits / total observed events |
| **Polycyclic** | A pathogen completing multiple infection cycles per season |
| **PWA** | Progressive Web App — installable, offline-capable web app |
| **RLS** | Row-Level Security — per-row database access control |
| **SCL** | Sentinel-2 Scene Classification Layer, used for cloud masking |
| **Smith Period** | Like Hutton but requiring ≥ 11 h RH ≥ 90% |
| **Spray window** | Specific hours when spraying will be effective (§13) |
| **STAC** | SpatioTemporal Asset Catalog — satellite data discovery standard |
| **Wallin DSV** | 1962 graded severity model (§8.4.1) |

---

# ═══════════════════════════════════════
# PART VII — THE PLAIN-LANGUAGE SUMMARY
# ═══════════════════════════════════════

*Everything above in simple words. If you read only this part, you will still understand the project.*

---

## What is this project?

**PRAHARI is an app that warns a farmer about crop disease *before* it happens.**

Crop diseases do not appear randomly. They need particular weather — usually warm nights with very high humidity, which keeps the leaves wet long enough for the disease to take hold. Scientists worked this out decades ago and wrote down the exact rules. For potato blight, the rule is roughly: *if there are two nights in a row where the temperature stays above 10 °C and the air is very humid for more than six hours, the disease will very likely start.*

Here is the useful part: **weather can be forecast.** So the disease can be forecast too — about a week ahead.

PRAHARI does this every night while everyone is asleep:

1. Collects the weather forecast for the next 7 days across the district
2. Runs the scientific disease rules for every small piece of land
3. Checks satellite photographs to see which crop is growing and how healthy it is
4. Works out which fields are in danger, and when
5. Finds the exact hours when spraying will actually work — no rain, no strong wind, not too hot
6. Turns all of that into a short spoken message in the farmer's own language
7. Sends it before the farmer wakes up

In the morning the farmer hears something like: *"There is a blight risk in your canal field. The last two nights were very humid. Spray on Tuesday between 6 and 9 in the morning. Rain is coming at 2 p.m., and after that the spray will wash off."*

That is the whole product. A warning that arrives early enough to be useful, with a specific instruction, spoken out loud.

## The hardest problem we had to solve

There was a serious hole in the earlier design, and it is worth explaining because fixing it changed the whole app.

The original map showed the district divided into small squares, coloured green, orange, and red. **But a farmer looking at that map cannot tell which square is his field.** Most smallholders have one or two hectares split across two to five separate parcels, with no fences and no numbers they know. A grid of coloured squares is meaningless to them. And the farmer could not even see where *he* was standing.

**A warning you cannot locate yourself in is not a product at all.**

So the app was rebuilt around this. Now:

- The map shows a **real satellite photograph** of the village — farmers recognise their own land from above, the same way anyone recognises their own street
- **Landmarks are drawn on top** — the canal, the road, the school, the temple, the pond. This is how farmers actually give directions
- A **"you are here" dot** shows exactly where the farmer is standing, with an honest circle showing how accurate it is
- The farmer **taps on his field**, and a machine-learning model draws the boundary around that parcel automatically. He drags a corner if it is slightly off
- Or he can **walk around the edge of his field** while the phone records the path
- Or a **KVK officer or village helper maps it for him** — which is how farmers with no smartphone get included
- The area is shown in **both hectares and bigha**, so he can immediately tell whether the boundary is right
- He **names the field in his own words** — "the canal field", "behind the school" — and that name is the first thing the voice message says

**The farmer never sees a grid again.** The squares still exist inside the computer, because the science needs them, but they are invisible. The farmer only ever sees his own fields, outlined on a photograph of his own village.

## Who is it for?

**Mainly for the small farmer.** Someone like Sunita — 38 years old, 1.2 hectares of potato in three separate parcels, reads Hindi slowly, prefers to listen, shares a ₹7,000 Android phone with her family, and whose data pack runs out before the month does. Her crop is worth about ₹80,000 and she has borrowed against it. A bad blight year takes half of it away. Today she sprays on a calendar her father used, or when she sees spots — which is already too late.

Everything in the app is designed for her. That is why it speaks instead of writing, why the buttons are large, why it works without internet, and why it never uses a technical word.

**Also for the KVK extension officer.** Someone like Dr. Arun Kale, responsible for 40 villages he cannot possibly visit often enough. He gets a screen that answers his real question — *"which villages need me this week?"* — plus the full scientific working behind every prediction, so he can check whether we are right. He knows this science. He will check. If he trusts it, he reaches thousands of farmers in a way no app can.

**Also for scientists and reviewers.** Everything is published — the accuracy including the bad numbers, the methods, and an honest list of what the app cannot do.

**Also for FPO coordinators**, who need a *village-wide* spray time rather than 40 different individual times — partly because one sprayer is shared between forty fields, and partly because spraying half a village leaves the disease a place to hide and come back from.

## What technologies are we using?

Everything is free. No credit card is needed anywhere.

**The app itself**
- React with Vite and TypeScript — a Progressive Web App, so it installs like an app but needs no app store
- MapLibre with satellite tiles from MapTiler — the map the farmer recognises
- Tailwind CSS for styling
- Works fully offline; everything important is stored on the phone

**The data**
- **Open-Meteo** — free hourly weather forecasts, no key needed. The main input
- **Sentinel-2 and Sentinel-1 satellites** (European Space Agency, free) — 10-metre photographs every 5 days to see the crop. Sentinel-1 uses radar, so it sees through monsoon clouds
- **Google Earth Engine** — free satellite computing, so we never download terabytes
- **OpenStreetMap** — the canal, the roads, the school for the map
- **SRTM elevation** — because a field 200 m higher up is about 1.3 °C cooler, and that changes the disease risk

**The AI and machine learning — nine models**
- **Field boundary detection** — draws the field outline when the farmer taps. This is the model that makes the whole app usable
- **Crop identification** from satellite images over the season, so we never run a potato model on a wheat field
- **Sowing date detection** from the satellite greenness curve, so warnings only start when the crop can actually get sick
- **A risk correction model** — the published science does the main calculation, and machine learning only corrects where it is consistently slightly wrong. The science is always the foundation; the ML is a small bounded adjustment, never more than ±0.25
- **Disease spread simulation** — when disease is confirmed 3 km away, wind direction and distance estimate when it might reach you
- **Leaf photo checking** — a small 4 MB model that runs *on the phone*, offline, so the photo never leaves the device
- **Gemini API (free tier)** — turns the numbers into warm natural speech in any Indian language, and answers spoken questions
- **Bhashini** (Indian government, free) — converts text to speech and speech to text in Indian languages
- **A fine-tuned Gemma model** — trained free on Kaggle's GPUs, as a backup so we are not dependent on anyone's free tier

**Important:** the AI **never invents a number.** The scientific rules calculate everything. The AI is only allowed to *say it nicely in the right language.* Every AI sentence is automatically checked before a farmer hears it — if it contains a number, date, or medicine name that was not in the original data, it is thrown away and a fixed template is used instead. This is deliberate. An AI that can invent a spray dose will eventually invent a wrong one, and a farmer will act on it.

**The behind-the-scenes part**
- **GitHub Actions** is our "server" — a free scheduled job that wakes at 2 a.m., does all the work, and shuts down. There is no always-on server to pay for
- **Supabase** — free Postgres database with maps and geography support
- **Vercel** — free hosting
- **Kaggle and Colab** — free GPUs for training the models

**Why the cost stays at zero even with many users:** the heavy work happens once per district per night, not once per farmer. Weather is fetched for 36 points and the rest is calculated, instead of 3,600 separate requests. The voice messages are made once and reused, because 50,000 farmers share about 40 distinct messages. So 50,000 farmers cost about the same as 50.

## What makes this different

Not that other apps are bad — most of them are good at what they set out to do. It is that PRAHARI picked a different, harder problem:

1. **It warns before, not after.** Most tools help you identify a disease you already have. Useful, but by then the loss has started. Acting before infection is cheaper and works better — it just needs a forecast, which needs real infrastructure
2. **The farmer can actually find his own field.** Solved properly with satellite photos, landmarks, a "you are here" dot, and automatic boundary detection
3. **It tells you exactly when to act.** Not "high risk" but "Tuesday, 6 to 9 in the morning, because it rains at 2"
4. **It speaks.** You never have to read anything
5. **It works without internet.** Everything important is on the phone
6. **It is honest.** We publish our accuracy including the embarrassing parts, and we publish a full page of what the app *cannot* do
7. **It admits that a false alarm is not the same as a miss.** An unnecessary spray costs about ₹650. A missed blight costs about ₹40,000. So we deliberately warn a bit too often rather than too rarely — and we explain that choice publicly instead of hiding it behind a nicer-looking number
8. **It helps the officer instead of replacing him.** We never name a medicine or a dose — that is a licensed professional's job. We give the timing; he gives the treatment

## The honest limitations

Written here because a product that hides its weaknesses cannot be trusted about its strengths.

- We **estimate** how long leaves stay wet from humidity. We do not measure it. A sensor in the field would be more accurate
- Weather comes from points about 11 km apart, and we calculate the values in between. Fields in unusual spots — a deep hollow, right beside a large lake — may differ
- The 1 km detail is a *calculation* resolution, not a *measurement* resolution. We are honest about this
- We only forecast the crops and diseases we have models for. Silence about a disease means we do not model it, not that it is absent
- Spread direction is an estimate from wind and distance. It is not a measurement of where spores actually are
- "No reports nearby" does not mean "no disease nearby". It means nobody has told us
- We do not yet account for the fact that some potato varieties resist blight better than others
- **None of the science is ours.** The rules are from 1956, 1962, and 1975, and Indian institutions have been refining them for decades with data we do not have. What we built is the last mile — getting that science to one specific hectare, in the farmer's language, by voice, in time to act, for free

---

## In one paragraph

PRAHARI is a free, voice-first app that tells a small Indian farmer, about a week in advance, whether crop disease is likely on his own specific field, and gives him the exact hours to spray. It works by running decades-old validated agricultural science over free weather forecasts and free satellite images every night, using nine machine-learning models to fill in what the science alone cannot see, and a carefully restricted AI to speak the result aloud in the farmer's own language. Its hardest and most important design achievement is that the farmer can find his own field on a satellite photograph of his own village, tap it once, and have the boundary drawn for him — because a warning you cannot locate yourself in is not a warning at all. It costs nothing to run, works without internet, publishes its own accuracy including the unflattering numbers, and is deliberately built to make the local extension officer more effective rather than to replace him.

---

**End of PRD.**

*This document is the single source of truth for PRAHARI. Every claim marked `[VERIFY]` in §43 must be resolved against a primary source before it is presented as fact. Every task marked `[HUMAN]` requires a person and cannot be accelerated by writing more code.*

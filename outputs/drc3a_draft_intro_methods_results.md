# DRC3a Draft: Energy Architecture, Reliability, and Oxygen System Fragility in Health Facilities in Eastern DRC

## Working Title

Energy architecture and the hidden reliability requirements of medical oxygen access: high-N survey evidence from health facilities in the Democratic Republic of the Congo

## Positioning Note

This draft is written as the beginning of a Nature Energy style paper. It treats the DRC2 survey as the high-N cross-sectional anchor and frames the next analytical need: longitudinal, high-frequency power and device telemetry to determine when installed oxygen capacity becomes functional oxygen capacity. Several citation details should be checked against the final reference library before submission.

## Introduction

Reliable electricity is increasingly recognized as a health system input rather than a background utility. Health facilities require electricity not only for lighting and communication, but for refrigeration, sterilization, diagnostics, surgical care, patient monitoring, and oxygen delivery. Yet global measures of health-facility electrification often remain organized around binary access: whether a facility has any electricity, whether a main source is present, or whether electricity was available during a recent service-readiness window. These measures are useful for mapping broad deficits, but they under-specify the operational problem faced by facilities that manage clinical services through hybrid, unstable, or intermittently available power systems.

Medical oxygen makes this measurement gap visible. Oxygen is commonly described as an essential medicine, but in practice oxygen access is delivered through infrastructure: concentrators, cylinders, pulse oximetry, distribution systems, pressure regulation, clinical protocols, maintenance routines, and staff who decide when and how to use available oxygen. Some oxygen modalities, especially cylinders, can provide oxygen at the bedside without continuous local electricity. Others, especially concentrators and pressure swing adsorption systems, are directly electricity dependent. As a result, the health-system meaning of "oxygen available" depends on the quality and continuity of the power system underneath it.

The oxygen literature has established that improved oxygen systems can change care and outcomes, especially for children with pneumonia and hypoxaemia. Cluster and implementation studies in Nigeria, Papua New Guinea, Uganda, and other settings show that oxygen system investments can improve oxygen availability, oxygen use, and in some cases mortality outcomes. Trials of oxygen delivery strategies, pulse oximetry, bubble CPAP, and high-flow nasal oxygen show that oxygen is not a single intervention, but a family of technologies whose benefits depend on clinical acuity, staff capacity, monitoring, referral systems, and facility context. Recent solar-powered oxygen studies are particularly important because they explicitly bundle oxygen delivery with a power intervention, showing that reliability is part of the oxygen system rather than an external condition.

However, many oxygen studies still measure energy only as background infrastructure. They report that concentrators are grid-connected, solar-powered, or backed by generators, but often do not quantify source switching, voltage quality, outage timing, generator runtime, battery state, protected circuit behavior, or the human work required to keep oxygen-producing systems online. Conversely, health-facility electrification studies increasingly measure reliability and sufficiency, but rarely treat oxygen as a tracer load whose clinical significance depends on moment-to-moment power quality. This leaves a gap between two literatures: oxygen studies can show that oxygen systems save lives, and energy studies can show that reliable electricity matters for health, but few studies connect energy architecture, reliability, equipment failure, and oxygen modality at scale.

Ryan et al.'s DRC2 work provides the immediate methodological bridge. In a study of health facility electrification in the Democratic Republic of the Congo, the authors define sufficient and reliable power as a combined condition: power must be adequate to serve the facility and reliable enough to exceed a survey-derived uptime threshold. Their preferred survey uptime definition prioritizes the respondent's count of "perfect" power days and then estimates remaining uptime from typical and bad outage days. This uptime definition was validated against high-frequency GridWatch sensor data and aligned more closely with measured uptime than alternative recall definitions. Importantly, the paper shows that reliability is measurable through survey instruments, but also that survey reliability is still a coarse proxy for a temporal process.

This paper extends that logic to oxygen. We ask whether energy regimes are associated with oxygen regimes across a high-N sample of health facilities, whether survey-derived reliability can be inferred from source architecture, and whether reported medical equipment failures suggest a mechanism through which energy instability threatens oxygen functionality. The central claim is not that cross-sectional survey data can prove a causal pathway from power to oxygen outcomes. Rather, the contribution is to show that oxygen access is systematically patterned by energy architecture, while operational reliability remains only partly visible from architecture alone. That combination motivates a high-T research agenda: to understand oxygen capacity, health systems need longitudinal power and device data that can distinguish nominal installed infrastructure from functional oxygen availability.

## Methods and Study Setting

### Study Setting

The analysis uses DRC2 survey data from health facilities in three provinces of the Democratic Republic of the Congo: Nord-Kivu, Sud-Kivu, and Haut Katanga. The study geography captures a heterogeneous electricity landscape, including central grid connections, community mini-grids, private or concession grids, solar systems, generators, and facilities reporting no energy source. This setting is analytically useful because the same clinical need for oxygen is embedded in multiple energy regimes rather than a single national grid environment.

The facility sample includes hospitals and reference facilities across the health system hierarchy: hopitaux generaux de reference, centres hospitaliers, centres de sante de reference, centres medicaux, and a small number of hopitaux provinciaux. Facility type and province are used as descriptive stratifiers and as contextual adjustment variables in exploratory models. Because the provincial and facility-type composition is not random, all results are interpreted as associational and descriptive rather than causal estimates.

### Data Source and Analytical Sample

The primary data source is the DRC2 facility electricity and oxygen survey. The raw survey file contained 565 submissions. Because some facilities had multiple responses, we first reproduced and audited the existing notebook deduplication rule, which selected the most complete response within repeated phone-number and facility-ID pairs. We then constructed a facility master table with one row per facility. Binary infrastructure fields were reconciled using an "any yes" rule across facility responses, while count, cost, and reliability fields were summarized using median, maximum, or latest values depending on the variable type. The resulting facility-level dataset includes 491 unique facilities.

The current facility master should be treated as a manuscript-development dataset. It preserves raw submissions, respondent-level deduplicated records, facility-level reconciliation, and conflict flags. The most important remaining data-quality task before publication is to recover the final Kobo/XLSForm choice labels and facility key used in the original DRC2 workflow, especially for complete confirmation of reliability recall variables and any manually adjudicated facility-type corrections.

### Energy Regime Variables

Energy source architecture was classified from reported grid, generator, and solar access. We created binary indicators for grid, generator, and solar presence; a count of energy sources from zero to three; and mutually exclusive energy profiles: no energy source, grid only, generator only, solar only, grid plus generator, grid plus solar, generator plus solar, and grid plus generator plus solar. Grid architecture was separately classified using the reported grid type into central grid, community mini-grid, private or concession grid, other grid, and no grid.

### Oxygen Regime Variables

Oxygen access was classified from reported oxygen-source fields and concentrator counts. We created indicators for any oxygen source, concentrator presence, cylinder presence, internal PSA, external PSA, other oxygen source, number of oxygen sources, and mutually exclusive oxygen profiles. The main oxygen outcomes in this draft are any oxygen source, concentrator access, cylinder access, multi-source oxygen, and concentrator-versus-cylinder patterning among facilities with oxygen.

### Survey-Based Reliability and Uptime

We reconstructed survey-based uptime using the preferred DRC2 v1 definition described in Ryan et al. The v1 approach treats the respondent's count of perfect power days as the least biased anchor and estimates remaining uptime using typical and bad outage-day information. We also reconstructed a three-day recall uptime measure using reported outage duration over the three recalled days. Facilities were classified as reliable if reconstructed uptime exceeded 91.7%, corresponding to at least 22 hours of power per 24 hours, the threshold used by Ryan et al. to align with the WHO SARA reliability concept.

This reconstruction is provisional pending recovery of the original XLSForm choice labels. The current results should therefore be read as analytical development rather than final inference. The central interpretation is robust to this caveat: source architecture is only a modest predictor of reconstructed reliability, which reinforces the need for direct longitudinal telemetry.

### Equipment Failure Coding

The survey asked whether medical equipment had been damaged and included a free-text field describing the damaged equipment. We coded these free-text responses using a transparent keyword dictionary. Categories included oxygen concentrators and oxygen devices, surgical lighting and operating-theatre electrical devices, electrical components and power-system equipment, ultrasound, patient monitoring, computers and printers, sterilization equipment, laboratory equipment, refrigeration and cold chain, neonatal equipment, radiography, and utility equipment. Cause/context terms were also coded, including voltage instability, power cuts, insufficient power, short circuits or burned electronics, poor installation, and lightning or atmospheric discharge.

The equipment-failure coding is intentionally conservative and auditable. It counts facility-level mentions of categories rather than attempting to infer exact device counts. A later qualitative adjudication step should review ambiguous terms and harmonize French spellings, abbreviations, and local terminology.

### Statistical Analysis

We used descriptive tables and figures to summarize energy and oxygen regimes overall and by facility type and province. We used chi-square tests and binary odds ratios to screen associations between energy predictors and oxygen outcomes. We also fit regularized logistic prediction models with five-fold cross-validation to evaluate whether energy variables predict oxygen access, oxygen modality, equipment damage, and reconstructed reliability. Cross-validated AUC was used as the main predictive-performance metric for binary outcomes, and cross-validated R2 and mean absolute error were used for continuous uptime.

All regression and prediction results are exploratory. Because the survey is cross-sectional and self-reported, we avoid causal language. P-values are interpreted alongside effect sizes and predictive performance, with particular attention to whether statistically detectable associations would be convincing to a reviewer as evidence of a practically meaningful relationship.

## Results

### 1. Energy Architecture Is Associated With Reconstructed Reliability, but Predictive Strength Is Modest

We first asked whether reported energy architecture predicts reconstructed survey reliability. In the facility master, reconstructed uptime v1 was available for 452 facilities. Mean reconstructed v1 uptime was 0.824 and the median was 0.943. Using the DRC2 reliability threshold of 91.7%, 52.1% of facilities met the reliable-power definition.

Energy architecture showed statistically detectable associations with reliability, especially grid architecture. Grid architecture was associated with reliable v1 status (chi-square p=0.000022, Cramer's V=0.24), while overall energy profile was also associated but more weakly (p=0.036, Cramer's V=0.18). Individual source indicators were weaker: solar presence was borderline (p=0.060), generator presence was not significant (p=0.229), and source count alone was not predictive (p=0.531).

The predictive results were modest. A model using energy architecture plus facility type and province predicted reliable v1 status with cross-validated AUC of 0.63. Source flags plus facility type and province produced a similar AUC of 0.63. Grid architecture alone produced AUC of 0.60. Energy profile alone performed no better than chance (AUC approximately 0.50), and source count alone was similarly weak (AUC 0.51). Continuous uptime was even less predictable from architecture: the best model explained only about 5% of cross-validated variation in reconstructed v1 uptime.

These results are important because they prevent an overly simple interpretation. Energy architecture matters, but it is not enough. Source categories provide a partial view of reliability, while operational reliability likely depends on temporal dynamics that the survey cannot fully observe: outage timing, voltage fluctuations, battery state, generator runtime, fuel availability, load prioritization, switching behavior, and local maintenance practices.

### 2. Generator Presence Strongly Predicts Oxygen Access and Concentrator Access

The second result is much sharper. Energy source architecture is strongly associated with oxygen access. Among 491 facilities, 341 (69.5%) reported at least one oxygen source, 313 (63.7%) reported concentrator access, and 152 (31.0%) reported two or more oxygen sources. Oxygen access increased strongly with energy-source complexity: facilities with no reported energy source had 30.8% any oxygen access and 23.1% concentrator access, while facilities reporting grid, generator, and solar had 94.5% any oxygen access and 92.9% concentrator access.

Generator presence was the strongest simple predictor. Facilities with a generator had substantially higher odds of any oxygen source (OR 15.1, p<0.001), concentrator access (OR 14.9, p<0.001), multi-source oxygen (OR 4.3, p<0.001), and cylinder access (OR 3.5, p<0.001). Facilities with two or more energy sources also had higher odds of oxygen access (OR 4.3 for any oxygen; OR 4.3 for concentrators), but the generator signal was much stronger than source count alone.

Solar showed a more nuanced pattern. Solar presence was associated with any oxygen and concentrator access in crude comparisons, but it was not associated with cylinder access, multi-source oxygen, PSA-linked oxygen, or reported equipment damage. This suggests that solar should not be treated as disconnected from oxygen, but neither should it be treated as equivalent to generator-backed oxygen readiness. In this dataset, generator presence appears to mark the facilities where oxygen systems are most likely to be present and layered.

Grid presence alone was not a strong predictor of any oxygen or concentrator access, but it was associated with cylinder access and multi-source oxygen. Grid architecture was also associated with oxygen profile, suggesting that the type of grid environment may shape modality mix more than the binary presence of grid access. This is consistent with the idea that oxygen systems respond not simply to whether electricity exists, but to how facilities manage reliability, backup, and redundancy.

### 3. Bad Power and Outage Burden Predict Equipment Damage, Linking Energy Instability to Oxygen System Fragility

The third result provides the mechanism layer. Across the facility master, 235 of 491 facilities (47.9%) reported medical equipment damage and provided a failure description. Free-text coding showed that oxygen concentrators or oxygen devices were the most frequently mentioned damaged category, reported by 70 facilities. Other common categories included surgical lighting and operating-theatre electrical devices (45 facilities), electrical components or power-system equipment (43), ultrasound or echography (40), patient monitoring or bedside clinical devices (39), computers or printers (35), and sterilization equipment (35).

Cause/context coding showed repeated references to voltage instability, power cuts, insufficient power, short circuits, burned electronics, poor installation, and lightning or atmospheric discharge. These categories should be interpreted as conservative facility-level mentions rather than exhaustive counts. Even so, they are clinically and technically meaningful because they identify the pathway that cross-sectional energy-source variables cannot fully measure: unstable electricity does not merely limit service availability; it can damage the devices that make oxygen access possible.

The association screen supports this interpretation. Bad-power days above the median were associated with equipment damage (OR 3.6, p<0.001), and outage hours above the median were also associated with equipment damage (OR 2.8, p<0.001). Generator presence was associated with equipment damage as well (OR 3.9, p<0.001), likely because generators mark facilities with more electrical equipment, more oxygen technology, and greater exposure to switching, fuel, load, and voltage-management problems. Reconstructed reliable v1 status was associated with lower odds of equipment damage (OR 0.53), consistent with the interpretation that reliability protects equipment functionality.

Together, these results suggest a three-part structure. First, source architecture only modestly predicts reliability, meaning that a cross-sectional energy-source inventory cannot fully characterize operational power quality. Second, generator-backed energy systems strongly predict oxygen access, especially concentrator access. Third, bad power and outage burden predict equipment damage, with oxygen devices the most frequently reported damaged equipment category. This is the empirical bridge to longitudinal telemetry: DRC2 shows the pattern, but high-frequency power and device data are needed to see when oxygen-producing infrastructure is actually usable.

## Draft Figure Logic

Figure 1 should show the literature gap: oxygen-rich studies often under-measure energy, and energy-rich studies often under-measure oxygen. The most useful version is the panel that maps studies by oxygen-system detail and energy-system detail over time, highlighting solar oxygen studies, oxygen-system trials, and energy-reliability studies.

Figure 2 should show the DRC2 high-N regime landscape: energy profiles and oxygen profiles by province and facility type, with facility counts.

Figure 3 should show the ordered empirical claim: energy architecture versus reconstructed reliability; generator presence versus oxygen access; bad power and outage burden versus equipment damage.

Figure 4 should bridge to high-T telemetry: a conceptual and empirical diagram showing how nominal architecture becomes functional oxygen availability only through time-varying uptime, voltage, switching, battery/generator behavior, protected circuits, and human operations.

## Working References to Verify

Ryan et al. DRC2 health facility electrification paper. Assessing the impacts of sufficient and reliable power in health facilities in the Democratic Republic of the Congo.

Graham HR et al. Oxygen systems to improve clinical care and outcomes for children and neonates: a stepped-wedge cluster-randomised trial in Nigeria. PLOS Medicine. 2019.

Conradi N et al. Solar-powered O2 delivery for the treatment of children with hypoxaemia in Uganda: a stepped-wedge cluster randomised controlled trial. The Lancet. 2024.

Duke T et al. Solar-powered oxygen systems in remote health centers in Papua New Guinea: a large-scale implementation effectiveness trial. Journal of Global Health. 2017.

Duke T et al. Solar-powered oxygen quality improvement and child pneumonia deaths: a large-scale effectiveness study. Archives of Disease in Childhood. 2021.

Subhi R et al. Clinical evaluation of a concentrator medical oxygen system with automated cylinder back-up in western Uganda: a pragmatic cluster quasi-experimental trial. VeriXiv. 2025.

Turnbull H et al. Solar-powered oxygen delivery: proof of concept. International Journal of Tuberculosis and Lung Disease. 2016.

Maitland K et al. Children’s Oxygen Administration Strategies Trial / COAST oxygen therapy studies.

McCollum ED et al. Bubble CPAP for children with high-risk conditions and severe pneumonia in Malawi. Lancet Respiratory Medicine. 2019.

Chisti MJ et al. Bubble CPAP for severe pneumonia and hypoxaemia in Bangladesh. The Lancet. 2015.

Gebre M et al. Bubble CPAP for severe pneumonia and hypoxaemia in Ethiopia. Lancet Global Health. 2024.

WHO Service Availability and Readiness Assessment (SARA). Reliability definition based on electricity available without interruptions of more than two consecutive hours during the last seven days.

IRENA. Health facility electrification and energy access indicators.

## Notes for Next Revision

Recover the Kobo/XLSForm choices file and facility key to finalize reliability variable labels, facility-type labels, and any manual corrections from the original DRC2 workflow.

Decide whether the manuscript should use "reliability" as the primary survey measure and reserve "uptime" for the reconstructed metric, or whether to foreground uptime v1 throughout.

Replace working references with formal citation-manager entries and confirm final journal names, years, DOIs, and trial names.

Add high-T telemetry results once the monitoring data are loaded, especially voltage excursions, outage timing, generator switching, protected-circuit behavior, and concentrator/oxygen load implications.

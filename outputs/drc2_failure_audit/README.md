# DRC2 equipment damage answer coding

The audit starts with **565 submissions and 128 original fields**, reproduces the existing completeness/phone/facility deduplication, retains **518 respondents**, and counts each category once per facility across **491 facilities**. The Drive `raw_submissions.csv` contains 35 additional helper fields; it is separately hashed rather than mistaken for the original questionnaire export.

The codebook asks whether medical equipment was damaged because of poor electricity supply (`Codebook!A38:B38`), then asks which equipment and any context about non-functionality and its cause (`Codebook!A39:B39`). See the [exact wording and source](source_manifest.json).

| Coding result | Facilities mentioning category | Denominator |
|---|---:|---:|
| Existing combined oxygen-device category | 70 | 491 |
| Narrower concentrator category | 65 | 491 |
| Lighting / surgical theatre devices | 45 | 491 |
| Electrical components / power system | 43 | 491 |
| Ultrasound / echography | 40 | 491 |

The narrower concentrator category ranks first under the current rules: **65/491 (13.24%)**, or **65/235 (27.66%)** of facilities reporting damage. These are provisional, multilabel **mention counts**. They do not estimate failure risk per concentrator, compare rates per installed device, or independently demonstrate that electricity caused a malfunction. Ownership, age, exposure and reporting differences remain relevant.

The existing answer classifier is a keyword parser, not a trained language model. [Legacy counts](legacy_category_reproduction.csv) are reproduced. The [audited codebook](codebook.json) separates concentrators from unspecified oxygen devices; comparator categories still contain broad word roots and also require review.

The controlled ledger retains the source CSV line, original answer, normalized text, every matching phrase/pattern, respondent deduplication link, facility aggregation and review flags. It contains 240 nonempty retained answers, including 30 without a device-category match, two yes/no-text conflicts and one local negation candidate. No answers or identity crosswalks are released.

`src/train_reviewed_equipment_model.py` prepares a supervised character TF-IDF/logistic baseline. It refuses unreviewed labels, keeps all respondents from a facility in the same validation fold, learns vocabulary within each training fold, and reports precision, recall and F1. **It has not been trained on these answers**: independent labels are pending. Agreement with keyword rules is not independent validation of the finding.

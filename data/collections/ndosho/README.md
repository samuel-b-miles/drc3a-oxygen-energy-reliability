# Ndosho source collection

All Ndosho electricity and operating records belong to collection **N001**. Historical grid/generator logs and later fuel registers are components of the same facility collection, distinguished by source, period and measurement method.

| Component | Released material | Evidence and current limit |
|---|---|---|
| [Charlie Huang historical workbook](historical/source_manifest.json) | [Preserved deidentified XLSX](historical/charlie_kwh_snapshot_deidentified.xlsx), cell ledger, redaction ledger and preservation audit | Source numbers, dates, formulas, cached results, native charts and existing errors retained. Generator kWh includes assumed conversions from runtime. Mixed dates and source calculation errors require a separate correction layer. |
| [Generator and fuel registers](generator_register/source_manifest.json) | Cell projection of both Ndosho tabs; event register table | Manual event runtime totals 96 h; separately labeled model-derived hours total 88.3667 h. The 600 L entered in fuel columns is not an independent metered burn total. The 2023 tab needs date reconciliation. |
| [HOPmeter loads](hopmeter/source_manifest.json) | Pinned retrieval script, 13-file inventory, hashes and coverage/duplicate checks | 3,228,373 source rows, 28 Jan 2023–18 Jan 2024. Originals and row-preserving normalized records are staged locally. Source timezone and physical meter labels remain unverified. No event-period concentrator-load overlap. |
| [Paired PowerWatch](powerwatch/coverage_request.json) | References to the Goma package, filtered to site S004 and series M004/M008 | Both deployed 27 May 2022 and returned measurements in the installation week and 14 Jan–8 Feb 2025 event window. October 2026 returns M004 only. Continuous paired coverage remains unverified; long-history measurement queries timed out. |

Charlie Huang is credited for the historical analysis. Samuel Miles and Layla Kwong are credited as stated in the source poster; Aashika Nair and Allison Wong appear as source annotators. HOPmeter files are credited to Aashika Nair's [astroash11/drc3 repository](https://github.com/astroash11/drc3/tree/c21987d8c0cb3d3653d6aad485ee32661e3a5565/data). No new blanket license is assigned to third-party source data.

The public workbook removes contact details, replaces facility/home labels with pseudonyms, removes private Slides links and omits the embedded poster containing a register photograph. The original is retained unchanged in ignored staging. Professional source credits remain. The named case and canonical references prevent a claim of irreversible anonymity.

Electricity measurements, inferred device operation, measured oxygen delivery and clinical outcomes remain separate. Neither the historical ledger nor these HOPmeter files supplies measured oxygen flow during the January 2025 event.

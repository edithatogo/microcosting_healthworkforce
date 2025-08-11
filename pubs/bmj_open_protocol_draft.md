# Protocol for the validation and application of a transparent, data-driven microcosting model for the Australian health workforce

**Version:** 1.0  
**Date:** 2025-08-12

**Authors:** [Author Names Go Here]

**Affiliations:** [Author Affiliations Go Here]

**Correspondence:** [Corresponding Author Details Go Here]

---

## Abstract

**Introduction:** Accurate microcosting of the health workforce is essential for robust health economic evaluations, strategic policy development, and effective budget planning. However, existing costing studies are often based on opaque spreadsheet models that are difficult to scale, validate, and adapt. This study protocol outlines the development and validation of a novel, open-source Python-based calculation engine designed to provide transparent, reproducible, and extensible workforce costing.

**Methods and Analysis:** This study will be conducted in two phases. The first phase is a software development and validation study. We developed a modular, data-driven calculation engine in Python. The engine's architecture separates data (e.g., salary scales, allowances from enterprise agreements), calculation logic (defined in an auditable JSON format), and reporting, ensuring full transparency. The model will be validated by comparing its outputs against manually calculated values derived from primary source documents (e.g., the Victorian Public Health Sector Enterprise Agreement). The primary validation outcome will be the percentage difference between the model's calculated annual cost and the source-of-truth value for key medical and scientific positions.

The second phase is an applied economic analysis. Using the validated model, we will conduct Deterministic and Probabilistic Sensitivity Analyses (DSA and PSA) to identify the key drivers of cost and quantify the range of cost uncertainty under various plausible scenarios.

**Ethics and Dissemination:** This study utilizes publicly available documents and aggregated, non-identifiable data, and as such, does not require formal ethics committee review. The findings will be disseminated through peer-reviewed publication (this protocol and a subsequent results paper) and presentation at relevant academic conferences. The open-source model itself will be made available on GitHub to ensure full transparency and to facilitate its use and extension by the wider research community.

---

## Introduction

The cost of the health workforce is the single largest driver of expenditure in most healthcare systems globally [1]. Consequently, the accurate and detailed estimation of these costs is a critical component of health economic evaluations, from health technology assessments to the planning of new models of care [2, 3]. Microcosting, which involves the detailed enumeration and costing of every input, is considered the gold standard for this purpose, offering greater precision than top-down allocation methods [4].

Despite its importance, health workforce microcosting faces significant methodological challenges. Studies often rely on bespoke, complex spreadsheet models. While powerful, these models are frequently opaque, making it difficult for third parties to audit the underlying calculations and assumptions. They are also prone to error, difficult to maintain, and lack the scalability required to easily adapt to different industrial agreements, jurisdictions, or professions [5]. This lack of transparency and scalability represents a significant barrier to the reproducibility and extension of health economic research.

To address these limitations, we have developed an open-source, data-driven microcosting calculation engine in Python. This protocol describes the methodology for the formal validation of this tool and its initial application to costing key positions within the Australian healthcare system.

## Aims and Objectives

The primary aim of this study is to validate a transparent and extensible software model for the microcosting of the health workforce and to apply it to a key Australian enterprise agreement.

The specific objectives are:

1.  To validate the outputs of the microcosting engine against a "source-of-truth" dataset derived manually from a contemporary, public-sector enterprise agreement.
2.  To quantify the total annual cost, including all associated on-costs and allowances, for a range of medical and scientific positions.
3.  To use Deterministic Sensitivity Analysis (DSA) to identify the most influential parameters driving cost variations.
4.  To use Probabilistic Sensitivity Analysis (PSA) to estimate the plausible range of cost uncertainty.

## Methods and Analysis

### Study Design

This is a model-based validation study, followed by a descriptive economic analysis using the validated model. The study is structured in two main parts: the validation of the software tool and its application to answer specific research questions.

### The Microcosting Model: A Summary

The software tool at the heart of this study is a Python-based calculation engine. Its key architectural features, designed to ensure transparency and extensibility, are:

-   **Modular Architecture:** The code is separated into distinct modules for data loading, calculation, validation, and reporting.
-   **Data-Driven Logic:** Calculation formulas are not hard-coded in Python. Instead, they are defined in an external, human-readable JSON file (`data/formulas.json`). This allows for easy auditing and adaptation of the model's logic without altering the source code.
-   **Safe Expression Evaluation:** The model uses the `asteval` library to safely parse and evaluate the mathematical expressions defined in the formula file, preventing the execution of arbitrary code.
-   **Integrated Sensitivity Analysis:** The engine includes dedicated modules for conducting DSA and PSA based on parameters defined in external scenario files.

### Phase 1: Model Validation

#### Data Sourcing and Extraction

The source document for this validation study will be the **[Placeholder: e.g., "Victorian Public Health Sector (Medical Scientists, Pharmacists and Psychologists) Enterprise Agreement 2020-2024"]**. The full text of this agreement is publicly available from **[Placeholder: e.g., "the Fair Work Commission website"]**.

A data extraction protocol will be followed. Two researchers will independently extract key cost parameters for all included job classifications. These parameters will include:
-   Base salary scales at each grade and step.
-   Standard allowances (e.g., professional development, uniforms).
-   Penalty rates for overtime, weekend, and public holiday work.
-   Leave entitlements (annual, sick, long-service).
-   Superannuation guarantee rate.

Extracted data will be compiled into a "source-of-truth" validation dataset. Any discrepancies between the two researchers will be resolved by consensus or by a third reviewer.

#### Validation Procedure

The model will be run to calculate the total annual cost for each included position. The primary validation endpoint is the percentage difference between the model's output and the value from the "source-of-truth" dataset. The model will be considered validated if the percentage difference is less than 0.1% for all tested positions, a threshold chosen to allow for minor floating-point discrepancies while ensuring substantive accuracy.

### Phase 2: Model Application

#### Deterministic Sensitivity Analysis (DSA)

Using the validated model, a one-way DSA will be conducted. Key input parameters (e.g., superannuation rate, key allowances, productive time percentage) will be varied by a plausible range (e.g., +/- 10%). The results will be presented in a tornado plot to visually identify the parameters with the most significant impact on the final cost.

#### Probabilistic Sensitivity Analysis (PSA)

A PSA will be conducted to explore the impact of simultaneous parameter uncertainty. Key parameters will be assigned probability distributions (e.g., a normal distribution for productive time, a uniform distribution for certain allowances). The model will be run for a large number of Monte Carlo simulations (e.g., 10,000). The results will be presented as a histogram of the mean cost, with 95% uncertainty intervals calculated.

## Patient and Public Involvement (PPI)

This study is a methodological and economic modeling study based on publicly available administrative documents. Therefore, there was no direct patient or public involvement in the design or conduct of the study.

## Ethics and Dissemination

This study uses publicly available, non-personal data in the form of enterprise agreements. No individual-level or patient-level data will be used. As such, this research is considered exempt from formal ethics committee review.

The results of this study will be submitted for publication in a peer-reviewed journal. The findings will also be presented at relevant national and international health economics and health services research conferences.

To promote transparency, reproducibility, and collaboration, the full source code for the microcosting engine, along with the documentation and protocols, will be maintained in a public GitHub repository.

## References

[1] [Placeholder reference on health system expenditure]  
[2] [Placeholder reference on the importance of costing in HTA]  
[3] [Placeholder reference on workforce planning]  
[4] [Placeholder reference on microcosting methodology]  
[5] [Placeholder reference on limitations of spreadsheet models]

# Statement of Work: Supplier Invoice Processing for Crestline Health Partners

## 1. Background

Crestline Health Partners operates 23 hospitals and receives about 60,000 supplier invoices per month for drugs, consumables and equipment. Accounts payable staff match invoices to purchase orders and goods receipts manually in Oracle Fusion, and 11 percent of invoices miss their early-payment discount window.

## 2. Scope of Work

The vendor will implement automated invoice capture and three-way matching: extract header and line-item data from PDF and scanned invoices, match each line to the purchase order and goods receipt in Oracle Fusion within configurable tolerances, flag exceptions such as price or quantity variance, and post matched invoices for payment approval.

## 3. Deliverables

D1: Invoice capture service. D2: Three-way matching engine with tolerance rules. D3: Exception handling workbench for AP staff. D4: Oracle Fusion integration. D5: Monthly accuracy and savings report template. D6: Forty-five days of hypercare.

## 4. Timeline and Milestones

The engagement lasts 18 weeks beginning 7 April 2027. M1, process mapping, completes in week 3. M2, the matching pilot at 3 hospitals, completes in week 9. M3, finance controller UAT, runs in weeks 13 and 14. Go-live across all 23 hospitals is planned for week 16.

## 5. Fees and Payment Terms

The fixed implementation fee is USD 336,000, invoiced 25 percent at kickoff, 25 percent at M2, and 50 percent at go-live. Payment is due within 30 days. In addition, a gain-share of 10 percent of verified early-payment discounts captured in the first 12 months is payable quarterly, capped at USD 90,000.

## 6. Service Levels

Invoices must be captured and matched within 4 business hours of receipt. Header field accuracy must be at least 98 percent and line-item accuracy at least 94 percent. Monthly availability is 99.7 percent. Severity 1 incidents receive a response within 30 minutes.

## 7. Assumptions

Crestline will provide Oracle Fusion sandbox access by week 2 and 12 months of historical invoices. Tolerance rules (default 2 percent price variance and 5 percent quantity variance) will be confirmed by the finance controller.

## 8. Out of Scope

Supplier master data cleansing, payment execution, tax filing and contract compliance checks are out of scope.

## 9. Acceptance Criteria

Go-live is accepted after two consecutive month-end closes in which matched invoices meet the accuracy service levels and no duplicate payments occur. The CFO signs the final acceptance.

## 10. Data Security

The solution runs in Crestline's Oracle Cloud Infrastructure (OCI) tenancy in the Hyderabad region. Data is encrypted at rest and in transit, supplier bank details are masked in the workbench, and logs are retained for 7 years to meet audit requirements.

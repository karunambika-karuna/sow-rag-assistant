"""Synthetic Statements of Work used as the demo corpus.

All clients, people and figures are fictional. The four SOWs deliberately share
the same section structure (payment terms, SLAs, milestones ...) with different
values, so the retriever has to find the right client's section rather than
any section about the right topic. That is what makes the benchmark non-trivial.
"""

SOWS = [
    {
        "file": "northwind_mutual_claims_sow",
        "format": "pdf",
        "title": "Statement of Work: Claims Intake Automation for Northwind Mutual Insurance",
        "sections": [
            ("1. Background",
             "Northwind Mutual Insurance processes roughly 18,000 motor and property claims per month. "
             "Claim packets arrive by email and through the broker portal as scanned PDFs, photos and "
             "handwritten forms. Today a team of 42 intake clerks keys the data into the ClaimCore system, "
             "with an average handling time of 26 minutes per claim. Northwind wants to reduce manual "
             "keying, shorten first notice of loss (FNOL) turnaround and improve data quality."),
            ("2. Scope of Work",
             "The vendor will build an intelligent document processing pipeline that classifies incoming "
             "claim documents into 11 document types, extracts 64 fields (policy number, loss date, loss "
             "location, vehicle registration, estimated damage and claimant details), validates them "
             "against the policy administration system and pushes approved records to ClaimCore through "
             "its REST API. Low-confidence fields are routed to a human review queue."),
            ("3. Deliverables",
             "D1: Document classification model and confusion-matrix report. D2: Field extraction service "
             "with confidence scores. D3: Human review web screen. D4: ClaimCore integration adapter. "
             "D5: Operations runbook and administrator training for up to 15 Northwind staff. "
             "D6: Ninety days of hypercare support after go-live."),
            ("4. Timeline and Milestones",
             "The engagement runs for 20 weeks from the kickoff date of 6 January 2027. Milestone M1, "
             "discovery and sample collection, completes in week 3. M2, the classification pilot on 2,000 "
             "historical claims, completes in week 8. M3, user acceptance testing, runs in weeks 15 to 17. "
             "Production go-live is planned for week 18, followed by hypercare."),
            ("5. Fees and Payment Terms",
             "The total fixed fee is USD 412,000. Payments are invoiced against milestones: 20 percent at "
             "kickoff, 30 percent on completion of M2, 30 percent on UAT sign-off and 20 percent thirty days "
             "after go-live. Invoices are payable within 45 days of receipt. Travel expenses are billed at "
             "cost and capped at USD 18,000."),
            ("6. Service Levels",
             "The production service must be available 99.5 percent of the time per calendar month, "
             "excluding scheduled maintenance on Sundays between 01:00 and 05:00 IST. Severity 1 incidents "
             "receive a response within 30 minutes and a workaround within 4 hours. Field-level extraction "
             "accuracy must be at least 95 percent on the agreed test set. Each missed availability target "
             "earns a service credit of 5 percent of the monthly support fee."),
            ("7. Assumptions",
             "Northwind will provide at least 5,000 labelled historical claim documents before week 4. "
             "ClaimCore API credentials and a sandbox environment will be available by week 6. Documents are "
             "in English; Hindi handwritten forms are out of scope for phase one."),
            ("8. Out of Scope",
             "Fraud scoring, payment disbursement, reserve setting and any changes to the ClaimCore user "
             "interface are excluded. Migration of historical claims older than 24 months is also excluded."),
            ("9. Acceptance Criteria",
             "A deliverable is accepted when Northwind signs the acceptance certificate or does not raise a "
             "written defect within 10 business days of delivery. UAT passes when no Severity 1 or Severity 2 "
             "defects remain open and extraction accuracy meets the service level."),
            ("10. Data Security",
             "All claim data stays in Northwind's Azure tenant in the Central India region. Personal data is "
             "encrypted at rest with AES-256 and in transit with TLS 1.2 or higher. Vendor staff access "
             "production data only through Northwind-managed virtual desktops, and access logs are retained "
             "for 365 days."),
        ],
    },
    {
        "file": "asterix_bank_kyc_sow",
        "format": "docx",
        "title": "Statement of Work: KYC Document Automation for Asterix Retail Bank",
        "sections": [
            ("1. Background",
             "Asterix Retail Bank onboards about 9,500 new retail customers per month across 140 branches. "
             "Know Your Customer (KYC) verification relies on branch staff comparing identity and address "
             "documents by eye, which causes a median account-opening delay of 3 working days and frequent "
             "audit findings. The bank wants an automated KYC document check with a clear audit trail."),
            ("2. Scope of Work",
             "The vendor will deliver a KYC document verification service that accepts PAN cards, passports, "
             "voter IDs, driving licences and utility bills; extracts name, date of birth, document number "
             "and address; checks consistency across documents with fuzzy name matching; detects tampering "
             "signals; and returns a verification decision with reasons to the bank's onboarding platform, "
             "OnboardX."),
            ("3. Deliverables",
             "D1: KYC extraction and cross-document matching service. D2: Tamper-detection module. "
             "D3: Decision explanation report for each application. D4: OnboardX integration. "
             "D5: Model risk documentation aligned to the bank's model governance policy. "
             "D6: Sixty days of hypercare support."),
            ("4. Timeline and Milestones",
             "The project runs for 16 weeks starting 3 February 2027. M1, data access and design sign-off, "
             "completes in week 2. M2, the extraction pilot at 5 branches, completes in week 7. M3, the model "
             "risk review with the bank's validation team, completes in week 11. Go-live across all branches "
             "is planned in week 14."),
            ("5. Fees and Payment Terms",
             "The engagement is billed on time and materials with a not-to-exceed cap of INR 1,85,00,000. "
             "Blended day rates are INR 38,000 for engineers and INR 52,000 for the solution architect. "
             "Invoices are raised monthly in arrears and are payable within 30 days. Any work beyond the cap "
             "requires a signed change request."),
            ("6. Service Levels",
             "The verification API must respond within 3 seconds for 95 percent of requests and be available "
             "99.9 percent of the time per month. Severity 1 incidents receive a response within 15 minutes "
             "and resolution within 2 hours. The false acceptance rate for tampered documents must stay below "
             "0.5 percent on the bank's red-team test set."),
            ("7. Assumptions",
             "The bank will provide 20,000 anonymised historical KYC files and access to the OnboardX test "
             "environment by week 2. Branch staff will be available for two pilot feedback sessions. The bank "
             "is responsible for regulatory interpretation of RBI KYC master directions."),
            ("8. Out of Scope",
             "Video KYC, biometric face matching, sanctions and PEP screening, and credit bureau checks are "
             "excluded from this SOW and may be addressed in a later phase."),
            ("9. Acceptance Criteria",
             "The pilot is accepted when straight-through verification reaches 70 percent of applications "
             "with zero high-risk misses, as measured over two consecutive weeks. Final acceptance requires "
             "sign-off from the bank's model validation team and the head of retail operations."),
            ("10. Data Security",
             "All data is processed on the bank's on-premise Kubernetes cluster in Mumbai; no customer data "
             "may leave the bank's network. Vendor engineers work from the bank's secure development centre. "
             "Audit logs of every verification decision are retained for 8 years."),
        ],
    },
    {
        "file": "helios_rfq_sow",
        "format": "pdf",
        "title": "Statement of Work: RFQ Processing Automation for Helios Industrial Supply",
        "sections": [
            ("1. Background",
             "Helios Industrial Supply is a B2B distributor of bearings, valves and electrical components. "
             "Its sales desk receives around 1,200 requests for quotation (RFQs) per week by email, as PDFs, "
             "spreadsheets and scanned drawings. Quoting is manual and takes an average of 2.5 days, and "
             "Helios estimates it loses 15 percent of opportunities to slow responses."),
            ("2. Scope of Work",
             "The vendor will automate RFQ intake: extract line items (part number, manufacturer, quantity, "
             "required delivery date) from each RFQ, normalise manufacturer names against Helios's brand "
             "master, recommend up to three suppliers per line based on purchase history, and create draft "
             "quotations in the Helios CRM for sales review. A quote or no-quote recommendation is produced "
             "for each RFQ."),
            ("3. Deliverables",
             "D1: RFQ extraction service for PDF, Excel, Word and email bodies. D2: Brand normalisation "
             "module. D3: Supplier recommendation engine. D4: CRM integration for draft quotations. "
             "D5: Sales desk dashboard showing RFQ status and turnaround. D6: Thirty days of hypercare."),
            ("4. Timeline and Milestones",
             "The work is delivered in two phases over 24 weeks from 10 March 2027. Phase 1 (weeks 1 to 12) "
             "covers extraction and CRM integration, with M1 extraction pilot in week 6. Phase 2 (weeks 13 to "
             "24) covers supplier recommendation and the dashboard, with M2 recommendation pilot in week 18 "
             "and full go-live in week 22."),
            ("5. Fees and Payment Terms",
             "The fixed fee is USD 268,000 for phase 1 and USD 194,000 for phase 2. Each phase is invoiced "
             "40 percent at phase start and 60 percent on phase acceptance. Invoices are payable within 60 "
             "days. A monthly support retainer of USD 6,500 begins after hypercare ends."),
            ("6. Service Levels",
             "Draft quotations must be created within 15 minutes of RFQ receipt for 90 percent of RFQs "
             "during business hours. Line-item extraction accuracy must be at least 92 percent. Platform "
             "availability is 99.0 percent per month. Severity 1 incidents receive a response within 1 hour."),
            ("7. Assumptions",
             "Helios will provide three years of purchase order history and a brand master of approximately "
             "900 manufacturers. The CRM vendor will expose the quotation API with at least 50 writable "
             "fields. Pricing decisions remain with the Helios sales team."),
            ("8. Out of Scope",
             "Automatic price calculation, sending quotations to customers without human approval, supplier "
             "onboarding and ERP inventory synchronisation are out of scope."),
            ("9. Acceptance Criteria",
             "Each phase is accepted when its pilot meets the service levels for four consecutive weeks and "
             "the Helios sales director signs the phase acceptance form."),
            ("10. Data Security",
             "The solution is hosted on AWS in the ap-south-1 (Mumbai) region inside Helios's account. "
             "Customer pricing data is classified as confidential, encrypted with AWS KMS keys, and access "
             "is restricted by IAM roles. Logs are retained for 180 days."),
        ],
    },
    {
        "file": "crestline_health_invoices_sow",
        "format": "md",
        "title": "Statement of Work: Supplier Invoice Processing for Crestline Health Partners",
        "sections": [
            ("1. Background",
             "Crestline Health Partners operates 23 hospitals and receives about 60,000 supplier invoices per "
             "month for drugs, consumables and equipment. Accounts payable staff match invoices to purchase "
             "orders and goods receipts manually in Oracle Fusion, and 11 percent of invoices miss their "
             "early-payment discount window."),
            ("2. Scope of Work",
             "The vendor will implement automated invoice capture and three-way matching: extract header and "
             "line-item data from PDF and scanned invoices, match each line to the purchase order and goods "
             "receipt in Oracle Fusion within configurable tolerances, flag exceptions such as price or "
             "quantity variance, and post matched invoices for payment approval."),
            ("3. Deliverables",
             "D1: Invoice capture service. D2: Three-way matching engine with tolerance rules. "
             "D3: Exception handling workbench for AP staff. D4: Oracle Fusion integration. "
             "D5: Monthly accuracy and savings report template. D6: Forty-five days of hypercare."),
            ("4. Timeline and Milestones",
             "The engagement lasts 18 weeks beginning 7 April 2027. M1, process mapping, completes in week 3. "
             "M2, the matching pilot at 3 hospitals, completes in week 9. M3, finance controller UAT, runs in "
             "weeks 13 and 14. Go-live across all 23 hospitals is planned for week 16."),
            ("5. Fees and Payment Terms",
             "The fixed implementation fee is USD 336,000, invoiced 25 percent at kickoff, 25 percent at M2, "
             "and 50 percent at go-live. Payment is due within 30 days. In addition, a gain-share of 10 "
             "percent of verified early-payment discounts captured in the first 12 months is payable "
             "quarterly, capped at USD 90,000."),
            ("6. Service Levels",
             "Invoices must be captured and matched within 4 business hours of receipt. Header field accuracy "
             "must be at least 98 percent and line-item accuracy at least 94 percent. Monthly availability is "
             "99.7 percent. Severity 1 incidents receive a response within 30 minutes."),
            ("7. Assumptions",
             "Crestline will provide Oracle Fusion sandbox access by week 2 and 12 months of historical "
             "invoices. Tolerance rules (default 2 percent price variance and 5 percent quantity variance) "
             "will be confirmed by the finance controller."),
            ("8. Out of Scope",
             "Supplier master data cleansing, payment execution, tax filing and contract compliance checks "
             "are out of scope."),
            ("9. Acceptance Criteria",
             "Go-live is accepted after two consecutive month-end closes in which matched invoices meet the "
             "accuracy service levels and no duplicate payments occur. The CFO signs the final acceptance."),
            ("10. Data Security",
             "The solution runs in Crestline's Oracle Cloud Infrastructure (OCI) tenancy in the Hyderabad "
             "region. Data is encrypted at rest and in transit, supplier bank details are masked in the "
             "workbench, and logs are retained for 7 years to meet audit requirements."),
        ],
    },
]

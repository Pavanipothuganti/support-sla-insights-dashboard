# Support SLA Breach Analysis Dashboard

Streamlit dashboard and batch pipeline for identifying weekly first-response SLA breaches by agent and shift.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Put the supplied files in `data/`: `tickets.csv`, `agents.csv`, `orders.csv`, `customers.csv`, `products.csv`, `support-policy.pdf`, and `email-thread.txt`. The CSV loader normalises column names and reports missing or malformed inputs in logs.

## Run

Generate reports:

```powershell
python run_analysis.py --cost-per-breach 350 --target-rate 15
```

Launch the dashboard:

```powershell
streamlit run app.py
```

The dashboard can also rerun the pipeline from its sidebar. Generated files are written to `reports/`.

## Project structure

```text
app.py                         Streamlit UI
run_analysis.py                Batch orchestration and CLI
src/data_loader.py             CSV loading, normalisation, quality checks
src/sla_calculator.py          Policy parsing and SLA flags
src/agent_analysis.py          Agent summaries
src/shift_analysis.py          Shift summaries and roster join
src/business_impact.py         Loss and savings estimates
src/validation.py              Sample checks and validation report
data/                          Source files supplied by Vireo
reports/                       Generated outputs
```

## Assumptions

- First response is the difference between the ticket creation timestamp and first response timestamp. If the source provides a numeric `first_response_time`, it is interpreted as hours.
- First-response targets are channel-specific and read from `support-policy.pdf` (chat: 15 minutes, voice: 2 hours, social: 4 hours, email: 8 hours). If the PDF cannot be read, these policy targets are used as defaults.
- Duplicate `ticket_id` rows are removed before analysis because the email thread notes that some tickets were re-imported during migration reconciliation.
- Source timestamps are UTC. SLA durations use elapsed UTC time; weekly reporting and roster assignment dates use India Standard Time (IST). Weeks run Monday-to-Sunday. Roster shifts are matched to the ticket creation date using `from_date`/`to_date`; invalid or unmatched assignment dates are `Unknown`.
- The default configurable cost is Rs 350 per breached ticket, matching the policy's automatic SLA credit. Vireo volume is estimated at 650 tickets per week.
- The financial estimate is a planning estimate, not an accounting statement.

## Outputs

`weekly_sla_report.csv`, `agent_performance_report.csv`, `shift_performance_report.csv`, `business_impact_report.csv`, `ticket_sla_detail.csv`, and `validation_report.txt`.

# Telecom Customer Operations Decision Hub

[![Live site](https://img.shields.io/badge/Live%20site-GitHub%20Pages-007C7C?style=flat-square)](https://timkong21.github.io/telecom-customer-operations-decision-hub/)

A source-driven portfolio product for operational decision support.

## About

This portfolio product is inspired by the [PwC Switzerland Power BI in Data Analytics virtual case experience on Forage](https://www.theforage.com/virtual-internships/prototype/a87GpgE6tiku7q3gu/Power%20BI%20in%20Data%20Analytics?ref=zYi2CnpbWjhcS7sAk). It extends the three case themes into a browser-based decision hub that communicates findings, evidence, and practical next steps for stakeholders.

It is not commissioned, endorsed by, or affiliated with PwC.

## Live product

Visit the [Telecom Customer Operations Decision Hub](https://timkong21.github.io/telecom-customer-operations-decision-hub/).

## Decision areas

| Area | Product focus | Source material |
| --- | --- | --- |
| Service operations | Call demand, resolution outcomes, and agent performance | Task 1: Call Centre Trends |
| Customer retention | Churn risk signals, customer segments, and intervention priorities | Task 2: Customer Retention |
| Diversity & inclusion | Representation, promotions, performance, and turnover context | Task 3: Diversity & Inclusion |

## How the hub is built

The hub is a static, source-driven reporting product. `scripts/analyze_case_data.py` reads the supplied source workbooks and produces [`site/data/case-metrics.json`](site/data/case-metrics.json). The site then renders those metrics as native browser charts, tables, and recommended decision actions.

The live hub is deliberately different from the original Power BI reference files:

- The web product is publicly viewable, responsive, and designed for concise stakeholder reporting.
- The `.pbix` files remain in the task folders as historical reference materials that can be opened in Power BI Desktop.
- Original screenshots in [`README assests`](README%20assests) are retained as portfolio evidence; the live charts are calculated from the supplied workbooks rather than embedded from an external dashboard service.

<p align="center">
  <img src="README%20assests/Project_Themes.png" alt="The three decision areas covered by the hub" style="width: 80%" />
</p>

## Run locally

Prerequisites: Node.js 20+ and Python 3 with `pandas` available.

```bash
npm run analyze
npm run build
npm run preview
```

`analyze` regenerates the auditable metrics JSON, `build` creates the static `dist` output, and `preview` prints the local URL to open.

## Deploy to GitHub Pages

The repository uses the existing manual **Deploy GitHub Pages** workflow.

1. Push the intended commit to `main`.
2. In GitHub, open **Actions** and select **Deploy GitHub Pages**.
3. Choose **Run workflow**, retaining the `main` branch.
4. After the run succeeds, verify the [live hub](https://timkong21.github.io/telecom-customer-operations-decision-hub/).

The workflow regenerates the static site and deploys its artifact; do not commit `dist`.

## Evidence and limitations

- This is portfolio-case data, not a live telecom operating system or a production decision engine.
- The visual relationships are descriptive associations; they do not establish causality.
- The supplied Diversity & Inclusion PBIX reference reports 10.1% turnover. The supplied workbook calculates 9.4% (47 of 500 FY20 leavers); the web hub displays the auditable workbook result and calls out this reconciliation.

## License and case-material notice

Author-created code and documentation are available under the [MIT License](LICENSE). The supplied workbooks, PBIX files, reference screenshots, external marks, and other case materials are excluded from that grant; see [NOTICE.md](NOTICE.md).

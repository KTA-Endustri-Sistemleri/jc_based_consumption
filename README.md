### JC Based Consumption

Job Card based Consumption for ERPNext Custom Systems.

This app overrides the default **Job Card → on_submit** behavior:

- If **Manufacturing Settings > Job Card and Capacity Planning > Job Card based Consumption** is enabled:
  - Creates **Material Consumption** and **Manufacture Stock Entries** directly from the Job Card.
  - Tracks consumption and production quantities per Job Card.
- If disabled:
  - Falls back to the **default ERPNext behavior**.

✅ Developed and tested on **ERPNext v15.x.x (develop branch, commit 29197af)**.
✅ Developed and tested on **ERPNext v15.79.0

---

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app jc_based_consumption
```

---

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/jc_based_consumption
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

---

### License

MIT

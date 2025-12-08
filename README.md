# IT566 Final Project — Campaigns & Channels CLI

> **Author:** Liam Progulske  
> **Course:** IT566 — Computer Scripting Techniques  
> **Description:** A Python/MySQL command-line system to manage advertising campaigns, channels, and daily marketing performance metrics with analytics such as CTR, CPC, and ROAS.

---

## 🛠 Technologies Used

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=flat-square)
![MAMP](https://img.shields.io/badge/MAMP-Local%20DB-lightgrey?style=flat-square)
![CLI](https://img.shields.io/badge/Interface-CLI-green?style=flat-square)

---

## How to Run the Application

### 1. Build the Database

```sql
SOURCE app_framework/database/mysql/build_db.sql;
```

### 2. Rebuild & Test Everything
```sql
SOURCE app_framework/database/mysql/rebuild_and_test.sql;
```

### 3. Start CLI Application
python3 app_framework/src/main.py -c app_framework/config/IT566_app_config.json

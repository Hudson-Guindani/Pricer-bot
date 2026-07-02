# Price Approver Bot

This project features a ChatOps automation assistant developed in Python that bridges Telegram messaging with a corporate Oracle Database (WinThor ERP schema). 

The bot automates the approval and registration of promotional prices or discount campaigns. When a user with a `Manager` role replies **"ok"** to an internal price request, the system parses the text using Regular Expressions, determines commercial routing rules (subsidiaries, regions, or retail chains), and injects a live promotional entry into the database.

### 🚀 Features

- **ChatOps Promotion Workflow:** Monitors chat streams and listens for explicit confirmations (`ok`) issued only by an authorized `Manager` profile.
- **Regex Information Parsing:** Scans the text structured layout to isolate dynamic integers and floats for `cliente` (customer), `produto` (product ID), and `preco` (promotional price).
- **Dynamic ERP Business Logic Routing:** Queries `PCCLIENT` and `PCTABPRCLI` to resolve specific structural definitions such as identifying retail chains (`codrede`), corporate tax status (`tipofj`), geographic operating regions (`numregiao`), or FIFO inventory overrides.
- **SQLAlchemy Transaction Injection:** Generates a new unique key sequence from Oracle (`DFSEQ_PCPRECOPROM.NEXTVAL`) and appends raw relational rows straight into `PCPRECOPROM`.
- **Advanced Error & Rate Limit Handling:** Features specialized catch blocks for Telegram API `429` statuses (Too Many Requests), gracefully notifying administrators to slow down and sleep-cycling the script to guarantee uptime.

### 🛠️ Technologies Used

- **Python 3**
- **pyTelegramBotAPI (Telebot)** (Telegram communication layer)
- **SQLAlchemy & Pandas** (Database abstraction engine and DataFrame-to-SQL injection)
- **Oracle SQL / PL-SQL** (Transactional backend storage)
- **Re (Regular Expressions)** (Text manipulation and data scraping)

### 📋 Setup & Environment Variables

1. Install required libraries:
   ```bash
   pip install pyTelegramBotAPI pandas sqlalchemy cx_oracle

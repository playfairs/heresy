## heresy is a Multifunctional Discord Bot created and owned by @playfairs, the bot was originally made because I was bored, but I later revamped and modified the bots src and redid the whole thing, the bot was simple and local, I chose to redo the bot and make it a lot better, or tried


# Requirements

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Database Setup

## PostgreSQL Configuration (MacOS)

1. Install PostgreSQL:
   ```bash
   brew install postgresql
   ```

2. Start PostgreSQL service:
   ```bash
   brew services start postgresql
   ```

3. Create the database:
   ```bash
   createdb hersey_bot
   ```

4. Install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install sqlalchemy psycopg2-binary python-dotenv
   ```

5. Configure `.env` file with your database URL:
   ```
   DATABASE_URL=postgresql://localhost/hersey_bot
   ```

## Running the Bot

Activate the virtual environment before running:
```bash
source venv/bin/activate
python3 main.py
```

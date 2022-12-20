## Costs collector from adnets Adsterra & Propellerads to Binom tracker using API

The program is designed to download daily data from advertising networks using a cron schedule task for yesterday and pushing this data to the tracker.

### Files description

```
.
├── config.py
├── costbin.log
├── costbin_note.ipynb
├── costbin.py
├── db
│   ├── binom.db
│   └── schema.sql
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

[costbin.py](./costbin.py) - Main program file.

[config.py](./config.py) - Basic configuration. Credentials takes from environment vars.

costbin.log - Log file with all program general events. It creates automatically when program runs.

[requirements.txt](./requirements.txt) - List of packages for Python3 environment.

[schema.sql](./schema.sql) - SQL dump of table schema. One table used at the moment.

binom.db - Sqlite DB file with one table. It creates automatically from schema.sql if not exists when program runs. 

[Dockerfile](./Dockerfile) - For deployment with Docker Python image.

[docker-compose.yml](./docker-compose.yml) - Composer file for deployment with Docker.






# Costs collector from adnets Adsterra & Propellerads to Binom tracker using API

The program is designed to download daily data from advertising networks using a cron schedule task for yesterday and pushing this data to the tracker.

## Files description


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

*costbin.log* - Log file with all program general events. It creates automatically when the program runs.

[costbin_note.ipynb](./costbin_note.ipynb) - Jupyter Notebook explaining the main parts of the program.

[requirements.txt](./requirements.txt) - List of packages for Python3 environment.

[schema.sql](./db/schema.sql) - SQL dump of table schema. One table used at the moment.

*binom.db* - Sqlite DB file with one table. It creates automatically from schema.sql if it doesn't exist when the program runs. 

**Table head with data sample:**

```
id          date        source      binom_id    date_s      date_e      timezone    token_val   cost      
----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------
1           2022-01-02  Adsterra    111111      2022-01-01  2022-01-01  0           77777777    2.0       
2           2022-01-02  Adsterra    222222      2022-01-01  2022-01-01  0           66666666    1.0       
3           2022-01-02  Adsterra    222222      2022-01-01  2022-01-01  0           55555555    2.0       
...         .... .. ..  ........    ......      .... .. ..  .... .. ..  .           .......     ...       
14          2022-01-02  Propellera  111         2022-01-01  2022-01-01  -5          3333333     0.001     
15          2022-01-02  Propellera  111         2022-01-01  2022-01-01  -5          4444444     0.002

```

[Dockerfile](./Dockerfile) - For deployment with Docker Python image. By default it sets 3 cron schedule tasks.

**Default cron table set list:**

```
# crontab -l
0 11 * * * /usr/local/bin/python3 /var/app/costbin.py --adsterra
5 11 * * * /usr/local/bin/python3 /var/app/costbin.py --propellerads
0 12 * * * /usr/local/bin/python3 /var/app/costbin.py --binom

```

[docker-compose.yml](./docker-compose.yml) - Composer file for deployment with Docker. Sets current app host directory as container work directory.


## Features


- Used independent workers for different tasks to get or push data.
- Handles connection and http exceptions and in case of that try to reconnect up to 10 times with 6s delay.
- Collects transitional data into a database to prevent it from being lost in-between transactions.
- Can be used for multiple data pulls per day without duplicates. All new entries checks in the database if they already exists before being added, and if so, they are skipping.
- Keeps general events in a log file at different levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.


## Usage


1) Retrieve **yesterdays** data from Adsterra (options: --adsterra, -a):

```sh
    $ python3 costbin.py --adsterra
```

2) Retrieve **yesterdays** data from Propellerads (options: --propellerads, -p):

```sh
    $ python3 costbin.py --propellerads
```

3) Push data that was **collected today** to the Binom tracker (options: --binom, -b):

```sh
    $ python3 costbin.py --binom
```

4) Display totals collected on date from db:

```sh
    $ sqlite3 -header -column db/binom.db \
    "SELECT date,source,binom_id,SUM(cost),COUNT(id) FROM binom WHERE date='2022-01-02' GROUP BY binom_id;"
    date        source        binom_id    SUM(cost)   COUNT(id) 
    ----------  ------------  ----------  ----------  ----------
    2022-01-02  Propellerads  111         37.851      724       
    2022-01-02  Propellerads  222         27.097      688       
    2022-01-02  Adsterra      777777      2.0         1         
    2022-01-02  Adsterra      666666      102.0       12        

```

Where SUM(cost) is the field for total costs of campaigns and COUNT(id) is the column for total number of entries grouped by id in the Binom tracker.



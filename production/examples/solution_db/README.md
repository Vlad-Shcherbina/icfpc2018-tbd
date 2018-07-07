This is the example how a solution DB could be organized.

Consider a simplified version of the 2010 task (http://www2010.icfpcontest.org/2010/task/).
We need to scrape cars from their server, generate fuels for these cars, and submit them.

For each of these steps there is a table and a script.

`car_scraper.py` downloads the cars from their server and records them as rows in `cars` table.

`solver_worker.py` takes the cars and attempts to generate fuels for them.
These attempts are recorded in `fuels` table.
In principle there could be multiple instances of this script, if we have different solvers.

`submitter.py` takes promising fuels not yet submitted and attempts to submit them.
These attempts together with the server responses are recorded in `fuel_submissions` table.

There is an additional `invocations` table to help troubleshooting. Invocation is an act of starting a specific version of a specific script by a specific user. Each row in each table is associated with an invocation that produced it.

This whole structure could be examined using `production.dashboard` app.

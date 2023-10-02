# Task Scheduler Script
## Sends out daily reports on subscriptions

## Usage
> In your terminal, run the following commands:

``` bash
docker buildx build -t report_scheduler .
```
followed by:

``` bash
docker run -d -v $(pwd):/usr/src/app --name report_scheduler report_scheduler:latest
```

> The above commands will setup and run a container with the script in it

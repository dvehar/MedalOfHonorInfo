# MedalOfHonorInfo
MedalOfHonorInfo Alexa Skill And BE AWS Services

On the BE I setup a chain of lambdas which will scrape Medal of Honor reciepient information and feed them into DynamoDB.
The steps are:
1) Check how many pages there are on the site and emit events onto AWS SNS for each page.
2) Lambdas are triggered for each page. The lambdas will scrape the recipient URLs and will emit events onto AWS SNS for each recipient found on the page.
3) Lambdas are triggered for each recipient. The lambdas scrape the recipient information and feed it into DynamoDB.

TODOs:
- Temove hardcoded ARNs and use environment variables
- Get rid of the thundering heard problem when scraping by scraping pages in batches or switching to a site that can handle ~3k rps. This problem is partially mitigated by retries.

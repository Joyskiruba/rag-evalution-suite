# API Rate Limits and Quotas

## Default Tier Limits
Free-tier API keys are limited to 60 requests per minute and 10,000 requests per day. Exceeding either limit returns an HTTP 429 response with a Retry-After header.

## Pro Tier Limits
Pro-tier API keys are limited to 600 requests per minute and 1,000,000 requests per day. Pro-tier customers can request a temporary burst limit increase for planned traffic spikes by contacting support 48 hours in advance.

## Enterprise Tier Limits
Enterprise customers negotiate custom rate limits directly with their account manager; there is no fixed default ceiling published for this tier.

## Webhook Retry Policy
Failed webhook deliveries are retried up to 5 times with exponential backoff, starting at 30 seconds and doubling each time, before being marked as permanently failed.

## Deprecation Notice Period
Breaking changes to any public API endpoint require a minimum 90-day deprecation notice posted to the developer changelog before the change takes effect.

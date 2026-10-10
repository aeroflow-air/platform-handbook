# LinkedIn: Running the whole airport locally, for £0

| | |
|---|---|
| **Title** | Running the whole airport locally, for £0 |
| **Date** | 10 Oct 2026 |
| **Status** | draft, not yet published |
| **Related** | [ADR-0013](../decisions/0013-central-event-bus.md), [ADR-0014](../decisions/0014-aspire-local-development.md), [aeroflow-local](https://github.com/aeroflow-air/aeroflow-local), [blog post PR (site-customer #20)](https://github.com/aeroflow-air/site-customer/pull/20) |

**LinkedIn post:** <!-- TODO: replace with the LinkedIn post URL once published -->

---

Today I ran a whole airport on my laptop, from one command, for £0.

AeroFlow Air is my fictional airline platform, built in public to show Azure-native platform engineering in .NET. A .NET Aspire AppHost now starts the Service Bus emulator, Keycloak for identity, two real services and six placeholders with dotnet run. No Azure bill, because the event bus only runs on the emulator locally.

It wasn't smooth. The first Linux run took five attempts: Aspire wanting HTTPS, placeholders fighting over port 5000, services clashing with Keycloak on 8080, and an iptables rule blocking the emulator from SQL. At home on Windows, a leftover DOCKER_HOST setting made every container "Runtime unhealthy". All of it is now in the README.

Then a flight simulator: about two minutes after start, 45 flight events had reached all six placeholders, and one trace follows an event to every service.

Next: real services reacting to events, and services declaring what they need so the platform builds the infrastructure.

What was the snag that cost you an evening on local setup?

The full write-up: https://aeroflow-air.github.io/site-customer/engineering/running-the-whole-airport-locally/

#PlatformEngineering #dotnet #DotNetAspire

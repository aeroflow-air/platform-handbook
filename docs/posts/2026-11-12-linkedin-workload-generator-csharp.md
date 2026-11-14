# LinkedIn: The workload generator, now in C#

| | |
|---|---|
| **Title** | The workload generator, now in C# |
| **Date** | 12 Nov 2026 |
| **Status** | draft, not yet published |
| **Related** | [ADR-0021 (draft PR)](https://github.com/aeroflow-air/platform-handbook/pull/117), [ADR-0009](../decisions/0009-workload-manifest.md), [blog post PR (site-customer #23)](https://github.com/aeroflow-air/site-customer/pull/23) |

**LinkedIn post:** <!-- TODO: replace with the LinkedIn post URL once published -->

---

Our services still declare what they need in a short workload.yaml, and the platform still turns that into governed Bicep. I wrote about that earlier.

The generator that does the turning was Python. Our team writes C#, so I wanted them to be able to read and change that generator in the language they already use.

It now also exists as a single-file .NET 10 app, generate.cs, with no project file. You run it with `dotnet run generator/generate.cs`. Golden-file tests require the C# output to match the Python output byte for byte.

Python is still the default in the deploy workflow. Callers can opt in, and we will pick one default once the C# path has stayed green.

The trade-off is honest: runners need the .NET 10 SDK, the first run spends a few seconds restoring and building, and we now have two implementations to keep in step.

The full write-up:
https://aeroflow-air.github.io/site-customer/engineering/workload-generator-in-csharp/

#PlatformEngineering #dotnet #Azure #GitHubActions

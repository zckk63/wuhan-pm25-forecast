\# Development and Environment Delivery



\## Branch flow



Feature branch -> dev -> staging -> main.



Examples of feature branches:

codex/improve-tests, codex/environment-pipelines,

codex/data-version-experiments.



Changes enter protected branches through pull requests.

Dev integrates features; staging verifies the candidate release;

main contains the production configuration.



Branch protection for dev, staging and main requires:

\- A pull request.

\- A successful check-and-build status.

\- An up-to-date source branch.

\- Enforcement without administrator bypass.



Review approvals are not required for this individual project.



\## Pipeline triggers



| Event | CI | Environment delivery |

|---|---|---|

| PR targeting dev/staging/main | Full checks | Skipped |

| Push to dev | Full checks | Skipped |

| Push to staging | Full checks | Staging |

| Push to main | Full checks | Production |

| Manual workflow run | Full checks | Skipped |



CI installs dependencies, runs Ruff, restores required application

datasets and the model from Azure, runs pytest, and builds Docker.



The environment delivery job depends on successful CI.



\## Environment configuration



GitHub environments: staging and production.



Each environment contains:

\- APP\_ENV.

\- APP\_TITLE.



Repository-level Secrets:

\- AZURE\_STORAGE\_ACCOUNT.

\- AZURE\_STORAGE\_SAS\_TOKEN.



The workflow generates a temporary UTF-8 .env file from environment

Secrets. Docker receives it through --env-file during verification.

The configuration is not baked into the image or uploaded as an artifact.



The application reads APP\_ENV and APP\_TITLE from process environment

variables. Local defaults apply when they are not set.



\## Image verification and records



Each delivery image is tagged with its branch and full Git commit SHA.



The verification runs Streamlit AppTest inside the built container.

It checks that the page runs without exceptions and displays the

configured title and environment.



A delivery-summary.json artifact records:

\- Environment.

\- Git commit SHA.

\- Image tag and image ID.

\- Application verification result.



Artifacts have a configured retention period of 30 days.

Download the delivery record before expiry if needed for grading.



Images are built and verified on the GitHub runner. They are not pushed

to a registry and disappear when the runner is discarded.

There is no persistent cloud-hosted application URL.



This implements the environment-specific build and verification flow

described in the course instructions.



\## Local Docker demonstration



Restore required data and model through DVC, then run:



&#x20;   docker build -t wuhan-pm25-forecast:0.1 .

&#x20;   docker run --rm -p 127.0.0.1:8501:8501 wuhan-pm25-forecast:0.1



Open http://localhost:8501.



Stop the foreground container with Ctrl+C.


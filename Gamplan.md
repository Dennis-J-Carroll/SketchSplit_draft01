\here’s the gist: **SketchSplit can be live in four weeks** if we sequence work into tight, parallel tracks—backend API, basic computer‑vision layer extraction, Replicate‑powered stylization, and a lightweight React/Tailwind front‑end.  We’ll leverage FastAPI + Uvicorn (deployed on Render’s free tier), OpenCV for Canny/threshold passes, Replicate’s hosted ControlNet (≈ \$0.01–0.03/run) for the “AI magic,” and Vercel for the UI.  Guardrails—rate‑limiting (SlowAPI), MIME validation, and secret management—are built in from the outset to avoid re‑work. 

## 1 · Objectives & Success Criteria

### Primary goals

* **MVP upload → multi‑layer sketch → download ZIP** in <15 s for a 1 MB photo.
* <\$20/month infra at <1,000 stylizations (Render + Replicate free‑tier budget).
* Codebase ready to swap Replicate for local ControlNet without breaking the API.

### KPIs

| Metric                      | Target  | Notes                                                                |
| --------------------------- | ------- | -------------------------------------------------------------------- |
| P50 end‑to‑end latency      | ≤ 15 s  | Replicate’s ControlNet predict time averages 8‑12 s ([Replicate][1]) |
| Failure rate (HTTP 5xx)     | < 2 %   | with SlowAPI back‑off                                                |
| First meaningful paint (UI) | < 1.5 s | Vercel edge hosting ([Reddit][2])                                    |

---

## 2 · High‑Level Timeline (4‑Week Sprint Plan)

| Week                            | Deliverables                                        | Key Tasks                                                                                                                                                                                                                                                                  | Owners    |
| ------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| **0 – Kick‑off (½ day)**        | Git repo, CI, `.env` template                       | init GitHub + pre‑commit; add requirements.txt                                                                                                                                                                                                                             | You       |
| **1 – Core API**                | `/stylize` FastAPI endpoint returning Replicate URL | • build `preprocess.py` (Canny + Gaussian per OpenCV docs ([docs.opencv.org][3], [GeeksforGeeks][4])) <br>• MIME/type validation (StackOverflow pattern ([Stack Overflow][5])) <br>• secret loading with python‑dotenv (GitGuardian best‑practice ([GitGuardian Blog][6])) | Backend   |
| **1.5 – Replicate integration** | `replicate_client.py` thin wrapper                  | • hook to ControlNet canny model (cost ≈ \$0.009–0.018/run ([Replicate][1], [Replicate][7])) <br>• parse URL response                                                                                                                                                      | Backend   |
| **2 – Front‑End alpha**         | React/Tailwind drag‑drop uploader                   | • scaffold via Vercel’s v0.dev <br>• fetch progress, show thumbnail <br>• fix PostCSS config so Tailwind classes purge in prod (common Vercel pitfall ([Reddit][2]))                                                                                                       | Frontend  |
| **2.5 – Layer Composer**        | ZIP bundle + preview GIF                            | • merge PNGs with Pillow, encode with imageio/ffmpeg <br>• serve `/download/{id}`                                                                                                                                                                                          | Backend   |
| **3 – Deployment & Hardening**  | Public URL on Render + Vercel                       | • Render blueprint (FastAPI guide ([Render][8])) & env vars <br>• enable SlowAPI rate‑limit (“60/min IP” per docs ([GitHub][9], [slowapi.readthedocs.io][10])) <br>• CORS & HTTPS                                                                                          | DevOps    |
| **3.5 – QA & Analytics**        | Cypress smoke tests; basic logging                  | • write upload/stylize test <br>• log timings to JSONLines                                                                                                                                                                                                                 | QA        |
| **4 – Polishing & Stretch**     | Style picker UX; Paperspace R\&D                    | • add dropdown prompts (“anime”, “charcoal”) <br>• spin up T4 notebook on Paperspace as future local pipe ([Paperspace by DigitalOcean Blog][11])                                                                                                                          | Full team |

---

## 3 · Work‑Package Breakdown

### 3.1 Backend API

* **Framework**: FastAPI + Uvicorn workers (async)
* **Security**:

  * Accept only `image/jpeg`, `image/png`, `image/heic` (validated via `UploadFile.content_type`) ([Stack Overflow][5])
  * 10 MB upload cap; reject else `413`.
  * Rate‑limit with SlowAPI (`@limiter.limit("60/minute")`) ([GitHub][9])
* **Pre‑processing**:

  * Canny parameters 100/200 (doc‑recommended) ([docs.opencv.org][3])
  * Optionally apply 5×5 Gaussian for noisy photos ([docs.opencv.org][3])
* **Stylize call**: POST to Replicate ControlNet; pass prompt + edge\_map file; receive URL.

### 3.2 Front‑End MVP

* **Stack**: React 18, Tailwind CSS, shadcn/ui components.
* **Key Screens**:

  * Home → drag‑drop or click upload.
  * Progress modal (fake progress bar until Replicate returns).
  * Result page → slider to compare original vs. stylized.
* **Deployment**: `vercel --prod`.  Tailwind builds need correct `content` glob to avoid style purge issue noted by community ([Reddit][2]).

### 3.3 DevOps & Secrets

* **Render**: one‑click FastAPI deploy, auto‑build from Git ([Render][8]).
* **Secrets**: `.env` read via python‑dotenv; never commit; rotate in Render/Vercel dashboard ([GitGuardian Blog][6]).
* **Observability**: enable Render logs + simple JSONLines audit per request.

### 3.4 Future GPU Migration Path

* Spin up NVIDIA T4 on Paperspace, install `diffusers`, `torch>=2.1`, and ControlNet weights ([Paperspace by DigitalOcean Blog][11]).
* Maintain same FastAPI contract (`/stylize`)—switch from Replicate client to local inference pipeline for zero‑code front‑end change.

---

## 4 · Risks & Mitigations

| Risk                     | Impact                | Mitigation                                                                          |
| ------------------------ | --------------------- | ----------------------------------------------------------------------------------- |
| Replicate latency spikes | Slower UX             | cache ControlNet weights via Replicate “cold‑start” avoid flag; queue jobs off‑peak |
| Abuse / DoS              | Cost blow‑up          | SlowAPI + Render free‑tier autosuspend; block >5 MB images                          |
| HEIC parsing failures    | User frustration      | fallback convert with `pyheif`; show clear error                                    |
| Tailwind purge bug       | Broken styles on prod | CI runs `npm run build && cypress smoke`; treat missing CSS as fail                 |

---

## 5 · Definition of Done

* All checklist items in Sections 2 & 3 marked complete in GitHub Projects.
* End‑to‑end Cypress test green on main.
* Public demo URL + README with curl example.
* Budget sheet shows < \$20 `/month` at 1 k runs (cost model built from Replicate pricing ([Replicate][1], [Replicate][7])).

---


If this plan looks solid, next step is to open the repo, push the skeleton (backend + requirements), and create **Milestone #1** for Week 1 tasks.  Ping me once you’ve pushed and I’ll auto‑generate your first GitHub issue list!

[1]: https://replicate.com/jagilley/controlnet?utm_source=chatgpt.com "jagilley/controlnet – Run with an API on Replicate"
[2]: https://www.reddit.com/r/tailwindcss/comments/1e67kk4/how_to_deploy_a_tailwind_project_with_vercel/?utm_source=chatgpt.com "How to deploy a tailwind project with vercel? : r/tailwindcss - Reddit"
[3]: https://docs.opencv.org/4.x/d7/de1/tutorial_js_canny.html?utm_source=chatgpt.com "Canny Edge Detection - OpenCV"
[4]: https://www.geeksforgeeks.org/python-opencv-canny-function/?utm_source=chatgpt.com "Python OpenCV – Canny() Function - GeeksforGeeks"
[5]: https://stackoverflow.com/questions/69192379/validate-file-type-and-extention-with-fastapi-uploadfile?utm_source=chatgpt.com "validate file type and extention with fastapi UploadFile - Stack Overflow"
[6]: https://blog.gitguardian.com/how-to-handle-secrets-in-python/?utm_source=chatgpt.com "How to Handle Secrets in Python - GitGuardian Blog"
[7]: https://replicate.com/lucataco/sdxl-controlnet?utm_source=chatgpt.com "lucataco/sdxl-controlnet – Run with an API on Replicate"
[8]: https://render.com/docs/deploy-fastapi?utm_source=chatgpt.com "Deploy a FastAPI App – Render Docs"
[9]: https://github.com/laurentS/slowapi?utm_source=chatgpt.com "laurentS/slowapi: A rate limiter for Starlette and FastAPI - GitHub"
[10]: https://slowapi.readthedocs.io/?utm_source=chatgpt.com "SlowApi Documentation"
[11]: https://blog.paperspace.com/custom-diffusion/?utm_source=chatgpt.com "Custom Diffusion with Paperspace"


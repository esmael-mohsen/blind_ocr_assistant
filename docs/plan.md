# Blind OCR Assistant — Project Plan & Spec Kit Constitution Seed

> **Purpose of this file:**  
> This document is the high-level project plan and governance seed for Spec Kit.  
> Use it as input for `/speckit.constitution` and `/speckit.specify` before generating the technical implementation plan.
>
> **Project Type:** Assistive AI system for blind and visually impaired users.  
> **Core Capability:** Voice-controlled OCR + full-text reading + Arabic/English translation on Raspberry Pi 4 using a free online-first / offline-fallback architecture.

---

## 1. Project Overview

### 1.1 Project Name

**Blind OCR Assistant**

Suggested repository name:

```text
blind-ocr-assistant
```

Suggested Spec Kit feature name:

```text
001-assistive-ocr-reading
```

---

### 1.2 Product Vision

Build a reliable, voice-first assistive reading system for blind and visually impaired users.  
The system captures text from the real world using an Orbbec Astra Pro camera, extracts Arabic and English text using a free online-first OCR pipeline, reads the full text aloud, and translates between Arabic and English on demand.

The system must prioritize:

- Accuracy over raw speed.
- Accessibility over visual UI complexity.
- Free tools and APIs over paid services.
- Online primary behavior with offline fallback.
- Clear voice guidance before, during, and after OCR.
- Robustness on Raspberry Pi 4 Model B with 4GB RAM.

---

### 1.3 Problem Statement

Blind users need a practical way to read printed Arabic and English text from documents, books, labels, medicine packages, receipts, signs, and similar real-world sources.

A simple OCR function is not enough because the user cannot visually verify:

- Whether the document is inside the camera frame.
- Whether the image is blurry.
- Whether lighting is poor.
- Whether the text is too close or too far.
- Whether OCR failed or partially succeeded.
- Whether the detected text needs translation.

Therefore, the system must behave as an **assistive reading workflow**, not just an OCR API wrapper.

---

### 1.4 Target Users

Primary users:

- Blind users.
- Visually impaired users.
- Users who need hands-free Arabic/English reading assistance.

Secondary users:

- Developers testing assistive AI prototypes.
- Academic evaluators reviewing a Raspberry Pi assistive technology project.
- Caregivers or supervisors helping configure the device.

---

## 2. Scope

### 2.1 In Scope

The initial system must support:

1. Voice command activation.
2. Arabic and English command handling.
3. Orbbec Astra Pro RGB image capture.
4. Orbbec Astra Pro depth-based guidance where available.
5. Image quality checking before OCR.
6. Best-frame selection from multiple frames.
7. Image preprocessing using OpenCV.
8. Free online OCR primary using OCR.space Free API.
9. Local OCR fallback using PaddleOCR.
10. Emergency OCR fallback using Tesseract with Arabic and English language data.
11. OCR result quality checking.
12. Arabic/English text cleanup.
13. Arabic RTL handling.
14. Language detection.
15. Full-text reading through TTS.
16. Arabic ↔ English translation on demand.
17. Free online translation primary using LibreTranslate when available.
18. Offline translation fallback using Argos Translate.
19. Online STT primary for voice commands.
20. Offline Vosk fallback for fixed voice commands.
21. Logging of OCR attempts, selected engine, raw text, clean text, and failure reasons.
22. Benchmarking across real-world image samples.

---

### 2.2 Out of Scope for Initial Version

The initial version must not include:

- Paid OCR services such as Google Vision, Azure AI Vision, or AWS Textract.
- Phone screen OCR as a primary target.
- Handwriting OCR as a guaranteed supported feature.
- Complex mobile application UI.
- Cloud storage of user images or text by default.
- User accounts or authentication.
- Model training.
- Custom OCR model fine-tuning.
- Multi-user synchronization.
- Continuous video OCR on every frame.
- Full natural language conversation beyond fixed assistant commands.

---

### 2.3 Explicit Non-Goals

The project must not attempt to:

- Replace professional screen readers.
- Guarantee perfect OCR on all real-world images.
- Depend on paid APIs.
- Hide OCR uncertainty from the user.
- Read sensitive content silently without explicit command.
- Upload images unnecessarily when local fallback is enough or when online primary is unavailable.

---

## 3. System Constraints

### 3.1 Hardware Constraints

Target hardware:

```text
Raspberry Pi 4 Model B
RAM: 4GB total, approximately 3.76 GiB visible
Camera: Orbbec Astra Pro
Swap: 2GB available
```

The system must be optimized for:

- Limited CPU.
- Limited RAM.
- Occasional thermal limits.
- Possible camera bandwidth limitations.
- Power stability constraints.
- Long-running operation.

---

### 3.2 Software Constraints

Preferred language:

```text
Python 3.10+
```

Expected runtime environment:

```text
Linux on Raspberry Pi
```

Core dependencies:

- OpenCV
- NumPy
- requests/httpx
- OCR.space API client
- PaddleOCR
- Tesseract OCR
- pytesseract or subprocess-based Tesseract wrapper
- Vosk
- eSpeak NG initially
- Piper TTS later if suitable
- LibreTranslate client
- Argos Translate fallback
- Optional FastAPI only if a local API service is needed

---

### 3.3 Cost Constraints

The project must use **free-only** OCR and translation services.

Allowed:

- OCR.space Free API.
- PaddleOCR local.
- Tesseract local.
- LibreTranslate free/self-hosted.
- Argos Translate local.
- Vosk local.
- Open-source TTS.

Not allowed in the initial plan:

- Google Cloud Vision paid usage.
- Azure AI Vision paid usage.
- AWS Textract paid usage.
- Paid STT/TTS/OCR plans.
- Any billing-dependent API as a required component.

---

## 4. Core Product Principles

These principles should become the foundation of the project constitution.

---

### Principle 1 — Accessibility First

Every feature must be usable by a blind user without needing visual confirmation.

Implications:

- Voice feedback must be available for every important state.
- The system must explain what it is doing.
- Errors must be spoken clearly.
- The system must guide image capture before OCR.
- No essential workflow may depend on reading a screen.

---

### Principle 2 — Accuracy Before Speed

OCR accuracy is more important than response time.

Implications:

- The system must not OCR a bad image immediately.
- It should guide the user to improve the capture.
- It should select the best frame from multiple frames.
- It may retry OCR using a better preprocessing variant.
- It may escalate from OCR.space to PaddleOCR when quality is low.
- High Accuracy Mode should be available when the user asks for it.

---

### Principle 3 — Free Online-First, Offline-Fallback Design

Online services may be used only if they are free and optional.

Implications:

- OCR.space is the free online OCR primary.
- PaddleOCR must remain available as the main offline accuracy fallback.
- Tesseract must remain available as emergency fallback.
- LibreTranslate may be used when available.
- Argos Translate must be available as offline translation fallback.
- The system must continue functioning in degraded mode without internet.

---

### Principle 4 — Graceful Degradation

Failure in one layer must not stop the full workflow unless all alternatives fail.

Implications:

- If OCR.space fails, use PaddleOCR.
- If PaddleOCR fails or is too heavy, use Tesseract.
- If online translation fails, use Argos Translate.
- If online STT fails, use Vosk command grammar.
- If OCR confidence is poor, tell the user and suggest recapture.

---

### Principle 5 — Voice-Guided Capture

The system must improve the image before OCR rather than accepting bad input.

Implications:

- Use brightness checks.
- Use blur detection.
- Use frame stability scoring.
- Use text-area detection when possible.
- Use depth guidance when available.
- Speak actionable instructions such as "move closer", "hold steady", or "increase lighting".

---

### Principle 6 — Privacy by Default

The system must avoid unnecessary storage or transmission.

Implications:

- Do not upload images except to the selected online OCR provider.
- Do not store images permanently unless debug mode is enabled.
- Store logs in a local folder only.
- Allow debug image saving to be disabled.
- Avoid including sensitive text in verbose logs unless explicitly configured.

---

### Principle 7 — Modular Engine Abstraction

OCR, translation, STT, and TTS engines must be swappable through interfaces.

Implications:

- OCR.space, PaddleOCR, and Tesseract must implement a common OCR interface.
- Translation engines must implement a common translation interface.
- STT engines must implement a common command-recognition interface.
- TTS engines must implement a common speaking interface.
- The cascade controller should not depend on engine-specific implementation details.

---

### Principle 8 — Testability and Benchmarking

The system must be measurable and testable.

Implications:

- Maintain a benchmark dataset of sample images.
- Track OCR engine result, duration, and quality score.
- Test Arabic, English, and mixed text.
- Test poor lighting, blur, angle, distance, and small fonts.
- Track memory usage during PaddleOCR fallback.
- Provide manual acceptance tests for assistive workflows.

---

### Principle 9 — Raspberry Pi Resource Awareness

Every component must respect Raspberry Pi limits.

Implications:

- Do not run all OCR engines in parallel by default.
- Use cascade execution.
- Lazy-load heavy engines such as PaddleOCR.
- Release camera resources properly.
- Avoid continuous OCR on every frame.
- Use bounded queues and timeouts.
- Avoid loading multiple large models unnecessarily.

---

### Principle 10 — Human-Understandable Failures

The system must never fail silently.

Implications:

- If no text is found, say so.
- If the image is bad, say how to improve it.
- If OCR failed online, say that local reading will be tried.
- If translation failed, say that fallback translation will be attempted.
- If all engines fail, ask the user to recapture.

---

## 5. Functional Requirements

### 5.1 Voice Command Requirements

The system must recognize at minimum:

Arabic commands:

```text
اقرأ النص
اقرأ بأعلى دقة
ترجم للعربي
ترجم للإنجليزي
كرر
توقف
كمل
أعد المحاولة
اقرأ ببطء
اقرأ بسرعة
عيد آخر جملة
عيد آخر فقرة
```

English commands:

```text
Read text
High accuracy
Translate to Arabic
Translate to English
Repeat
Stop
Continue
Try again
Read slowly
Read faster
Repeat last sentence
Repeat last paragraph
```

---

### 5.2 Capture Requirements

The system must:

- Start camera capture only after a read command.
- Capture multiple frames instead of one random frame.
- Score each frame.
- Select the best frame.
- Use depth data where available for distance guidance.
- Avoid OCR when the image quality is clearly poor.

---

### 5.3 OCR Requirements

The system must:

- Use OCR.space Free API as the online primary OCR engine.
- Use PaddleOCR as the primary local accuracy fallback.
- Use Tesseract `ara+eng` as emergency fallback.
- Use cascade execution by default.
- Use High Accuracy Mode when requested.
- Evaluate OCR quality before accepting the result.
- Preserve both raw and cleaned OCR text.

---

### 5.4 Text Processing Requirements

The system must:

- Clean OCR output.
- Fix unnecessary spaces and line breaks.
- Handle Arabic right-to-left text.
- Detect Arabic, English, and mixed text.
- Preserve raw text for debugging.
- Prepare clean text for TTS and translation.

---

### 5.5 Translation Requirements

The system must:

- Translate Arabic to English.
- Translate English to Arabic.
- Translate the latest clean OCR text on demand.
- Use LibreTranslate as free online/self-hosted primary when available.
- Use Argos Translate as offline fallback.
- Speak translated text after translation.

---

### 5.6 TTS Requirements

The system must:

- Read the full detected text aloud.
- Support pause, continue, repeat, slower, and faster commands.
- Start with eSpeak NG for initial implementation.
- Allow later upgrade to Piper TTS.

---

### 5.7 Logging Requirements

The system must record:

- Timestamp.
- Capture status.
- Selected OCR engine.
- OCR duration.
- OCR quality score.
- Whether fallback was used.
- Error reason if any.
- Optional raw text and clean text.
- Optional debug image paths when enabled.

---

## 6. Non-Functional Requirements

### 6.1 Accessibility

- All core actions must have spoken feedback.
- The user must not need a visual interface.
- The system must use short, actionable voice instructions.
- Arabic and English voice prompts must be supported.

---

### 6.2 Reliability

- Online failure must trigger offline fallback.
- OCR failure must trigger recapture guidance.
- Engine exceptions must not crash the assistant.
- The assistant must return to a listening state after each workflow.

---

### 6.3 Performance

Accuracy is the priority, but the system should still:

- Avoid unnecessary engine calls.
- Avoid running all OCR engines by default.
- Lazy-load heavy OCR models.
- Limit capture frames to a configurable count.
- Use compressed/resized images for online OCR where appropriate.
- Avoid blocking the assistant indefinitely.

---

### 6.4 Maintainability

- Use modular packages.
- Keep engine-specific code isolated.
- Keep configuration centralized.
- Use typed interfaces where practical.
- Keep command handling separate from OCR logic.
- Keep camera logic separate from OCR logic.

---

### 6.5 Observability

- Provide structured logs.
- Record fallback events.
- Record OCR quality decisions.
- Provide benchmark scripts.
- Provide a quickstart demo mode.

---

## 7. High-Level Workflow

### 7.1 Normal Reading Workflow

```text
User says: "اقرأ النص"
        ↓
Assistant confirms the command
        ↓
Camera opens
        ↓
System checks image quality
        ↓
System guides user if needed
        ↓
System captures multiple frames
        ↓
System selects best frame
        ↓
System preprocesses image
        ↓
System sends image to OCR.space
        ↓
System checks OCR result quality
        ↓
If good: clean text and read
        ↓
If weak: run PaddleOCR
        ↓
If weak/fail: run Tesseract
        ↓
Clean text
        ↓
Read full text aloud
```

---

### 7.2 Translation Workflow

```text
User says: "ترجم للإنجليزي"
        ↓
System uses latest clean OCR text
        ↓
System detects source language
        ↓
System calls LibreTranslate if available
        ↓
If unavailable, system uses Argos Translate
        ↓
System reads translated text aloud
```

---

### 7.3 Offline Workflow

```text
No internet detected
        ↓
Assistant says: "الإنترنت غير متاح، سأستخدم القراءة المحلية"
        ↓
PaddleOCR is used
        ↓
If PaddleOCR fails, Tesseract is used
        ↓
Clean text
        ↓
Read full text
```

---

### 7.4 High Accuracy Workflow

```text
User says: "اقرأ بأعلى دقة"
        ↓
Capture best frame
        ↓
Run OCR.space if online
        ↓
Run PaddleOCR
        ↓
Compare result quality
        ↓
Select best text
        ↓
Clean and read full text
```

---

## 8. Success Criteria

The project is successful when:

1. A blind user can trigger OCR by voice.
2. The system gives spoken guidance before capture.
3. The system can read Arabic printed text.
4. The system can read English printed text.
5. The system can read mixed Arabic/English text with acceptable quality.
6. The system can fall back from OCR.space to PaddleOCR.
7. The system can fall back from PaddleOCR to Tesseract.
8. The system can translate Arabic ↔ English on demand.
9. The system can function without paid services.
10. The system can function in offline degraded mode.
11. The system can run on Raspberry Pi 4 with 4GB RAM.
12. The system logs OCR decisions and failures for later improvement.

---

## 9. Recommended Spec Kit Workflow

Use this document in the following order:

### Step 1 — Initialize Spec Kit

```bash
specify init --here --force --integration copilot
```

Or use your preferred integration.

---

### Step 2 — Create Constitution

Suggested prompt:

```text
/speckit.constitution

Create a project constitution for an assistive OCR reading system for blind users running on Raspberry Pi 4. The constitution must enforce accessibility-first design, accuracy-before-speed decisions, free online-first with offline fallback architecture, graceful degradation, voice-guided capture, privacy by default, modular engine abstraction, testability, Raspberry Pi resource awareness, and human-understandable failures. Use the project plan in plan.md as the governing source of truth.
```

---

### Step 3 — Create Feature Spec

Suggested prompt:

```text
/speckit.specify

Build a voice-first assistive OCR reading system for blind users. It runs on Raspberry Pi 4 Model B with Orbbec Astra Pro camera. The user can say Arabic or English commands to read printed text. The system guides the user by voice, captures multiple frames, selects the best frame, performs OCR using a free online-first cascade with OCR.space primary, PaddleOCR local accuracy fallback, and Tesseract emergency fallback. It cleans Arabic/English text, handles RTL, reads the full text aloud, and translates Arabic ↔ English on demand using LibreTranslate primary and Argos Translate fallback. No paid services are allowed.
```

---

### Step 4 — Generate Technical Plan

Use `implementationPlan.md` as the source prompt for `/speckit.plan`.

---

### Step 5 — Generate Tasks

```text
/speckit.tasks
```

---

### Step 6 — Implement

```text
/speckit.implement
```

---

## 10. Final Decision Summary

The project will use:

```text
Camera:
Orbbec Astra Pro RGB + Depth

Image Processing:
OpenCV quality check
OpenCV best-frame selection
OpenCV preprocessing

OCR:
OCR.space Free API primary
PaddleOCR accuracy fallback
Tesseract ara+eng emergency fallback

Text:
Arabic/English cleanup
RTL fix
Language detection

Translation:
LibreTranslate online/free or self-hosted primary
Argos Translate offline fallback

Voice:
Online STT primary
Vosk offline fallback

TTS:
eSpeak NG initially
Piper TTS optional later upgrade

Execution:
Sequential cascade by default
High Accuracy Mode on request
No paid APIs
No model training in initial version

# ADR-015: Speech-to-Text Provider

**Status:** OPEN
**Deciders:** Tech Lead
**Sprint:** 0 (decision can be deferred to Sprint 2 if audio ingestion is not in MVP)
**Date Decided:** —
**Invariants Affected:** INV-SEC-02 (PII scrubbing — transcripts must be scanned for PII before embedding), INV-EPI-06 (visual/audio extraction confidence cap — audio-derived claims capped at 0.80)

---

## Context

Chitragupt accepts audio and video files as source documents — meeting recordings, stakeholder interviews, screen recordings with narration. These files are transcribed to text before entering the standard ingestion pipeline (chunking → embedding → retrieval).

The transcription step introduces unique considerations:
- Audio files can be large (1-hour meeting = ~50MB MP3)
- Transcription latency can be significant (minutes, not seconds) — must be async
- Speaker diarisation (who said what) affects trust tier assignment
- Transcripts must be PII-scanned before embedding (INV-SEC-02)
- All audio-derived requirements are confidence-capped at 0.80 (INV-EPI-06)

This ADR may be deferred to Sprint 2 if audio ingestion is confirmed as post-MVP. The PM must confirm this during Sprint 0.

## Decision Drivers

- Transcription accuracy on business/technical speech (domain jargon, product names, technical terms)
- Speaker diarisation support (identifying which speaker made which statement)
- Async API with webhook or polling (not synchronous — large files would block)
- Cost per audio minute at expected volume
- Data retention and privacy posture — audio of client meetings is sensitive
- Language support (English primary; multilingual if required)
- File format support (MP3, MP4, WAV, M4A, WebM)

## Considered Options

| Option | Accuracy | Diarisation | Async | Cost / hour | Privacy | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAI Whisper API** | Very High | ❌ (no diarisation) | ❌ (synchronous) | ~$0.36 | Sent to OpenAI | Simple; no diarisation |
| **AssemblyAI** | Very High | ✅ | ✅ Webhook | ~$0.65 | Configurable | Best diarisation; async native |
| **Deepgram** | Very High | ✅ | ✅ Webhook | ~$0.59 | Configurable | Fast; real-time and async |
| **Google Speech-to-Text v2** | High | ✅ | ✅ | ~$0.016–$0.048/min | GCP data handling | Broad language support |
| **AWS Transcribe** | High | ✅ | ✅ | ~$0.024/min | AWS data handling | Native if AWS deployment |
| **Self-hosted Whisper** | High | ❌ | ✅ (via queue) | Infra cost only | Full control | High GPU cost; no diarisation |

## Evaluation Matrix

| Criterion | Weight | AssemblyAI | Deepgram | OpenAI Whisper | AWS Transcribe |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Transcription accuracy on business speech | 30% | | | | |
| Speaker diarisation support | 25% | | | | |
| Async API with webhook/callback | 20% | | | | |
| Privacy / zero-retention posture | 15% | | | | |
| Cost per audio-hour | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — First confirm with PM whether audio ingestion is in MVP scope. If deferred, update status to DEFERRED. If in scope, fill in the evaluation matrix.

**Is audio ingestion in MVP scope? (PM to confirm):** Yes / No / Deferred to Sprint 2

**Chosen provider (if in scope):**

**Async mechanism (webhook URL / polling):**

**Maximum file size accepted:**

**Speaker diarisation: enabled / disabled:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**

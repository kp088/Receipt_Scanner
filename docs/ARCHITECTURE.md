# Architecture

This document explains how the Receipt Scanner is put together: the main components, what happens when a receipt is scanned, how the data is stored and where each piece lives in the code.

## System overview

```mermaid
flowchart LR
    user([User])

    subgraph frontend["Frontend: React + Vite"]
        ui["Upload zone<br/>Receipt editor<br/>History and summary"]
        client["api.js<br/>fetch wrapper"]
    end

    subgraph backend["Backend: FastAPI"]
        router["Receipts router<br/>/api/v1/receipts"]
        deps["Extractor factory<br/>dependencies.py"]
        schema["Pydantic schemas<br/>request and reply validation"]
        checks["Totals sanity checks<br/>services/validation.py"]
        orm["SQLAlchemy models"]
    end

    subgraph extractors["Extractors: one interface, three providers"]
        gemini["GeminiExtractor"]
        openai["OpenAIExtractor"]
        mock["MockExtractor<br/>no key, used in tests"]
    end

    subgraph storage["Storage"]
        db[("SQLite<br/>receipts, line_items")]
        files[/"uploads folder<br/>original images"/]
    end

    geminiapi{{"Google Gemini API"}}
    openaiapi{{"OpenAI API"}}

    user --> ui --> client
    client -- "HTTP / JSON" --> router
    router --> deps
    deps --> gemini & openai & mock
    gemini --> geminiapi
    openai --> openaiapi
    router --> schema --> checks
    router --> orm --> db
    router --> files
```

## What happens when a receipt is scanned

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI router
    participant EX as Extractor
    participant LLM as Vision model
    participant DB as SQLite

    User->>UI: Drop a receipt photo
    UI->>API: POST /api/v1/receipts/scan (image)
    API->>API: Check size and real file type
    API->>EX: extract(image)
    EX->>LLM: Prompt + image
    LLM-->>EX: JSON text
    EX->>EX: Parse JSON, validate against schema
    EX-->>API: ReceiptData
    API->>DB: Save receipt, items and image file
    API->>API: Run totals sanity checks
    API-->>UI: Receipt + warnings
    UI-->>User: Editable form next to the image
    User->>UI: Fix a wrong value, Save
    UI->>API: PUT /api/v1/receipts/{id}
    API->>DB: Update
    API-->>UI: Updated receipt, warnings re-checked
```

## Data model

```mermaid
erDiagram
    RECEIPT ||--o{ LINE_ITEM : contains

    RECEIPT {
        int id PK
        string merchant
        date purchase_date
        string currency
        float subtotal
        float tax
        float total
        string payment_method
        string category
        string image_filename
        bool is_sample
        datetime created_at
    }

    LINE_ITEM {
        int id PK
        int receipt_id FK
        string description
        float quantity
        float unit_price
        float amount
    }
```

## Code map

```
receipt-scanner/
├── app/                        Backend (FastAPI)
│   ├── main.py                 App setup, CORS, serves the built frontend
│   ├── config.py               Settings read from .env
│   ├── database.py             Engine and per-request session
│   ├── models.py               SQLAlchemy tables
│   ├── schemas.py              Pydantic request and response models
│   ├── dependencies.py         Chooses the extractor from settings
│   ├── routers/
│   │   └── receipts.py         All /api/v1/receipts endpoints
│   ├── extractors/
│   │   ├── base.py             Extractor interface and error type
│   │   ├── prompt.py           Shared prompt and reply parsing
│   │   ├── gemini_extractor.py
│   │   ├── openai_extractor.py
│   │   └── mock_extractor.py
│   └── services/
│       ├── validation.py       Totals sanity checks
│       └── samples.py          Sample receipts for a new database
├── frontend/                   Frontend (React + Vite)
│   └── src/
│       ├── App.jsx             Page state and layout
│       ├── api.js              Calls to the backend
│       ├── format.js           Money and date formatting
│       ├── styles.css
│       └── components/         UploadZone, ReceiptEditor, HistoryList, SummaryBar
├── tests/                      PyTest suite (runs in mock mode, no network)
├── Dockerfile                  One image: builds the frontend, serves it from FastAPI
└── .env.example                Settings template
```

## Design decisions

| Decision | Why |
|----------|-----|
| Extractors share one interface | A new AI provider is one new file; the router never changes. |
| Mock extractor | The project runs and the tests pass with no API key and no cost. |
| Model output is never trusted | Every reply is parsed and validated with Pydantic, then the totals are cross-checked. Problems become warnings for a person to review, not silent bad data. |
| File type detected from the bytes | The upload's claimed content type can be wrong or forged. |
| Images saved under random names | User-supplied filenames never reach the disk. |
| Database URL comes from settings | SQLite locally; PostgreSQL in production with no code change. |
| Samples are added only when the database is created | A first-time visitor sees a working dashboard, and samples stay gone once deleted. |
| FastAPI serves the built frontend | Deployment is a single Docker image. |

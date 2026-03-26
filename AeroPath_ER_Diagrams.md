# AeroPath AI: Logical Data Model & ER Diagrams

This document outlines the entity-relationship structure and logical flow of the AeroPath AI smart city platform.

## 1. Entity Relationship (ER) Diagram

The following diagram represents the core logical entities in the system. Note that while **Users** are managed via Firebase Auth, the logical relationships between telemetry, junctions, and ambulances define the system's operational flow.

```mermaid
erDiagram
    USER ||--o{ ROUTE : requests
    USER {
        string uid PK
        string email
        string fullName
        string role "private_user | ambulance_driver"
        string registrationNum "optional"
    }

    JUNCTION ||--o{ TELEMETRY : generates
    JUNCTION {
        string id PK
        string name
        float latitude
        float longitude
        string currentState "NORMAL | GREEN_WAVE"
        int congestionLevel "1 to 5"
    }

    TELEMETRY {
        timestamp time PK
        string junctionId FK
        int vehicleCount
        float avgSpeed
        string weather "Clear | Rain | Fog"
    }

    AMBULANCE ||--o| USER : "belongs to"
    AMBULANCE ||--o{ GPS_TRACK : "broadcasts"
    AMBULANCE {
        string id PK
        string plateNumber
        boolean isActive
    }

    GPS_TRACK {
        timestamp time PK
        string ambulanceId FK
        float latitude
        float longitude
    }

    ROUTE {
        string id PK
        string userId FK
        string startPoint
        string endPoint
        float distanceKM
        float estTimeMinutes
    }
```

---

## 2. System Architecture / Flow Diagram

This diagram explains the step-by-step technological handoff between the IoT simulation, the ML engine, and the EVP Green Wave logic.

```mermaid
graph TD
    A[IoT Junciton Simulator] -->|Raw Count/Speed| B(Backend Data Ingestor)
    C[Open-Meteo Weather API] -->|Temp/Conditions| B
    
    B --> D{Intelligence Engine}
    
    subgraph "The Intelligence Engine"
        D -->|Feature Vector| E[RandomForest ML Model]
        E -->|Predicted Congestion| F[State Manager]
        
        G[Ambulance GPS Stream] -->|Proximity Check| H[EVP Algorithm]
        H -->|Geofence Trigger| F
    end
    
    F -->|Live State API| I[Frontend Dashboard]
    J[Leaflet Map Layer] --- I
    K[OSRM Routing] --- I
    
    L[Firebase Auth] -->|JWT Verification| B
```

---

## 3. Data Dictionary

### 3.1. Junctions (In-Memory / State)
The primary data structure is a JSON object mapping junction IDs to real-time status.
- **`junction_states`**: Stores predicted congestion, current active signal (Green/Red), and if a "Green Wave" is currently overriding the manual ML prediction.

### 3.2. Firebase Authentication (Identity)
The system uses Firebase as a decoupled identity provider.
- **Private Users**: Metadata contains standard profile info.
- **Ambulance Drivers**: Metadata contains custom claims `role: 'ambulance'` allowing the backend to accept GPS broadcasts from their UID.

### 3.3. ML Training Data
Synthetic dataset stored in `traffic_data.csv` (7200 rows) with the following features:
- `hour`: 0-23
- `is_rush_hour`: binary (0/1)
- `is_weekend`: binary (0/1)
- `weather_condition`: encoded (0=Clear, 1=Rain, etc.)
- `congestion_level`: target class (1 to 5)

# AI Gold Scalper System Wiki

## Overview
The AI Gold Scalper system is a sophisticated trading platform that leverages machine learning and advanced analytics to optimize trading decisions for XAUUSD. It integrates multiple components, each with specific roles and responsibilities.

## Core Components

### 1. Enhanced System Orchestrator
- **Role**: Manages system initialization, component startup, shutdown, and monitoring.
- **Components**:
  - ai_server
  - model_registry
  - enhanced_trade_logger
- **Features**:
  - Interactive setup
  - Custom component selection
  - Deployment type handling

### 2. AI Server
- **Role**: Provides AI-driven trading signals using pre-trained models.
- **Features**:
  - Consolidates signals from ML models, technical analysis, and GPT-4.
  - Uses caching for performance optimization.

### 3. Model Registry
- **Role**: Manages the lifecycle of machine learning models.
- **Features**:
  - Version control
  - Performance tracking

## Additional Components

### Adaptive Learning System
- **Role**: Continuously learns from trading results to improve model performance.
- **Features**:
  - Retrains models based on new data.
  - Provides real-time updates to model configurations.

### Performance Dashboard
- **Role**: Visualizes system performance metrics.
- **Features**:
  - Displays trading performance and system health.

## Key Interactions
- **Model Training**: Automated processes retrain models utilizing adaptive learning and performance monitoring.
- **Data Processing**: Ingests market data for feature extraction and model prediction.
- **Signal Generation**: Generates trading signals combining technical and machine learning insights.

## Why These Components Exist
- **Efficiency**: Optimizes trading decisions by employing ensemble learning and adaptive strategies.
- **Flexibility**: Provides the ability to select which components to run based on deployment needs.
- **Scalability**: Supports both local development and VPS production configurations.

## Deprecated Components
- **Old VPS Components**: Consolidated into the primary AI server, removing redundancy and improving maintainability.
- **Obsolete Documentation**: Historical documents have been deprecated to focus on current, relevant information.

## Future Directions
- Streamline the integration of new models and analytics.
- Expand adaptive learning to include new algorithms and data sources.
- Enhance the user interface for more intuitive interaction.

This comprehensive directory serves as your starting point for exploring the various facets of the AI Gold Scalper system.

# Weather Comment Generation System ☀️

An automated weather comment generation system using LangGraph and LLM. Based on weather information and historical comment data for specified regions, this system leverages Large Language Models (LLM) to automatically generate short weather comments (approximately 15 characters).

## 🆕 Latest Updates (2025-06-15)

- **Major LLM Selection Improvements**: Fixed argument inconsistencies in LLM comment selection
- **Timezone Issue Resolution**: Resolved datetime mixing errors in time-series data retrieval
- **Forecast Data Optimization**: Efficient weather change tracking at 3-6 hour intervals
- **Prompt Optimization**: Improved LLM to reliably return numerical values only
- **System Enhancements**: Strengthened error handling and performance improvements

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## 📗 Project Structure

```
MobileCommentGenerator/
├── src/                          # Backend Python Application
│   ├── data/                     # Data Classes & Management
│   │   ├── comment_generation_state.py  # Workflow State Management
│   │   ├── comment_pair.py       # Comment Pair Data Model
│   │   ├── evaluation_criteria.py       # Evaluation Criteria Definition
│   │   ├── forecast_cache.py     # Weather Forecast Cache Management
│   │   ├── location_manager.py   # Location Data Management
│   │   ├── past_comment.py       # Historical Comments Management
│   │   ├── weather_data.py       # Weather Data Model
│   │   ├── weather_trend.py      # Weather Trend Analysis
│   │   └── Chiten.csv            # Location Master Data
│   ├── apis/                     # External API Integration
│   │   └── wxtech_client.py      # WxTech Weather API Integration
│   ├── algorithms/               # Algorithm Implementation
│   │   ├── comment_evaluator.py        # Comment Evaluation Logic
│   │   └── similarity_calculator.py    # Similarity Calculation
│   ├── nodes/                    # LangGraph Nodes
│   │   ├── input_node.py         # Input Node
│   │   ├── weather_forecast_node.py     # Weather Forecast Retrieval Node
│   │   ├── retrieve_past_comments_node.py # Historical Comments Retrieval Node
│   │   ├── select_comment_pair_node.py  # Comment Selection Node
│   │   ├── comment_selector.py   # Comment Selection Logic
│   │   ├── evaluate_candidate_node.py   # Candidate Evaluation Node
│   │   ├── generate_comment_node.py     # Comment Generation Node
│   │   ├── output_node.py        # Output Node
│   │   └── mock_nodes.py         # Mock Nodes (for testing)
│   ├── workflows/                # Workflow Implementation
│   │   └── comment_generation_workflow.py
│   ├── llm/                      # LLM Integration
│   │   ├── llm_client.py         # LLM Client Base
│   │   ├── llm_manager.py        # LLM Manager
│   │   ├── prompt_builder.py     # Prompt Construction
│   │   ├── prompt_templates.py   # Prompt Templates
│   │   └── providers/            # LLM Provider Implementation
│   │       ├── base_provider.py         # Base Provider
│   │       ├── openai_provider.py       # OpenAI Integration
│   │       ├── gemini_provider.py       # Google Gemini Integration
│   │       └── anthropic_provider.py    # Anthropic Claude Integration
│   ├── repositories/             # Data Repository
│   │   └── local_comment_repository.py # Local Data Access
│   ├── utils/                    # Utilities
│   │   ├── common_utils.py       # Common Utilities
│   │   └── weather_comment_validator.py # Weather Comment Validation
│   ├── ui/                       # Streamlit UI
│   │   ├── streamlit_components.py      # UI Components
│   │   ├── streamlit_utils.py    # UI Utilities
│   │   └── pages/                # Multi-page Configuration
│   │       └── statistics.py     # Statistics Information Page
│   └── config/                   # Configuration Management
│       ├── weather_config.py     # Weather Forecast Configuration
│       ├── comment_config.py     # Comment Generation Configuration
│       ├── config_loader.py      # Configuration Loader
│       └── severe_weather_config.py # Severe Weather Configuration
├── frontend/                     # Vue.js/Nuxt.js Frontend (Fully Separated)
│   ├── pages/                    # Page Components
│   │   └── index.vue             # Main Page (Overall Layout & State Management)
│   ├── components/               # UI Components
│   │   ├── LocationSelection.vue    # Location Selection (Regional List & Search)
│   │   ├── GenerateSettings.vue     # Generation Settings (LLM Provider Selection)
│   │   ├── GeneratedComment.vue     # Generation Result Display (Comments & History)
│   │   └── WeatherData.vue          # Weather Data Display (Forecast Info & Details)
│   ├── composables/              # Composition API
│   │   └── useApi.ts             # API Calls (REST Communication & Error Handling)
│   ├── constants/                # Constant Definitions
│   │   ├── locations.ts          # Location Data (National Location List)
│   │   └── regions.ts            # Regional Data (Regional Classification & Display Order)
│   ├── types/                    # TypeScript Type Definitions
│   │   └── index.ts              # API & UI Type Definitions
│   ├── app.vue                   # Application Global Layout
│   ├── nuxt.config.ts            # Nuxt Configuration (UI Module Settings)
│   ├── package.json              # Node.js Dependencies
│   └── start_frontend.sh         # Frontend Startup Script
├── api_server.py                 # FastAPI API Server
├── app.py                        # Streamlit Main Entry Point
├── start_api.sh                  # API Server Startup Script
├── data/                         # Data Files
│   ├── forecast_cache/           # Weather Forecast Cache
│   └── generation_history.json  # Generation History
├── config/                       # Configuration Files (YAML)
│   ├── weather_thresholds.yaml   # Weather Threshold Settings
│   ├── expression_rules.yaml     # Expression Rules
│   ├── ng_words.yaml             # NG Words
│   └── llm_config.yaml           # LLM Configuration
├── output/                       # Generated CSV Files & Analysis Results
├── tests/                        # Test Suite
│   ├── integration/              # Integration Tests
│   └── test_*.py                 # Various Unit Tests
├── docs/                         # Documentation
├── scripts/                      # Utility Scripts
├── examples/                     # Sample Code
├── pyproject.toml                # Project Settings & Dependencies
├── uv.lock                       # uv Lock File
├── requirements.txt              # Traditional Dependencies File
├── pytest.ini                    # pytest Configuration
├── mypy.ini                      # mypy Configuration
├── Makefile                      # Build & Execution Scripts
├── setup.sh                     # Setup Script
└── README.md                     # This File
```

## 🎯 Key Features

- **LangGraph Workflow**: Systematic implementation of state and error handling logic
- **Multi-LLM Providers**: OpenAI/Gemini/Anthropic support  
- **Adaptability-Based Selection**: LLM selection of optimal pairs from historical comments based on adaptability
- **Expression Rule Application**: Automatic checking of NG words and character limits
- **12-Hour Weather Forecast**: Uses 12-hour ahead data by default
- **Dual UI Implementation**: Streamlit (development) + Vue.js/Nuxt.js (production)
- **FastAPI Integration**: RESTful API for frontend-backend separation
- **Weather Forecast Caching**: Efficient weather data management and caching functionality

## 📊 Current Progress Status

### ✅ Phase 1: Foundation System (100% Completed)
- [x] **Location Data Management System**: CSV reading validation & location info retrieval functionality
- [x] **Weather Forecast Integration**: WxTech API integration (12-hour ahead data support)
- [x] **Historical Comment Retrieval**: enhanced50.csv-based data analysis & similarity selection validation
- [x] **LLM Integration**: Multi-provider support (OpenAI/Gemini/Anthropic)

### ✅ Phase 2: LangGraph Workflow (100% Completed)
- [x] **SelectCommentPairNode**: Comment similarity-based selection
- [x] **EvaluateCandidateNode**: Multi-criteria evaluation
- [x] **Basic Workflow**: Sequential implementation with implemented nodes
- [x] **InputNode/OutputNode**: Complete implementation
- [x] **GenerateCommentNode**: LLM integration implementation
- [x] **Integration Testing**: End-to-end test implementation
- [x] **Workflow Visualization**: Implementation trace tools

### ✅ Phase 3: Streamlit UI (100% Completed)
- [x] **Basic UI Implementation**: Location selection, LLM provider selection, comment generation
- [x] **Detailed Information Display**: Weather info, historical comments, evaluation result details
- [x] **Batch Processing**: Multi-location batch processing functionality
- [x] **CSV Export**: Generation result export functionality
- [x] **Error Handling**: User-friendly error display

### ✅ Phase 4: Frontend Separation (100% Completed)
- [x] **Frontend Separation**: Migration of Vue.js/Nuxt.js to independent project
- [x] **Project Structure Clarification**: Responsibility separation between frontend/ and src/
- [x] **API Implementation**: FastAPI RESTful API endpoints completion
- [x] **Integration Documentation**: Frontend-backend integration guide
- [x] **UI Components**: Complete implementation of location selection, settings, result display

### 🚀 Phase 5: Deployment (0% Completed)
- [ ] **AWS Deployment**: Lambda/ECS & CloudWatch integration

## 📄 Setup

### Environment Requirements
- Python 3.10 or higher
- uv (recommended)
- Node.js 18 or higher (for frontend)

### Quick Start (using uv)

```bash
# 1. Clone repository
git clone https://github.com/sakamo-wni/MobileCommentGenerator.git
cd MobileCommentGenerator

# 2. Install dependencies (uv automatically creates virtual environment)
uv sync

# 3. Environment variable setup
cp .env.example .env
# Configure API keys in .env file

# 4. Start application
# Backend (FastAPI)
uv run ./start_api.sh

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Access URLs:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Alternative Setup Methods

#### Streamlit Version (Development & Debug)

```bash
# When virtual environment is already created
uv run streamlit run app.py
```

#### Other Scripts

```bash
# Using setup script
chmod +x setup.sh
./setup.sh dev

# Using Makefile
make setup
make help
```

## 🔑 API Key Configuration

### Required Settings
Configure LLM provider API keys in `.env` file:

```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Weather forecast data
WXTECH_API_KEY=your_wxtech_api_key_here

# AWS (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## 🌤️ Weather Forecast Time Configuration

The system uses **12-hour ahead weather forecast** by default to generate comments. This setting can be changed via environment variables.

### Environment Variable Settings

Add the following environment variables to your `.env` file:

```bash
# How many hours ahead to use for forecast (default: 12)
WEATHER_FORECAST_HOURS_AHEAD=12
```

### Configuration Examples

```bash
# To use 6-hour ahead forecast
WEATHER_FORECAST_HOURS_AHEAD=6

# To use 24-hour ahead (next day same time) forecast
WEATHER_FORECAST_HOURS_AHEAD=24

# To use 3-hour ahead forecast
WEATHER_FORECAST_HOURS_AHEAD=3
```

### Configuration Verification

The configured time is displayed as "🕐 Forecast Time" in the UI's regional detailed information. The displayed time is automatically converted to Japan Standard Time (JST).

**Note**: This setting ensures weather data for the specified time is used consistently across all components.

## 📄 Frontend Details

### File Structure and Roles

| File | Role | Main Functions |
|------|------|----------------|
| **pages/index.vue** | Main Page | Overall layout, state management, page control |
| **app.vue** | Application Root | Global styles, common layout |
| **components/LocationSelection.vue** | Location Selection Component | Regional location list, search, filtering functionality |
| **components/GenerateSettings.vue** | Settings Component | LLM provider selection, generation option settings |
| **components/GeneratedComment.vue** | Result Display Component | Generated comment display, history, copy functionality |
| **components/WeatherData.vue** | Weather Information Component | Current/forecast weather data, detailed information display |
| **composables/useApi.ts** | API Communication Layer | REST API calls, error handling, loading state |
| **constants/locations.ts** | Location Data | National location coordinates, names, regional classification |
| **constants/regions.ts** | Regional Data | Regional classification display order, category classification |
| **types/index.ts** | Type Definitions | TypeScript types, API specifications, UI state types |

### State Management

```typescript
// Main state in pages/index.vue
const selectedLocation = ref<Location | null>(null)
const generatedComment = ref<GeneratedComment | null>(null)
const isGenerating = ref(false)
const error = ref<string | null>(null)
```

### API Communication

```typescript
// composables/useApi.ts
export const useApi = () => {
  // Get location list
  const getLocations = async (): Promise<Location[]>
  
  // Generate comment
  const generateComment = async (params: GenerateSettings): Promise<GeneratedComment>
  
  // Get generation history
  const getHistory = async (): Promise<GeneratedComment[]>
}
```

### UI Feature Details

#### LocationSelection.vue
- **Regional Filter**: Regional display by Hokkaido, Tohoku, Kanto, etc., search functionality
- **Search Function**: Filtering by location name
- **Favorites**: Save frequently used locations, priority display
- **Responsive**: Mobile and tablet support

#### GenerateSettings.vue
- **LLM Provider Selection**: OpenAI, Gemini, Anthropic
- **API Key Status Display**: Icon display for configured providers
- **Generation Options**: Detailed settings (for future expansion)

#### GeneratedComment.vue
- **Comment Display**: Integrated display of weather comments and advice
- **Copy Function**: One-click copy to clipboard
- **Generation History**: List of past generation results, chronological display
- **Export**: CSV format download functionality

#### WeatherData.vue
- **Current Weather**: Real-time weather information
- **12-Hour Forecast**: Detailed display of default forecast time, temperature trend display
- **Weather Parameters**: Detailed information including wind speed, humidity, precipitation
- **Warning Information**: Severe weather alerts

## 🚀 Usage

### Vue.js Frontend (Recommended)

```bash
uv run ./start_api.sh
```

1. Open http://localhost:3000 in browser
2. Select location and weather from left panel
3. Select LLM provider
4. Click "Generate Comment" button
5. Check generated comments and weather information

### Streamlit UI (Development & Debug)

```bash
uv run streamlit run app.py
```

1. Open http://localhost:8501 in browser
2. Select location and LLM provider from left panel
3. Click "🎯 Generate Comment" button
4. Check generated comments and detailed information

### Programmatic Usage

```python
from src.workflows.comment_generation_workflow import run_comment_generation
from datetime import datetime

# Generate comment for single location
result = run_comment_generation(
    location_name="Tokyo",
    target_datetime=datetime.now(),
    llm_provider="openai"
)

print(f"Generated Comment: {result['final_comment']}")
```

## 🧪 Testing

```bash
# Run all tests
make test

# Test with coverage
make test-cov

# Integration tests
make test-integration

# Quick test (main functions only)
make quick-test
```

## 🔧 Development Tools

### Code Quality

```bash
# Code quality check
make lint                         # Code quality check
make format                       # Code formatting
make type-check                   # Type checking
```

### Configured Tools
- **Black**: Code formatter (100 characters)
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Fast linter
- **pytest**: Test framework

### Other Useful Commands

```bash
# Maintenance
make clean                        # Clean temporary files
uv sync                           # Update dependencies

# Log output
tail -f logs/llm_generation.log    # LLM generation log

# Help
make help
```

## 📊 Project Information

### Technology Stack

**Backend:**
- Python 3.10+
- LangGraph 0.0.35+
- LangChain 0.1.0+
- Streamlit 1.28.0+
- OpenAI/Gemini/Anthropic APIs

**Frontend:**
- Vue.js 3.5+
- Nuxt.js 3.17+
- TypeScript 5.3+
- FastAPI 0.104+

**Data Processing:**
- Pandas 2.1.4+
- NumPy 1.26.2+
- Scikit-learn 1.3.2+

**AWS (Optional):**
- Boto3 1.34.0+
- AWS CLI 1.32.0+

### Metadata
- **Version**: 1.0.0
- **License**: MIT
- **Last Updated**: 2025-06-15
- **Development Team**: WNI Team

## 📝 Update History

- **v1.1.1** (2025-06-15): LLM selection functionality and timezone issue fixes, prompt optimization
- **v1.1.0** (2025-06-15): FastAPI integration, frontend separation completion, PastComment fixes
- **v1.0.0** (2025-06-12): Phase 4 completion - Vue.js/Nuxt.js frontend implementation
- **v0.3.0** (2025-06-06): Phase 2 completion - LangGraph workflow implementation

### 🐛 Bug Fixes (v1.1.1)

**LLM Selection Function Fixes:**
- `comment_selector.py`: Fixed argument inconsistency in LLM API calls
- Improved prompts for reliable numerical selection
- Normal operation of LLM selection in weather/advice integrated comments

**Timezone Issue Fixes:**
- Resolved timezone-aware/naive datetime mixing errors
- Improved stability of time-series data retrieval
- Forecast data intervals: Efficient weather change tracking at 3-6 hour intervals

**System Improvements:**
- Enhanced error handling
- Improved forecast data robustness
- Prompt optimization for improved LLM response accuracy

**Verified Operation:**
- Weather comments: Appropriate selection by LLM
- Advice comments: Successful selection of #34 "Going out OK"
- Final output: Confirmed generation of "Calm during the day, going out OK"

🚀 Confirmed that generated comments change appropriately according to regional and weather conditions

## 🤝 Contributing

1. Create issues for bug reports and feature requests
2. Contribute via Fork & Pull Request
3. Follow [development guidelines](docs/CONTRIBUTING.md)

## 🔗 Support

If issues persist, please report them in GitHub Issues.

---

**If this setup guide doesn't resolve your issues, please report them in GitHub Issues.**
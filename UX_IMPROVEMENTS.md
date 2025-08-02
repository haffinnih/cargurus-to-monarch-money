# CarGurus Scraper: UX Improvements Plan

## Overview

This document outlines planned user experience improvements for the CarGurus scraper, focusing on making the tool more accessible to new users while maintaining power-user functionality.

## Core Philosophy

**Different users need different experiences:**

- **First-time users** need guidance and setup assistance
- **Casual users** want simplicity and minimal configuration
- **Power users** need full control and automation capabilities

## 🎯 Primary Goal: Setup Wizard with Persistent Configuration

### Problem Statement

New users face several barriers:

1. Don't know how to get CarGurus URLs
2. Confused by entity IDs and model paths
3. Need to re-enter parameters every time
4. Overwhelmed by technical output

### Solution: Interactive Setup with YAML Persistence

#### Setup Wizard Flow

```bash
$ uv run cargurus-scraper --setup
👋 Welcome to CarGurus Scraper!
Let's set up your vehicle data extraction in 3 easy steps.

📋 Step 1: Vehicle Information
1. Go to https://www.cargurus.com/research/price-trends
2. Search for your vehicle (year, make, model, trim)
3. Copy the complete URL from your browser

🔗 Paste your CarGurus URL here: [user input]
✅ Found: 2022 Honda Civic EX-L

📋 Step 2: Account Settings
What should we call this vehicle in your CSV files?
💰 Account name: [user input: "2022 Honda Civic EX-L"]

📋 Step 3: Data Preferences
📅 How much data do you want?
  1. Last 6 months (recommended)
  2. Last year (maximum available)
  3. Custom date range
  4. Use dates from URL (2024-01-01 to 2024-12-31)

💾 Save this configuration for future use?
📁 Configuration name: [user input: "honda-civic"]

✅ Setup complete! Configuration saved to ~/.cargurus/honda-civic.yaml

🚀 To run with this configuration:
   cargurus-scraper --config honda-civic

🔄 To update this configuration:
   cargurus-scraper --config honda-civic --setup
```

#### YAML Configuration Format

```yaml
# ~/.cargurus/honda-civic.yaml
name: "honda-civic"
description: "2022 Honda Civic EX-L price tracking"
created: "2024-08-02"
last_used: "2024-08-02"

vehicle:
  account_name: "2022 Honda Civic EX-L"

url_info:
  url: "https://www.cargurus.com/research/price-trends/Honda-Civic-EX-L-d2441?entityIds=c32015&startDate=1735689600000&endDate=1767225599000"
  model_path: "Honda-Civic-EX-L-d2441"
  entity_id: "c32015"

date_preferences:
  mode: "url_dates" # "url_dates", "relative", "fixed", "max_range"
  relative_months: 6 # if mode == "relative"
  fixed_start: "2024-01-01" # if mode == "fixed"
  fixed_end: "2024-12-31" # if mode == "fixed"

output:
  directory: "output"
  filename_template: "{account_name}_{start_date}_{end_date}.csv"

user_preferences:
  verbosity: "normal" # "quiet", "normal", "verbose"
  auto_accept_prompts: false
  open_csv_after_export: false
```

## 🛠 Implementation Plan

### Phase 1: Core Setup Wizard (High Priority)

#### New CLI Arguments

```python
parser.add_argument("--setup", action="store_true",
                   help="Interactive setup wizard")
parser.add_argument("--config", type=str,
                   help="Use saved configuration file")
parser.add_argument("--list-configs", action="store_true",
                   help="List available configurations")
parser.add_argument("--config-dir", type=str, default="~/.cargurus",
                   help="Configuration directory")
```

#### Configuration Manager Class

```python
# cargurus_scraper/config_manager.py
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VehicleConfig:
    name: str
    description: str
    account_name: str
    url: str
    model_path: str
    entity_id: str
    date_mode: str
    # ... other fields

class ConfigManager:
    def __init__(self, config_dir: str = "~/.cargurus"):
        self.config_dir = Path(config_dir).expanduser()
        self.config_dir.mkdir(exist_ok=True)

    def save_config(self, config: VehicleConfig) -> None:
        """Save configuration to YAML file."""

    def load_config(self, name: str) -> VehicleConfig:
        """Load configuration from YAML file."""

    def list_configs(self) -> List[str]:
        """List all available configurations."""

    def delete_config(self, name: str) -> None:
        """Delete a configuration file."""
```

#### Setup Wizard Implementation

```python
# cargurus_scraper/setup_wizard.py
class SetupWizard:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def run_interactive_setup(self, existing_config: Optional[str] = None) -> VehicleConfig:
        """Run the interactive setup wizard."""
        print("👋 Welcome to CarGurus Scraper!")

        # Step 1: URL Collection
        config = self._get_url_info()

        # Step 2: Account Settings
        config = self._get_account_settings(config)

        # Step 3: Date Preferences
        config = self._get_date_preferences(config)

        # Step 4: Output Preferences
        config = self._get_output_preferences(config)

        # Step 5: Save Configuration
        self._save_configuration(config)

        return config

    def _get_url_info(self) -> Dict:
        """Guide user through URL collection and parsing."""

    def _validate_url_interactive(self, url: str) -> Dict:
        """Validate URL and show extracted information."""
```

### Phase 2: Enhanced User Experience

#### Improved CLI Arguments

```python
# Verbosity control
parser.add_argument("-q", "--quiet", action="store_true",
                   help="Minimal output")
parser.add_argument("-v", "--verbose", action="store_true",
                   help="Detailed progress")

# Non-interactive mode
parser.add_argument("--yes", "-y", action="store_true",
                   help="Accept all defaults automatically")

# Output control
parser.add_argument("--output", "-o", type=str,
                   help="Custom output file path")
parser.add_argument("--output-dir", type=str,
                   help="Custom output directory")

# Configuration management
parser.add_argument("--save-config", type=str,
                   help="Save current settings to named configuration")
parser.add_argument("--update-config", type=str,
                   help="Update existing configuration")
parser.add_argument("--delete-config", type=str,
                   help="Delete a saved configuration")
```

#### Better Error Handling

```python
# cargurus_scraper/error_handler.py
class UserFriendlyErrorHandler:
    @staticmethod
    def handle_url_error(error: Exception) -> None:
        """Provide helpful guidance for URL parsing errors."""
        print("❌ Unable to parse the CarGurus URL")
        print("💡 Make sure you copied the complete URL from your browser")
        print("📖 Need help? Run: cargurus-scraper --setup")
        print(f"🔧 Technical details: {str(error)}")

    @staticmethod
    def handle_api_error(error: Exception) -> None:
        """Provide helpful guidance for API errors."""
        if "429" in str(error):
            print("⏳ CarGurus is temporarily limiting requests")
            print("💡 Please wait 2-3 minutes and try again")
            print("🔧 If this continues, try a smaller date range")
        elif "404" in str(error):
            print("❌ Vehicle data not found")
            print("💡 Double-check your URL and try again")
            print("📖 Need help? Run: cargurus-scraper --setup")
```

### Phase 3: Advanced Features

#### Smart Defaults and Suggestions

```python
class SmartDefaults:
    @staticmethod
    def suggest_account_name(model_path: str, entity_id: str) -> str:
        """Generate smart default account name from URL components."""

    @staticmethod
    def suggest_date_range(url_dates: tuple) -> Dict[str, str]:
        """Suggest optimal date range based on URL and current date."""

    @staticmethod
    def suggest_output_filename(account_name: str, date_range: tuple) -> str:
        """Generate smart filename based on vehicle and dates."""
```

#### Configuration Templates

```yaml
# ~/.cargurus/templates/basic-vehicle.yaml
name: "template-basic"
description: "Basic vehicle tracking template"
template: true

vehicle:
  account_name: "" # User fills in

url_info:
  url: "" # User fills in

date_preferences:
  mode: "relative"
  relative_months: 6

output:
  directory: "output"
  filename_template: "{account_name}_{start_date}_{end_date}.csv"

user_preferences:
  verbosity: "normal"
  auto_accept_prompts: false
```

## 📋 Implementation Checklist

### Phase 1: Core Setup Wizard

- [ ] Create `ConfigManager` class with YAML support
- [ ] Implement `SetupWizard` class
- [ ] Add `--setup`, `--config`, `--list-configs` CLI arguments
- [ ] Update main CLI flow to check for configurations
- [ ] Create configuration directory structure
- [ ] Add YAML dependency to project
- [ ] Write tests for configuration management
- [ ] Update README with setup wizard documentation

### Phase 2: Enhanced UX

- [ ] Add verbosity control (`--quiet`, `--verbose`)
- [ ] Implement non-interactive mode (`--yes`)
- [ ] Add custom output options (`--output`, `--output-dir`)
- [ ] Improve error messages with actionable suggestions
- [ ] Add configuration update/delete functionality
- [ ] Handle existing file conflicts gracefully

### Phase 3: Advanced Features

- [ ] Smart default suggestions
- [ ] Configuration templates
- [ ] Configuration validation and migration
- [ ] Bulk operations (multiple vehicles)
- [ ] Export/import configurations

## 📊 Success Metrics

### User Experience Goals

- **Reduce time to first success**: From 10+ minutes to under 3 minutes
- **Eliminate repeated parameter entry**: Use saved configurations
- **Reduce support questions**: Self-service through guided setup
- **Increase user retention**: Make it easy to come back and get more data

### Technical Goals

- **Maintain backward compatibility**: Existing commands still work
- **Clean configuration management**: No config file conflicts or corruption
- **Robust error handling**: Always provide next steps
- **Comprehensive testing**: All configuration scenarios covered

## 🚀 Usage Examples After Implementation

### First-time user experience:

```bash
$ uv run cargurus-scraper --setup
# Guided wizard creates ~/.cargurus/my-honda.yaml

$ uv run cargurus-scraper --config my-honda
🔍 Fetching data for 2022 Honda Civic EX-L...
✅ Saved: output/2022_Honda_Civic_EX-L_2024-02-01_2024-08-01.csv
```

### Power user experience:

```bash
$ uv run cargurus-scraper --config honda --verbose --output ~/car-data/honda-latest.csv --yes
```

### Configuration management:

```bash
$ uv run cargurus-scraper --list-configs
Available configurations:
  honda-civic    2022 Honda Civic EX-L (last used: 2024-08-01)
  toyota-camry   2020 Toyota Camry LE (last used: 2024-07-15)

$ uv run cargurus-scraper --config honda-civic --update-config
# Opens wizard to update existing configuration
```

This approach transforms the tool from a technical utility into a user-friendly application that grows with the user's needs while maintaining all existing functionality for current users.

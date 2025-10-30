# Jira Allocations Project

This project contains multiple versions of a Jira allocation application with different approaches and implementations.

## Project Files

- `app_modern.py` - The latest modern version of the application (Main Streamlit App)
- `app_modern copy.py` - Copy of the modern version
- `app_improved_not_work.py` - Improved version (currently not working)
- `app_v1.py` - Original version of the application
- `bu_mapping_current.xlsx` - Business unit mapping data

## Features

- 📄 **PDF Invoice Processing** - Automatic extraction of Atlassian invoice data
- 💰 **VAT Handling** - Toggle between Include/Exclude VAT calculations
- 👥 **User Management** - CSV import and business unit mapping
- 📊 **Allocation Calculation** - Smart distribution based on user counts
- 💾 **Data Persistence** - Automatic saving of business unit mappings
- 📱 **Modern UI** - Clean, responsive Streamlit interface

## Setup

1. Clone the repository
   ```bash
   git clone https://github.com/thungong/jiraallocate.git
   cd jiraallocate
   ```

2. Install required dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application
   ```bash
   streamlit run app_modern.py
   ```

4. Open your browser to `http://localhost:8501`

## Usage

1. **Upload Files:**
   - 📄 Invoice PDF from Atlassian
   - 👥 Users CSV file with email addresses

2. **Configure VAT:**
   - ✅ Check "Include VAT" for newer invoices with Tax column
   - ❌ Uncheck for older invoices with only "Amount excl. tax"

3. **Process:**
   - App automatically extracts amounts and maps users
   - Review and edit business unit mappings as needed
   - Download allocation results

## Deployment Options

### 🌟 Recommended: Streamlit Cloud (Free)

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Connect your GitHub account
3. Select repository: `thungong/jiraallocate`
4. Set main file: `app_modern.py`
5. Click Deploy!

### 🚀 Alternative Platforms

#### Heroku
```bash
# Install Heroku CLI, then:
heroku create your-app-name
git push heroku main
```

#### Railway
1. Go to [railway.app](https://railway.app/)
2. Connect GitHub repository
3. Railway will auto-detect and deploy

#### Docker
```bash
# Build and run locally
docker build -t jira-allocations .
docker run -p 8501:8501 jira-allocations
```

### 📜 Deployment Script
Run the interactive deployment helper:
```bash
./deploy.sh
```

## Requirements

- Python 3.9+
- Streamlit >= 1.28.0
- pandas >= 2.0.0
- pdfplumber >= 0.10.0
- openpyxl >= 3.1.0

## File Structure

```
jiraallocate/
├── app_modern.py          # Main Streamlit application
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python version specification
├── Dockerfile            # Container configuration
├── Procfile              # Heroku deployment config
├── deploy.sh             # Deployment helper script
├── bu_mapping_current.xlsx # Business unit mapping data
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for internal business use.
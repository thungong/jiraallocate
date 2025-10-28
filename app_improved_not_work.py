import streamlit as st
import pandas as pd
import pdfplumber
import io
import os
import re
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Tuple
import plotly.express as px
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PERSIST_FILE = "bu_mapping_current.xlsx"
BACKUP_DIR = "backups"
DEFAULT_PRODUCTS = [
    ("Confluence", 30),
    ("draw.io Diagrams |", 30),
    ("Flowchart & PlantUML", 30),
    ("Jira Service", 14),
    ("Jira, Standard", 52),
    ("draw.io Diagrams for", 52),
]

# Backup throttling
LAST_BACKUP_TIME = None
BACKUP_COOLDOWN = timedelta(seconds=30)  # 30 seconds minimum between backups

# Page Configuration
st.set_page_config(
    page_title="Atlassian Expense Allocation Tool", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    color: #0052CC;
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 2rem;
}
.status-success {
    background-color: #E3FCEF;
    border: 1px solid #00875A;
    border-radius: 4px;
    padding: 0.5rem;
    color: #00875A;
}
.status-warning {
    background-color: #FFF7E6;
    border: 1px solid #FF8B00;
    border-radius: 4px;
    padding: 0.5rem;
    color: #FF8B00;
}
.metric-card {
    background-color: #F4F5F7;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_bu_mapping() -> pd.DataFrame:
    """Load BU mapping with caching for better performance"""
    columns = ['User name', 'Email', 'Cost To']
    try:
        if os.path.exists(PERSIST_FILE):
            bu_df = pd.read_excel(PERSIST_FILE)
            for col in columns:
                if col not in bu_df.columns:
                    bu_df[col] = ""
            return bu_df[columns]
        else:
            return pd.DataFrame(columns=columns)
    except Exception as e:
        st.error(f"Error loading BU mapping: {str(e)}")
        return pd.DataFrame(columns=columns)

def save_bu_mapping(df: pd.DataFrame, create_backup: bool = True) -> bool:
    """Save BU mapping with backup option"""
    try:
        # Create backup if requested
        if create_backup and os.path.exists(PERSIST_FILE):
            create_backup_file()
        
        df.to_excel(PERSIST_FILE, index=False)
        st.cache_data.clear()  # Clear cache to reload fresh data
        return True
    except Exception as e:
        st.error(f"Error saving BU mapping: {str(e)}")
        return False

def create_backup_file():
    """Create backup of current BU mapping with throttling"""
    global LAST_BACKUP_TIME
    
    try:
        # Check throttling
        now = datetime.now()
        if LAST_BACKUP_TIME and (now - LAST_BACKUP_TIME) < BACKUP_COOLDOWN:
            logger.info("Backup skipped due to cooldown period")
            return
        
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"bu_mapping_backup_{timestamp}.xlsx")
        
        if os.path.exists(PERSIST_FILE):
            df = pd.read_excel(PERSIST_FILE)
            df.to_excel(backup_path, index=False)
            LAST_BACKUP_TIME = now
            logger.info(f"Backup created: {backup_path}")
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def extract_invoice_items(text: str, custom_products: Optional[List[Tuple[str, int]]] = None) -> List[Dict]:
    """Extract invoice items with better error handling and flexibility"""
    products = custom_products or DEFAULT_PRODUCTS
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = []
    
    for name, default_count in products:
        amount = None
        for line in lines:
            if name.lower() in line.lower():
                # More flexible regex patterns
                patterns = [
                    r"USD\s*([\d,]+\.\d{2})",
                    r"\$\s*([\d,]+\.\d{2})",
                    r"([\d,]+\.\d{2})\s*USD",
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            amount = float(match.group(1).replace(',', ''))
                            break
                        except ValueError:
                            continue
                if amount:
                    break
        
        found.append({
            "desc": name,
            "amount": amount,
            "count": default_count,
        })
    
    return found

def rounding_safe_split(total: float, n: int) -> List[float]:
    """Distribute amount evenly with rounding-safe calculation"""
    if n == 0:
        return []
    
    per_user = total / n
    shares = [round(per_user, 2) for _ in range(n)]
    diff = round(total - sum(shares), 2)
    
    # Distribute remaining difference
    if abs(diff) > 0:
        shares[-1] += diff
    
    return shares

def validate_csv_format(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate CSV format"""
    required_columns = ['email']
    missing_columns = [col for col in required_columns if col not in df.columns.str.lower()]
    
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    # Check for valid emails
    email_col = None
    for col in df.columns:
        if col.lower() == 'email':
            email_col = col
            break
    
    if email_col:
        invalid_emails = df[~df[email_col].apply(validate_email)]
        if len(invalid_emails) > 0:
            return False, f"Found {len(invalid_emails)} invalid email addresses"
    
    return True, "CSV format is valid"

def display_metrics(data: Dict[str, any]):
    """Display metrics in a nice format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{data.get('total_users', 0)}</h3>
            <p>Total Users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{data.get('it_users', 0)}</h3>
            <p>IT Users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>${data.get('total_amount', 0):,.2f}</h3>
            <p>Total Amount</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{data.get('products_found', 0)}</h3>
            <p>Products Found</p>
        </div>
        """, unsafe_allow_html=True)

# Sidebar Navigation
page = st.sidebar.radio(
    "Navigation", 
    ["🏠 Dashboard", "💰 Expense Allocation", "🏢 BU Mapping Management", "📊 Analytics"],
    index=1
)

# Dashboard Page
if page == "🏠 Dashboard":
    st.markdown('<h1 class="main-header">📊 Dashboard</h1>', unsafe_allow_html=True)
    
    # Load current statistics
    bu_df = load_bu_mapping()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Statistics")
        st.metric("Total Users in BU Mapping", len(bu_df))
        st.metric("Unique Business Units", bu_df['Cost To'].nunique() if not bu_df.empty else 0)
    
    with col2:
        st.subheader("📁 Recent Files")
        if os.path.exists(PERSIST_FILE):
            mod_time = datetime.fromtimestamp(os.path.getmtime(PERSIST_FILE))
            st.write(f"BU Mapping last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show backup files
        if os.path.exists(BACKUP_DIR):
            backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.xlsx')]
            st.write(f"Available backups: {len(backups)}")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 View BU Mapping", use_container_width=True):
            st.info("Navigate to 'BU Mapping Management' in the sidebar")
    
    with col2:
        if st.button("💰 New Allocation", use_container_width=True):
            st.info("Navigate to 'Expense Allocation' in the sidebar")
    
    with col3:
        if st.button("🔄 Create Backup", use_container_width=True):
            create_backup_file()
            st.success("Backup created successfully!")

# BU Mapping Management Page
elif page == "🏢 BU Mapping Management":
    st.markdown('<h1 class="main-header">🏢 BU Mapping Management</h1>', unsafe_allow_html=True)
    st.write("Add, edit, or delete Business Unit mapping here. All changes are saved instantly.")

    bu_df = load_bu_mapping()
    
    # Upload mapping section
    with st.expander("📤 Upload New Mapping", expanded=False):
        bu_upload = st.file_uploader("Upload BU Mapping Excel (.xlsx) to replace current mapping", type=["xlsx"])
        if bu_upload:
            try:
                upload_df = pd.read_excel(bu_upload)
                columns = ['User name', 'Email', 'Cost To']
                
                for col in columns:
                    if col not in upload_df.columns:
                        upload_df[col] = ""
                
                upload_df = upload_df[columns]
                
                # Validate emails
                invalid_emails = upload_df[~upload_df['Email'].apply(validate_email)]
                if len(invalid_emails) > 0:
                    st.warning(f"Found {len(invalid_emails)} rows with invalid emails. Please fix these:")
                    st.dataframe(invalid_emails)
                else:
                    if save_bu_mapping(upload_df):
                        st.success("BU Mapping replaced and saved successfully!")
                        st.rerun()
                    
            except Exception as e:
                st.error(f"Error processing uploaded file: {str(e)}")

    # Statistics
    if not bu_df.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", len(bu_df))
        with col2:
            st.metric("Business Units", bu_df['Cost To'].nunique())
        with col3:
            st.metric("Unknown Mappings", len(bu_df[bu_df['Cost To'] == 'Unknown']))

    # Editable table
    st.subheader("📝 Edit Mapping")
    edited_df = st.data_editor(
        bu_df,
        num_rows="dynamic",
        use_container_width=True,
        key="bu_edit",
        column_config={
            "Email": st.column_config.TextColumn(
                "Email",
                help="User email address",
                validate="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            "Cost To": st.column_config.SelectboxColumn(
                "Cost To",
                help="Business unit for cost allocation",
                options=["IT", "Finance", "Marketing", "Sales", "HR", "Operations", "Unknown"]
            )
        }
    )

    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes", use_container_width=True):
            if save_bu_mapping(edited_df, create_backup=True):
                st.success("Changes saved successfully!")
    
    with col2:
        # Delete rows functionality
        if not edited_df.empty:
            to_delete = st.multiselect(
                "Select rows to delete", 
                options=edited_df.index, 
                format_func=lambda x: f"{edited_df.loc[x, 'User name']} ({edited_df.loc[x, 'Email']})"
            )
            
            if to_delete and st.button("🗑️ Delete Selected", use_container_width=True):
                edited_df = edited_df.drop(index=to_delete).reset_index(drop=True)
                if save_bu_mapping(edited_df, create_backup=True):
                    st.success("Selected rows deleted successfully!")
                    st.rerun()
    
    with col3:
        # Download current mapping
        if not edited_df.empty:
            with io.BytesIO() as buf:
                edited_df.to_excel(buf, index=False)
                st.download_button(
                    "📥 Download Mapping", 
                    data=buf.getvalue(), 
                    file_name=f"BU-mapping-{datetime.now().strftime('%Y%m%d')}.xlsx",
                    use_container_width=True
                )

# Expense Allocation Page  
elif page == "💰 Expense Allocation":
    st.markdown('<h1 class="main-header">💰 Atlassian Expense Allocation</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 📋 Instructions:
    1. **Upload Invoice PDF** - Your Atlassian invoice in PDF format
    2. **Upload Users CSV** - Export from your system (must contain 'email' column)
    3. **Review and Adjust** - Check auto-detected amounts and BU mappings
    4. **Download Results** - Get your allocation Excel files
    """)
    
    st.divider()
    
    # File upload section
    col1, col2 = st.columns(2)
    
    with col1:
        pdf_file = st.file_uploader("📄 Upload Invoice PDF", type=["pdf"], key="pdf_file")
        
    with col2:
        csv_file = st.file_uploader("👥 Upload Users CSV", type=["csv"], key="csv_file")

    if pdf_file and csv_file:
        try:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Parse Invoice
            status_text.text("📖 Reading PDF invoice...")
            progress_bar.progress(10)
            
            with pdfplumber.open(pdf_file) as pdf:
                text = ''
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
                    progress_bar.progress(10 + (i + 1) * 20 // len(pdf.pages))
            
            if not text.strip():
                st.error("❌ Could not extract text from PDF. Please ensure the PDF is not image-based.")
                st.stop()
            
            # Show PDF preview in expander
            with st.expander("📄 PDF Text Preview", expanded=False):
                st.text_area("Extracted Text", text, height=200)
            
            progress_bar.progress(30)
            status_text.text("🔍 Extracting product information...")
            
            product_items = extract_invoice_items(text)
            missing = [i for i in product_items if i['amount'] is None]
            
            progress_bar.progress(40)
            
            # Handle missing amounts
            if missing:
                st.warning(f"⚠️ Could not auto-extract {len(missing)} product amounts. Please enter them manually below:")
                
                cols = st.columns(2)
                for i, item in enumerate(product_items):
                    if item['amount'] is None:
                        col_idx = i % 2
                        with cols[col_idx]:
                            manual_amount = st.number_input(
                                f"💰 {item['desc']}", 
                                min_value=0.0, 
                                format="%.2f", 
                                key=f"manual_{i}",
                                help=f"Default user count: {item['count']}"
                            )
                            item['amount'] = manual_amount
                
                if any(i['amount'] is None or i['amount'] == 0 for i in product_items):
                    st.info("👆 Please fill in all missing amounts to continue.")
                    st.stop()
            
            # Validate and load users
            status_text.text("👥 Processing user data...")
            progress_bar.progress(50)
            
            users_df = pd.read_csv(csv_file)
            
            # Validate CSV format
            is_valid, message = validate_csv_format(users_df)
            if not is_valid:
                st.error(f"❌ CSV Validation Error: {message}")
                st.stop()
            
            # Standardize column names
            users_df.columns = users_df.columns.str.lower()
            users_df['email'] = users_df['email'].str.lower().str.strip()
            
            # Try to find name column
            name_col = None
            for possible_name in ['user name', 'username', 'name', 'display_name']:
                if possible_name in users_df.columns:
                    name_col = possible_name
                    break
            
            if name_col:
                users_df['User name'] = users_df[name_col]
            else:
                users_df['User name'] = users_df['email'].str.split('@').str[0]
            
            progress_bar.progress(60)
            status_text.text("🏢 Loading BU mapping...")
            
            # Load and merge BU mapping with proper column handling
            bu_df = load_bu_mapping()
            bu_df['Email'] = bu_df['Email'].str.lower().str.strip()
            
            merged = pd.merge(users_df, bu_df, left_on='email', right_on='Email', how='left', suffixes=('_user', '_bu'))
            unmapped = merged[merged['Cost To'].isna()]
            
            progress_bar.progress(70)
            
            # Handle unmapped users
            if len(unmapped) > 0:
                st.info(f"ℹ️ Found {len(unmapped)} new users. Auto-adding to BU mapping with 'Unknown' cost center.")
                
                new_entries = []
                for idx, row in unmapped.iterrows():
                    # Use the correct column name after merge
                    user_name = row.get("User name_user", row.get("User name", ""))
                    if not user_name:
                        user_name = row["email"].split('@')[0]
                    
                    new_entries.append({
                        "User name": user_name,
                        "Email": row["email"],
                        "Cost To": "Unknown",
                    })
                
                # Update BU mapping
                new_bu_df = pd.concat([bu_df, pd.DataFrame(new_entries)], ignore_index=True)
                new_bu_df = new_bu_df.drop_duplicates(subset=["Email"], keep="last")
                
                if save_bu_mapping(new_bu_df, create_backup=True):
                    # Re-merge with updated mapping
                    merged = pd.merge(users_df, new_bu_df, left_on='email', right_on='Email', how='left', suffixes=('_user', '_bu'))
                else:
                    st.error("Failed to save updated BU mapping")
                    st.stop()
            
            progress_bar.progress(80)
            status_text.text("💰 Calculating allocations...")
            
            # Calculate allocations
            merged['Cost To'] = merged['Cost To'].fillna("Unknown")
            total_users = len(merged)
            it_users = merged[merged['Cost To'].str.upper() == "IT"]
            num_it_users = len(it_users)
            
            # Get product names for output
            product_names = [p['desc'] for p in product_items]
            total_amount = sum(p['amount'] for p in product_items)
            
            # Calculate metrics
            metrics_data = {
                'total_users': total_users,
                'it_users': num_it_users,
                'total_amount': total_amount,
                'products_found': len([p for p in product_items if p['amount'] is not None])
            }
            
            progress_bar.progress(90)
            
            # Display metrics
            st.subheader("📊 Allocation Summary")
            display_metrics(metrics_data)
            
            # Rounding-safe allocations
            alloc_shares = {}
            for idx in [0, 1, 2, 4, 5]:  # All users products
                if idx < len(product_items):
                    alloc_shares[product_names[idx]] = rounding_safe_split(product_items[idx]['amount'], total_users)
            
            # Jira Service (IT only)
            jira_service_shares = [0.00] * total_users
            if num_it_users > 0 and len(product_items) > 3:
                shares_for_it = rounding_safe_split(product_items[3]['amount'], num_it_users)
                it_idx = merged["Cost To"].str.upper() == "IT"
                share_iter = iter(shares_for_it)
                for i in range(total_users):
                    if it_idx.iloc[i]:
                        jira_service_shares[i] = next(share_iter)
            
            # Create output DataFrame with proper column handling
            # Determine the correct user name column after merge
            user_name_col = None
            for possible_col in ["User name_user", "User name_bu", "User name"]:
                if possible_col in merged.columns:
                    user_name_col = possible_col
                    break
            
            if user_name_col is None:
                # Create user names from email if not available
                user_names = merged["email"].str.split('@').str[0]
            else:
                user_names = merged[user_name_col].fillna(merged["email"].str.split('@').str[0])
            
            output_df = pd.DataFrame({
                "User name": user_names,
                "Email": merged["email"],
                "Cost To": merged["Cost To"],
            })
            
            # Add product columns
            for idx, product_name in enumerate(product_names):
                if idx == 3:  # Jira Service
                    output_df[product_name] = jira_service_shares
                elif idx in alloc_shares:
                    output_df[product_name] = alloc_shares[product_name]
                else:
                    output_df[product_name] = [0.00] * total_users
            
            progress_bar.progress(100)
            status_text.text("✅ Allocation completed successfully!")
            
            st.success("🎉 Allocation calculated successfully!")
            
            # Display results
            st.subheader("👥 Individual Allocations (Preview)")
            st.dataframe(output_df.head(10), hide_index=True, use_container_width=True)
            
            if len(output_df) > 10:
                st.info(f"Showing first 10 of {len(output_df)} users. Download full results below.")
            
            # Summary by Cost To
            st.subheader("🏢 Summary by Business Unit")
            summary_cols = product_names
            summary = output_df.groupby("Cost To")[summary_cols].sum().reset_index()
            summary["Grand Total"] = summary[summary_cols].sum(axis=1)
            summary = summary.sort_values("Grand Total", ascending=False)
            
            st.dataframe(summary, hide_index=True, use_container_width=True)
            
            # Download section
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Individual allocation download
                towrite = io.BytesIO()
                with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
                    output_df.to_excel(writer, index=False, sheet_name="Individual Allocation")
                    summary.to_excel(writer, index=False, sheet_name="Summary by BU")
                
                towrite.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label="📊 Download Full Allocation Report",
                    data=towrite.getvalue(),
                    file_name=f"Expense_Allocation_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                # Summary only download
                with io.BytesIO() as buf2:
                    summary.to_excel(buf2, index=False)
                    st.download_button(
                        "🏢 Download BU Summary Only", 
                        data=buf2.getvalue(), 
                        file_name=f"BU_Summary_{timestamp}.xlsx",
                        use_container_width=True
                    )
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ An error occurred during processing: {str(e)}")
            logger.error(f"Processing error: {str(e)}", exc_info=True)
    
    else:
        st.info("👆 Please upload both Invoice PDF and Users CSV files to proceed.")

elif page == "📊 Analytics":
    st.markdown('<h1 class="main-header">📊 Analytics</h1>', unsafe_allow_html=True)
    
    try:
        bu_df = load_bu_mapping()
        
        if bu_df.empty:
            st.info("📭 No BU mapping data available. Please add some data first.")
            st.markdown("### 🚀 Quick Start")
            st.markdown("1. Go to **BU Mapping Management** to add users")
            st.markdown("2. Or upload a CSV file with user data")
        else:
            bu_counts = bu_df['Cost To'].value_counts()
            
            # Only show charts if we have valid data
            if len(bu_counts) > 0 and bu_counts.sum() > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("👥 Users by Business Unit")
                    # Use plotly for better compatibility
                    fig_bar = px.bar(
                        x=bu_counts.index, 
                        y=bu_counts.values,
                        labels={'x': 'Business Unit', 'y': 'Number of Users'},
                        title="Users by Business Unit"
                    )
                    fig_bar.update_layout(showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col2:
                    st.subheader("📈 BU Distribution")
                    # Create a simple pie chart using plotly with better data handling
                    fig = px.pie(
                        values=bu_counts.values, 
                        names=bu_counts.index, 
                        title="Business Unit Distribution"
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📋 Detailed Breakdown")
                breakdown_df = bu_df.groupby('Cost To').agg({
                    'User name': 'count',
                    'Email': lambda x: ', '.join(x[:3]) + ('...' if len(x) > 3 else '')
                }).rename(columns={'User name': 'Count', 'Email': 'Sample Users'})
                
                st.dataframe(breakdown_df, use_container_width=True)
            else:
                st.warning("⚠️ No valid data found for visualization")
        
        # Show backup history
        if os.path.exists(BACKUP_DIR):
            st.subheader("🔄 Backup History")
            try:
                backups = []
                backup_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.xlsx')]
                
                for f in backup_files:
                    try:
                        path = os.path.join(BACKUP_DIR, f)
                        mod_time = datetime.fromtimestamp(os.path.getmtime(path))
                        size_kb = round(os.path.getsize(path)/1024, 2)
                        backups.append({
                            'File': f, 
                            'Created': mod_time.strftime('%Y-%m-%d %H:%M:%S'), 
                            'Size (KB)': size_kb
                        })
                    except OSError:
                        continue  # Skip files that can't be accessed
                
                if backups:
                    backup_df = pd.DataFrame(backups).sort_values('Created', ascending=False)
                    st.dataframe(backup_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No backup files found")
                    
            except Exception as e:
                st.error(f"Error loading backup history: {str(e)}")
        else:
            st.info("💡 Backup directory will be created when you make your first backup")
            
    except Exception as e:
        st.error(f"❌ Error loading analytics data: {str(e)}")
        logger.error(f"Analytics error: {str(e)}", exc_info=True)
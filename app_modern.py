import streamlit as st
import pandas as pd
import pdfplumber
import io
import os
import re
import time
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Atlassian Expense Allocation Tool", 
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Constants
PERSIST_FILE = "bu_mapping_current.xlsx"

# Custom CSS for modern blue styling
st.markdown("""
<style>
        /* Minimal Theme - Clean White & Gray */
        .stApp {
            background: #ffffff;
            color: #1a1a1a;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* Content Areas */
        .main .block-container {
            background: #ffffff;
            border-radius: 8px;
            padding: 2rem;
            max-width: 1200px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #1a1a1a !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }
        
        h1 {
            font-size: 2rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: #f8f9fa !important;
            border-right: 1px solid #e9ecef !important;
        }
        
        /* Navigation */
        .stSelectbox > div > div {
            background: #ffffff !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
            color: #374151 !important;
        }
        
        /* Buttons - Minimal Style */
        .stButton > button {
            background: #ffffff !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
        }
        
        .stButton > button:hover {
            background: #f9fafb !important;
            border-color: #9ca3af !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        
        /* Primary buttons */
        .stButton > button[kind="primary"] {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #1a1a1a !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background: #374151 !important;
            border-color: #374151 !important;
        }
        
        /* File uploader */
        .stFileUploader > div {
            background: #f9fafb !important;
            border: 2px dashed #d1d5db !important;
            border-radius: 8px !important;
            padding: 2rem !important;
        }
        
        /* Info/Warning/Success boxes */
        .stAlert {
            border-radius: 8px !important;
            border: 1px solid #e5e7eb !important;
            background: #f9fafb !important;
        }
        
        .stAlert[data-baseweb="notification"][data-testid="stNotification"] {
            background: #f0f9ff !important;
            border-color: #0ea5e9 !important;
        }
        
        /* Text Input */
        .stTextInput > div > div > input {
            background: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #374151 !important;
            box-shadow: 0 0 0 3px rgba(55, 65, 81, 0.1) !important;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            background: #f9fafb !important;
            color: #374151 !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 6px !important;
        }
        
        /* Metrics */
        .metric-container {
            background: #ffffff !important;
            border-radius: 8px !important;
            padding: 1rem !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }    /* Modern card styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        border: 2px solid rgba(14, 165, 233, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #0EA5E9, #3B82F6);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #0284C7, #2563EB);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
    }
    
        /* Data Editor - Minimal Clean Style */
        div[data-testid="stDataFrame"], 
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stDataFrame"] table,
        .dataframe,
        .dataframe-container,
        .stDataEditor,
        .stDataEditor > div {
            background: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 6px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
            font-size: 14px !important;
        }
        
        /* Data Editor Headers - Minimal */
        div[data-testid="stDataFrame"] th,
        .dataframe th,
        .stDataEditor th {
            background: #f9fafb !important;
            color: #374151 !important;
            border: 1px solid #e5e7eb !important;
            font-weight: 500 !important;
            text-align: left !important;
            padding: 12px 16px !important;
            font-size: 13px !important;
            letter-spacing: 0.025em !important;
            text-transform: uppercase !important;
        }
        
        /* Data Editor Cells - Clean */
        div[data-testid="stDataFrame"] td,
        .dataframe td,
        .stDataEditor td {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #f3f4f6 !important;
            padding: 12px 16px !important;
        }
        
        /* Data Editor Row Hover - Subtle */
        div[data-testid="stDataFrame"] tr:hover td,
        .dataframe tr:hover td,
        .stDataEditor tr:hover td {
            background-color: #f9fafb !important;
        }
        
        /* Data Editor Control Buttons - Minimal */
        div[data-testid="stDataFrame"] button,
        .dataframe button,
        .stDataEditor button,
        button[title*="Add"],
        button[title*="add"],
        button[title*="Delete"],
        button[title*="delete"],
        button[aria-label*="row"],
        button[data-testid*="row"] {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 4px !important;
            padding: 6px 8px !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            min-width: 28px !important;
            min-height: 28px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
        }
        
        div[data-testid="stDataFrame"] button:hover,
        .dataframe button:hover,
        .stDataEditor button:hover {
            background: #374151 !important;
            border-color: #374151 !important;
        }
        
        /* Control area styling */
        div[data-testid="stDataFrame"] .row-controls,
        div[data-testid="stDataFrame"] .add-row,
        div[data-testid="stDataFrame"] .delete-row,
        .dataframe-controls,
        .table-controls {
            background: #ffffff !important;
            padding: 8px !important;
            margin: 4px !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 6px !important;
            display: flex !important;
            gap: 8px !important;
        }
        
        /* Icon styling */
        button[title*="Add row"] svg,
        button[aria-label*="Add row"] svg,
        button[title*="Delete"] svg,
        button[aria-label*="Delete"] svg {
            fill: #ffffff !important;
            width: 14px !important;
            height: 14px !important;
        }
        
        /* Input Fields - Clean */
        div[data-testid="stDataFrame"] input,
        .dataframe input,
        .stDataEditor input {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #d1d5db !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
        }
        
        div[data-testid="stDataFrame"] input:focus,
        .dataframe input:focus,
        .stDataEditor input:focus {
            border-color: #374151 !important;
            box-shadow: 0 0 0 3px rgba(55, 65, 81, 0.1) !important;
            outline: none !important;
        }
        
        /* Select Fields */
        div[data-testid="stDataFrame"] select,
        .dataframe select,
        .stDataEditor select {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 1px solid #d1d5db !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
        }
        
        /* Checkboxes */
        div[data-testid="stDataFrame"] input[type="checkbox"],
        .dataframe input[type="checkbox"],
        .stDataEditor input[type="checkbox"] {
            accent-color: #1a1a1a !important;
        }    /* Section headers */
    h1, h2, h3 {
        color: #1E40AF;
        font-weight: 700;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #0EA5E9, transparent);
        margin: 2rem 0;
    }
    
    /* Success/Info messages */
    .stSuccess {
        background: linear-gradient(45deg, #10B981, #059669);
        border-radius: 12px;
        border: none;
    }
    
    .stInfo {
        background: linear-gradient(45deg, #0EA5E9, #3B82F6);
        border-radius: 12px;
        border: none;
    }
    
    .stWarning {
        background: linear-gradient(45deg, #F59E0B, #D97706);
        border-radius: 12px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
page = st.sidebar.radio("📋 Navigation", ["💰 Expense Allocation", "👥 BU Mapping Management"])

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {
        'pdf_file': None,
        'csv_file': None,
        'pdf_content': None,
        'users_data': None,
        'include_vat': False,  # Default to exclude VAT (older format)
        'allocation_result': None,  # Cache for allocation results
        'summary_result': None,     # Cache for summary results
    }

def extract_invoice_items(text, include_vat=False):
    items = [
        ("Confluence", 30),
        ("draw.io Diagrams |", 30),
        ("Flowchart & PlantUML", 30),
        ("Jira Service", 14),
        ("Jira, Standard", 52),
        ("draw.io Diagrams for", 52),
    ]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = []
    for name, default_count in items:
        for line in lines:
            if name.lower() in line.lower():
                amount = None
                if include_vat:
                    # For new format with VAT: look for 'Amount' column (includes VAT)
                    # Pattern looks for: USD XXX.XX at the end of line (final amount column)
                    matches = re.findall(r"USD\s*([\d,]+\.\d{2})", line)
                    if matches:
                        # Take the last USD amount (rightmost column = Amount with VAT)
                        amount = float(matches[-1].replace(',', ''))
                else:
                    # For old format: look for any USD amount (Amount excl. tax)
                    match = re.search(r"USD\s*([\d,]+\.\d{2})", line)
                    if match:
                        amount = float(match.group(1).replace(',', ''))
                
                found.append({
                    "desc": name,
                    "amount": amount,
                    "count": default_count,
                })
                break
        else:
            found.append({"desc": name, "amount": None, "count": default_count})
    return found

def rounding_safe_split(total, n):
    per_user = total / n
    shares = [round(per_user, 2) for _ in range(n)]
    diff = round(total - sum(shares), 2)
    shares[-1] += diff
    return shares

# ===== BU Mapping Management =====
if page == "👥 BU Mapping Management":
    st.title("👥 Business Unit Mapping Management")
    st.markdown("**Manage user-to-business unit mappings for cost allocation**")
    
    with st.expander("📋 How to Manage Mappings", expanded=False):
        st.markdown("""
        **Primary Methods (Recommended):**
        • **➕ Add Users:** Click the **+** button at the bottom of the table to add new rows
        • **✏️ Edit Data:** Click on any cell in the table to edit user information directly
        • **🗑️ Delete Users:** Use checkboxes to select rows, then they'll be removed
        • **💾 Save Changes:** Click 'Save Changes' to persist all your modifications
        
        **Alternative Method:**
        • **📁 Bulk Upload:** Upload Excel file only when you need to replace ALL data at once
        • **📥 Export:** Download current mapping as Excel for backup or sharing
        """)

    columns = ['User name', 'Email', 'Cost To']
    
    # Load existing or create new
    if os.path.exists(PERSIST_FILE):
        bu_df = pd.read_excel(PERSIST_FILE)
        for col in columns:
            if col not in bu_df.columns:
                bu_df[col] = ""
        bu_df = bu_df[columns]
    else:
        bu_df = pd.DataFrame(columns=columns)

    # Show current data statistics
    if not bu_df.empty:
        total_users = len(bu_df)
        unique_bus = bu_df['Cost To'].nunique()
        st.info(f"📊 **Current Data:** {total_users} users mapped to {unique_bus} business units")
    else:
        st.info("📊 **Database is empty** - Add your first user mapping below")
    
    st.divider()
    
    # Get options for Cost To dropdown
    existing_cost_to = bu_df['Cost To'].dropna().unique().tolist() if not bu_df.empty else []
    default_options = ["IT", "Finance", "Marketing", "Sales", "HR", "Operations", "Club", "FS", "Unknown"]
    all_options = list(set(default_options + existing_cost_to))
    all_options.sort()

    st.markdown("### � User Mapping Database")
    
    # Quick stats and tips
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        if not bu_df.empty:
            st.metric("👥 Total Users", len(bu_df))
    with col_info2:
        if not bu_df.empty:
            unique_cost_centers = bu_df['Cost To'].nunique()
            st.metric("🏢 Business Units", unique_cost_centers)
    
    st.markdown("**� How to manage rows:**")
    col_tip1, col_tip2, col_tip3 = st.columns(3)
    with col_tip1:
        st.markdown("📝 **Add:** Click **+** at bottom of table")
    with col_tip2:
        st.markdown("✏️ **Edit:** Click any cell to modify")
    with col_tip3:
        st.markdown("🗑️ **Delete:** Select row checkbox, then delete icon")
    
    # Show instruction before table
    st.info("📝 **Instructions:** Use checkboxes on the left to select rows for deletion. Click the trash icon to delete selected rows.")
    
    # Dynamic data editor with improved visibility
    edited_df = st.data_editor(
        bu_df,
        num_rows="dynamic",
        use_container_width=True,
        key="bu_editor",
        height=400,  # Set fixed height to show more rows
        hide_index=False,  # Keep index visible for debugging
        column_config={
            "User name": st.column_config.TextColumn(
                "👤 User Name",
                help="Full name of the user",
                required=True,
                width="medium"
            ),
            "Email": st.column_config.TextColumn(
                "📧 Email",
                help="User email address - must be unique",
                required=True,
                width="large"
            ),
            "Cost To": st.column_config.SelectboxColumn(
                "🏢 Cost To (BU)",
                help="Business unit for cost allocation",
                options=all_options,
                required=True,
                width="small"
            )
        },
        disabled=False  # Ensure editing is enabled
    )
    
    # Check if data has changed and show save options
    data_changed = not edited_df.equals(bu_df)
    
    if data_changed:
        st.warning("⚠️ **คุณมีการเปลี่ยนแปลงข้อมูลที่ยังไม่ได้บันทึก!** กรุณากดปุ่ม Save เพื่อบันทึกการเปลี่ยนแปลง")
    
    # Save options - prominent and clear
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("💾 **Save Changes**", use_container_width=True, type="primary", disabled=not data_changed):
            try:
                # Save to Excel directly in current directory
                edited_df.to_excel(PERSIST_FILE, index=False)
                st.success(f"✅ **Saved successfully!** {len(edited_df)} records saved to {PERSIST_FILE}")
                
                # Update session state to reflect saved data
                st.session_state.bu_data_saved = True
                
                # Refresh the page to show updated data
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ **Save failed:** {str(e)}")
                
    with col2:
        if st.button("🔄 **Reset to Last Saved**", use_container_width=True, disabled=not data_changed):
            st.rerun()
            
    with col3:
        if st.button("📥 **Export Excel**", use_container_width=True):
            try:
                # Create a temporary file for download
                buffer = io.BytesIO()
                edited_df.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Excel File",
                    data=buffer.getvalue(),
                    file_name=f"bu_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")
                
    with col4:
        # Auto-save toggle
        auto_save = st.checkbox("🔄 Auto-save", value=False, help="Automatically save changes every few seconds")
    
    # Auto-save functionality
    if auto_save and data_changed:
        if "last_auto_save" not in st.session_state:
            st.session_state.last_auto_save = time.time()
        
        # Auto-save every 5 seconds if changes detected
        if time.time() - st.session_state.last_auto_save > 5:
            try:
                edited_df.to_excel(PERSIST_FILE, index=False)
                st.session_state.last_auto_save = time.time()
                st.success("🔄 **Auto-saved!**", icon="✅")
            except Exception as e:
                st.error(f"❌ Auto-save failed: {str(e)}")
    
    # Show current save status
    if os.path.exists(PERSIST_FILE):
        file_time = datetime.fromtimestamp(os.path.getmtime(PERSIST_FILE))
        st.caption(f"📁 **Last saved:** {file_time.strftime('%Y-%m-%d %H:%M:%S')} | **Rows:** {len(edited_df)} | **File:** {PERSIST_FILE}")
    else:
        st.caption("📁 **No saved file found** - Save your changes to create the database file")

    st.divider()
    
    # Additional tips
    with st.expander("🎁 Quick Tips for Table Management", expanded=False):
        st.markdown("""
        **✅ To Add New Users:**
        1. Scroll to bottom of table
        2. Click the **+** (plus) button 
        3. Fill in the new row with user details
        4. **Click Save Changes** to persist data
        
        **✂️ To Delete Users:**
        1. Find the checkbox column on the **left side** of the table
        2. Click checkboxes to select rows you want to delete
        3. Look for the **trash/delete icon** (usually appears after selection)
        4. Click the delete icon to remove selected rows
        5. **Click Save Changes** to make deletion permanent
        
        **✏️ To Edit Users:**
        - Simply click on any cell and type new information
        - Use dropdown for Cost To (BU) column
        - **Click Save Changes** after editing
        
        **💾 Important:**
        - **ALWAYS click "Save Changes"** after any modifications
        - Changes are temporary until you save!
        - Use Auto-save for convenience (saves every 5 seconds)
        """)

    # Advanced options section
    with st.expander("⚙️ Advanced Options & Bulk Operations", expanded=False):
        st.markdown("**⚠️ Bulk Data Replacement**")
        st.markdown("*Use this only when you need to replace ALL existing data*")
        
        bu_upload = st.file_uploader(
            "Upload Excel file to replace ALL current mappings", 
            type=["xlsx"],
            help="⚠️ This will completely replace your current database!"
        )
        if bu_upload:
            try:
                upload_df = pd.read_excel(bu_upload)
                for col in columns:
                    if col not in upload_df.columns:
                        upload_df[col] = ""
                bu_df = upload_df[columns]
                bu_df.to_excel(PERSIST_FILE, index=False)
                st.success("✅ All BU Mappings replaced with uploaded data!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")

# ===== Expense Allocation =====
elif page == "💰 Expense Allocation":
    st.title("💰 Atlassian Expense Allocation")
    
    with st.expander("🔍 How it Works", expanded=False):
        st.markdown("""
        **Simple 3-step process:**
        
        1. **📄 Upload Invoice PDF** - Your Atlassian invoice file
        2. **👥 Upload Users CSV** - Export from your system (must contain 'email' column)  
        3. **⚡ Auto-Processing** - App extracts amounts, maps users, calculates allocations
        4. **📊 Download Results** - Get Excel files with detailed allocations
        
        **New users** are automatically added to BU mapping with "Unknown" cost center.
        You can edit mappings in the **BU Mapping Management** page.
        """)
    
    st.divider()
    
    # File upload section with session state
    st.markdown("### 📁 Upload Files")
    col1, col2 = st.columns(2)
    
    with col1:
        pdf_file = st.file_uploader("📄 Invoice PDF", type=["pdf"], key="pdf_file")
        # VAT Toggle
        include_vat = st.checkbox(
            "💰 Include VAT in calculations", 
            value=False,
            help="Check this if your PDF has a separate 'Amount' column with VAT included. Uncheck for older PDFs with only 'Amount excl. tax'."
        )
        # Store in session state
        if pdf_file is not None:
            st.session_state.uploaded_files['pdf_file'] = pdf_file.name
            st.session_state.uploaded_files['pdf_content'] = pdf_file.read()
            # Reset file pointer for processing
            pdf_file.seek(0)
        # Store VAT preference in session state
        st.session_state.uploaded_files['include_vat'] = include_vat
    
    with col2:
        csv_file = st.file_uploader("👥 Users CSV", type=["csv"], key="csv_file") 
        # Store in session state
        if csv_file is not None:
            st.session_state.uploaded_files['csv_file'] = csv_file.name
            st.session_state.uploaded_files['users_data'] = csv_file.read()
            # Reset file pointer for processing
            csv_file.seek(0)
    
    # Show uploaded file status
    if st.session_state.uploaded_files['pdf_file'] or st.session_state.uploaded_files['csv_file']:
        st.markdown("**📋 Uploaded Files Status:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.uploaded_files['pdf_file']:
                st.success(f"✅ PDF: {st.session_state.uploaded_files['pdf_file']}")
            else:
                st.info("⏳ No PDF uploaded")
        with col2:
            if st.session_state.uploaded_files['csv_file']:
                st.success(f"✅ CSV: {st.session_state.uploaded_files['csv_file']}")
            else:
                st.info("⏳ No CSV uploaded")
        
        # Clear files button
        col_clear1, col_clear2 = st.columns(2)
        with col_clear1:
            if st.button("🗑️ Clear All Files"):
                for key in st.session_state.uploaded_files.keys():
                    st.session_state.uploaded_files[key] = None
                st.rerun()
        
        with col_clear2:
            if st.button("🔄 Clear Cache & Restart"):
                st.session_state.clear()
                st.rerun()

    # Check if we have both files (either newly uploaded or from session)
    has_pdf = pdf_file is not None or st.session_state.uploaded_files['pdf_content'] is not None
    has_csv = csv_file is not None or st.session_state.uploaded_files['users_data'] is not None

    if has_pdf and has_csv:
        st.divider()
        
        # Parse Invoice (use session state data if available)
        st.markdown("### 📄 Processing Invoice...")
        
        if st.session_state.uploaded_files['allocation_result'] is not None:
            # Show cached results
            st.info("📋 Using previously calculated results. Upload new files to recalculate.")
            text = "Using cached data - PDF already processed"
        else:
            # Process files
            with st.spinner("Extracting text from PDF..."):
                if pdf_file is not None:
                    # Use newly uploaded file
                    with pdfplumber.open(pdf_file) as pdf:
                        text = ''
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + '\n'
                else:
                    # Use session state data
                    import io
                    pdf_bytes = io.BytesIO(st.session_state.uploaded_files['pdf_content'])
                    with pdfplumber.open(pdf_bytes) as pdf:
                        text = ''
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + '\n'
        
        with st.expander("📝 PDF Text Preview", expanded=False):
            st.text_area("Extracted text:", text, height=200)
        
        # Only process if not cached
        if st.session_state.uploaded_files['allocation_result'] is None:
            # Extract product items with VAT setting
            include_vat = st.session_state.uploaded_files.get('include_vat', False)
            product_items = extract_invoice_items(text, include_vat)
            
            # Show calculation mode
            vat_mode = "Include VAT" if include_vat else "Exclude VAT"
            st.info(f"📊 **Calculation Mode:** {vat_mode} - Using {'final Amount column' if include_vat else 'Amount excl. tax column'}")
            
            missing = [i for i in product_items if i['amount'] is None]
            
            # Manual input for missing amounts
            if missing:
                st.warning("⚠️ Could not auto-extract all amounts. Please enter missing values:")
                
                for i in range(len(product_items)):
                    if product_items[i]['amount'] is None:
                        manual = st.number_input(
                            f"💰 Amount for: **{product_items[i]['desc']}**", 
                            min_value=0.0, 
                            format="%.2f", 
                            key=f"manual_{i}"
                        )
                        product_items[i]['amount'] = manual
                
                if any(i['amount'] is None or i['amount']==0 for i in product_items):
                    st.info("🔄 Please enter all missing amounts to continue.")
                    st.stop()

            # Use real product names for output
            product_names = [p['desc'] for p in product_items]

            # Load Users (from uploaded file or session)
            st.markdown("### 👥 Processing Users...")
            if csv_file is not None:
                users_df = pd.read_csv(csv_file)
            else:
                # Use session state data
                import io
                csv_bytes = io.BytesIO(st.session_state.uploaded_files['users_data'])
                users_df = pd.read_csv(csv_bytes)
            
            users_df['email'] = users_df['email'].str.lower()
            
            if 'User name' not in users_df.columns:
                users_df['User name'] = users_df.get('username', users_df.get('name', ''))

            # Load Current BU Mapping
            if os.path.exists(PERSIST_FILE):
                bu_df = pd.read_excel(PERSIST_FILE)
                bu_df['Email'] = bu_df['Email'].str.lower()
            else:
                bu_df = pd.DataFrame(columns=['User name', 'Email', 'Cost To'])

            # Find and auto-add unmapped users
            merged = pd.merge(users_df, bu_df, left_on='email', right_on='Email', how='left')
            unmapped = merged[merged['Cost To'].isna()]
            
            if len(unmapped) > 0:
                default_cost_to = "Unknown"
                auto_added = []
                
                for idx, row in unmapped.iterrows():
                    new_entry = {
                        "User name": row.get("User name", ""),
                        "Email": row["email"],
                        "Cost To": default_cost_to,
                    }
                    auto_added.append(new_entry)
                
                # Update mapping and save
                new_bu_df = pd.concat([bu_df, pd.DataFrame(auto_added)], ignore_index=True)
                new_bu_df = new_bu_df.drop_duplicates(subset=["Email"], keep="last")
                new_bu_df.to_excel(PERSIST_FILE, index=False)
                
                st.info(f"➕ Auto-added {len(auto_added)} new users with Cost To = '{default_cost_to}'. Edit in BU Mapping Management if needed.")
                
                # Re-merge with updated mapping
                merged = pd.merge(users_df, new_bu_df, left_on='email', right_on='Email', how='left')

            # Calculate allocations
            merged['Cost To'] = merged['Cost To'].fillna("")
            total_users = len(merged)
            it_users = merged[merged['Cost To'].str.upper() == "IT"]
            num_it_users = len(it_users)

            # Rounding-safe allocations
            alloc_shares = {}
            for idx in [0, 1, 2, 4, 5]:
                alloc_shares[product_names[idx]] = rounding_safe_split(product_items[idx]['amount'], total_users)

            # Jira Service (IT only)
            inv4_shares = [0.00] * total_users
            if num_it_users > 0:
                shares_for_it = rounding_safe_split(product_items[3]['amount'], num_it_users)
                it_idx = merged["Cost To"].str.upper() == "IT"
                share_iter = iter(shares_for_it)
                for i in range(total_users):
                    if it_idx.iloc[i]:
                        inv4_shares[i] = next(share_iter)

            # Create output DataFrame
            output_df = pd.DataFrame({
                "User name": merged["User name_x"] if "User name_x" in merged.columns else merged["User name"],
                "Email": merged["email"],
                "Cost To": merged["Cost To"],
                product_names[0]: alloc_shares[product_names[0]],
                product_names[1]: alloc_shares[product_names[1]],
                product_names[2]: alloc_shares[product_names[2]],
                product_names[3]: inv4_shares,
                product_names[4]: alloc_shares[product_names[4]],
                product_names[5]: alloc_shares[product_names[5]],
            })

            # Summary by Cost To
            summary_cols = product_names
            summary = output_df.groupby("Cost To")[summary_cols].sum().reset_index()
            summary["Grand Total"] = summary[summary_cols].sum(axis=1)
            
            # Store results in session state
            st.session_state.uploaded_files['allocation_result'] = output_df
            st.session_state.uploaded_files['summary_result'] = summary

            st.divider()
        
    # Display results (either newly calculated or from session state)
    if st.session_state.uploaded_files['allocation_result'] is not None:
        output_df = st.session_state.uploaded_files['allocation_result']
        summary = st.session_state.uploaded_files['summary_result']
        
        st.markdown("### 📊 Allocation Results")
        st.success("✅ Allocation data available!")
        
        # Show calculation summary
        include_vat = st.session_state.uploaded_files.get('include_vat', False)
        if include_vat:
            st.info("💰 **Calculation includes VAT** - Using final Amount column from invoice")
        else:
            st.info("💰 **Calculation excludes VAT** - Using Amount excl. tax column from invoice")
        
        st.markdown("**Preview (first 10 rows):**")
        st.dataframe(output_df.head(10), hide_index=True, use_container_width=True)

        st.markdown("### 🏢 Summary by Business Unit")
        st.dataframe(summary, hide_index=True, use_container_width=True)

        # Download buttons
        st.markdown("### 📥 Download Results")
        col1, col2 = st.columns(2)
        
        with col1:
            # Summary download
            with io.BytesIO() as buf:
                summary.to_excel(buf, index=False)
                st.download_button(
                    "📊 Download Summary by BU",
                    data=buf.getvalue(),
                    file_name="Expense_Allocation_Summary.xlsx",
                    use_container_width=True
                )

        with col2:
            # Full allocation download
            with io.BytesIO() as towrite:
                with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
                    output_df.to_excel(writer, index=False, sheet_name="Expense Allocation")
                towrite.seek(0)
                st.download_button(
                    "📋 Download Full Allocation",
                    data=towrite.getvalue(),
                    file_name="Expense_Allocation_Output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    else:
        st.info("📁 Please upload both Invoice PDF and Users CSV to proceed.")
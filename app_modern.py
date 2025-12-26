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
    """
    Enhanced invoice item extraction - extracts ALL line items from invoice.
    No longer limited to predefined products.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    found = []
    
    # Pattern to identify product lines (lines with USD amounts and product info)
    # Typically: Product Name ... USD XX.XX ... USD XX.XX (optional)
    for line in lines:
        # Skip header lines, total lines, etc.
        if any(skip in line.lower() for skip in ['description', 'total', 'subtotal', 'amount due', 'balance']):
            continue
        
        # Look for lines with USD amounts
        matches = re.findall(r"USD\s*([\d,]+\.\d{2})", line)
        
        if matches and len(matches) >= 1:
            # This looks like a product line
            # Extract product name (text before first USD)
            product_name_match = re.match(r"^(.+?)\s+USD", line)
            if product_name_match:
                product_name = product_name_match.group(1).strip()
                
                # Skip if it's clearly not a product line
                if len(product_name) < 3 or product_name.isdigit():
                    continue
                
                # Extract amount based on VAT setting
                amounts = [float(m.replace(',', '')) for m in matches]
                
                if include_vat:
                    # For new format with VAT: take the LAST amount (rightmost = total with VAT)
                    amount = amounts[-1]
                else:
                    # For old format: take the FIRST amount (Amount excl. tax)
                    amount = amounts[0]
                
                # Try to extract quantity/user count if present
                # Look for patterns like: "x 30" or "30 users" or just a number
                count_match = re.search(r'[xX×]\s*(\d+)|(\d+)\s*user', line)
                count = int(count_match.group(1) or count_match.group(2)) if count_match else 1
                
                found.append({
                    "desc": product_name,
                    "amount": amount,
                    "count": count,
                })
    
    return found


def extract_invoice_items_from_tables(pdf_file, include_vat=False):
    """
    Advanced extraction using pdfplumber's table detection.
    Extracts ALL line items from invoice tables dynamically.
    """
    found = []
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Extract tables from the page
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                for table in tables:
                    # Skip empty tables
                    if not table or len(table) < 2:
                        continue
                    
                    # Identify columns
                    header_row = table[0] if table else []
                    desc_col_idx = None
                    amount_col_idx = None
                    qty_col_idx = None
                    
                    # Find column indices by header names
                    for idx, cell in enumerate(header_row):
                        if cell and isinstance(cell, str):
                            cell_lower = cell.lower()
                            
                            # Find description column
                            if desc_col_idx is None and any(term in cell_lower for term in ['description', 'product', 'item']):
                                desc_col_idx = idx
                            
                            # Find quantity column
                            if qty_col_idx is None and any(term in cell_lower for term in ['quantity', 'qty', 'users']):
                                qty_col_idx = idx
                            
                            # Find amount column based on VAT setting
                            if include_vat:
                                # Look for total/amount column (rightmost amount column with VAT)
                                if 'amount' in cell_lower and 'excl' not in cell_lower:
                                    amount_col_idx = idx
                            else:
                                # Look for amount excl. tax
                                if 'amount' in cell_lower and 'excl' in cell_lower:
                                    amount_col_idx = idx
                    
                    # Auto-detect columns if headers don't match
                    if desc_col_idx is None:
                        desc_col_idx = 0  # First column is usually description
                    
                    if amount_col_idx is None and len(header_row) > 0:
                        # Find rightmost column with USD amounts
                        # For include_vat=True, we want the rightmost amount column
                        # For include_vat=False, we want the first amount column (if multiple exist)
                        amount_columns = []
                        for row in table[1:]:
                            for idx in range(len(row)):
                                cell = row[idx] if idx < len(row) else None
                                if cell and re.search(r'USD|[\d,]+\.\d{2}', str(cell)):
                                    if idx not in amount_columns:
                                        amount_columns.append(idx)
                            if amount_columns:
                                break
                        
                        if amount_columns:
                            if include_vat:
                                # Use rightmost (last) amount column
                                amount_col_idx = amount_columns[-1]
                            else:
                                # Use leftmost (first) amount column
                                amount_col_idx = amount_columns[0]
                    
                    # Extract all product rows
                    for row_idx, row in enumerate(table[1:], 1):  # Skip header row
                        if not row or len(row) <= desc_col_idx:
                            continue
                        
                        # Get description
                        desc_cell = row[desc_col_idx] if desc_col_idx < len(row) else None
                        if not desc_cell:
                            continue
                        
                        desc = str(desc_cell).strip()
                        
                        # Skip non-product rows (totals, headers, empty)
                        if not desc or len(desc) < 3:
                            continue
                        if any(skip in desc.lower() for skip in ['total', 'subtotal', 'amount due', 'description']):
                            continue
                        
                        # Get amount
                        amount = None
                        if amount_col_idx is not None and amount_col_idx < len(row):
                            cell_value = row[amount_col_idx]
                            if cell_value:
                                # Extract numeric value (handle both "USD XXX.XX" and "XXX.XX" formats)
                                match = re.search(r'([\d,]+\.\d{2})', str(cell_value))
                                if match:
                                    amount = float(match.group(1).replace(',', ''))
                        
                        # Get quantity/user count
                        count = 1
                        if qty_col_idx is not None and qty_col_idx < len(row):
                            qty_cell = row[qty_col_idx]
                            if qty_cell:
                                qty_match = re.search(r'(\d+)', str(qty_cell))
                                if qty_match:
                                    count = int(qty_match.group(1))
                        
                        # Add to results if we have both description and amount
                        if desc and amount is not None:
                            found.append({
                                "desc": desc,
                                "amount": amount,
                                "count": count,
                            })
    
    except Exception as e:
        # If table extraction fails, return empty results
        # The fallback text extraction will be used
        import traceback
        print(f"Table extraction error: {e}")
        traceback.print_exc()
    
    return found

def show_extraction_debug_info(product_items, text_preview=""):
    """
    Display detailed extraction results for debugging and transparency.
    """
    st.markdown("### 🔍 Extraction Details")
    
    extraction_df = pd.DataFrame(product_items)
    extraction_df['Status'] = extraction_df['amount'].apply(
        lambda x: '✅ Found' if x is not None else '❌ Missing'
    )
    extraction_df['Amount (USD)'] = extraction_df['amount'].apply(
        lambda x: f"${x:,.2f}" if x is not None else "N/A"
    )
    
    display_df = extraction_df[['desc', 'Status', 'Amount (USD)', 'count']].copy()
    display_df.columns = ['Product', 'Status', 'Amount', 'User Count']
    
    st.dataframe(display_df, width="stretch")
    
    # Summary statistics
    found_count = sum(1 for item in product_items if item['amount'] is not None)
    total_count = len(product_items)
    success_rate = (found_count / total_count * 100) if total_count > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Found", f"{found_count}/{total_count}")
    with col2:
        st.metric("Success Rate", f"{success_rate:.0f}%")
    with col3:
        total_amount = sum(item['amount'] for item in product_items if item['amount'] is not None)
        st.metric("Total Extracted", f"${total_amount:,.2f}")

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
        width="stretch",
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
        if st.button("💾 **Save Changes**", width="stretch", type="primary", disabled=not data_changed):
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
        if st.button("🔄 **Reset to Last Saved**", width="stretch", disabled=not data_changed):
            st.rerun()
            
    with col3:
        if st.button("📥 **Export Excel**", width="stretch"):
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
                    width="stretch"
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
            value=True,
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
                    pdf_bytes = io.BytesIO(pdf_file.read())
                    pdf_file.seek(0)  # Reset for potential reuse
                    
                    with pdfplumber.open(pdf_bytes) as pdf:
                        text = ''
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + '\n'
                else:
                    # Use session state data
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
            # Extract product items with smart multi-method extraction
            include_vat = st.session_state.uploaded_files.get('include_vat', False)
            
            # Method 1: Try table extraction first (more accurate)
            st.info("🔍 **Smart Extraction:** Analyzing PDF structure...")
            
            # Reset pdf_bytes for table extraction
            if pdf_file is not None:
                pdf_bytes = io.BytesIO(pdf_file.read())
                pdf_file.seek(0)
            else:
                pdf_bytes = io.BytesIO(st.session_state.uploaded_files['pdf_content'])
            
            product_items = extract_invoice_items_from_tables(pdf_bytes, include_vat)
            
            # Method 2: Fallback to text extraction for items not found
            items_found_by_table = sum(1 for item in product_items if item['amount'] is not None)
            if items_found_by_table < len(product_items):
                st.info(f"🔄 **Hybrid Extraction:** Found {items_found_by_table}/{len(product_items)} items via table, using text extraction for remaining...")
                text_items = extract_invoice_items(text, include_vat)
                
                # Merge results: prefer table extraction, use text extraction as fallback
                for i, item in enumerate(product_items):
                    if item['amount'] is None and i < len(text_items):
                        product_items[i]['amount'] = text_items[i]['amount']
            else:
                st.success(f"✅ **Table Extraction Successful:** Found all {items_found_by_table} product amounts")
            
            # Show calculation mode with detailed explanation
            vat_mode = "Include VAT" if include_vat else "Exclude VAT"
            if include_vat:
                st.info(f"📊 **Calculation Mode: {vat_mode}** ✅\n"
                       f"- Using **rightmost/final Amount column** (includes VAT)\n"
                       f"- For invoices with multiple amount columns, this selects the total with tax")
            else:
                st.info(f"📊 **Calculation Mode: {vat_mode}** \n"
                       f"- Using **Amount excl. tax column** (excludes VAT)\n"
                       f"- For invoices with multiple amount columns, this selects the amount without tax")
            
            # Show detailed extraction results
            with st.expander("🔍 View Extraction Details", expanded=False):
                show_extraction_debug_info(product_items, text[:500])
            
            # Display invoice total summary
            total_extracted = sum(item['amount'] for item in product_items if item['amount'] is not None)
            total_items = len(product_items)
            st.success(f"📋 **Invoice Summary:** {total_items} line items | **Total Amount:** ${total_extracted:,.2f}")
            
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

            # Prepare dynamic allocation columns
            # Each product can have different user count and allocation rules
            allocation_columns = {}
            
            for product in product_items:
                product_name = product['desc']
                product_amount = product['amount']
                product_count = product.get('count', total_users)  # Default to total users if not specified
                
                # Check if this is a Jira Service-like product (IT only)
                # Detect by keywords in product name
                is_it_only = any(keyword in product_name.lower() for keyword in ['jira service', 'service management'])
                
                if is_it_only and num_it_users > 0:
                    # Allocate only to IT users
                    shares = [0.00] * total_users
                    shares_for_it = rounding_safe_split(product_amount, num_it_users)
                    it_idx = merged["Cost To"].str.upper() == "IT"
                    share_iter = iter(shares_for_it)
                    for i in range(total_users):
                        if it_idx.iloc[i]:
                            shares[i] = next(share_iter)
                    allocation_columns[product_name] = shares
                else:
                    # Allocate to all users or specific count
                    # If product_count matches total_users, allocate evenly to all
                    # Otherwise, allocate to first N users (or adjust as needed)
                    if product_count >= total_users or product_count == 1:
                        # Allocate evenly to all users
                        allocation_columns[product_name] = rounding_safe_split(product_amount, total_users)
                    else:
                        # Allocate to subset of users (first N users that match criteria)
                        # For now, allocate evenly to all - can be customized later
                        allocation_columns[product_name] = rounding_safe_split(product_amount, total_users)

            # Create output DataFrame dynamically
            output_data = {
                "User name": merged["User name_x"] if "User name_x" in merged.columns else merged["User name"],
                "Email": merged["email"],
                "Cost To": merged["Cost To"],
            }
            
            # Add all product columns
            for product_name, shares in allocation_columns.items():
                output_data[product_name] = shares
            
            output_df = pd.DataFrame(output_data)

            # Summary by Cost To
            product_names = [p['desc'] for p in product_items]
            summary = output_df.groupby("Cost To")[product_names].sum().reset_index()
            summary["Grand Total"] = summary[product_names].sum(axis=1)
            
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
        
        # Display grand total comparison
        product_cols = [col for col in output_df.columns if col not in ['User name', 'Email', 'Cost To']]
        calculated_total = output_df[product_cols].sum().sum()
        st.metric("🧮 **Calculated Grand Total**", f"${calculated_total:,.2f}", help="Sum of all allocations - should match invoice total")
        
        st.markdown("**Preview (first 10 rows):**")
        st.dataframe(output_df.head(10), hide_index=True, width="stretch")

        st.markdown("### 🏢 Summary by Business Unit")
        st.dataframe(summary, hide_index=True, width="stretch")

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
                    width="stretch"
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
                    width="stretch"
                )

    else:
        st.info("📁 Please upload both Invoice PDF and Users CSV to proceed.")